"""Regression for a real 2048x512 source rejected by the gutter-only recipe."""
import tempfile,unittest,json
from pathlib import Path
import native_atlas_recipe as recipe
import native_edge_clamp_atlas as edge

class EdgeClampTests(unittest.TestCase):
    def test_original_sources_are_assigned_exactly_once_without_rescaling(self):
        sizes={'regular':(512,512),'wide':(2048,512),'tall':(512,2048),'square':(2048,2048)}
        layouts=recipe.layouts(sizes,recipe.EDGE_CLAMP)
        names=[name for mapping,side in layouts for name in mapping]
        self.assertCountEqual(names,sizes)
        for mapping,side in layouts:
            self.assertLessEqual(side,2048)
            for name,(x,y,w,h) in mapping.items():
                self.assertEqual((w,h),sizes[name])
                self.assertGreaterEqual(min(x,y),0)
                self.assertLessEqual(max(x+w,y+h),side)
                if max(w,h)+8>2048:self.assertEqual(len(mapping),1)

    def test_legacy_rejection_and_regular_tight_layout_are_preserved(self):
        for policy in (recipe.LEGACY,recipe.TIGHT):
            with self.assertRaises(ValueError):recipe.layouts({'source':(2048,512)},policy)
        regular={'one':(512,512),'two':(512,256)}
        self.assertEqual(recipe.layouts(regular,recipe.EDGE_CLAMP),recipe.layouts(regular,recipe.TIGHT))

    def test_rejects_unbounded_or_malformed_dimensions(self):
        for size in ((2049,512),(512,4096),(0,1),(-1,5),(True,512),(2048,2.5)):
            with self.subTest(size=size),self.assertRaises(ValueError):edge.layouts({'source':size})

    def test_dedicated_page_preserves_every_source_pixel_and_extends_borders(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.png'
            for dims in ((2048,512),(512,2048),(2048,2048),(2041,16)):
                source=Image.new('RGB',dims)
                # A non-uniform pattern detects any crop, rescale, or axis reversal.
                source.putdata([((x*13+y*7)%256,(x//7)%256,(y//3)%256) for y in range(dims[1]) for x in range(dims[0])])
                source.save(path)
                mapping,side=edge.layouts({path:dims})[0]
                actual=edge.image(mapping,side);x,y,w,h=mapping[path]
                self.assertEqual(actual.crop((x,y,x+w,y+h)).tobytes(),source.tobytes())
                for px,py in ((0,0),(side-1,0),(0,side-1),(side-1,side-1),(100,side-1)):
                    expected=source.getpixel((max(0,min(w-1,px-x)),max(0,min(h-1,py-y))))
                    self.assertEqual(actual.getpixel((px,py)),expected)

    def test_clamp_sampler_is_explicit_and_legacy_gltf_stays_unchanged(self):
        old={'textures':[{'source':0}]};recipe.apply_sampler(old,recipe.LEGACY)
        self.assertEqual(old,{'textures':[{'source':0}]})
        new={'textures':[{'source':0}]};recipe.apply_sampler(new,recipe.EDGE_CLAMP)
        self.assertEqual(new['textures'][0]['sampler'],0)
        self.assertEqual(new['samplers'][0]['wrapS'],33071)
        self.assertEqual(new['samplers'][0]['wrapT'],33071)

    def test_distinct_cache_binding_and_source_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);recipe.bind_cache(cache,recipe.EDGE_CLAMP)
            before=(cache/'.atlas_recipe.json').read_bytes()
            with self.assertRaises(ValueError):recipe.bind_cache(cache,recipe.TIGHT)
            self.assertEqual((cache/'.atlas_recipe.json').read_bytes(),before)
        self.assertIn('edge_layout_sha256',recipe.stamp(recipe.EDGE_CLAMP))

    def test_shared_edge_touching_page_is_rejected(self):
        with self.assertRaises(ValueError):edge.image({'a':(0,0,2048,512),'b':(0,512,1,1)},2048)

if __name__=='__main__':unittest.main()
