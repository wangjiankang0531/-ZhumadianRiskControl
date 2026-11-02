import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest
from PIL import Image

from build_bc7_mode6_texture import prepare

HERE=Path(__file__).parent
NODE=Path('D:/Program Files/nodejs/node.exe')
text=(HERE/'bc7_partitions.mjs').read_text()
PARTITIONS=json.loads(re.search(r'BC7_PARTITION2=Object.freeze\((\[[^;]+\])\)',text)[1])
ANCHORS=json.loads(re.search(r'BC7_ANCHOR2=Object.freeze\((\[[^;]+\])\)',text)[1])


def decode_reference(block):
    value=int.from_bytes(block,'little');position=0
    def read(count):
        nonlocal position
        out=(value>>position)&((1<<count)-1);position+=count;return out
    mode=0
    while read(1)==0:mode+=1
    if mode==6:
        endpoints=[[0]*4 for _ in range(2)]
        for c in range(4):
            for e in range(2):endpoints[e][c]=read(7)
        parity=[read(1),read(1)]
        for e in range(2):
            for c in range(4):endpoints[e][c]=endpoints[e][c]*2+parity[e]
        weights=[0,4,9,13,17,21,26,30,34,38,43,47,51,55,60,64];out=[]
        for p in range(16):
            w=weights[read(3 if p==0 else 4)]
            out.extend(((64-w)*endpoints[0][c]+w*endpoints[1][c]+32)>>6 for c in range(4))
    elif mode==1:
        partition=read(6);endpoints=[[0]*3 for _ in range(4)]
        for c in range(3):
            for e in range(4):endpoints[e][c]=read(6)
        parity=[read(1),read(1)]
        for e in range(4):
            for c in range(3):
                v=endpoints[e][c]*2+parity[e//2];endpoints[e][c]=v*2+(v>>6)
        weights=[0,9,18,27,37,46,55,64];out=[]
        for p in range(16):
            subset=(PARTITIONS[partition]>>p)&1;w=weights[read(2 if p in (0,ANCHORS[partition]) else 3)]
            out.extend(((64-w)*endpoints[subset*2][c]+w*endpoints[subset*2+1][c]+32)>>6 for c in range(3));out.append(255)
    else:raise ValueError('Unimplemented test reference mode')
    if position!=128:raise ValueError('Incorrect block boundary')
    return bytes(out)


class OpaqueBc7Tests(unittest.TestCase):
    def run_node(self,name,*args,raw=None):
        return subprocess.run([str(NODE),str(HERE/name),*args],input=raw,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)

    def test_all_64_partition_masks_and_anchor_bit_layouts_match_independent_pillow(self):
        run=self.run_node('bc7_partition_probe.mjs');self.assertEqual(run.returncode,0,run.stderr)
        rows=json.loads(run.stdout);self.assertEqual(len(rows),64)
        for row in rows:
            with self.subTest(partition=row['partition']):
                block=bytes.fromhex(row['encoded']);self.assertEqual(block[0]&3,2)
                decoded=Image.frombytes('RGBA',(4,4),block,'bcn',(7,'BC7')).tobytes()
                self.assertEqual(decoded,decode_reference(block))
                self.assertTrue(all(decoded[i]==255 for i in range(3,64,4)))

    def test_mixed_profile_never_increases_per_block_error_against_mode6(self):
        width=height=16;pixels=bytes(v for y in range(height) for x in range(width) for v in ((x*31+y*23)%256,(x*73+y*11)%256,(x*13+y*47)%256,255))
        header=json.dumps([dict(level=0,width=width,height=height)]).encode();batch=b'MB7R'+struct.pack('<I',len(header))+header+pixels
        one=self.run_node('bc7_mode6_cli.mjs','--profile=mode6',raw=batch);two=self.run_node('bc7_mode6_cli.mjs','--profile=mode1-6',raw=batch)
        self.assertEqual(one.returncode,0,one.stderr);self.assertEqual(two.returncode,0,two.stderr);self.assertEqual(len(two.stdout),256)
        self.assertTrue(any(b&3==2 for b in two.stdout[::16]))
        for i in range(16):
            b=two.stdout[i*16:(i+1)*16];self.assertEqual(Image.frombytes('RGBA',(4,4),b,'bcn',(7,'BC7')).tobytes(),decode_reference(b))
            old=Image.frombytes('RGBA',(4,4),one.stdout[i*16:(i+1)*16],'bcn',(7,'BC7')).tobytes();new=decode_reference(b);bx=i%4;by=i//4
            source=bytes(pixels[((by*4+y)*16+bx*4+x)*4+c] for y in range(4) for x in range(4) for c in range(4))
            self.assertLessEqual(sum((a-b)**2 for i,(a,b) in enumerate(zip(source,new)) if i%4!=3),sum((a-b)**2 for i,(a,b) in enumerate(zip(source,old)) if i%4!=3))

    def test_cli_rejects_unknown_profile_and_trailing_batch(self):
        header=json.dumps([dict(width=1,height=1)]).encode();raw=b'MB7R'+struct.pack('<I',len(header))+header+bytes([0,0,0,255])
        self.assertNotEqual(self.run_node('bc7_mode6_cli.mjs','--profile=unknown',raw=raw).returncode,0)
        self.assertNotEqual(self.run_node('bc7_mode6_cli.mjs',raw=raw+b'X').returncode,0)

    def test_full_mips_independent_decode_quality_and_no_raw_disk_copies(self):
        with tempfile.TemporaryDirectory(prefix='bc7-test-') as td:
            root=Path(td);source=root/'input.jpg';image=Image.new('RGB',(16,16));image.putdata([(x*8+y*8,)*3 for y in range(16) for x in range(16)]);image.save(source,quality=95)
            before=source.read_bytes();out=root/'encoded';result=prepare(source,hashlib.sha256(before).hexdigest(),out,NODE,profile='mode1-6')
            self.assertTrue(result['accepted']);self.assertEqual(result['sourceSize'],[16,16]);self.assertEqual(len(result['mips']),5);self.assertEqual(result['mips'][-1]['width'],1)
            self.assertEqual({p.name for p in out.iterdir()},{'manifest.json','texture.bc7'});self.assertEqual(source.read_bytes(),before)
            self.assertLess(sum(p.stat().st_size for p in out.iterdir()),16384)

    def test_report_only_scan_never_publishes_a_payload(self):
        with tempfile.TemporaryDirectory(prefix='bc7-report-') as td:
            root=Path(td);source=root/'source.jpg';Image.new('RGB',(16,16),(23,45,67)).save(source);before=source.read_bytes()
            result=prepare(source,hashlib.sha256(before).hexdigest(),root/'report',NODE,profile='mode1-6',persist_payload=False)
            self.assertTrue(result['accepted']);self.assertFalse(result['payloadSaved']);self.assertEqual({p.name for p in (root/'report').iterdir()},{'manifest.json'});self.assertEqual(source.read_bytes(),before)

    def test_source_hash_fresh_output_and_opaque_dimensions_are_not_relaxed(self):
        with tempfile.TemporaryDirectory(prefix='bc7-boundary-') as td:
            root=Path(td);source=root/'input.jpg';Image.new('RGB',(16,16)).save(source);out=root/'output'
            with self.assertRaisesRegex(ValueError,'SHA'):prepare(source,'0'*64,out,NODE,profile='mode1-6')
            self.assertFalse(out.exists());out.mkdir()
            with self.assertRaisesRegex(ValueError,'Fresh'):prepare(source,hashlib.sha256(source.read_bytes()).hexdigest(),out,NODE)


if __name__=='__main__':unittest.main()
