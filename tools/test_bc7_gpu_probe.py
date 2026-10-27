from pathlib import Path
import hashlib,json,tempfile,unittest
from serve_bc7_gpu_probe import validate

class Bc7GpuProbeContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bc7-gpu-contract-');self.root=Path(self.tmp.name)
        self.block=b'\x40'+bytes(15);payload=self.block*3;sha=lambda raw:hashlib.sha256(raw).hexdigest()
        self.manifest={'schema':'xnby.bc7.mip_chain.v1','format':'BC7_UNORM_BLOCK','sourceSHA256':'a'*64,'sourceSize':[4,4],'payloadBytes':48,'payloadSHA256':sha(payload),'accepted':True,'qualityThresholds':{'rgbPSNRMin':40.0,'rgbChannelP99Max':16,'rgbMaxErrorMax':96},'producerPath':'not-client-visible','mips':[{'level':i,'width':size,'height':size,'offset':i*16,'bytes':16,'sha256':sha(self.block),'pillowDecodedSHA256':'b'*64,'accepted':True,'quality':{'rgbPSNR':50.0,'rgbChannelP99':1,'rgbMaxError':2}} for i,size in enumerate([4,2,1])]}
        (self.root/'texture.bc7').write_bytes(payload);self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        raw=json.dumps(self.manifest).encode();(self.root/'manifest.json').write_bytes(raw);self.digest=hashlib.sha256(raw).hexdigest()
    def test_only_canonical_descriptor_fields_and_reference_hashes_are_exposed(self):
        descriptor,payload=validate(self.root,self.digest);self.assertEqual(len(payload),48);self.assertNotIn('producerPath',descriptor);self.assertEqual(len(descriptor['mips']),3);self.assertEqual(descriptor['mips'][0]['pillowDecodedSHA256'],'b'*64)
    def test_unaccepted_quality_is_rejected_before_payload_access(self):
        self.manifest['accepted']=False;self.save();(self.root/'texture.bc7').unlink()
        with self.assertRaisesRegex(ValueError,'Unaccepted'):validate(self.root,self.digest)
    def test_one_failed_mip_cannot_be_hidden_by_the_top_level_flag(self):
        self.manifest['mips'][1]['accepted']=False;self.save()
        with self.assertRaisesRegex(ValueError,'Unaccepted'):validate(self.root,self.digest)
    def test_payload_and_manifest_sha_mismatch_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'manifest SHA'):validate(self.root,'0'*64)
        (self.root/'texture.bc7').write_bytes(bytes(48))
        with self.assertRaisesRegex(ValueError,'payload differs'):validate(self.root,self.digest)
    def test_invalid_reference_hash_and_incomplete_chain_are_rejected(self):
        self.manifest['mips'][0]['pillowDecodedSHA256']='invalid';self.save()
        with self.assertRaises(ValueError):validate(self.root,self.digest)
        self.manifest['mips']=self.manifest['mips'][:1];self.save()
        with self.assertRaises(ValueError):validate(self.root,self.digest)

if __name__=='__main__':unittest.main()
