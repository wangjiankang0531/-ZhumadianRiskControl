import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_original_attachment_references import FIELDS, audit, decode_row, field_inventory, reference_kind


class AttachmentAudit(unittest.TestCase):
    def test_empty_is_not_recovery_or_a_reference(self):
        for value in (None, '', '  ', 'null', '[]', '{}', '""'):
            with self.subTest(value=value):
                result = field_inventory(value)
                self.assertFalse(result['nonEmpty'])
                self.assertFalse(result['references'])

    def test_business_template_and_object_routes_are_distinct(self):
        self.assertEqual(reference_kind('/sys-file/bucket/object.pdf'), 'business-sys-file-object')
        self.assertEqual(reference_kind('/zhumadian/api/serv/sys-file/local/file/template.xlsx'), 'business-classpath-template')
        self.assertEqual(reference_kind('/api/file/Download?fileName=opaque'), 'platform-file-api')

    def test_nested_original_attachment_shapes_do_not_output_names_or_urls(self):
        text = json.dumps([{'name': 'private-original-filename.pdf', 'url': '/sys-file/a/secret.pdf'},
                           {'children': [{'file_url': 'https://private.example/bucket/secret.pdf?signature=secret'}]}])
        result = field_inventory(text)
        self.assertEqual(len(result['references']), 2)
        for forbidden in ('private-original', 'private.example', 'signature', 'secret.pdf'):
            self.assertNotIn(forbidden, json.dumps(result))

    def test_strings_without_recognized_reference_do_not_become_objects(self):
        result = field_inventory('{"id":"private-id","name":"private-name"}')
        self.assertTrue(result['unrecognizedStructured'])
        self.assertFalse(result['references'])

    def test_plain_and_json_string_list_urls_are_found(self):
        self.assertEqual(len(field_inventory('/sys-file/a/b')['references']), 1)
        self.assertEqual(len(field_inventory('["/sys-file/a/b","https://example.invalid/file"]')['references']), 2)
        self.assertEqual(len(field_inventory('"opaque-file-name.xlsx"')['references']), 1)

    def test_original_form_delimiters_split_multiple_objects_only_when_explicit(self):
        for separator in (',', ';'):
            value = '/sys-file/bucket/first.png' + separator + ' /sys-file/bucket/second.png'
            result = field_inventory(value, separator)
            self.assertEqual(len(result['references']), 2)
            self.assertEqual(result['format'], 'delimited-plain')
        self.assertEqual(len(field_inventory('https://example.invalid/object?x=a,b')['references']), 1)
        self.assertEqual(len(field_inventory('[{"url":"https://example.invalid/object?x=a,b"}]', ',')['references']), 1)
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_SUPPORTED'):
            field_inventory('one|two', '|')

    def test_malformed_json_is_preserved_as_unknown(self):
        result = field_inventory('[{"url":"truncated')
        self.assertEqual(result['format'], 'malformed-json')
        self.assertTrue(result['nonEmpty'])
        self.assertTrue(result['unrecognizedStructured'])
        self.assertFalse(result['references'])

    def test_unsafe_paths_and_credentials_do_not_turn_into_fetches(self):
        for value in ('/a/%2e%2e/private', '/a/../private', '/a\\private'):
            self.assertEqual(reference_kind(value), 'unsafe-relative-path')
        self.assertEqual(reference_kind('https://user:secret@example.invalid/a'), 'url-with-userinfo')
        self.assertEqual(reference_kind('javascript:private'), 'unsupported-scheme')
        self.assertEqual(reference_kind('http://example.invalid:bad/a'), 'unsupported-reference')

    def test_structure_and_field_size_limits_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'STRUCTURE_LIMIT'):
            field_inventory('[' * 18 + '"/url"' + ']' * 18)
        with self.assertRaisesRegex(ValueError, 'FIELD_LIMIT'):
            field_inventory('x' * (1024 * 1024 + 1))

    def test_only_selected_columns_are_utf8_decoded(self):
        table, row = decode_row('["t",["2F61","not-hex-private-unselected"]]', ['url', 'other'], ['url'])
        self.assertEqual(row, {'url': '/a'})
        for raw, code in [('["t",[]]', 'ROW_WIDTH'), ('["t",["X"]]', 'UTF8_HEX_REQUIRED')]:
            with self.assertRaisesRegex(ValueError, code):
                decode_row(raw, ['url'], ['url'])

    def make_export(self, folder):
        folder.mkdir()
        tables = []; counts = []
        for schema, names in FIELDS.items():
            lines = []
            for table, fields in names.items():
                tables.append({'TABLE_SCHEMA': schema, 'TABLE_NAME': table, 'columns': [{'COLUMN_NAME': f} for f in fields]})
                values = ['/sys-file/fixture/object.pdf'.encode().hex()] + [None] * (len(fields) - 1)
                lines.append(json.dumps([table, values], separators=(',', ':')).encode() + b'\n')
                counts.append({'schema': schema, 'table': table, 'rows': 1})
            (folder / (schema + '.rows.jsonl.gz')).write_bytes(gzip.compress(b''.join(lines)))
        (folder / 'catalog.json').write_text(json.dumps({'tablesAndViews': tables}), encoding='utf-8')
        files = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in folder.iterdir()]
        raw = json.dumps({'files': files, 'tableCounts': counts}).encode()
        (folder / 'manifest.json').write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def test_pinned_stream_audit_counts_fields_deduplicates_and_remains_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pin = self.make_export(root / 'export')
            result = audit(root / 'export', pin, root / 'output')
            self.assertEqual(result['uniqueReferenceCount'], 1)
            self.assertEqual(len(result['fields']), sum(len(fs) for ts in FIELDS.values() for fs in ts.values()))
            self.assertFalse(result['referenceScopeComplete'])
            self.assertFalse(result['objectsRecovered'])
            self.assertFalse(result['fileServiceRuntimeVerified'])
            self.assertNotIn('object.pdf', json.dumps(result))
            with self.assertRaisesRegex(ValueError, 'FRESH_SEPARATE'):
                audit(root / 'export', pin, root / 'output')

    def test_only_top_level_bucket_names_are_compared_without_entering_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pin = self.make_export(root / 'export')
            snapshot = root / 'objects'; (snapshot / '.minio.sys').mkdir(parents=True)
            (snapshot / '.minio.sys/private-do-not-open').write_text('not a public object')
            result = audit(root / 'export', pin, root / 'output', snapshot)
            observation = result['objectSnapshotObservation']
            self.assertEqual(observation['topLevelBusinessDirectories'], 0)
            self.assertEqual(observation['referencedBucketFingerprints'], 1)
            self.assertEqual(observation['referencedBucketDirectoryMatches'], 0)
            self.assertFalse(observation['internalMetadataOpened'])
            (snapshot / 'fixture').mkdir()
            result = audit(root / 'export', pin, root / 'output2', snapshot)
            self.assertEqual(result['objectSnapshotObservation']['referencedBucketDirectoryMatches'], 1)
            self.assertNotIn('fixture', json.dumps(result))

    def test_wrong_pin_or_modified_payload_is_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pin = self.make_export(root / 'export')
            with self.assertRaisesRegex(ValueError, 'MANIFEST_PIN_MISMATCH'):
                audit(root / 'export', '0' * 64, root / 'output')
            target = root / 'export/jnpf.rows.jsonl.gz'; raw = bytearray(target.read_bytes()); raw[-1] ^= 1; target.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'PAYLOAD_SHA_MISMATCH'):
                audit(root / 'export', pin, root / 'output')
            self.assertFalse((root / 'output').exists())

    def test_renamed_or_missing_selected_field_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pin = self.make_export(root / 'export')
            path = root / 'export/catalog.json'; value = json.loads(path.read_bytes())
            value['tablesAndViews'][0]['columns'][0]['COLUMN_NAME'] = 'unknown_field'
            path.write_text(json.dumps(value), encoding='utf-8')
            manifest_path = root / 'export/manifest.json'; manifest = json.loads(manifest_path.read_bytes())
            entry = next(x for x in manifest['files'] if x['name'] == 'catalog.json')
            entry.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            raw = json.dumps(manifest).encode(); manifest_path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'ATTACHMENT_COLUMNS_REQUIRED'):
                audit(root / 'export', hashlib.sha256(raw).hexdigest(), root / 'output')


if __name__ == '__main__':
    unittest.main()
