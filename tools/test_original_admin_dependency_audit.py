"""Owned Python canaries verify blocking; no original archive, Node or app is run."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import run_original_candidate_without_admin_build_tools as audit


class Classification(unittest.TestCase):
    def test_original_archive_and_build_tools_are_recognized(self):
        for value in ['Y:/source/dist_new.tar.gz', r'\\host\share\DIST_NEW.TAR.GZ', 'node.exe',
                      'D:/Program Files/nodejs/node.exe', 'D:/app/node_modules/@babel/parser/lib/index.js',
                      'D:/app/adapt_original_admin_static.mjs']:
            with self.subTest(value=value): self.assertIsNotNone(audit.forbidden_file(value))

    def test_runtime_inputs_are_not_rejected(self):
        for value in ['D:/payload/admin_static.zip', 'D:/payload/admin_runtime.json',
                      'D:/runtime/opm-service-admin-3.6.0.jar', 'D:/jdk/bin/java.exe', 7]:
            with self.subTest(value=value): self.assertIsNone(audit.forbidden_file(value))

    def test_direct_and_shell_node_invocations_are_rejected(self):
        for executable, arguments in [('node.exe', ['node.exe', '--version']), (None, ['node.exe', '--version']),
            ('cmd.exe', ['cmd.exe', '/c', 'node.exe --version']),
            ('powershell.exe', ['powershell.exe', '-Command', '& "D:/Program Files/nodejs/node.exe" a.mjs'])]:
            with self.subTest(executable=executable): self.assertIsNotNone(audit.forbidden_command(executable, arguments))
        self.assertIsNone(audit.forbidden_command('java.exe', ['java.exe', '-cp', 'application.jar', 'fixture.Main']))

    def test_isolated_hook_blocks_canaries_and_records_ready_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); report = root / 'audit.json'; script = root / 'canary.py'
            script.write_text('''import importlib.util,json,pathlib,subprocess,sys
s=importlib.util.spec_from_file_location('own_audit',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
root=pathlib.Path(sys.argv[2]); ready=root/'ready.json'; report=root/'audit.json'
(root/'dist_new.tar.gz').write_bytes(b'owned harmless canary')
a=m.AdminBuildAudit(report,ready,'a'*64);a.install()
try:(root/'dist_new.tar.gz').read_bytes()
except PermissionError:pass
else:raise AssertionError('CANARY_ARCHIVE_NOT_BLOCKED')
try:sys.audit('subprocess.Popen',None,['node.exe','--version'],None,None)
except PermissionError:pass
else:raise AssertionError('CANARY_NODE_NOT_BLOCKED')
ready.write_text('{}',encoding='utf-8')
subprocess.run([sys.executable,'-B','-c','pass'],check=True)
a.snapshot('owned-canary-completed')
''', encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', script, audit.__file__, root], capture_output=True, timeout=15,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            state = json.loads(report.read_bytes()); self.assertTrue(state['installed']); self.assertTrue(state['readyFileOpenObserved'])
            self.assertEqual(len(state['blockedAttempts']), 2)
            self.assertEqual(state['subprocessEvents'], 2)
            self.assertEqual(state['phase'], 'owned-canary-completed')

    def test_cli_needs_explicit_controller_pin_and_options(self):
        result = subprocess.run([sys.executable, '-B', audit.__file__], capture_output=True, timeout=8,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 2); self.assertIn(b'--controller-sha256', result.stderr)

    def test_cli_forwards_arguments_under_audit_before_running_pinned_own_canary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); tools = root / 'tools'; tools.mkdir()
            workspace = root / 'work'; workspace.mkdir(); reports = workspace / 'reports'; reports.mkdir()
            controller = tools / 'serve_original_integrated_candidate.py'
            controller.write_text('''import pathlib,sys
workspace=pathlib.Path(sys.argv[sys.argv.index('--workspace')+1]);name=sys.argv[sys.argv.index('--name')+1]
run=workspace/name;run.mkdir();(run/'ready.json').write_text('{}',encoding='utf-8')
''', encoding='utf-8')
            pin = hashlib.sha256(controller.read_bytes()).hexdigest(); report = reports / 'audit.json'
            result = subprocess.run([sys.executable, '-B', audit.__file__, '--controller', controller,
                '--controller-sha256', pin, '--audit-output', report, '--', '--workspace', workspace,
                '--name', 'own-j1', '--admin-frontend-runtime', 'owned-fixture-only.json',
                '--admin-frontend-runtime-sha256', 'a' * 64], capture_output=True, timeout=15,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            state = json.loads(report.read_bytes())
            self.assertTrue(state['readyFileOpenObserved']); self.assertTrue(state['controllerReturned'])
            self.assertEqual(state['blockedAttempts'], []); self.assertEqual(state['controllerSHA256'], pin)


if __name__ == '__main__': unittest.main()
