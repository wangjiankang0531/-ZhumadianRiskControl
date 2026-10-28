"""Mixed publication identity, failure isolation and actual loopback delivery."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

sys.path.insert(0,str(Path(__file__).resolve().parent))
from readonly_texture_union import ReadOnlyTextureUnion
import test_readonly_hybrid_store as hybrid_fixture


def sha(raw):return hashlib.sha256(raw).hexdigest()


class Handler:
    path='/api/prepared-textures'
    command='GET'
    def reply(self,*args):self.result=args


class TextureUnionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=hybrid_fixture.HybridStoreTests('runTest');self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.root=self.fixture.root;self.folder=self.root/'complete';self.folder.mkdir()
        self.payload=bytes(range(48));self.source='a'*64;self.digest=sha(self.payload)
        self.manifest=dict(schema='xnby.bc7.mip_chain.v1',format='BC7_UNORM_BLOCK',sourceSHA256=self.source,
            sourceSize=[4,4],payloadBytes=48,payloadSHA256=self.digest,accepted=True,
            qualityThresholds=dict(rgbPSNRMin=40,rgbChannelP99Max=16,rgbMaxErrorMax=96),
            source='PRIVATE_PRODUCER_PATH',mips=[dict(level=i,width=size,height=size,offset=i*16,bytes=16,
            sha256=sha(self.payload[i*16:(i+1)*16]),accepted=True,quality=dict(rgbPSNR=50,rgbChannelP99=1,rgbMaxError=2)) for i,size in enumerate((4,2,1))])
        (self.folder/'texture.bc7').write_bytes(self.payload);self.config=self.root/'complete-index.json';self.publish()

    def publish(self):
        raw=json.dumps(self.manifest).encode();(self.folder/'manifest.json').write_bytes(raw)
        self.config.write_text(json.dumps(dict(schema='xnby.prepared_texture_index.v1',resourceRoot=str(self.root),
            entries=[dict(sourceSHA256=self.manifest['sourceSHA256'],directory='complete',manifestSHA256=sha(raw))])),'utf-8')

    def store(self):return ReadOnlyTextureUnion(self.config,self.fixture.path)

    def get(self,store,path,method='GET'):
        h=Handler();h.path=path;h.command=method;handled=store.handle(h)
        return handled,getattr(h,'result',None)

    def snapshot(self):
        return {str(p.relative_to(self.root)):(p.stat().st_size,p.stat().st_mtime_ns,sha(p.read_bytes()))
                for p in self.root.rglob('*') if p.is_file() and p not in (self.root/'state.json',self.root/'state.lock')}

    def test_index_has_both_formats_no_private_paths_and_cannot_be_mutated_by_caller(self):
        before=self.snapshot();store=self.store();index=store.index()
        self.assertEqual(index['schema'],'xnby.prepared_texture_index.v2')
        self.assertEqual({r['format'] for r in index['entries']},{'bc7','bc7_rgba_overlap'})
        self.assertEqual(len(index['entries']),2);self.assertNotIn(str(self.root),json.dumps(index))
        index['entries'][0]['sourceSHA256']='changed';self.assertNotIn('changed',json.dumps(store.index()))
        full=self.get(store,f'/prepared-textures/{self.source}/{self.digest}/manifest.json')[1]
        self.assertEqual(full[0],200);self.assertNotIn('PRIVATE_PRODUCER_PATH',full[1].decode())
        self.assertEqual(before,self.snapshot())

    def test_full_only_publication_is_supported_and_missing_hybrid_is_not_redirected(self):
        store=ReadOnlyTextureUnion(self.config)
        self.assertEqual(store.index()['entries'],[dict(sourceSHA256=self.source,payloadSHA256=self.digest,format='bc7')])
        hybrid=self.fixture.manifest['sourceSHA256']
        self.assertEqual(self.get(store,f'/prepared-hybrid-textures/{hybrid}/{self.digest}/prefix.bc7')[1][0],409)
        self.assertEqual(self.get(store,f'/prepared-textures/{self.source}/{self.digest}/texture.bc7')[1][:2],(200,self.payload))

    def test_competing_source_formats_and_failed_quality_cannot_enter_union(self):
        original=copy.deepcopy(self.manifest)
        self.manifest['sourceSHA256']=self.fixture.manifest['sourceSHA256'];self.publish()
        with self.assertRaisesRegex(ValueError,'competing'):self.store()
        self.manifest=copy.deepcopy(original);self.manifest['mips'][0]['accepted']=False;self.publish()
        with self.assertRaises(ValueError):self.store()
        self.manifest=original;self.publish()
        self.fixture.manifest['accepted']=False
        (self.fixture.base/'manifest.json').write_text(json.dumps(self.fixture.manifest))
        self.fixture.config['entries'][0]['manifestSHA256']=sha((self.fixture.base/'manifest.json').read_bytes());self.fixture.publish()
        with self.assertRaises(ValueError):self.store()

    def test_changed_full_or_hybrid_payload_is_rejected_without_repair_or_other_format_loss(self):
        store=self.store();hybrid=next(r for r in store.index()['entries'] if r['format']=='bc7_rgba_overlap')
        path=self.folder/'texture.bc7';path.write_bytes(b'x'*48)
        self.assertEqual(self.get(store,f'/prepared-textures/{self.source}/{self.digest}/texture.bc7')[1][0],409)
        self.assertEqual(path.read_bytes(),b'x'*48)
        self.assertEqual(self.get(store,f"/prepared-hybrid-textures/{hybrid['sourceSHA256']}/{hybrid['payloadSHA256']}/tail.rgba")[1][0],200)
        path.write_bytes(self.payload)
        overlap=self.fixture.overlap/'overlap.rgba';old=overlap.read_bytes();overlap.write_bytes(bytes(len(old)))
        self.assertEqual(self.get(store,f"/prepared-hybrid-textures/{hybrid['sourceSHA256']}/{hybrid['payloadSHA256']}/overlap.rgba")[1][0],409)
        self.assertEqual(self.get(store,f'/prepared-textures/{self.source}/{self.digest}/texture.bc7')[1][0],200)

    def test_queries_unknown_hashes_malformed_routes_and_writes_are_rejected(self):
        store=self.store()
        for path in ('/api/prepared-textures?file=secret','/prepared-textures/../config.json',
                     f'/prepared-textures/{self.source}/{self.digest}/source.jpg'):
            with self.subTest(path=path):self.assertEqual(self.get(store,path)[1][0],400)
        self.assertEqual(self.get(store,f'/prepared-textures/{"b"*64}/{self.digest}/manifest.json')[1][0],409)
        self.assertEqual(self.get(store,'/api/prepared-textures','POST')[1][0],405)
        self.assertFalse(self.get(store,'/unrelated')[0])

    def test_actual_preview_cli_union_payloads_head_host_and_state_ownership(self):
        resources=self.root/'resources';bundle=self.root/'bundle';state=self.root/'state.json';project=self.root/'layers.json'
        project.write_bytes(b'{"user":"unchanged"}')
        for name in ('index.html','viewer.js','source-gain-worker.js'):
            p=bundle/'web'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        for rel in ('data/showcase/zhumadian_native_hierarchy.json','assets/landscape/icons.png',
                    'assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin',
                    'assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf',
                    'assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg',
                    'assets/showcase/runtime/zhumadian/full/base_lod_quality.json'):
            p=resources/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        (resources/'data/showcase/zhumadian_native_hierarchy.json').write_text(json.dumps(dict(root_records=[dict(tile_id=118,sha256='c'*64)])))
        (resources/'work/zhumadian_native_chunk_cache').mkdir(parents=True)
        before=self.snapshot()
        args=[sys.executable,'-I','-B',str(Path(__file__).with_name('serve_native_preview.py')),'--state',str(state),
              '--bundle',str(bundle),'--resources',str(resources),'--layers',str(project),'--prepared-lod',
              '--prepared-textures',str(self.config),'--hybrid-textures',str(self.fixture.path),'--no-browser']
        flags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
        proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=flags);http=build_opener(ProxyHandler({}))
        def request(path,method='GET',headers=None):
            try:r=http.open(Request(url+path,method=method,headers=headers or {}),timeout=5)
            except HTTPError as error:r=error
            with r:return r.status,r.read(),dict(r.headers)
        try:
            deadline=time.monotonic()+8
            while not state.exists():
                if proc.poll() is not None:self.fail(proc.stderr.read().decode(errors='replace'))
                if time.monotonic()>deadline:self.fail('union preview readiness timeout')
                time.sleep(.02)
            saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port'])
            status,raw,_=request('/api/prepared-textures');self.assertEqual(status,200);index=json.loads(raw)
            self.assertEqual(len(index['entries']),2)
            for entry in index['entries']:
                prefix='prepared-textures' if entry['format']=='bc7' else 'prepared-hybrid-textures'
                names=('texture.bc7',) if entry['format']=='bc7' else ('prefix.bc7','tail.rgba','overlap.rgba')
                for name in ('manifest.json',*names):
                    route=f"/{prefix}/{entry['sourceSHA256']}/{entry['payloadSHA256']}/{name}"
                    self.assertEqual(request(route)[0],200);self.assertEqual(request(route,'HEAD')[:2],(200,b''))
            self.assertEqual(request('/api/prepared-textures',headers={'Host':'unrelated.invalid'})[0],403)
            wrong=list(args);wrong[wrong.index('--prepared-textures')+1]=str(self.root/'other.json')
            result=subprocess.run(wrong,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0);self.assertIn(b'different prepared textures',result.stderr)
            wrong=list(args);wrong[wrong.index('--hybrid-textures')+1]=str(self.root/'other-hybrid.json')
            result=subprocess.run(wrong,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0);self.assertIn(b'different hybrid textures',result.stderr)
            wrong=list(args);at=wrong.index('--hybrid-textures');del wrong[at:at+2]
            result=subprocess.run(wrong,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0);self.assertIn(b'different hybrid textures',result.stderr)
            health=json.loads(request('/api/health')[1]);self.assertFalse(health['nativeReaderEnabled']);self.assertFalse(health['conversionEnabled']);self.assertEqual(health['loaded'],0)
            self.assertEqual(request('/application/config.json')[:2],(200,b'{"schema":"xnby.portal.config.v1","mode":"local"}'))
            self.assertEqual(self.snapshot(),before)
        finally:
            if proc.poll() is None and state.exists():
                saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port']);request('/__preview__/stop','POST',{'X-Preview-Key':saved['controlKey']});proc.wait(timeout=5)
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
            errors=proc.stderr.read().decode(errors='replace');proc.stderr.close()
        self.assertEqual(proc.returncode,0,errors)


if __name__=='__main__':unittest.main()
