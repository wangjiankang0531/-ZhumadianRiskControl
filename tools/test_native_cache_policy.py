import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import native_cache_policy as policy
from native_cache_leases import LeaseRegistry


def make_bundle(cache, name, size=40, stamp=1):
    folder = cache / name
    part = folder / "part_000"
    part.mkdir(parents=True)
    (folder / "complete.json").write_text("{}")
    (part / "geometry.bin").write_bytes(b"x" * size)
    for p in policy.files_in(folder):
        os.utime(p, (stamp, stamp))
    return folder


class CachePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name) / "cache"
        self.cache.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_family_and_root_share_limit_and_lru(self):
        old = make_bundle(self.cache, "family_tile_1_0123456789abcdef", 60, 1)
        new = make_bundle(self.cache, "tile_2_depth_5", 60, 2)
        result = policy.prune(self.cache, limit=70)
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        self.assertLessEqual(result["remaining_bytes"], 70)

    def test_cross_process_native_handoff_pin_blocks_prune(self):
        a = make_bundle(self.cache, "tile_1_depth_5")
        b = make_bundle(self.cache, "family_tile_1_0123456789abcdef")
        script = "import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import native_cache_policy as p;lock=p.tile_lock(Path(sys.argv[2]),1);print('ready',flush=True);sys.stdin.readline();lock.close()"
        child = subprocess.Popen(
            [sys.executable, "-c", script, str(Path(__file__).parent), str(self.cache)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), "ready")
            report = policy.prune(self.cache, limit=0)
            self.assertTrue(a.exists() and b.exists())
            self.assertGreater(report["over_limit_bytes"], 0)
        finally:
            child.communicate("\n", timeout=10)
            if child.poll() is None:
                child.kill()
                child.wait()
        policy.prune(self.cache, limit=0)
        self.assertFalse(a.exists() or b.exists())

    def test_active_readers_share_but_writer_cannot_replace(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        with policy.bundle_lock(self.cache, folder.name):
            with policy.bundle_lock(self.cache, folder.name):
                with self.assertRaises(TimeoutError):
                    with policy.bundle_lock(
                        self.cache, folder.name, exclusive=True, timeout=0
                    ):
                        pass
            policy.prune(self.cache, limit=0)
            self.assertTrue(folder.exists())
        with policy.bundle_lock(self.cache, folder.name, exclusive=True, timeout=0):
            pass
        policy.prune(self.cache, limit=0)
        self.assertFalse(folder.exists())

    def test_unknown_files_are_preserved_and_reported_over_limit(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        (folder / "user-note.txt").write_text("keep")
        external = self.cache.parent / "original.osgb"
        external.write_bytes(b"original")
        report = policy.prune(self.cache, limit=0)
        self.assertEqual((folder / "user-note.txt").read_text(), "keep")
        self.assertEqual(external.read_bytes(), b"original")
        self.assertGreater(report["over_limit_bytes"], 0)

    def test_junction_part_never_traversed(self):
        outside = self.cache.parent / "source"
        outside.mkdir()
        (outside / "geometry.bin").write_bytes(b"ORIGINAL")
        folder = self.cache / "tile_1_depth_5"
        folder.mkdir()
        link = folder / "part_000"
        if os.name == "nt":
            subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(link), str(outside)],
                check=True,
                capture_output=True,
            )
        else:
            link.symlink_to(outside, target_is_directory=True)
        try:
            policy.prune(self.cache, limit=0)
            self.assertEqual((outside / "geometry.bin").read_bytes(), b"ORIGINAL")
        finally:
            if os.name == "nt":
                os.rmdir(link)
            else:
                link.unlink()

    def test_invalid_bundle_and_outside_lock_paths_rejected(self):
        for name in [
            "../source",
            "family_tile_9999_0123456789abcdef",
            "tile_0_depth_5",
        ]:
            with self.assertRaises(ValueError):
                with policy.bundle_lock(self.cache, name):
                    pass

    def test_web_batch_pins_until_release(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        registry = LeaseRegistry(janitor=False)
        try:
            token = registry.grant(self.cache, folder.name, lambda: True)
            policy.prune(self.cache, limit=0)
            self.assertTrue(folder.exists())
            with registry.use(token, self.cache, folder.name):
                pass
            with self.assertRaises(PermissionError):
                with registry.use(token, self.cache, "tile_2_depth_5"):
                    pass
            registry.release(token)
            policy.prune(self.cache, limit=0)
            self.assertFalse(folder.exists())
        finally:
            registry.close()

    def test_expiry_releases_abandoned_batch_but_active_response_remains_pinned(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        registry = LeaseRegistry(ttl=0.04, janitor=False)
        try:
            token = registry.grant(self.cache, folder.name, lambda: True)
            with registry.use(token, self.cache, folder.name):
                time.sleep(0.05)
                registry.expire()
                policy.prune(self.cache, limit=0)
                self.assertTrue(folder.exists())
            with self.assertRaises(PermissionError):
                with registry.use(token, self.cache, folder.name):
                    pass
            policy.prune(self.cache, limit=0)
            self.assertFalse(folder.exists())
        finally:
            registry.close()

    def test_failed_grant_and_capacity_do_not_leak_locks(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        registry = LeaseRegistry(maximum=1, janitor=False)
        try:
            with self.assertRaises(FileNotFoundError):
                registry.grant(self.cache, folder.name, lambda: False)
            token = registry.grant(self.cache, folder.name, lambda: True)
            with self.assertRaises(RuntimeError):
                registry.grant(self.cache, folder.name, lambda: True)
            registry.release(token)
            with policy.bundle_lock(self.cache, folder.name, True, 0):
                pass
        finally:
            registry.close()

    def test_unchanged_cache_does_not_scan_on_release(self):
        policy.prune(self.cache)
        with patch.object(
            policy, "prune", side_effect=AssertionError("unexpected full scan")
        ):
            self.assertEqual(policy.maintain(self.cache)["skipped"], "cache unchanged")

    def test_growth_accounting_clears_only_after_budget_is_satisfied(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        policy.mark_dirty(self.cache)
        with policy.bundle_lock(self.cache, folder.name):
            report = policy.prune(self.cache, limit=0)
            self.assertGreater(report["over_limit_bytes"], 0)
            self.assertIsNotNone(policy.maintenance_token(self.cache))
        policy.prune(self.cache, limit=0)
        self.assertIsNone(policy.maintenance_token(self.cache))
        self.assertFalse(folder.exists())

    def test_new_growth_during_scan_is_not_lost(self):
        make_bundle(self.cache, "tile_1_depth_5")
        policy.mark_dirty(self.cache)
        remove = policy.remove_bundle

        def grow(cache, folder):
            remove(cache, folder)
            policy.mark_dirty(cache)

        with patch.object(policy, "remove_bundle", side_effect=grow):
            policy.prune(self.cache, limit=0)
        self.assertIsNotNone(policy.maintenance_token(self.cache))
        policy.maintain(self.cache)
        self.assertIsNone(policy.maintenance_token(self.cache))

    def test_janitor_services_pending_growth_after_last_batch_released(self):
        folder = make_bundle(self.cache, "tile_1_depth_5")
        registry = LeaseRegistry(janitor=False)
        try:
            token = registry.grant(self.cache, folder.name, lambda: True)
            registry.release(token)
            policy.mark_dirty(self.cache)
            registry.expire()
            self.assertFalse(registry.entries)
            self.assertIsNone(policy.maintenance_token(self.cache))
        finally:
            registry.close()

    def test_corrupt_accounting_is_rebuilt_instead_of_silently_skipped(self):
        make_bundle(self.cache, "tile_1_depth_5")
        (self.cache / "prune_status.json").write_text("invalid")
        report = policy.maintain(self.cache)
        self.assertGreater(report["remaining_bytes"], 0)
        self.assertEqual(report["over_limit_bytes"], 0)

    def test_missing_and_wrong_shape_accounting_trigger_one_rebuild(self):
        make_bundle(self.cache, "tile_1_depth_5")
        status = self.cache / "prune_status.json"
        for content in [
            None,
            "[]",
            '{"over_limit_bytes":"0"}',
            '{"over_limit_bytes":0}',
            '{"limit_bytes":1,"remaining_bytes":2,"over_limit_bytes":0}',
        ]:
            with self.subTest(content=content):
                status.unlink(missing_ok=True)
                if content is not None:
                    status.write_text(content)
                report = policy.maintain(self.cache)
                self.assertGreater(report["remaining_bytes"], 0)
                self.assertEqual(
                    policy.maintain(self.cache)["skipped"], "cache unchanged"
                )

    def test_binary_dirty_request_is_reconciled_without_parser_failure(self):
        make_bundle(self.cache, "tile_1_depth_5")
        (self.cache / "maintenance.request").write_bytes(b"\xff\x00")
        policy.maintain(self.cache)
        self.assertIsNone(policy.maintenance_token(self.cache))


if __name__ == "__main__":
    unittest.main()
