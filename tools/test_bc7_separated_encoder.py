import json,struct,subprocess,unittest
from pathlib import Path
from PIL import Image
HERE=Path(__file__).parent;NODE=Path('D:/Program Files/nodejs/node.exe')
PROFILE='mode0-1-2-3-4-5-6'
def reference_decode(block):
    value=int.from_bytes(block,'little');pos=0
    def read(n):
        nonlocal pos
        out=(value>>pos)&((1<<n)-1);pos+=n;return out
    mode=0
    while read(1)==0:mode+=1
    if mode not in (4,5):raise ValueError('Separated modes only')
    rotation=read(2);selection=read(1) if mode==4 else 0;endpoints=[[0]*4 for _ in range(2)]
    def expand(q,bits):return (q<<(8-bits))|((q<<(8-bits))>>bits)
    for c in range(3):
        for e in range(2):endpoints[e][c]=expand(read(5 if mode==4 else 7),5 if mode==4 else 7)
    for e in range(2):endpoints[e][3]=expand(read(6 if mode==4 else 8),6 if mode==4 else 8)
    primary=[read(1 if i==0 else 2) for i in range(16)];secondary=[read((3 if mode==4 else 2)-int(i==0)) for i in range(16)]
    w2=[0,21,43,64];w3=[0,9,18,27,37,46,55,64];out=[]
    for i in range(16):
        rgb,alpha=(secondary[i],primary[i]) if selection else (primary[i],secondary[i]);rw=w3 if mode==4 and selection else w2;aw=w3 if mode==4 and not selection else w2
        pixel=[]
        for c in range(4):
            w=aw[alpha] if c==3 else rw[rgb];pixel.append(((64-w)*endpoints[0][c]+w*endpoints[1][c]+32)>>6)
        if rotation:pixel[3],pixel[rotation-1]=pixel[rotation-1],pixel[3]
        out.extend(pixel)
    if pos!=128:raise ValueError('Wrong separated block length')
    return bytes(out)
def encode(raw,width,height,profile=PROFILE):
    header=json.dumps([dict(level=0,width=width,height=height)]).encode();batch=b'MB7R'+struct.pack('<I',len(header))+header+raw
    run=subprocess.run([str(NODE),str(HERE/'bc7_mode6_cli.mjs'),'--profile='+profile],input=batch,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
    if run.returncode:raise AssertionError(run.stderr)
    return run.stdout
class SeparatedBc7Tests(unittest.TestCase):
    def test_all_mode4_mode5_rotations_and_index_selections_match_two_decoders(self):
        run=subprocess.run([str(NODE),str(HERE/'bc7_separated_probe.mjs')],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
        self.assertEqual(run.returncode,0,run.stderr);rows=json.loads(run.stdout);self.assertEqual(len(rows),48)
        for row in rows:
            with self.subTest(mode=row['mode'],rotation=row['rotation'],selection=row['selection'],seed=row['seed']):
                block=bytes.fromhex(row['encoded']);pillow=Image.frombytes('RGBA',(4,4),block,'bcn',(7,'BC7')).tobytes();self.assertEqual(pillow,reference_decode(block));self.assertEqual(pillow.hex(),row['reference']);self.assertTrue(all(pillow[i]==255 for i in range(3,64,4)))
    def test_separate_color_axes_select_new_modes_and_improve_source_error(self):
        pixels=bytes(v for y in range(4) for x in range(4) for v in (x*60+7,y*60+13,y*60+29,255))
        old=Image.frombytes('RGBA',(4,4),encode(pixels,4,4,'mode0-1-2-3-6'),'bcn',(7,'BC7')).tobytes();block=encode(pixels,4,4);new=Image.frombytes('RGBA',(4,4),block,'bcn',(7,'BC7')).tobytes()
        self.assertIn(block[0]&63,[16,48,32]);self.assertEqual(new,reference_decode(block));self.assertLess(sum((a-b)**2 for a,b in zip(new,pixels)),sum((a-b)**2 for a,b in zip(old,pixels)))
    def test_visible_pixels_of_partial_blocks_do_not_regress(self):
        for width,height in [(9,3),(3,3),(6,7),(1,1),(7,9)]:
            with self.subTest(width=width,height=height):
                raw=bytes(v for y in range(height) for x in range(width) for v in ((x*31+y*23)%256,(x*73+y*11)%256,(x*13+y*47)%256,255))
                old=Image.frombytes('RGBA',(width,height),encode(raw,width,height,'mode0-1-2-3-6'),'bcn',(7,'BC7')).tobytes();encoded=encode(raw,width,height);new=Image.frombytes('RGBA',(width,height),encoded,'bcn',(7,'BC7')).tobytes()
                self.assertEqual(encoded,encode(raw,width,height));self.assertTrue(all(new[i]==255 for i in range(3,len(new),4)))
                for by in range((height+3)//4):
                    for bx in range((width+3)//4):
                        offsets=[(y*width+x)*4+c for y in range(by*4,min(height,by*4+4)) for x in range(bx*4,min(width,bx*4+4)) for c in range(3)]
                        self.assertLessEqual(sum((new[i]-raw[i])**2 for i in offsets),sum((old[i]-raw[i])**2 for i in offsets))
if __name__=='__main__':unittest.main()
