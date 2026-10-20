import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from indexed_family_source import IndexedFamilyHTTP, IndexedFamilyStore, LevelIndexProvider
from landscape_level_index import Camera, finalize_tile
from osgb_memory_pages import canonical, sha
from test_indexed_source_bundle import catalog, R, A, A1, A2, B, F
from test_source_memory_store import Reader


class Reader(Reader):
    def __call__(self, *args):
        descriptor, payload = super().__call__(*args)
        for image in descriptor['images']:
            image.update(originalWidth=image['width'], originalHeight=image['height'],
                         sourceRect=[0,0,image['width'],image['height']])
        return descriptor, payload


class Catalogs:
    identity = 'f'*64
    records = {1: {'sha256': 'a'*64}}
    def __call__(self, tile):
        if tile != 1:
            raise KeyError(tile)
        c = catalog()
        for n in c['nodes']:
            n['level'] = int(n['name'].split('_L')[1].split('_')[0])
        return c


class IndexedServiceTests(unittest.TestCase):
    def setup_provider(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        catalogs = Catalogs()
        c = catalogs(1)
        exact = {n['name']: dict(sourceSHA256=n['sha256'], sourceBytes=n['bytes'],
                                 boundsMin=[-1, 10, -1], boundsMax=[1, 11, 1],
                                 edgeP90=.1 if n['name'] in (A2, B, F) else 20, texelP90=.01)
                 for n in c['nodes']}
        tile = finalize_tile(c, exact)
        tile.update(catalogSHA256='a'*64)
        raw = canonical(tile)
        (directory/'tile_1.json').write_bytes(raw)
        (directory/'index_manifest.json').write_bytes(canonical(dict(
            schema='zhumadian.level_bounds.manifest.v1', sourceManifestSHA256=catalogs.identity,
            tiles=[dict(tile=1, path='tile_1.json', bytes=len(raw), sha256=sha(raw))])))
        return directory, catalogs, LevelIndexProvider(directory, catalogs)

    def test_pinned_tile_identity_and_incomplete_graph_refused(self):
        directory, catalogs, provider = self.setup_provider()
        self.assertTrue(provider.tile(1)['complete'])
        (directory/'tile_1.json').write_bytes(b'changed')
        fresh = LevelIndexProvider(directory, catalogs)
        with self.assertRaises(ValueError):
            fresh.tile(1)
        manifest = json.loads((directory/'index_manifest.json').read_bytes())
        manifest['sourceManifestSHA256'] = '0'*64
        (directory/'index_manifest.json').write_bytes(canonical(manifest))
        with self.assertRaises(ValueError):
            LevelIndexProvider(directory, catalogs)

    def test_same_indexed_view_has_one_job_and_is_a_complete_descendant_cut(self):
        _, catalogs, provider = self.setup_provider()
        reader = Reader()
        store = IndexedFamilyStore(catalogs, reader, provider)
        self.addCleanup(store.close)
        camera = Camera((0, 0, 0), (0, 1, 0), 90, 1, 100)
        key = store.register_view(1, A, camera)
        self.assertEqual(key, store.register_view(1, A, camera))
        deadline = time.monotonic()+3
        while True:
            plan = store.plan(1, parent=key)
            if plan is not None:
                break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.005)
        self.assertEqual({F, A2}, {n['name'] for n in plan['marker']['source_nodes']})
        self.assertEqual(2, reader.calls)
        granted, digest = store.grant(1, parent=key)
        folder = 'family_tile_1_'+granted['family_key']
        raw, media = store.payload(granted['cache_lease'], folder, 'part_000', 'geometry.bin')
        self.assertTrue(raw)
        self.assertEqual(digest, plan['markerSHA256'])
        self.assertTrue(store.release(granted['cache_lease']))
        with self.assertRaises(PermissionError):
            store.payload(granted['cache_lease'], folder, 'part_000', 'geometry.bin')

    def test_real_loopback_plan_lease_payload_and_invalid_view(self):
        _, catalogs, provider = self.setup_provider()
        store = IndexedFamilyStore(catalogs, Reader(), provider)
        self.addCleanup(store.close)
        class Base(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                if not self._native_response():
                    self.send_error(404)
        class Handler(IndexedFamilyHTTP, Base):
            memory_sources = store
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join(2)))
        root = f'http://127.0.0.1:{server.server_port}'
        route = root+f'/api/lod-index-family-plan/1/{A}?view=0,0,0,0,1,0,90,1,100,6'
        deadline = time.monotonic()+3
        while True:
            with urlopen(route) as response:
                value = json.load(response)
                if response.status == 200:
                    break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.005)
        with urlopen(root+'/api/lod-index-family/1/'+value['indexedRequest']) as response:
            leased = json.load(response)
        folder = 'family_tile_1_'+leased['family_key']
        with urlopen(root+f'/native/{folder}/part_000/geometry.bin?lease='+leased['cache_lease']) as response:
            self.assertGreater(len(response.read()), 0)
        self.assertEqual({F, A2}, {n['name'] for n in leased['source_nodes']})
        for invalid in ('nan,0,0,0,1,0,90,1,100,6', '0,0,0,0,1,0,90,1,999999,6'):
            with self.assertRaises(HTTPError) as error:
                urlopen(root+f'/api/lod-index-family-plan/1/{A}?view='+invalid)
            self.assertEqual(422, error.exception.code)
            error.exception.close()


if __name__ == '__main__':
    unittest.main()
