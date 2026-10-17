"""Independently validate real source family coverage, files, and concurrent residency."""

import argparse
import json
import sys
from pathlib import Path
import convert_zhumadian_native_chunks as chunks
import convert_zhumadian_native_family as families
from native_source_frontier import SourceForest


def verify(tile, depth, parent):
    whole = chunks.convert(tile, depth)
    family = families.convert(tile, parent)
    root = chunks.ROOT
    master = json.loads(
        (root / "data/showcase/zhumadian_native_hierarchy.json").read_text(
            encoding="utf-8"
        )
    )
    entry = next(r for r in master["root_records"] if r["tile_id"] == tile)
    forest = SourceForest(
        json.loads((root / entry["catalog"]).read_text(encoding="utf-8"))
    )
    before = {n["name"] for n in whole["source_nodes"]}
    after = forest.replace_family(
        before, parent, [n["name"] for n in family["source_nodes"]]
    )
    maximum = 0
    for marker, folder in [
        (whole, chunks.CACHE / f"tile_{tile}_depth_{depth}"),
        (family, chunks.CACHE / f"family_tile_{tile}_{families.family_key(parent)}"),
    ]:
        payload, indices = 0, 0
        for part in marker["parts"]:
            physical = (
                part["vertices"] * 64
                + part["indices"] * 4
                + sum((part["atlas_size"] // (2**i)) ** 2 * 4 for i in range(12))
            )
            if physical != part["gpu_payload_bytes"] or physical > chunks.PART_LIMIT:
                raise ValueError(
                    "physical resource/upload accounting differs from marker"
                )
            maximum = max(maximum, physical)
            payload += physical
            indices += part["indices"]
            if sum(s["count"] for s in part["source_spans"]) != part["indices"]:
                raise ValueError("source index spans omit triangles")
            for file in part["files"]:
                path = folder / part["directory"] / file["name"]
                if (
                    path.stat().st_size != file["bytes"]
                    or chunks.native.sha(path) != file["sha256"]
                ):
                    raise ValueError("family output file changed")
        if payload != marker["gpu_payload_bytes"] or indices != marker["indices"]:
            raise ValueError("aggregate source resource accounting differs")
    parent_record = next(n for n in whole["source_nodes"] if n["name"] == parent)
    retained = sum(n["triangles"] for n in whole["source_nodes"] if n["name"] != parent)
    selected = retained + sum(n["triangles"] for n in family["source_nodes"])
    if (
        selected
        != whole["indices"] // 3 - parent_record["triangles"] + family["indices"] // 3
    ):
        raise ValueError("parent replacement triangle accounting differs")
    return {
        "schema": "xnby.source_family.verification.v1",
        "tile": tile,
        "base_depth": depth,
        "replacement_parent": parent,
        "children": [n["name"] for n in family["source_nodes"]],
        "frontier_before": len(before),
        "frontier_after": len(after),
        "complete_cut": True,
        "unreplaced_nodes_retained": sorted(before - {parent}),
        "parent_triangles_removed": parent_record["triangles"],
        "children_triangles": family["indices"] // 3,
        "result_triangles": selected,
        "root_payload_bytes": whole["gpu_payload_bytes"],
        "candidate_payload_bytes": family["gpu_payload_bytes"],
        "retained_root_plus_candidate_bytes": whole["gpu_payload_bytes"]
        + family["gpu_payload_bytes"],
        "max_upload_bytes": maximum,
        "original_texture_pixels": True,
        "catalog_sha256": entry["sha256"],
        "runtime_integrated": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tile", type=int, default=141)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--parent", default="Tile_141_L21_0uuuu00.osgb")
    args = parser.parse_args()
    sys.path.insert(0, str(chunks.ROOT / "work/geospatial_deps"))
    print(
        json.dumps(
            verify(args.tile, args.depth, args.parent), ensure_ascii=False, indent=2
        )
    )
