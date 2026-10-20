import math
import random
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from landscape_level_index import BoundsIndex, Camera, finalize_tile, intersects, select_cut


class LevelIndexTests(unittest.TestCase):
    def setUp(self):
        self.camera = Camera((0, 0, 0), (0, 1, 0), 90, 1, 100, 1, 100)

    @staticmethod
    def entry(i, low, high):
        return dict(id=i, boundsMin=low, boundsMax=high, level=i % 7)

    def test_edges_corners_crossing_near_and_enclosing_boxes_are_not_center_culled(self):
        entries = [self.entry(0, (8, 9, 8), (12, 11, 12)),
                   self.entry(1, (-12, 9, 8), (-8, 11, 12)),
                   self.entry(2, (-1, -1, -1), (1, 2, 1)),
                   self.entry(3, (-200, -200, -200), (200, 200, 200)),
                   self.entry(4, (30, 9, 30), (32, 11, 32)),
                   self.entry(5, (-1, -20, -1), (1, -10, 1))]
        actual, _ = BoundsIndex(entries).query(self.camera)
        self.assertEqual([0, 1, 2, 3], [e['id'] for e in actual])

    def test_far_and_tangent_planes(self):
        entries = [self.entry(0, (-1, 99, -1), (1, 100, 1)),
                   self.entry(1, (-1, 101, -1), (1, 102, 1)),
                   self.entry(2, (10, 10, 0), (10, 10, 0))]
        actual, _ = BoundsIndex(entries).query(self.camera)
        self.assertEqual([0, 2], [e['id'] for e in actual])

    def test_vertical_camera_and_wide_aspect(self):
        cam = Camera((0, 0, 10), (0, 0, 0), 50, 3, 100)
        self.assertEqual([1], [e['id'] for e in BoundsIndex([
            self.entry(1, (-1, -1, 0), (1, 1, 1))]).query(cam)[0]])

    def test_empty_index(self):
        self.assertEqual(([], {'bvhNodesVisited': 0, 'entryBoundsTested': 0}), BoundsIndex([]).query(self.camera))

    def test_random_bvh_matches_independent_corner_plane_oracle(self):
        rng = random.Random(13579)
        entries = []
        for i in range(10000):
            low = [rng.uniform(-2000, 2000) for _ in range(3)]
            high = [x+rng.uniform(0, 20) for x in low]
            entries.append(self.entry(i, low, high))
        index = BoundsIndex(entries)
        for _ in range(12):
            pos = tuple(rng.uniform(-500, 500) for _ in range(3))
            cam = Camera(pos, tuple(x+d for x, d in zip(pos, (0.2, 1, -0.1))), 40, 1.8, 720, .1, 150)
            planes = cam.planes()
            def oracle(e):
                corners = [tuple(e['boundsMax'][a] if mask & (1 << a) else e['boundsMin'][a]
                                 for a in range(3)) for mask in range(8)]
                return all(any(sum(x*n for x, n in zip(p, normal))+offset >= -1e-7 for p in corners)
                           for normal, offset in planes)
            expected = {e['id'] for e in entries if oracle(e)}
            actual, stats = index.query(cam)
            self.assertEqual(expected, {e['id'] for e in actual})
            self.assertLess(stats['entryBoundsTested'], len(entries)//8)

    def test_invalid_bounds_duplicate_identity_and_projection_refused(self):
        for entries in [[self.entry(0, (0, 0, 0), (-1, 0, 0))],
                        [self.entry(0, (0, 0, 0), (math.nan, 0, 0))],
                        [self.entry(0, (0, 0, 0), (1, 1, 1))]*2]:
            with self.assertRaises(ValueError):
                BoundsIndex(entries)
        with self.assertRaises(ValueError):
            Camera((0, 0, 0), (0, 0, 0), 50, 1, 100)

    def fixture(self):
        # Parent's own geometry is offscreen; its real descendant enters view.
        catalog = {'tile_id': 1, 'root': 'wrapper', 'nodes': [
            dict(name='wrapper', children=['p'], level=None),
            dict(name='p', children=['left', 'right'], level=16, sha256='p', bytes=1),
            dict(name='left', children=['fine'], level=17, sha256='left', bytes=2),
            dict(name='right', children=[], level=17, sha256='right', bytes=3),
            dict(name='fine', children=[], level=18, sha256='fine', bytes=4)]}
        def record(name, n, low, high, metric):
            return dict(sourceSHA256=name, sourceBytes=n, boundsMin=low, boundsMax=high,
                        edgeP90=metric, texelP90=metric/4)
        exact = {'p': record('p', 1, (100, 10, 0), (110, 20, 2), 20),
                 'left': record('left', 2, (-2, 10, -2), (2, 12, 2), 10),
                 'right': record('right', 3, (100, 10, 0), (110, 20, 2), 10),
                 'fine': record('fine', 4, (-1, 10, -1), (1, 12, 1), .1)}
        return catalog, exact

    def test_exact_subtree_envelope_includes_children_outside_parent(self):
        catalog, exact = self.fixture()
        tile = finalize_tile(catalog, exact)
        parent = next(n for n in tile['nodes'] if n['name'] == 'p')
        self.assertEqual([-2, 10, -2], parent['subtreeMin'])
        self.assertEqual([110, 20, 2], parent['subtreeMax'])

    def test_mixed_cut_is_complete_and_skips_intermediate_visible_tiers(self):
        from native_source_frontier import SourceForest
        catalog, exact = self.fixture()
        tile = finalize_tile(catalog, exact)
        cut, stats = select_cut(tile, self.camera)
        self.assertEqual(['fine', 'right'], cut)
        self.assertEqual(frozenset(cut), SourceForest(catalog).validate_cut(cut))
        self.assertEqual(4, stats['nodesVisited'])

    def test_outside_view_stays_coarse_and_depth_limit_is_honored(self):
        catalog, exact = self.fixture()
        tile = finalize_tile(catalog, exact)
        away = Camera((0, 0, 0), (0, -1, 0), 90, 1, 100)
        self.assertEqual(['p'], select_cut(tile, away)[0])
        self.assertEqual(['p'], select_cut(tile, self.camera, max_depth=1)[0])

    def test_partial_bounds_and_changed_source_never_become_runtime_index(self):
        catalog, exact = self.fixture()
        exact.pop('right')
        with self.assertRaises(ValueError):
            finalize_tile(catalog, exact)
        catalog, exact = self.fixture()
        exact['left']['sourceSHA256'] = 'changed'
        with self.assertRaises(ValueError):
            finalize_tile(catalog, exact)
        with self.assertRaises(ValueError):
            select_cut({'schema': 'zhumadian.level_bounds.tile.v1', 'complete': False}, self.camera)


class CoverageTierTests(unittest.TestCase):
    def test_exact_tier_scales_retain_terminal_branches(self):
        from native_source_frontier import SourceForest
        from seal_landscape_level_index import coverage_tiers
        from test_indexed_source_bundle import catalog,R,A,A1,A2,B,F
        nodes={name:dict(texelP90=value) for name,value in ((R,100),(A,50),(A1,20),(A2,10),(B,25),(F,1))}
        actual=coverage_tiers(SourceForest(catalog()),nodes)
        self.assertEqual([1,2,3],[v['depth'] for v in actual])
        self.assertEqual([2,3,3],[v['sourceCount'] for v in actual])
        self.assertEqual([50,25,25],[v['maxTexel'] for v in actual])

    def test_nonfinite_texture_scale_cannot_enter_initial_tier(self):
        from native_source_frontier import SourceForest
        from seal_landscape_level_index import coverage_tiers
        from test_indexed_source_bundle import catalog
        forest=SourceForest(catalog());nodes={name:dict(texelP90=float('nan')) for name in forest.nodes}
        with self.assertRaisesRegex(ValueError,'texture scale'):coverage_tiers(forest,nodes)

if __name__ == '__main__':
    unittest.main()
