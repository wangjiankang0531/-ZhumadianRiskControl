"""Synthetic source-tree boundaries; original file and HTTP coverage is checked separately."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import threading
import time
from unittest.mock import patch
import original_frontend_roots as profile


class StaticRootIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.resources = self.root / 'resources'; self.resources.mkdir()
        self.roots = {}
        for role in profile.ROLES:
            path = self.resources / role; path.mkdir(); self.roots[role] = path
            if role == 'tiles':
                target = path / '0/0/0.png'; target.parent.mkdir(parents=True); target.write_bytes(b'synthetic map')
            else:
                (path / 'index.html').write_bytes(b'owned synthetic index')
                (path / 'asset.js').write_bytes(b'synthetic content; never executed')
        self.bindings = self.root / 'bindings.private.json'; self.manifest = self.root / 'manifest.private.json'
        self.write_bindings(); self.prepared = profile.prepare(self.bindings, self.manifest); self.pin = profile.sha(self.manifest)

    def write_bindings(self, roots=None):
        self.bindings.write_text(json.dumps({'schema': profile.BINDINGS, 'appBasePath': '/zhumadian',
            'roots': roots or {role: str(path) for role, path in self.roots.items()}}), encoding='utf-8')

    def select(self): return profile.select(self.manifest, self.pin, self.bindings)

    def test_all_five_roots_and_map_content_are_verified_without_copying(self):
        roots, proof = self.select(); self.assertEqual(roots, self.roots)
        self.assertTrue(proof['allFiveRootsContentVerified']); self.assertFalse(proof['resourcesCopied'])
        self.assertFalse(proof['legacyGatewayReceiptRead'])
        self.assertNotIn(str(self.root), self.manifest.read_text('utf-8'))

    def test_relocation_changes_bindings_without_rebuilding_content_manifest(self):
        target = self.root / '中文 迁移'
        self.assertEqual(self.resources.resolve().parent, self.root)
        self.assertEqual(target.absolute().parent, self.root); self.assertFalse(target.exists())
        self.resources.rename(target)
        self.write_bindings({role: (target.name + '/' + role) for role in profile.ROLES})
        roots, proof = self.select(); self.assertEqual(profile.sha(self.manifest), self.pin)
        self.assertEqual(roots['tiles'], target / 'tiles')

    def test_changed_asset_is_rejected(self):
        (self.roots['mobile'] / 'asset.js').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'RESOURCE_CONTENT_OR_SET_MISMATCH'): self.select()

    def test_extra_file_is_rejected(self):
        (self.roots['security_pc'] / 'extra.js').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'RESOURCE_CONTENT_OR_SET_MISMATCH'): self.select()

    def test_missing_file_is_rejected(self):
        (self.roots['emergency_pc'] / 'asset.js').unlink()
        with self.assertRaisesRegex(ValueError, 'RESOURCE_CONTENT_OR_SET_MISMATCH'): self.select()

    def test_extra_empty_directory_is_rejected(self):
        (self.roots['bigscreen'] / 'new-route').mkdir()
        with self.assertRaisesRegex(ValueError, 'RESOURCE_CONTENT_OR_SET_MISMATCH'): self.select()

    def test_empty_map_root_cannot_claim_complete_content(self):
        (self.roots['tiles'] / '0/0/0.png').unlink()
        with self.assertRaisesRegex(ValueError, 'INDEX_OR_MAP_REQUIRED'): self.select()

    def test_overlapping_roots_are_rejected(self):
        values = {role: str(path) for role, path in self.roots.items()}; values['security_pc'] = str(self.resources)
        self.write_bindings(values)
        with self.assertRaisesRegex(ValueError, 'DISJOINT_ORIGINAL_FRONTEND_ROOTS_REQUIRED'): self.select()

    def test_missing_role_or_duplicate_binding_keys_are_rejected(self):
        values = {role: str(path) for role, path in self.roots.items() if role != 'tiles'}; self.write_bindings(values)
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL_FRONTEND_BINDINGS_REQUIRED'): self.select()
        self.bindings.write_bytes(b'{"schema":"one","schema":"two"}')
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_FRONTEND_DOCUMENT_KEY'): self.select()

    def test_bad_manifest_pin_fails_before_missing_bindings_are_read(self):
        with self.assertRaisesRegex(ValueError, 'FRONTEND_MANIFEST_PIN_MISMATCH'):
            profile.select(self.manifest, '0' * 64, self.root / 'absent.json')

    def test_manifest_must_not_be_written_into_a_resource_root(self):
        output = self.roots['security_pc'] / 'private-index.json'
        with self.assertRaisesRegex(ValueError, 'METADATA_MUST_NOT_ENTER_RESOURCE_ROOT'):
            profile.prepare(self.bindings, output)
        self.assertFalse(output.exists())

    def test_explicit_three_part_selection_is_required(self):
        self.assertFalse(profile.validate_selection(None, None, None))
        for args in [(self.manifest, self.pin, None), (None, self.pin, self.bindings),
                     (self.manifest, 'bad', self.bindings)]:
            with self.subTest(args=args), self.assertRaises(ValueError): profile.select(*args)

    def test_integrated_bad_flags_fail_before_workspace_creation(self):
        workspace = self.root / 'absent-workspace'
        command = [sys.executable, '-B', str(Path(__file__).with_name('serve_original_integrated_candidate.py')),
            '--workspace', str(workspace), '--name', 'own-j999', '--previous-receipt', str(self.root / 'absent.json')]
        for flags, reason in [(['--frontend-roots-manifest', 'absent.json'], b'FRONTEND_MANIFEST_PIN_AND_BINDINGS_REQUIRED_TOGETHER'),
            (['--frontend-roots-manifest', 'absent.json', '--frontend-roots-sha256', 'bad', '--frontend-roots-bindings', 'absent.json'], b'EXPLICIT_FRONTEND_MANIFEST_PIN_REQUIRED')]:
            result = subprocess.run(command + flags, capture_output=True, timeout=8,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertNotEqual(result.returncode, 0); self.assertIn(reason, result.stderr)
            self.assertFalse(workspace.exists())

    def test_actual_controller_explicit_branch_uses_verified_roots_only(self):
        roots, proof = self.select()
        tree = ast.parse(Path(__file__).with_name('serve_original_integrated_candidate.py').read_text('utf-8'))
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
            and isinstance(n.test, ast.Name) and n.test.id == 'frontend_roots_requested')
        scope = {'frontend_roots_requested': True, 'preverified_frontends': (roots, proof)}
        exec(compile(ast.Module(body=[branch], type_ignores=[]), 'actual-frontends-root-choice', 'exec'), scope)
        self.assertEqual(scope['roots'], roots)

    def test_shared_file_hashing_has_bounded_actual_concurrency(self):
        root = self.roots['security_pc']
        for index in range(24): (root / ('extra-' + str(index) + '.js')).write_bytes(b'synthetic')
        original = profile.hash_member; lock = threading.Lock(); active = 0; peak = 0
        def observed(candidate):
            nonlocal active, peak
            with lock: active += 1; peak = max(peak, active)
            try:
                time.sleep(.005); return original(candidate)
            finally:
                with lock: active -= 1
        with patch.object(profile, 'hash_member', observed): result = profile.scan(root, 'security_pc')
        self.assertEqual(result['fileCount'], 26); self.assertGreater(peak, 1)
        self.assertLessEqual(peak, profile.HASH_WORKERS); self.assertEqual(active, 0)

    def test_file_changed_after_enumeration_is_rejected_before_hash(self):
        file = self.roots['mobile'] / 'asset.js'; before = file.stat()
        file.write_bytes(b'changed after enumeration')
        with self.assertRaisesRegex(ValueError, 'FRONTEND_RESOURCE_CHANGED_BEFORE_HASH'):
            profile.hash_member((file, 'asset.js', before.st_size, before.st_mtime_ns))


if __name__ == '__main__': unittest.main()
