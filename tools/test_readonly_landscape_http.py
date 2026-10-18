import hashlib
import http.client
import http.server
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from tools import landscape_web_server as web
from tools import native_cache_policy as policy
from tools.native_cache_leases import LeaseRegistry
from tools.readonly_landscape_store import ReadOnlyLandscapeStore


class ReadOnlyHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cache = self.root/'work/zhumadian_native_chunk_cache'
        self.folder = self.cache/'tile_117_depth_3'
        part = self.folder/'part_000'
        part.mkdir(parents=True)
        (self.cache/'.locks').mkdir()
        for name in ('tile_117.lock','tile_117_depth_3.lock'):
            (self.cache/'.locks'/name).write_bytes(b'')
        (self.root/'tools').mkdir()
        stamp = {}
        for key,name in [('converter_sha256','convert_zhumadian_native_chunks.py'),('texture_helper_sha256','native_texture_parts.py'),('frontier_helper_sha256','native_source_frontier.py'),('atlas_recipe_sha256','native_atlas_recipe.py')]:
            data=('frozen-source-'+name).encode()
            (self.root/'tools'/name).write_bytes(data)
            stamp[key] = hashlib.sha256(data).hexdigest()
        files = []
        for name,data in [('geometry.gltf',b'{"asset":{"version":"2.0"}}'),('geometry.bin',b'geometry'),('atlas.jpg',b'original-source-jpeg')]:
            (part/name).write_bytes(data)
            files.append(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        self.marker = dict(schema='hongtu.osgb_native_chunk_bundle.v1',tile_id=117,depth=3,complete_frontier=True,texture_policy='original_pixels_v1',stamp=stamp,gpu_payload_bytes=1568,parts=[dict(directory='part_000',gpu_payload_bytes=1568,files=files)])
        (self.folder/'complete.json').write_text(json.dumps(self.marker))
        self.registry = LeaseRegistry(ttl=.15,janitor=False,read_only=True)
        store = ReadOnlyLandscapeStore(self.root)
        class Handler(web.Handler):
            read_only_lod = True
            read_only_store = store
            def log_message(self,*args):pass
        Handler.root = self.root
        Handler.read_only_leases = self.registry
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.registry.close();self.temp.cleanup()

    def request(self,path,method='GET'):
        c = http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        c.request(method,path)
        r = c.getresponse();result=r.status,r.read(),dict(r.getheaders());c.close();return result

    def snapshot(self):
        return {p.relative_to(self.cache).as_posix():(p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.cache.rglob('*') if p.is_file()}

    def test_real_http_read_renew_release_and_expiry_do_not_write_or_maintain(self):
        before = self.snapshot()
        with patch.object(web.POOL,'submit') as submit,patch.object(policy,'maintain',side_effect=AssertionError('Read-only mode must not maintain')) as maintain:
            status,body,_ = self.request('/api/lod/117/3')
            self.assertEqual(status,200)
            token = json.loads(body)['cache_lease']
            path = '/native/tile_117_depth_3/part_000/atlas.jpg?lease='+token
            self.assertEqual(self.request(path)[1],b'original-source-jpeg')
            status,body,headers = self.request(path,'HEAD')
            self.assertEqual((status,body,headers['Content-Length']),(200,b'',str(len(b'original-source-jpeg'))))
            self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST')[0],204)
            self.assertEqual(self.request(path)[0],409)
            status,body,_ = self.request('/api/lod/117/3');self.assertEqual(status,200)
            time.sleep(.2);self.registry.expire()
            submit.assert_not_called();maintain.assert_not_called()
        self.assertEqual(self.snapshot(),before)

    def test_missing_bundle_or_existing_locks_never_schedules_or_creates(self):
        before = self.snapshot()
        with patch.object(web.POOL,'submit') as submit,patch.object(policy,'maintain') as maintain:
            self.assertEqual(self.request('/api/lod/118/3')[0],409)
            self.assertEqual(self.request('/api/lod-family/117/Tile_117_L19_0uuuu.osgb')[0],409)
            submit.assert_not_called();maintain.assert_not_called()
        self.assertEqual(self.snapshot(),before)
        (self.cache/'.locks/tile_117_depth_3.lock').unlink()
        before = self.snapshot()
        self.assertEqual(self.request('/api/lod/117/3')[0],409)
        self.assertEqual(self.snapshot(),before)

    def test_worker_static_entry_is_explicitly_served_without_opening_other_scripts(self):
        static=self.root/'apps/landscape_web/dist';static.mkdir(parents=True)
        (static/'source-gain-worker.js').write_text('self.onmessage = () => {};')
        self.assertEqual(self.request('/source-gain-worker.js')[0],200)
        self.assertEqual(self.request('/unexpected-worker.js')[0],404)

    def test_corrupt_payload_stale_producer_and_changed_marker_are_rejected(self):
        status,body,_ = self.request('/api/lod/117/3');self.assertEqual(status,200)
        token = json.loads(body)['cache_lease']
        photo = self.folder/'part_000/atlas.jpg'
        original = photo.read_bytes();photo.write_bytes(b'x'*len(original))
        self.assertEqual(self.request('/native/tile_117_depth_3/part_000/atlas.jpg?lease='+token)[0],422)
        self.assertEqual(self.request('/api/lod/117/3')[0],422)
        photo.write_bytes(original)
        self.marker['stamp']['converter_sha256']='0'*64
        (self.folder/'complete.json').write_text(json.dumps(self.marker))
        self.assertEqual(self.request('/api/lod/117/3')[0],422)
        self.assertEqual(self.request('/native/tile_117_depth_3/part_000/geometry.bin?lease='+token)[0],422)

    def test_unlisted_file_link_and_path_escape_are_not_served(self):
        for path in ('/native/tile_117_depth_3/part_000/private.json','/native/tile_117_depth_3/../complete.json','/api/lod-family/117/Tile_118_L19_0uuuu.osgb'):
            self.assertIn(self.request(path)[0],(400,404))
        with self.assertRaises(ValueError):self.server.RequestHandlerClass.read_only_store.payload('tile_117_depth_3','part_999','atlas.jpg')
        outside = self.root/'outside.jpg';outside.write_bytes(b'outside')
        photo = self.folder/'part_000/atlas.jpg';photo.unlink()
        try:photo.symlink_to(outside)
        except OSError:self.skipTest('This Windows token cannot create file symlinks')
        self.assertEqual(self.request('/api/lod/117/3')[0],422)

    def test_readonly_lock_cannot_create_a_file_or_request_exclusive_access(self):
        missing = self.cache/'.locks/not-created.lock'
        with self.assertRaises(FileNotFoundError):policy.FileLock(missing,read_only=True)
        self.assertFalse(missing.exists())
        with self.assertRaises(ValueError):policy.FileLock(missing,exclusive=True,read_only=True)


if __name__=='__main__':unittest.main()
