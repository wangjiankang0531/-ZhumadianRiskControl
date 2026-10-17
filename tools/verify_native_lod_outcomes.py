"""Reconcile each native rejection event with counters; retain real errors separately."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

PREFIX = '[native_lod_outcome] '
FAILURES = {'root_conversion_budget', 'root_decode_error', 'root_runtime_budget',
            'root_gpu_error', 'family_conversion_budget', 'family_decode_error',
            'family_gpu_or_transaction_error'}
RUNTIME_BUDGET = {'root_runtime_budget', 'family_runtime_budget'}
ERRORS = {'root_decode_error', 'root_gpu_error', 'family_decode_error',
          'family_gpu_or_transaction_error', 'family_transaction_rejection'}
CATEGORIES = FAILURES | RUNTIME_BUDGET | ERRORS


def reconcile(data, lines):
    assert data['passed'] and data['stations']
    events = [json.loads(line[len(PREFIX):]) for line in lines if line.startswith(PREFIX)]
    for event in events:
        assert event['category'] in CATEGORIES
        assert type(event['tile']) is int and 1 <= event['tile'] <= 2346
        assert type(event['depth']) is int and 1 <= event['depth'] <= 12
        assert isinstance(event['reason'], str) and event['reason']
        if event['category'].startswith('family_'):
            assert re.fullmatch(rf'Tile_{event["tile"]}_L[0-9]+_0[0-9u]+\.osgb', event['parent'])
        else:
            assert event['parent'] == ''
    counts = Counter(e['category'] for e in events)
    previous = Counter()
    for station in data['stations']:
        current = station['outcome_counts']
        assert set(current) <= CATEGORIES
        assert all(type(v) is int and v > 0 for v in current.values())
        current = Counter(current)
        assert all(current[key] >= previous[key] for key in previous)
        assert sum(current[k] for k in FAILURES) == station['failures']
        assert sum(current[k] for k in RUNTIME_BUDGET) == station['budget_fallbacks']
        previous = current
    assert counts == previous, 'Missing, duplicate, or unaccounted rejection event'
    errors = [e for e in events if e['category'] in ERRORS]
    return {'events': len(events), 'counts': dict(counts), 'failures': sum(counts[k] for k in FAILURES),
            'runtimeBudgetFallbacks': sum(counts[k] for k in RUNTIME_BUDGET),
            'errors': errors, 'errorCount': len(errors),
            'scope': 'all classified events in this run; original aggregate counters keep their existing semantics'}


def visible_route(data):
    return [{key: station[key] for key in ('cycle', 'stage', 'camera', 'viewport', 'resident',
              'local_families', 'drawn_base_indices', 'drawn_child_indices', 'removed_parent_indices')}
            for station in data['stations']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stats', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Do not overwrite earlier evidence'
    data = json.loads(args.stats.read_text('utf-8'))
    result = reconcile(data, args.log.read_text('utf-8').splitlines())
    if args.baseline:
        baseline = json.loads(args.baseline.read_text('utf-8'))
        a, b = visible_route(data), visible_route(baseline)
        assert len(a) == len(b)
        result['sameVisibleRouteAsBaseline'] = a == b
        result['differentStations'] = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    result['passed'] = result['errorCount'] == 0
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    assert result['passed'], 'Actual native errors remain; inspect the complete event report'


if __name__ == '__main__':
    main()