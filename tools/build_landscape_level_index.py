"""Precompute exact LEVEL/source bounds without changing GIS or decoding images.

Only metadata is persisted under --output. Each original node is verified against
the existing SHA-pinned catalog before and after the owned geometry-only reader.
An interrupted tile resumes; incomplete tiles cannot be used as complete indices.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

from landscape_level_index import finalize_tile
from native_source_frontier import SourceForest
from osgb_cropped_pages import parse_geometry_frame
from osgb_memory_pages import mesh_metrics, percentile
import numpy as np
from osgb_stdio_worker import StdioWorker
from readonly_source_memory_store import PinnedMemoryReader, PinnedCatalogs, ordinary


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    pending = path.with_suffix(path.suffix+".pending")
    pending.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")), "utf-8")
    pending.replace(path)


def geometry_metrics(desc, payload):
    low, high = np.full(3, np.inf), np.full(3, -np.inf)
    edges, texels = [], []
    for mesh in desc["meshes"]:
        def values(key, dtype, width):
            segment = mesh[key]
            return np.frombuffer(payload, dtype=dtype, count=segment["count"], offset=segment["offset"]).reshape(-1, width)
        positions = values("positions", "<f4", 3).astype(np.float64)
        uv = values("uv", "<f4", 2).astype(np.float64)
        ids = values("indices", "<u4", 3)
        points = positions[ids]
        low = np.minimum(low, points.min(axis=(0, 1)))
        high = np.maximum(high, points.max(axis=(0, 1)))
        image = desc["images"][mesh["image"]]
        texture = uv[ids]*[image["width"], image["height"]]
        lengths = np.stack([np.linalg.norm(points[:,i]-points[:,j], axis=1) for i,j in ((0,1),(1,2),(2,0))])
        pixels = np.stack([np.linalg.norm(texture[:,i]-texture[:,j], axis=1) for i,j in ((0,1),(1,2),(2,0))])
        edges.append(lengths.max(axis=0))
        valid = pixels > 1e-6
        texels.append(lengths[valid]/pixels[valid])
    def p90(items):
        values = np.concatenate(items)
        if not values.size:
            return 0.0
        k = min(len(values)-1, int(len(values)*.9))
        return float(np.partition(values, k)[k])
    return {"boundsMin": low.tolist(), "boundsMax": high.tolist(), "edgeP90": p90(edges),
            "texelP90": p90(texels), "triangles": desc["triangles"], "vertices": desc["vertices"]}


def build(package, output, tiles):
    package = package.resolve(strict=True)
    output = output.absolute()
    project_work = Path(__file__).resolve().parents[1]/"work"
    if not output.resolve().is_relative_to(project_work.resolve()) or output.resolve() == project_work.resolve():
        raise ValueError("index output must be a dedicated project work directory")
    output.mkdir(parents=True, exist_ok=True)
    resources = package/"resources"
    manifest = json.loads((package/"source_runtime_manifest.json").read_text("utf-8"))
    binding = json.loads((package/"source_runtime_binding.json").read_text("utf-8"))
    data = (package/binding["dataRoot"]).resolve(strict=True)
    reader_hashes = manifest["readerFiles"]
    pinned = PinnedMemoryReader(package/"reader/zmd_osgb_stream_reader.exe", data, reader_hashes)
    catalogs = PinnedCatalogs(resources)
    master = json.loads((resources/"data/showcase/zhumadian_native_hierarchy.json").read_text("utf-8"))
    source_identity = catalogs.identity
    recipe = sha(Path(__file__).read_bytes()+Path(__file__).with_name("landscape_level_index.py").read_bytes())
    roots = [{"id": r["tile_id"], "tile": r["tile_id"], "level": 0,
              "boundsMin": r["bounds_min"], "boundsMax": r["bounds_max"],
              "catalogSHA256": r["sha256"]} for r in master["root_records"]]
    write(output/"root_index.json", {"schema": "zhumadian.level_bounds.roots.v1",
          "sourceManifestSHA256": source_identity, "coordinateSystem": "source_local_metres",
          "boundsSource": "audited_original_base_geometry", "roots": roots})
    wanted = sorted(catalogs.records if tiles is None else tiles)
    if not wanted or any(t not in catalogs.records for t in wanted):
        raise ValueError("invalid requested source tiles")
    worker = StdioWorker(pinned.executable, data)
    started = time.monotonic()
    state = {"status": "running", "driverPid": os.getpid(), "tilesRequested": wanted,
             "sourceManifestSHA256": source_identity, "recipeSHA256": recipe,
             "completedTiles": [], "nodesRead": 0, "resumedNodes": 0,
             "sourceWrites": 0, "imagePayloadBytes": 0, "indexBytes": 0}

    def checkpoint():
        state.update(elapsedSeconds=time.monotonic()-started, worker=worker.audit())
        write(output/"build_phase.json", state)

    checkpoint()
    try:
        for tile in wanted:
            catalog = catalogs(tile)
            forest = SourceForest(catalog)
            catalog_sha = catalogs.records[tile]["sha256"]
            complete = output/f"tile_{tile}.json"
            partial = output/f"tile_{tile}.partial.json"
            identity = {"sourceManifestSHA256": source_identity, "catalogSHA256": catalog_sha,
                        "recipeSHA256": recipe}
            if complete.exists():
                prior = json.loads(complete.read_text("utf-8"))
                if all(prior.get(k) == v for k, v in identity.items()) and prior.get("complete") is True:
                    state["completedTiles"].append(tile)
                    state["resumedNodes"] += len(prior["nodes"])
                    checkpoint()
                    continue
                raise ValueError("complete index belongs to a different source or recipe")
            records = {}
            if partial.exists():
                prior = json.loads(partial.read_text("utf-8"))
                if not all(prior.get(k) == v for k, v in identity.items()):
                    raise ValueError("partial index belongs to a different source or recipe")
                records = prior["records"]
                state["resumedNodes"] += len(records)
            for name in sorted(n for n in forest.depths if forest.nodes[n]["level"] is not None):
                source = forest.nodes[name]
                if name in records:
                    if records[name]["sourceSHA256"] != source["sha256"]:
                        raise ValueError("resumed source identity differs")
                    continue
                node = f"Tile_{tile}/{name}"
                path = ordinary(data/node, data)
                before = path.stat()
                if before.st_size != source["bytes"] or sha(path.read_bytes()) != source["sha256"]:
                    raise ValueError("original source differs from pinned catalog")
                raw = worker.request(node, "--geometry-only")
                desc, payload = parse_geometry_frame(raw, node, source["bytes"])
                record = geometry_metrics(desc, payload)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha(path.read_bytes()) != source["sha256"]:
                    raise ValueError("source changed during exact index generation")
                record.update(sourceSHA256=source["sha256"], sourceBytes=source["bytes"])
                records[name] = record
                state.update(tile=tile, currentNode=name, nodesRead=state["nodesRead"]+1)
                if state["nodesRead"] % 16 == 0:
                    write(partial, {**identity, "records": records, "complete": False})
                    checkpoint()
                    print(json.dumps({"tile": tile, "nodesRead": state["nodesRead"],
                                      "elapsedSeconds": round(time.monotonic()-started, 3)}), flush=True)
            result = finalize_tile(catalog, records)
            result.update(identity)
            write(complete, result)
            state["indexBytes"] += complete.stat().st_size
            state["completedTiles"].append(tile)
            checkpoint()
        pinned.verify_runtime()
        state["status"] = "verified"
    except Exception:
        state.update(status="failed", error=traceback.format_exc())
        raise
    finally:
        worker.close()
        checkpoint()
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tiles", help="Comma separated tile IDs; omission builds all reachable source nodes")
    args = parser.parse_args()
    selected = None if args.tiles is None else {int(x) for x in args.tiles.split(",")}
    print(json.dumps(build(args.package, args.output, selected), ensure_ascii=False), flush=True)
