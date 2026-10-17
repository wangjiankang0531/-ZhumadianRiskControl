"""Candidate cache must bind source bytes, recipe and complete payloads before reuse."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import verify_tight_native_atlas as candidate


class CandidateCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='xnby_tight_cache_test_')
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.root_patch = patch.object(candidate, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.root_patch.stop)
        self.candidate = self.root / 'work/tight_atlas_candidate_test'
        self.cache = candidate.candidate_cache(self.candidate)
        self.source = self.root / 'assets/驻马店园区/tile_140/Tile_140_L16_0.osgb'
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'original source fixture')
        node = {'name': self.source.name, 'children': [], 'level': 16,
                'bytes': self.source.stat().st_size, 'sha256': candidate.sha(self.source)}
        self.catalog = self.root / 'data/catalog.json'
        self.catalog.parent.mkdir()
        self.catalog.write_text(json.dumps({'root': node['name'], 'nodes': [node],
            'source_directory': 'assets/驻马店园区/tile_140'}), encoding='utf-8')
        master = self.root / 'data/showcase/zhumadian_native_hierarchy.json'
        master.parent.mkdir()
        master.write_text(json.dumps({'root_records': [{'tile_id': 140,
            'catalog': 'data/catalog.json', 'sha256': candidate.sha(self.catalog)}]}), encoding='utf-8')
        exporter = self.root / 'work/osgb_exporter_build/Release/ht_osgb_exporter.exe'
        exporter.parent.mkdir(parents=True)
        exporter.write_bytes(b'fingerprinted fixture only, never executed')
        self.folder = self.cache / 'tile_140_depth_3'
        part = self.folder / 'part_000'
        part.mkdir(parents=True)
        files = []
        for name, data in [('geometry.gltf', b'fixture gltf'), ('geometry.bin', b'fixture geometry'), ('atlas.jpg', b'fixture pixels')]:
            path = part / name
            path.write_bytes(data)
            files.append({'name': name, 'bytes': len(data), 'sha256': candidate.sha(path)})
        self.marker = {'schema': 'hongtu.osgb_native_chunk_bundle.v1', 'tile_id': 140,
            'depth': 3, 'complete_frontier': True,
            'atlas_layout_policy': candidate.tight.POLICY,
            'stamp': candidate.verified_source_stamp(140, 3),
            'parts': [{'directory': 'part_000', 'atlas_layout_policy': candidate.tight.POLICY, 'files': files}]}
        self.write_marker(self.marker)

    def write_marker(self, marker):
        (self.folder / 'complete.json').write_text(json.dumps(marker), encoding='utf-8')

    def test_valid_current_source_reuses_without_starting_converter(self):
        with patch.object(candidate.chunks, 'convert', side_effect=AssertionError('Must reuse checked cache')):
            self.assertEqual(candidate.prepare(self.candidate, 140, 3), self.marker)

    def test_same_size_source_tamper_and_catalog_tamper_invalidate(self):
        self.source.write_bytes(b'X' * self.source.stat().st_size)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))
        self.source.write_bytes(b'original source fixture')
        self.catalog.write_text('{}', encoding='utf-8')
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_exporter_or_layout_recipe_change_invalidates(self):
        changed = copy.deepcopy(self.marker)
        changed['stamp']['tight_layout_sha256'] = '0' * 64
        self.write_marker(changed)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))
        self.write_marker(self.marker)
        path = self.root / 'work/osgb_exporter_build/Release/ht_osgb_exporter.exe'
        path.write_bytes(b'changed fixture')
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_payload_corruption_or_missing_page_invalidates(self):
        (self.folder / 'part_000/geometry.bin').write_bytes(b'altered geometry')
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))
        (self.folder / 'part_000/geometry.bin').write_bytes(b'fixture geometry')
        (self.folder / 'part_000/atlas.jpg').rename(self.folder / 'part_000/atlas.missing')
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_incomplete_or_truncated_marker_never_reuses(self):
        changed = copy.deepcopy(self.marker)
        changed['complete_frontier'] = False
        self.write_marker(changed)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))
        (self.folder / 'complete.json').write_text('{', encoding='utf-8')
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_complete_family_cache_binds_every_real_child(self):
        import shutil
        catalog = json.loads(self.catalog.read_text(encoding='utf-8'))
        leaf = catalog['nodes'][0]
        parent = 'Tile_140_L15_0u.osgb'
        catalog['root'] = parent
        catalog['nodes'].insert(0, {'name': parent, 'children': [leaf['name']]})
        self.catalog.write_text(json.dumps(catalog), encoding='utf-8')
        master = self.root / 'data/showcase/zhumadian_native_hierarchy.json'
        value = json.loads(master.read_text(encoding='utf-8'))
        value['root_records'][0]['sha256'] = candidate.sha(self.catalog)
        master.write_text(json.dumps(value), encoding='utf-8')
        folder = self.cache / f'family_tile_140_{candidate.families.family_key(parent)}'
        shutil.copytree(self.folder, folder)
        marker = copy.deepcopy(self.marker)
        marker.update(schema='xnby.osgb_native_family.v1', replacement_parent=parent,
                      complete_sibling_family=True,
                      stamp=candidate.verified_source_stamp(140, 3, parent))
        marker.pop('complete_frontier')
        (folder / 'complete.json').write_text(json.dumps(marker), encoding='utf-8')
        with patch.object(candidate.families, 'convert', side_effect=AssertionError('Must reuse complete family')):
            self.assertEqual(candidate.prepare(self.candidate, 140, parent=parent), marker)
        self.source.write_bytes(b'X' * self.source.stat().st_size)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, parent=parent))

    def test_unsafe_part_directory_is_rejected_before_any_payload_read(self):
        changed = copy.deepcopy(self.marker)
        changed['parts'][0]['directory'] = '../outside'
        self.write_marker(changed)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_duplicate_physical_page_is_rejected_even_with_valid_file_hashes(self):
        changed = copy.deepcopy(self.marker)
        changed['parts'].append(copy.deepcopy(changed['parts'][0]))
        self.write_marker(changed)
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))

    def test_marker_link_is_rejected_before_reading_external_payload(self):
        marker_path = self.folder / 'complete.json'
        outside = self.root / 'outside-complete.json'
        marker_path.rename(outside)
        try:
            marker_path.symlink_to(outside)
        except OSError as error:
            self.skipTest('Host cannot create a test file symlink: ' + str(error))
        self.assertIsNone(candidate.cached_candidate(self.candidate, 140, 3))
        self.assertFalse(candidate.present(self.candidate, 140, 3, self.marker))
        self.assertEqual(json.loads(outside.read_text('utf-8')), self.marker)
        marker_path.unlink()

    def test_rebuild_uses_explicit_recipe_and_checks_persisted_marker(self):
        (self.folder / 'complete.json').write_text('{', encoding='utf-8')
        def publish(tile, depth, *, atlas_layout, cache_root):
            self.assertEqual((tile, depth, atlas_layout, cache_root),
                             (140, 3, candidate.tight.POLICY, self.cache))
            pending = self.folder / 'complete.pending.json'
            pending.write_text(json.dumps(self.marker), encoding='utf-8')
            pending.replace(self.folder / 'complete.json')
            return self.marker
        with patch.object(candidate.chunks, 'convert', side_effect=publish):
            marker = candidate.prepare(self.candidate, 140, 3)
        self.assertEqual(json.loads((self.folder / 'complete.json').read_text()), marker)
        self.assertFalse((self.folder / 'complete.pending.json').exists())
        self.assertEqual(candidate.cached_candidate(self.candidate, 140, 3), marker)

    def test_converter_result_without_complete_disk_marker_is_rejected(self):
        (self.folder / 'complete.json').write_text('{', encoding='utf-8')
        with patch.object(candidate.chunks, 'convert', return_value=self.marker):
            with self.assertRaises(RuntimeError):
                candidate.prepare(self.candidate, 140, 3)



if __name__ == '__main__':
    unittest.main()
