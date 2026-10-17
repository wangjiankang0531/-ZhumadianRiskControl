"""Convert a complete real OSGB frontier into bounded upload parts; never omit siblings."""

import argparse
import array
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import convert_zhumadian_native_root as native
import native_texture_parts as textures
import native_source_frontier as source_frontier
import native_cache_policy as cache_policy
import native_atlas_recipe as recipes

ROOT = native.ROOT
CACHE = ROOT / "work/zhumadian_native_chunk_cache"
PART_LIMIT = 32 * 1024 * 1024
ROOT_LIMIT = 384 * 1024 * 1024


def groups(sources, byte_limit=4 * 1024 * 1024, node_limit=12):
    """The initial estimate is conservative; actual exported payload can split again."""
    result, current, amount = [], [], 0
    for source in sources:
        if current and (
            amount + source["bytes"] > byte_limit or len(current) >= node_limit
        ):
            result.append(current)
            current, amount = [], 0
        current.append(source)
        amount += source["bytes"]
    if current:
        result.append(current)
    assert [r["name"] for group in result for r in group] == [
        r["name"] for r in sources
    ]
    return result


def clean(folder, remove_outputs=True, *, cache_root=None):
    cache = CACHE if cache_root is None else Path(cache_root)
    assert folder.resolve().is_relative_to(cache.resolve()) and not cache_policy.linked(folder)
    allowed = {
        "source_list.txt",
        "source_triangles.tsv",
        "frontier.obj",
        "frontier.mtl",
    }
    if remove_outputs:
        allowed |= {"geometry.bin", "geometry.gltf", "atlas.jpg"}
    for path in folder.iterdir():
        if path.name in allowed or re.fullmatch(r"texture_\d+\.rgb", path.name):
            if cache_policy.linked(path):
                raise ValueError("Derived output cannot be a link")
            if path.is_file():
                path.unlink()


def prune(protected):
    return cache_policy.prune(CACHE, protected)


def build_parts(bundle, sources, source_directory, env, alias, first_part, *, atlas_layout=None, cache_root=None):
    with recipes.BUILD_LOCK:
        previous_size = native.full.SIZE
        try:
            return _build_parts(bundle, sources, source_directory, env, alias, first_part,
                                atlas_layout=atlas_layout, cache_root=cache_root)
        finally:
            native.full.SIZE = previous_size


def _build_parts(bundle, sources, source_directory, env, alias, first_part, *, atlas_layout=None, cache_root=None):
    atlas_layout = recipes.policy(atlas_layout)
    folder = bundle / "_texture_export"
    folder.mkdir(parents=True, exist_ok=True)
    clean(folder, cache_root=cache_root)
    paths = [source_directory / record["name"] for record in sources]
    source_list = folder / "source_list.txt"
    source_list.write_text(
        "".join(
            str(alias / path.relative_to((ROOT / "assets/驻马店园区").resolve())) + "\n"
            for path in paths
        ),
        encoding="utf-8",
    )
    obj = folder / "frontier.obj"
    audit = folder / "source_triangles.tsv"
    try:
        native.base.run_hidden(
            [
                str(ROOT / "work/osgb_exporter_build/Release/ht_osgb_exporter.exe"),
                str(source_list),
                str(obj),
                str(audit),
            ],
            folder,
            env,
            "native frontier part",
        )
        counts = native.audit_frontier(paths, obj, audit)
        from PIL import Image

        materials = native.full.material_images(obj)
        sizes = {}
        for path in dict.fromkeys(materials.values()):
            with Image.open(path) as image:
                sizes[path] = image.size
        all_parts = []
        for mapping, atlas_size in recipes.layouts(sizes, atlas_layout):
            atlas_extent = recipes.extent(atlas_size)
            texture_bytes = recipes.mip_bytes(atlas_size)
            max_faces = (PART_LIMIT - texture_bytes) // 204
            count = textures.face_count(obj, materials, mapping)
            for first_face in range(0, count, max_faces):
                part_folder = bundle / f"part_{first_part+len(all_parts):03d}"
                part_folder.mkdir(exist_ok=True)
                clean(part_folder, cache_root=cache_root)
                part_obj = part_folder / "frontier.obj"
                textures.slice_obj(
                    obj,
                    part_obj,
                    materials,
                    mapping,
                    first_face,
                    min(max_faces, count - first_face),
                )
                part_counts = textures.face_counts(part_obj)
                native.full.SIZE = max(atlas_extent)
                recipes.save_atlas(mapping, part_folder / "atlas.jpg", atlas_size, atlas_layout)
                views, vertices, indices, low, high, _ = native.full.write_geometry(
                    [part_obj], mapping, part_folder / "geometry.bin", atlas_extent=atlas_extent
                )
                texture_bytes = recipes.mip_bytes(atlas_size)
                payload = vertices * 64 + indices * 4 + texture_bytes
                if payload > PART_LIMIT:
                    raise ValueError(f"part upload budget: {payload} > {PART_LIMIT}")
                assert indices > 0 and indices // 3 == sum(part_counts.values())
                gltf = {
                    "asset": {
                        "version": "2.0",
                        "generator": "XNBY source-sized native texture part",
                    },
                    "buffers": [
                        {
                            "uri": "geometry.bin",
                            "byteLength": (part_folder / "geometry.bin").stat().st_size,
                        }
                    ],
                    "bufferViews": views,
                    "accessors": [
                        {
                            "bufferView": 0,
                            "componentType": 5126,
                            "count": vertices,
                            "type": "VEC3",
                            "min": low,
                            "max": high,
                        },
                        {
                            "bufferView": 1,
                            "componentType": 5126,
                            "count": vertices,
                            "type": "VEC3",
                        },
                        {
                            "bufferView": 2,
                            "componentType": 5126,
                            "count": vertices,
                            "type": "VEC2",
                        },
                        {
                            "bufferView": 3,
                            "componentType": 5125,
                            "count": indices,
                            "type": "SCALAR",
                        },
                    ],
                    "images": [{"uri": "atlas.jpg"}],
                    "textures": [{"source": 0}],
                    "materials": [
                        {
                            "pbrMetallicRoughness": {
                                "baseColorTexture": {"index": 0},
                                "metallicFactor": 0,
                                "roughnessFactor": 1,
                            }
                        }
                    ],
                    "meshes": [
                        {
                            "primitives": [
                                {
                                    "attributes": {
                                        "POSITION": 0,
                                        "NORMAL": 1,
                                        "TEXCOORD_0": 2,
                                    },
                                    "indices": 3,
                                    "material": 0,
                                }
                            ]
                        }
                    ],
                    "nodes": [{"mesh": 0}],
                    "scenes": [{"nodes": [0]}],
                    "scene": 0,
                }
                recipes.apply_sampler(gltf, atlas_layout)
                (part_folder / "geometry.gltf").write_text(
                    json.dumps(gltf), encoding="utf-8"
                )
                positions, triangles = array.array("f"), array.array("I")
                with (part_folder / "geometry.bin").open("rb") as source:
                    positions.fromfile(source, vertices * 3)
                    source.seek(views[3]["byteOffset"])
                    triangles.fromfile(source, indices)
                uvs = array.array("f")
                with (part_folder / "geometry.bin").open("rb") as source:
                    source.seek(views[2]["byteOffset"])
                    uvs.fromfile(source, vertices * 2)
                edges, texels = [], []
                for first in range(0, indices, 3):
                    points = [
                        positions[int(i) * 3 : int(i) * 3 + 3]
                        for i in triangles[first : first + 3]
                    ]
                    edges.append(
                        max(
                            math.dist(points[a], points[b])
                            for a, b in ((0, 1), (1, 2), (2, 0))
                        )
                    )
                    ids = triangles[first : first + 3]
                    for a, b in ((0, 1), (1, 2), (2, 0)):
                        uv_length = (
                            math.hypot(
                                (uvs[ids[a] * 2] - uvs[ids[b] * 2]) * atlas_extent[0],
                                (uvs[ids[a] * 2 + 1] - uvs[ids[b] * 2 + 1]) * atlas_extent[1],
                            )
                        )
                        if uv_length > 1e-6:
                            texels.append(math.dist(points[a], points[b]) / uv_length)
                record = {
                    "directory": part_folder.name,
                    "vertices": vertices,
                    "indices": indices,
                    "gpu_payload_bytes": payload,
                    "atlas_size": max(atlas_extent),
                    "source_atlas_pages": len(mapping),
                    "source_texture_scale": 1.0,
                    "source_names": [r["name"] for r in sources],
                    "source_face_counts": part_counts,
                    "source_spans": source_frontier.face_spans(part_obj),
                    "files": [
                        {
                            "name": name,
                            "bytes": (part_folder / name).stat().st_size,
                            "sha256": native.sha(part_folder / name),
                        }
                        for name in ("geometry.gltf", "geometry.bin", "atlas.jpg")
                    ],
                }
                if atlas_layout == recipes.RECTANGULAR:
                    record["atlas_extent"] = list(atlas_extent)
                if atlas_layout != recipes.LEGACY:
                    record["atlas_layout_policy"] = atlas_layout
                all_parts.append((record, edges, texels))
                clean(part_folder, remove_outputs=False, cache_root=cache_root)
        summed = {}
        for record, _, _ in all_parts:
            for name, amount in record["source_face_counts"].items():
                summed[name] = summed.get(name, 0) + amount
        if summed != {name: amount for name, amount in counts.items() if amount}:
            raise ValueError("texture partitions omit or duplicate source faces")
        return all_parts
    finally:
        clean(folder, cache_root=cache_root)
        if not any(folder.iterdir()):
            folder.rmdir()


def convert_locked(tile, depth, *, atlas_layout=None, cache_root=None):
    atlas_layout, CACHE = recipes.resolve_cache(ROOT, globals()["CACHE"], atlas_layout, cache_root)
    master = json.loads(
        (ROOT / "data/showcase/zhumadian_native_hierarchy.json").read_text(
            encoding="utf-8"
        )
    )
    root_record = next(r for r in master["root_records"] if r["tile_id"] == tile)
    catalog_path = ROOT / root_record["catalog"]
    assert native.sha(catalog_path) == root_record["sha256"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert depth <= catalog["max_descendant_depth"]
    sources = native.frontier(catalog, depth)
    source_frontier.SourceForest(catalog).validate_cut([r["name"] for r in sources])
    source_directory = (ROOT / catalog["source_directory"]).resolve()
    assert source_directory.is_relative_to((ROOT / "assets/驻马店园区").resolve())
    assert sources and sum(r["bytes"] for r in sources) <= 64 * 1024 * 1024
    for record in sources:
        path = source_directory / record["name"]
        assert (
            path.parent == source_directory and native.sha(path) == record["sha256"]
        ), "source changed"
    folder = CACHE / f"tile_{tile}_depth_{depth}"
    recipes.writable_bundle(folder)
    stamp = {
        "catalog_sha256": root_record["sha256"],
        "depth": depth,
        "frontier": sources,
        "converter_sha256": native.sha(Path(__file__)),
        "texture_helper_sha256": native.sha(Path(textures.__file__)),
        "frontier_helper_sha256": native.sha(Path(source_frontier.__file__)),
        "native_helper_sha256": native.sha(Path(native.__file__)),
        "packer_sha256": native.sha(Path(native.full.__file__)),
        "exporter_sha256": native.sha(
            ROOT / "work/osgb_exporter_build/Release/ht_osgb_exporter.exe"
        ),
    }
    stamp.update(recipes.stamp(atlas_layout))
    marker = folder / "complete.json"
    rejected = folder / "rejected.json"
    if rejected.exists():
        previous = json.loads(rejected.read_text(encoding="utf-8"))
        if previous["stamp"] == stamp:
            raise ValueError(previous["reason"])
    if marker.exists() and not cache_policy.linked(marker):
        try:
            complete = json.loads(marker.read_text(encoding="utf-8"))
            valid = (complete["stamp"] == stamp and complete["tile_id"] == tile
                     and complete["depth"] == depth and complete["complete_frontier"] is True
                     and recipes.payload_present(folder, complete))
            if valid:
                marker.touch()
                print(json.dumps({"cached": True, "bundle": str(marker)}), flush=True)
                return complete
        except (OSError, KeyError, TypeError, ValueError):
            pass
    cache_policy.mark_dirty(CACHE)
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
    parts, edges, texels, payload = [], [], [], 0
    try:
        for group in groups(sources):
            batch = build_parts(folder, group, source_directory, env, alias, len(parts),
                                atlas_layout=atlas_layout, cache_root=CACHE)
            for part, sample, texel_sample in batch:
                payload += part["gpu_payload_bytes"]
                if payload > ROOT_LIMIT or len(parts) >= 64:
                    raise ValueError(
                        "complete root frontier exceeds native residency budget"
                    )
                parts.append(part)
                edges.extend(sample)
                texels.extend(texel_sample)
                print(
                    f'part {len(parts)}: {part["indices"]//3} triangles, {part["gpu_payload_bytes"]} bytes; original texture pixels',
                    flush=True,
                )
        assert parts and all(p["source_texture_scale"] == 1.0 for p in parts)
        edges.sort()
        result = {
            "schema": "hongtu.osgb_native_chunk_bundle.v1",
            "tile_id": tile,
            "depth": depth,
            "stamp": stamp,
            "parts": parts,
            "complete_frontier": True,
            "frontier_count": len(sources),
            "gpu_payload_bytes": payload,
            "indices": sum(p["indices"] for p in parts),
            "longest_edge_p90_m": edges[min(len(edges) - 1, int(len(edges) * 0.9))],
            "texel_world_p90_m": sorted(texels)[
                min(len(texels) - 1, int(len(texels) * 0.9))
            ],
            "texture_policy": "original_pixels_v1",
            "source_nodes": source_frontier.source_metadata(
                folder, parts, sources, catalog, source_directory
            ),
        }
        if atlas_layout != recipes.LEGACY:
            result["atlas_layout_policy"] = atlas_layout
        temporary = folder / "complete.pending.json"
        temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
        temporary.replace(marker)
        rejected.unlink(missing_ok=True)
        (folder / "failure.json").unlink(missing_ok=True)
        print(
            json.dumps(
                {"bundle": str(marker), "parts": len(parts), "payload_bytes": payload}
            ),
            flush=True,
        )
        return result
    except Exception as error:
        (folder / "failure.json").write_text(
            json.dumps({"reason": str(error)}), encoding="utf-8"
        )
        if "budget" in str(error):
            rejected.write_text(
                json.dumps({"stamp": stamp, "reason": str(error)}), encoding="utf-8"
            )
        raise
    finally:
        cache_policy.prune(CACHE, folder)


def convert(tile, depth, *, atlas_layout=None, cache_root=None):
    import msvcrt

    atlas_layout, CACHE = recipes.resolve_cache(ROOT, globals()["CACHE"], atlas_layout, cache_root)
    recipes.bind_cache(CACHE, atlas_layout)

    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / "decoder.lock").open("a+b") as lock:
        # Windows byte locks also reject reads by another process. Inspect the
        # file length without reading the locked byte, then acquire ownership.
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
                    raise RuntimeError("native chunk cache lock deadline")
                time.sleep(0.05)
        try:
            with cache_policy.bundle_lock(CACHE, f"tile_{tile}_depth_{depth}", exclusive=True):
                return convert_locked(tile, depth, atlas_layout=atlas_layout, cache_root=CACHE)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tile", type=int, required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--atlas-layout", choices=recipes.LAYOUTS)
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    assert 1 <= args.tile <= 2346 and 0 <= args.depth <= 32
    sys.path.insert(0, str(ROOT / "work/geospatial_deps"))
    convert(args.tile, args.depth, atlas_layout=args.atlas_layout, cache_root=args.cache_root)
