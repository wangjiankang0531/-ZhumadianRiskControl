"""Synthetic metadata/integrity tests; real original-resource preparation is separate."""
import hashlib
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
import portable_original_admin_frontend as runtime


class PrivateAdminArtifact(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'artifact'; self.root.mkdir()
        self.files = {'index.html': b'<html>synthetic fixture, never original UI</html>'}
        self.files.update({'assets/fixture-' + str(i) + '.txt': b'synthetic resource' for i in range(runtime.SOURCE_FILES - 1)})
        self.payload = self.root / runtime.PAYLOAD; self.write_zip()
        self.spec = {'kind': runtime.KIND, 'ownerId': str(uuid.uuid4()), 'base': '/zhumadian/admin',
            'sourceArchiveSHA256': runtime.SOURCE_SHA, 'sourceArchiveBytes': runtime.SOURCE_ARCHIVE_BYTES,
            'sourceExpandedBytes': runtime.SOURCE_EXPANDED_BYTES, 'privateOriginalResourcesIncluded': True,
            'businessLogicRedesigned': False, 'originalJavaScriptEvaluated': False,
            **{key: 'a' * 64 for key in ['deploymentRecipeSHA256', 'nodeSHA256', 'parserSHA256']},
            'fileCount': len(self.files), 'expandedBytes': sum(map(len, self.files.values())),
            'files': [{'path': n, 'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for n, v in self.files.items()]}
        self.manifest = self.root / runtime.MANIFEST; self.save()

    def write_zip(self):
        with zipfile.ZipFile(self.payload, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in self.files.items(): archive.writestr(name, value)

    def save(self):
        self.spec['payloadSHA256'] = runtime.sha(self.payload); self.spec['payloadBytes'] = self.payload.stat().st_size
        self.manifest.write_text(json.dumps(self.spec), encoding='utf-8'); self.pin = runtime.sha(self.manifest)

    def load(self): return runtime.load(self.manifest, self.pin)

    def test_complete_synthetic_artifact_loads_and_relocates_without_node_or_original_tar(self):
        files, proof = self.load(); self.assertEqual(files, self.files)
        self.assertFalse(proof['nodeOrParserRequiredAtRuntime']); self.assertFalse(proof['sourceArchiveReadAtRuntime'])
        moved = self.root.with_name('中文 空格'); self.root.rename(moved)
        files, proof = runtime.load(moved / runtime.MANIFEST, self.pin); self.assertEqual(files, self.files)

    def test_explicit_pair_and_trusted_pin_are_required(self):
        self.assertFalse(runtime.validate_selection(None, None))
        for manifest, pin in [(self.manifest, None), (None, self.pin), (self.manifest, 'bad')]:
            with self.subTest(pin=pin), self.assertRaises(ValueError): runtime.load(manifest, pin)
        with self.assertRaisesRegex(ValueError, 'MANIFEST_PIN_MISMATCH'): runtime.load(self.manifest, '0' * 64)

    def test_wrong_mount_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'KIND_OR_BASE_MISMATCH'):
            runtime.load(self.manifest, self.pin, '/other/admin')

    def test_duplicate_json_keys_are_rejected(self):
        self.manifest.write_bytes(b'{"kind":"one","kind":"two"}'); self.pin = runtime.sha(self.manifest)
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ADMIN_RUNTIME_MANIFEST_KEY'): self.load()

    def test_extra_file_beside_payload_is_rejected(self):
        (self.root / 'unreviewed.js').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'EXACT_ADMIN_RUNTIME_FILE_SET'): self.load()

    def test_changed_payload_is_rejected(self):
        self.payload.write_bytes(self.payload.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_PIN_MISMATCH'): self.load()

    def test_member_byte_change_is_rejected_even_with_new_payload_pin(self):
        self.files['index.html'] = b'changed'; self.write_zip(); self.save()
        with self.assertRaisesRegex(ValueError, 'REGULAR_ADMIN_RUNTIME_ZIP_MEMBER_REQUIRED|MEMBER_BYTES_MISMATCH'): self.load()

    def test_missing_zip_member_is_rejected(self):
        self.files.pop('index.html'); self.write_zip(); self.save()
        with self.assertRaisesRegex(ValueError, 'EXACT_ADMIN_RUNTIME_ZIP_MEMBERS'): self.load()

    def test_manifest_traversal_or_duplicate_member_is_rejected(self):
        self.spec['files'][1]['path'] = '../outside'; self.save()
        with self.assertRaisesRegex(ValueError, 'RELATIVE_ADMIN_STATIC_MEMBER_REQUIRED'): self.load()
        self.spec['files'][1]['path'] = 'index.html'; self.save()
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ADMIN_RUNTIME_MEMBER'): self.load()

    def test_symlink_zip_entry_is_rejected(self):
        with zipfile.ZipFile(self.payload, 'w') as archive:
            for name, raw in self.files.items():
                member = zipfile.ZipInfo(name)
                member.external_attr = (0o120777 if name == 'index.html' else 0o100644) << 16
                archive.writestr(member, raw)
        self.save()
        with self.assertRaisesRegex(ValueError, 'REGULAR_ADMIN_RUNTIME_ZIP_MEMBER_REQUIRED'): self.load()

    def test_declared_expansion_limit_is_enforced(self):
        self.spec['files'][0]['bytes'] = runtime.MAX_EXPANDED + 1; self.save()
        with self.assertRaisesRegex(ValueError, 'SIZE_OR_PIN_MISMATCH'): self.load()

    def test_cli_requires_explicit_verify_arguments(self):
        run = subprocess.run([sys.executable, '-B', runtime.__file__, 'verify'], capture_output=True, timeout=8,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(run.returncode, 2); self.assertIn(b'--manifest', run.stderr)

    def test_preparation_rejects_an_untrusted_tool_before_creating_output(self):
        inputs = self.root.parent / 'build-inputs'; inputs.mkdir()
        for name in ['original.tar.gz', 'node.exe', 'parser.js', 'recipe.mjs']:
            (inputs / name).write_bytes(b'synthetic input that must never execute')
        output = self.root.parent / 'never-created'
        with self.assertRaisesRegex(ValueError, 'TRUSTED_ADMIN_PREPARATION_TOOL_PIN_MISMATCH'):
            runtime.prepare(inputs / 'original.tar.gz', inputs / 'node.exe', inputs / 'parser.js', output,
                '/zhumadian/admin', '0' * 64, runtime.sha(inputs / 'parser.js'),
                runtime.sha(inputs / 'recipe.mjs'), inputs / 'recipe.mjs')
        self.assertFalse(output.exists())

    def test_integrated_bad_flags_fail_before_workspace_creation(self):
        workspace = self.root.parent / 'absent-workspace'
        command = [sys.executable, '-B', str(Path(__file__).with_name('serve_original_integrated_candidate.py')),
                   '--workspace', str(workspace), '--name', 'own-j999', '--previous-receipt', str(self.root.parent / 'absent.json')]
        for flags, reason in [(['--admin-frontend-runtime', 'absent.json'], b'ADMIN_RUNTIME_MANIFEST_AND_PIN_REQUIRED_TOGETHER'),
                              (['--admin-frontend-runtime', 'absent.json', '--admin-frontend-runtime-sha256', 'bad'], b'EXPLICIT_ADMIN_RUNTIME_MANIFEST_PIN_REQUIRED')]:
            run = subprocess.run(command + flags, capture_output=True, timeout=8,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertNotEqual(run.returncode, 0); self.assertIn(reason, run.stderr)
            self.assertFalse(workspace.exists())

    def test_integrated_component_is_checked_before_legacy_metadata_or_run_creation(self):
        app = self.root.parent / 'Application'; workspace = app / 'work/runtime'; workspace.mkdir(parents=True)
        (app / 'tools').mkdir(); (app / 'tools/reference_flat_runtime.py').write_bytes(b'fixture marker only')
        command = [sys.executable, '-B', str(Path(__file__).with_name('serve_original_integrated_candidate.py')),
            '--workspace', str(workspace), '--name', 'own-j999', '--previous-receipt', str(self.root.parent / 'absent.json'),
            '--admin-frontend-runtime', str(self.manifest), '--admin-frontend-runtime-sha256', '0' * 64]
        run = subprocess.run(command, capture_output=True, timeout=8,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertNotEqual(run.returncode, 0); self.assertIn(b'ADMIN_RUNTIME_MANIFEST_PIN_MISMATCH', run.stderr)
        self.assertFalse((workspace / 'own-j999').exists()); self.assertFalse((app / 'UserData').exists())

    def test_actual_prepared_controller_branch_only_uses_preloaded_bytes(self):
        files, proof = self.load()
        tree = ast.parse(Path(__file__).with_name('serve_original_integrated_candidate.py').read_text('utf-8'))
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and isinstance(n.test, ast.Name) and n.test.id == 'prepared_admin_requested')
        scope = {'prepared_admin_requested': True, 'preloaded_admin': (files, proof)}
        exec(compile(ast.Module(body=[branch], type_ignores=[]), 'actual-prepared-admin-branch', 'exec'), scope)
        self.assertIs(scope['admin_files'], files)
        self.assertEqual(scope['archive_receipt']['archiveSHA256'], runtime.SOURCE_SHA)


if __name__ == '__main__': unittest.main()
