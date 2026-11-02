"""Source recipe integrity and checkout isolation; no renderer or business service starts."""
from pathlib import Path
import copy
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_native_manual_preview_source as source


class SourceRecipeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='native source recipe ')
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repository'
        self.repo.mkdir()
        self.git('init', '--quiet')
        self.git('config', 'core.autocrlf', 'false')
        (self.repo / 'native').mkdir()
        (self.repo / 'native/main.cpp').write_bytes(b'committed-source\r\n')
        self.git('add', 'native/main.cpp')
        self.git('-c', 'user.name=Source recipe fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'synthetic fixture')
        commit = self.git('rev-parse', 'HEAD').decode().strip()
        blob = self.git('rev-parse', 'HEAD:native/main.cpp').decode().strip()
        data = self.git('cat-file', 'blob', blob)
        self.recipe = {'schema': source.SCHEMA, 'sourceFiles': 1,
                       'commits': {'Application': commit, 'XNBYEngine': commit},
                       'files': [{'path': 'Application/native/main.cpp', 'origin': 'git', 'gitBlob': blob,
                                  'baseSHA256': source.digest(data), 'SHA256': source.digest(data)}]}
        self.repositories = {'Application': self.repo, 'XNBYEngine': self.repo}
        self.overlay = self.root / 'overlay'
        self.overlay.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True, timeout=10).stdout

    def prepare(self):
        return source.prepare_files(self.recipe, self.repositories, self.overlay)

    def test_git_bytes_ignore_modified_checkout_and_preserve_head_index(self):
        head = self.git('rev-parse', 'HEAD')
        index = (self.repo / '.git/index').read_bytes()
        (self.repo / 'native/main.cpp').write_bytes(b'unpublished-held-work')
        self.assertEqual(self.prepare()['Application/native/main.cpp'], b'committed-source\r\n')
        self.assertEqual((self.repo / 'native/main.cpp').read_bytes(), b'unpublished-held-work')
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual((self.repo / '.git/index').read_bytes(), index)

    def test_wrong_commit_or_missing_blob_is_rejected(self):
        self.recipe['commits']['Application'] = '0' * 40
        with self.assertRaises(ValueError):
            self.prepare()

    def test_wrong_blob_or_base_hash_is_rejected(self):
        for key, value in [('gitBlob', '0' * 40), ('baseSHA256', '0' * 64)]:
            with self.subTest(key=key):
                recipe = copy.deepcopy(self.recipe)
                recipe['files'][0][key] = value
                with self.assertRaises(ValueError):
                    source.prepare_files(recipe, self.repositories, self.overlay)

    def test_final_source_hash_is_checked(self):
        self.recipe['files'][0]['SHA256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Prepared source hash mismatch'):
            self.prepare()

    def test_path_traversal_absolute_backslash_ads_and_normalization_rejected(self):
        for value in ['../secret', '/Application/a', 'Application/../secret', 'Application//a',
                      'Application/./a', 'Application/a:stream', 'Application\\a', 'Other/a']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.relative_path(value)

    def test_duplicate_case_colliding_source_paths_rejected(self):
        duplicate = copy.deepcopy(self.recipe['files'][0])
        duplicate['path'] = 'Application/native/MAIN.cpp'
        self.recipe['files'].append(duplicate)
        self.recipe['sourceFiles'] = 2
        with self.assertRaisesRegex(ValueError, 'case-colliding'):
            self.prepare()

    def test_overlay_requires_exact_pin_and_does_not_modify_input(self):
        (self.overlay / 'native').mkdir()
        path = self.overlay / 'native/main.cpp'
        path.write_bytes(b'own-frozen-overlay')
        self.recipe['overlays'] = {'native/main.cpp': source.digest(path.read_bytes())}
        self.recipe['files'][0]['SHA256'] = self.recipe['overlays']['native/main.cpp']
        self.assertEqual(self.prepare()['Application/native/main.cpp'], path.read_bytes())
        path.write_bytes(b'changed-after-pin')
        with self.assertRaisesRegex(ValueError, 'Recipe input changed'):
            self.prepare()
        self.assertEqual(path.read_bytes(), b'changed-after-pin')

    def test_incomplete_patch_chain_rejected(self):
        (self.overlay / 'tools').mkdir()
        raw = b'# own empty fixture patch\n'
        (self.overlay / 'tools/native_static_shell_patch.py').write_bytes(raw)
        self.recipe['patches'] = {'native_static_shell_patch.py': source.digest(raw)}
        with self.assertRaisesRegex(ValueError, 'Incomplete patch chain'):
            self.prepare()

    def test_fresh_materialization_and_no_overwrite_of_existing_output(self):
        output = self.root / 'fresh-source'
        values = self.prepare()
        source.write_fresh(output, values, {'sourceFiles': 1})
        self.assertEqual((output / 'Application/native/main.cpp').read_bytes(), b'committed-source\r\n')
        marker = output / 'user-data'
        marker.write_bytes(b'keep')
        with self.assertRaises(ValueError):
            source.write_fresh(output, values, {})
        self.assertEqual(marker.read_bytes(), b'keep')

    def test_unsafe_write_has_no_partial_output(self):
        output = self.root / 'must-not-exist'
        with self.assertRaises(ValueError):
            source.write_fresh(output, {'Application/../escape': b'bad'}, {})
        self.assertFalse(output.exists())
        self.assertFalse((self.root / 'escape').exists())
        self.assertEqual(list(self.root.glob('must-not-exist.prepare-*')), [])


if __name__ == '__main__':
    unittest.main()
