"""Exact source-node cuts and index ownership for atomic OSGB family replacement."""

import array
import math
import re
from pathlib import Path

GEOMETRY_NAME = re.compile(r"Tile_[+-]\d+_[+-]\d+_L\d+_0[0-9u]+")


class SourceForest:
    def __init__(self, catalog):
        self.root = catalog["root"]
        self.nodes = {node["name"]: node for node in catalog["nodes"]}
        if len(self.nodes) != len(catalog["nodes"]) or self.root not in self.nodes:
            raise ValueError("duplicate or missing source node")
        self.depths = {}
        visiting = set()

        def visit(name, depth):
            if name in visiting or name in self.depths:
                raise ValueError("cycle or multiple parents in source hierarchy")
            if name not in self.nodes:
                raise ValueError("missing source child")
            visiting.add(name)
            self.depths[name] = depth
            children = self.nodes[name]["children"]
            if len(set(children)) != len(children):
                raise ValueError("duplicate source child")
            for child in children:
                visit(child, depth + 1)
            visiting.remove(name)

        visit(self.root, 0)

    def validate_cut(self, names):
        names = list(names)
        selected = set(names)
        if (
            len(selected) != len(names)
            or not selected
            or not selected <= self.depths.keys()
        ):
            raise ValueError("invalid source frontier names")
        consumed = set()

        def cover(name):
            if name in selected:
                consumed.add(name)
                return
            children = self.nodes[name]["children"]
            if not children:
                raise ValueError("source frontier leaves a coverage hole")
            for child in children:
                cover(child)

        cover(self.root)
        if consumed != selected:
            raise ValueError("source frontier overlaps an ancestor")
        return frozenset(selected)

    def replace_family(self, cut, parent, ready_children):
        previous = self.validate_cut(cut)
        children = self.nodes.get(parent, {}).get("children", [])
        ready = list(ready_children)
        if (
            parent not in previous
            or not children
            or len(set(ready)) != len(ready)
            or set(ready) != set(children)
        ):
            raise ValueError(
                "replacement requires the visible parent and every direct child"
            )
        return self.validate_cut((previous - {parent}) | set(children))


def face_spans(obj):
    """OBJ face order is also write_geometry's exact index order; no bbox clipping."""
    spans, current, index = [], None, 0
    with Path(obj).open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith(("o ", "g ")):
                match = GEOMETRY_NAME.search(line)
                current = match.group() if match else None
            elif line.startswith("f "):
                if current is None or len(line.split()) != 4:
                    raise ValueError("unattributed or non-triangular source face")
                if spans and spans[-1]["geometry_name"] == current:
                    spans[-1]["count"] += 3
                else:
                    spans.append({"geometry_name": current, "first": index, "count": 3})
                index += 3
    return spans


def geometry_name(path):
    names = set(GEOMETRY_NAME.findall(Path(path).read_bytes().decode("latin1")))
    if len(names) != 1:
        raise ValueError("ambiguous source geometry identity")
    return names.pop()


def source_metadata(folder, parts, sources, catalog, source_directory):
    import json

    forest = SourceForest(catalog)
    records = {}
    for source in sources:
        key = geometry_name(source_directory / source["name"])
        if key in records:
            raise ValueError("duplicate source geometry identity")
        records[key] = {
            "name": source["name"],
            "geometry_name": key,
            "depth": forest.depths[source["name"]],
            "children": forest.nodes[source["name"]]["children"],
            "source_sha256": source["sha256"],
            "spans": [],
            "triangles": 0,
            "bounds_min": [math.inf] * 3,
            "bounds_max": [-math.inf] * 3,
            "edges": [],
            "texels": [],
        }
    for part in parts:
        part_folder = folder / part["directory"]
        gltf = json.loads((part_folder / "geometry.gltf").read_text(encoding="utf-8"))
        views = gltf["bufferViews"]
        positions, indices, uvs = array.array("f"), array.array("I"), array.array("f")
        with (part_folder / "geometry.bin").open("rb") as data:
            data.seek(views[0]["byteOffset"])
            positions.fromfile(data, part["vertices"] * 3)
            data.seek(views[2]["byteOffset"])
            uvs.fromfile(data, part["vertices"] * 2)
            data.seek(views[3]["byteOffset"])
            indices.fromfile(data, part["indices"])
        expected_first = 0
        attributed = {}
        for span in part["source_spans"]:
            first, count, key = span["first"], span["count"], span["geometry_name"]
            if (
                first != expected_first
                or count <= 0
                or count % 3
                or first + count > len(indices)
                or key not in records
            ):
                raise ValueError("source index ownership has a gap or overlap")
            expected_first += count
            attributed[key] = attributed.get(key, 0) + count // 3
            record = records[key]
            record["spans"].append(
                {"part": part["directory"], "first": first, "count": count}
            )
            record["triangles"] += count // 3
            for offset in range(first, first + count, 3):
                ids = indices[offset : offset + 3]
                points = [positions[i * 3 : i * 3 + 3] for i in ids]
                for point in points:
                    if len(point) != 3 or not all(math.isfinite(x) for x in point):
                        raise ValueError("source bounds contain an invalid vertex")
                    record["bounds_min"] = [
                        min(a, b) for a, b in zip(record["bounds_min"], point)
                    ]
                    record["bounds_max"] = [
                        max(a, b) for a, b in zip(record["bounds_max"], point)
                    ]
                record["edges"].append(
                    max(
                        math.dist(points[a], points[b])
                        for a, b in [(0, 1), (1, 2), (2, 0)]
                    )
                )
                for a, b in [(0, 1), (1, 2), (2, 0)]:
                    pixels = (
                        math.hypot(
                            uvs[ids[a] * 2] - uvs[ids[b] * 2],
                            uvs[ids[a] * 2 + 1] - uvs[ids[b] * 2 + 1],
                        )
                        * part["atlas_size"]
                    )
                    if pixels > 1e-6:
                        record["texels"].append(
                            math.dist(points[a], points[b]) / pixels
                        )
        if (
            expected_first != part["indices"]
            or attributed != part["source_face_counts"]
        ):
            raise ValueError("source spans disagree with audited triangle counts")
    output = []
    for record in records.values():
        for samples, target in [
            ("edges", "longest_edge_p90_m"),
            ("texels", "texel_world_p90_m"),
        ]:
            values = sorted(record.pop(samples))
            record[target] = (
                values[min(len(values) - 1, int(len(values) * 0.9))] if values else 0
            )
        if not record["triangles"]:
            record["bounds_min"] = record["bounds_max"] = None
        output.append(record)
    if sum(r["triangles"] for r in output) * 3 != sum(p["indices"] for p in parts):
        raise ValueError("source metadata omits triangles")
    return output
