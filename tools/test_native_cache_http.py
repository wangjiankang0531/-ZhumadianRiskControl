import concurrent.futures
import hashlib
import http.client
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from tools import landscape_web_server as web
import native_cache_policy as policy
from native_cache_leases import LeaseRegistry


class CacheHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cache = self.root / "work/zhumadian_native_chunk_cache"
        self.cache.mkdir(parents=True)
        self.folder = self.cache / "tile_141_depth_5"
        part = self.folder / "part_000"
        part.mkdir(parents=True)
        for name, data in [
            ("geometry.gltf", b'{"buffers":[{"uri":"geometry.bin"}]}'),
            ("geometry.bin", b"geometry"),
            ("atlas.jpg", b"texture"),
        ]:
            (part / name).write_bytes(data)
        self.marker = {
            "complete_frontier": True,
            "parts": [
                {
                    "directory": "part_000",
                    "files": [
                        {"name": p.name, "bytes": p.stat().st_size}
                        for p in part.iterdir()
                    ],
                }
            ],
        }
        (self.folder / "complete.json").write_text(json.dumps(self.marker))
        future = concurrent.futures.Future()
        future.set_result(self.marker)

        class Handler(web.Handler):
            root = self.root

            def log_message(self, *args):
                pass

        self.registry = LeaseRegistry(janitor=False)
        self.patches = [
            patch.object(web, "JOBS", {(141, 5): future}),
            patch.object(web, "CACHE_LEASES", self.registry),
            patch.object(
                web,
                "bundle_present",
                lambda *args: (self.folder / "complete.json").exists(),
            ),
        ]
        for item in self.patches:
            item.start()
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.registry.close()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def request(self, url, method="GET"):
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            c.request(method, url)
            r = c.getresponse()
            return r.status, r.read()
        finally:
            c.close()

    def grant(self):
        status, body = self.request("/api/lod/141/5")
        self.assertEqual(status, 200, body)
        return json.loads(body)["cache_lease"]

    def test_full_batch_survives_interleaved_prune_and_releases(self):
        token = self.grant()
        for filename in ["geometry.gltf", "geometry.bin", "atlas.jpg"]:
            policy.prune(self.cache, limit=0)
            self.assertTrue(self.folder.exists())
            status, body = self.request(
                f"/native/tile_141_depth_5/part_000/{filename}?lease={token}"
            )
            self.assertEqual(status, 200)
            self.assertTrue(body)
        self.assertEqual(
            self.request(f"/api/lod-lease/{token}/release", "POST")[0], 204
        )
        policy.prune(self.cache, limit=0)
        self.assertFalse(self.folder.exists())
        self.assertEqual(
            self.request(
                f"/native/tile_141_depth_5/part_000/geometry.bin?lease={token}"
            )[0],
            409,
        )

    def test_mismatched_expired_malformed_leases_and_head(self):
        token = self.grant()
        path = "/native/tile_141_depth_5/part_000/geometry.bin"
        self.assertEqual(self.request(path + "?lease=" + token, "HEAD")[0], 200)
        self.assertEqual(self.request(path + "?lease=bad")[0], 400)
        self.assertEqual(
            self.request(path + "?lease=" + token + "&lease=" + token)[0], 400
        )
        self.assertEqual(
            self.request(
                "/native/tile_142_depth_5/part_000/geometry.bin?lease=" + token
            )[0],
            409,
        )
        self.registry.release(token)
        self.assertEqual(self.request(path + "?lease=" + token, "HEAD")[0], 409)

    def test_file_head_without_batch_lease_still_protects_response(self):
        self.assertEqual(
            self.request("/native/tile_141_depth_5/part_000/geometry.bin", "HEAD")[0],
            200,
        )

    def test_release_unknown_token_is_idempotent_and_other_writes_denied(self):
        self.assertEqual(
            self.request("/api/lod-lease/" + "a" * 32 + "/release", "POST")[0], 204
        )
        self.assertEqual(self.request("/layers/default.json", "POST")[0], 501)


if __name__ == "__main__":
    unittest.main()
