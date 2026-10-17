import tempfile,unittest,struct
from pathlib import Path
import native_rectangular_atlas as rectangular
import native_atlas_recipe as recipe
import build_zhumadian_full_stage as geometry

class RectangularTests(unittest.TestCase):
    def test_full_width_and_height_use_rectangles_with_original_pixels(self):
        self.assertEqual(rectangular.layouts({'wide':(2048,512)})[0][1],(2048,520))
        self.assertEqual(rectangular.layouts({'tall':(512,2048)})[0][1],(520,2048))
        self.assertEqual(rectangular.layouts({'square':(2048,2048)})[0][1],(2048,2048))
        with tempfile.TemporaryDirectory() as tmp:
            from PIL import Image
            p=Path(tmp)/'source.png';im=Image.new('RGB',(2048,512));im.putdata([((x*5)%256,(y*7)%256,(x+y)%256) for y in range(512) for x in range(2048)]);im.save(p)
            mapping,extent=rectangular.layouts({p:im.size})[0]
            page=rectangular.image(mapping,extent);x,y,w,h=mapping[p]
            self.assertEqual(page.size,extent)
            self.assertEqual(page.crop((x,y,x+w,y+h)).tobytes(),im.tobytes())
            self.assertEqual(page.getpixel((2047,519)),im.getpixel((2047,511)))

    def test_rectangular_mip_bytes_match_independent_level_chain(self):
        for w,h in [(2048,520),(520,2048),(520,264),(2048,2048)]:
            levels=[];a,b=w,h
            while True:
                levels.append(a*b*4)
                if a==b==1:break
                a,b=max(1,a//2),max(1,b//2)
            self.assertEqual(recipe.mip_bytes((w,h)),sum(levels))
        self.assertLess(recipe.mip_bytes((2048,520)),recipe.mip_bytes(2048))
        for extent in [(0,512),(2049,512),(True,512),(),(1,2,3)]:
            with self.subTest(extent=extent),self.assertRaises(ValueError):recipe.extent(extent)

    def test_pixel_coordinates_and_triangles_survive_rectangular_uv_normalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            from PIL import Image
            p=Path(tmp);Image.new('RGB',(2048,512),(35,90,120)).save(p/'source.png');(p/'source.mtl').write_text('newmtl a\nmap_Kd source.png\n')
            obj=p/'source.obj';obj.write_text('mtllib source.mtl\nv 0 0 0\nv 4 0 0\nv 0 2 0\nvt 0 0\nvt 1 0\nvt 0 1\nusemtl a\nf 1/1 2/2 3/3\n')
            mapping={p/'source.png':(0,4,2048,512)}
            views,n,k,*_=geometry.write_geometry([obj],mapping,p/'rect.bin',atlas_extent=(2048,520))
            data=(p/'rect.bin').read_bytes();uvs=struct.unpack_from('<6f',data,views[2]['byteOffset'])
            self.assertEqual((n,k),(3,3))
            for i,(px,py) in enumerate([(0,516),(2048,516),(0,4)]):
                self.assertAlmostEqual(uvs[i*2]*2048,px,places=4)
                self.assertAlmostEqual(uvs[i*2+1]*520,py,places=4)
            self.assertEqual(struct.unpack_from('<9f',data,0),(0,0,0,4,0,0,0,2,0))

    def test_legacy_square_extent_and_sampler_binding_remain_explicit(self):
        self.assertEqual(recipe.extent(520),(520,520))
        self.assertEqual(recipe.policy(),recipe.LEGACY)
        gltf={'textures':[{'source':0}]};recipe.apply_sampler(gltf,recipe.RECTANGULAR)
        self.assertEqual(gltf['samplers'][0]['wrapS'],33071)
        self.assertIn('rectangular_layout_sha256',recipe.stamp(recipe.RECTANGULAR))

if __name__=='__main__':unittest.main()
