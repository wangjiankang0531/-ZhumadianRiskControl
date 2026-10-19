"""Import customer-supplied enterprise reference points without executing source HTML.

This does not infer factory boundaries, field accuracy or ground elevations.
The native/Web DLG readers own rendering; input documents remain untouched.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = [225319.5, 3648440.1, 30.9]
COLORS = {"危化生产": "#D64545", "危化使用": "#E08A1E", "一般化工": "#2F7FD1", "医药": "#2F9E6B"}
W = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate source field")
        result[key] = value
    return result


def read_points(path):
    raw = Path(path).read_bytes()
    if len(raw) > 4 * 1048576:
        raise ValueError("Source HTML exceeds limit")
    source = raw.decode("utf-8-sig")
    declarations = list(re.finditer(r"\b(?:var|let|const)\s+DATA\s*=\s*", source))
    if len(declarations) != 1:
        raise ValueError("Expected one JSON DATA declaration")
    def invalid_constant(value):
        raise ValueError("Nonfinite source JSON")
    decoder = json.JSONDecoder(object_pairs_hook=strict_object, parse_constant=invalid_constant)
    points, _ = decoder.raw_decode(source[declarations[0].end():])
    if not isinstance(points, list) or not 1 <= len(points) <= 1000:
        raise ValueError("Invalid enterprise point list")
    seen = set()
    for point in points:
        if not isinstance(point, dict) or type(point.get("no")) is not int or point["no"] <= 0 or point["no"] in seen:
            raise ValueError("Invalid or duplicate enterprise number")
        seen.add(point["no"])
        for field in ["name", "type", "src", "craft", "chem", "status", "addr", "acc"]:
            if not isinstance(point.get(field), str) or not point[field] or len(point[field]) > 4000:
                raise ValueError("Missing enterprise text")
        if point["type"] not in COLORS:
            raise ValueError("Unsupported enterprise type")
        xy = point.get("wgs")
        if not isinstance(xy, list) or len(xy) != 2 or any(type(n) not in (int, float) or not math.isfinite(n) for n in xy):
            raise ValueError("WGS84 coordinates explicitly required; no GCJ approximation")
        if not 114 <= xy[0] <= 120 or not 0 <= xy[1] <= 84:
            raise ValueError("Coordinates outside UTM 50N area")
    return points


def read_enterprises(path):
    with ZipFile(path) as archive:
        members = [m for m in archive.infolist() if m.filename == "word/document.xml"]
        if len(members) != 1 or members[0].file_size > 4 * 1048576:
            raise ValueError("Invalid document XML")
        raw = archive.read(members[0])
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("DTD/entity declarations are not supported")
    document = ET.fromstring(raw)
    rows = []
    for table in document.findall(".//w:tbl", W):
        table_rows = [["".join(t.text or "" for t in c.findall(".//w:t", W)).strip()
                       for c in row.findall("w:tc", W)] for row in table.findall("w:tr", W)]
        if not table_rows or table_rows[0][:2] != ["序号", "企业名称"]:
            continue
        rows.extend(table_rows[1:])
    if not rows or len(rows) > 1000:
        raise ValueError("Enterprise table not found or excessive rows")
    result = {}
    for row in rows:
        if not any(row):
            continue
        if len(row) != 7 or not re.fullmatch(r"[1-9][0-9]*", row[0]) or int(row[0]) in result:
            raise ValueError("Invalid enterprise table row")
        result[int(row[0])] = row
    return result


def transformer():
    from pyproj import Transformer, network
    network.set_network_enabled(False)
    return Transformer.from_crs("EPSG:4326", "EPSG:32650", always_xy=True, allow_ballpark=False)


def build_distribution(points, table, projection, ground_z, label_height):
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in [ground_z, label_height]) or abs(ground_z) > 100000 or not 0 <= label_height <= 500:
        raise ValueError("Invalid display elevation or sign height")
    if {p["no"] for p in points} != set(table):
        raise ValueError("Document enterprise numbers differ")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    layers = [{"id": "customer-enterprises-" + str(i), "name": kind + "企业（资料估算点位）", "visible": True, "locked": False, "features": []} for i, kind in enumerate(COLORS, 1)]
    by_kind = dict(zip(COLORS, layers))
    records = []
    audit = []
    for p in points:
        row = table[p["no"]]
        if not p["name"].startswith(row[1]) or p["type"] != row[2] or p["status"] != row[6]:
            raise ValueError("Enterprise name/type/status differs between sources")
        east, north = projection.transform(*p["wgs"], errcheck=True)
        local = [round(east - ORIGIN[0], 6), round(north - ORIGIN[1], 6), ground_z]
        if any(not math.isfinite(v) or abs(v) > 100000 for v in local):
            raise ValueError("Point outside local landscape range")
        identity = "customer-enterprise-" + str(p["no"]).zfill(3)
        binding = {"objectType": "enterprise", "businessId": identity, "enterpriseId": identity, "sourceSystem": "customer-reference-import"}
        short = p["name"] + "\n" + p["type"] + " · " + p["status"] + "\n重大危险源：" + row[3] + "\n资料估算位置 · 待核实"
        provenance = {"positionStatus": "estimated_from_address_not_surveyed", "boundaryStatus": "not_provided", "sourceWGS84": p["wgs"], "sourceGCJ02": p.get("gcj"), "sourceBD09": p.get("bd"), "sourceConfidenceLabel": p["acc"], "elevationStatus": "display_datum_not_surveyed", "displayGroundZ": ground_z}
        feature = {"id": identity, "name": p["name"], "type": "point", "positions": [local], "style": {"icon": "pin", "sizePx": 30, "pattern": "solid", "widthPx": 3, "color": COLORS[p["type"]], "opacity": 1, "fillColor": COLORS[p["type"]], "fillOpacity": .18}, "label": {"visible": True, "text": short, "fontPx": 14, "color": "#E9FAFF", "opacity": 1, "offset": [12, -16], "placement": "billboard", "heightM": label_height}, "business": binding, "provenance": provenance}
        by_kind[p["type"]]["features"].append(feature)
        attributes = [["企业类型", row[2]], ["项目状态", row[6]], ["重大危险源情况", row[3]], ["重点监管工艺", row[4]], ["重点监管危化品", row[5]], ["地址依据", p["addr"]], ["位置说明", "资料依据地址路网估算，非实测，待核实"], ["边界说明", "未提供厂界红线，须人工描绘与核实"], ["高程说明", "显示基准高程，非实测高程"], ["资料日期", "原文未注明"]]
        records.append({**binding, "name": p["name"], "updatedAt": now, "attributes": [{"label": k, "value": v} for k, v in attributes]})
        audit.append({"spatialId": identity, "number": p["no"], "position": local, "sourceName": row[1], "displayName": p["name"], "provenance": provenance})
    layers.append({"id": "customer-enterprise-boundaries", "name": "企业边界（人工描绘待核实）", "visible": True, "locked": False, "features": []})
    document = {"schema": "hongtu.landscape.layers.v1", "scene": "zhumadian", "coordinates": {"srs": "EPSG:32650", "origin": ORIGIN, "axes": "east,north,up", "unit": "metre"}, "layers": layers}
    business = {"schema": "xnby.business.records.v1", "scene": "zhumadian", "exportedAt": now, "ttlHours": 24, "records": records}
    return document, business, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--local-ground-z", type=float, required=True, help="Explicit display datum only; source has no measured elevations")
    parser.add_argument("--label-height", type=float, default=0)
    args = parser.parse_args()
    before = {str(p.resolve()): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size": p.stat().st_size, "mtimeNs": p.stat().st_mtime_ns} for p in [args.html, args.docx]}
    document, business, items = build_distribution(read_points(args.html), read_enterprises(args.docx), transformer(), args.local_ground_z, args.label_height)
    sys.path.insert(0, str(ROOT))
    from services.data import validate_layers, validate_records
    validate_layers(document)
    validate_records(business)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    manifest = {"schema": "xnby.customer.enterprise.import.v1", "source": before, "pointCount": len(items), "boundaryCount": 0, "estimatedPositions": True, "measuredElevations": False, "items": items, "rendererStatus": "billboard_extension_pending_validation", "outputs": {}}
    for name, value in [("企业分布_待核实.json", document), ("企业资料台账_本地.json", business)]:
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with (args.output_dir / name).open("xb") as stream:
            stream.write(raw)
        manifest["outputs"][name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    for path, expected in before.items():
        p = Path(path)
        if expected != {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size": p.stat().st_size, "mtimeNs": p.stat().st_mtime_ns}:
            raise RuntimeError("Source changed during import; review outputs")
    with (args.output_dir / "import_manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"points": len(items), "boundaries": 0, "layers": len(document["layers"]), "sourceUnchanged": True, "output": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
