"""Bounded read-only reachability check before expensive candidate validation.

The child reads at most 64 bytes from each explicitly named file. This does not
replace later SHA verification, keep a share online, or prove app readiness.
"""
from pathlib import Path
import json
import os
import re
import stat
import subprocess
import sys


class SourcePreflightError(RuntimeError):
    def __init__(self, report):
        self.report = report
        super().__init__('CANDIDATE_SOURCE_PREFLIGHT_FAILED:' + report['reason'])


def checked_files(files):
    if not isinstance(files, list) or not 1 <= len(files) <= 8:
        raise ValueError('EXPLICIT_BOUNDED_SOURCE_FILE_LIST_REQUIRED')
    labels = set()
    for item in files:
        if (not isinstance(item, dict) or set(item) != {'label', 'path'} or
                not isinstance(item['label'], str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', item['label']) or
                item['label'] in labels or not isinstance(item['path'], str) or
                not Path(item['path']).is_absolute() or len(item['path']) > 2048 or
                any(ord(c) < 32 for c in item['path'])):
            raise ValueError('EXPLICIT_UNIQUE_SOURCE_LABEL_AND_ABSOLUTE_FILE_REQUIRED')
        labels.add(item['label'])
    return files


def _probe(files):
    rows = []
    for item in checked_files(files):
        reason = 'not-readable'
        try:
            with Path(item['path']).open('rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
                    reason = 'not-nonempty-regular-file'
                else:
                    head = stream.read(64)
                    after = os.fstat(stream.fileno())
                    reason = ('readable' if head and before.st_size == after.st_size and
                              before.st_mtime_ns == after.st_mtime_ns else 'changed-during-read')
        except OSError:
            pass
        rows.append({'label': item['label'], 'readable': reason == 'readable', 'reason': reason})
    return rows


def require_source_files(files, timeout=8):
    files = checked_files(files)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not .1 <= timeout <= 30:
        raise ValueError('BOUNDED_SOURCE_PROBE_TIMEOUT_REQUIRED')
    report = {'passed': False, 'reason': 'worker-failed', 'timeoutSeconds': timeout,
              'labels': [item['label'] for item in files], 'files': [],
              'scope': 'bounded file-head reachability; full content verification follows'}
    command = [sys.executable, '-B', str(Path(__file__).absolute()), '--probe', json.dumps(files)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=timeout,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for only this owned probe child.
        report['reason'] = 'read-timeout'
        raise SourcePreflightError(report) from None
    except OSError:
        raise SourcePreflightError(report) from None
    try:
        if run.returncode != 0 or len(run.stdout) > 8192:
            raise ValueError('BOUNDED_WORKER_RESULT_REQUIRED')
        rows = json.loads(run.stdout)
        if not isinstance(rows, list) or len(rows) != len(files):
            raise ValueError('EXACT_WORKER_RESULT_REQUIRED')
        for item, row in zip(files, rows):
            if (not isinstance(row, dict) or set(row) != {'label', 'readable', 'reason'} or
                    row['label'] != item['label'] or type(row['readable']) is not bool or
                    row['reason'] not in {'readable', 'not-readable', 'not-nonempty-regular-file', 'changed-during-read'} or
                    row['readable'] != (row['reason'] == 'readable')):
                raise ValueError('MATCHING_WORKER_RESULT_REQUIRED')
        report['files'] = rows
        report['passed'] = all(row['readable'] for row in rows)
        report['reason'] = 'readable' if report['passed'] else 'source-unavailable'
    except (ValueError, TypeError, UnicodeError):
        report['reason'] = 'invalid-worker-result'
    if not report['passed']:
        raise SourcePreflightError(report)
    return report


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--probe' or len(sys.argv[2]) > 32768:
        raise SystemExit('EXPLICIT_SOURCE_PROBE_ARGUMENTS_REQUIRED')
    print(json.dumps(_probe(json.loads(sys.argv[2]))))
