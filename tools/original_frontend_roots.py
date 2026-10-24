"""Content identity and relocatable bindings for five original frontend/map roots.

Only private metadata is written. Original resources, maps and business data are
never copied, extracted, modified or uploaded by this tool.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import stat
import uuid
from concurrent.futures import ThreadPoolExecutor

ROLES = ('security_pc', 'emergency_pc', 'mobile', 'bigscreen', 'tiles')
KIND = 'xnby.original-frontend.content.v1'
BINDINGS = 'xnby.original-frontend.bindings.v1'
MAX_MEMBERS = 200000
MAX_BYTES = 2 * 1024**3
MAX_DOCUMENT = 32 * 1024**2
HASH_WORKERS = 8
HASH_BATCH = 64


def require(value, code):
    if not value: raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def no_redirect(path, directory):
    path = Path(path); info = path.lstat()
    require(not path.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400
            and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)),
            'REGULAR_FRONTEND_DIRECTORY_REQUIRED' if directory else 'REGULAR_FRONTEND_FILE_REQUIRED')
    return info


def document(path, limit=MAX_DOCUMENT):
    path = Path(path); no_redirect(path, False)
    require(0 < path.stat().st_size <= limit, 'BOUNDED_FRONTEND_DOCUMENT_REQUIRED')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'DUPLICATE_FRONTEND_DOCUMENT_KEY'); result[key] = value
        return result
    result = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    require(isinstance(result, dict), 'FRONTEND_DOCUMENT_OBJECT_REQUIRED')
    return result


def relative(value):
    require(isinstance(value, str) and value and '\\' not in value
            and not any(ord(c) < 32 for c in value), 'RELATIVE_FRONTEND_MEMBER_REQUIRED')
    require(not PurePosixPath(value).is_absolute() and not re.match(r'^[A-Za-z]:', value)
            and all(part not in ('', '.', '..') for part in value.split('/')), 'RELATIVE_FRONTEND_MEMBER_REQUIRED')
    return value


def read_bindings(path):
    path = Path(path); no_redirect(path, False)
    path = path.resolve(strict=True); before = sha(path); spec = document(path, 65536)
    require(set(spec) == {'schema', 'appBasePath', 'roots'} and spec['schema'] == BINDINGS
            and spec['appBasePath'] == '/zhumadian' and isinstance(spec['roots'], dict)
            and set(spec['roots']) == set(ROLES), 'EXACT_ORIGINAL_FRONTEND_BINDINGS_REQUIRED')
    roots = {}
    for role, value in spec['roots'].items():
        require(isinstance(value, str) and value and not any(ord(c) < 32 for c in value), 'EXPLICIT_FRONTEND_ROOT_REQUIRED')
        root = Path(value)
        if not root.is_absolute():
            relative(value.replace('\\', '/')); root = path.parent / root
        no_redirect(root, True); roots[role] = root.resolve(strict=True)
    require(all(a == b or not roots[a].is_relative_to(roots[b]) for a in ROLES for b in ROLES),
            'DISJOINT_ORIGINAL_FRONTEND_ROOTS_REQUIRED')
    require(sha(path) == before, 'FRONTEND_BINDINGS_CHANGED_DURING_READ')
    return roots, before


def hash_member(candidate):
    path, name, size, modified = candidate
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size == size and before.st_mtime_ns == modified,
                'FRONTEND_RESOURCE_CHANGED_BEFORE_HASH')
        pin = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    require(before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            'FRONTEND_RESOURCE_CHANGED_DURING_SCAN')
    return {'path': name, 'bytes': size, 'sha256': pin}


def scan(root, role, progress=None):
    root = Path(root).resolve(strict=True); no_redirect(root, True)
    files = []; candidates = []; directories = []; pending = [root]; total = 0; members = 0
    while pending:
        current = pending.pop()
        # Windows enumeration already returns sizes/times; retain those values
        # rather than issuing an extra network path-stat for every small tile.
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path); info = entry.stat(follow_symlinks=False)
                name = relative(path.relative_to(root).as_posix())
                require(not entry.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                        'FRONTEND_MEMBER_REDIRECTION_REJECTED')
                members += 1; require(members <= MAX_MEMBERS, 'FRONTEND_MEMBER_COUNT_LIMIT')
                if stat.S_ISDIR(info.st_mode):
                    directories.append(name); pending.append(path)
                else:
                    require(stat.S_ISREG(info.st_mode), 'REGULAR_FRONTEND_MEMBER_REQUIRED')
                    total += info.st_size; require(total <= MAX_BYTES, 'FRONTEND_CONTENT_SIZE_LIMIT')
                    candidates.append((path, name, info.st_size, info.st_mtime_ns))
    with ThreadPoolExecutor(max_workers=HASH_WORKERS) as pool:
        for start in range(0, len(candidates), HASH_BATCH):
            files.extend(pool.map(hash_member, candidates[start:start + HASH_BATCH]))
            if progress is not None: progress(role, len(files), len(candidates))
    files.sort(key=lambda row: row['path']); directories.sort()
    require(files and (role == 'tiles' or any(row['path'] == 'index.html' for row in files)), 'ORIGINAL_FRONTEND_INDEX_OR_MAP_REQUIRED')
    tree = {'files': files, 'directories': directories}
    pin = hashlib.sha256(json.dumps(tree, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return dict(tree, fileCount=len(files), directoryCount=len(directories), bytes=total, treeSHA256=pin)


def prepare(bindings, output, progress=None):
    bindings = Path(bindings).resolve(strict=True); roots, bindings_pin = read_bindings(bindings)
    output = Path(output).absolute()
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir()
            and output.parent.resolve(strict=True) == output.parent, 'FRESH_FRONTEND_CONTENT_MANIFEST_REQUIRED')
    require(all(not output.is_relative_to(root) for root in roots.values()), 'FRONTEND_METADATA_MUST_NOT_ENTER_RESOURCE_ROOT')
    roles = {role: scan(root, role, progress) for role, root in roots.items()}
    require(sha(bindings) == bindings_pin, 'FRONTEND_BINDINGS_CHANGED_DURING_PREPARATION')
    result = {'kind': KIND, 'ownerId': str(uuid.uuid4()), 'appBasePath': '/zhumadian', 'roles': roles,
              'fileCount': sum(row['fileCount'] for row in roles.values()), 'bytes': sum(row['bytes'] for row in roles.values()),
              'resourcesCopied': False, 'resourcesModified': False, 'businessLogicRedesigned': False,
              'privateResourceIndex': True}
    raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    require(len(raw) <= MAX_DOCUMENT, 'FRONTEND_MANIFEST_SIZE_LIMIT')
    with output.open('xb') as stream: stream.write(raw)
    return {'manifestSHA256': sha(output), 'fileCount': result['fileCount'], 'bytes': result['bytes'], 'resourcesCopied': False}


def validate_selection(manifest, pin, bindings):
    requested = manifest is not None or pin is not None or bindings is not None
    if requested:
        require(manifest is not None and pin is not None and bindings is not None,
                'FRONTEND_MANIFEST_PIN_AND_BINDINGS_REQUIRED_TOGETHER')
        require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin), 'EXPLICIT_FRONTEND_MANIFEST_PIN_REQUIRED')
    return requested


def select(manifest, pin, bindings, progress=None):
    require(validate_selection(manifest, pin, bindings), 'EXPLICIT_FRONTEND_CONTENT_SELECTION_REQUIRED')
    manifest = Path(manifest); no_redirect(manifest, False)
    require(sha(manifest) == pin, 'FRONTEND_MANIFEST_PIN_MISMATCH')
    spec = document(manifest)
    require(spec.get('kind') == KIND and spec.get('appBasePath') == '/zhumadian'
            and isinstance(spec.get('roles'), dict) and set(spec['roles']) == set(ROLES), 'EXACT_ORIGINAL_FRONTEND_CONTENT_REQUIRED')
    require(spec.get('resourcesCopied') is False and spec.get('resourcesModified') is False
            and spec.get('businessLogicRedesigned') is False and spec.get('privateResourceIndex') is True,
            'READONLY_ORIGINAL_FRONTEND_PROVENANCE_REQUIRED')
    owner = spec.get('ownerId'); require(isinstance(owner, str) and re.fullmatch('[0-9a-f-]{36}', owner)
        and str(uuid.UUID(owner)) == owner, 'FRONTEND_CONTENT_OWNER_UUID_REQUIRED')
    roots, bindings_pin = read_bindings(bindings); observed = {role: scan(root, role, progress) for role, root in roots.items()}
    require(observed == spec['roles'], 'FRONTEND_RESOURCE_CONTENT_OR_SET_MISMATCH')
    total = sum(row['fileCount'] for row in observed.values()); size = sum(row['bytes'] for row in observed.values())
    require(total == spec.get('fileCount') and size == spec.get('bytes'), 'FRONTEND_CONTENT_TOTAL_MISMATCH')
    require(sha(manifest) == pin and sha(bindings) == bindings_pin, 'FRONTEND_SELECTION_CHANGED_DURING_VERIFICATION')
    return roots, {'mode': 'verified-original-static-roots', 'manifestSHA256': pin, 'bindingsSHA256': bindings_pin,
        'ownerId': owner, 'fileCount': total, 'bytes': size,
        'roles': {role: {key: row[key] for key in ['fileCount', 'directoryCount', 'bytes', 'treeSHA256']} for role, row in observed.items()},
        'legacyGatewayReceiptRead': False, 'resourcesCopied': False, 'allFiveRootsContentVerified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('prepare'); build.add_argument('--bindings', type=Path, required=True); build.add_argument('--output', type=Path, required=True)
    verify = commands.add_parser('verify'); verify.add_argument('--manifest', type=Path, required=True)
    verify.add_argument('--manifest-sha256', required=True); verify.add_argument('--bindings', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.bindings, args.output) if args.command == 'prepare' else select(args.manifest, args.manifest_sha256, args.bindings)[1]
    print(json.dumps(result))


if __name__ == '__main__': main()
