"""Check the read-only business snapshot route against a live loopback HTTP server."""
import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parent / 'landscape_web_server.py'
spec = importlib.util.spec_from_file_location('xnby_test_web_server', SERVER_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        app = root / 'Application'
        app.mkdir()
        (root / 'Assets' / 'BusinessData').mkdir(parents=True)
        self.default = root / 'Assets/BusinessData/business_records.json'
        self.snapshot = {'schema': 'xnby.business.records.v1', 'scene': 'zhumadian',
                         'exportedAt': '2026-10-13T00:00:00Z', 'ttlHours': 24, 'records': []}
        self.default.write_text(json.dumps(self.snapshot), encoding='utf-8')
        (root / 'Assets' / 'Spatial').mkdir()
        self.spatial = root / 'Assets/Spatial/spatial_catalog.json'
        self.spatial.write_text(json.dumps({'schema':'xnby.spatial.catalog.v1','objects':[]}), encoding='utf-8')
        class QuietHandler(module.Handler):
            def log_message(self, *args):
                pass
        QuietHandler.root = app
        QuietHandler.business = None
        QuietHandler.spatial = None
        self.handler = QuietHandler
        self.server = module.http.server.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def get(self, path='/business/default.json', method='GET', data=None):
        return urllib.request.urlopen(urllib.request.Request(self.url + path, method=method, data=data), timeout=5)

    def test_portal_static_routes_are_exact_and_read_only(self):
        dist = self.handler.root / 'apps/landscape_web/dist'
        dist.mkdir(parents=True)
        for name in ('portal.html', 'portal.js', 'portal.css'):
            body = ('test ' + name).encode('utf-8')
            (dist / name).write_bytes(body)
            with self.get('/' + name) as response:
                self.assertEqual(response.read(), body)
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            with self.get('/' + name, method='HEAD') as response:
                self.assertEqual(response.read(), b'')
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get('/' + name, method='POST', data=b'change')
            self.assertEqual(error.exception.code, 501)
            self.assertEqual((dist / name).read_bytes(), body)
        for route in ('/portal_modules.js', '/portal/secret.json', '/portal.html/extra', '/%2e%2e/portal.html'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get(route)
            self.assertEqual(error.exception.code, 404)

    def test_canonical_snapshot_get_and_head(self):
        with self.get() as response:
            self.assertEqual(json.load(response), self.snapshot)
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            self.assertIn('no-store', response.headers['Cache-Control'])
        with self.get(method='HEAD') as response:
            self.assertEqual(response.read(), b'')
            self.assertGreater(int(response.headers['Content-Length']), 0)

    def test_explicit_publication_path_and_unpublished_file(self):
        configured = Path(self.temp.name) / 'configured.json'
        changed = {**self.snapshot, 'ttlHours': 48}
        configured.write_text(json.dumps(changed), encoding='utf-8')
        self.handler.business = configured
        with self.get() as response:
            self.assertEqual(json.load(response)['ttlHours'], 48)
        self.handler.business = configured.with_name('missing.json')
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get()
        self.assertEqual(error.exception.code, 404)

    def test_oversized_snapshot_rejected_before_body_transfer(self):
        with self.default.open('wb') as output:
            output.truncate(8 * 1048576 + 1)
        for method in ('GET', 'HEAD'):
            for route in ('/business/default.json','/business/%64efault.json','/business%2Fdefault.json'):
                with self.assertRaises(urllib.error.HTTPError) as error:
                    self.get(route, method=method)
                self.assertEqual(error.exception.code, 413)

    def test_no_write_methods_and_no_arbitrary_file_routes(self):
        before = self.default.read_bytes()
        for method in ('POST', 'PUT', 'DELETE'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get(method=method, data=b'changed')
            self.assertEqual(error.exception.code, 501)
        for route in ('/business/other.json', '/business/%2e%2e/secret.json', '/business/default.json%00', '/business%5cdefault.json'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get(route)
            self.assertEqual(error.exception.code, 404)
        self.assertEqual(self.default.read_bytes(), before)


    def test_spatial_directory_get_head_and_fixed_publication_path(self):
        with self.get('/spatial/default.json') as response:
            self.assertEqual(json.load(response)['schema'], 'xnby.spatial.catalog.v1')
            self.assertIn('no-store', response.headers['Cache-Control'])
        with self.get('/spatial/default.json', method='HEAD') as response:
            self.assertEqual(response.read(), b'')
        self.handler.spatial = Path(self.temp.name) / 'configured_spatial.json'
        self.handler.spatial.write_text('{"objects":[1]}', encoding='utf-8')
        with self.get('/spatial/default.json') as response:
            self.assertEqual(json.load(response)['objects'], [1])

    def test_spatial_directory_missing_size_limit_and_read_only(self):
        before = self.spatial.read_bytes()
        for method in ('POST', 'PUT', 'DELETE'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get('/spatial/default.json', method=method, data=b'changed')
            self.assertEqual(error.exception.code, 501)
        self.assertEqual(self.spatial.read_bytes(), before)
        for route in ('/spatial/other.json', '/spatial/%2e%2e/secret.json', '/spatial/default.json%00', '/spatial%5cdefault.json'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get(route)
            self.assertEqual(error.exception.code, 404)
        with self.spatial.open('wb') as output:
            output.truncate(4 * 1048576 + 1)
        for method in ('GET', 'HEAD'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get('/spatial/default.json', method=method)
            self.assertEqual(error.exception.code, 413)
            for route in ('/spatial/%64efault.json','/spatial%2Fdefault.json'):
                with self.assertRaises(urllib.error.HTTPError) as error:
                    self.get(route, method=method)
                self.assertEqual(error.exception.code, 413)
        self.spatial.unlink()
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/spatial/default.json')
        self.assertEqual(error.exception.code, 404)


    def test_prepared_base_quality_exact_route_read_only_and_bounded(self):
        target = self.handler.root / "assets/showcase/runtime/zhumadian/full/base_lod_quality.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"schema":"xnby.base.lod.quality.v1"}')
        route = "/assets/showcase/runtime/zhumadian/full/base_lod_quality.json"
        with self.get(route) as response:
            self.assertEqual(json.load(response)["schema"], "xnby.base.lod.quality.v1")
        with self.get(route, method="HEAD") as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(route, method="POST", data=b"{}").close()
        self.assertEqual(error.exception.code, 501)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(route.replace("base_lod_quality.json", "other.json")).close()
        self.assertEqual(error.exception.code, 404)
        target.write_bytes(b" " * (1048576 + 1))
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(route).close()
        self.assertEqual(error.exception.code, 413)


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        module.POOL.shutdown(wait=True, cancel_futures=True)
