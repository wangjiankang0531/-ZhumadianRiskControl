"""Prepare verified original admin static files once; runtime loading needs only stdlib.

This private component contains original frontend resources. Never add its ZIP or
manifest to Git. It provides no login, business API or authentication shortcut.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import shutil
import stat
import uuid
import zipfile

SOURCE_SHA = 'f64765343660b98322554a800f05ff8b76da14c92e3729d7f01ff2d9f85a3b08'
KIND = 'xnby.original-admin.frontend-runtime.v1'
MANIFEST = 'admin_runtime.json'
PAYLOAD = 'admin_static.zip'
MAX_COMPRESSED = 64 * 1024**2
MAX_EXPANDED = 128 * 1024**2
MAX_MANIFEST = 8 * 1024**2
MAX_FILES = 20000
SOURCE_FILES = 1589
SOURCE_ARCHIVE_BYTES = 13095102
SOURCE_EXPANDED_BYTES = 30216262


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(path):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, 'st_file_attributes', 0) & 0x400, 'REGULAR_ADMIN_RUNTIME_FILE_REQUIRED')
    return path.resolve(strict=True)


def base_path(value):
    require(isinstance(value, str) and len(value) <= 128
            and re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*', value), 'EXPLICIT_ADMIN_DEPLOYMENT_BASE_REQUIRED')
    return value


def relative(value):
    require(isinstance(value, str) and value and '\\' not in value
            and not any(ord(c) < 32 for c in value), 'RELATIVE_ADMIN_STATIC_MEMBER_REQUIRED')
    parts = value.split('/')
    require(not PurePosixPath(value).is_absolute() and not any(p in ('', '.', '..') for p in parts)
            and not re.match(r'^[A-Za-z]:', value), 'RELATIVE_ADMIN_STATIC_MEMBER_REQUIRED')
    return value


def validate_selection(manifest, pin):
    requested = manifest is not None or pin is not None
    if requested:
        require(manifest is not None and pin is not None, 'ADMIN_RUNTIME_MANIFEST_AND_PIN_REQUIRED_TOGETHER')
        require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin), 'EXPLICIT_ADMIN_RUNTIME_MANIFEST_PIN_REQUIRED')
    return requested


def document(path):
    path = regular(path)
    require(0 < path.stat().st_size <= MAX_MANIFEST, 'BOUNDED_ADMIN_RUNTIME_MANIFEST_REQUIRED')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'DUPLICATE_ADMIN_RUNTIME_MANIFEST_KEY')
            result[key] = value
        return result
    result = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    require(isinstance(result, dict), 'ADMIN_RUNTIME_MANIFEST_OBJECT_REQUIRED')
    return result


def load(manifest, pin, expected_base='/zhumadian/admin'):
    require(validate_selection(manifest, pin), 'EXPLICIT_ADMIN_RUNTIME_SELECTION_REQUIRED')
    base_path(expected_base)
    manifest = regular(manifest)
    require(manifest.name == MANIFEST and sha(manifest) == pin, 'ADMIN_RUNTIME_MANIFEST_PIN_MISMATCH')
    root = manifest.parent
    require(not root.is_symlink() and not getattr(root.lstat(), 'st_file_attributes', 0) & 0x400,
            'ADMIN_RUNTIME_ROOT_REDIRECTION_REJECTED')
    require({p.name for p in root.iterdir()} == {MANIFEST, PAYLOAD}, 'EXACT_ADMIN_RUNTIME_FILE_SET_REQUIRED')
    spec = document(manifest)
    require(spec.get('kind') == KIND and spec.get('base') == expected_base, 'ADMIN_RUNTIME_KIND_OR_BASE_MISMATCH')
    owner = spec.get('ownerId')
    require(isinstance(owner, str) and re.fullmatch('[0-9a-f-]{36}', owner)
            and str(uuid.UUID(owner)) == owner, 'ADMIN_RUNTIME_OWNER_UUID_REQUIRED')
    require(spec.get('sourceArchiveSHA256') == SOURCE_SHA and spec.get('privateOriginalResourcesIncluded') is True
            and spec.get('businessLogicRedesigned') is False and spec.get('originalJavaScriptEvaluated') is False,
            'ORIGINAL_ADMIN_RUNTIME_PROVENANCE_REQUIRED')
    require(spec.get('sourceArchiveBytes') == SOURCE_ARCHIVE_BYTES
            and spec.get('sourceExpandedBytes') == SOURCE_EXPANDED_BYTES, 'ORIGINAL_ADMIN_SOURCE_SIZE_MISMATCH')
    for key in ['deploymentRecipeSHA256', 'nodeSHA256', 'parserSHA256', 'payloadSHA256']:
        require(isinstance(spec.get(key), str) and re.fullmatch('[0-9a-f]{64}', spec[key]), 'ADMIN_RUNTIME_FINGERPRINT_REQUIRED')
    rows = spec.get('files')
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_FILES
            and type(spec.get('fileCount')) is int and spec['fileCount'] == len(rows) == SOURCE_FILES, 'ADMIN_RUNTIME_FILE_COUNT_MISMATCH')
    members = {}; total = 0
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'EXACT_ADMIN_RUNTIME_MEMBER_FIELDS')
        name = relative(row['path'])
        require(name not in members, 'DUPLICATE_ADMIN_RUNTIME_MEMBER')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_EXPANDED
                and isinstance(row['sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['sha256']),
                'ADMIN_RUNTIME_MEMBER_SIZE_OR_PIN_MISMATCH')
        members[name] = row; total += row['bytes']
        require(total <= MAX_EXPANDED, 'ADMIN_RUNTIME_EXPANSION_LIMIT')
    require(type(spec.get('expandedBytes')) is int and total == spec['expandedBytes']
            and 'index.html' in members, 'ADMIN_RUNTIME_TOTAL_OR_INDEX_MISMATCH')
    payload = regular(root / PAYLOAD)
    require(payload.stat().st_size == spec.get('payloadBytes') and payload.stat().st_size <= MAX_COMPRESSED
            and sha(payload) == spec['payloadSHA256'], 'ADMIN_RUNTIME_PAYLOAD_PIN_MISMATCH')
    files = {}
    with zipfile.ZipFile(payload) as archive:
        entries = archive.infolist()
        require(len(entries) == len(members) and {e.filename for e in entries} == set(members), 'EXACT_ADMIN_RUNTIME_ZIP_MEMBERS')
        for entry in entries:
            name = relative(entry.filename); row = members[name]
            require(not entry.is_dir() and stat.S_IFMT(entry.external_attr >> 16) in (0, stat.S_IFREG)
                    and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    and not entry.flag_bits & 1 and entry.file_size == row['bytes'], 'REGULAR_ADMIN_RUNTIME_ZIP_MEMBER_REQUIRED')
            with archive.open(entry) as stream:
                raw = stream.read(row['bytes'] + 1)
            require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'ADMIN_RUNTIME_MEMBER_BYTES_MISMATCH')
            files[name] = raw
    require(sha(manifest) == pin, 'ADMIN_RUNTIME_MANIFEST_CHANGED_AFTER_VERIFICATION')
    source = {'archiveSHA256': SOURCE_SHA, 'archiveBytes': spec['sourceArchiveBytes'], 'files': len(rows),
              'expandedBytes': spec['sourceExpandedBytes'], 'resourcesExtracted': False}
    proof = {'mode': 'prepared-original-admin-frontend', 'selectionSHA256': pin, 'ownerId': owner,
             'base': expected_base, 'fileCount': len(rows), 'expandedBytes': total,
             'payloadSHA256': spec['payloadSHA256'], 'deploymentRecipeSHA256': spec['deploymentRecipeSHA256'],
             'sourceArchive': source, 'sourceArchiveReadAtRuntime': False, 'nodeOrParserRequiredAtRuntime': False,
             'runtimeResourcesExtracted': False, 'businessLogicRedesigned': False}
    return files, proof


def prepare(archive, node, parser, output, base, node_pin, parser_pin, recipe_pin, recipe=None):
    archive, node, parser = map(regular, [archive, node, parser]); base_path(base)
    recipe = regular(recipe or Path(__file__).with_name('adapt_original_admin_static.mjs'))
    for path, pin in [(node, node_pin), (parser, parser_pin), (recipe, recipe_pin)]:
        require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin) and sha(path) == pin,
                'TRUSTED_ADMIN_PREPARATION_TOOL_PIN_MISMATCH')
    require(archive.stat().st_size <= MAX_COMPRESSED and sha(archive) == SOURCE_SHA, 'FIXED_ORIGINAL_ADMIN_ARCHIVE_REQUIRED')
    output = Path(output).absolute()
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir()
            and output.parent.resolve(strict=True) == output.parent, 'FRESH_ADMIN_RUNTIME_OUTPUT_REQUIRED')
    require(all(not output.is_relative_to(p.parent) for p in [archive, node, parser]), 'ADMIN_RUNTIME_OUTPUT_OVERLAPS_SOURCE')
    ceiling = MAX_EXPANDED + MAX_MANIFEST + 2 * 1024**2
    free = shutil.disk_usage(output.parent).free
    require(free >= 2 * ceiling + 64 * 1024**2, 'ADMIN_RUNTIME_SPACE_RESERVE_REQUIRED')
    # Original tar parsing/AST transformation are build-time dependencies only.
    from readonly_original_static_archive import load_archive
    from adapt_original_admin_archive import adapt_admin_files
    original, source = load_archive(archive, SOURCE_SHA)
    files, deployment = adapt_admin_files(original, base, node, parser, recipe)
    require(set(files) == set(original) and len(files) == SOURCE_FILES, 'ALL_ORIGINAL_ADMIN_RESOURCES_REQUIRED')
    require(sum(map(len, files.values())) <= MAX_EXPANDED, 'ADMIN_RUNTIME_EXPANSION_LIMIT')
    for path, pin in [(archive, SOURCE_SHA), (node, node_pin), (parser, parser_pin), (recipe, recipe_pin)]:
        require(sha(path) == pin, 'ADMIN_PREPARATION_INPUT_CHANGED')
    output.mkdir(); payload = output / PAYLOAD; rows = []
    with zipfile.ZipFile(payload, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in sorted(files):
            relative(name); raw = files[name]
            member = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o100644 << 16; zipped.writestr(member, raw)
            rows.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    require(payload.stat().st_size <= MAX_COMPRESSED, 'ADMIN_RUNTIME_COMPRESSED_LIMIT')
    spec = {'kind': KIND, 'ownerId': str(uuid.uuid4()), 'base': base,
            'sourceArchiveSHA256': SOURCE_SHA, 'sourceArchiveBytes': source['archiveBytes'], 'sourceExpandedBytes': source['expandedBytes'],
            'deploymentRecipeSHA256': deployment['recipeSHA256'], 'nodeSHA256': deployment['nodeSHA256'], 'parserSHA256': deployment['parserSHA256'],
            'payloadSHA256': sha(payload), 'payloadBytes': payload.stat().st_size, 'fileCount': len(rows),
            'expandedBytes': sum(r['bytes'] for r in rows), 'files': rows,
            'privateOriginalResourcesIncluded': True, 'businessLogicRedesigned': False, 'originalJavaScriptEvaluated': False,
            'conservativeWriteCeilingBytes': ceiling, 'freeBytesBeforePreparation': free}
    manifest = output / MANIFEST; manifest.write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')
    prepared, proof = load(manifest, sha(manifest), base)
    require(prepared == files, 'ADMIN_RUNTIME_PREPARED_BYTES_MISMATCH')
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('prepare')
    for name in ['archive', 'node', 'parser', 'output']:
        build.add_argument('--' + name, type=Path, required=True)
    for name in ['node-sha256', 'parser-sha256', 'recipe-sha256']:
        build.add_argument('--' + name, required=True)
    build.add_argument('--base', default='/zhumadian/admin'); build.add_argument('--recipe', type=Path)
    verify = commands.add_parser('verify'); verify.add_argument('--manifest', type=Path, required=True)
    verify.add_argument('--manifest-sha256', required=True); verify.add_argument('--base', default='/zhumadian/admin')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.archive, args.node, args.parser, args.output, args.base,
                         args.node_sha256, args.parser_sha256, args.recipe_sha256, args.recipe)
    else:
        _, result = load(args.manifest, args.manifest_sha256, args.base)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
