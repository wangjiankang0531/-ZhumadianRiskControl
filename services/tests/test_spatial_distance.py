import unittest,math
from services.spatial_distance import horizontal_distance

def feature(kind,points):return {'type':kind,'positions':points}
class SpatialDistanceTests(unittest.TestCase):
 def test_point_is_horizontal_local_metres_and_not_elevation_or_geographic_degrees(self):self.assertEqual(horizontal_distance([0,0,10000],feature('point',[[3,4,-10000]])),5)
 def test_long_line_midpoint_is_near_even_when_all_vertices_far(self):self.assertEqual(horizontal_distance([0,0,0],feature('line',[[-10000,10,0],[10000,10,100]])),10)
 def test_segment_clamps_to_endpoint_and_duplicate_vertices_are_finite(self):
  self.assertEqual(horizontal_distance([0,0,0],feature('line',[[3,4,0],[3,4,2],[6,8,0]])),5)
 def test_inside_region_and_edge_are_zero_and_outside_uses_closing_segment(self):
  ring=[[-10,-10,0],[10,-10,0],[10,10,0],[-10,10,0]]
  for points in [ring,list(reversed(ring)),ring+[ring[0]]]:
   self.assertEqual(horizontal_distance([0,0,100],feature('region',points)),0);self.assertEqual(horizontal_distance([-10,0,1],feature('region',points)),0);self.assertEqual(horizontal_distance([-13,0,0],feature('region',points)),3)
 def test_concave_notch_stays_outside_not_bbox_or_vertex_approximation(self):
  ring=[[0,0,0],[10,0,0],[10,10,0],[7,10,0],[7,3,0],[3,3,0],[3,10,0],[0,10,0]]
  self.assertEqual(horizontal_distance([5,8,0],feature('region',ring)),2);self.assertEqual(horizontal_distance([1,8,0],feature('region',ring)),0)
 def test_translation_and_submetre_distance_preserved(self):self.assertAlmostEqual(horizontal_distance([1e8,1e8,0],feature('line',[[1e8-1000,1e8+.125,0],[1e8+1000,1e8+.125,0]])),.125)
if __name__=='__main__':unittest.main()
