"""Write a private, read-only ownership observation. Never installs or reloads."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.layer_sync_server_owner import inspect, loads, plain, read, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--preflight-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = plain(args.output)
    if output.exists():
        raise ValueError('PRIOR_OWNER_REPORT_RETAINED')
    if not re.fullmatch('[0-9a-f]{64}', args.preflight_sha256):
        raise ValueError('EXACT_PREFLIGHT_PIN_REQUIRED')
    try:
        raw = read(args.preflight, 65536)
        if sha(raw) != args.preflight_sha256:
            raise ValueError('PREFLIGHT_REPORT_CHANGED')
        report = inspect(args.application, loads(raw.decode('utf-8-sig')))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        # No arbitrary exception text, process command line, auth/config contents.
        report = {'schema': 'xnby.layer-sync.server-owner-observation.v1', 'passed': False,
                  'reason': 'OWNER_OR_PINNED_SNAPSHOT_NOT_VERIFIED',
                  'configurationServiceDatabaseAndLayerWrites': 0, 'credentialsReadOrRecorded': False,
                  'deploymentPerformed': False, 'reloadAuthorizedByObservation': False}
    report['recordedAt'] = datetime.datetime.now().astimezone().isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print('OWNER_CHECK_PASSED' if report['passed'] else 'OWNER_CHECK_NOT_READY')
    print('Report: ' + str(output))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
