import copy
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from tools.import_enterprise_distribution import read_points, read_enterprises, build_distribution, transformer, ORIGIN


def point():
    return {"no": 1, "name": "合成企业有限公司", "type": "危化生产", "src": "无", "craft": "—", "chem": "—", "status": "在建", "addr": "合成地址", "acc": "低", "wgs": [117, 0], "gcj": [117.006, -.002]}


def table():
    return {1: ["1", "合成企业有限", "危化生产", "无", "—", "—", "在建"]}


class Projection:
    def transform(self, lon, lat, **kwargs):
        return ORIGIN[0]+10, ORIGIN[1]+20


class EnterpriseImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def html(self, data):
        p=self.root/'source.html'
        p.write_text('<script>throw new Error("must not execute");var DATA = '+json.dumps(data)+';</script>',encoding='utf-8')
        return p
    def test_json_points_parse_without_executing_html(self):
        self.assertEqual(read_points(self.html([point()])),[point()])
    def test_gcj_only_points_duplicate_ids_bool_and_nonfinite_rejected(self):
        for change in [lambda p:p.pop('wgs'),lambda p:p.update(no=True),lambda p:p.update(wgs=[float('nan'),0]),lambda p:p.update(wgs=[32,114])]:
            p=point();change(p)
            with self.assertRaises(ValueError):read_points(self.html([p]))
        with self.assertRaises(ValueError):read_points(self.html([point(),point()]))
    def test_document_blank_trailing_row_ignored_but_partial_row_rejected(self):
        def write(last):
            rows=[['序号','企业名称','企业类型','重大危险源情况','重点监管工艺','危化品','状态'],*table().values(),last]
            xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>'+''.join('<w:tr>'+''.join('<w:tc><w:p><w:r><w:t>'+v+'</w:t></w:r></w:p></w:tc>' for v in row)+'</w:tr>' for row in rows)+'</w:tbl></w:body></w:document>'
            p=self.root/'source.docx'
            with ZipFile(p,'w') as z:z.writestr('word/document.xml',xml)
            return p
        self.assertEqual(read_enterprises(write([''])),table())
        with self.assertRaises(ValueError):read_enterprises(write(['2']))
    def test_points_never_become_inferred_factory_boundaries(self):
        p=point();before=copy.deepcopy(p)
        d,b,a=build_distribution([p],table(),Projection(),0,60)
        features=[f for layer in d['layers'] for f in layer['features']]
        self.assertEqual([f['type'] for f in features],['point'])
        self.assertEqual(d['layers'][-1]['features'],[])
        self.assertEqual(features[0]['positions'],[[10,20,0]])
        self.assertEqual(features[0]['provenance']['boundaryStatus'],'not_provided')
        self.assertEqual(p,before)
    def test_sources_conflict_is_not_silently_fuzzy_joined(self):
        for change in [lambda t:t[1].__setitem__(1,'另一个企业'),lambda t:t[1].__setitem__(2,'医药'),lambda t:t[1].__setitem__(6,'已建成'),lambda t:t.update({2:t[1]})]:
            t=table();change(t)
            with self.assertRaises(ValueError):build_distribution([point()],t,Projection(),0,60)
    def test_label_and_business_keep_estimation_and_elevation_caveats(self):
        d,b,a=build_distribution([point()],table(),Projection(),0,60);f=d['layers'][0]['features'][0]
        self.assertIn('待核实',f['label']['text']);self.assertEqual(f['label']['placement'],'billboard');self.assertEqual(f['label']['heightM'],60)
        self.assertIn('非实测',{v['label']:v['value'] for v in b['records'][0]['attributes']}['高程说明'])
        self.assertEqual(a[0]['provenance']['sourceConfidenceLabel'],'低')
    def test_invalid_heights_rejected_before_projection(self):
        for ground,height in [(float('nan'),60),(0,-1),(0,501),(True,60)]:
            with self.assertRaises(ValueError):build_distribution([point()],table(),Projection(),ground,height)
    def test_real_projection_axis_order_known_utm_reference_and_inverse(self):
        p=transformer();x,y=p.transform(117,0,errcheck=True)
        self.assertAlmostEqual(x,500000,places=6);self.assertAlmostEqual(y,0,places=6)
        x,y=p.transform(114.06,32.96,errcheck=True)
        lon,lat=p.transform(x,y,direction='INVERSE',errcheck=True)
        self.assertAlmostEqual(lon,114.06,places=9);self.assertAlmostEqual(lat,32.96,places=9)

if __name__=='__main__':unittest.main()
