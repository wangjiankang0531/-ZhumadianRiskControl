"""Validate a sealed tj-original-jdbc-hex-v1 export without a DB connection.

SQL definitions and row values remain data. This module never executes them.
A successful verification proves artifact consistency, not source authenticity,
restore compatibility, relational integrity, or application parity.
"""
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
import argparse
import gzip
import hashlib
import json
import re
import stat
import sys
import time

FORMAT = 'tj-original-jdbc-hex-v1'
SCHEMAS = ('jnpf', 'tj_endanger')
PAYLOAD_FILES = ('catalog.json', 'jnpf.rows.jsonl.gz', 'tj_endanger.rows.jsonl.gz')
HEX = re.compile(r'[0-9A-F]*\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')


class InvalidExport(ValueError):
    """A fixed error code, never a source value or SQL statement."""


def require(condition, code):
    if not condition:
        raise InvalidExport(code)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def parse_json(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(InvalidExport('NONFINITE_JSON')))
    except InvalidExport:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise InvalidExport('INVALID_JSON') from None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, code):
    require(type(value) is int and 0 <= value <= 2**63 - 1, code)
    return value


def identifier(value):
    require(isinstance(value, str) and 0 < len(value) <= 64 and '\0' not in value,
            'INVALID_METADATA_IDENTIFIER')
    return value


def sha_string(value):
    require(isinstance(value, str) and SHA.fullmatch(value), 'INVALID_SHA256')
    return value


def java_quote(value):
    # Match the exporter's string writer, including its control-character form.
    escapes = {'"': '\\"', '\\': '\\\\', '\n': '\\n', '\r': '\\r', '\t': '\\t'}
    return '"' + ''.join(escapes.get(c, '\\u%04x' % ord(c) if ord(c) < 32 else c)
                         for c in value) + '"'


def encode_row(table, values):
    return ('[' + java_quote(table) + ',[' + ','.join('null' if x is None else java_quote(x)
            for x in values) + ']]\n').encode('utf-8')


@dataclass(frozen=True)
class Limits:
    compressed_bytes: int = 512 * 1024**2
    metadata_bytes: int = 32 * 1024**2
    uncompressed_bytes: int = 16 * 1024**3
    line_bytes: int = 9 * 1024**2
    row_value_bytes: int = 4 * 1024**2
    seconds: float = 1200


class Budget:
    def __init__(self, limits):
        self.limits = limits
        self.deadline = time.monotonic() + limits.seconds
        self.uncompressed = 0

    def check(self):
        require(time.monotonic() <= self.deadline, 'VERIFICATION_TIME_LIMIT')

    def add(self, count):
        self.check()
        self.uncompressed += count
        require(self.uncompressed <= self.limits.uncompressed_bytes, 'UNCOMPRESSED_SIZE_LIMIT')


def regular_file(path):
    require(path.exists(), 'EXPORT_FILE_MISSING')
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'NONREGULAR_EXPORT_FILE')
    return info


def file_sha(path, budget, expected_size):
    h = hashlib.sha256()
    read_bytes = 0
    with path.open('rb') as stream:
        while block := stream.read(1024**2):
            budget.check()
            read_bytes += len(block)
            require(read_bytes <= expected_size, 'EXPORT_CHANGED_DURING_VERIFICATION')
            h.update(block)
    require(read_bytes == expected_size, 'EXPORT_CHANGED_DURING_VERIFICATION')
    return h.hexdigest()


def metadata_bytes(path, limit, code):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, code)
    return raw


def source_state(value):
    require(isinstance(value, dict), 'SOURCE_STATE_MISSING')
    require(value.get('readOnly') == '1' and value.get('isolationLevel') == 'REPEATABLE-READ'
            and value.get('timeZone') == '+00:00', 'SOURCE_STATE_CLAIMS_INVALID')
    require(value.get('lowerCaseTableNames') in ('0', '1', '2'), 'SOURCE_CASE_MODE_MISSING')
    require(isinstance(value.get('version'), str) and value['version']
            and isinstance(value.get('sqlMode'), str), 'SOURCE_VERSION_OR_SQL_MODE_MISSING')
    require(all(isinstance(value.get(field), str) and value[field] for field in
                ('sourceTime', 'connectionCharset', 'connectionCollation')), 'SOURCE_CONTEXT_MISSING')


def catalog_tables(catalog):
    require(isinstance(catalog, dict) and catalog.get('format') == FORMAT, 'CATALOG_FORMAT_INVALID')
    source_state(catalog.get('sourceState'))
    databases = catalog.get('databases')
    require(isinstance(databases, list) and len(databases) == 2
            and all(isinstance(r, dict) for r in databases), 'SCHEMA_METADATA_INVALID')
    require(all(isinstance(r.get('Database'), str) for r in databases), 'SCHEMA_METADATA_INVALID')
    require({r.get('Database') for r in databases if isinstance(r, dict)} == set(SCHEMAS),
            'SCHEMA_METADATA_INVALID')
    require(all(isinstance(r.get('Create Database'), str) and r['Create Database'] for r in databases),
            'DATABASE_DEFINITION_MISSING')
    objects = catalog.get('tablesAndViews')
    require(isinstance(objects, list) and objects, 'TABLE_METADATA_MISSING')
    names = set()
    tables = {schema: [] for schema in SCHEMAS}
    types = Counter()
    generated = 0
    views = 0
    case_names = {}
    for obj in objects:
        require(isinstance(obj, dict), 'TABLE_METADATA_INVALID')
        schema, table = obj.get('TABLE_SCHEMA'), identifier(obj.get('TABLE_NAME'))
        require(schema in SCHEMAS and (schema, table) not in names, 'TABLE_SCOPE_OR_DUPLICATE')
        names.add((schema, table))
        case_names.setdefault((schema, table.casefold()), []).append(table)
        kind = obj.get('TABLE_TYPE')
        require(kind in ('BASE TABLE', 'VIEW'), 'TABLE_KIND_UNSUPPORTED')
        create = obj.get('create')
        definition_key = 'Create Table' if kind == 'BASE TABLE' else 'Create View'
        name_key = 'Table' if kind == 'BASE TABLE' else 'View'
        require(isinstance(create, dict) and isinstance(create.get(definition_key), str)
                and create[definition_key] and create.get(name_key) == table, 'OBJECT_DEFINITION_MISSING')
        columns = obj.get('columns')
        require(isinstance(columns, list) and columns, 'COLUMN_METADATA_MISSING')
        column_names = set()
        writable = []
        for ordinal, col in enumerate(columns, 1):
            require(isinstance(col, dict), 'COLUMN_METADATA_INVALID')
            name = identifier(col.get('COLUMN_NAME'))
            require(name.casefold() not in column_names and col.get('ORDINAL_POSITION') == str(ordinal),
                    'COLUMN_DUPLICATE_OR_ORDER_INVALID')
            column_names.add(name.casefold())
            require(isinstance(col.get('DATA_TYPE'), str) and col['DATA_TYPE']
                    and isinstance(col.get('COLUMN_TYPE'), str) and col['COLUMN_TYPE'], 'COLUMN_TYPE_MISSING')
            expression = col.get('GENERATION_EXPRESSION')
            require(expression is None or isinstance(expression, str), 'GENERATION_METADATA_INVALID')
            extra = col.get('EXTRA') or ''
            require(isinstance(extra, str), 'EXTRA_METADATA_INVALID')
            require(expression or not re.search(r'\b(?:VIRTUAL|STORED) GENERATED\b', extra),
                    'GENERATION_EXPRESSION_MISSING')
            if kind == 'BASE TABLE':
                types[col['DATA_TYPE'].lower()] += 1
                if expression:
                    generated += 1
                else:
                    writable.append(col)
        if kind == 'BASE TABLE':
            require(obj.get('ENGINE') == 'InnoDB', 'NONTRANSACTIONAL_TABLE')
            require(writable, 'NO_WRITABLE_COLUMNS')
            tables[schema].append((table, writable))
        else:
            views += 1
    require(all(any(obj['TABLE_SCHEMA'] == schema for obj in objects) for schema in SCHEMAS),
            'SCHEMA_OBJECTS_MISSING')
    auxiliary = {}
    for kind, definition_key in (('triggers', 'SQL Original Statement'), ('events', 'Create Event'),
                                 ('procedures', 'Create Procedure'), ('functions', 'Create Function')):
        entries = catalog.get(kind)
        require(isinstance(entries, list), 'AUXILIARY_METADATA_MISSING')
        seen = set()
        for item in entries:
            require(isinstance(item, dict), 'AUXILIARY_METADATA_INVALID')
            key = (item.get('dbName'), identifier(item.get('objectName')))
            require(key[0] in SCHEMAS and key not in seen, 'AUXILIARY_SCOPE_OR_DUPLICATE')
            require(isinstance(item.get('definition'), dict) and item['definition'],
                    'AUXILIARY_DEFINITION_MISSING')
            require(isinstance(item['definition'].get(definition_key), str) and item['definition'][definition_key],
                    'AUXILIARY_SQL_DEFINITION_MISSING')
            seen.add(key)
        auxiliary[kind] = len(entries)
    return tables, {'columnTypes': dict(sorted(types.items())), 'generatedColumnsExcluded': generated,
                    'views': views, 'auxiliarySQLObjects': auxiliary,
                    'caseCollisionsForInsensitiveTarget': [list(key) for key, value in case_names.items()
                                                         if len(value) > 1]}


def verify(directory, manifest_sha256, limits=None):
    limits = limits or Limits()
    budget = Budget(limits)
    root = Path(directory)
    require(root.is_dir() and not root.is_symlink()
            and not (getattr(root.lstat(), 'st_file_attributes', 0) & 0x400), 'EXPORT_DIRECTORY_INVALID')
    require(not (root / 'FAILED.json').exists(), 'FAILED_EXPORT')
    require({x.name for x in root.iterdir()} == set(PAYLOAD_FILES) | {'manifest.json'},
            'EXPORT_FILE_SET_INVALID')
    manifest_path = root / 'manifest.json'
    require(regular_file(manifest_path).st_size <= limits.metadata_bytes, 'MANIFEST_SIZE_LIMIT')
    raw_manifest = metadata_bytes(manifest_path, limits.metadata_bytes, 'MANIFEST_SIZE_LIMIT')
    require(digest(raw_manifest) == sha_string(manifest_sha256), 'MANIFEST_SHA_MISMATCH')
    manifest = parse_json(raw_manifest)
    require(isinstance(manifest, dict) and manifest.get('format') == FORMAT
            and manifest.get('completed') is True, 'MANIFEST_NOT_COMPLETE')
    require(manifest.get('schemas') == list(SCHEMAS), 'MANIFEST_SCHEMA_SCOPE_INVALID')
    for field, expected in (('readOnlySnapshotVerified', True), ('fullMetadataPrivilegesVerified', True),
            ('sourceBusinessDmlOrDdlExecuted', False), ('directPhysicalDatadirAccess', False),
            ('generatedColumnsExcludedFromRows', True)):
        require(manifest.get(field) is expected, 'MANIFEST_EXPORT_CLAIMS_INVALID')
    source_state(manifest.get('sourceState'))
    file_entries = manifest.get('files')
    require(isinstance(file_entries, list) and len(file_entries) == 3, 'MANIFEST_FILES_INVALID')
    require(all(isinstance(item, dict) and isinstance(item.get('name'), str) for item in file_entries),
            'MANIFEST_FILE_INVALID')
    require({item['name'] for item in file_entries} == set(PAYLOAD_FILES), 'MANIFEST_FILE_SCOPE_OR_DUPLICATE')
    named = {}
    compressed_total = 0
    signatures = {}
    for item in file_entries:
        require(isinstance(item, dict), 'MANIFEST_FILE_INVALID')
        name = item.get('name')
        require(name in PAYLOAD_FILES and name not in named, 'MANIFEST_FILE_SCOPE_OR_DUPLICATE')
        path = root / name
        info = regular_file(path)
        require(integer(item.get('bytes'), 'FILE_BYTE_COUNT_INVALID') == info.st_size, 'FILE_SIZE_MISMATCH')
        compressed_total += info.st_size
        require(compressed_total + len(raw_manifest) <= limits.compressed_bytes, 'COMPRESSED_SIZE_LIMIT')
        require(file_sha(path, budget, info.st_size) == sha_string(item.get('sha256')), 'FILE_SHA_MISMATCH')
        named[name] = item
        signatures[name] = (info.st_size, info.st_mtime_ns, info.st_ino)
    catalog_path = root / 'catalog.json'
    require(catalog_path.stat().st_size <= limits.metadata_bytes, 'CATALOG_SIZE_LIMIT')
    raw_catalog = metadata_bytes(catalog_path, limits.metadata_bytes, 'CATALOG_SIZE_LIMIT')
    require(digest(raw_catalog) == named['catalog.json']['sha256'], 'CATALOG_CHANGED_DURING_VERIFICATION')
    catalog = parse_json(raw_catalog)
    tables, metadata = catalog_tables(catalog)
    require(manifest['sourceState'] == catalog['sourceState'], 'SOURCE_STATE_MISMATCH')
    expected_counts = manifest.get('tableCounts')
    require(isinstance(expected_counts, list), 'TABLE_COUNTS_MISSING')
    expected_order = [(schema, name) for schema in SCHEMAS for name, _ in tables[schema]]
    require(len(expected_counts) == len(expected_order), 'TABLE_COUNT_COVERAGE_INVALID')
    counts = {}
    for entry, key in zip(expected_counts, expected_order):
        require(isinstance(entry, dict) and (entry.get('schema'), entry.get('table')) == key,
                'TABLE_COUNT_ORDER_OR_SCOPE_INVALID')
        counts[key] = (integer(entry.get('rows'), 'TABLE_ROW_COUNT_INVALID'),
                       sha_string(entry.get('rowStreamSHA256')))
    table_reports = []
    nulls = empty_values = 0
    total_rows = 0
    try:
        for schema in SCHEMAS:
            ordered = tables[schema]
            positions = {name: index for index, (name, _) in enumerate(ordered)}
            observed = {name: [0, hashlib.sha256()] for name, _ in ordered}
            last_position = -1
            with gzip.open(root / (schema + '.rows.jsonl.gz'), 'rb') as stream:
                while raw := stream.readline(limits.line_bytes + 1):
                    budget.add(len(raw))
                    require(len(raw) <= limits.line_bytes, 'ROW_LINE_SIZE_LIMIT')
                    require(raw.endswith(b'\n'), 'ROW_LINE_TRUNCATED')
                    row = parse_json(raw)
                    require(isinstance(row, list) and len(row) == 2 and isinstance(row[0], str)
                            and isinstance(row[1], list), 'ROW_SHAPE_INVALID')
                    name, values = row
                    require(name in positions, 'ROW_TABLE_UNKNOWN')
                    position = positions[name]
                    require(position >= last_position, 'ROW_TABLE_ORDER_INVALID')
                    last_position = position
                    require(len(values) == len(ordered[position][1]), 'ROW_COLUMN_COUNT_MISMATCH')
                    value_bytes = 0
                    for value in values:
                        if value is None:
                            nulls += 1
                        else:
                            require(isinstance(value, str) and len(value) % 2 == 0 and HEX.fullmatch(value),
                                    'ROW_HEX_INVALID')
                            value_bytes += len(value) // 2
                            empty_values += value == ''
                    require(value_bytes <= limits.row_value_bytes, 'ROW_VALUE_SIZE_LIMIT')
                    require(encode_row(name, values) == raw, 'ROW_ENCODING_NONCANONICAL')
                    observed[name][0] += 1
                    observed[name][1].update(raw)
            for name, columns in ordered:
                count, h = observed[name]
                expected_count, expected_sha = counts[(schema, name)]
                require(count == expected_count, 'TABLE_ROW_COUNT_MISMATCH')
                require(h.hexdigest() == expected_sha, 'TABLE_ROW_STREAM_SHA_MISMATCH')
                total_rows += count
                table_reports.append({'schema': schema, 'table': name, 'rows': count,
                                      'writableColumns': len(columns), 'rowStreamSHA256': h.hexdigest()})
    except (gzip.BadGzipFile, EOFError, OSError):
        raise InvalidExport('GZIP_STREAM_INVALID') from None
    for name, before in signatures.items():
        after = regular_file(root / name)
        require((after.st_size, after.st_mtime_ns, after.st_ino) == before, 'EXPORT_CHANGED_DURING_VERIFICATION')
    require(metadata_bytes(manifest_path, limits.metadata_bytes, 'MANIFEST_SIZE_LIMIT') == raw_manifest,
            'MANIFEST_CHANGED_DURING_VERIFICATION')
    budget.check()
    return {'format': FORMAT, 'manifestSHA256': manifest_sha256, 'artifactIntegrityVerified': True,
            'fileBytesVerified': compressed_total + len(raw_manifest), 'uncompressedRowBytesVerified': budget.uncompressed,
            'schemas': list(SCHEMAS), 'tables': len(table_reports), 'rows': total_rows, 'tableCounts': table_reports,
            'sqlNullValues': nulls, 'nonNullEmptyValues': empty_values, **metadata,
            'exporterSourceStateClaimsConsistent': True, 'sourceVersion': manifest['sourceState']['version'],
            'sourceLowerCaseTableNames': manifest['sourceState']['lowerCaseTableNames'],
            'databaseConnections': 0, 'SQLExecuted': False, 'sourceFilesChanged': False,
            'sourceAuthenticityIndependentlyProven': False, 'primaryKeyUniquenessVerified': False,
            'foreignKeyIntegrityVerified': False, 'fieldTypeRestorationVerified': False,
            'auxiliaryMetadataStableDuringSnapshotVerified': False,
            'restoreVerified': False, 'applicationParityVerified': False,
            'publicOrGitDataUpload': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--export-directory', type=Path, required=True)
    ap.add_argument('--manifest-sha256', required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        root, report_path = args.export_directory.absolute(), args.report.resolve()
        require(not report_path.is_relative_to(root.resolve()), 'REPORT_MUST_BE_OUTSIDE_EXPORT')
        require(not report_path.exists(), 'REPORT_ALREADY_EXISTS')
        report = verify(root, args.manifest_sha256)
        with report_path.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({key: report[key] for key in ('artifactIntegrityVerified', 'tables', 'rows',
              'databaseConnections', 'restoreVerified', 'applicationParityVerified')}))
    except InvalidExport as error:
        print(json.dumps({'artifactIntegrityVerified': False, 'errorCode': str(error)}), file=sys.stderr)
        return 2
    except (OSError, UnicodeError, TypeError, KeyError, ValueError):
        print(json.dumps({'artifactIntegrityVerified': False, 'errorCode': 'INVALID_EXPORT_OR_REPORT_IO'}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
