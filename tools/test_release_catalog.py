import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.release_catalog import Catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Application'; self.root.mkdir()
        self.layers = self.root.parent / 'Assets/DLG/layers.json'; self.layers.parent.mkdir(parents=True)
        self.layers.write_bytes(b'{"userData":"preserve"}')
        self.db = self.root.parent / 'Assets/BusinessData/business.sqlite'
        self.catalog = Catalog(self.root, self.root / 'work/selection.json')
        for version in ('old', 'new'):
            folder = self.root / 'Packages' / version; folder.mkdir(parents=True)
            files = {'editor.exe': version.encode(), 'apps/landscape_web/dist/viewer.js': version.encode(),
                     ('runtime/python/python.exe' if os.name == 'nt' else 'runtime/python/bin/python3'): b'python',
                     'tools/landscape_web_server.py': b'server'}
            records = []
            for name, data in files.items():
                f = folder / name; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
                records.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            (folder / 'package.json').write_text(json.dumps({'schema': 'xnby.zhumadian.release.v1',
                'editorVersion': version, 'webVersion': version, 'apiVersion': '0.3.0',
                'activeExecutable': 'editor.exe', 'verified': version == 'old', 'files': records}))
    def choose(self, version, revision, layers=None):
        return self.catalog.select('Packages/' + version, layers or self.layers, self.db, revision, candidate=version == 'new')
    def test_pair_switch_and_rollback_keeps_user_data(self):
        raw = self.layers.read_bytes(); self.choose('old', 0); self.choose('new', 1)
        self.assertEqual(self.catalog.plan('editor')['selected']['editorVersion'], 'new')
        self.assertEqual(self.catalog.plan('web')['selected']['webVersion'], 'new')
        state = self.catalog.rollback(2)
        self.assertEqual((state['revision'], state['selected']['webVersion']), (3, 'old'))
        self.assertEqual(self.layers.read_bytes(), raw); self.assertFalse(self.db.exists())
    def test_stale_writer_cannot_overwrite(self):
        self.choose('old', 0); before = self.catalog.state.read_bytes()
        with self.assertRaisesRegex(ValueError, 'revision conflict'): self.choose('new', 0)
        self.assertEqual(self.catalog.state.read_bytes(), before)
    def test_changed_candidate_rejects_without_changing_pointer(self):
        self.choose('old', 0); before = self.catalog.state.read_bytes()
        (self.root / 'Packages/new/editor.exe').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'content changed'): self.choose('new', 1)
        self.assertEqual(self.catalog.state.read_bytes(), before)
    def test_candidate_requires_explicit_selection(self):
        with self.assertRaisesRegex(ValueError, 'explicit candidate'):
            self.catalog.select('Packages/new', self.layers, self.db, 0)
    def test_manifest_changed_after_selection_refuses_launch(self):
        self.choose('new', 0); p = self.root / 'Packages/new/package.json'; p.write_bytes(p.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'manifest changed'): self.catalog.plan('editor')
    def test_atomic_replace_failure_keeps_previous_and_cleans_pending(self):
        self.choose('old', 0); before = self.catalog.state.read_bytes()
        with patch('tools.release_catalog.os.replace', side_effect=OSError('injected disk failure')):
            with self.assertRaises(OSError): self.choose('new', 1)
        self.assertEqual(self.catalog.state.read_bytes(), before)
        self.assertFalse(list(self.catalog.state.parent.glob('*.pending')))
        self.assertFalse(self.catalog.state.with_name('selection.json.lock').exists())
    def test_live_writer_is_not_removed(self):
        lock = self.catalog.state.with_name('selection.json.lock'); lock.parent.mkdir(parents=True); lock.write_text('owned')
        with self.assertRaisesRegex(RuntimeError, 'writer already exists'): self.choose('old', 0)
        self.assertEqual(lock.read_text(), 'owned')
    def test_rollback_uses_current_shared_data_binding(self):
        self.choose('old', 0)
        other = self.layers.with_name('later.json'); other.write_bytes(b'new user data')
        self.choose('new', 1, other)
        state = self.catalog.rollback(2)
        self.assertEqual((self.root / state['selected']['data']['layers']).resolve(), other)
    def test_rollback_refuses_changed_old_release(self):
        self.choose('old', 0); self.choose('new', 1)
        (self.root / 'Packages/old/editor.exe').write_bytes(b'changed')
        with self.assertRaises(ValueError): self.catalog.rollback(2)
        self.assertEqual(self.catalog.read()['revision'], 2)
    def test_paths_move_with_installation(self):
        self.choose('old', 0)
        target = self.root.parent.with_name(self.root.parent.name + '_moved')
        self.root.parent.rename(target)
        try:
            newroot = target / 'Application'; new = Catalog(newroot, newroot / 'work/selection.json')
            plan = new.plan('web')
            self.assertIn(str(target / 'Assets/DLG/layers.json'), plan['command'])
            self.assertNotIn(str(self.root), json.dumps(plan))
        finally: target.rename(self.root.parent)
    def test_data_arguments_cannot_be_overridden(self):
        self.choose('new', 0)
        for arg in ('--layers=x', '--layer-database', '--host=0.0.0.0', '--port=99'):
            with self.subTest(arg=arg), self.assertRaises(ValueError): self.catalog.plan('web', extra=[arg])
    def test_package_project_seed_cannot_become_shared_data(self):
        seed=self.root/'Packages/new/seed.json';seed.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'outside package folders'):
            self.catalog.select('Packages/new',seed,self.db,0,candidate=True)
    def test_server_modified_after_selection_cannot_launch(self):
        self.choose('new',0)
        (self.root/'Packages/new/tools/landscape_web_server.py').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'content changed'):self.catalog.plan('web')
    def test_cli_parses_port_after_kind_and_preserves_editor_args(self):
        import subprocess,sys
        self.choose('new',0)
        script=self.root/'tools/release_catalog.py';script.parent.mkdir();script.write_bytes(Path(__file__).with_name('release_catalog.py').read_bytes())
        result=subprocess.run([sys.executable,'-X','utf8',str(script),'--state',str(self.catalog.state),'plan','web','--port','8887'],capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        command=json.loads(result.stdout)['command'];self.assertEqual(command[command.index('--port')+1],'8887')
        result=subprocess.run([sys.executable,'-X','utf8',str(script),'--state',str(self.catalog.state),'plan','editor','--','--validate-layers','--stats=test.json'],capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['command'][-2:],['--validate-layers','--stats=test.json'])
    def test_package_traversal_rejected(self):
        with self.assertRaises(ValueError): self.catalog.select('../elsewhere', self.layers, self.db, 0)
    def test_missing_shared_file_does_not_seed_packaged_copy(self):
        self.layers.unlink()
        with self.assertRaises(ValueError): self.choose('new', 0)
        self.assertFalse(self.layers.exists())
    def test_corrupt_pointer_does_not_fall_back(self):
        self.catalog.state.parent.mkdir(parents=True); self.catalog.state.write_text('{}')
        with self.assertRaises(ValueError): self.catalog.plan('web')
    def test_locked_record_is_one_pair_not_separate_app_pointers(self):
        self.choose('old', 0); self.choose('new', 1)
        state = self.catalog.read()
        self.assertEqual(state['selected']['editorVersion'], state['selected']['webVersion'])
        self.assertEqual(len(state['history']), 1)


if __name__ == '__main__': unittest.main()
