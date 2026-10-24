"""Compare two sealed original exports without connecting to either database.

Rows are compared as multisets of their exact canonical bytes, including duplicate
counts. Catalog definitions are data, never SQL to execute. The temporary SQLite
spool contains private export data and must stay outside public/Git directories.
"""
from pathlib import Path
from dataclasses import dataclass
from tempfile import TemporaryDirectory
import argparse
import gzip
import hashlib
import json
import shutil
import sqlite3
import sys
import time

import verify_original_database_export as export


class InvalidComparison(ValueError):
    """Fixed error codes only: never interpolate private source values."""


def require(condition, code):
    if not condition:
        raise InvalidComparison(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


@dataclass(frozen=True)
class Limits:
    spool_bytes: int = 256 * 1024**2
    minimum_free_after_spool: int = 256 * 1024**2
    seconds: float = 1200


def metadata_entries(catalog):
    """Ignore only object enumeration order, not column order or DDL content."""
    entries = {}
    for item in catalog['databases']:
        entries[('database', item['Database'], '')] = canonical(item)
    for item in catalog['tablesAndViews']:
        entries[('tableOrView', item['TABLE_SCHEMA'], item['TABLE_NAME'])] = canonical(item)
    for kind in ('triggers', 'events', 'procedures', 'functions'):
        for item in catalog[kind]:
            entries[(kind, item['dbName'], item['objectName'])] = canonical(item)
    return entries


def context_entries(catalog):
    # Source wall-clock time changes by definition between original and restored
    # exports. Preserve the remaining context; do not silently normalize modes.
    return {k: v for k, v in catalog['sourceState'].items() if k != 'sourceTime'}


def input_stamp(root):
    return {name: (export.regular_file(root / name).st_size,
                   (root / name).stat().st_mtime_ns,
                   (root / name).stat().st_ino)
            for name in (*export.PAYLOAD_FILES, 'manifest.json')}


def recheck(root, manifest_sha, stamp, deadline):
    require(input_stamp(root) == stamp, 'INPUT_CHANGED_DURING_COMPARISON')
    raw = export.metadata_bytes(root / 'manifest.json', 32 * 1024**2, 'MANIFEST_SIZE_LIMIT')
    require(export.digest(raw) == manifest_sha, 'INPUT_CHANGED_DURING_COMPARISON')
    manifest = export.parse_json(raw)
    for item in manifest['files']:
        require(time.monotonic() <= deadline, 'COMPARISON_TIME_LIMIT')
        budget = export.Budget(export.Limits(seconds=max(0.001, deadline - time.monotonic())))
        require(export.file_sha(root / item['name'], budget, item['bytes']) == item['sha256'],
                'INPUT_CHANGED_DURING_COMPARISON')
    require(input_stamp(root) == stamp, 'INPUT_CHANGED_DURING_COMPARISON')


def compare(source_directory, source_manifest_sha256, target_directory,
            target_manifest_sha256, scratch_parent, limits=None, export_limits=None):
    limits = limits or Limits()
    export_limits = export_limits or export.Limits()
    require(type(limits.spool_bytes) is int and 1024**2 <= limits.spool_bytes <= 4 * 1024**3,
            'SPOOL_BUDGET_INVALID')
    require(type(limits.minimum_free_after_spool) is int and limits.minimum_free_after_spool >= 0
            and 0 < limits.seconds <= 7200, 'COMPARISON_LIMITS_INVALID')
    deadline = time.monotonic() + limits.seconds
    source_arg, target_arg, scratch_arg = map(Path, (source_directory, target_directory, scratch_parent))
    # Verify the supplied roots before resolving them; resolving first would hide
    # a root symlink/reparse point from the existing artifact verifier.
    for root in (source_arg, target_arg):
        require(root.is_dir() and not root.is_symlink()
                and not (getattr(root.lstat(), 'st_file_attributes', 0) & 0x400), 'INPUT_ROOT_INVALID')
    source, target = source_arg.resolve(), target_arg.resolve()
    require(source != target and not source.is_relative_to(target) and not target.is_relative_to(source),
            'INPUT_DIRECTORIES_MUST_BE_DISTINCT')
    require(scratch_arg.is_dir() and not scratch_arg.is_symlink()
            and not (getattr(scratch_arg.lstat(), 'st_file_attributes', 0) & 0x400), 'SCRATCH_ROOT_INVALID')
    scratch = scratch_arg.resolve()
    require(not scratch.is_relative_to(source) and not scratch.is_relative_to(target)
            and not source.is_relative_to(scratch) and not target.is_relative_to(scratch),
            'SCRATCH_MUST_BE_SEPARATE')
    # One SQLite file, no rollback journal/WAL, and no external sort files. For
    # requests above 1 GiB this also enforces an explicit peak/free-space budget.
    free_before = shutil.disk_usage(scratch).free
    require(free_before >= limits.spool_bytes + limits.minimum_free_after_spool,
            'INSUFFICIENT_SCRATCH_SPACE')
    stamps = [input_stamp(root) for root in (source, target)]
    reports = []
    for root, pinned in ((source_arg, source_manifest_sha256), (target_arg, target_manifest_sha256)):
        require(time.monotonic() <= deadline, 'COMPARISON_TIME_LIMIT')
        remaining = min(export_limits.seconds, max(0.001, deadline - time.monotonic()))
        bounded = export.Limits(**{**export_limits.__dict__, 'seconds': remaining})
        reports.append(export.verify(root, pinned, bounded))
    catalogs = [export.parse_json(export.metadata_bytes(root / 'catalog.json', export_limits.metadata_bytes,
                                                       'CATALOG_SIZE_LIMIT')) for root in (source, target)]
    entries = [metadata_entries(c) for c in catalogs]
    metadata_differences = []
    for key in sorted(entries[0].keys() | entries[1].keys()):
        left, right = entries[0].get(key), entries[1].get(key)
        if left != right:
            metadata_differences.append({
                'kind': key[0], 'objectKeySHA256': export.digest(canonical(key)),
                'sourceSHA256': export.digest(left) if left is not None else None,
                'targetSHA256': export.digest(right) if right is not None else None})
    contexts = [context_entries(c) for c in catalogs]
    context_differences = sorted(k for k in contexts[0].keys() | contexts[1].keys()
                                 if contexts[0].get(k) != contexts[1].get(k))
    counters = {}
    for side, report in enumerate(reports):
        for item in report['tableCounts']:
            key = (item['schema'], item['table'])
            counters.setdefault(key, [0, 0])[side] = item['rows']
    differences = {}
    peak_spool = 0
    with TemporaryDirectory(prefix='original-export-comparison-', dir=scratch) as tmp:
        spool_path = Path(tmp) / 'private-rows.sqlite'
        db = None
        try:
            db = sqlite3.connect(spool_path)
            db.execute('PRAGMA page_size=4096')
            db.execute('PRAGMA journal_mode=OFF')
            db.execute('PRAGMA synchronous=OFF')
            db.execute('PRAGMA temp_store=MEMORY')
            db.execute('PRAGMA cache_size=-2048')
            db.execute('PRAGMA max_page_count=' + str(limits.spool_bytes // 4096))
            db.execute('CREATE TABLE rows(schema_index INTEGER NOT NULL, table_name TEXT NOT NULL, '
                       'canonical_row BLOB NOT NULL, balance INTEGER NOT NULL, '
                       'PRIMARY KEY(schema_index,table_name,canonical_row)) WITHOUT ROWID')
            db.execute('BEGIN')
            seen_rows = [0, 0]
            for side, root in enumerate((source, target)):
                direction = 1 if side == 0 else -1
                for schema_index, schema in enumerate(export.SCHEMAS):
                    with gzip.open(root / (schema + '.rows.jsonl.gz'), 'rb') as stream:
                        while raw := stream.readline(export_limits.line_bytes + 1):
                            require(time.monotonic() <= deadline, 'COMPARISON_TIME_LIMIT')
                            require(len(raw) <= export_limits.line_bytes and raw.endswith(b'\n'),
                                    'INPUT_CHANGED_DURING_COMPARISON')
                            row = export.parse_json(raw)
                            require(isinstance(row, list) and len(row) == 2 and isinstance(row[0], str)
                                    and isinstance(row[1], list) and export.encode_row(*row) == raw,
                                    'INPUT_CHANGED_DURING_COMPARISON')
                            db.execute('INSERT INTO rows VALUES(?,?,?,?) ON CONFLICT '
                                       '(schema_index,table_name,canonical_row) DO UPDATE '
                                       'SET balance=balance+excluded.balance',
                                       (schema_index, row[0], raw, direction))
                            seen_rows[side] += 1
            require(seen_rows == [r['rows'] for r in reports], 'INPUT_CHANGED_DURING_COMPARISON')
            # No ORDER BY/GROUP BY temporary copies of sensitive values. The
            # primary-key traversal is streamed, and aggregation is in Python.
            for schema_index, name, balance in db.execute(
                    'SELECT schema_index,table_name,balance FROM rows WHERE balance<>0'):
                require(time.monotonic() <= deadline, 'COMPARISON_TIME_LIMIT')
                key = (export.SCHEMAS[schema_index], name)
                counts = differences.setdefault(key, [0, 0, 0])
                counts[0] += max(balance, 0)
                counts[1] += max(-balance, 0)
                counts[2] += 1
            db.commit()
            peak_spool = spool_path.stat().st_size
            require(peak_spool <= limits.spool_bytes, 'SPOOL_SIZE_LIMIT')
            for root, pinned, stamp in zip((source, target),
                    (source_manifest_sha256, target_manifest_sha256), stamps):
                recheck(root, pinned, stamp, deadline)
        except sqlite3.Error as error:
            code = getattr(error, 'sqlite_errorcode', None)
            if code == sqlite3.SQLITE_FULL:
                raise InvalidComparison('SPOOL_SIZE_LIMIT') from None
            raise InvalidComparison('PRIVATE_SPOOL_IO_FAILED') from None
        finally:
            if db is not None:
                db.close()
    table_results = []
    for key in sorted(counters.keys() | differences.keys()):
        count = counters.get(key, [0, 0])
        delta = differences.get(key, [0, 0, 0])
        table_results.append({'schema': key[0], 'tableKeySHA256': export.digest(canonical(key)),
                              'sourceRows': count[0], 'targetRows': count[1],
                              'missingRowOccurrences': delta[0], 'additionalRowOccurrences': delta[1],
                              'differentDistinctRowValues': delta[2], 'rowMultisetEqual': not any(delta)})
    row_equal = not differences
    metadata_equal = not metadata_differences
    context_equal = not context_differences
    format_equal = reports[0]['format'] == reports[1]['format']
    return {'comparisonFormat': 'tj-original-export-multiset-comparison-v1',
            'sourceManifestSHA256': source_manifest_sha256,
            'targetManifestSHA256': target_manifest_sha256,
            'sourceArtifactIntegrityVerified': True, 'targetArtifactIntegrityVerified': True,
            'rowComparison': 'Exact canonical bytes and duplicate multiplicities; source row order ignored',
            'rowMultisetsEqual': row_equal, 'metadataExactlyEqual': metadata_equal,
            'sourceContextEqualExceptCaptureTime': context_equal,
            'metadataDifferences': metadata_differences, 'sourceContextDifferenceKeys': context_differences,
            'tableComparisons': table_results,
            'exportFormatEqual': format_equal,
            'sourceExportFormat': reports[0]['format'], 'targetExportFormat': reports[1]['format'],
            'legacyFloatEncodingRisk': any(r['legacyFloatEncodingRisk'] for r in reports),
            'exportedContentEqual': row_equal and metadata_equal and context_equal and format_equal,
            'spoolBudgetBytes': limits.spool_bytes, 'observedSpoolBytesBeforeClose': peak_spool,
            'diskFreeBefore': free_before, 'minimumFreeAfterSpoolBudget': limits.minimum_free_after_spool,
            'temporarySpoolRemoved': True, 'sourceFilesChanged': False,
            'originalDatabaseConnections': 0, 'sourceSQLExecuted': False,
            'sourceAuthenticityIndependentlyVerified': False, 'restoreExecutionVerified': False,
            'fieldTypeRestorationVerified': False, 'generatedColumnValuesCompared': False,
            'originalBusinessBehaviorVerified': False, 'fullCloneReady': False,
            'publicOrGitDataUpload': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for side in ('source', 'target'):
        parser.add_argument('--' + side + '-directory', type=Path, required=True)
        parser.add_argument('--' + side + '-manifest-sha256', required=True)
    parser.add_argument('--scratch-parent', type=Path, required=True)
    parser.add_argument('--spool-limit-mib', type=int, default=256)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        report_path = args.report.absolute()
        require(not report_path.exists(), 'REPORT_ALREADY_EXISTS')
        for root in (args.source_directory.resolve(), args.target_directory.resolve(),
                     args.scratch_parent.resolve()):
            require(not report_path.resolve().is_relative_to(root), 'REPORT_MUST_BE_SEPARATE')
        report = compare(args.source_directory, args.source_manifest_sha256,
                         args.target_directory, args.target_manifest_sha256, args.scratch_parent,
                         Limits(spool_bytes=args.spool_limit_mib * 1024**2))
        with report_path.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({key: report[key] for key in ('rowMultisetsEqual', 'metadataExactlyEqual',
            'sourceContextEqualExceptCaptureTime', 'exportedContentEqual', 'restoreExecutionVerified')}))
        return 0 if report['exportedContentEqual'] else 1
    except (InvalidComparison, export.InvalidExport) as error:
        print(json.dumps({'comparisonCompleted': False, 'errorCode': str(error)}), file=sys.stderr)
        return 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, gzip.BadGzipFile, EOFError):
        print(json.dumps({'comparisonCompleted': False, 'errorCode': 'INVALID_COMPARISON_INPUT_OR_IO'}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
