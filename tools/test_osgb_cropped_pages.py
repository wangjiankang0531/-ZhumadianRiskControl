import copy,json,struct,unittest
from test_osgb_memory_reader import fixture,frame
from osgb_cropped_pages import parse_geometry_frame,parse_crop_frame,plan_mesh,page
from osgb_memory_reader import parse_frame
from osgb_memory_pages import mip_bytes
class CropProtocol(unittest.TestCase):
 def geometry(self):
  d,p=fixture();p=p[4:];d['schema']='zhumadian.osgb.geometry.v1';d['payloadBytes']=len(p)
  d['images'][0]={k:v for k,v in d['images'][0].items() if k not in ('offset','bytes','count')};d['images'][0]['pixelsOmitted']=True
  for k in ('positions','uv','indices'):d['meshes'][0][k]['offset']-=4
  return d,p
 def encoded(self,d,p,magic=b'ZMDGEO01'):
  raw=json.dumps(d).encode();return magic+struct.pack('<QQ',len(raw),len(p))+raw+p
 def test_explicit_geometry_only_and_legacy_separation(self):
  d,p=self.geometry();raw=self.encoded(d,p);a,b=parse_geometry_frame(raw,d['node'],100);self.assertEqual(bytes(b),p)
  with self.assertRaises(ValueError):parse_frame(raw,d['node'],100)
  original,pixels=fixture()
  with self.assertRaises(ValueError):parse_geometry_frame(frame(original,pixels),d['node'],100)
 def test_geometry_rejects_hidden_pixels_overlap_and_wrong_indices(self):
  for change in (lambda d:d['images'][0].update(bytes=4),lambda d:d['images'][0].update(pixelsOmitted=False),lambda d:d['meshes'][0]['uv'].update(offset=0)):
   d,p=self.geometry();change(d)
   with self.assertRaises(ValueError):parse_geometry_frame(self.encoded(d,p),d['node'],100)
 def test_large_geometry_metadata_does_not_invent_large_rgba(self):
  d,p=self.geometry();d['images'][0].update(width=4096,height=4096);a,b=parse_geometry_frame(self.encoded(d,p),d['node'],100);self.assertEqual(len(b),72)
 def test_crop_exact_request_and_rejects_ambiguous_metadata(self):
  image=dict(width=16,height=16,sourceOrigin='bottom_left');crop=(2,3,2,1);pixels=bytes([1,2,3,255]*2)
  d=dict(schema='zhumadian.osgb.rgba_crop.v1',node='test',sourceBytes=100,sourceImage=0,sourceWidth=16,sourceHeight=16,sourceOrigin='bottom_left',rowOrder='source_storage',format='rgba8',crop=list(crop),payloadBytes=8,externalReadAttempts=0,writeAttempts=0)
  self.assertEqual(bytes(parse_crop_frame(self.encoded(d,pixels,b'ZMDROI01'),'test',100,0,image,crop)),pixels)
  for change in (lambda d:d.update(sourceImage=True),lambda d:d.update(writeAttempts=1),lambda d:d.update(sourceWidth=8),lambda d:d.update(extra=0),lambda d:d.update(crop=[2,4,2,1])):
   bad=copy.deepcopy(d);change(bad)
   with self.assertRaises(ValueError):parse_crop_frame(self.encoded(bad,pixels,b'ZMDROI01'),'test',100,0,image,crop)
 def test_page_uses_actual_one_mip_but_original_uv_and_world_texel_metric(self):
  d,p=fixture();d['images'][0].update(originalWidth=4,originalHeight=4,sourceRect=[1,2,1,1]);part,files,metrics=page(d,memoryview(p),d['meshes'][0],'part_000','Tile_1_L16_0u.osgb');self.assertEqual(part['source_image']['uv_transform'],[4,4,-1,-2]);self.assertEqual(part['gpu_payload_bytes'],208);self.assertEqual(files['geometry.bin'][0],p[4:]);self.assertAlmostEqual(metrics[3][0],.25)
 def test_large_single_triangle_seam_and_mipmapped_crop_refused(self):
  d,p=fixture();image=dict(width=4096,height=4096);m=d['meshes'][0]
  with self.assertRaisesRegex(ValueError,'seam'):plan_mesh(m,image,memoryview(p))
  m['sampler']['minFilter']=9987
  with self.assertRaisesRegex(ValueError,'mip'):plan_mesh(m,image,memoryview(p))
class ReaderDispatch(unittest.TestCase):
 def test_ordinary_bounded_source_uses_one_full_frame_and_exact_arrays(self):
  from osgb_cropped_pages import PinnedCropReader
  d,p=fixture();calls=[];reader=PinnedCropReader.__new__(PinnedCropReader)
  reader._invoke=lambda node,record,mode=None:(calls.append(mode) or frame(d,p))
  actual,data=reader(1,'Tile_1_L16_0u.osgb',{'bytes':100})
  self.assertEqual(calls,[None]);self.assertEqual(bytes(data),p)
  self.assertEqual(actual['images'][0]['sourceRect'],[0,0,1,1])
 def test_file_or_security_failures_never_fall_back_to_another_mode(self):
  from osgb_cropped_pages import PinnedCropReader
  for error in (PermissionError('blocked'),RuntimeError('unexpected reader failure')):
   calls=[];reader=PinnedCropReader.__new__(PinnedCropReader)
   def invoke(node,record,mode=None):calls.append(mode);raise error
   reader._invoke=invoke
   with self.assertRaises(type(error)):reader(1,'Tile_1_L16_0u.osgb',{'bytes':100})
   self.assertEqual(calls,[None])
 def test_unreferenced_vertices_are_compacted_from_verified_ram_without_more_helper_calls(self):
  from osgb_cropped_pages import PinnedCropReader
  d,_=fixture();p=struct.pack('<4B12f8f3I',20,40,60,255,0,0,0,1,0,0,0,1,0,1,1,0,0,0,1,0,0,1,1,1,0,1,2)
  d['vertices']=4;d['payloadBytes']=len(p);m=d['meshes'][0];m['positions'].update(bytes=48,count=12);m['uv'].update(offset=52,bytes=32,count=8);m['indices'].update(offset=84)
  calls=[];reader=PinnedCropReader.__new__(PinnedCropReader);reader._invoke=lambda node,record,mode=None:(calls.append(mode) or frame(d,p))
  actual,data=reader(1,'Tile_1_L16_0u.osgb',{'bytes':100});self.assertEqual(calls,[None]);self.assertEqual(actual['vertices'],3);self.assertEqual(actual['triangles'],1)
if __name__=='__main__':unittest.main()
