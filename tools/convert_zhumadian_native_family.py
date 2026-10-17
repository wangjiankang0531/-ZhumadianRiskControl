"""Prepare every direct child of one visible OSGB node for an atomic local replacement."""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
import convert_zhumadian_native_chunks as chunks
import native_source_frontier as frontier

ROOT = chunks.ROOT
CACHE = chunks.CACHE
FAMILY_LIMIT = 256 * 1048576


def family_key(parent):
    return hashlib.sha256(parent.encode("utf-8")).hexdigest()[:16]


def convert_locked(tile, parent, *, atlas_layout=None, cache_root=None):
    atlas_layout, CACHE = chunks.recipes.resolve_cache(ROOT, globals()["CACHE"], atlas_layout, cache_root)
    native = chunks.native
    master = json.loads(
        (ROOT / "data/showcase/zhumadian_native_hierarchy.json").read_text(
            encoding="utf-8"
        )
    )
    root_record = next(r for r in master["root_records"] if r["tile_id"] == tile)
    catalog_path = ROOT / root_record["catalog"]
    if native.sha(catalog_path) != root_record["sha256"]:
        raise ValueError("source hierarchy changed")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    forest = frontier.SourceForest(catalog)
    if parent not in forest.depths or not forest.nodes[parent]["children"]:
        raise ValueError("family parent is not a reachable refinable source node")
    sources = [forest.nodes[name] for name in forest.nodes[parent]["children"]]
    directory = (ROOT / catalog["source_directory"]).resolve()
    if not directory.is_relative_to((ROOT / "assets/驻马店园区").resolve()):
        raise ValueError("source directory escapes GIS assets")
    if sum(s["bytes"] for s in sources) > 64 * 1048576:
        raise ValueError("family source decode budget exceeded")
    for source in sources:
        path = directory / source["name"]
        if path.parent != directory or native.sha(path) != source["sha256"]:
            raise ValueError("source child changed")
    folder = CACHE / f"family_tile_{tile}_{family_key(parent)}"
    chunks.recipes.writable_bundle(folder)
    stamp = {
        "catalog_sha256": root_record["sha256"],
        "parent": parent,
        "children": sources,
        "family_converter_sha256": native.sha(Path(__file__)),
        "converter_sha256": native.sha(Path(chunks.__file__)),
        "frontier_helper_sha256": native.sha(Path(frontier.__file__)),
        "texture_helper_sha256": native.sha(Path(chunks.textures.__file__)),
        "native_helper_sha256": native.sha(Path(native.__file__)),
        "packer_sha256": native.sha(Path(native.full.__file__)),
        "exporter_sha256": native.sha(
            ROOT / "work/osgb_exporter_build/Release/ht_osgb_exporter.exe"
        ),
    }
    stamp.update(chunks.recipes.stamp(atlas_layout))
    marker = folder / "complete.json"
    if marker.is_file():
        try:
            ready = json.loads(marker.read_text(encoding="utf-8"))
            valid = (
                ready["stamp"] == stamp
                and ready["schema"] == "xnby.osgb_native_family.v1"
                and ready["replacement_parent"] == parent
                and ready["complete_sibling_family"]
                and 0 < len(ready["parts"]) <= 64
                and {n["name"] for n in ready["source_nodes"]}
                == {s["name"] for s in sources}
                and chunks.recipes.payload_present(folder, ready)
            )
            if valid:
                marker.touch()
                print(json.dumps({"cached": True, "bundle": str(marker)}), flush=True)
                return ready
        except (OSError, KeyError, TypeError, ValueError):
            pass  # Rebuild only the derived candidate after stale/corrupt cache.
    chunks.cache_policy.mark_dirty(CACHE)
    marker.unlink(missing_ok=True)
    defaults = native.base.parse_args([])
    osg = native.base.resolve_path(ROOT, defaults.osgconv)
    env = os.environ.copy()
    env["PATH"] = str(osg.parent) + os.pathsep + env.get("PATH", "")
    env["OSG_LIBRARY_PATH"] = str(
        native.base.resolve_path(ROOT, defaults.osg_plugin_dir)
    )
    env["OSG_NOTIFY_LEVEL"] = "WARN"
    alias = native.base.ensure_ascii_source_alias(
        ROOT / "assets/驻马店园区", ROOT / "work/zmd_source",
        exporter=ROOT / "work/osgb_exporter_build/Release/ht_osgb_exporter.exe"
    )
    try:
        parts, edges, texels = [], [], []
        for group in chunks.groups(sources):
            for part, edge_samples, texel_samples in chunks.build_parts(
                folder, group, directory, env, alias, len(parts),
                atlas_layout=atlas_layout, cache_root=CACHE
            ):
                parts.append(part)
                edges.extend(edge_samples)
                texels.extend(texel_samples)
                if (
                    len(parts) > 64
                    or sum(p["gpu_payload_bytes"] for p in parts) > FAMILY_LIMIT
                ):
                    raise ValueError(
                        "complete sibling family exceeds local candidate budget"
                    )
        nodes = frontier.source_metadata(folder, parts, sources, catalog, directory)
        if {node["name"] for node in nodes} != set(forest.nodes[parent]["children"]):
            raise ValueError("family conversion omitted a direct child")
        if not parts or not edges or not texels:
            raise ValueError("empty drawable source family")
        result = {
            "schema": "xnby.osgb_native_family.v1",
            "tile_id": tile,
            "replacement_parent": parent,
            "parent_source_sha256": forest.nodes[parent]["sha256"],
            "family_key": family_key(parent),
            "stamp": stamp,
            "complete_sibling_family": True,
            "parts": parts,
            "source_nodes": nodes,
            "gpu_payload_bytes": sum(p["gpu_payload_bytes"] for p in parts),
            "indices": sum(p["indices"] for p in parts),
            "texture_policy": "original_pixels_v1",
            "longest_edge_p90_m": sorted(edges)[
                min(len(edges) - 1, int(len(edges) * 0.9))
            ],
            "texel_world_p90_m": sorted(texels)[
                min(len(texels) - 1, int(len(texels) * 0.9))
            ],
        }
        if atlas_layout != chunks.recipes.LEGACY:
            result["atlas_layout_policy"] = atlas_layout
        pending = folder / "complete.pending.json"
        pending.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        pending.replace(marker)
        (folder / "failure.json").unlink(missing_ok=True)
        print(
            json.dumps(
                {
                    "bundle": str(marker),
                    "children": len(nodes),
                    "parts": len(parts),
                    "payload_bytes": result["gpu_payload_bytes"],
                }
            ),
            flush=True,
        )
        return result
    except Exception as error:
        # A rejected candidate owns only derived files in this family folder.
        for part in folder.iterdir():
            if (
                part.is_dir()
                and not part.is_symlink()
                and chunks.re.fullmatch(r"part_\d{3}", part.name)
            ):
                chunks.clean(part, cache_root=CACHE)
                if not any(part.iterdir()):
                    part.rmdir()
        (folder / "failure.json").write_text(
            json.dumps({"reason": str(error)}), encoding="utf-8"
        )
        raise


def convert(tile, parent, *, atlas_layout=None, cache_root=None):
    import msvcrt

    atlas_layout, CACHE = chunks.recipes.resolve_cache(ROOT, globals()["CACHE"], atlas_layout, cache_root)
    chunks.recipes.bind_cache(CACHE, atlas_layout)

    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / "decoder.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        deadline = time.monotonic() + 100
        while True:
            try:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise RuntimeError("native family cache lock deadline")
                time.sleep(0.05)
        try:
            name = f"family_tile_{tile}_{family_key(parent)}"
            with chunks.cache_policy.bundle_lock(CACHE, name, exclusive=True):
                try:
                    return convert_locked(tile, parent, atlas_layout=atlas_layout, cache_root=CACHE)
                finally:
                    chunks.cache_policy.maintain(CACHE)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tile", type=int, required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--receipt-name")
    parser.add_argument("--atlas-layout", choices=chunks.recipes.LAYOUTS)
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    args.atlas_layout, CACHE = chunks.recipes.resolve_cache(ROOT, CACHE, args.atlas_layout, args.cache_root)
    args.cache_root = CACHE
    if not 1 <= args.tile <= 2346:
        parser.error("tile outside source catalog")
    sys.path.insert(0, str(ROOT / "work/geospatial_deps"))
    if args.receipt_name and not chunks.re.fullmatch(
        r"native_family_[0-9]+_tile_[0-9]+_depth_[0-9]+\.json", args.receipt_name
    ):
        parser.error("invalid owned receipt name")
    try:
        convert(args.tile, args.parent, atlas_layout=args.atlas_layout, cache_root=args.cache_root)
    finally:
        if args.receipt_name:
            receipt = CACHE / args.receipt_name
            receipt.write_text(
                json.dumps(
                    {
                        "parent": args.parent,
                        "directory": f"family_tile_{args.tile}_{family_key(args.parent)}",
                    }
                ),
                encoding="utf-8",
            )
