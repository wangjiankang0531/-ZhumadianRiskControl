"""Real loopback HTTP/lease tests; tiny data, no native process or original GIS."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request


class PreparedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='prepared-preview-')
        self.root = Path(self.tmp.name)
        self.resources = self.root/'resources'
        self.bundle = self.root/'bundle'
        self.state = self.root/'state.json'
        self.project = self.root/'layers.json'
        self.project.write_bytes(b'{"userData":"unchanged"}')
        for rel in ['web/index.html','web/viewer.js','web/source-gain-worker.js']:
            self.write(self.bundle/rel, b'fixture')
        for rel in ['data/showcase/zhumadian_native_hierarchy.json','assets/landscape/icons.png','assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin','assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf','assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg','assets/showcase/runtime/zhumadian/full/base_lod_quality.json']:
            self.write(self.resources/rel, b'fixture')
        stamp = {'catalog_sha256':'a'*64}
        for key,name in [('converter_sha256','convert_zhumadian_native_chunks.py'),('texture_helper_sha256','native_texture_parts.py'),('frontier_helper_sha256','native_source_frontier.py'),('atlas_recipe_sha256','native_atlas_recipe.py')]:
            data = ('fixture producer '+name).encode()
            self.write(self.resources/'tools'/name, data)
            stamp[key] = hashlib.sha256(data).hexdigest()
        self.cache = self.resources/'work/zhumadian_native_chunk_cache'
        self.folder = self.cache/'tile_118_depth_3'
        files = []
        for name,data in [('geometry.gltf',b'{"asset":{"version":"2.0"}}'),('geometry.bin',b'geometry'),('atlas.jpg',b'jpeg fixture')]:
            self.write(self.folder/'part_000'/name, data)
            files.append(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        self.marker = dict(schema='hongtu.osgb_native_chunk_bundle.v1',tile_id=118,depth=3,texture_policy='original_pixels_v1',complete_frontier=True,stamp=stamp,gpu_payload_bytes=1024,parts=[dict(directory='part_000',files=files,gpu_payload_bytes=1024)])
        self.write(self.folder/'complete.json', json.dumps(self.marker).encode())
        for name in ('tile_118.lock','tile_118_depth_3.lock'):
            self.write(self.cache/'.locks'/name, b'0')
        self.write(self.resources/'data/showcase/zhumadian_native_hierarchy.json',json.dumps({'root_records':[{'tile_id':118,'sha256':'a'*64}]}).encode())
        self.additional = self.prepare_additional_resources()
        self.before = self.snapshot()
        self.script = Path(__file__).with_name('serve_native_preview.py')
        self.args = [sys.executable,'-I','-B',str(self.script),'--bundle',str(self.bundle),'--resources',str(self.resources),'--layers',str(self.project),'--state',str(self.state),'--no-browser','--prepared-lod']
        for root in self.additional:self.args.extend(['--prepared-resource',str(root)])
        self.flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        self.proc = subprocess.Popen(self.args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=self.flags)
        deadline = time.monotonic()+6
        while not self.state.exists():
            if self.proc.poll() is not None:
                self.fail(self.proc.stderr.read().decode(errors='replace'))
            if time.monotonic() > deadline:self.fail('preview readiness timeout')
            time.sleep(.02)
        self.saved = json.loads(self.state.read_bytes())
        self.url = 'http://127.0.0.1:'+str(self.saved['port'])
        self.http = build_opener(ProxyHandler({}))

    def prepare_additional_resources(self):
        return []

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

    def snapshot(self):
        return {p.relative_to(self.resources).as_posix():(p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.resources.rglob('*') if p.is_file()}

    def request(self, path, method='GET', headers=None, data=None):
        req = Request(self.url+path,method=method,headers=headers or {},data=b'' if method=='POST' and data is None else data)
        try:response=self.http.open(req,timeout=5)
        except HTTPError as error:response=error
        with response:return response.status,response.read(),dict(response.headers)

    def admit(self):
        status,body,headers=self.request('/api/lod/118/3')
        self.assertEqual(status,200)
        return json.loads(body),headers

    def tearDown(self):
        try:
            if self.proc.poll() is None:
                self.request('/__preview__/stop','POST',{'X-Preview-Key':self.saved['controlKey']})
                self.proc.wait(timeout=5)
            self.assertEqual(self.proc.returncode,0)
            self.assertEqual(self.project.read_bytes(),b'{"userData":"unchanged"}')
        finally:
            self.proc.stderr.close()
            self.tmp.cleanup()

    def test_health_truthfully_advertises_readonly_plans_without_native_reader(self):
        status,body,_=self.request('/api/health');health=json.loads(body)
        self.assertEqual(status,200);self.assertFalse(health['conversionEnabled']);self.assertFalse(health['nativeReaderEnabled'])
        self.assertEqual(health['application'],'xnby.landscape.web.v1');self.assertEqual(health['lodAccess'],'read_only')
        self.assertTrue(self.saved['preparedLOD'])

    def test_plan_verified_payload_release_and_no_disk_changes(self):
        status,body,_=self.request('/api/lod-plan/118/3');plan=json.loads(body)
        self.assertEqual(status,200);self.assertNotIn('cache_lease',plan['marker']);self.assertFalse(plan['availabilityVerified'])
        marker,headers=self.admit();self.assertEqual(headers['X-XNBY-Source-Marker-SHA256'],plan['markerSHA256'])
        path='/native/tile_118_depth_3/part_000/geometry.bin?lease='+marker['cache_lease']
        self.assertEqual(self.request(path)[:2],(200,b'geometry'))
        self.assertEqual(self.request(path,'HEAD')[:2],(200,b''))
        self.assertEqual(self.request('/api/lod-lease/'+marker['cache_lease']+'/release','POST')[0],204)
        self.assertEqual(self.request(path)[0],409)
        self.assertEqual(self.snapshot(),self.before)

    def test_fixed_metadata_wait_hint_avoids_compatibility_retry_without_admitting(self):
        plain=self.request('/api/lod-plan/118/3')
        hinted=self.request('/api/lod-plan/118/3?wait_ms=200')
        self.assertEqual(hinted[:2],plain[:2])
        family='/api/lod-family-plan/118/Tile_118_L19_0uuuu.osgb'
        self.assertEqual(self.request(family+'?wait_ms=200')[0],409)
        self.assertEqual(json.loads(self.request('/api/health')[1])['loaded'],0)
        self.assertEqual(self.snapshot(),self.before)
        for path in ['/api/lod-plan/118/3?wait_ms=201','/api/lod-plan/118/3?wait_ms=200&convert=1','/api/lod-plan/118/3?wait_ms=200&wait_ms=200','/api/lod/118/3?wait_ms=200']:
            with self.subTest(path=path):self.assertEqual(self.request(path)[0],422)
        self.assertEqual(json.loads(self.request('/api/health')[1])['loaded'],0)

    def test_missing_data_never_creates_output_or_retries_conversion(self):
        for path in ['/api/lod/119/3','/api/lod-plan/119/3','/api/lod-family/118/Tile_118_L19_0uuuu.osgb']:
            status,body,_=self.request(path);self.assertEqual(status,409)
            self.assertFalse(json.loads(body)['conversionEnabled'])
        self.assertEqual(self.snapshot(),self.before)

    def test_payload_mutation_and_marker_mutation_are_rejected(self):
        marker,_=self.admit()
        self.write(self.folder/'part_000/geometry.bin',b'changed!')
        path='/native/tile_118_depth_3/part_000/geometry.bin?lease='+marker['cache_lease']
        self.assertEqual(self.request(path)[0],422)
        self.assertEqual(self.request('/api/lod/118/3')[0],422)

    def test_plan_does_not_admit_and_unknown_lease_cannot_read(self):
        self.assertEqual(self.request('/api/lod-plan/118/3')[0],200)
        self.assertEqual(self.request('/native/tile_118_depth_3/part_000/geometry.bin?lease='+'0'*32)[0],409)
        self.assertEqual(self.request('/native/tile_118_depth_3/part_000/geometry.bin')[0],422)

    def test_foreign_origin_release_does_not_invalidate_live_payload(self):
        marker,_=self.admit();token=marker['cache_lease']
        self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST',{'Origin':'https://unrelated.invalid'})[0],403)
        self.assertEqual(self.request('/native/tile_118_depth_3/part_000/geometry.bin?lease='+token)[0],200)

    def test_invalid_paths_foreign_hosts_and_nonempty_posts_are_rejected(self):
        for path in ['/api/lod/9999/3','/api/lod/118/0','/api/lod/118/3?convert=1','/native/../secret.txt','/api/lod-family/118/Tile_119_L19_0uuuu.osgb']:
            with self.subTest(path=path):self.assertIn(self.request(path)[0],(404,422))
        self.assertEqual(self.request('/api/health',headers={'Host':'unrelated.invalid'})[0],403)
        self.assertEqual(self.request('/api/lod-lease/'+'0'*32+'/release','POST',data=b'x')[0],400)

    def test_missing_existing_lock_does_not_create_one(self):
        path=self.cache/'.locks/tile_118_depth_3.lock';path.unlink()
        self.assertEqual(self.request('/api/lod/118/3')[0],409);self.assertFalse(path.exists())

    def test_duplicate_start_keeps_prepared_mode(self):
        before=self.state.read_bytes()
        completed=subprocess.run(self.args,capture_output=True,timeout=5,creationflags=self.flags)
        self.assertEqual(completed.returncode,0);self.assertEqual(self.state.read_bytes(),before)


if __name__=='__main__':unittest.main()
