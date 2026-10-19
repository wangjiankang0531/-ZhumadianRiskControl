import unittest
import numpy as np
from ground_enterprise_distribution import heights_on_triangles
class GroundTests(unittest.TestCase):
 def test_sloped_surface_interpolation_and_outside(self):
  v=np.array([[0,0,2],[10,0,12],[0,10,22]],float);idx=np.array([0,1,2]);self.assertEqual(heights_on_triangles(v,idx,[(2,3),(20,20)]),[10.0,None])
 def test_display_contact_uses_top_visible_surface_without_adding_height(self):
  v=np.array([[0,0,0],[10,0,0],[0,10,0],[0,0,8],[10,0,8],[0,10,8]],float);idx=np.arange(6);self.assertEqual(heights_on_triangles(v,idx,[(2,2)],batch=1),[8.0])
 def test_vertical_and_degenerate_faces_do_not_invent_ground(self):
  v=np.array([[0,0,0],[0,0,10],[0,10,10]],float);self.assertEqual(heights_on_triangles(v,np.array([0,1,2]),[(0,3)]),[None])
 def test_nonfinite_geometry_is_rejected(self):
  v=np.array([[0,0,0],[float('nan'),0,0],[0,10,0]]);self.assertRaises(ValueError,heights_on_triangles,v,np.array([0,1,2]),[(0,0)])
if __name__=='__main__':unittest.main()
