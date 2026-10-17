import concurrent.futures
import http.client
import http.server
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import landscape_web_server as web


class FamilyHttpTests(unittest.TestCase):
    def setUp(self):
        class Handler(web.Handler):
            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.jobs = patch.object(web, "JOBS", {})
        self.jobs.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.jobs.stop()

    def get(self, path):
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def test_complete_family_response_and_derived_route(self):
        marker = {
            "schema": "xnby.osgb_native_family.v1",
            "complete_sibling_family": True,
            "replacement_parent": "Tile_141_L21_0uuuu00.osgb",
        }
        ready = concurrent.futures.Future()
        ready.set_result(marker)
        with patch.object(web.POOL, "submit", return_value=ready) as worker, patch.object(web.CACHE_LEASES,"grant",return_value="a"*32):
            status, body, headers = self.get(
                "/api/lod-family/141/Tile_141_L21_0uuuu00.osgb"
            )
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), {**marker,"cache_lease":"a"*32})
            self.assertIn("no-store", headers["Cache-Control"])
            worker.assert_called_once()
        handler = web.Handler.__new__(web.Handler)
        path = handler.translate_path(
            "/native/family_tile_141_be3b6f4853ba4a36/part_000/geometry.gltf"
        )
        self.assertTrue(
            Path(path)
            .as_posix()
            .endswith("family_tile_141_be3b6f4853ba4a36/part_000/geometry.gltf")
        )

    def test_invalid_tile_identity_parent_and_source_paths_are_not_scheduled(self):
        with patch.object(web.POOL, "submit") as worker:
            for route in [
                "/api/lod-family/0/Tile_0_L21_0u.osgb",
                "/api/lod-family/141/Tile_142_L21_0u.osgb",
                "/api/lod-family/141/../secrets",
                "/api/lod-family/141/Tile_141_L21_0u.osgb%2fextra",
            ]:
                self.assertEqual(self.get(route)[0], 400)
            worker.assert_not_called()
        for route in [
            "/native/family_tile_141_be3b6f4853ba4a36/../complete.json",
            "/native/family_tile_141_be3b6f4853ba4a36/complete.json",
            "/native/family_tile_141_be3b6f4853ba4a36/part_000/frontier.obj",
        ]:
            self.assertEqual(self.get(route)[0], 404)

    def test_queue_is_bounded_and_failure_keeps_parent_available(self):
        web.JOBS.update(
            {
                (1, "pending"): concurrent.futures.Future(),
                (2, "pending"): concurrent.futures.Future(),
            }
        )
        with patch.object(web.POOL, "submit") as worker:
            self.assertEqual(
                self.get("/api/lod-family/141/Tile_141_L21_0u.osgb")[0], 202
            )
            worker.assert_not_called()
        web.JOBS.clear()
        failed = concurrent.futures.Future()
        failed.set_exception(
            ValueError("complete sibling family exceeds local candidate budget")
        )
        with patch.object(web.POOL, "submit", return_value=failed):
            status, body, _ = self.get("/api/lod-family/141/Tile_141_L21_0u.osgb")
            self.assertEqual(status, 422)
            self.assertIn(b"budget", body)


if __name__ == "__main__":
    unittest.main()
