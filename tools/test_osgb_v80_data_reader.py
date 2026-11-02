import hashlib
import io
import struct
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image
from osgb_v80_data_reader import DataReader, UnsupportedOSGB
from osgb_v80_memory_frame import build_frame
from osgb_memory_reader import parse_frame
from osgb_v80_source_reader import PinnedOSGBDataReader

I=lambda v:struct.pack('<I',v)
B=lambda v:bytes([v])
F=lambda *v:struct.pack('<'+'f'*len(v),*v)
S=lambda v:I(len(v))+v
COMMON=lambda name=b'':S(name)+I(2)+B(0)
OBJ=lambda kind,identifier,body:S(kind.encode())+I(identifier)+COMMON()+body
NODE=lambda mask=0xffffffff:B(0)*5+B(1)+I(mask)+B(0)


def fixture(*,positions=None,uv=None,indices=(0,1,2),filename=b'original.jpg',filter=9729,mask=0xffffffff,colors=False):
    image=Image.new('RGB',(4,4));image.putdata([(i*11,i*7,255-i*9) for i in range(16)])
    stream=io.BytesIO();image.save(stream,format='JPEG',quality=100,subsampling=0);image.close();jpeg=stream.getvalue()
    source_image=I(6)+S(filename)+I(0)+I(1)+I(len(jpeg))+jpeg+COMMON()
    texture=B(0)*2+b''.join(B(1)+I(v) for v in (10496,10496,10496,filter,9729))+F(1)+bytes([1,0,0,1])+struct.pack('<4d',0,0,0,0)+I(0)+I(0)+B(0)*3+B(0)+I(515)+I(6409)+F(0)+B(1)+source_image+I(0)*2
    texture=OBJ('osg::Texture2D',5,texture)
    state=B(0)*2+B(1)+I(1)+I(1)+I(3553)+I(1)+B(1)+I(1)+I(1)+texture+I(0)+B(0)+I(0)*3+S(b'')+B(1)+B(0)*2
    state=OBJ('osg::StateSet',4,state)
    positions=positions or [(-0.0,0.0,0.0),(1.0,0.0,0.0),(0.0,1.0,0.0)]
    uv=uv or [(0.0,0.0),(1.0,0.0),(0.0,1.0)]
    position_raw=b''.join(F(*p) for p in positions);uv_raw=b''.join(F(*p) for p in uv);index_raw=b''.join(I(i) for i in indices)
    def array_data(identifier,kind,count,raw):return B(1)+I(identifier)+I(kind)+I(count)+raw+B(0)+I(4)+I(0)
    color_data=B(1)+array_data(3,17,1,F(.5,.5,.5,1)) if colors else B(0)
    geometry=B(1)+state+B(0)*3+bytes([1,0,0])+B(0)*4+I(1)+I(54)+I(4)+I(len(indices))+index_raw
    geometry+=B(1)+array_data(1,16,len(positions),position_raw)+B(0)+color_data+B(0)*2+B(1)+I(1)+array_data(2,15,len(uv),uv_raw)+B(0)+B(1)
    geometry=OBJ('osg::Geometry',3,geometry)
    root=OBJ('osg::Geode',1,NODE(mask)+B(1)+I(1)+geometry)
    return bytes.fromhex('a10e916c4545fb1a')+I(1)+I(80)+I(0)+S(b'0')+root,dict(jpeg=jpeg,positions=position_raw,uv=uv_raw,indices=index_raw)


class OSGBDataTests(unittest.TestCase):
    def setUp(self):self.raw,self.expected=fixture();self.node='Tile_1/Tile_1_L19_0uuuu.osgb'
    def test_complete_structural_decode_and_exact_consumption(self):
        r=DataReader(self.raw);root=r.parse();self.assertEqual(root['class'],'osg::Geode');self.assertEqual(r.offset,len(self.raw));self.assertEqual(len(r.arrays),2)
        self.assertEqual([v['encoded'] for v in r.objects.values() if v['class']=='osg::Image'],[self.expected['jpeg']])
    def test_every_truncated_prefix_fails_instead_of_returning_partial_geometry(self):
        for n in range(len(self.raw)):
            with self.subTest(size=n),self.assertRaises(UnsupportedOSGB):DataReader(self.raw[:n]).parse()
    def test_mutable_input_oversize_and_trailing_bytes_are_rejected(self):
        for value in (bytearray(self.raw),memoryview(self.raw),b'',self.raw+b'x'):
            with self.assertRaises(UnsupportedOSGB):DataReader(value).parse()
        with self.assertRaises(UnsupportedOSGB):DataReader(self.raw,maximum=len(self.raw)-1)
    def test_signature_version_domains_and_compression_are_not_guessed(self):
        for start,raw in ((0,b'badMAGIC'),(8,I(2)),(12,I(81)),(16,I(4)),(24,b'x')):
            changed=self.raw[:start]+raw+self.raw[start+len(raw):]
            with self.assertRaises(UnsupportedOSGB):DataReader(changed).parse()
    def test_unknown_class_and_noncanonical_boolean_fail_closed(self):
        raw=self.raw.replace(b'osg::Geode',b'osg::Evilx',1)
        with self.assertRaises(UnsupportedOSGB):DataReader(raw).parse()
        # First object common data ends after the empty name, variance and user-data flag.
        offset=25+4+len(b'osg::Geode')+4+4+4
        changed=self.raw[:offset]+b'\xff'+self.raw[offset+1:]
        with self.assertRaises(UnsupportedOSGB):DataReader(changed).parse()
    def test_nonfinite_position_and_uv_arrays_are_rejected(self):
        for options in ({'positions':[(float('nan'),0,0),(1,0,0),(0,1,0)]},{'uv':[(0,float('inf')),(1,0),(0,1)]}):
            raw,_=fixture(**options)
            with self.assertRaises(UnsupportedOSGB):DataReader(raw).parse()
    def test_original_array_bytes_and_negative_zero_survive_frame_validation(self):
        frame,audit=build_frame(self.raw,self.node);d,p=parse_frame(frame,self.node,len(self.raw));mesh=d['meshes'][0]
        for key in ('positions','uv','indices'):
            segment=mesh[key];self.assertEqual(p[segment['offset']:segment['offset']+segment['bytes']],self.expected[key])
        self.assertEqual(audit['sourceSHA256'],hashlib.sha256(self.raw).hexdigest());self.assertEqual((d['vertices'],d['triangles']),(3,1))
    def test_jpeg_rows_follow_bottom_left_source_storage_without_uv_rewrite(self):
        frame,_=build_frame(self.raw,self.node);d,p=parse_frame(frame,self.node,len(self.raw));image=d['images'][0]
        with Image.open(io.BytesIO(self.expected['jpeg'])) as loaded:
            flipped=loaded.transpose(Image.Transpose.FLIP_TOP_BOTTOM);rgba=flipped.convert('RGBA')
            try:expected=rgba.tobytes()
            finally:rgba.close();flipped.close()
        self.assertEqual(p[image['offset']:image['offset']+image['bytes']],expected);self.assertEqual(image['sourceOrigin'],'bottom_left')
    def test_non_utf8_embedded_names_are_opaque_and_not_external_file_reads(self):
        raw,_=fixture(filename=b'C:/does-not-exist/\xff\xc2.jpg');r=DataReader(raw);r.parse()
        self.assertEqual(next(v for v in r.objects.values() if v['class']=='osg::Image')['filenameBytes'],b'C:/does-not-exist/\xff\xc2.jpg')
        with patch('builtins.open',side_effect=AssertionError('No external source-file reads')):build_frame(raw,self.node)
    def test_invalid_indices_uv_count_and_source_colors_require_explicit_support(self):
        for options in ({'indices':(0,1,3)},{'indices':(0,1)},{'uv':[(0,0),(1,0)]},{'colors':True}):
            raw,_=fixture(**options)
            with self.assertRaises(UnsupportedOSGB):build_frame(raw,self.node)
    def test_masked_nodes_and_unimplemented_mip_sampling_are_not_dropped(self):
        for options in ({'mask':0},{'filter':9987}):
            raw,_=fixture(**options)
            with self.assertRaises(UnsupportedOSGB):build_frame(raw,self.node)
    def test_names_and_memory_budget_cannot_escape_the_declared_contract(self):
        for node in ('Tile_2/Tile_1_L19_0uuuu.osgb','../source.osgb','Tile_1/../../secret'):
            with self.assertRaises(UnsupportedOSGB):build_frame(self.raw,node)
        for maximum in (True,0,16,129*1048576):
            with self.assertRaises(UnsupportedOSGB):build_frame(self.raw,self.node,maximum)


class PinnedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'Data';folder=self.root/'Tile_1';folder.mkdir(parents=True)
        self.name='Tile_1_L19_0uuuu.osgb';self.source=folder/self.name
        self.raw,_=fixture();self.source.write_bytes(self.raw)
        self.pin=dict(bytes=len(self.raw),sha256=hashlib.sha256(self.raw).hexdigest());self.reader=PinnedOSGBDataReader(self.root)
    def test_actual_callable_uses_original_bytes_and_no_subprocess_or_asset_writes(self):
        before=(self.source.read_bytes(),self.source.stat().st_mtime_ns)
        with patch('subprocess.run',side_effect=AssertionError('No native launch')):
            desc,payload=self.reader(1,self.name,self.pin)
        self.assertEqual((desc['vertices'],desc['triangles']),(3,1));self.assertEqual(desc['sourceBytes'],len(self.raw));self.assertGreater(len(payload),0)
        self.assertEqual(before,(self.source.read_bytes(),self.source.stat().st_mtime_ns))
        self.assertEqual([p.name for p in self.source.parent.iterdir()],[self.name])
    def test_source_sha_and_size_changes_are_rejected_without_repair(self):
        self.source.write_bytes(self.raw[:-1]+b'\0')
        with self.assertRaisesRegex(ValueError,'SHA differs'):self.reader(1,self.name,self.pin)
        changed=self.source.read_bytes();self.assertNotEqual(changed,self.raw)
        self.source.write_bytes(self.raw+b'x')
        with self.assertRaisesRegex(ValueError,'size differs'):self.reader(1,self.name,self.pin)
        self.assertEqual(self.source.read_bytes(),self.raw+b'x')
    def test_paths_and_unpinned_source_requests_are_rejected(self):
        for tile,name,pin in ((True,self.name,self.pin),(1,'../'+self.name,self.pin),(2,self.name,self.pin),(1,self.name,{'bytes':True,'sha256':self.pin['sha256']}),(1,self.name,{'bytes':len(self.raw),'sha256':'bad'})):
            with self.assertRaises(ValueError):self.reader(tile,name,pin)
    def test_implementation_change_is_detected_before_source_decode(self):
        other=Path(self.temp.name)/'modified.py';other.write_text('changed','utf-8');self.reader.code['reader']=other
        with self.assertRaisesRegex(ValueError,'implementation changed'):self.reader(1,self.name,self.pin)
    def test_reparse_source_path_is_not_followed(self):
        with patch.object(Path,'is_symlink',return_value=True),self.assertRaises(ValueError):self.reader(1,self.name,self.pin)
    def test_runtime_identity_is_deterministic_and_requires_explicit_data_root(self):
        self.assertEqual(self.reader.identity,PinnedOSGBDataReader(self.root).identity)
        with self.assertRaises(ValueError):PinnedOSGBDataReader(self.root.parent)


if __name__=='__main__':unittest.main()
