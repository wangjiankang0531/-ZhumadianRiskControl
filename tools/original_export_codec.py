"""Versioned export projection and parameterized restore expressions, no DB I/O."""
import re

FORMAT_V1 = 'tj-original-jdbc-hex-v1'
FORMAT_V2 = 'tj-original-jdbc-hex-v2'
FORMATS = (FORMAT_V1, FORMAT_V2)
ROW_PROJECTION_V2 = {'float': 'hex(cast(cast(column as double) as binary))',
                     'default': 'hex(cast(column as binary))',
                     'sqlNull': 'json-null', 'generatedColumns': 'excluded'}
TYPES = frozenset(('tinyint smallint mediumint int integer bigint decimal numeric float double real '
                   'bit char varchar tinytext text mediumtext longtext binary varbinary tinyblob blob '
                   'mediumblob longblob date time datetime timestamp year enum set json geometry point '
                   'linestring polygon multipoint multilinestring multipolygon geometrycollection').split())


class InvalidEncoding(ValueError):
    """Fixed error codes only."""


def column_type(column):
    if not isinstance(column, dict) or not isinstance(column.get('DATA_TYPE'), str):
        raise InvalidEncoding('COLUMN_DATA_TYPE_REQUIRED')
    kind = column['DATA_TYPE'].lower()
    if kind not in TYPES:
        raise InvalidEncoding('COLUMN_DATA_TYPE_UNSUPPORTED')
    if column.get('GENERATION_EXPRESSION'):
        raise InvalidEncoding('GENERATED_COLUMN_MUST_BE_EXCLUDED')
    return kind


def float_projection_supported(version):
    if not isinstance(version, str) or 'mariadb' in version.lower():
        return False
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:[^0-9].*)?', version)
    if not match:
        return False
    try:
        parts = tuple(map(int, match.groups()))
        return parts >= (8, 0, 17)
    except ValueError:
        return False


def restore_expression(column, export_format):
    if export_format not in FORMATS:
        raise InvalidEncoding('EXPORT_FORMAT_UNSUPPORTED')
    kind = column_type(column)
    if kind == 'float' and export_format == FORMAT_V1:
        raise InvalidEncoding('LEGACY_FLOAT_ENCODING_NOT_LOSSLESS')
    if kind == 'json':
        return 'CONVERT(UNHEX(?) USING utf8mb4)'
    if kind == 'bit':
        return 'CAST(CONV(?,16,10) AS UNSIGNED)'
    charset = column.get('CHARACTER_SET_NAME')
    if charset is not None:
        if not isinstance(charset, str) or not re.fullmatch('[a-z0-9_]+', charset):
            raise InvalidEncoding('COLUMN_CHARSET_INVALID')
        return 'CONVERT(UNHEX(?) USING ' + charset + ')'
    # Geometry values retain MySQL's internal bytes/SRID. Reconstructing WKB can
    # alter the axis order. Target compatibility still needs real-DB validation.
    return 'UNHEX(?)'


def restore_parameter(value):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 8 * 1024**2 or len(value) % 2 or not re.fullmatch('[0-9A-F]*', value):
        raise InvalidEncoding('ROW_HEX_INVALID')
    return value
