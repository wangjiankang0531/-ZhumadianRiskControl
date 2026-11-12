"""Read-only OSGB deployment integrity audit, independent of drive letter and editor startup."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import ExitStack, contextmanager
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import msvcrt
import os
import re
import sys
import threading
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client_workspace import parse_document, read_configuration

NATIVE_HIERARCHY_SHA256 = '8f5d57991dc8af440995cafd3c1d764ed37ea4b19090513ad489f19db8762185'
MAX_JSON = 16 * 1024 * 1024
REPARSE = 0x400
DEFAULT_PATHS = {'gis': 'Assets/3DGIS/驻马店园区', 'renderData': 'Assets/Runtime',
                 'icons': 'Assets/Icons/PointSymbols', 'downloads': 'UserData/Cache/Downloads',
                 'dlgDrafts': 'UserData/Drafts/DLG', 'sceneDrafts': 'UserData/Drafts/Scenes'}


def document_for(root):
    return {'schema': 'xnby.client-workspace.v1', 'workspaceRoot': str(root), 'paths': dict(DEFAULT_PATHS)}


def unique_pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def canonical_name(value):
    if (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_+.-]+\.osgb', value)
            or value in ('.', '..') or value.endswith(('.', ' '))):
        raise ValueError('UNSAFE_OSGB_FILENAME')
    return value


def extended(path):
    text = str(Path(path).absolute())
    return text if text.startswith('\\\\?\\') else '\\\\?\\' + text


class _ByHandle(ctypes.Structure):
    _fields_ = [('attributes', wintypes.DWORD), ('creation', wintypes.FILETIME),
                ('access', wintypes.FILETIME), ('write', wintypes.FILETIME),
                ('volume', wintypes.DWORD), ('sizeHigh', wintypes.DWORD),
                ('sizeLow', wintypes.DWORD), ('links', wintypes.DWORD),
                ('indexHigh', wintypes.DWORD), ('indexLow', wintypes.DWORD)]


class WindowsReadOnly:
    """Normal read handles, no share-write/delete and no reparse following."""
    def __init__(self):
        if os.name != 'nt':
            raise RuntimeError('WINDOWS_LOCAL_WORKSPACE_REQUIRED')
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        self.api.CreateFileW.restype = wintypes.HANDLE
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.invalid = ctypes.c_void_p(-1).value
        self.api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ByHandle)]

    def open(self, path, directory=False):
        info = Path(path).lstat()
        if getattr(info, 'st_file_attributes', 0) & REPARSE:
            raise ValueError('REPARSE_PATH_REFUSED')
        if directory != Path(path).is_dir():
            raise ValueError('WRONG_FILESYSTEM_OBJECT_TYPE')
        flags = 0x00200000 | (0x02000000 if directory else 0x08000000)
        handle = self.api.CreateFileW(extended(path), 0x80 if directory else 0x81,
                                      3 if directory else 1, None, 3, flags, None)
        if handle == self.invalid:
            raise ctypes.WinError(ctypes.get_last_error())
        # The directory remains held without delete sharing. A final file handle
        # uses OPEN_REPARSE_POINT; inspect its attributes before reading bytes.
        current = _ByHandle()
        if not self.api.GetFileInformationByHandle(handle, ctypes.byref(current)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.api.CloseHandle(handle)
            raise error
        if current.attributes & REPARSE or bool(current.attributes & 0x10) != directory:
            self.api.CloseHandle(handle)
            raise ValueError('OPENED_OBJECT_REDIRECTED_OR_WRONG_TYPE')
        return handle

    @contextmanager
    def directory(self, path):
        handle = self.open(path, directory=True)
        try:
            yield
        finally:
            self.api.CloseHandle(handle)

    @contextmanager
    def file(self, path):
        handle = self.open(path)
        try:
            fd = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_BINARY)
        except BaseException:
            self.api.CloseHandle(handle)
            raise
        with os.fdopen(fd, 'rb') as stream:
            yield stream


class Cancelled(Exception):
    pass


class AuditProgress:
    def __init__(self, callback, cancel_event=None, cancel_file=None):
        self.callback = callback
        self.cancel = cancel_event or threading.Event()
        self.cancel_file = cancel_file
        self.lock = threading.Lock()
        self.next_emit = self.next_cancel_poll = 0.0
        self.values = {'phase': 'catalogs', 'completedFiles': 0, 'verifiedFiles': 0,
                       'readBytes': 0, 'completedTiles': 0, 'stabilityFiles': 0}

    def check_cancel(self):
        if self.cancel.is_set():
            raise Cancelled('CANCELLED_WITHOUT_CHANGING_DATA')
        now = time.monotonic()
        if self.cancel_file is not None and now >= self.next_cancel_poll:
            with self.lock:
                if now >= self.next_cancel_poll:
                    self.next_cancel_poll = now + .25
                    if self.cancel_file.exists():
                        self.cancel.set()
        if self.cancel.is_set():
            raise Cancelled('CANCELLED_WITHOUT_CHANGING_DATA')

    def update(self, force=False, **increments):
        with self.lock:
            for key, value in increments.items():
                if isinstance(value, str):
                    self.values[key] = value
                else:
                    self.values[key] = self.values.get(key, 0) + value
            now = time.monotonic()
            if self.callback and (force or now >= self.next_emit):
                self.next_emit = now + 1
                self.callback(dict(self.values))


def read_pinned_json(reader, path, expected):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('EXPLICIT_HIERARCHY_OR_CATALOG_SHA_REQUIRED')
    with reader.file(path) as stream:
        if os.fstat(stream.fileno()).st_size > MAX_JSON:
            raise ValueError('BOUNDED_CATALOG_REQUIRED')
        raw = stream.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('CATALOG_SHA256_MISMATCH')
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_pairs)


def osgb_entries(directory):
    names = set()
    extra = 0
    for entry in os.scandir(directory):
        info = entry.stat(follow_symlinks=False)
        if getattr(info, 'st_file_attributes', 0) & REPARSE:
            raise ValueError('REPARSE_ENTRY_REFUSED')
        if entry.is_dir(follow_symlinks=False):
            raise ValueError('UNINDEXED_NESTED_GIS_DIRECTORY')
        if entry.name.lower().endswith('.osgb'):
            key = entry.name.casefold()
            if key in names:
                raise ValueError('CASE_COLLIDING_GIS_FILES')
            names.add(key)
        else:
            extra += 1
    return names, extra


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def verify_workspace(document, expected_hierarchy=NATIVE_HIERARCHY_SHA256, *, workers=2,
                     progress=None, cancel_event=None, cancel_file=None):
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError('ONE_TO_FOUR_BOUNDED_WORKERS_REQUIRED')
    root, resolved = parse_document(document)
    root = Path(str(root))
    gis = Path(str(resolved['gis']))
    runtime = Path(str(resolved['renderData']))
    data = gis / 'Data'
    master_path = runtime / 'data/showcase/zhumadian_native_hierarchy.json'
    reader = WindowsReadOnly()
    state = AuditProgress(progress, cancel_event, cancel_file)
    started = time.monotonic()
    result = {'schema': 'xnby.offline-osgb.integrity.v1', 'passed': False,
              'workspaceRoot': str(root), 'relativeGIS': document['paths']['gis'],
              'nativeHierarchySHA256': expected_hierarchy, 'workers': workers,
              'scope': 'Every catalogued OSGB including unreachable nodes; source directories enumerated; nonOSGB extras counted without claiming their hash validation',
              'dataChangedOrCopied': False, 'userConfigurationChanged': False,
              'cancelled': False, 'issues': [], 'issueCount': 0}
    issue_lock = threading.Lock()

    def issue(kind, path, **details):
        with issue_lock:
            result['issueCount'] += 1
            if len(result['issues']) < 128:
                result['issues'].append({'kind': kind, 'path': str(path), **details})

    catalogs = []
    try:
        with ExitStack() as scope:
            ancestors = set()
            for leaf in [data, master_path.parent]:
                for parent in [*reversed(leaf.parents), leaf]:
                    if parent not in ancestors:
                        scope.enter_context(reader.directory(parent))
                        ancestors.add(parent)
            master = read_pinned_json(reader, master_path, expected_hierarchy)
            if master.get('schema') != 'hongtu.osgb_native_hierarchy.v1':
                raise ValueError('NATIVE_HIERARCHY_SCHEMA_REQUIRED')
            rows = master['root_records']
            if not isinstance(rows, list) or not 1 <= len(rows) <= 10000 or len(rows) != master['base_root_count']:
                raise ValueError('COMPLETE_BOUNDED_ROOT_LIST_REQUIRED')
            tile_ids = [row['tile_id'] for row in rows]
            if any(type(tile) is not int or tile < 1 for tile in tile_ids) or len(set(tile_ids)) != len(rows):
                raise ValueError('UNIQUE_POSITIVE_TILE_IDS_REQUIRED')
            expected_top = {'tile_' + str(tile) for tile in tile_ids}
            actual_top = set()
            top_extra_non_osgb = 0
            for entry in os.scandir(data):
                info = entry.stat(follow_symlinks=False)
                if getattr(info, 'st_file_attributes', 0) & REPARSE:
                    raise ValueError('REPARSE_DATA_ROOT_ENTRY')
                if entry.is_dir(follow_symlinks=False):
                    actual_top.add(entry.name.casefold())
                elif entry.name.lower().endswith('.osgb'):
                    issue('unindexed_root_osgb', entry.name)
                else:
                    top_extra_non_osgb += 1
            for name in sorted(actual_top - expected_top):
                issue('unindexed_root_directory', name)
            result.update(expectedFiles=master['total_source_nodes'], expectedBytes=master['total_source_bytes'],
                          expectedTiles=len(rows), rootNonOSGBExtraFiles=top_extra_non_osgb)
            if type(result['expectedFiles']) is not int or not 0 < result['expectedFiles'] <= 2000000:
                raise ValueError('BOUNDED_EXPECTED_NODE_COUNT_REQUIRED')
            if type(result['expectedBytes']) is not int or result['expectedBytes'] <= 0:
                raise ValueError('EXPECTED_SOURCE_BYTES_REQUIRED')
            state.update(force=True, expectedFiles=result['expectedFiles'], expectedBytes=result['expectedBytes'])

            def load_tile_catalog(row):
                tile = row['tile_id']
                relative_catalog = f'assets/showcase/runtime/zhumadian/native_hierarchy/tile_{tile}.json'
                if row['catalog'] != relative_catalog:
                    raise ValueError('EXACT_RELATIVE_CATALOG_NAMESPACE_REQUIRED')
                catalog_path = runtime / relative_catalog
                with reader.directory(catalog_path.parent):
                    catalog = read_pinned_json(reader, catalog_path, row['sha256'])
                if (catalog.get('schema') != 'hongtu.osgb_root_hierarchy.v1' or catalog['tile_id'] != tile
                        or catalog['source_directory'] != f'assets/驻马店园区/Data/Tile_{tile}'):
                    raise ValueError('CATALOG_SOURCE_NAMESPACE_DIFFERS')
                nodes = catalog['nodes']
                if not isinstance(nodes, list) or len(nodes) != row['node_count'] or len(nodes) > 100000:
                    raise ValueError('COMPLETE_BOUNDED_NODE_LIST_REQUIRED')
                names = [canonical_name(node['name']) for node in nodes]
                if len(set(name.casefold() for name in names)) != len(nodes):
                    raise ValueError('DUPLICATE_SOURCE_NAME')
                for node in nodes:
                    if (type(node['bytes']) is not int or not 0 <= node['bytes'] <= 1024**3
                            or not isinstance(node['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', node['sha256'])):
                        raise ValueError('INVALID_SOURCE_SIZE_OR_SHA')
                declared_bytes = sum(node['bytes'] for node in nodes)
                if declared_bytes != row['source_bytes']:
                    raise ValueError('CATALOG_SOURCE_BYTE_COUNT_DIFFERS')
                return catalog_path, nodes, names, declared_bytes

            def tile_work(row):
                tile = row['tile_id']
                catalog_path, nodes, names, declared_bytes = load_tile_catalog(row)
                folder = data / f'Tile_{tile}'
                stamps = []
                aggregate = hashlib.sha256()
                extra_files = 0
                original_names = set()
                state.check_cancel()
                try:
                    with reader.directory(folder):
                        original_names, extra_files = osgb_entries(folder)
                        known = {name.casefold() for name in names}
                        for name in sorted(original_names - known):
                            issue('unindexed_osgb', f'Data/Tile_{tile}/{name}')
                        for node in sorted(nodes, key=lambda node: node['name']):
                            state.check_cancel()
                            name = node['name']
                            if (type(node['bytes']) is not int or not 0 <= node['bytes'] <= 1024**3
                                    or not re.fullmatch('[0-9a-f]{64}', node['sha256'])):
                                raise ValueError('INVALID_SOURCE_SIZE_OR_SHA')
                            path = folder / name
                            verified = False
                            try:
                                with reader.file(path) as stream:
                                    before = os.fstat(stream.fileno())
                                    if before.st_size != node['bytes']:
                                        issue('size_mismatch', f'Data/Tile_{tile}/{name}', expected=node['bytes'], actual=before.st_size)
                                    else:
                                        digest = hashlib.sha256()
                                        while chunk := stream.read(1024 * 1024):
                                            state.check_cancel()
                                            digest.update(chunk)
                                            state.update(readBytes=len(chunk))
                                        actual_sha = digest.hexdigest()
                                        if actual_sha != node['sha256']:
                                            issue('sha256_mismatch', f'Data/Tile_{tile}/{name}', expected=node['sha256'], actual=actual_sha)
                                        elif stamp(os.fstat(stream.fileno())) != stamp(before):
                                            issue('changed_while_reading', f'Data/Tile_{tile}/{name}')
                                        else:
                                            verified = True
                                            stamps.append((name, stamp(before)))
                                            aggregate.update((name + '\0' + actual_sha + '\0' + str(before.st_size) + '\n').encode('utf-8'))
                            except (OSError, ValueError) as error:
                                issue('missing_busy_or_redirected_file', f'Data/Tile_{tile}/{name}', errorType=type(error).__name__, winerror=getattr(error, 'winerror', None))
                            state.update(completedFiles=1, verifiedFiles=int(verified))
                        if osgb_entries(folder)[0] != original_names:
                            issue('directory_changed_during_read', f'Data/Tile_{tile}')
                except OSError as error:
                    issue('missing_or_busy_tile', f'Data/Tile_{tile}', errorType=type(error).__name__, winerror=getattr(error, 'winerror', None))
                    state.update(completedFiles=len(nodes))
                state.update(completedTiles=1)
                return {'tile': tile, 'declaredFiles': len(nodes), 'declaredBytes': declared_bytes,
                        'catalog': str(catalog_path), 'catalogSHA256': row['sha256'],
                        'sourceAuditSHA256': aggregate.hexdigest(), 'stamps': stamps, 'originalNames': sorted(original_names), 'nonOSGBExtraFiles': extra_files}

            state.update(force=True, phase='checking_catalogs')
            declared_files = declared_bytes = 0
            for row in sorted(rows, key=lambda row: row['tile_id']):
                state.check_cancel()
                _, checked_nodes, _, checked_bytes = load_tile_catalog(row)
                declared_files += len(checked_nodes)
                declared_bytes += checked_bytes
                state.update(catalogsValidated=1)
            if declared_files != result['expectedFiles'] or declared_bytes != result['expectedBytes']:
                raise ValueError('MASTER_AND_ALL_CATALOG_TOTALS_DIFFER')
            state.update(force=True, phase='hashing_osgb')
            iterator = iter(sorted(rows, key=lambda row: row['tile_id']))
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='xnby-osgb-integrity') as pool:
                pending = set()
                def submit_next():
                    try:
                        row = next(iterator)
                    except StopIteration:
                        return
                    pending.add(pool.submit(tile_work, row))
                for _ in range(workers):
                    submit_next()
                try:
                    while pending:
                        done, _ = wait(pending, return_when=FIRST_COMPLETED)
                        for future in done:
                            pending.remove(future)
                            catalogs.append(future.result())
                            submit_next()
                except BaseException:
                    state.cancel.set()
                    for future in pending:
                        future.cancel()
                    raise
            catalogs.sort(key=lambda tile: tile['tile'])
            if sum(tile['declaredFiles'] for tile in catalogs) != result['expectedFiles']:
                issue('master_node_count_differs', 'native_hierarchy')
            if sum(tile['declaredBytes'] for tile in catalogs) != result['expectedBytes']:
                issue('master_source_bytes_differs', 'native_hierarchy')
            state.update(force=True, phase='checking_stability')
            aggregate = hashlib.sha256()
            for tile in catalogs:
                state.check_cancel()
                with reader.directory(data / f'Tile_{tile["tile"]}'):
                    for name, before in tile['stamps']:
                        state.check_cancel()
                        path = data / f'Tile_{tile["tile"]}' / name
                        try:
                            current = path.lstat()
                            if getattr(current, 'st_file_attributes', 0) & REPARSE or stamp(current) != before:
                                issue('changed_after_hash', f'Data/Tile_{tile["tile"]}/{name}')
                        except OSError:
                            issue('missing_after_hash', f'Data/Tile_{tile["tile"]}/{name}')
                        state.update(stabilityFiles=1)
                    if osgb_entries(data / f'Tile_{tile["tile"]}')[0] != set(tile['originalNames']):
                        issue('directory_changed_after_hash', f'Data/Tile_{tile["tile"]}')
                with reader.directory(Path(tile['catalog']).parent):
                    read_pinned_json(reader, Path(tile['catalog']), tile['catalogSHA256'])
                aggregate.update(f'{tile["tile"]}\0{tile["catalogSHA256"]}\0{tile["sourceAuditSHA256"]}\n'.encode('utf-8'))
            read_pinned_json(reader, master_path, expected_hierarchy)
            result.update(verifiedFiles=state.values['verifiedFiles'], completedFiles=state.values['completedFiles'],
                          readBytes=state.values['readBytes'], stabilityFiles=state.values['stabilityFiles'],
                          validatedCatalogs=len(catalogs), sourceAuditSHA256=aggregate.hexdigest(),
                          nonOSGBExtraFiles=sum(t['nonOSGBExtraFiles'] for t in catalogs),
                          observation='Hashes matched at read time; matching inode/size/mtime checked again; no guarantee against later modification')
            result['passed'] = (result['issueCount'] == 0 and result['verifiedFiles'] == result['expectedFiles']
                                and result['readBytes'] == result['expectedBytes']
                                and result['stabilityFiles'] == result['expectedFiles'])
    except Cancelled as error:
        result.update(cancelled=True, error=str(error))
    except (OSError, ValueError, KeyError, TypeError) as error:
        result.update(errorType=type(error).__name__, error=str(error))
    finally:
        result['elapsedSeconds'] = time.monotonic() - started
        result['progress'] = dict(state.values)
        state.update(force=True, phase='passed' if result['passed'] else 'cancelled' if result['cancelled'] else 'failed')
    return result


def safe_report_path(path, document):
    _, paths = parse_document(document)
    target = path.absolute()
    for key in ['gis', 'renderData']:
        asset = Path(str(paths[key])).resolve()
        if target.resolve().is_relative_to(asset):
            raise ValueError('REPORT_MUST_NOT_BE_WRITTEN_INSIDE_READ_ONLY_ASSETS')
    if target.exists():
        raise FileExistsError('REPORT_ALREADY_EXISTS_REFUSE_OVERWRITE')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--workspace-root', type=Path)
    selection.add_argument('--config', type=Path)
    parser.add_argument('--hierarchy-sha256', default=NATIVE_HIERARCHY_SHA256)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--cancel-file', type=Path)
    args = parser.parse_args()
    document = read_configuration(args.config) if args.config else document_for(args.workspace_root)
    report = safe_report_path(args.report, document)
    def progress(value):
        print(json.dumps({'type': 'progress', **value}), flush=True)
    result = verify_workspace(document, args.hierarchy_sha256, workers=args.workers,
                              progress=progress, cancel_file=args.cancel_file)
    report.parent.mkdir(parents=True, exist_ok=True)
    temp = report.with_name(report.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as output:
            output.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
            output.flush()
            os.fsync(output.fileno())
        os.rename(temp, report)  # Windows refuses an existing destination.
    finally:
        if temp.exists():
            temp.unlink()
    print(json.dumps({'type': 'result', 'passed': result['passed'], 'cancelled': result['cancelled'],
                      'verifiedFiles': result.get('verifiedFiles'), 'issueCount': result['issueCount'],
                      'seconds': result['elapsedSeconds'], 'report': str(report)}), flush=True)
    return 0 if result['passed'] else 2 if result['cancelled'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
