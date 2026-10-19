"""Lossless original-image physical pages for the existing atomic source frontier.

Pure memory only: no export files, atlas writes, resampling or cache cleanup.
"""
from __future__ import annotations
import array
import copy
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from types import MappingProxyType

from osgb_memory_gltf import MemoryGltf
from native_source_frontier import SourceForest

FORMAT = "osgb_memory_png_v1"
LAYOUT = "three_float32_pu_uint32_v1"
ROOT_SCHEMA = "zhumadian.osgb_source_frontier.v2"
FAMILY_SCHEMA = "zhumadian.osgb_source_family.v2"
MIB = 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mip_bytes(width, height):
    if any(type(n) is not int or not 1 <= n <= 8192 for n in (width, height)):
        raise ValueError("invalid source image extent")
    result = 0
    while True:
        result += width * height * 4
        if width == height == 1:
            return result
        width, height = max(1, width // 2), max(1, height // 2)


def floats(payload, segment, kind):
    values = array.array(kind)
    values.frombytes(payload[segment["offset"]:segment["offset"] + segment["bytes"]])
    if sys.byteorder != "little":
        values.byteswap()
    return values


def percentile(values):
    return sorted(values)[min(len(values) - 1, int(len(values) * .9))] if values else 0.0


def mesh_metrics(mesh, image, payload):
    positions, uv, indices = (floats(payload, mesh[key], kind)
                              for key, kind in (("positions", "f"), ("uv", "f"), ("indices", "I")))
    edges, texels = [], []
    low, high = [math.inf] * 3, [-math.inf] * 3
    for at in range(0, len(indices), 3):
        ids = indices[at:at + 3]
        points = [positions[index * 3:index * 3 + 3] for index in ids]
        triangle_edges = []
        for point in points:
            low = [min(a, b) for a, b in zip(low, point)]
            high = [max(a, b) for a, b in zip(high, point)]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            length = math.dist(points[i], points[j])
            triangle_edges.append(length)
            u, v = ids[i] * 2, ids[j] * 2
            pixels = math.hypot((uv[u] - uv[v]) * image["width"],
                                (uv[u + 1] - uv[v + 1]) * image["height"])
            if pixels > 1e-6:
                texels.append(length / pixels)
        edges.append(max(triangle_edges))
    return low, high, edges, texels


def page(descriptor, payload, mesh, directory, source_name, *, metric_image=None):
    image = descriptor["images"][mesh["image"]]
    rgba = payload[image["offset"]:image["offset"] + image["bytes"]]
    if any(alpha != 255 for alpha in rgba[3::4]):
        raise ValueError("nonopaque original image needs a separate material contract")
    selected = copy.deepcopy(mesh)
    selected["image"] = 0
    single = {**descriptor, "images": [image], "meshes": [selected],
              "vertices": mesh["positions"]["count"] // 3,
              "triangles": mesh["indices"]["count"] // 3}
    builder = MemoryGltf("geometry", max_bytes=128 * MIB)
    builder.add(single, payload)
    delivered, _ = builder.finish()
    gltf = json.loads(delivered["geometry.gltf"][0])
    del gltf["extensionsUsed"]
    del gltf["materials"][0]["extensions"]
    del gltf["meshes"][0]["primitives"][0]["mode"]
    gltf["images"][0]["uri"] = "texture.png"
    resources = {
        "geometry.gltf": (canonical(gltf), "model/gltf+json"),
        "geometry.bin": delivered["geometry.bin"],
        "texture.png": delivered["geometry_texture_0.png"],
    }
    native_cost = single["vertices"] * 64 + single["triangles"] * 12 + mip_bytes(image["width"], image["height"])
    if native_cost > 32 * MIB:
        raise ValueError("original source page exceeds the unchanged 32MiB bound")
    geometry_name = source_name[:-5]
    part = {
        "directory": directory, "source_format": FORMAT, "geometry_layout": LAYOUT,
        "vertices": single["vertices"], "indices": single["triangles"] * 3,
        "source_image": {"file": "texture.png", "width": image["width"], "height": image["height"],
                         "opaque": True, "row_order": "source_storage", "source_origin": image["sourceOrigin"],
                         "sampler": gltf["samplers"][0]},
        "files": [{"name": name, "bytes": len(value[0]), "sha256": sha(value[0])}
                  for name, value in sorted(resources.items())],
        "gpu_payload_bytes": native_cost, "source_names": [source_name],
        "source_spans": [{"geometry_name": geometry_name, "first": 0, "count": single["triangles"] * 3}],
        "source_face_counts": {geometry_name: single["triangles"]},
    }
    return part, resources, mesh_metrics(mesh, metric_image or image, payload)


@dataclass(frozen=True)
class SourceBundle:
    # JSON bytes prevent callers from mutating the marker owned by the store.
    marker_json: bytes
    resources: object
    folder: str
    delivery_bytes: int

    @property
    def marker_sha256(self):
        return sha(self.marker_json)

    def marker(self):
        return json.loads(self.marker_json)


def build_bundle(tile, catalog, reader, *, depth=None, parent=None, recipe_identity,
                 page_builder=page, source_format=FORMAT):
    if type(tile) is not int or not 1 <= tile <= 2346 or (depth is None) == (parent is None):
        raise ValueError("one root depth or one parent is required")
    if catalog.get("tile_id") != tile or catalog.get("source_directory") != f"assets/驻马店园区/Data/Tile_{tile}":
        raise ValueError("catalog belongs to a different source directory")
    forest = SourceForest(catalog)
    pattern = re.compile(rf"Tile_{tile}_L[0-9]+_0[0-9u]+\.osgb")
    for name in forest.depths:
        node = forest.nodes[name]
        if (not pattern.fullmatch(name) or not re.fullmatch(r"[0-9a-f]{64}", node.get("sha256", ""))
                or type(node.get("bytes")) is not int or not 0 < node["bytes"] <= 32 * MIB):
            raise ValueError("invalid reachable source identity")
    if parent is None:
        if type(depth) is not int or not 1 <= depth <= max(forest.depths.values()) or depth > 12:
            raise ValueError("requested frontier is outside this source forest")
        cut = {forest.root}
        for _ in range(depth):
            cut = {child for name in cut for child in forest.nodes[name]["children"] or [name]}
        names = sorted(forest.validate_cut(cut))
        folder = f"tile_{tile}_depth_{depth}"
    else:
        if not isinstance(parent, str) or parent not in forest.depths or not forest.nodes[parent]["children"]:
            raise ValueError("unknown or terminal source parent")
        names = sorted(forest.nodes[parent]["children"])
        folder = f"family_tile_{tile}_{sha(parent.encode())[:16]}"
    parts, resources, records, edges, texels = [], {}, [], [], []
    for name in names:
        record = forest.nodes[name]
        descriptor, payload = reader(tile, name, record)
        if descriptor["node"] != f"Tile_{tile}/{name}" or descriptor["sourceBytes"] != record["bytes"]:
            raise ValueError("reader returned a different source")
        node = {"name": name, "geometry_name": name[:-5], "depth": forest.depths[name],
                "children": record["children"], "source_sha256": record["sha256"],
                "spans": [], "triangles": 0, "bounds_min": [math.inf] * 3,
                "bounds_max": [-math.inf] * 3}
        node_edges, node_texels = [], []
        for mesh in descriptor["meshes"]:
            if len(parts) >= 64:
                raise ValueError("complete source family exceeds the unchanged 64-page bound")
            part, files, (low, high, mesh_edges, mesh_texels) = page_builder(descriptor, payload, mesh, f"part_{len(parts):03}", name)
            parts.append(part)
            resources.update({(part["directory"], key): value for key, value in files.items()})
            if sum(len(value[0]) for value in resources.values()) > 128 * MIB:
                raise ValueError("complete memory bundle exceeds delivery bound")
            node["spans"].append({"part": part["directory"], "first": 0, "count": part["indices"]})
            node["triangles"] += part["indices"] // 3
            node["bounds_min"] = [min(a, b) for a, b in zip(node["bounds_min"], low)]
            node["bounds_max"] = [max(a, b) for a, b in zip(node["bounds_max"], high)]
            node_edges.extend(mesh_edges)
            node_texels.extend(mesh_texels)
        if node["triangles"] != descriptor["triangles"]:
            raise ValueError("physical pages do not preserve every source triangle")
        node["longest_edge_p90_m"] = percentile(node_edges)
        node["texel_world_p90_m"] = percentile(node_texels)
        edges.extend(node_edges)
        texels.extend(node_texels)
        records.append(node)
    total = sum(part["gpu_payload_bytes"] for part in parts)
    if not parts or total > (384 if parent is None else 256) * MIB:
        raise ValueError("complete source cut exceeds unchanged bundle budget")
    marker = {
        "schema": ROOT_SCHEMA if parent is None else FAMILY_SCHEMA, "source_format": source_format,
        "tile_id": tile, "texture_policy": "original_pixels_v1",
        "parts": parts, "source_nodes": records, "indices": sum(p["indices"] for p in parts),
        "gpu_payload_bytes": total, "longest_edge_p90_m": percentile(edges),
        "texel_world_p90_m": percentile(texels),
        "stamp": sha(canonical({"catalog": catalog, "recipe": recipe_identity, "format": source_format})),
    }
    if parent is None:
        marker.update(depth=depth, complete_frontier=True)
    else:
        marker.update(replacement_parent=parent, complete_sibling_family=True,
                      parent_source_sha256=forest.nodes[parent]["sha256"], family_key=sha(parent.encode())[:16])
    raw = canonical(marker)
    return SourceBundle(raw, MappingProxyType(resources), folder, len(raw) + sum(len(v[0]) for v in resources.values()))

