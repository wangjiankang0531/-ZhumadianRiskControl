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
  m['sampler'].update(wrapS=10497,wrapT=10497)
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
class GeometryOnlyBudgetPreflight(unittest.TestCase):
 def test_large_source_refuses_oversized_combined_pixels_before_any_crop_read(self):
  from osgb_cropped_pages import PinnedCropReader,SourceImageNeedsCrop
  import array
  d,_=CropProtocol().geometry();uv=[]
  for y in range(8):
   for x in range(8):uv.extend((x/8,y/8,(x+1)/8,y/8,x/8,(y+1)/8))
  positions=array.array('f',[0.0]*(192*3)).tobytes();coords=array.array('f',uv).tobytes();indices=array.array('I',range(192)).tobytes();payload=positions+coords+indices
  d.update(vertices=192,triangles=64,payloadBytes=len(payload));d['images'][0].update(width=8192,height=8192)
  mesh=d['meshes'][0];mesh['positions']=dict(offset=0,bytes=len(positions),count=576);mesh['uv']=dict(offset=len(positions),bytes=len(coords),count=384);mesh['indices']=dict(offset=len(positions)+len(coords),bytes=len(indices),count=192);mesh['sampler'].update(wrapS=33071,wrapT=33071,minFilter=9729)
  calls=[];reader=PinnedCropReader.__new__(PinnedCropReader)
  def invoke(node,record,mode=None):
   calls.append(mode)
   if mode is None:raise SourceImageNeedsCrop('bounded source crop required')
   if mode=='--geometry-only':return CropProtocol().encoded(d,payload)
   raise AssertionError('RGBA must not be fetched for an impossible complete RAM plan')
  reader._invoke=invoke
  with self.assertRaisesRegex(ValueError,'unchanged RAM payload'):reader(1,'Tile_1_L16_0u.osgb',{'bytes':100})
  self.assertEqual([None,'--geometry-only'],calls)

class ClampBoundaryPlanning(unittest.TestCase):
 def test_clamped_source_borders_keep_original_uv_and_bilinear_pixels(self):
  import array,math
  from unittest.mock import patch
  coords=[(-.1,-.1),(.2,-.1),(-.1,.2),(.8,.8),(1.1,.8),(.8,1.1),(.8,-.1),(1.1,-.1),(1.1,.2),(-.1,.8),(.2,1.1),(-.1,1.1)]
  uv=array.array('f',[c for pair in coords for c in pair]).tobytes();indices=array.array('I',range(12)).tobytes();payload=memoryview(uv+indices)
  mesh=dict(uv=dict(offset=0,bytes=len(uv),count=24),indices=dict(offset=len(uv),bytes=len(indices),count=12),sampler=dict(minFilter=9729,magFilter=9729,wrapS=10496,wrapT=33071))
  image=[[float(y*16+x) for x in range(16)] for y in range(16)]
  def linear(data,u,v):
   h,w=len(data),len(data[0]);x=max(0,min(w-1,u*w-.5));y=max(0,min(h-1,v*h-.5));a,b=math.floor(x),math.floor(y);dx,dy=x-a,y-b
   return sum(data[min(h-1,b+j)][min(w-1,a+i)]*(dx if i else 1-dx)*(dy if j else 1-dy) for i in (0,1) for j in (0,1))
  with patch('osgb_cropped_pages.MIB',16):pages=plan_mesh(mesh,dict(width=16,height=16),payload)
  self.assertEqual(list(range(4)),sorted(t for ids,_,_ in pages for t in ids))
  original=struct.unpack('<24f',uv)
  for ids,refs,(x,y,w,h) in pages:
   cropped=[row[x:x+w] for row in image[y:y+h]]
   self.assertLessEqual(len(refs)*64+len(ids)*12+mip_bytes(w,h),512)
   for tri in ids:
    for a,b,c in ((1,0,0),(0,1,0),(0,0,1),(.2,.3,.5),(.5,.5,0)):
     u=sum(weight*original[(tri*3+k)*2] for k,weight in enumerate((a,b,c)));v=sum(weight*original[(tri*3+k)*2+1] for k,weight in enumerate((a,b,c)))
     self.assertAlmostEqual(linear(image,u,v),linear(cropped,(u*16-x)/w,(v*16-y)/h),places=10)

if __name__=='__main__':unittest.main()
