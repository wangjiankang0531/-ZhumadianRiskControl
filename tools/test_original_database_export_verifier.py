from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy
import gzip
import hashlib
import json
import subprocess
import sys
import unittest

import verify_original_database_export as v


def column(name, ordinal, kind='varchar', generated=''):
    return {'COLUMN_NAME': name, 'ORDINAL_POSITION': str(ordinal), 'DATA_TYPE': kind,
            'COLUMN_TYPE': kind, 'CHARACTER_SET_NAME': 'utf8mb4' if kind == 'varchar' else None,
            'COLLATION_NAME': 'utf8mb4_bin' if kind == 'varchar' else None,
            'EXTRA': 'VIRTUAL GENERATED' if generated else '', 'GENERATION_EXPRESSION': generated}


class Fixture:
    def __init__(self, root):
        self.root = root
        self.root.mkdir()
        self.state = {'readOnly': '1', 'isolationLevel': 'REPEATABLE-READ', 'timeZone': '+00:00',
                      'version': '8.0.fixture', 'sqlMode': 'STRICT_TRANS_TABLES', 'lowerCaseTableNames': '0',
                      'sourceTime': '2025-01-02 03:04:05.123456', 'connectionCharset': 'utf8mb4',
                      'connectionCollation': 'utf8mb4_bin'}
        self.catalog = {'format': v.FORMAT, 'sourceState': self.state,
                        'databases': [{'Database': s, 'Create Database': 'CREATE DATABASE `' + s + '`'}
                                      for s in v.SCHEMAS], 'tablesAndViews': []}
        for schema, name in [('jnpf', 'users_fixture'), ('jnpf', 'zero_rows'), ('tj_endanger', 'types_fixture')]:
            self.catalog['tablesAndViews'].append({'TABLE_SCHEMA': schema, 'TABLE_NAME': name,
                'TABLE_TYPE': 'BASE TABLE', 'ENGINE': 'InnoDB', 'create': {'Table': name, 'Create Table': 'CREATE TABLE data_only'},
                'columns': [column('id', 1, 'bigint'), column('value', 2), column('computed', 3, 'int', '`id` + 1')]})
        self.catalog['tablesAndViews'].append({'TABLE_SCHEMA': 'tj_endanger', 'TABLE_NAME': 'view_fixture',
            'TABLE_TYPE': 'VIEW', 'ENGINE': None, 'create': {'View': 'view_fixture', 'Create View': 'CREATE VIEW data_only'},
            'columns': [column('id', 1, 'bigint')]})
        for kind, key in (('triggers', 'SQL Original Statement'), ('events', 'Create Event'),
                          ('procedures', 'Create Procedure'), ('functions', 'Create Function')):
            self.catalog[kind] = [{'dbName': 'tj_endanger', 'objectName': kind + '_fixture',
                'definition': {key: 'UNTRUSTED SQL; CALL side_effect();'}}]
        self.rows = {'jnpf': [('users_fixture', ['39323233333732303336383534373735383037', None]),
                             ('users_fixture', ['30', ''])],
                     'tj_endanger': [('types_fixture', ['31', 'E4B8ADE69687F09F9880']),
                                     ('types_fixture', ['32', '00017FFF5C0A'])]}
        self.manifest = {'format': v.FORMAT, 'completed': True, 'schemas': list(v.SCHEMAS),
            'sourceState': copy.deepcopy(self.state), 'readOnlySnapshotVerified': True,
            'fullMetadataPrivilegesVerified': True, 'sourceBusinessDmlOrDdlExecuted': False,
            'directPhysicalDatadirAccess': False, 'generatedColumnsExcludedFromRows': True}

    def write(self, raw_streams=None):
        (self.root / 'catalog.json').write_text(json.dumps(self.catalog, ensure_ascii=False), encoding='utf-8')
        table_counts = []
        for schema in v.SCHEMAS:
            rows = self.rows[schema]
            stream = b''.join(v.encode_row(name, values) for name, values in rows)
            if raw_streams and schema in raw_streams:
                stream = raw_streams[schema]
            (self.root / (schema + '.rows.jsonl.gz')).write_bytes(gzip.compress(stream, mtime=0))
            for obj in self.catalog['tablesAndViews']:
                if obj['TABLE_SCHEMA'] != schema or obj['TABLE_TYPE'] != 'BASE TABLE':
                    continue
                name = obj['TABLE_NAME']
                lines = [v.encode_row(n, vals) for n, vals in rows if n == name]
                table_counts.append({'schema': schema, 'table': name, 'rows': len(lines),
                                     'rowStreamSHA256': v.digest(b''.join(lines))})
        self.manifest['tableCounts'] = table_counts
        return self.seal()

    def seal(self):
        self.manifest['files'] = [{'name': n, 'bytes': (self.root / n).stat().st_size,
                                  'sha256': v.digest((self.root / n).read_bytes())} for n in v.PAYLOAD_FILES]
        return self.write_manifest()

    def write_manifest(self):
        raw = json.dumps(self.manifest, ensure_ascii=False).encode()
        (self.root / 'manifest.json').write_bytes(raw)
        self.sha = v.digest(raw)
        return self.sha


class ExportVerification(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(Path(self.temp.name) / 'export')
        self.f.write()

    def reject(self, code, **kwargs):
        with self.assertRaisesRegex(v.InvalidExport, '^' + code + '$'):
            v.verify(self.f.root, self.f.sha, **kwargs)

    def test_complete_fixture_preserves_null_empty_generated_zero_table_and_original_bytes(self):
        before = {p.name: p.read_bytes() for p in self.f.root.iterdir()}
        report = v.verify(self.f.root, self.f.sha)
        self.assertEqual((report['tables'], report['rows'], report['views']), (3, 4, 1))
        self.assertEqual((report['sqlNullValues'], report['nonNullEmptyValues']), (1, 1))
        self.assertEqual(report['generatedColumnsExcluded'], 3)
        self.assertEqual(report['tableCounts'][1]['rows'], 0)
        self.assertEqual(report['auxiliarySQLObjects'], dict.fromkeys(('triggers', 'events', 'procedures', 'functions'), 1))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.f.root.iterdir()})
        self.assertEqual(report['databaseConnections'], 0)
        for field in ('SQLExecuted', 'restoreVerified', 'applicationParityVerified', 'primaryKeyUniquenessVerified',
                      'foreignKeyIntegrityVerified', 'fieldTypeRestorationVerified'):
            self.assertIs(report[field], False)

    def test_missing_success_manifest_or_failed_marker(self):
        (self.f.root / 'manifest.json').unlink()
        self.reject('EXPORT_FILE_SET_INVALID')
        self.f.write()
        (self.f.root / 'FAILED.json').write_text('{}')
        self.reject('FAILED_EXPORT')

    def test_manifest_pinned_and_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(v.InvalidExport, 'MANIFEST_SHA_MISMATCH'):
            v.verify(self.f.root, '0' * 64)
        p = self.f.root / 'manifest.json'
        raw = p.read_bytes().replace(b'{', b'{"completed":true,', 1)
        p.write_bytes(raw); self.f.sha = v.digest(raw)
        self.reject('DUPLICATE_JSON_KEY')

    def test_payload_name_escape_and_duplicates_rejected(self):
        for bad in ('../outside', 'D:/outside', 'jnpf.rows.jsonl.gz'):
            with self.subTest(bad=bad):
                self.f.write()
                self.f.manifest['files'][0]['name'] = bad
                self.f.write_manifest()
                self.reject('MANIFEST_FILE_SCOPE_OR_DUPLICATE')

    def test_file_sha_and_byte_count_are_checked(self):
        p = self.f.root / 'catalog.json'
        p.write_bytes(p.read_bytes() + b' ')
        self.reject('FILE_SIZE_MISMATCH')
        self.f.manifest['files'][0]['bytes'] += 1
        self.f.write_manifest()
        self.reject('FILE_SHA_MISMATCH')

    def test_corrupt_and_truncated_gzip_rejected_even_with_matching_file_manifest(self):
        for truncate in (False, True):
            with self.subTest(truncate=truncate):
                self.f.write(); p = self.f.root / 'jnpf.rows.jsonl.gz'; raw = p.read_bytes()
                p.write_bytes(raw[:-3] if truncate else raw[:-8] + bytes([raw[-8] ^ 1]) + raw[-7:])
                self.f.seal()
                self.reject('GZIP_STREAM_INVALID')

    def test_unknown_table_and_column_shape_rejected(self):
        self.f.rows['jnpf'][0] = ('not_a_table', ['31', None])
        self.f.write(); self.reject('ROW_TABLE_UNKNOWN')
        self.f.rows['jnpf'][0] = ('users_fixture', ['31'])
        self.f.write(); self.reject('ROW_COLUMN_COUNT_MISMATCH')

    def test_hex_is_even_uppercase_and_non_null_is_string(self):
        for bad in ('abcD', '1', 'GG', 0, False, {}):
            with self.subTest(bad=bad):
                self.f.write(raw_streams={'jnpf': json.dumps(['users_fixture', ['31', bad]]).encode() + b'\n'})
                self.reject('ROW_HEX_INVALID')

    def test_noncanonical_or_unterminated_row_rejected(self):
        line = v.encode_row('users_fixture', ['31', None])
        self.f.write(raw_streams={'jnpf': line.replace(b',', b', ', 1)})
        self.reject('ROW_ENCODING_NONCANONICAL')
        self.f.write(raw_streams={'jnpf': line[:-1]})
        self.reject('ROW_LINE_TRUNCATED')

    def test_table_count_and_row_digest_rejected(self):
        self.f.manifest['tableCounts'][0]['rows'] += 1
        self.f.write_manifest(); self.reject('TABLE_ROW_COUNT_MISMATCH')
        self.f.write(); self.f.manifest['tableCounts'][0]['rowStreamSHA256'] = '0' * 64
        self.f.write_manifest(); self.reject('TABLE_ROW_STREAM_SHA_MISMATCH')

    def test_table_count_scope_order_and_empty_table_coverage(self):
        self.f.manifest['tableCounts'].pop(1)
        self.f.write_manifest(); self.reject('TABLE_COUNT_COVERAGE_INVALID')
        self.f.write(); self.f.manifest['tableCounts'].reverse()
        self.f.write_manifest(); self.reject('TABLE_COUNT_ORDER_OR_SCOPE_INVALID')

    def test_noncontiguous_table_rows_rejected(self):
        self.f.rows['jnpf'] = [('users_fixture', ['31', None]), ('zero_rows', ['32', '']),
                               ('users_fixture', ['33', ''])]
        self.f.write(); self.reject('ROW_TABLE_ORDER_INVALID')

    def test_readonly_utc_and_schema_claims_must_match(self):
        self.f.manifest['sourceState']['timeZone'] = '+08:00'
        self.f.write_manifest(); self.reject('SOURCE_STATE_CLAIMS_INVALID')
        self.f.manifest['sourceState'] = copy.deepcopy(self.f.state)
        self.f.manifest['sourceState']['version'] = '8.0.other-fixture'
        self.f.write_manifest(); self.reject('SOURCE_STATE_MISMATCH')
        self.f.manifest['schemas'] = ['jnpf', 'other']
        self.f.write_manifest(); self.reject('MANIFEST_SCHEMA_SCOPE_INVALID')

    def test_unsafe_export_claims_not_accepted(self):
        for key in ('sourceBusinessDmlOrDdlExecuted', 'directPhysicalDatadirAccess'):
            with self.subTest(key=key):
                self.f.write(); self.f.manifest[key] = True; self.f.write_manifest()
                self.reject('MANIFEST_EXPORT_CLAIMS_INVALID')
                self.f.manifest[key] = False

    def test_engine_columns_and_generated_metadata_rejected(self):
        obj = self.f.catalog['tablesAndViews'][0]
        obj['ENGINE'] = 'MyISAM'; self.f.write(); self.reject('NONTRANSACTIONAL_TABLE')
        obj['ENGINE'] = 'InnoDB'; obj['columns'][1]['ORDINAL_POSITION'] = '1'
        self.f.write(); self.reject('COLUMN_DUPLICATE_OR_ORDER_INVALID')
        obj['columns'][1]['ORDINAL_POSITION'] = '2'; obj['columns'][2]['GENERATION_EXPRESSION'] = ''
        self.f.write(); self.reject('GENERATION_EXPRESSION_MISSING')

    def test_resource_limits_cover_expansion_row_line_and_time(self):
        for limits, code in ((v.Limits(uncompressed_bytes=5), 'UNCOMPRESSED_SIZE_LIMIT'),
                             (v.Limits(row_value_bytes=1), 'ROW_VALUE_SIZE_LIMIT'),
                             (v.Limits(line_bytes=4), 'ROW_LINE_SIZE_LIMIT'),
                             (v.Limits(compressed_bytes=4), 'COMPRESSED_SIZE_LIMIT'),
                             (v.Limits(metadata_bytes=4), 'MANIFEST_SIZE_LIMIT'),
                             (v.Limits(seconds=-1), 'VERIFICATION_TIME_LIMIT')):
            with self.subTest(code=code): self.reject(code, limits=limits)

    def test_java_control_character_quoting_and_unicode_name(self):
        name = '原表"\\\b'
        obj = self.f.catalog['tablesAndViews'][0]; obj['TABLE_NAME'] = name; obj['create']['Table'] = name
        self.f.rows['jnpf'] = [(name, ['31', ''])]
        self.f.write()
        self.assertEqual(v.verify(self.f.root, self.f.sha)['rows'], 3)
        self.assertIn(b'\\u0008', gzip.decompress((self.f.root / 'jnpf.rows.jsonl.gz').read_bytes()))

    def test_case_collisions_are_explicit_and_do_not_claim_restoration(self):
        extra = copy.deepcopy(self.f.catalog['tablesAndViews'][0]); extra['TABLE_NAME'] = 'USERS_FIXTURE'
        extra['create']['Table'] = 'USERS_FIXTURE'
        self.f.catalog['tablesAndViews'].append(extra); self.f.write()
        result = v.verify(self.f.root, self.f.sha)
        self.assertEqual(result['caseCollisionsForInsensitiveTarget'], [['jnpf', 'users_fixture']])
        self.assertFalse(result['restoreVerified'])

    def test_metadata_is_never_executed_and_unknown_types_remain_unproven(self):
        self.f.catalog['tablesAndViews'][0]['columns'][1]['DATA_TYPE'] = 'geometry'
        self.f.write()
        with patch('socket.create_connection', side_effect=AssertionError('No networking')):
            result = v.verify(self.f.root, self.f.sha)
        self.assertIn('geometry', result['columnTypes'])
        self.assertFalse(result['SQLExecuted'])
        self.assertFalse(result['fieldTypeRestorationVerified'])

    def test_auxiliary_definitions_cannot_be_missing_or_null(self):
        for kind, key in (('triggers', 'SQL Original Statement'), ('events', 'Create Event'),
                          ('procedures', 'Create Procedure'), ('functions', 'Create Function')):
            with self.subTest(kind=kind):
                original = self.f.catalog[kind][0]['definition'][key]
                self.f.catalog[kind][0]['definition'][key] = None
                self.f.write(); self.reject('AUXILIARY_SQL_DEFINITION_MISSING')
                self.f.catalog[kind][0]['definition'][key] = original

    def test_table_definition_name_mismatch_and_missing_source_context(self):
        obj = self.f.catalog['tablesAndViews'][0]
        obj['create']['Table'] = 'wrong_original_name'
        self.f.write(); self.reject('OBJECT_DEFINITION_MISSING')
        obj['create']['Table'] = obj['TABLE_NAME']
        self.f.catalog['sourceState']['connectionCharset'] = None
        self.f.write(); self.reject('SOURCE_CONTEXT_MISSING')

    def test_metadata_change_between_hash_and_parse_is_detected(self):
        original = v.metadata_bytes
        def changed(path, limit, code):
            raw = original(path, limit, code)
            return raw + b' ' if path.name == 'catalog.json' else raw
        with patch.object(v, 'metadata_bytes', side_effect=changed):
            self.reject('CATALOG_CHANGED_DURING_VERIFICATION')

    def test_cli_success_exclusive_report_and_export_unchanged(self):
        tool = Path(v.__file__)
        report = Path(self.temp.name) / 'report.json'
        command = [sys.executable, '-B', str(tool), '--export-directory', str(self.f.root),
                   '--manifest-sha256', self.f.sha, '--report', str(report)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['rows'], 4)
        before = report.read_bytes()
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)['errorCode'], 'REPORT_ALREADY_EXISTS')
        self.assertEqual(report.read_bytes(), before)
        command[-1] = str(self.f.root / 'report.json')
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)['errorCode'], 'REPORT_MUST_BE_OUTSIDE_EXPORT')


if __name__ == '__main__':
    unittest.main()
