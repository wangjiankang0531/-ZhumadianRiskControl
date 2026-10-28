import copy,hashlib,io,json,struct,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from test_osgb_memory_reader import fixture
import osgb_memory_pages as original
import osgb_sampler_pages as sampler


def image_fixture(width=8,height=8,minimum=9729):
    d,p=fixture();old_image=d['images'][0];geometry=p[4:]
    pixels=bytes(v for y in range(height) for x in range(width) for v in (x*17%256,y*19%256,(x+y)*23%256,255))
    d['images'][0].update(width=width,height=height,bytes=len(pixels),count=len(pixels))
    for key in ('positions','uv','indices'):d['meshes'][0][key]['offset']+=len(pixels)-4
    d['meshes'][0]['sampler']['minFilter']=minimum;d['payloadBytes']=len(pixels)+len(geometry)
    return d,memoryview(pixels+geometry),pixels


class SamplerPages(unittest.TestCase):
    def compare(self,width,height,minimum):
        d,p,pixels=image_fixture(width,height,minimum);before=copy.deepcopy(d);raw=bytes(p)
        old,of,om=original.page(d,p,d['meshes'][0],'part_000','Tile_1_L16_0u.osgb')
        new,nf,nm=sampler.page(d,p,d['meshes'][0],'part_000','Tile_1_L16_0u.osgb')
        self.assertEqual(d,before);self.assertEqual(bytes(p),raw);self.assertEqual(om,nm)
        self.assertEqual(of,nf);self.assertEqual(old['files'],new['files'])
        self.assertEqual(old['vertices'],new['vertices']);self.assertEqual(old['indices'],new['indices'])
        image=new['source_image'];self.assertEqual(image['source_rect'],[0,0,width,height]);self.assertEqual(image['uv_transform'],[1,1,0,0])
        self.assertEqual(image['sampler'],old['source_image']['sampler'])
        with Image.open(io.BytesIO(nf['texture.png'][0])) as raster:self.assertEqual(raster.tobytes(),pixels)
        return old,new
    def test_linear_source_uses_one_full_resolution_level_and_identical_payloads(self):
        old,new=self.compare(8,8,9729)
        self.assertEqual(new['source_image']['mip_levels'],1)
        self.assertEqual(old['gpu_payload_bytes']-new['gpu_payload_bytes'],original.mip_bytes(8,8)-8*8*4)
    def test_nearest_source_also_keeps_one_level(self):
        old,new=self.compare(7,3,9728);self.assertEqual(new['source_image']['mip_levels'],1)
        self.assertEqual(new['gpu_payload_bytes'],new['vertices']*64+new['indices']*4+7*3*4)
    def test_mipmap_sampler_keeps_every_level_and_full_cost(self):
        for minimum in (9984,9985,9986,9987):
            with self.subTest(minimum=minimum):
                old,new=self.compare(8,4,minimum);self.assertEqual(new['source_image']['mip_levels'],4);self.assertEqual(old['gpu_payload_bytes'],new['gpu_payload_bytes'])
    def test_one_pixel_texture_does_not_claim_a_saving(self):
        old,new=self.compare(1,1,9729);self.assertEqual(old['gpu_payload_bytes'],new['gpu_payload_bytes'])
    def test_preexisting_crop_or_geometry_only_input_is_not_reinterpreted(self):
        for key,value in (('originalWidth',8),('sourceRect',[0,0,8,8]),('pixelsOmitted',False)):
            d,p,_=image_fixture();d['images'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):sampler.page(d,p,d['meshes'][0],'part_000','Tile_1_L16_0u.osgb')
        d,p,_=image_fixture();d['schema']='zhumadian.osgb.geometry.v1'
        with self.assertRaises(ValueError):sampler.page(d,p,d['meshes'][0],'part_000','Tile_1_L16_0u.osgb')
    def test_complete_root_and_family_keep_original_arrays_and_no_asset_io(self):
        d,p,_=image_fixture();names=['Tile_1_L16_0u.osgb','Tile_1_L17_0uu.osgb']
        catalog=dict(tile_id=1,source_directory='assets/驻马店园区/Data/Tile_1',root=names[0],nodes=[dict(name=n,children=[names[1]] if i==0 else [],level=16+i,sha256='a'*64,bytes=100) for i,n in enumerate(names)])
        def reader(tile,name,record):return {**d,'node':f'Tile_1/{name}'},p
        with patch('subprocess.run',side_effect=AssertionError('No helper execution allowed')):
            for kwargs in ({'depth':1},{'parent':names[0]}):
                old=original.build_bundle(1,catalog,reader,recipe_identity='a'*64,**kwargs);new=sampler.build_bundle(1,catalog,reader,recipe_identity='b'*64,**kwargs)
                marker=new.marker();self.assertEqual(marker['source_format'],'osgb_memory_png_crop_v2');self.assertEqual(len(marker['parts']),1)
                self.assertEqual(old.resources,new.resources);self.assertEqual(sum(p['indices'] for p in old.marker()['parts']),sum(p['indices'] for p in marker['parts']))
                self.assertEqual(marker['parts'][0]['source_image']['mip_levels'],1)
    def test_bounded_memory_store_uses_versioned_sampler_cost_and_matching_lease(self):
        from readonly_source_memory_store import MemorySourceStore
        d,p,_=image_fixture();name='Tile_1_L16_0u.osgb'
        catalog=dict(tile_id=1,source_directory='assets/驻马店园区/Data/Tile_1',root=name,nodes=[dict(name=name,children=['Tile_1_L17_0uu.osgb'],level=16,sha256='a'*64,bytes=100),dict(name='Tile_1_L17_0uu.osgb',children=[],level=17,sha256='a'*64,bytes=100)])
        class Catalogs:
            identity='a'*64
            def __call__(self,tile):return catalog
        class Reader:
            identity='b'*64
            def __call__(self,tile,name,record):return {**d,'node':f'Tile_1/{name}'},p
        store=MemorySourceStore(Catalogs(),Reader(),builder=sampler.build_bundle,builder_identity=sampler.builder_identity())
        try:
            plan=store.plan(1,depth=1,wait_ms=200);self.assertIsNotNone(plan)
            marker,digest=store.grant(1,depth=1);self.assertEqual(digest,plan['markerSHA256'])
            self.assertEqual(marker['parts'][0]['source_image']['mip_levels'],1)
            for file in marker['parts'][0]['files']:
                data,_=store.payload(marker['cache_lease'],'tile_1_depth_1','part_000',file['name'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),file['sha256'])
            self.assertTrue(store.release(marker['cache_lease']))
            with self.assertRaises(PermissionError):store.payload(marker['cache_lease'],'tile_1_depth_1','part_000','texture.png')
            self.assertFalse(store.audit()['assetWritesEnabled'])
        finally:store.close()

    def test_recipe_pins_adapter_and_existing_v2_page_implementation(self):
        value=sampler.builder_identity();self.assertRegex(value,r'^[0-9a-f]{64}$')
        with patch.object(sampler.Path,'read_bytes',return_value=b'changed-code'):
            self.assertNotEqual(value,sampler.builder_identity())


if __name__=='__main__':unittest.main()
