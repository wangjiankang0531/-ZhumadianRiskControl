import copy
import io
import json
import struct
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from PIL import Image
from osgb_memory_reader import parse_frame
from osgb_memory_gltf import MemoryGltf


def fixture():
    payload=struct.pack('<4B9f6f3I',20,40,60,255,0,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,1,2)
    d={'schema':'zhumadian.osgb.memory.v1','node':'Tile_1/Tile_1_L16_0u.osgb','sourceBytes':100,'payloadBytes':len(payload),'externalReadAttempts':0,'writeAttempts':0,'coordinates':'source_local_metres','uv':'source_unchanged','littleEndian':True,'vertices':3,'triangles':1,
       'images':[{'offset':0,'bytes':4,'count':4,'width':1,'height':1,'format':'rgba8','rowOrder':'source_storage','sourceOrigin':'bottom_left'}],
       'meshes':[{'positions':{'offset':4,'bytes':36,'count':9},'uv':{'offset':40,'bytes':24,'count':6},'indices':{'offset':64,'bytes':12,'count':3},'image':0,'unlit':True,'boundsMin':[0,0,0],'boundsMax':[1,1,0],'vertexColorsWhite':True,'sampler':{'wrapS':10496,'wrapT':10496,'minFilter':9729,'magFilter':9729}}]}
    return d,payload


def frame(d,p):
    text=json.dumps(d).encode();return b'ZMDOSGB1'+struct.pack('<QQ',len(text),len(p))+text+p


class MemoryProtocol(unittest.TestCase):
    def parse(self,d,p):return parse_frame(frame(d,p),'Tile_1/Tile_1_L16_0u.osgb',100)
    def test_valid_original_arrays(self):
        d,p=fixture();actual,data=self.parse(d,p);self.assertEqual(actual,d);self.assertEqual(bytes(data),p)
    def test_wrong_identity_and_access_modes(self):
        for key,value in [('node','Tile_2/wrong.osgb'),('sourceBytes',99),('writeAttempts',1),('externalReadAttempts',1),('externalReadAttempts',False),('littleEndian',False),('triangles',True)]:
            d,p=fixture();d[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):self.parse(d,p)
    def test_index_outside_geometry(self):
        d,p=fixture();bad=bytearray(p);struct.pack_into('<I',bad,64,3)
        with self.assertRaises(ValueError):self.parse(d,bad)
    def test_nonfinite_position(self):
        d,p=fixture();bad=bytearray(p);struct.pack_into('<f',bad,4,float('nan'))
        with self.assertRaises(ValueError):self.parse(d,bad)
    def test_overlapping_segments(self):
        d,p=fixture();d['meshes'][0]['uv']['offset']=4
        with self.assertRaises(ValueError):self.parse(d,p)
    def test_truncated_and_trailing_frame(self):
        d,p=fixture();raw=frame(d,p)
        for bad in [raw[:-1],raw+b'x',b'wrong'+raw[5:]]:
            with self.assertRaises(ValueError):parse_frame(bad,d['node'],100)
    def test_geometry_and_image_shape_mismatch(self):
        for mutate in [lambda d:d['images'][0].update(width=2),lambda d:d['meshes'][0]['uv'].update(count=5),lambda d:d['meshes'][0].update(vertexColorsWhite=False),lambda d:d.update(vertices=4)]:
            d,p=fixture();mutate(d)
            with self.assertRaises(ValueError):self.parse(d,p)
    def test_lossless_gltf_does_not_include_raw_image_in_geometry(self):
        d,p=fixture();before=copy.deepcopy(d);builder=MemoryGltf('qa');builder.add(d,memoryview(p));resources,summary=builder.finish();g=json.loads(resources['qa.gltf'][0]);image=Image.open(io.BytesIO(resources['qa_texture_0.png'][0]));self.assertEqual(image.convert('RGBA').tobytes(),p[:4]);self.assertEqual(resources['qa.bin'][0],p[4:]);self.assertEqual(summary['triangles'],1);self.assertEqual(g['samplers'][0]['wrapS'],33071);self.assertEqual(d,before)
    def test_duplicate_source_and_capacity_rejected(self):
        d,p=fixture();builder=MemoryGltf('qa');builder.add(d,memoryview(p))
        with self.assertRaises(ValueError):builder.add(d,memoryview(p))
        with self.assertRaises(ValueError):MemoryGltf('qa',max_bytes=4).add(d,memoryview(p))
    def test_completed_frontier_is_sealed(self):
        d,p=fixture();builder=MemoryGltf('qa');builder.add(d,memoryview(p));resources,_=builder.finish()
        with self.assertRaises(ValueError):builder.add(d,memoryview(p))
        with self.assertRaises(ValueError):builder.finish()
        with self.assertRaises(TypeError):resources['unverified.bin']=(b'x','application/octet-stream')
    def test_unsupported_sampler_not_silently_changed(self):
        with self.assertRaises(ValueError):MemoryGltf.sampler({'wrapS':33069,'wrapT':10496,'minFilter':9729,'magFilter':9729})

if __name__=='__main__':unittest.main()
