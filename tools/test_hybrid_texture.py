from pathlib import Path
import sys,json,hashlib,struct,subprocess,tempfile,unittest,copy
from PIL import Image
from build_hybrid_texture import prepare_hybrid
from hybrid_texture import describe_hybrid,ReadOnlyHybridTexture
from readonly_texture_store import ReadOnlyTextureStore
HERE=Path(__file__).parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
class HybridTextureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='hybrid-texture-');self.root=Path(self.tmp.name);self.source=self.root/'source.jpg';Image.new('RGB',(8,8),(31,47,63)).save(self.source,quality=95);self.source_raw=self.source.read_bytes();self.source_sha=sha(self.source_raw)
        with Image.open(self.source) as image:base=image.convert('RGBA')
        self.references=[base.resize((s,s),Image.Resampling.LANCZOS).tobytes() for s in [8,4,2,1]]
        rows=[dict(width=s,height=s) for s in [8,4,2,1,1]];header=json.dumps(rows).encode();batch=b'MB7R'+struct.pack('<I',len(header))+header+b''.join(self.references)+bytes([255,255,255,255])
        run=subprocess.run(['D:/Program Files/nodejs/node.exe',str(HERE/'bc7_mode6_cli.mjs'),'--profile=mode6'],input=batch,capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0);self.assertEqual(run.returncode,0,run.stderr);self.good=run.stdout[:112];self.payload=self.good[:80]+run.stdout[112:128]+self.good[96:]
        offset=0;mips=[]
        for i,s in enumerate([8,4,2,1]):
            size=((s+3)//4)**2*16;mips.append(dict(level=i,width=s,height=s,offset=offset,bytes=size,sha256=sha(self.payload[offset:offset+size]),sourceRgbaSHA256=sha(self.references[i]),accepted=True,quality=dict(rgbPSNR=999)));offset+=size
        self.manifest=dict(schema='xnby.bc7.mip_chain.v1',format='BC7_UNORM_BLOCK',sourceSHA256=self.source_sha,sourceSize=[8,8],payloadBytes=len(self.payload),payloadSHA256=sha(self.payload),mips=mips,accepted=True)
    def tearDown(self):self.tmp.cleanup()
    def prepare(self,name='hybrid'):
        raw=json.dumps(self.manifest).encode();return prepare_hybrid(self.source,self.source_sha,raw,sha(raw),self.payload,self.root/name)
    def pin(self,folder):return sha((folder/'manifest.json').read_bytes())
    def test_prefix_is_rechecked_and_the_tail_is_exact_not_the_failed_bc7(self):
        result=self.prepare();self.assertEqual(result['tailStartLevel'],2);self.assertEqual(result['payloadBytes'],100);self.assertEqual((self.root/'hybrid/prefix.bc7').read_bytes(),self.payload[:80]);self.assertEqual((self.root/'hybrid/tail.rgba').read_bytes(),self.references[2]+self.references[3]);self.assertEqual(self.source.read_bytes(),self.source_raw)
        store=ReadOnlyHybridTexture(self.root/'hybrid',self.pin(self.root/'hybrid'));safe=store.descriptor();self.assertEqual(len(safe['mips']),4);self.assertNotIn('sourceRgbaSHA256',safe['mips'][-1]);self.assertNotIn('referenceManifestSHA256',safe);self.assertTrue(safe['accepted']);self.assertEqual(safe['payloadBytes'],len(store.payload('bc7'))+len(store.payload('rgba8')))
    def test_forged_prior_acceptance_does_not_hide_the_actual_failed_mip(self):
        self.manifest['accepted']=True
        for row in self.manifest['mips']:row['accepted']=True;row['quality']={'rgbPSNR':999,'rgbChannelP99':0,'rgbMaxError':0}
        self.assertEqual(self.prepare()['tailStartLevel'],2)
    def test_fresh_output_and_source_reference_digests_are_required(self):
        self.prepare();raw=json.dumps(self.manifest).encode()
        with self.assertRaisesRegex(ValueError,'Fresh'):self.prepare()
        with self.assertRaisesRegex(ValueError,'manifest'):prepare_hybrid(self.source,self.source_sha,raw,'0'*64,self.payload,self.root/'other')
        forged=dict(self.manifest,sourceSHA256='0'*64);forged_raw=json.dumps(forged).encode()
        with self.assertRaisesRegex(ValueError,'source SHA'):prepare_hybrid(self.source,'0'*64,forged_raw,sha(forged_raw),self.payload,self.root/'other')
        self.assertFalse((self.root/'other').exists())
    def test_empty_prefix_and_unneeded_tail_are_rejected(self):
        self.payload=self.good;self.manifest['payloadSHA256']=sha(self.payload)
        for row in self.manifest['mips']:row['sha256']=sha(self.payload[row['offset']:row['offset']+row['bytes']])
        with self.assertRaisesRegex(ValueError,'passing prefix'):self.prepare()
    def test_layout_identity_quality_and_exact_tail_proof_are_required(self):
        good=self.prepare();mutations=[lambda m:m.update(tailStartLevel=0),lambda m:m.update(tailStartLevel=4),lambda m:m.update(tailStartLevel=2.0),lambda m:m['mips'].pop(),lambda m:m['mips'][2].update(offset=1),lambda m:m['mips'][2].update(format='bc7'),lambda m:m['mips'][2].update(sourceRgbaSHA256='0'*64),lambda m:m['mips'][2]['quality'].update(rgbPSNR=50),lambda m:m['mips'][0].update(accepted=False),lambda m:m['components']['rgba8'].update(file='../other'),lambda m:m.update(payloadBytes=m['payloadBytes']+1)]
        for i,mutate in enumerate(mutations):
            with self.subTest(case=i):
                value=copy.deepcopy(good);mutate(value)
                with self.assertRaises(ValueError):describe_hybrid(value,self.source_sha)
    def test_component_or_manifest_mutation_is_rejected_without_repair(self):
        self.prepare();folder=self.root/'hybrid';store=ReadOnlyHybridTexture(folder,self.pin(folder));path=folder/'tail.rgba';path.write_bytes(bytes(20));before=path.read_bytes()
        with self.assertRaises(ValueError):store.payload('rgba8')
        self.assertEqual(path.read_bytes(),before);(folder/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'manifest changed'):store.payload('bc7')
    def test_a_hash_consistent_nonopaque_tail_still_fails(self):
        value=self.prepare();folder=self.root/'hybrid';tail=bytearray((folder/'tail.rgba').read_bytes());tail[3]=0;(folder/'tail.rgba').write_bytes(tail);value['components']['rgba8']['sha256']=sha(tail)
        for row in value['mips']:
            if row['format']=='rgba8':row['sha256']=row['decodedRgbaSHA256']=row['sourceRgbaSHA256']=sha(tail[row['offset']:row['offset']+row['bytes']])
        value['payloadSHA256']=sha((folder/'prefix.bc7').read_bytes()+tail);(folder/'manifest.json').write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'not opaque'):ReadOnlyHybridTexture(folder,self.pin(folder))
    def test_hybrid_does_not_relax_the_legacy_complete_bc7_schema(self):
        value=self.prepare()
        with self.assertRaisesRegex(ValueError,'source/format'):ReadOnlyTextureStore._descriptor(value,self.source_sha)
if __name__=='__main__':unittest.main()
