"""Real HTTP source selection, provenance, lease ownership and corruption tests."""
import hashlib
import json
from pathlib import Path
import shutil
import unittest

from test_preview_prepared_lod import PreparedPreviewTests as BasePreviewTests
from preview_prepared_sources import PreparedSources


class FallbackPreviewTests(BasePreviewTests):
    def prepare_additional_resources(self):
        self.backup = self.root/'explicit-backup'
        shutil.copytree(self.resources,self.backup)
        self.backup_folder = self.backup/'work/zhumadian_native_chunk_cache/tile_118_depth_3'
        self.write(self.backup_folder/'part_000/geometry.bin',b'backup geometry')
        marker=json.loads((self.backup_folder/'complete.json').read_bytes())
        for row in marker['parts'][0]['files']:
            if row['name']=='geometry.bin':row.update(bytes=15,sha256=hashlib.sha256(b'backup geometry').hexdigest())
        self.write(self.backup_folder/'complete.json',json.dumps(marker).encode())
        return [self.backup]

    def test_fallback_plan_and_payload_are_bound_to_the_same_source(self):
        (self.folder/'complete.json').unlink()
        before={p.relative_to(self.backup).as_posix():(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.backup.rglob('*') if p.is_file()}
        status,body,_=self.request('/api/lod-plan/118/3');self.assertEqual(status,200)
        plan=json.loads(body);marker,headers=self.admit()
        self.assertEqual(headers['X-XNBY-Source-Marker-SHA256'],plan['markerSHA256'])
        path='/native/tile_118_depth_3/part_000/geometry.bin?lease='+marker['cache_lease']
        self.assertEqual(self.request(path)[:2],(200,b'backup geometry'))
        # A primary appearing afterwards cannot redirect an admitted lease.
        self.write(self.folder/'complete.json',json.dumps(self.marker).encode())
        self.assertEqual(self.request(path)[:2],(200,b'backup geometry'))
        primary,_=self.admit()
        self.assertEqual(self.request('/native/tile_118_depth_3/part_000/geometry.bin?lease='+primary['cache_lease'])[:2],(200,b'geometry'))
        self.assertEqual({p.relative_to(self.backup).as_posix():(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.backup.rglob('*') if p.is_file()},before)

    def test_present_corrupt_primary_is_not_bypassed(self):
        self.write(self.folder/'part_000/geometry.bin',b'bad data')
        self.assertEqual(self.request('/api/lod/118/3')[0],422)
        self.assertEqual(json.loads(self.request('/api/health')[1])['loaded'],0)

    def test_bundle_catalog_identity_must_match_the_fixed_scene(self):
        marker=json.loads((self.folder/'complete.json').read_bytes())
        marker['stamp']['catalog_sha256']='b'*64
        self.write(self.folder/'complete.json',json.dumps(marker).encode())
        self.assertEqual(self.request('/api/lod-plan/118/3')[0],422)
        self.assertEqual(self.request('/api/lod/118/3')[0],422)

    def test_fallback_producer_mismatch_does_not_admit(self):
        (self.folder/'complete.json').unlink()
        marker=json.loads((self.backup_folder/'complete.json').read_bytes())
        marker['stamp']['converter_sha256']='0'*64
        self.write(self.backup_folder/'complete.json',json.dumps(marker).encode())
        self.assertEqual(self.request('/api/lod-plan/118/3')[0],422)
        self.assertEqual(self.request('/api/lod/118/3')[0],422)

    def test_different_scene_duplicate_root_and_unbounded_sources_are_rejected(self):
        with self.assertRaises(ValueError):PreparedSources(self.resources,[self.resources])
        with self.assertRaises(ValueError):PreparedSources(self.resources,[self.backup]*4)
        self.write(self.backup/'data/showcase/zhumadian_native_hierarchy.json',json.dumps({'root_records':[{'tile_id':118,'sha256':'c'*64}]}).encode())
        with self.assertRaisesRegex(ValueError,'different scenes'):PreparedSources(self.resources,[self.backup])

    def test_released_fallback_lease_cannot_read_any_source(self):
        (self.folder/'complete.json').unlink();marker,_=self.admit();token=marker['cache_lease']
        self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST')[0],204)
        self.assertEqual(self.request('/native/tile_118_depth_3/part_000/geometry.bin?lease='+token)[0],409)


if __name__=='__main__':unittest.main()
