import unittest
import original_export_codec as c


class RestoreCodec(unittest.TestCase):
    def column(self, kind, charset=None):
        return {'DATA_TYPE': kind, 'CHARACTER_SET_NAME': charset, 'GENERATION_EXPRESSION': ''}

    def test_float_legacy_is_rejected_and_v2_remains_parameterized(self):
        with self.assertRaisesRegex(c.InvalidEncoding, '^LEGACY_FLOAT_ENCODING_NOT_LOSSLESS$'):
            c.restore_expression(self.column('float'), c.FORMAT_V1)
        self.assertEqual(c.restore_expression(self.column('float'), c.FORMAT_V2), 'UNHEX(?)')

    def test_json_bit_and_charsets_use_distinct_restore_expressions(self):
        self.assertEqual(c.restore_expression(self.column('json'), c.FORMAT_V2), 'CONVERT(UNHEX(?) USING utf8mb4)')
        self.assertEqual(c.restore_expression(self.column('bit'), c.FORMAT_V2), 'CAST(CONV(?,16,10) AS UNSIGNED)')
        for charset in ('utf8mb4', 'utf16', 'latin1'):
            self.assertEqual(c.restore_expression(self.column('varchar', charset), c.FORMAT_V2),
                             'CONVERT(UNHEX(?) USING ' + charset + ')')

    def test_geometry_and_binary_do_not_reinterpret_axes_or_encoding(self):
        for kind in ('geometry', 'point', 'blob', 'longblob', 'varbinary', 'binary'):
            self.assertEqual(c.restore_expression(self.column(kind), c.FORMAT_V2), 'UNHEX(?)')

    def test_invalid_format_metadata_or_charset_cannot_generate_sql(self):
        for column, fmt in [(self.column('varchar', 'utf8); DROP TABLE x'), c.FORMAT_V2),
                            ({}, c.FORMAT_V2), (self.column('unknown'), c.FORMAT_V2),
                            (self.column('int'), 'unknown')]:
            with self.assertRaises(c.InvalidEncoding):
                c.restore_expression(column, fmt)
        with self.assertRaisesRegex(c.InvalidEncoding, '^GENERATED_COLUMN_MUST_BE_EXCLUDED$'):
            c.restore_expression({**self.column('int'), 'GENERATION_EXPRESSION': '`id`+1'}, c.FORMAT_V2)

    def test_parameters_preserve_null_empty_and_bytes_without_sql_interpolation(self):
        for value in (None, '', '00017FFF', 'E4B8ADE69687'):
            self.assertEqual(c.restore_parameter(value), value)
        for value in ('0', 'ab', '00\n', 'GG', 0, False, "';DROP TABLE x"):
            with self.assertRaisesRegex(c.InvalidEncoding, '^ROW_HEX_INVALID$'):
                c.restore_parameter(value)

    def test_version_gate_has_no_mariadb_or_unknown_version_fallback(self):
        for version in ('8.0.17', '8.0.44-log', '8.4.0', '9.0.0'):
            self.assertTrue(c.float_projection_supported(version))
        for version in ('5.7.44', '8.0.16', '8.0.fixture', '10.11.0-MariaDB', None):
            self.assertFalse(c.float_projection_supported(version))


if __name__ == '__main__':
    unittest.main()
