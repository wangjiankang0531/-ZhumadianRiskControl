import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from original_candidate_source_preflight import SourcePreflightError, require_source_files


class SourcePreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='own-source-probe-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'own.synthetic'
        self.path.write_bytes(b'private synthetic content is never returned')
        self.files = [{'label': 'own_source', 'path': str(self.path)}]

    def test_real_child_reads_head_without_returning_content_or_path(self):
        before = self.path.read_bytes()
        result = require_source_files(self.files)
        self.assertTrue(result['passed'])
        self.assertNotIn('private synthetic', json.dumps(result))
        self.assertNotIn(str(self.path), json.dumps(result))
        self.assertEqual(before, self.path.read_bytes())

    def test_real_child_reports_missing_file_and_empty_file(self):
        for path in (self.root / 'missing', self.root / 'empty'):
            if path.name == 'empty': path.write_bytes(b'')
            with self.assertRaises(SourcePreflightError) as error:
                require_source_files([{'label': 'own_missing', 'path': str(path)}])
            self.assertEqual(error.exception.report['reason'], 'source-unavailable')

    def test_real_sleeping_owned_child_is_killed_and_waited_on_timeout(self):
        real_run = subprocess.run
        started = time.monotonic()
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return real_run([sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)
        with patch('original_candidate_source_preflight.subprocess.run', side_effect=run):
            with self.assertRaises(SourcePreflightError) as error:
                require_source_files(self.files, timeout=.2)
        self.assertEqual(error.exception.report['reason'], 'read-timeout')
        self.assertEqual(len(calls), 1)
        self.assertLess(time.monotonic() - started, 10)

    def test_unexpected_worker_labels_or_flags_are_rejected(self):
        for rows in ([{'label': 'other', 'readable': True, 'reason': 'readable'}],
                     [{'label': 'own_source', 'readable': True, 'reason': 'not-readable'}],
                     [{'label': 'own_source', 'readable': 1, 'reason': 'readable'}]):
            with patch('original_candidate_source_preflight.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(rows).encode(), b'')):
                with self.assertRaises(SourcePreflightError) as error: require_source_files(self.files)
            self.assertEqual(error.exception.report['reason'], 'invalid-worker-result')

    def test_worker_error_does_not_expose_stderr(self):
        with patch('original_candidate_source_preflight.subprocess.run', return_value=subprocess.CompletedProcess([], 1, b'', b'private test stderr')):
            with self.assertRaises(SourcePreflightError) as error: require_source_files(self.files)
        self.assertNotIn('private test', str(error.exception.report))

    def test_relative_duplicate_and_control_character_input_rejected(self):
        bad = [[{'label': 'bad', 'path': 'relative'}], self.files * 2,
               [{'label': 'bad', 'path': str(self.path) + '\n'}]]
        for files in bad:
            with self.assertRaises(ValueError): require_source_files(files)

    def controller_fixture(self, missing=False):
        app = self.root / 'Application'
        workspace = app / 'work' / 'own-fixture'
        (app / 'tools').mkdir(parents=True)
        (app / 'tools' / 'reference_flat_runtime.py').write_bytes(b'# own fixture marker')
        preparation = workspace / 'own-pboot-r32'
        preparation.mkdir(parents=True)
        source = self.path if not missing else self.root / 'missing-original'
        (preparation / 'preparation.json').write_text(json.dumps({'sourceArchive': str(source)}))
        controller = Path(__file__).with_name('serve_original_integrated_candidate.py')
        command = [sys.executable, '-B', str(controller), '--workspace', str(workspace), '--name', 'own-j99',
                   '--previous-receipt', str(self.root / 'never-read-previous.json'), '--check-sources-only',
                   '--original-business-config', str(self.path), '--original-business-config-sha256', '0' * 64]
        return workspace, command

    def test_real_controller_source_only_success_does_not_start_or_require_a_previous_run(self):
        workspace, command = self.controller_fixture()
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        report = json.loads(result.stdout)
        self.assertEqual(report['state'], 'sources-readable-only')
        self.assertTrue(report['passed'])
        self.assertFalse((workspace / 'own-j99').exists())
        self.assertFalse((workspace.parents[1] / 'UserData').exists())

    def test_real_controller_missing_source_exits_before_instance_or_content_hash(self):
        workspace, command = self.controller_fixture(missing=True)
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report['state'], 'source-unavailable')
        self.assertEqual(report['reason'], 'source-unavailable')
        self.assertFalse((workspace / 'own-j99').exists())
        self.assertFalse((workspace.parents[1] / 'UserData').exists())

    def test_timeout_bounds_rejected_before_child_start(self):
        with patch('original_candidate_source_preflight.subprocess.run') as runner:
            for value in (0, -1, True, 31, float('nan'), float('inf')):
                with self.assertRaises(ValueError): require_source_files(self.files, timeout=value)
            runner.assert_not_called()


if __name__ == '__main__': unittest.main()
