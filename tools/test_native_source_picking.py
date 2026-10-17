"""Reject incomplete or mismatched visible-family reference cuts."""
import copy
import unittest
from verify_native_source_picking import reconstruct_cut


class SourcePickReferenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {'root': 'r', 'nodes': [
            {'name': 'r', 'children': ['a', 'b'], 'sha256': 'r-sha'},
            {'name': 'a', 'children': ['a0', 'a1'], 'sha256': 'a-sha'},
            {'name': 'b', 'children': [], 'sha256': 'b-sha'},
            {'name': 'a0', 'children': [], 'sha256': 'a0-sha'},
            {'name': 'a1', 'children': [], 'sha256': 'a1-sha'},
        ]}
        self.records = {n['name']: dict(n, depth={'r':0,'a':1,'b':1,'a0':2,'a1':2}[n['name']], source_sha256=n['sha256']) for n in self.catalog['nodes']}
    def node(self, name):
        return copy.deepcopy(self.records[name])
    def test_nested_families_sorted_from_arbitrary_stats_order(self):
        families = [('a', [self.node('a0'), self.node('a1')]), ('r', [self.node('a'), self.node('b')])]
        self.assertEqual(reconstruct_cut(self.catalog, [self.node('r')], families), {'a0','a1','b'})
    def test_base_frontier_and_unrefined_sibling(self):
        self.assertEqual(reconstruct_cut(self.catalog, [self.node('a'),self.node('b')], [('a',[self.node('a0'),self.node('a1')])]), {'a0','a1','b'})
    def test_missing_sibling_rejected(self):
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[self.node('r')],[('r',[self.node('a')])])
    def test_base_hole_rejected(self):
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[self.node('a')],[])
    def test_hidden_ancestor_overlap_rejected(self):
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[self.node('r'),self.node('a')],[])
    def test_duplicate_family_rejected(self):
        family=('r',[self.node('a'),self.node('b')])
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[self.node('r')],[family,copy.deepcopy(family)])
    def test_source_hash_mismatch_rejected(self):
        node=self.node('r');node['source_sha256']='different-source'
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[node],[])
    def test_depth_and_child_metadata_mismatch_rejected(self):
        for key,value in [('depth',2),('children',['a']),('children',['a','b','b'])]:
            node=self.node('r');node[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):
                reconstruct_cut(self.catalog,[node],[])
    def test_duplicate_source_and_tree_cycle_rejected(self):
        with self.assertRaises(AssertionError):
            reconstruct_cut(self.catalog,[self.node('r'),self.node('r')],[])
        catalog=copy.deepcopy(self.catalog);catalog['nodes'][2]['children']=['r']
        with self.assertRaises(AssertionError):
            reconstruct_cut(catalog,[self.node('r')],[])


if __name__=='__main__':
    unittest.main()