from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import unittest

import compare_original_database_exports as c
from test_original_database_export_verifier import Fixture


class CompareExports(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.left = Fixture(self.root / 'source')
        self.left.rows['jnpf'].append(copy.deepcopy(self.left.rows['jnpf'][0]))
        self.left.write()
        self.right = copy.deepcopy(self.left)
        self.right.root = self.root / 'target'
        self.right.root.mkdir()
        self.right.write()
        self.scratch = self.root / 'scratch'
        self.scratch.mkdir()
        self.limits = c.Limits(spool_bytes=8 * 1024**2, minimum_free_after_spool=0)

    def compare(self, **kwargs):
        return c.compare(self.left.root, self.left.sha, self.right.root, self.right.sha,
                         self.scratch, kwargs.pop('limits', self.limits), **kwargs)

    def test_row_order_does_not_change_comparison_and_duplicates_survive(self):
        self.right.rows['jnpf'] = self.right.rows['jnpf'][1:] + self.right.rows['jnpf'][:1]
        self.right.rows['tj_endanger'].reverse()
        self.right.state['sourceTime'] = '2026-01-02 03:04:05.123456'
        self.right.manifest['sourceState'] = copy.deepcopy(self.right.state)
        self.right.write()
        report = self.compare()
        self.assertTrue(report['exportedContentEqual'])
        self.assertTrue(report['rowMultisetsEqual'])
        self.assertEqual(sum(x['sourceRows'] for x in report['tableComparisons']), 5)
        self.assertNotEqual(self.left.manifest['tableCounts'][0]['rowStreamSHA256'],
                            self.right.manifest['tableCounts'][0]['rowStreamSHA256'])
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertGreater(report['observedSpoolBytesBeforeClose'], 0)
        for key in ('restoreExecutionVerified', 'fieldTypeRestorationVerified',
                    'originalBusinessBehaviorVerified', 'fullCloneReady',
                    'generatedColumnValuesCompared'):
            self.assertIs(report[key], False)

    def test_duplicate_multiplicity_difference_is_detected(self):
        self.right.rows['jnpf'].pop()
        self.right.write()
        report = self.compare()
        self.assertFalse(report['rowMultisetsEqual'])
        self.assertEqual(sum(x['missingRowOccurrences'] for x in report['tableComparisons']), 1)
        self.assertEqual(sum(x['additionalRowOccurrences'] for x in report['tableComparisons']), 0)

    def test_equal_total_counts_cannot_hide_replacement_or_null_empty_change(self):
        self.right.rows['jnpf'][0] = ('users_fixture', [self.right.rows['jnpf'][0][1][0], ''])
        self.right.write()
        report = self.compare()
        self.assertFalse(report['rowMultisetsEqual'])
        self.assertEqual(sum(x['missingRowOccurrences'] for x in report['tableComparisons']), 1)
        self.assertEqual(sum(x['additionalRowOccurrences'] for x in report['tableComparisons']), 1)
        self.assertEqual(sum(x['differentDistinctRowValues'] for x in report['tableComparisons']), 2)

    def test_values_and_source_files_do_not_leak_or_change(self):
        before = {str(p): p.read_bytes() for root in (self.left.root, self.right.root)
                  for p in root.iterdir()}
        self.right.rows['tj_endanger'][0] = ('types_fixture', ['31', 'FEFF'])
        self.right.write()
        before = {str(p): p.read_bytes() for root in (self.left.root, self.right.root)
                  for p in root.iterdir()}
        report = self.compare()
        raw = json.dumps(report)
        for value in ('E4B8ADE69687F09F9880', 'FEFF', 'users_fixture', 'UNTRUSTED SQL', 'side_effect'):
            self.assertNotIn(value, raw)
        self.assertEqual(before, {str(p): p.read_bytes() for root in (self.left.root, self.right.root)
                                 for p in root.iterdir()})
        self.assertEqual(report['originalDatabaseConnections'], 0)
        self.assertFalse(report['sourceSQLExecuted'])

    def test_ddl_indexes_generated_expressions_and_auxiliary_are_not_normalized(self):
        for mode in ('ddl', 'generated', 'auxiliary', 'collation'):
            with self.subTest(mode=mode):
                self.right = copy.deepcopy(self.left)
                self.right.root = self.root / 'target'
                if mode == 'ddl':
                    self.right.catalog['tablesAndViews'][0]['create']['Create Table'] += ' KEY `x` (`id`)'
                elif mode == 'generated':
                    self.right.catalog['tablesAndViews'][0]['columns'][2]['GENERATION_EXPRESSION'] = '`id` + 2'
                elif mode == 'auxiliary':
                    self.right.catalog['triggers'][0]['definition']['SQL Original Statement'] += ' altered'
                else:
                    self.right.catalog['tablesAndViews'][0]['columns'][1]['COLLATION_NAME'] = 'utf8mb4_general_ci'
                self.right.write()
                report = self.compare()
                self.assertTrue(report['rowMultisetsEqual'])
                self.assertFalse(report['metadataExactlyEqual'])
                self.assertEqual(len(report['metadataDifferences']), 1)

    def test_missing_zero_row_table_fails_metadata_comparison(self):
        self.right.catalog['tablesAndViews'] = [x for x in self.right.catalog['tablesAndViews']
                                               if x['TABLE_NAME'] != 'zero_rows']
        self.right.write()
        report = self.compare()
        self.assertTrue(report['rowMultisetsEqual'])
        self.assertFalse(report['exportedContentEqual'])
        self.assertEqual(len(report['metadataDifferences']), 1)

    def test_source_modes_must_match_except_capture_time(self):
        self.right.state['sqlMode'] = 'NO_BACKSLASH_ESCAPES'
        self.right.manifest['sourceState'] = copy.deepcopy(self.right.state)
        self.right.write()
        report = self.compare()
        self.assertFalse(report['sourceContextEqualExceptCaptureTime'])
        self.assertEqual(report['sourceContextDifferenceKeys'], ['sqlMode'])

    def test_catalog_object_enumeration_order_is_ignored_but_column_order_is_not(self):
        self.right.catalog['databases'].reverse()
        self.right.write()
        self.assertTrue(self.compare()['exportedContentEqual'])
        cols = self.right.catalog['tablesAndViews'][0]['columns']
        cols[0], cols[1] = cols[1], cols[0]
        cols[0]['ORDINAL_POSITION'], cols[1]['ORDINAL_POSITION'] = '1', '2'
        self.right.write()
        self.assertFalse(self.compare()['metadataExactlyEqual'])

    def test_pinned_manifest_and_corrupt_payload_rejected_before_spooling(self):
        with self.assertRaisesRegex(c.export.InvalidExport, '^MANIFEST_SHA_MISMATCH$'):
            c.compare(self.left.root, '0' * 64, self.right.root, self.right.sha, self.scratch, self.limits)
        path = self.right.root / 'tj_endanger.rows.jsonl.gz'
        path.write_bytes(path.read_bytes()[:-2])
        with self.assertRaises(c.export.InvalidExport):
            self.compare()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_input_mutation_during_compare_is_rejected_and_spool_is_removed(self):
        original = c.recheck
        mutated = False

        def mutate(*args):
            nonlocal mutated
            if not mutated:
                path = self.right.root / 'catalog.json'
                path.write_bytes(path.read_bytes() + b' ')
                mutated = True
            return original(*args)

        with patch.object(c, 'recheck', side_effect=mutate):
            with self.assertRaisesRegex(c.InvalidComparison, '^INPUT_CHANGED_DURING_COMPARISON$'):
                self.compare()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_spool_budget_failure_does_not_leave_private_rows(self):
        payload = '41' * (600 * 1024)
        for fixture in (self.left, self.right):
            fixture.rows['tj_endanger'] = [('types_fixture', ['31', payload])]
            fixture.write()
        with self.assertRaisesRegex(c.InvalidComparison, '^SPOOL_SIZE_LIMIT$'):
            self.compare(limits=c.Limits(spool_bytes=1024**2, minimum_free_after_spool=0))
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_free_space_budget_is_checked_before_temp_creation(self):
        with patch.object(c.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(100, 99, 1)):
            with self.assertRaisesRegex(c.InvalidComparison, '^INSUFFICIENT_SCRATCH_SPACE$'):
                self.compare()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_aliased_and_overlapping_directories_rejected(self):
        with self.assertRaisesRegex(c.InvalidComparison, '^INPUT_DIRECTORIES_MUST_BE_DISTINCT$'):
            c.compare(self.left.root, self.left.sha, self.left.root, self.left.sha, self.scratch, self.limits)
        with self.assertRaisesRegex(c.InvalidComparison, '^SCRATCH_MUST_BE_SEPARATE$'):
            c.compare(self.left.root, self.left.sha, self.right.root, self.right.sha, self.root, self.limits)

    def test_cli_equal_different_and_preexisting_report_are_distinct(self):
        script = Path(c.__file__)
        report = self.root / 'report.json'
        args = [sys.executable, str(script), '--source-directory', str(self.left.root),
                '--source-manifest-sha256', self.left.sha, '--target-directory', str(self.right.root),
                '--target-manifest-sha256', self.right.sha, '--scratch-parent', str(self.scratch),
                '--spool-limit-mib', '8', '--report', str(report)]
        run = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        original = report.read_bytes()
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)
        self.assertEqual(report.read_bytes(), original)
        self.right.rows['jnpf'].pop()
        self.right.write()
        args[args.index('--target-manifest-sha256') + 1] = self.right.sha
        args[-1] = str(self.root / 'different.json')
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
