import copy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_enterprise_csv import HEADERS, read_csv, reconcile


def fixture():
    values = dict(zip(HEADERS, ["1", "合成企业有限公司", "危化生产", "无", "—", "1,3-合成物", "在建",
                               "合成地址", "中等（依据地址估算，建议现场核对）",
                               "114.070001", "32.960002", "114.063003", "32.954004"]))
    row = {"number": 1, "values": values, "bd09": [114.070001, 32.960002], "gcj02": [114.063003, 32.954004]}
    reference = {"no": 1, "name": values["企业名称"], "type": "危化生产", "wgs": [114.057, 32.956],
                 "bd": row["bd09"], "gcj": row["gcj02"]}
    binding = {"objectType": "enterprise", "businessId": "customer-enterprise-001",
               "enterpriseId": "customer-enterprise-001", "sourceSystem": "customer-reference-import"}
    feature = {"id": binding["businessId"], "name": reference["name"], "type": "point",
               "positions": [[10.25, 20.5, 31.125]], "label": {"text": "旧标牌", "heightM": 0},
               "business": binding, "provenance": {"sourceWGS84": reference["wgs"],
               "displaySurface": "existing_ground_sample"}}
    doc = {"layers": [{"features": [feature]}, {"features": [{"id": "manual-boundary", "type": "region",
            "positions": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}]}]}
    record = {**binding, "name": reference["name"], "attributes": [{"label": "高程说明", "value": "已贴面，非实测"},
               {"label": "重点监管危化品", "value": "旧值"}]}
    return row, reference, doc, {"records": [record]}


class CSVImport(unittest.TestCase):
    def parse(self, headers, rows):
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"source.csv"
            path.write_bytes(b"\xef\xbb\xbf"+stream.getvalue().encode("utf-8"))
            return read_csv(path)

    def apply(self, row=None, reference=None, doc=None, records=None):
        r, p, d, b = fixture()
        return reconcile([row or r], [reference or p], doc or d, records or b,
                         source_name="coordinate-source.csv", source_sha256="a"*64)

    def test_named_coordinates_and_quoted_chemical_comma(self):
        row, *_ = fixture()
        result = self.parse(HEADERS, [list(row["values"].values()), []])
        self.assertEqual(result[0]["bd09"], row["bd09"])
        self.assertEqual(result[0]["gcj02"], row["gcj02"])
        self.assertEqual(result[0]["values"]["重点监管危险化学品"], "1,3-合成物")

    def test_no_coordinate_inverse_or_geometry_edit_and_manual_boundary_survives(self):
        row, reference, doc, business = fixture()
        before = copy.deepcopy([row, reference, doc, business])
        new_doc, records, audit = self.apply(row, reference, doc, business)
        self.assertEqual(new_doc["layers"][0]["features"][0]["positions"], [[10.25, 20.5, 31.125]])
        self.assertEqual(new_doc["layers"][1], doc["layers"][1])
        self.assertEqual([row, reference, doc, business], before)
        self.assertFalse(audit["coordinateInverseUsed"])
        self.assertFalse(audit["boundariesInferred"])
        self.assertEqual(audit["precisionCounts"], {"中等": 1})

    def test_precision_source_coordinates_and_latest_csv_attributes_are_exposed(self):
        doc, business, _ = self.apply()
        f = doc["layers"][0]["features"][0]
        self.assertIn("CSV资料定位：中等", f["label"]["text"])
        self.assertIn("待核实", f["label"]["text"])
        self.assertEqual(f["provenance"]["coordinateCSV"]["sourceCRS"], ["BD09", "GCJ02"])
        self.assertEqual(f["provenance"]["displaySurface"], "existing_ground_sample")
        attrs = {a["label"]: a["value"] for a in business["records"][0]["attributes"]}
        self.assertEqual(attrs["重点监管危化品"], "1,3-合成物")
        self.assertEqual(attrs["高程说明"], "已贴面，非实测")
        self.assertEqual(attrs["坐标精度"], fixture()[0]["values"]["坐标精度"])

    def test_changed_coordinate_pair_cannot_reuse_an_unrelated_wgs84_point(self):
        for change in (lambda r:r["bd09"].__setitem__(0, 114.08), lambda r:r["gcj02"].__setitem__(1, 32.97)):
            row, *_ = fixture()
            change(row)
            with self.assertRaisesRegex(ValueError, "matching WGS84"):
                self.apply(row=row)

    def test_missing_wgs84_wrong_name_or_category_refused(self):
        for mutate in (lambda p:p.pop("wgs"), lambda p:p.update(name="另一企业"), lambda p:p.update(type="医药")):
            _, p, *_ = fixture()
            mutate(p)
            with self.assertRaises(ValueError):
                self.apply(reference=p)

    def test_duplicate_or_missing_columns_extra_cells_and_duplicate_ids_refused(self):
        row, *_ = fixture()
        cells = list(row["values"].values())
        for headers, rows in [(HEADERS[:-1], [cells[:-1]]), (HEADERS[:-1]+[HEADERS[0]], [cells]),
                              (HEADERS, [cells+["unexpected"]]), (HEADERS, [cells, cells])]:
            with self.assertRaises(ValueError):
                self.parse(headers, rows)

    def test_nonfinite_swapped_axes_and_missing_accuracy_refused(self):
        for key, value in [("百度BD09经度", "NaN"), ("腾讯GCJ02经度", "32.9"),
                           ("腾讯GCJ02纬度", "114.06"), ("坐标精度", "")]:
            row, *_ = fixture()
            row["values"][key] = value
            with self.assertRaises(ValueError):
                self.parse(HEADERS, [list(row["values"].values())])

    def test_missing_or_conflicting_business_binding_is_not_fuzzy_joined(self):
        row, reference, doc, records = fixture()
        records["records"][0]["name"] = "同名相似企业"
        with self.assertRaises(ValueError):
            self.apply(row, reference, doc, records)


if __name__ == "__main__":
    unittest.main()
