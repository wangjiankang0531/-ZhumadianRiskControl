"""Reconcile customer BD09/GCJ02 CSV with the existing explicit WGS84 reference.

No coordinate-system guessing or approximate GCJ inverse is performed. New or
changed coordinate pairs require a new explicit WGS84 reference. Source files and
current user geometry are never edited by this importer.
"""
from __future__ import annotations
import argparse
import copy
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import unicodedata
from pathlib import Path
from import_enterprise_distribution import read_points, COLORS

HEADERS = ["序号", "企业名称", "企业类型", "重大危险源情况", "重点监管危险化工工艺",
           "重点监管危险化学品", "项目状态", "地址依据", "坐标精度",
           "百度BD09经度", "百度BD09纬度", "腾讯GCJ02经度", "腾讯GCJ02纬度"]


def read_csv(path):
    raw = Path(path).read_bytes()
    if not 0 < len(raw) <= 4 * 1048576:
        raise ValueError("CSV source length outside bounds")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if (reader.fieldnames is None or len(reader.fieldnames) != len(HEADERS)
            or set(reader.fieldnames) != set(HEADERS)):
        raise ValueError("CSV must contain unique named BD09 and GCJ02 columns")
    output, seen = [], set()
    for record in reader:
        if not any(record.values()):
            continue
        if None in record or any(value is None for value in record.values()):
            raise ValueError("CSV row length differs from named columns")
        record = {key: value.strip() for key, value in record.items()}
        if not re.fullmatch(r"[1-9][0-9]*", record["序号"]):
            raise ValueError("invalid enterprise number")
        number = int(record["序号"])
        if number in seen:
            raise ValueError("duplicate enterprise number")
        seen.add(number)
        if any(not value or len(value) > 4000 or "\x00" in value for value in record.values()):
            raise ValueError("missing or excessive CSV enterprise text")
        if record["企业类型"] not in COLORS:
            raise ValueError("unsupported enterprise category")
        coords = []
        for key in HEADERS[-4:]:
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", record[key]):
                raise ValueError("invalid named source coordinate")
            coords.append(float(record[key]))
        if not all(math.isfinite(value) for value in coords) or not (114 <= coords[0] <= 120 and 0 <= coords[1] <= 84 and 114 <= coords[2] <= 120 and 0 <= coords[3] <= 84):
            raise ValueError("source coordinates outside expected region or axes swapped")
        output.append({"number": number, "values": record, "bd09": coords[:2], "gcj02": coords[2:]})
        if len(output) > 1000:
            raise ValueError("too many CSV enterprises")
    if not output:
        raise ValueError("CSV has no enterprises")
    return output


def normalized(value):
    return unicodedata.normalize("NFKC", value).strip()


def reconcile(rows, references, document, business, *, source_name, source_sha256):
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256) or Path(source_name).name != source_name:
        raise ValueError("invalid CSV source identity")
    points = {p["no"]: p for p in references}
    if len(points) != len(references) or {row["number"] for row in rows} != set(points):
        raise ValueError("CSV and explicit WGS84 enterprise references differ")
    if len({row["number"] for row in rows}) != len(rows):
        raise ValueError("duplicate CSV enterprise identity")
    doc, records = copy.deepcopy(document), copy.deepcopy(business)
    features = {f["id"]: f for layer in doc["layers"] for f in layer["features"]}
    by_business = {r["businessId"]: r for r in records["records"] if r["objectType"] == "enterprise"}
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    counts, audit = {}, []
    for row in rows:
        p, values = points[row["number"]], row["values"]
        if normalized(values["企业名称"]) != normalized(p["name"]) or values["企业类型"] != p["type"]:
            raise ValueError("CSV enterprise name/category identity differs")
        # Pair comparison, not treating BD09/GCJ02 numbers as EPSG:4326.
        if row["bd09"] != p.get("bd") or row["gcj02"] != p.get("gcj"):
            raise ValueError("changed BD09/GCJ02 pair needs an explicit matching WGS84 reference")
        wgs = p.get("wgs")
        if not isinstance(wgs, list) or len(wgs) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in wgs):
            raise ValueError("explicit WGS84 reference missing")
        identity = f"customer-enterprise-{row['number']:03}"
        f, record = features[identity], by_business[identity]
        if (f["type"] != "point" or normalized(f["name"]) != normalized(values["企业名称"])
                or normalized(record["name"]) != normalized(values["企业名称"])
                or f["business"] != {key: record[key] for key in ("objectType", "businessId", "enterpriseId", "sourceSystem")}):
            raise ValueError("existing spatial/business identity differs from CSV")
        precision = values["坐标精度"]
        group = precision.split("（", 1)[0]
        counts[group] = counts.get(group, 0) + 1
        f["provenance"].update({
            "sourceBD09": row["bd09"], "sourceGCJ02": row["gcj02"],
            "sourceConfidenceLabel": precision,
            "coordinateCSV": {"file": source_name, "sha256": source_sha256,
                              "number": row["number"], "sourceCRS": ["BD09", "GCJ02"],
                              "referenceMatch": "exact_dual_pair_same_number_and_name",
                              "wgs84Reference": "existing_customer_map_explicit_wgs84",
                              "sourceWGS84": wgs},
        })
        f["label"]["text"] = (f"{f['name']}\n{values['企业类型']} · {values['项目状态']}\n"
                               f"重大危险源：{values['重大危险源情况']}\nCSV资料定位：{group} · 待核实")
        attributes = {a["label"]: a["value"] for a in record["attributes"]}
        if len(attributes) != len(record["attributes"]):
            raise ValueError("duplicate existing business attribute")
        attributes.update({
            "企业类型": values["企业类型"], "项目状态": values["项目状态"],
            "重大危险源情况": values["重大危险源情况"],
            "重点监管工艺": values["重点监管危险化工工艺"],
            "重点监管危化品": values["重点监管危险化学品"],
            "地址依据": values["地址依据"], "坐标精度": precision,
            "坐标来源": source_name,
            "BD09经纬度": f"{row['bd09'][0]:.6f}, {row['bd09'][1]:.6f}",
            "GCJ02经纬度": f"{row['gcj02'][0]:.6f}, {row['gcj02'][1]:.6f}",
            "位置说明": f"客户CSV资料定位：{precision}；非现场实测，待核实",
            "坐标校核": "同号同名企业的BD09与GCJ02均与原地图资料一致；保持现有场景位置",
        })
        record["attributes"] = [{"label": key, "value": value} for key, value in attributes.items()]
        record["updatedAt"] = now
        audit.append({"number": row["number"], "featureId": identity, "name": f["name"],
                      "bd09Exact": True, "gcj02Exact": True, "positionsPreserved": True,
                      "precision": precision, "positions": f["positions"]})
    records["exportedAt"] = now
    return doc, records, {"count": len(audit), "precisionCounts": counts, "items": audit,
                          "coordinateInverseUsed": False, "boundariesInferred": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["csv", "reference-html", "layers", "business", "output-dir"]:
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    sources = [args.csv, args.reference_html, args.layers, args.business]
    def fact(path):
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size, "mtimeNs": path.stat().st_mtime_ns}
    before = {str(p.resolve()): fact(p) for p in sources}
    document, records, report = reconcile(read_csv(args.csv), read_points(args.reference_html),
        json.loads(args.layers.read_text("utf-8-sig")), json.loads(args.business.read_text("utf-8-sig")),
        source_name=args.csv.name, source_sha256=before[str(args.csv.resolve())]["sha256"])
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from services.data import validate_layers, validate_records
    validate_layers(document)
    validate_records(records)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    outputs = {}
    for name, value in [("企业分布_待核实.json", document), ("企业资料台账_本地.json", records)]:
        body = (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
        with (args.output_dir/name).open("xb") as stream:
            stream.write(body)
        outputs[name] = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
    assert before == {str(p.resolve()): fact(p) for p in sources}, "source changed during import"
    manifest = {"schema": "zhumadian.customer_coordinate_csv.v1", "sources": before,
                "sourceFilesUnchanged": True, "report": report, "outputs": outputs}
    with (args.output_dir/"csv_import_manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"points": report["count"], "precisionCounts": report["precisionCounts"],
                      "positionsPreserved": True, "sourceFilesUnchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
