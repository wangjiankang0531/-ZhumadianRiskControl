import copy,unittest
from services.data import presentation

class EnterpriseLabelProjectionTests(unittest.TestCase):
    def feature(self):
        return {"name":"合成企业", "style":{}, "label":{"visible":True,"text":"企业资料\n待核实","fontPx":14,"color":"#FFFFFF","opacity":.8,"offset":[12,-16],"placement":"billboard","heightM":60}}
    def test_private_projection_preserves_sign_parameters_without_mutating_source(self):
        f=self.feature();before=copy.deepcopy(f);_,label=presentation(f,True)
        self.assertEqual(label,f['label']);self.assertEqual(f,before)
    def test_public_projection_does_not_expose_private_enterprise_card(self):
        _,label=presentation(self.feature(),False)
        self.assertNotIn('placement',label);self.assertNotIn('heightM',label);self.assertNotIn('企业资料',label['text'])
    def test_invalid_private_height_and_placement_rejected(self):
        for key,value in [('heightM',True),('heightM',None),('heightM',-1),('heightM',501),('heightM',float('inf')),('placement',None),('placement','unknown')]:
            f=self.feature();f['label'][key]=value
            with self.assertRaises(ValueError):presentation(f,True)
    def test_legacy_label_fields_remain_exact(self):
        f=self.feature();del f['label']['placement'];del f['label']['heightM'];self.assertEqual(presentation(f,True)[1],f['label'])
