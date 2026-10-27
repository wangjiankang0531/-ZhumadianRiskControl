import hashlib
import http.client
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from tools import landscape_web_server as web
from tools.readonly_texture_store import ReadOnlyTextureStore


class PreparedTextureHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.folder=self.root/'texture_0';self.folder.mkdir()
        self.source='a'*64;self.raw=bytes(range(48));self.digest=hashlib.sha256(self.raw).hexdigest()
        rows=[]
        for level,size in enumerate([4,2,1]):
            rows.append(dict(level=level,width=size,height=size,offset=level*16,bytes=16,sha256=hashlib.sha256(self.raw[level*16:(level+1)*16]).hexdigest(),accepted=True,quality=dict(rgbPSNR=50.0,rgbChannelP99=1,rgbMaxError=2)))
        self.manifest=dict(schema='xnby.bc7.mip_chain.v1',format='BC7_UNORM_BLOCK',sourceSHA256=self.source,sourceSize=[4,4],payloadBytes=48,payloadSHA256=self.digest,mips=rows,accepted=True,qualityThresholds=dict(rgbPSNRMin=40.0,rgbChannelP99Max=16,rgbMaxErrorMax=96),source='PRIVATE_PRODUCER_PATH',encodeMs=10)
        self.config=self.root/'index.json';self.write_fixture()
        store=ReadOnlyTextureStore(self.config)
        class Handler(web.Handler):
            prepared_textures=store
            def log_message(self,*args):pass
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.route=f'/prepared-textures/{self.source}/{self.digest}/'

    def write_fixture(self):
        raw=json.dumps(self.manifest).encode();(self.folder/'manifest.json').write_bytes(raw);(self.folder/'texture.bc7').write_bytes(self.raw)
        self.config.write_text(json.dumps(dict(schema='xnby.prepared_texture_index.v1',resourceRoot=str(self.root),entries=[dict(directory='texture_0',sourceSHA256=self.source,manifestSHA256=hashlib.sha256(raw).hexdigest())])))

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()

    def request(self,path,method='GET'):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5);connection.request(method,path);response=connection.getresponse();result=response.status,response.read(),dict(response.getheaders());connection.close();return result

    def snapshot(self):
        return {p.name:(p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.root.rglob('*') if p.is_file()}

    def test_http_descriptor_payload_head_and_index_are_read_only_and_sanitized(self):
        before=self.snapshot()
        with patch.object(web.POOL,'submit',side_effect=AssertionError('No conversion')) as submit:
            status,raw,_=self.request('/api/prepared-textures');self.assertEqual(status,200);self.assertEqual(json.loads(raw)['entries'],[dict(sourceSHA256=self.source,payloadSHA256=self.digest)])
            status,raw,_=self.request(self.route+'manifest.json');self.assertEqual(status,200);descriptor=json.loads(raw);self.assertNotIn('source',descriptor);self.assertNotIn('encodeMs',descriptor);self.assertEqual(descriptor['mips'],self.manifest['mips'])
            status,raw,_=self.request(self.route+'texture.bc7');self.assertEqual((status,raw),(200,self.raw))
            status,raw,headers=self.request(self.route+'texture.bc7','HEAD');self.assertEqual((status,raw,headers['Content-Length']),(200,b'',str(len(self.raw))))
            submit.assert_not_called()
        self.assertEqual(before,self.snapshot())

    def test_changed_payload_and_manifest_refused_without_repair(self):
        (self.folder/'texture.bc7').write_bytes(b'x'*48);before=self.snapshot();self.assertEqual(self.request(self.route+'texture.bc7')[0],409);self.assertEqual(before,self.snapshot())
        (self.folder/'manifest.json').write_bytes(b'{}');before=self.snapshot();self.assertEqual(self.request(self.route+'manifest.json')[0],409);self.assertEqual(before,self.snapshot())

    def test_unknown_digest_path_and_query_refused(self):
        self.assertEqual(self.request(self.route.replace(self.digest,'c'*64)+'texture.bc7')[0],409)
        for suffix in ['../private','texture.bc7/extra','source.txt']:
            self.assertEqual(self.request(self.route+suffix)[0],404)
        self.assertEqual(self.request(self.route+'texture.bc7?path=elsewhere')[0],409)

    def test_startup_requires_pinned_descriptor_payload_and_complete_mips(self):
        self.manifest['mips'].pop();self.write_fixture()
        with self.assertRaises(ValueError):ReadOnlyTextureStore(self.config)
        self.manifest['mips'].append(dict(level=2,width=1,height=1,offset=32,bytes=16,sha256='f'*64));self.write_fixture()
        with self.assertRaises(ValueError):ReadOnlyTextureStore(self.config)

    def test_index_rejects_traversal_duplicates_and_linked_payload(self):
        config=json.loads(self.config.read_text());config['entries'].append(config['entries'][0]);self.config.write_text(json.dumps(config))
        with self.assertRaises(ValueError):ReadOnlyTextureStore(self.config)
        config['entries']=config['entries'][:1];config['entries'][0]['directory']='../escape';self.config.write_text(json.dumps(config))
        with self.assertRaises(ValueError):ReadOnlyTextureStore(self.config)
        self.write_fixture();target=self.root/'outside.bc7';target.write_bytes(self.raw);(self.folder/'texture.bc7').unlink()
        try:(self.folder/'texture.bc7').symlink_to(target)
        except OSError as error:self.skipTest('File symlink privilege unavailable: '+str(error))
        with self.assertRaises(ValueError):ReadOnlyTextureStore(self.config)

    def test_unconfigured_index_is_empty(self):
        handler=self.server.RequestHandlerClass;store=handler.prepared_textures;handler.prepared_textures=None
        try:
            status,raw,_=self.request('/api/prepared-textures');self.assertEqual((status,json.loads(raw)['entries']),(200,[]));self.assertEqual(self.request(self.route+'texture.bc7')[0],404)
        finally:handler.prepared_textures=store

    def test_failed_missing_relaxed_or_nonfinite_quality_never_enters_the_store(self):
        original=json.loads(json.dumps(self.manifest))
        mutations=[
            lambda m:m.pop('accepted'),lambda m:m.update(accepted=False),lambda m:m.update(accepted=1),
            lambda m:m['mips'][1].update(accepted=False),lambda m:m['mips'][1].pop('quality'),
            lambda m:m.pop('qualityThresholds'),lambda m:m['qualityThresholds'].update(rgbPSNRMin=39),
            lambda m:m['qualityThresholds'].update(rgbChannelP99Max=17),lambda m:m['qualityThresholds'].update(rgbMaxErrorMax=97),
            lambda m:m['mips'][1]['quality'].update(rgbPSNR=39.999),lambda m:m['mips'][1]['quality'].update(rgbPSNR=float('nan')),
            lambda m:m['mips'][1]['quality'].update(rgbPSNR=float('inf')),lambda m:m['mips'][1]['quality'].update(rgbChannelP99=True),
            lambda m:m['mips'][1]['quality'].update(rgbMaxError=97),
        ]
        try:
            for i,mutate in enumerate(mutations):
                with self.subTest(case=i):
                    self.manifest=json.loads(json.dumps(original));mutate(self.manifest);self.write_fixture();before=self.snapshot()
                    with self.assertRaisesRegex(ValueError,'quality'):ReadOnlyTextureStore(self.config)
                    self.assertEqual(before,self.snapshot())
        finally:self.manifest=original;self.write_fixture()
