import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from osgb_memory_pages import build_bundle, canonical, sha
from test_source_memory_store import Reader

R = 'Tile_1_L16_0u.osgb'
A = 'Tile_1_L17_0uu.osgb'
B = 'Tile_1_L17_0u0.osgb'
A1 = 'Tile_1_L18_0uuu.osgb'
A2 = 'Tile_1_L18_0uu0.osgb'
F = 'Tile_1_L19_0uuuu.osgb'


def catalog():
    return dict(tile_id=1, root=R, source_directory='assets/驻马店园区/Data/Tile_1', nodes=[
        dict(name=name, children=children, bytes=100, sha256=str(i)*64)
        for i, (name, children) in enumerate([(R, [A, B]), (A, [A1, A2]), (B, []),
                                             (A1, [F]), (A2, []), (F, [])])])


class IndexedBundles(unittest.TestCase):
    def build(self, names, parent=None, reader=None):
        return build_bundle(1, catalog(), reader or Reader(), selection=names, parent=parent, recipe_identity='indexed-test')

    def test_direct_selected_sources_without_decoding_intermediate_levels(self):
        class Observed(Reader):
            def __init__(self):
                super().__init__()
                self.names = []
            def __call__(self, tile, name, record):
                self.names.append(name)
                return super().__call__(tile, name, record)
        reader = Observed()
        bundle = self.build([F, A2, B], reader=reader)
        self.assertEqual(set(reader.names), {F, A2, B})
        self.assertEqual(3, reader.calls)
        marker = bundle.marker()
        self.assertEqual('zhumadian.osgb_source_cut.v3', marker['schema'])
        self.assertTrue(marker['complete_source_cut'])
        self.assertEqual((1, 3), (marker['min_depth'], marker['max_depth']))
        self.assertEqual(9, marker['indices'])
        self.assertNotIn('complete_sibling_family', marker)

    def test_descendant_branch_is_complete_but_need_not_be_direct_siblings(self):
        bundle = self.build([F, A2], parent=A)
        marker = bundle.marker()
        self.assertEqual('zhumadian.osgb_source_descendants.v3', marker['schema'])
        self.assertEqual(A, marker['replacement_parent'])
        self.assertEqual(sha(A.encode()+b'\n'+canonical(sorted([F, A2])))[:16], marker['family_key'])
        self.assertEqual(sha(canonical(sorted([F, A2]))), marker['source_cut_key'])

    def test_holes_overlaps_foreign_branches_duplicate_and_parent_refused(self):
        for selected, parent in [([F], None), ([A, F, B], None), ([F, B], A),
                                 ([F, F, A2], A), ([A], A), ([A1], A), ([], None)]:
            with self.subTest(selected=selected, parent=parent):
                with self.assertRaises(ValueError):
                    self.build(selected, parent)

    def test_deterministic_order_and_isolation_from_original_catalog(self):
        original = catalog()
        before = copy.deepcopy(original)
        a = build_bundle(1, original, Reader(), selection=[F, A2], parent=A, recipe_identity='same')
        b = build_bundle(1, original, Reader(), selection=[A2, F], parent=A, recipe_identity='same')
        self.assertEqual(a.marker_json, b.marker_json)
        self.assertEqual(dict(a.resources), dict(b.resources))
        self.assertEqual(before, original)

    def test_vectorized_index_metrics_match_existing_original_triangle_metrics(self):
        from build_landscape_level_index import geometry_metrics
        from osgb_memory_pages import mesh_metrics, percentile
        from test_osgb_cropped_pages import CropProtocol
        desc, payload = CropProtocol().geometry()
        actual = geometry_metrics(desc, memoryview(payload))
        low, high, edges, texels = mesh_metrics(desc['meshes'][0], desc['images'][0], memoryview(payload))
        self.assertEqual(low, actual['boundsMin'])
        self.assertEqual(high, actual['boundsMax'])
        self.assertAlmostEqual(percentile(edges), actual['edgeP90'], places=12)
        self.assertAlmostEqual(percentile(texels), actual['texelP90'], places=12)


class LargeGeometryPlanning(unittest.TestCase):
    def test_mipmapped_geometry_splits_with_complete_images_and_exact_triangle_ownership(self):
        import array
        from unittest.mock import patch
        from osgb_cropped_pages import plan_mesh
        uv = array.array('f', [.2,.2,.8,.2,.2,.8]*4).tobytes()
        indices = array.array('I', range(12)).tobytes()
        mesh = dict(uv=dict(offset=0, bytes=len(uv), count=24),
                    indices=dict(offset=len(uv), bytes=len(indices), count=12),
                    sampler=dict(minFilter=9987, magFilter=9729, wrapS=33071, wrapT=33071))
        with patch('osgb_cropped_pages.MIB', 16):
            pages = plan_mesh(mesh, dict(width=2,height=2), memoryview(uv+indices))
        self.assertEqual(2, len(pages))
        self.assertEqual([0,1,2,3], sorted(t for ids, refs, crop in pages for t in ids))
        for ids, refs, crop in pages:
            self.assertEqual((0,0,2,2), crop)
            self.assertLessEqual(len(refs)*64+len(ids)*12+20, 32*16)


if __name__ == '__main__':
    unittest.main()
