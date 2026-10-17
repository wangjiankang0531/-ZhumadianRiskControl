"""Two-stage real-source parent cache recovery check; keeps the evicted bundle as backup.

Use only after the viewer has retired Tile140/depth3's CPU parent page. Run
`evict`, advance the browser near view to trigger a real restoration, then run
`verify`. This never deletes cache files or modifies original GIS/DLG data.
"""
from contextlib import ExitStack
from pathlib import Path
import argparse
import hashlib
import json
import re
import time

import native_cache_policy as policy

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / 'Assets/Cache/zhumadian_native_chunk_cache'
BACKUP = ROOT.parent / 'Backup/lod_parent_rebuild_20261016'
RECORD = BACKUP / 'recovery_record.json'
NAME = 'tile_140_depth_3'
IDENTITY = ('schema', 'tile_id', 'depth', 'replacement_parent', 'family_key',
            'texture_policy', 'source_nodes', 'parts', 'stamp', 'gpu_payload_bytes', 'indices')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same_identity(left, right):
    return {key: left.get(key) for key in IDENTITY} == {key: right.get(key) for key in IDENTITY}


def verify_payload(folder, marker):
    for part in marker['parts']:
        assert re.fullmatch(r'part_\d{3}', part['directory'])
        for item in part['files']:
            assert item['name'] in {'geometry.gltf', 'geometry.bin', 'atlas.jpg'}
            path = folder / part['directory'] / item['name']
            assert path.resolve().is_relative_to(folder.resolve()) and not policy.linked(path)
            assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256']


def source_snapshot(marker):
    master = json.loads((ROOT / 'data/showcase/zhumadian_native_hierarchy.json').read_text(encoding='utf-8'))
    row = next(row for row in master['root_records'] if row['tile_id'] == 140)
    catalog_path = ROOT / row['catalog']
    assert digest(catalog_path) == marker['stamp']['catalog_sha256'] == row['sha256']
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    directory = (ROOT / catalog['source_directory']).resolve()
    assert directory.is_relative_to((ROOT / 'assets/驻马店园区').resolve())
    records = []
    for item in marker['stamp']['frontier']:
        path = directory / item['name']
        assert path.parent == directory and path.name == item['name']
        actual = digest(path)
        assert actual == item['sha256']
        records.append({'name': item['name'], 'sha256': actual, 'bytes': path.stat().st_size})
    return {'catalogSha256': digest(catalog_path), 'sources': records,
            'userDLGSha256': digest(ROOT / 'projects/驻马店图层.json')}


def paths():
    assert CACHE.resolve() == ROOT.parent.resolve() / 'Assets/Cache/zhumadian_native_chunk_cache'
    assert (ROOT / 'work/zhumadian_native_chunk_cache').resolve() == CACHE.resolve()
    backup_root = ROOT.parent.resolve() / 'Backup'
    assert backup_root.resolve() == backup_root and not policy.linked(backup_root)
    assert BACKUP.resolve().parent == backup_root
    assert not policy.linked(CACHE) and not policy.linked(BACKUP)
    folder, saved = CACHE / NAME, BACKUP / NAME
    assert folder.resolve().parent == CACHE.resolve() and saved.resolve().parent == BACKUP.resolve()
    assert not policy.linked(folder) and not policy.linked(saved)
    return folder, saved


def evict():
    folder, saved = paths()
    assert not BACKUP.exists(), 'Use the existing recovery journal; never overwrite a previous backup'
    with ExitStack() as stack:
        # Same lock order as maintenance. An active native/web reader prevents the move.
        stack.enter_context(policy.FileLock(CACHE / '.locks/prune.lock', True, 0))
        stack.enter_context(policy.tile_lock(CACHE, 140, True, 0))
        marker = json.loads((folder / 'complete.json').read_text(encoding='utf-8'))
        verify_payload(folder, marker)
        record = {'schema': 'xnby.parent_cache_recovery.v1', 'state': 'prepared',
                  'tile': 140, 'depth': 3, 'cache': str(folder), 'backup': str(saved),
                  'marker': marker, 'before': source_snapshot(marker)}
        BACKUP.mkdir()
        RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        policy.mark_dirty(CACHE)
        # Both absolute paths were checked above; same-volume rename preserves all files.
        folder.rename(saved)
        assert not folder.exists() and (saved / 'complete.json').is_file()
        record.update(state='evicted', evictedAt=time.time())
        RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'state': 'evicted', 'cacheAbsent': True, 'backupPreserved': str(saved),
            'originalSourcesUnchanged': True}


def verify():
    folder, saved = paths()
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    assert record['state'] in {'evicted', 'verified'}
    with policy.bundle_lock(CACHE, NAME, timeout=0):
        rebuilt = json.loads((folder / 'complete.json').read_text(encoding='utf-8'))
        assert same_identity(record['marker'], rebuilt), 'Rebuilt source page identity changed'
        verify_payload(folder, rebuilt)
        assert source_snapshot(rebuilt) == record['before'], 'Source GIS or user DLG changed'
        verify_payload(saved, record['marker'])
        record.update(state='verified', verifiedAt=time.time(), sourceIdentityMatch=True,
                      rebuiltFilesSha256Match=True, originalSourcesUnchanged=True,
                      backupStillIntact=True)
        RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return {key: record[key] for key in ('state', 'sourceIdentityMatch', 'rebuiltFilesSha256Match',
                                       'originalSourcesUnchanged', 'backupStillIntact')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('evict', 'verify'))
    parser.add_argument('--run-id', default='20261016', help='Unique backup journal suffix; use the same value for both stages')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', args.run_id):
        parser.error('run-id must contain 1-40 letters, digits, underscores or hyphens')
    BACKUP = ROOT.parent / 'Backup' / ('lod_parent_rebuild_' + args.run_id)
    RECORD = BACKUP / 'recovery_record.json'
    print(json.dumps(evict() if args.stage == 'evict' else verify(), ensure_ascii=False))
