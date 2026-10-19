"""Bounded RAM ownership and leases for immutable original-source pages.

The 256MiB limit covers retained encoded bundles and a 128MiB build reservation,
not Python/OSG process RSS. GPU limits remain exclusively in the WEB allocator.
"""
from __future__ import annotations
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import secrets
import threading
import time
from osgb_memory_reader import read_node
from osgb_memory_pages import build_bundle, canonical, sha, MIB

PLAN_SCHEMA = "xnby.source_bundle_plan.v1"


def ordinary(path, root):
    path, root = Path(path), Path(root)
    if not path.is_relative_to(root):
        raise ValueError("path outside fixed source root")
    for entry in [root, *reversed(list(path.parents)[:len(path.relative_to(root).parts)-1]), path]:
        stat = entry.lstat()
        if entry.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked source or runtime path")
    if not path.is_file():
        raise ValueError("source is not a regular file")
    return path


class PinnedMemoryReader:
    def __init__(self, executable, source_root, runtime_hashes):
        self.executable = Path(executable).resolve(strict=True)
        self.source_root = Path(source_root).resolve(strict=True)
        self.runtime = self.executable.parent
        self.hashes = dict(runtime_hashes)
        if self.executable.name not in self.hashes or not self.hashes or len(self.hashes) > 32:
            raise ValueError("reader runtime must have explicit pinned identities")
        for name, digest in self.hashes.items():
            if (Path(name).is_absolute() or ".." in Path(name).parts
                    or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                raise ValueError("invalid runtime manifest")
        self.verify_runtime()
        self.identity = sha(canonical(self.hashes))

    def verify_runtime(self):
        actual = {p.relative_to(self.runtime).as_posix() for p in self.runtime.rglob("*") if p.is_file()}
        if actual != set(self.hashes):
            raise ValueError("unexpected executable/plugin runtime contents")
        for name, digest in self.hashes.items():
            path = ordinary(self.runtime / name, self.runtime)
            if sha(path.read_bytes()) != digest:
                raise ValueError("reader runtime changed")

    def __call__(self, tile, name, record):
        self.verify_runtime()
        descriptor, payload, _ = read_node(self.executable, self.source_root, f"Tile_{tile}/{name}",
                                          record["sha256"], executable_sha256=self.hashes[self.executable.name])
        if descriptor["sourceBytes"] != record["bytes"]:
            raise ValueError("source byte length differs from pinned catalog")
        return descriptor, payload


class PinnedCatalogs:
    def __init__(self, resource_root):
        self.root = Path(resource_root).resolve(strict=True)
        index = ordinary(self.root / "data/showcase/zhumadian_native_hierarchy.json", self.root)
        raw = index.read_bytes()
        if len(raw) > 16 * MIB:
            raise ValueError("source forest index too large")
        graph = json.loads(raw)
        records = graph["root_records"]
        self.records = {row["tile_id"]: row for row in records}
        # Deployment uses a trusted, preconfigured resource-directory junction.
        # Resolve that fixed anchor once; requested filenames cannot choose a link.
        self.catalog_root = (self.root / "assets/showcase/runtime/zhumadian/native_hierarchy").resolve(strict=True)
        if len(self.records) != len(records):
            raise ValueError("duplicate source root")
        self.identity = sha(raw)

    def __call__(self, tile):
        record = self.records[tile]
        name = f"assets/showcase/runtime/zhumadian/native_hierarchy/tile_{tile}.json"
        if record["catalog"] != name:
            raise ValueError("source catalog path changed")
        path = ordinary(self.catalog_root / f"tile_{tile}.json", self.catalog_root)
        raw = path.read_bytes()
        if len(raw) > 16 * MIB or sha(raw) != record["sha256"]:
            raise ValueError("source catalog SHA mismatch")
        return json.loads(raw)


class MemoryStoreBusy(RuntimeError):
    pass


class MemorySourceStore:
    def __init__(self, catalogs, reader, *, limit=256 * MIB, build_reservation=128 * MIB,
                 clock=time.monotonic, ttl=180, max_jobs=16, max_leases=256):
        if not 0 < build_reservation <= limit or limit > 256 * MIB or not 0 < ttl <= 180:
            raise ValueError("invalid bounded memory store policy")
        self.catalogs, self.reader = catalogs, reader
        self.limit, self.build_reservation, self.clock, self.ttl = limit, build_reservation, clock, ttl
        self.max_jobs, self.max_leases = max_jobs, max_leases
        if not 1 <= max_jobs <= 16 or not 1 <= max_leases <= 256:
            raise ValueError("unbounded request policy")
        self.recipe = sha(canonical({"reader": reader.identity, "catalogs": catalogs.identity,
                         "code": {name: sha((Path(__file__).parent / name).read_bytes()) for name in
                                  ("osgb_memory_pages.py", "osgb_memory_gltf.py", "osgb_memory_reader.py")}}))
        self.lock = threading.RLock()
        self.entries, self.jobs, self.failures, self.leases = OrderedDict(), {}, OrderedDict(), {}
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="source-memory")
        self.building = None
        self.closed = False
        self.stats = {"builds": 0, "failures": 0, "evictions": 0, "payloads": 0,
                      "peakEncodedAndReservation": 0}

    @staticmethod
    def key(tile, depth, parent):
        if type(tile) is not int or not 1 <= tile <= 2346 or (depth is None) == (parent is None):
            raise ValueError("invalid memory source request")
        if parent is None:
            if type(depth) is not int or not 1 <= depth <= 12:
                raise ValueError("invalid source depth")
            return tile, depth, None
        if not isinstance(parent, str) or not re.fullmatch(rf"Tile_{tile}_L[0-9]+_0[0-9u]+\.osgb", parent):
            raise ValueError("invalid source parent")
        return tile, None, parent

    def _expire(self):
        for token, lease in list(self.leases.items()):
            if lease["expires"] <= self.clock():
                del self.leases[token]
                self.entries[lease["key"]]["refs"] -= 1

    def _bytes(self):
        return sum(entry["bundle"].delivery_bytes for entry in self.entries.values())

    def _room(self, additional):
        self._expire()
        while self._bytes() + additional > self.limit:
            key = next((key for key, entry in self.entries.items() if not entry["refs"]), None)
            if key is None:
                raise MemoryStoreBusy("all memory bundles are leased; keep previous layer")
            del self.entries[key]
            self.stats["evictions"] += 1

    def _build(self, key):
        try:
            with self.lock:
                self._room(self.build_reservation)
                self.building = key
                self.stats["peakEncodedAndReservation"] = max(self.stats["peakEncodedAndReservation"],
                                                               self._bytes() + self.build_reservation)
            tile, depth, parent = key
            bundle = build_bundle(tile, self.catalogs(tile), self.reader, depth=depth, parent=parent,
                                  recipe_identity=self.recipe)
            if bundle.delivery_bytes > self.build_reservation:
                raise ValueError("source bundle exceeds reserved encoded delivery")
            with self.lock:
                self.entries[key] = {"bundle": bundle, "refs": 0}
                self.entries.move_to_end(key)
                self.stats["builds"] += 1
        except Exception as error:
            with self.lock:
                self.failures[key] = f"{type(error).__name__}: {error}"
                self.stats["failures"] += 1
                while len(self.failures) > 256:
                    self.failures.popitem(last=False)
        finally:
            with self.lock:
                self.building = None
                self.jobs.pop(key, None)

    def request(self, tile, *, depth=None, parent=None):
        key = self.key(tile, depth, parent)
        with self.lock:
            if self.closed:
                raise RuntimeError("source memory store closed")
            self._expire()
            if key in self.entries:
                self.entries.move_to_end(key)
                return self.entries[key]["bundle"]
            if key in self.failures:
                raise ValueError(self.failures[key])
            if key not in self.jobs:
                if len(self.jobs) >= self.max_jobs:
                    raise MemoryStoreBusy("source preparation queue full")
                # Holding the lock prevents worker completion before registration.
                self.jobs[key] = self.executor.submit(self._build, key)
            return None

    def plan(self, tile, *, depth=None, parent=None):
        bundle = self.request(tile, depth=depth, parent=parent)
        if bundle is None:
            return None
        return {"schema": PLAN_SCHEMA, "verification": "metadata_only", "availabilityVerified": False,
                "markerSHA256": bundle.marker_sha256, "marker": bundle.marker()}

    def grant(self, tile, *, depth=None, parent=None):
        key = self.key(tile, depth, parent)
        with self.lock:
            bundle = self.request(tile, depth=depth, parent=parent)
            if bundle is None:
                return None
            if len(self.leases) >= self.max_leases:
                raise MemoryStoreBusy("source memory lease limit")
            token = secrets.token_hex(16)
            self.entries[key]["refs"] += 1
            self.leases[token] = {"key": key, "expires": self.clock() + self.ttl}
            return {**bundle.marker(), "cache_lease": token}, bundle.marker_sha256

    def release(self, token):
        with self.lock:
            self._expire()
            lease = self.leases.pop(token, None)
            if lease:
                self.entries[lease["key"]]["refs"] -= 1
            return lease is not None

    def payload(self, token, folder, part, name):
        if not re.fullmatch(r"[0-9a-f]{32}", token) or not re.fullmatch(r"part_[0-9]{3}", part) or name not in ("geometry.gltf", "geometry.bin", "texture.png"):
            raise ValueError("invalid source memory payload identity")
        with self.lock:
            self._expire()
            lease = self.leases.get(token)
            if lease is None:
                raise PermissionError("source memory lease expired or unknown")
            bundle = self.entries[lease["key"]]["bundle"]
            if bundle.folder != folder:
                raise PermissionError("source lease belongs to a different bundle")
            value = bundle.resources[(part, name)]
            # Immutable bytes are safe after leaving the lock, including concurrent release.
            lease["expires"] = self.clock() + self.ttl
            self.entries.move_to_end(lease["key"])
            self.stats["payloads"] += 1
            return value

    def audit(self):
        with self.lock:
            self._expire()
            return {**self.stats, "encodedBytes": self._bytes(), "limit": self.limit,
                    "buildReservation": self.build_reservation, "bundles": len(self.entries),
                    "activeLeases": len(self.leases), "queuedJobs": len(self.jobs),
                    "building": self.building, "failuresByRequest": {str(k): v for k, v in self.failures.items()},
                    "assetWritesEnabled": False, "gpuLimitsChanged": False}

    def close(self):
        with self.lock:
            self.closed = True
        self.executor.shutdown(wait=True, cancel_futures=True)

