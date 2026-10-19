import copy
import unittest
from build_portable_source_package import merge_layers

def document(layer_id, feature_id):
    return {"schema":"hongtu.landscape.layers.v1", "scene":"zhumadian",
        "coordinates":{"srs":"EPSG:32650", "unit":"metre", "axes":"east,north,up", "origin":[1,2,3]},
        "layers":[{"id":layer_id,"name":layer_id,"visible":True,"locked":False,
            "features":[{"id":feature_id,"name":feature_id,"type":"point","positions":[[4,5,6]],
                         "style":{"markerSize":32,"label":"original user label"}}]}]}

class MergeUserLayers(unittest.TestCase):
    def test_exact_user_layers_and_source_documents_are_preserved(self):
        published,user=document("enterprise","company"),document("road","crossing")
        before=copy.deepcopy((published,user));merged=merge_layers(published,user)
        self.assertEqual(merged["layers"],[*published["layers"],*user["layers"]])
        self.assertEqual((published,user),before)
        merged["layers"][1]["features"][0]["positions"][0][0]=999
        self.assertEqual((published,user),before)
    def test_identical_existing_layer_is_not_duplicated(self):
        published=document("road","crossing")
        self.assertEqual(merge_layers(published,copy.deepcopy(published)),published)
    def test_different_coordinate_frames_are_refused(self):
        published,user=document("enterprise","company"),document("road","crossing")
        user["coordinates"]["origin"][0]=9
        with self.assertRaisesRegex(ValueError,"coordinate frames differ"):
            merge_layers(published,user)
    def test_conflicting_layer_identity_is_not_silently_renamed(self):
        with self.assertRaisesRegex(ValueError,"layer identity"):
            merge_layers(document("same","one"),document("same","other"))
    def test_conflicting_feature_identity_is_not_silently_rebound(self):
        with self.assertRaisesRegex(ValueError,"feature identity"):
            merge_layers(document("enterprise","same"),document("road","same"))

if __name__ == "__main__":
    unittest.main()
