from pathlib import Path
import json
import tempfile
import unittest
import native_atlas_recipe as recipe


class AtlasRecipeTests(unittest.TestCase):
    def test_default_layout_is_legacy_and_explicit_tight_keeps_source_rectangles(self):
        sizes={'source':(512,512)}
        old=recipe.layouts(sizes);new=recipe.layouts(sizes,recipe.TIGHT)
        self.assertEqual(recipe.policy(),recipe.LEGACY)
        self.assertEqual(old[0][0],new[0][0])
        self.assertEqual((old[0][1],new[0][1]),(1024,520))
    def test_npot_mips_use_floor_each_level_and_include_one_pixel(self):
        self.assertEqual(recipe.mip_bytes(520),sum(n*n*4 for n in [520,260,130,65,32,16,8,4,2,1]))
        for n in (1024,2048):
            self.assertEqual(recipe.mip_bytes(n),sum((n//2**i)**2*4 for i in range(12)))
        for n in (0,-1,True,2049):
            with self.subTest(n=n),self.assertRaises(ValueError):recipe.mip_bytes(n)
    def test_unknown_policy_rejected(self):
        for value in ('', 'tight_unknown',False):
            with self.subTest(value=value),self.assertRaises(ValueError):recipe.policy(value)
    def test_default_and_explicit_namespaces_cannot_escape_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);legacy=root/'legacy';(root/'work').mkdir()
            self.assertEqual(recipe.cache_directory(root,legacy),legacy)
            self.assertEqual(recipe.cache_directory(root,legacy,recipe.TIGHT),root/'work/native_recipe_cache'/recipe.TIGHT)
            for override in (root/'work',root/'outside',root/'work/../../outside'):
                with self.subTest(override=override),self.assertRaises(ValueError):recipe.cache_directory(root,legacy,recipe.TIGHT,override)
    def test_cache_format_collision_preserves_existing_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)/'cache';recipe.bind_cache(cache,recipe.LEGACY)
            before=(cache/'.atlas_recipe.json').read_bytes()
            with self.assertRaises(ValueError):recipe.bind_cache(cache,recipe.TIGHT)
            self.assertEqual((cache/'.atlas_recipe.json').read_bytes(),before)
            recipe.bind_cache(cache,recipe.LEGACY)
            self.assertFalse((cache/'.atlas_recipe.pending.json').exists())
    def test_unbound_legacy_bundle_cannot_be_reinterpreted_as_tight(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);folder=cache/'tile_140_depth_3';folder.mkdir()
            marker=folder/'complete.json';marker.write_text('{}')
            with self.assertRaises(ValueError):recipe.bind_cache(cache,recipe.TIGHT)
            self.assertEqual(marker.read_text(),'{}')
            self.assertFalse((cache/'.atlas_recipe.json').exists())
    def test_unbound_tight_bundle_can_be_bound_without_changing_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);folder=cache/'tile_140_depth_3';folder.mkdir()
            marker=folder/'complete.json';marker.write_text(json.dumps({'atlas_layout_policy':recipe.TIGHT}))
            before=marker.read_bytes();recipe.bind_cache(cache,recipe.TIGHT)
            self.assertEqual(marker.read_bytes(),before)
    def test_invalid_or_linked_recipe_marker_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)/'cache';cache.mkdir();marker=cache/'.atlas_recipe.json';marker.write_text('{')
            with self.assertRaises(ValueError):recipe.bind_cache(cache,recipe.TIGHT)
            outside=Path(tmp)/'outside.json';marker.rename(outside)
            try:marker.symlink_to(outside)
            except OSError as error:self.skipTest(str(error))
            with self.assertRaises(ValueError):recipe.bind_cache(cache,recipe.TIGHT)
            self.assertEqual(outside.read_text(),'{');marker.unlink()


    def test_published_payload_rejects_corruption_missing_and_duplicate_parts(self):
        import copy, hashlib
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'complete.json').write_text('{}');part=folder/'part_000';part.mkdir()
            files=[]
            for name in ['geometry.gltf','geometry.bin','atlas.jpg']:
                data=name.encode();(part/name).write_bytes(data)
                files.append({'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            marker={'parts':[{'directory':'part_000','files':files}]}
            self.assertTrue(recipe.payload_present(folder,marker))
            duplicate=copy.deepcopy(marker);duplicate['parts']*=2
            self.assertFalse(recipe.payload_present(folder,duplicate))
            (part/'geometry.bin').write_bytes(b'X'*len(b'geometry.bin'))
            self.assertFalse(recipe.payload_present(folder,marker))
            (part/'geometry.bin').unlink()
            self.assertFalse(recipe.payload_present(folder,marker))
    def test_pending_metadata_link_cannot_overwrite_external_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'bundle';folder.mkdir();outside=Path(tmp)/'external';outside.write_bytes(b'preserve')
            try:(folder/'complete.pending.json').symlink_to(outside)
            except OSError as error:self.skipTest(str(error))
            with self.assertRaises(ValueError):recipe.writable_bundle(folder)
            self.assertEqual(outside.read_bytes(),b'preserve')
            (folder/'complete.pending.json').unlink()
    def test_build_size_is_restored_on_export_failure(self):
        from unittest.mock import patch
        import convert_zhumadian_native_chunks as chunks
        before=chunks.native.full.SIZE
        def fail(*args,**kwargs):
            chunks.native.full.SIZE=520
            raise RuntimeError('synthetic export failure')
        with patch.object(chunks,'_build_parts',side_effect=fail):
            with self.assertRaises(RuntimeError):chunks.build_parts(None,None,None,None,None,None)
        self.assertEqual(chunks.native.full.SIZE,before)


    def test_release_config_absent_keeps_legacy_and_present_uses_reader_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);legacy=root/'work/zhumadian_native_chunk_cache'
            self.assertEqual(recipe.resolve_cache(root,legacy),(recipe.LEGACY,legacy))
            path=root/'data/showcase/zhumadian_native_recipe.json';path.parent.mkdir(parents=True)
            declaration={'schema':'xnby.native.atlas.release.v1','atlas_layout_policy':recipe.TIGHT,'cache_relative_path':'work/zhumadian_native_chunk_cache'}
            path.write_text(json.dumps(declaration))
            self.assertEqual(recipe.resolve_cache(root,legacy),(recipe.TIGHT,legacy))
            other=root/'work/explicit_legacy'
            self.assertEqual(recipe.resolve_cache(root,legacy,recipe.LEGACY,other),(recipe.LEGACY,other))
    def test_release_config_rejects_unknown_fields_layout_and_cache_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);legacy=root/'work/zhumadian_native_chunk_cache';path=root/'data/showcase/zhumadian_native_recipe.json';path.parent.mkdir(parents=True)
            valid={'schema':'xnby.native.atlas.release.v1','atlas_layout_policy':recipe.TIGHT,'cache_relative_path':'work/zhumadian_native_chunk_cache'}
            for patch in [{'schema':'future'}, {'atlas_layout_policy':'guess'}, {'cache_relative_path':'../../outside'}, {'extra':True}]:
                path.write_text(json.dumps(dict(valid,**patch)))
                with self.subTest(patch=patch),self.assertRaises(ValueError):recipe.resolve_cache(root,legacy)
                self.assertFalse(legacy.exists())
            path.write_text('[]')
            with self.assertRaises(ValueError):recipe.resolve_cache(root,legacy)
    def test_dangling_release_declaration_link_does_not_fall_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'data/showcase/zhumadian_native_recipe.json';path.parent.mkdir(parents=True)
            try:path.symlink_to(root/'missing')
            except OSError as error:self.skipTest(str(error))
            with self.assertRaises(ValueError):recipe.resolve_cache(root,root/'work/cache')
            path.unlink()


if __name__=='__main__':unittest.main()