"""Independent asset verification regressions using in-memory files only."""
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import verify_prepared_native_assets as audit


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


class PreparedAssetVerifierTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('D:/virtual_only/信能本源').absolute()
        self.package = self.root/'Application/work/frozen'
        self.store = self.root/'Assets/Runtime/PreparedScenes/v1'
        self.data, self.links = {}, set()
        self.catalog = dict(root='root', max_descendant_depth=2, nodes=[
            dict(name='root', children=['n1']), dict(name='n1', children=['n2']), dict(name='n2', children=[])])
        catalog_path = 'data/catalog1.json'
        self.data[self.package/catalog_path] = encoded(self.catalog)
        self.hierarchy = dict(root_records=[dict(tile_id=1, catalog=catalog_path, sha256=sha(encoded(self.catalog)))])
        self.data[self.package/'data/showcase/zhumadian_native_hierarchy.json'] = encoded(self.hierarchy)
        self.data[self.package/'tools/producer.py'] = b'producer code'
        self.data[self.package/'work/osgb_exporter_build/Release/ht_osgb_exporter.exe'] = b'exporter identity only; never executed'
        family = 'family_tile_1_'+sha(b'n1')[:16]
        self.plan = dict(schema='xnby.native.preparation_plan.v1', base_depth=1, max_depth=2, tiles=[1],
                         hierarchy_sha256=sha(encoded(self.hierarchy)),
                         catalogs=[dict(tile=1, path=catalog_path, sha256=sha(encoded(self.catalog)))],
                         jobs=[dict(tile=1, depth=1, directory='tile_1_depth_1'),
                               dict(tile=1, depth=2, parent='n1', directory=family)],
                         producer_sha256={'producer.py':sha(b'producer code')},
                         exporter_sha256=sha(b'exporter identity only; never executed'))
        self.markers = {}
        for job in self.plan['jobs']:
            name = job['directory']
            folder = self.store/name/'part_000'
            self.data[folder/'geometry.bin'] = b'virtual mesh'
            self.data[folder/'atlas.jpg'] = b'virtual texture; no real JPEG is created'
            self.data[folder/'geometry.gltf'] = encoded(dict(buffers=[dict(uri='geometry.bin', byteLength=len(b'virtual mesh'))], images=[dict(uri='atlas.jpg')]))
            self.markers[name] = dict(tile_id=1, depth=job['depth'], replacement_parent='n1',
                                      complete_frontier=True, complete_sibling_family=True,
                                      atlas_layout_policy='test_recipe', gpu_payload_bytes=100,
                                      parts=[dict(directory='part_000', gpu_payload_bytes=100, files=[])])
        self.refresh()
        def open_file(path, mode='r', *args, **kwargs):
            if mode not in ('r', 'rb'):
                raise AssertionError('Verifier attempted to modify virtual files: '+str(path))
            value = self.data[path]
            return io.BytesIO(value) if mode == 'rb' else io.StringIO(value.decode('utf-8'))
        contexts = [patch.object(Path, 'open', open_file),
                    patch.object(Path, 'stat', lambda p, **kw: SimpleNamespace(st_size=len(self.data[p]), st_mtime_ns=7)),
                    patch.object(Path, 'is_file', lambda p: p in self.data),
                    patch.object(Path, 'is_dir', lambda p: any(p in file.parents for file in self.data)),
                    patch.object(Path, 'resolve', lambda p, **kw: p.absolute()),
                    patch.object(audit, 'linked', lambda p: p in self.links)]
        for context in contexts:
            context.start()
            self.addCleanup(context.stop)

    def refresh(self):
        rows = []
        for name, marker in self.markers.items():
            folder = self.store/name/'part_000'
            marker['parts'][0]['files'] = [dict(name=n, bytes=len(self.data[folder/n]), sha256=sha(self.data[folder/n]))
                                            for n in ('geometry.gltf', 'geometry.bin', 'atlas.jpg')]
            payload = encoded(marker)
            self.data[self.store/name/'complete.json'] = payload
            rows.append(dict(directory=name, marker_sha256=sha(payload), parts=1, gpu_payload_bytes=100))
        binding = dict(plan=self.plan, atlas_layout_policy='test_recipe')
        plan_hash = sha(json.dumps(binding, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
        self.data[self.store/'preparation.plan.json'] = encoded(binding)
        self.manifest = dict(schema='xnby.native.asset_manifest.v1', plan_sha256=plan_hash,
                             complete=True, codecs=['rgba8'], bundles=rows)
        self.descriptor = dict(schema='xnby.native.asset_package.v1', state='sealed',
                               storage_limit_bytes=8*1024**3, plan_sha256=plan_hash, manifest_sha256='')
        self.refresh_manifest()

    def refresh_manifest(self):
        self.data[self.store/'.asset_manifest.json'] = encoded(self.manifest)
        self.descriptor['manifest_sha256'] = sha(encoded(self.manifest))
        self.data[self.store/'.asset_package.json'] = encoded(self.descriptor)

    def reader(self):
        return audit.PreparedAssets(self.package, self.store)

    def test_complete_generation_verified_without_any_virtual_write(self):
        before = copy.deepcopy(self.data)
        result = self.reader().audit()
        self.assertTrue(result['passed'])
        self.assertEqual((result['bundles'],result['physicalParts']), (2,2))
        self.assertEqual(self.data, before)

    def test_building_generation_refused(self):
        self.descriptor['state'] = 'building'
        self.refresh_manifest()
        with self.assertRaises(audit.AssetVerificationError): self.reader()

    def test_duplicate_or_missing_manifest_bundle_refused_after_valid_rehash(self):
        for duplicate in (True, False):
            self.refresh()
            if duplicate: self.manifest['bundles'][1] = self.manifest['bundles'][0]
            else: self.manifest['bundles'].pop()
            self.refresh_manifest()
            with self.assertRaises(audit.AssetVerificationError): self.reader()

    def test_plan_cannot_omit_source_jobs_even_with_matching_control_hashes(self):
        self.plan['jobs'].pop()
        self.refresh()
        with self.assertRaises(audit.AssetVerificationError): self.reader()

    def test_changed_frozen_producer_refused(self):
        self.data[self.package/'tools/producer.py'] = b'changed'
        with self.assertRaises(audit.AssetVerificationError): self.reader()

    def test_payload_corruption_refused(self):
        reader = self.reader()
        self.data[self.store/'tile_1_depth_1/part_000/atlas.jpg'] = b'changed'
        with self.assertRaises(audit.AssetVerificationError): reader.bundle('tile_1_depth_1')

    def test_gltf_external_reference_refused_even_with_matching_hashes(self):
        path = self.store/'tile_1_depth_1/part_000/geometry.gltf'
        self.data[path] = encoded(dict(buffers=[dict(uri='../geometry.bin', byteLength=12)], images=[dict(uri='atlas.jpg')]))
        self.refresh()
        with self.assertRaises(audit.AssetVerificationError): self.reader().bundle('tile_1_depth_1')

    def test_asset_namespace_and_payload_links_refused(self):
        for path in (self.store.parent, self.store/'tile_1_depth_1/part_000/atlas.jpg'):
            self.links = {path}
            with self.assertRaises(audit.AssetVerificationError): self.reader().audit()

    def test_undeclared_bundle_refused(self):
        with self.assertRaises(audit.AssetVerificationError): self.reader().bundle('tile_2_depth_1')

    def test_runtime_record_must_identify_same_readonly_generation(self):
        reader = self.reader()
        for lod in ({}, dict(cache_access='read_only'), dict(cache_access='prepare', prepared_assets=reader.identity()),
                    dict(cache_access='read_only', prepared_assets={**reader.identity(), 'manifest_sha256':'0'*64})):
            with self.assertRaises(audit.AssetVerificationError): reader.require_runtime_identity(lod)
        reader.require_runtime_identity(dict(cache_access='read_only', prepared_assets=reader.identity()))

    def test_duplicate_json_keys_refused(self):
        path = self.store/'.asset_package.json'
        self.data[path] = b'{"state":"building","state":"sealed"}'
        with self.assertRaises(audit.AssetVerificationError): self.reader()

    def test_path_escape_refused(self):
        with self.assertRaises(audit.AssetVerificationError): audit.owned(self.store, '../other')
        with self.assertRaises(audit.AssetVerificationError): audit.PreparedAssets(self.package, self.root/'other/v1')


if __name__ == '__main__':
    unittest.main()
