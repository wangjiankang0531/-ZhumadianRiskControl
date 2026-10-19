import copy
import io
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image
from test_osgb_memory_reader import fixture
from osgb_memory_pages import build_bundle, mip_bytes, FORMAT, MIB
from readonly_source_memory_store import MemorySourceStore, MemoryStoreBusy, PinnedCatalogs

ROOT = "Tile_1_L16_0u.osgb"
CHILD = "Tile_1_L17_0uu.osgb"


class Catalog:
    identity = "fixture_catalog"
    def __call__(self, tile):
        if tile != 1:
            raise KeyError(tile)
        return {"tile_id": 1, "root": ROOT, "source_directory": "assets/驻马店园区/Data/Tile_1",
                "nodes": [{"name": ROOT, "children": [CHILD], "bytes": 100, "sha256": "a"*64},
                          {"name": CHILD, "children": [], "bytes": 100, "sha256": "b"*64}]}


class Reader:
    identity = "fixture_reader"
    def __init__(self):
        self.calls = 0
    def __call__(self, tile, name, record):
        self.calls += 1
        d, p = fixture()
        d["node"] = f"Tile_{tile}/{name}"
        return d, memoryview(p)


def ready(store, *, parent=None):
    deadline = time.monotonic() + 4
    while True:
        result = store.plan(1, depth=1 if parent is None else None, parent=parent)
        if result is not None:
            return result
        if time.monotonic() >= deadline:
            raise AssertionError("memory job did not finish")
        time.sleep(.005)


class Pages(unittest.TestCase):
    def bundle(self, **options):
        return build_bundle(1, Catalog()(1), Reader(), recipe_identity="test", **options)

    def test_original_geometry_image_and_sampler(self):
        bundle = self.bundle(depth=1)
        marker = bundle.marker()
        self.assertEqual(marker["source_format"], FORMAT)
        part = marker["parts"][0]
        self.assertEqual(part["gpu_payload_bytes"], 3*64+12+4)
        self.assertEqual(part["source_image"]["sampler"]["wrapS"], 33071)
        self.assertEqual(part["source_image"]["source_origin"], "bottom_left")
        self.assertEqual(bundle.resources[("part_000", "geometry.bin")][0], fixture()[1][4:])
        image = Image.open(io.BytesIO(bundle.resources[("part_000", "texture.png")][0]))
        self.assertEqual(image.tobytes(), fixture()[1][:4])
        gltf = json.loads(bundle.resources[("part_000", "geometry.gltf")][0])
        self.assertNotIn("extensionsUsed", gltf)
        self.assertNotIn("mode", gltf["meshes"][0]["primitives"][0])
        self.assertEqual(set(gltf["meshes"][0]["primitives"][0]["attributes"]), {"POSITION", "TEXCOORD_0"})
        self.assertEqual(marker["source_nodes"][0]["bounds_min"], [0, 0, 0])
        self.assertEqual(marker["source_nodes"][0]["bounds_max"], [1, 1, 0])
        self.assertAlmostEqual(marker["longest_edge_p90_m"], 2**.5)
        self.assertGreater(marker["texel_world_p90_m"], 0)

    def test_complete_family_and_deterministic_rebuild(self):
        a, b = self.bundle(parent=ROOT), self.bundle(parent=ROOT)
        self.assertEqual(a.marker_json, b.marker_json)
        self.assertEqual(dict(a.resources), dict(b.resources))
        self.assertEqual(a.marker()["parent_source_sha256"], "a"*64)
        self.assertEqual([n["name"] for n in a.marker()["source_nodes"]], [CHILD])
        self.assertTrue(a.marker()["complete_sibling_family"])
        marker = a.marker()
        marker["indices"] = -1
        self.assertEqual(a.marker()["indices"], 3)
        with self.assertRaises(TypeError):
            a.resources["tamper"] = b"x"

    def test_non_power_two_mips_count_real_dimensions(self):
        self.assertEqual(mip_bytes(3, 5), (15+2+1)*4)
        for pair in ((0, 2), (True, 2), (8193, 1)):
            with self.assertRaises(ValueError):
                mip_bytes(*pair)

    def test_missing_child_cycle_path_and_wrong_reader_rejected(self):
        for mutate in (lambda c:c["nodes"][0]["children"].append("missing.osgb"),
                       lambda c:c["nodes"][1]["children"].append(ROOT),
                       lambda c:c.update(source_directory="../Data/Tile_1")):
            catalog = Catalog()(1)
            mutate(catalog)
            with self.assertRaises(ValueError):
                build_bundle(1, catalog, Reader(), depth=1, recipe_identity="test")
        def wrong(tile, name, record):
            d, p = fixture()
            return d, memoryview(p)
        with self.assertRaises(ValueError):
            build_bundle(1, Catalog()(1), wrong, depth=1, recipe_identity="test")

    def test_alpha_and_complete_page_limit_refuse_partial_delivery(self):
        class Alpha(Reader):
            def __call__(self, *args):
                d, p = super().__call__(*args)
                p = bytearray(p)
                p[3] = 254
                return d, memoryview(p)
        with self.assertRaises(ValueError):
            build_bundle(1, Catalog()(1), Alpha(), depth=1, recipe_identity="test")
        class Many(Reader):
            def __call__(self, *args):
                d, p = super().__call__(*args)
                d["meshes"] = d["meshes"]*65
                return d, p
        with self.assertRaisesRegex(ValueError, "64-page"):
            build_bundle(1, Catalog()(1), Many(), depth=1, recipe_identity="test")


class Store(unittest.TestCase):
    def make(self, reader=None, **options):
        store = MemorySourceStore(Catalog(), reader or Reader(), **options)
        self.addCleanup(store.close)
        return store

    def test_one_job_same_request_and_no_partial_plan(self):
        gate = threading.Event()
        started = threading.Event()
        class Slow(Reader):
            def __call__(self, *args):
                started.set()
                gate.wait(2)
                return super().__call__(*args)
        reader = Slow()
        store = self.make(reader)
        self.assertIsNone(store.plan(1, depth=1))
        self.assertTrue(started.wait(1))
        for _ in range(10):
            self.assertIsNone(store.grant(1, depth=1))
        gate.set()
        plan = ready(store)
        self.assertEqual(reader.calls, 1)
        self.assertFalse(plan["availabilityVerified"])
        self.assertNotIn("cache_lease", plan["marker"])
        self.assertLessEqual(store.audit()["peakEncodedAndReservation"], 256*MIB)

    def test_lease_ownership_release_and_expiry(self):
        clock = [0]
        store = self.make(clock=lambda: clock[0])
        ready(store)
        marker, digest = store.grant(1, depth=1)
        token = marker["cache_lease"]
        self.assertEqual(len(digest), 64)
        value = store.payload(token, "tile_1_depth_1", "part_000", "texture.png")
        self.assertEqual(value[1], "image/png")
        with self.assertRaises(PermissionError):
            store.payload(token, "family_tile_1_"+"a"*16, "part_000", "texture.png")
        with self.assertRaises(ValueError):
            store.payload(token, "tile_1_depth_1", "part_000", "atlas.jpg")
        self.assertTrue(store.release(token))
        self.assertFalse(store.release(token))
        marker, _ = store.grant(1, depth=1)
        clock[0] = 181
        with self.assertRaises(PermissionError):
            store.payload(marker["cache_lease"], "tile_1_depth_1", "part_000", "geometry.bin")
        self.assertEqual(store.audit()["activeLeases"], 0)

    def test_leased_bundle_cannot_be_evicted_for_build_reservation(self):
        # This tiny encoded-cache fixture exercises policy without allocating hundreds of MiB.
        probe = build_bundle(1, Catalog()(1), Reader(), depth=1, recipe_identity="test")
        size = probe.delivery_bytes + 1000
        store = self.make(limit=size, build_reservation=size)
        ready(store)
        marker, _ = store.grant(1, depth=1)
        store.plan(1, parent=ROOT)
        with self.assertRaises(ValueError):
            ready(store, parent=ROOT)
        self.assertEqual(store.audit()["bundles"], 1)
        self.assertEqual(store.audit()["evictions"], 0)
        self.assertTrue(store.payload(marker["cache_lease"], "tile_1_depth_1", "part_000", "texture.png"))

    def test_unleased_eviction_rebuild_has_same_identity(self):
        probe = build_bundle(1, Catalog()(1), Reader(), depth=1, recipe_identity="test")
        size = probe.delivery_bytes + 1000
        store = self.make(limit=size, build_reservation=size)
        first = ready(store)["markerSHA256"]
        ready(store, parent=ROOT)
        again = ready(store)["markerSHA256"]
        self.assertEqual(first, again)
        self.assertEqual(store.audit()["builds"], 3)
        self.assertEqual(store.audit()["evictions"], 2)

    def test_failed_build_is_not_restarted_by_polling(self):
        class Bad(Reader):
            def __call__(self, *args):
                self.calls += 1
                raise ValueError("rejected source")
        reader = Bad()
        store = self.make(reader)
        for _ in range(5):
            with self.assertRaises(ValueError):
                ready(store)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(store.audit()["failures"], 1)

    def test_pending_queue_refuses_a_different_request_before_starting_it(self):
        gate = threading.Event()
        class Slow(Reader):
            def __call__(self, *args):
                gate.wait(2)
                return super().__call__(*args)
        store = self.make(Slow(), max_jobs=1)
        self.assertIsNone(store.plan(1, depth=1))
        try:
            with self.assertRaises(MemoryStoreBusy):
                store.plan(1, parent=ROOT)
            self.assertEqual(store.audit()["queuedJobs"], 1)
        finally:
            gate.set()
        ready(store)

    def test_queue_bounded_and_lease_count_bounded(self):
        store = self.make(max_leases=1)
        ready(store)
        store.grant(1, depth=1)
        with self.assertRaises(MemoryStoreBusy):
            store.grant(1, depth=1)
        for values in ((True, 1, None), (1, 1, ROOT), (1, None, "../wrong")):
            with self.assertRaises(ValueError):
                store.key(*values)


if __name__ == "__main__":
    unittest.main()

