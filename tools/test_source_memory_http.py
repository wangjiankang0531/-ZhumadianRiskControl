import json
from pathlib import Path
import sys
import threading
import unittest
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_source_memory_store import Catalog, Reader, ready
from readonly_source_memory_store import MemorySourceStore
from source_memory_http import MemorySourceHTTP


class NoFilesystemFallback(BaseHTTPRequestHandler):
    def _native_response(self, head=False):
        raise AssertionError("new memory route fell through to filesystem")
    def _source_plans_enabled(self):
        return False
    def _readonly_plan(self, *args, **kwargs):
        raise AssertionError("legacy producer reached")
    def _readonly_bundle(self, *args, **kwargs):
        raise AssertionError("legacy lease reached")


class HTTP(unittest.TestCase):
    def setUp(self):
        store = MemorySourceStore(Catalog(), Reader())
        ready(store)
        class Handler(MemorySourceHTTP, NoFilesystemFallback):
            memory_sources = store
            def do_GET(self):
                if self.path.split("?")[0] == "/plan":
                    return self._readonly_plan(1, depth=1)
                if self.path.split("?")[0] == "/bundle":
                    return self._readonly_bundle(1, depth=1)
                if not self._native_response():
                    self.send_error(404)
            def do_HEAD(self):
                self._native_response(True)
            def log_message(self, *args):
                pass
        self.store = store
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.store.close()

    def request(self, path, method="GET"):
        try:
            response = urllib.request.urlopen(urllib.request.Request(self.base+path, method=method))
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def test_plan_bundle_header_and_exact_leased_payload(self):
        status, headers, raw = self.request("/plan")
        self.assertEqual(status, 200)
        plan = json.loads(raw)
        self.assertNotIn("cache_lease", plan["marker"])
        status, headers, raw = self.request("/bundle")
        self.assertEqual(status, 200)
        marker = json.loads(raw)
        self.assertEqual(headers["X-XNBY-Source-Marker-SHA256"], plan["markerSHA256"])
        token = marker["cache_lease"]
        path = f"/native/tile_1_depth_1/part_000/texture.png?lease={token}"
        status, headers, raw = self.request(path)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        head_status, head_headers, head_raw = self.request(path, "HEAD")
        self.assertEqual(head_status, 200)
        self.assertEqual(int(head_headers["Content-Length"]), len(raw))
        self.assertEqual(head_raw, b"")
        self.store.release(token)
        self.assertEqual(self.request(path)[0], 409)

    def test_missing_or_foreign_lease_and_path_escape_never_fall_through(self):
        for path in ("/native", "/native/tile_1_depth_1/part_000/atlas.jpg",
                     "/native/tile_1_depth_1/part_000/../../geometry.bin",
                     "/native/tile_1_depth_1/part_000/texture.png",
                     "/native/tile_1_depth_1/part_000/texture.png?lease="+"a"*32,
                     "/native/tile_1_depth_1/part_000/texture.png?lease="+"a"*32+"&lease="+"b"*32):
            with self.subTest(path=path):
                self.assertIn(self.request(path)[0], (400, 409, 422))
        self.assertEqual(self.request("/bundle?extra=1")[0], 400)
        self.assertEqual(self.request("/plan?extra=1")[0], 400)

    def test_metadata_pending_returns_202_without_a_lease(self):
        gate = threading.Event()
        class Slow(Reader):
            def __call__(self, *args):
                gate.wait(2)
                return super().__call__(*args)
        other = MemorySourceStore(Catalog(), Slow())
        original = self.server.RequestHandlerClass.memory_sources
        self.server.RequestHandlerClass.memory_sources = other
        try:
            status, headers, raw = self.request("/plan")
            self.assertEqual(status, 202)
            self.assertEqual(headers["Retry-After"], "1")
            self.assertNotIn("cache_lease", json.loads(raw))
            self.assertEqual(other.audit()["activeLeases"], 0)
        finally:
            gate.set()
            other.close()
            self.server.RequestHandlerClass.memory_sources = original


if __name__ == "__main__":
    unittest.main()

