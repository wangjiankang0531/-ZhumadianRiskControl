import json,re,subprocess,struct,unittest
from pathlib import Path
from PIL import Image
HERE=Path(__file__).parent;NODE=Path('D:/Program Files/nodejs/node.exe')
TABLE=(HERE/'bc7_three_subset_partitions.mjs').read_text()
def array(name):return json.loads(re.search(name+r'=Object.freeze\((\[[^;]+\])\)',TABLE)[1])
TWO=(HERE/'bc7_partitions.mjs').read_text();P2=json.loads(re.search(r'BC7_PARTITION2=Object.freeze\((\[[^;]+\])\)',TWO)[1]);A2=json.loads(re.search(r'BC7_ANCHOR2=Object.freeze\((\[[^;]+\])\)',TWO)[1])
PARTITION=array('BC7_PARTITION3');A32=array('BC7_ANCHOR32');A33=array('BC7_ANCHOR33')
def independent_decode(block):
    value=int.from_bytes(block,'little');pos=0
    def read(n):
        nonlocal pos
        out=(value>>pos)&((1<<n)-1);pos+=n;return out
    mode=0
    while read(1)==0:mode+=1
    if mode not in [0,2,3]:raise ValueError('Only extra opaque modes')
    partition=read(4 if mode==0 else 6);endpoints=[[0]*3 for _ in range(4 if mode==3 else 6)]
    for c in range(3):
        for e in range(len(endpoints)):endpoints[e][c]=read(4 if mode==0 else 7 if mode==3 else 5)
    parity=[read(1) for _ in range(len(endpoints))] if mode in [0,3] else [0]*len(endpoints)
    for e in range(len(endpoints)):
        for c in range(3):
            q=endpoints[e][c]*2+parity[e] if mode in [0,3] else endpoints[e][c];endpoints[e][c]=q if mode==3 else (q<<3)|(q>>2)
    weights=[0,9,18,27,37,46,55,64] if mode==0 else [0,21,43,64];out=[]
    for i in range(16):
        subset=(P2[partition]>>i)&1 if mode==3 else (PARTITION[partition]>>(i*2))&3;anchor=i in ([0,A2[partition]] if mode==3 else [0,A32[partition],A33[partition]]);w=weights[read((3 if mode==0 else 2)-int(anchor))]
        out.extend(((64-w)*endpoints[subset*2][c]+w*endpoints[subset*2+1][c]+32)>>6 for c in range(3));out.append(255)
    if pos!=128:raise ValueError('Incorrect three-subset block length')
    return bytes(out)
def encode(raw,width,height,profile):
    header=json.dumps([dict(level=0,width=width,height=height)]).encode();batch=b'MB7R'+struct.pack('<I',len(header))+header+raw
    run=subprocess.run([str(NODE),str(HERE/'bc7_mode6_cli.mjs'),'--profile='+profile],input=batch,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
    if run.returncode:raise AssertionError(run.stderr)
    return run.stdout
class ThreeSubsetBc7Tests(unittest.TestCase):
    def test_every_mode0_mode2_mode3_partition_matches_two_independent_decoders(self):
        run=subprocess.run([str(NODE),str(HERE/'bc7_three_subset_probe.mjs')],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
        self.assertEqual(run.returncode,0,run.stderr);rows=json.loads(run.stdout);self.assertEqual(len(rows),144)
        for row in rows:
            with self.subTest(mode=row['mode'],partition=row['partition']):
                block=bytes.fromhex(row['encoded']);pillow=Image.frombytes('RGBA',(4,4),block,'bcn',(7,'BC7')).tobytes()
                self.assertEqual(pillow,independent_decode(block));self.assertEqual(pillow.hex(),row['reference']);self.assertTrue(all(pillow[i]==255 for i in range(3,64,4)))
    def test_known_normative_example_and_all_anchor_memberships(self):
        self.assertEqual((PARTITION[6]>>18)&3,1);self.assertEqual([A32[6],A33[6]],[15,3])
        for mask,a,b in zip(PARTITION,A32,A33):self.assertEqual(mask&3,0);self.assertEqual((mask>>(a*2))&3,1);self.assertEqual((mask>>(b*2))&3,2)
    def test_small_mip_per_block_error_cannot_regress_and_real_modes_are_selected(self):
        width=height=16
        raw=bytes(v for y in range(height) for x in range(width) for v in ((x*31+y*23)%256,(x*73+y*11)%256,(x*13+y*47)%256,255))
        old=encode(raw,width,height,'mode1-6');new=encode(raw,width,height,'mode0-1-2-3-6');self.assertEqual(new,encode(raw,width,height,'mode0-1-2-3-6'))
        count=0
        for i in range(16):
            before=Image.frombytes('RGBA',(4,4),old[i*16:(i+1)*16],'bcn',(7,'BC7')).tobytes();block=new[i*16:(i+1)*16];after=Image.frombytes('RGBA',(4,4),block,'bcn',(7,'BC7')).tobytes()
            if block[0]&1 or block[0]&7==4 or block[0]&15==8:count+=1;self.assertEqual(after,independent_decode(block))
            source=bytes(raw[((i//4*4+y)*width+i%4*4+x)*4+c] for y in range(4) for x in range(4) for c in range(4))
            self.assertLessEqual(sum((a-b)**2 for j,(a,b) in enumerate(zip(source,after)) if j%4!=3),sum((a-b)**2 for j,(a,b) in enumerate(zip(source,before)) if j%4!=3))
        self.assertGreater(count,0)
    def test_non_power_of_two_edges_remain_opaque_and_deterministic(self):
        width,height=9,3;raw=bytes(v for y in range(height) for x in range(width) for v in (x*27,y*83,(x*37+y*11)%256,255))
        encoded=encode(raw,width,height,'mode0-1-2-3-6');self.assertEqual(len(encoded),48)
        decoded=Image.frombytes('RGBA',(width,height),encoded,'bcn',(7,'BC7'));self.assertEqual(decoded.getextrema()[3],(255,255));self.assertEqual(encoded,encode(raw,width,height,'mode0-1-2-3-6'))
if __name__=='__main__':unittest.main()
