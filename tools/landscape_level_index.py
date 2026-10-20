"""Exact source bounds, indexed frustum queries and complete mixed-level cuts.

This module never guesses child extents from filenames or parent rectangles.
Bounds describe original triangles; subtree envelopes include every descendant.
The quality measure is projected tessellation/texel size, not geometric-error SSE.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def bounds(low, high):
    if (len(low) != 3 or len(high) != 3 or
            any(type(x) not in (int, float) or not math.isfinite(x) for x in (*low, *high)) or
            any(a > b for a, b in zip(low, high))):
        raise ValueError("invalid exact source bounds")
    return tuple(low), tuple(high)


def union(items):
    items = list(items)
    if not items:
        raise ValueError("empty bounds union")
    return (tuple(min(x[0][a] for x in items) for a in range(3)),
            tuple(max(x[1][a] for x in items) for a in range(3)))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def normalized(v):
    length = math.sqrt(dot(v, v))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError("degenerate camera direction")
    return tuple(x/length for x in v)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


@dataclass(frozen=True)
class Camera:
    position: tuple
    target: tuple
    fov: float
    aspect: float
    height: int
    near: float = 0.1
    far: float = 60000.0

    def __post_init__(self):
        bounds(self.position, self.position)
        bounds(self.target, self.target)
        if not (math.isfinite(self.fov) and 0 < self.fov < 179 and
                math.isfinite(self.aspect) and self.aspect > 0 and type(self.height) is int and
                self.height > 0 and math.isfinite(self.near) and math.isfinite(self.far) and
                0 < self.near < self.far):
            raise ValueError("invalid camera projection")
        normalized(tuple(b-a for a, b in zip(self.position, self.target)))

    def frame(self):
        forward = normalized(tuple(b-a for a, b in zip(self.position, self.target)))
        right = cross(forward, (0, 0, 1))
        right = normalized(right) if dot(right, right) > 1e-12 else (1, 0, 0)
        return forward, right, normalized(cross(right, forward))

    def planes(self):
        forward, right, up = self.frame()
        y = math.tan(math.radians(self.fov/2))
        normals = [tuple(forward[a]*y*self.aspect+s*right[a] for a in range(3)) for s in (-1, 1)]
        normals += [tuple(forward[a]*y+s*up[a] for a in range(3)) for s in (-1, 1)]
        return ([(n, -dot(n, self.position)) for n in normals] +
                [(forward, -dot(forward, self.position)-self.near),
                 (tuple(-x for x in forward), dot(forward, self.position)+self.far)])

    def quality(self, node):
        low, high = bounds(node["boundsMin"], node["boundsMax"])
        distance_box = bounds(node.get("subtreeMin", low), node.get("subtreeMax", high))
        distance = max(self.near, math.sqrt(sum(max(a-c, c-b, 0)**2
                                               for a, b, c in zip(*distance_box, self.position))))
        metric = max(node["edgeP90"], node["texelP90"]*4)
        return metric*self.height/(2*distance*math.tan(math.radians(self.fov/2)))


def intersects(box, planes):
    low, high = box
    # AABB positive vertex, including tangent planes and near-plane crossings.
    return all(sum(n[a]*(high[a] if n[a] >= 0 else low[a]) for a in range(3))+d >= -1e-7
               for n, d in planes)


class BoundsIndex:
    """Median BVH over exact boxes. IDs and level metadata remain unchanged."""

    def __init__(self, entries, leaf_size=8):
        if not 1 <= leaf_size <= 64:
            raise ValueError("invalid BVH leaf size")
        self.entries = tuple(entries)
        if len({entry["id"] for entry in self.entries}) != len(self.entries):
            raise ValueError("duplicate indexed source")
        self.boxes = [bounds(e["boundsMin"], e["boundsMax"]) for e in self.entries]
        self.nodes = []

        def build(ids):
            box = union(self.boxes[i] for i in ids)
            index = len(self.nodes)
            self.nodes.append(None)
            if len(ids) <= leaf_size:
                self.nodes[index] = box, tuple(ids), None
            else:
                axis = max(range(3), key=lambda a: box[1][a]-box[0][a])
                ids.sort(key=lambda i: (self.boxes[i][0][axis]+self.boxes[i][1][axis], i))
                half = len(ids)//2
                children = build(ids[:half]), build(ids[half:])
                self.nodes[index] = box, (), children
            return index

        if self.entries:
            build(list(range(len(self.entries))))

    def query(self, camera):
        planes = camera.planes()
        pending = [0] if self.nodes else []
        found = []
        visited = tested = 0
        while pending:
            box, ids, children = self.nodes[pending.pop()]
            visited += 1
            if not intersects(box, planes):
                continue
            if children:
                pending.extend(children)
            else:
                for i in ids:
                    tested += 1
                    if intersects(self.boxes[i], planes):
                        found.append(self.entries[i])
        return sorted(found, key=lambda e: e["id"]), {"bvhNodesVisited": visited, "entryBoundsTested": tested}


def finalize_tile(catalog, exact):
    """Reject partial metadata; build conservative envelopes, never inferred boxes."""
    from native_source_frontier import SourceForest
    forest = SourceForest(catalog)
    needed = {n for n in forest.depths if forest.nodes[n]["level"] is not None}
    if set(exact) != needed:
        raise ValueError("incomplete or extra exact source bounds")
    result = {}

    def visit(name):
        source = forest.nodes[name]
        children = source["children"]
        child_boxes = [visit(child) for child in children]
        if name not in needed:
            envelope = union(child_boxes)
        else:
            record = dict(exact[name])
            if record["sourceSHA256"] != source["sha256"] or record["sourceBytes"] != source["bytes"]:
                raise ValueError("source metadata identity changed")
            own = bounds(record["boundsMin"], record["boundsMax"])
            if any(not math.isfinite(record[k]) or record[k] <= 0 for k in ("edgeP90", "texelP90")):
                raise ValueError("invalid source detail metric")
            envelope = union([own, *child_boxes])
            record.update(name=name, depth=forest.depths[name], level=source["level"], children=children,
                          subtreeMin=list(envelope[0]), subtreeMax=list(envelope[1]))
            result[name] = record
        return envelope

    envelope = visit(forest.root)
    return {"schema": "zhumadian.level_bounds.tile.v1", "tile": catalog["tile_id"],
            "root": forest.root, "roots": ([forest.root] if forest.root in needed else forest.nodes[forest.root]["children"]),
            "boundsMin": envelope[0], "boundsMax": envelope[1], "complete": True,
            "nodes": [result[n] for n in sorted(result)]}


def select_cut(tile, camera, target_pixels=6.0, max_depth=None):
    """Complete mixed-depth frontier; offscreen branches remain coarse.

    The renderer must keep the previous complete cut until the selected cut is
    fully decoded, uploaded and within the concurrent old/new resource budget.
    """
    if tile.get("schema") != "zhumadian.level_bounds.tile.v1" or tile.get("complete") is not True:
        raise ValueError("a complete exact-bounds index is required")
    if not math.isfinite(target_pixels) or target_pixels <= 0:
        raise ValueError("invalid detail target")
    nodes = {n["name"]: n for n in tile["nodes"]}
    if len(nodes) != len(tile["nodes"]):
        raise ValueError("duplicate exact source")
    planes = camera.planes()
    selected = []
    visited = 0

    def visit(name):
        nonlocal visited
        node = nodes[name]
        visited += 1
        envelope = bounds(node["subtreeMin"], node["subtreeMax"])
        visible = intersects(envelope, planes)
        refine = (visible and node["children"] and camera.quality(node) > target_pixels and
                  (max_depth is None or node["depth"] < max_depth))
        if refine:
            for child in node["children"]:
                visit(child)
        else:
            selected.append(name)

    for root in tile["roots"]:
        visit(root)
    return selected, {"nodesVisited": visited, "selectedSources": len(selected)}
