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


    def test_plan_reads_only_marker_and_never_admits_or_leases_payload(self):
        from tools import readonly_landscape_store as readonly
        original=readonly.read_bytes;reads=[]
        def metadata_only(path,maximum):
            self.assertEqual(path.name,'complete.json')
            reads.append(path.name);return original(path,maximum)
        with patch.object(readonly,'read_bytes',side_effect=metadata_only),patch.object(web.POOL,'submit',side_effect=AssertionError('No producer')):
            status,body,headers=self.request('/api/lod-plan/117/3')
        value=json.loads(body);self.assertEqual(status,200);self.assertEqual(reads,['complete.json'])
        self.assertEqual(value['schema'],'xnby.source_bundle_plan.v1');self.assertFalse(value['availabilityVerified']);self.assertEqual(value['verification'],'metadata_only')
        self.assertNotIn('cache_lease',value);self.assertNotIn('cache_lease',value['marker']);self.assertFalse(self.registry.entries);self.assertFalse(self.server.RequestHandlerClass.read_only_store.entries)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(self.request('/native/tile_117_depth_3/part_000/atlas.jpg')[0],422)

    def test_verified_load_binds_exact_plan_marker_sha(self):
        status,body,_=self.request('/api/lod-plan/117/3');self.assertEqual(status,200);plan=json.loads(body)
        status,body,headers=self.request('/api/lod/117/3');self.assertEqual(status,200)
        self.assertEqual(headers['X-XNBY-Source-Marker-SHA256'],plan['markerSHA256']);self.assertEqual(plan['markerSHA256'],hashlib.sha256((self.folder/'complete.json').read_bytes()).hexdigest())
        token=json.loads(body)['cache_lease'];self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST')[0],204);self.assertFalse(self.registry.entries)

    def test_metadata_availability_is_not_a_substitute_for_verified_load(self):
        from tools import readonly_landscape_store as readonly
        original=readonly.read_bytes
        def corrupt(path,maximum):
            raw=original(path,maximum)
            return b'x'*len(raw) if path.name=='atlas.jpg' else raw
        with patch.object(readonly,'read_bytes',side_effect=corrupt):
            self.assertEqual(self.request('/api/lod-plan/117/3')[0],200)
            self.assertEqual(self.request('/api/lod/117/3')[0],422)
        self.assertFalse(self.registry.entries)

    def test_plan_capability_is_readonly_and_cannot_reach_writable_producers(self):
        health=json.loads(self.request('/api/health')[1]);self.assertEqual(health['descriptorPlanSchema'],'xnby.source_bundle_plan.v1')
        handler=self.server.RequestHandlerClass;handler.read_only_lod=False
        try:
            with patch.object(web.POOL,'submit',side_effect=AssertionError('No producer')):
                self.assertEqual(self.request('/api/lod-plan/117/3')[0],404)
                self.assertEqual(self.request('/api/lod-family-plan/117/Tile_117_L19_0uuuu.osgb')[0],404)
            self.assertNotIn('descriptorPlanSchema',json.loads(self.request('/api/health')[1]))
        finally:handler.read_only_lod=True

    def test_family_plan_route_passes_only_validated_source_identity(self):
        store=self.server.RequestHandlerClass.read_only_store
        with patch.object(store,'plan',return_value={'schema':'test-route'}) as plan:
            self.assertEqual(self.request('/api/lod-family-plan/117/Tile_117_L19_0uuuu.osgb')[0],200)
            plan.assert_called_once_with(117,depth=None,parent='Tile_117_L19_0uuuu.osgb')
        for route in ['/api/lod-plan/0/3','/api/lod-plan/117/99','/api/lod-plan/117/3?skip=1','/api/lod-family-plan/117/Tile_118_L19_0uuuu.osgb','/api/lod-family-plan/117/../../private']:
            self.assertEqual(self.request(route)[0],400)

    def test_post_grant_json_failure_releases_the_new_lease(self):
        store=self.server.RequestHandlerClass.read_only_store;original=store.describe_with_identity
        def invalid(*args,**kwargs):
            marker,digest=original(*args,**kwargs);return {**marker,'invalid_number':float('nan')},digest
        with patch.object(store,'describe_with_identity',side_effect=invalid):self.assertEqual(self.request('/api/lod/117/3')[0],422)
        self.assertFalse(self.registry.entries)


if __name__=='__main__':unittest.main()
