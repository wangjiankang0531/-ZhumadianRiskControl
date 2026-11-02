from pathlib import Path
import unittest,tempfile,json,hashlib,io,copy
from PIL import Image
from readonly_hybrid_store import ReadOnlyHybridStore
from build_hybrid_overlap import build_overlap
sha=lambda data:hashlib.sha256(data).hexdigest()

class HybridStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.base=self.root/'base/texture';self.overlap=self.root/'overlap/texture';self.base.mkdir(parents=True);self.overlap.mkdir(parents=True)
        stream=io.BytesIO();Image.new('RGB',(16,16),(31,47,63)).save(stream,format='JPEG',quality=100);self.source=self.root/'source.jpg';self.source.write_bytes(stream.getvalue());source_sha=sha(stream.getvalue())
        with Image.open(self.source) as loaded:original=loaded.convert('RGBA')
        prefix=bytes([31])*336;tail=[];mips=[];offset=0;overlap=[];overlap_rows=[];overlap_offset=0
        for level in range(5):
            size=16>>level;image=original.resize((size,size),Image.Resampling.LANCZOS);raw=image.tobytes();image.close();kind='bc7' if level<3 else 'rgba8'
            if level==3:offset=0
            count=((size+3)//4)**2*16 if kind=='bc7' else len(raw);data=prefix[offset:offset+count] if kind=='bc7' else raw
            mips.append(dict(level=level,width=size,height=size,offset=offset,bytes=len(data),format=kind,sha256=sha(data),sourceRgbaSHA256=sha(raw),decodedRgbaSHA256='b'*64 if kind=='bc7' else sha(raw),accepted=True,quality=dict(rgbPSNR=50 if kind=='bc7' else 999,rgbChannelP99=1 if kind=='bc7' else 0,rgbMaxError=2 if kind=='bc7' else 0)));offset+=len(data)
            if kind=='rgba8':tail.append(raw)
            if level in [1,2]:overlap_rows.append(dict(level=level,width=size,height=size,offset=overlap_offset,bytes=len(raw),sha256=sha(raw),sourceRgbaSHA256=sha(raw),accepted=True,quality=dict(rgbPSNR=999,rgbChannelP99=0,rgbMaxError=0)));overlap.append(raw);overlap_offset+=len(raw)
        original.close();tail=b''.join(tail);payload=prefix+tail
        self.manifest=dict(schema='xnby.bc7_rgba_tail.v1',format='BC7_PREFIX_RGBA8_TAIL',sourceSHA256=source_sha,sourceSize=[16,16],tailStartLevel=3,payloadBytes=len(payload),payloadSHA256=sha(payload),components=dict(bc7=dict(file='prefix.bc7',bytes=len(prefix),sha256=sha(prefix)),rgba8=dict(file='tail.rgba',bytes=len(tail),sha256=sha(tail))),mips=mips,accepted=True,qualityThresholds=dict(rgbPSNRMin=40,rgbChannelP99Max=16,rgbMaxErrorMax=96))
        overlap=b''.join(overlap);self.ov=dict(schema='xnby.bc7_rgba_overlap.v1',sourceSHA256=source_sha,basePayloadSHA256=sha(payload),startLevel=1,payloadBytes=len(overlap),payloadSHA256=sha(overlap),mips=overlap_rows)
        (self.base/'prefix.bc7').write_bytes(prefix);(self.base/'tail.rgba').write_bytes(tail);(self.overlap/'overlap.rgba').write_bytes(overlap)
        (self.base/'manifest.json').write_text(json.dumps(self.manifest));(self.overlap/'manifest.json').write_text(json.dumps(self.ov))
        self.config=dict(schema='xnby.prepared_hybrid_store.v1',resourceRoot=str(self.base.parent),overlapRoot=str(self.overlap.parent),entries=[dict(sourceSHA256=source_sha,directory='texture',manifestSHA256=sha((self.base/'manifest.json').read_bytes()),overlapDirectory='texture',overlapManifestSHA256=sha((self.overlap/'manifest.json').read_bytes()))]);self.path=self.root/'config.json';self.publish()
    def tearDown(self):self.temp.cleanup()
    def publish(self):self.path.write_text(json.dumps(self.config))
    def test_index_combined_payload_and_sanitized_descriptor(self):
        store=ReadOnlyHybridStore(self.path);index=store.index();self.assertEqual(index['schema'],'xnby.prepared_texture_index.v2');row=index['entries'][0];self.assertEqual(row['format'],'bc7_rgba_overlap');descriptor=store.descriptor(row['sourceSHA256'],row['payloadSHA256']);self.assertEqual(descriptor['payloadBytes'],676)
        pieces=[store.payload(row['sourceSHA256'],row['payloadSHA256'],name) for name in ['prefix.bc7','tail.rgba','overlap.rgba']];self.assertEqual(sha(b''.join(pieces)),row['payloadSHA256']);self.assertNotIn(str(self.root),json.dumps(descriptor));self.assertNotIn('sourceRgbaSHA256',json.dumps(descriptor['texture']))
    def test_pinned_base_and_overlap_manifest_rechecked(self):
        for folder in [self.base,self.overlap]:
            old=(folder/'manifest.json').read_bytes();store=ReadOnlyHybridStore(self.path);row=store.index()['entries'][0];(folder/'manifest.json').write_bytes(old+b' ')
            with self.assertRaises(ValueError):store.descriptor(row['sourceSHA256'],row['payloadSHA256'])
            (folder/'manifest.json').write_bytes(old)
    def test_payload_mutations_and_unknown_component_rejected(self):
        store=ReadOnlyHybridStore(self.path);row=store.index()['entries'][0]
        for folder,name in [(self.base,'prefix.bc7'),(self.base,'tail.rgba'),(self.overlap,'overlap.rgba')]:
            p=folder/name;old=p.read_bytes();p.write_bytes(bytes([old[0]^1])+old[1:])
            with self.assertRaises(ValueError):store.payload(row['sourceSHA256'],row['payloadSHA256'],name)
            p.write_bytes(old)
        with self.assertRaises(ValueError):store.payload(row['sourceSHA256'],row['payloadSHA256'],'source.jpg')
    def test_traversal_duplicate_source_and_wrong_pin_fail_closed(self):
        old=copy.deepcopy(self.config)
        for mutate in [lambda c:c['entries'][0].update(directory='../base'),lambda c:c['entries'].append(copy.deepcopy(c['entries'][0])),lambda c:c['entries'][0].update(manifestSHA256='0'*64)]:
            self.config=copy.deepcopy(old);mutate(self.config);self.publish()
            with self.assertRaises(ValueError):ReadOnlyHybridStore(self.path)
    def test_self_consistent_overlap_must_match_pinned_original_pixel_proof(self):
        self.ov['mips'][0]['sha256']=self.ov['mips'][0]['sourceRgbaSHA256']='0'*64;(self.overlap/'manifest.json').write_text(json.dumps(self.ov));self.config['entries'][0]['overlapManifestSHA256']=sha((self.overlap/'manifest.json').read_bytes());self.publish()
        with self.assertRaises(ValueError):ReadOnlyHybridStore(self.path)
    def test_builder_recomputes_original_mips_and_requires_fresh_output(self):
        output=self.root/'fresh';result=build_overlap(self.base,self.config['entries'][0]['manifestSHA256'],self.source,output);self.assertEqual(result,self.ov);self.assertEqual((output/'overlap.rgba').read_bytes(),(self.overlap/'overlap.rgba').read_bytes())
        with self.assertRaises(ValueError):build_overlap(self.base,self.config['entries'][0]['manifestSHA256'],self.source,output)
    def test_fixed_http_routes_have_no_paths_or_write_surface(self):
        store=ReadOnlyHybridStore(self.path);row=store.index()['entries'][0]
        class Handler:
            command='GET';path='/api/prepared-textures'
            def reply(self,*args):self.result=args
        handler=Handler();self.assertTrue(store.handle(handler));self.assertEqual(handler.result[0],200);handler.path=f"/prepared-hybrid-textures/{row['sourceSHA256']}/{row['payloadSHA256']}/overlap.rgba";self.assertTrue(store.handle(handler));self.assertEqual(handler.result[0],200)
        handler.command='POST';self.assertFalse(store.handle(handler));handler.command='GET';handler.path='/prepared-hybrid-textures/../config.json';self.assertFalse(store.handle(handler))
if __name__=='__main__':unittest.main()
