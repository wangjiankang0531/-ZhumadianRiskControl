"""Reproduce the manual preview sources from pinned Git blobs, without touching a checkout.

This prepares source only: it never builds, starts a reader, copies GIS, or changes Git refs.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

SCHEMA = 'xnby.native.manual-preview.source.v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('Invalid source-relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Unsafe source-relative path: ' + value)
    if path.parts[0] not in ('Application', 'XNBYEngine'):
        raise ValueError('Unexpected source root: ' + value)
    return value


def git_blobs(repository, commit, rows):
    """One bounded batch per repository; neither HEAD nor worktree files are read."""
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('An exact Git commit is required')
    requests = []
    for row in rows:
        relative_path(row['path'])
        requests.append(commit + ':' + row['path'].split('/', 1)[1])
    result = subprocess.run(['git', '-C', str(repository), 'cat-file', '--batch'],
                            input=('\n'.join(requests) + '\n').encode(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45, check=True)
    offset, values = 0, {}
    for row in rows:
        end = result.stdout.find(b'\n', offset)
        if end < 0:
            raise ValueError('Incomplete Git batch response')
        header = result.stdout[offset:end].decode('ascii').split()
        if len(header) != 3 or header[1] != 'blob':
            raise ValueError('Pinned Git source is missing: ' + row['path'])
        size = int(header[2])
        if size < 0 or size > 8 * 1024 * 1024:
            raise ValueError('Unexpected source blob size')
        offset = end + 1
        data = result.stdout[offset:offset + size]
        if len(data) != size or result.stdout[offset + size:offset + size + 1] != b'\n':
            raise ValueError('Incomplete Git source blob')
        if header[0] != row['gitBlob'] or digest(data) != row['baseSHA256']:
            raise ValueError('Pinned Git source mismatch: ' + row['path'])
        values[row['path']] = data
        offset += size + 1
    if offset != len(result.stdout):
        raise ValueError('Unexpected trailing Git batch output')
    return values


def validate_recipe(recipe):
    if recipe.get('schema') != SCHEMA:
        raise ValueError('Unsupported recipe schema')
    files = recipe['files']
    if not files or len(files) != recipe['sourceFiles'] or len(files) > 2000:
        raise ValueError('Source count mismatch')
    seen = set()
    for row in files:
        name = relative_path(row['path'])
        if name.casefold() in seen:
            raise ValueError('Duplicate or case-colliding source path')
        seen.add(name.casefold())
        for key in ('baseSHA256', 'SHA256'):
            if not re.fullmatch(r'[0-9a-f]{64}', row[key]):
                raise ValueError('Invalid SHA256')
        if row.get('origin') == 'git':
            if not re.fullmatch(r'[0-9a-f]{40}', row['gitBlob']):
                raise ValueError('Invalid Git blob pin')
        elif row.get('origin') != 'annotation-probe':
            raise ValueError('Unknown source origin')
    for root in ('Application', 'XNBYEngine'):
        if not re.fullmatch(r'[0-9a-f]{40}', recipe['commits'][root]):
            raise ValueError('Invalid source commit pin')


def checked_file(root, name, pin):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing or redirected recipe input: ' + name)
    data = path.read_bytes()
    if digest(data) != pin:
        raise ValueError('Recipe input changed: ' + name)
    return data


def prepare_files(recipe, repositories, overlay_root, reader=git_blobs):
    validate_recipe(recipe)
    values = {}
    for root in ('Application', 'XNBYEngine'):
        rows = [r for r in recipe['files'] if r['origin'] == 'git' and r['path'].startswith(root + '/')]
        if rows:
            values.update(reader(repositories[root], recipe['commits'][root], rows))
    for row in recipe['files']:
        if row['origin'] == 'annotation-probe':
            data = checked_file(overlay_root, 'tools/native_annotation_probe.inl', row['baseSHA256'])
            values[row['path']] = data
    for name, pin in recipe.get('overlays', {}).items():
        relative_path('Application/' + name)
        values['Application/' + name] = checked_file(overlay_root, name, pin)
    modules = {}
    for name, pin in recipe.get('patches', {}).items():
        if name not in ('native_static_shell_patch.py', 'native_annotation_probe_patch.py', 'native_manual_preview_patch.py'):
            raise ValueError('Unknown source patch')
        raw = checked_file(overlay_root, 'tools/' + name, pin)
        namespace = {'__name__': 'source_recipe_patch'}
        exec(compile(raw, name, 'exec'), namespace)
        modules[name] = namespace
    if modules:
        if set(modules) != {'native_static_shell_patch.py', 'native_annotation_probe_patch.py', 'native_manual_preview_patch.py'}:
            raise ValueError('Incomplete patch chain')
        main = 'Application/native/main.cpp'
        for name in ('native_static_shell_patch.py', 'native_annotation_probe_patch.py', 'native_manual_preview_patch.py'):
            values[main] = modules[name]['patched_main'](values[main])
        editor = 'Application/native/landscape_editor.inl'
        values[editor] = modules['native_manual_preview_patch.py']['patched_editor_dialog'](values[editor])
    if set(values) != {r['path'] for r in recipe['files']}:
        raise ValueError('Prepared source set mismatch')
    for row in recipe['files']:
        if digest(values[row['path']]) != row['SHA256']:
            raise ValueError('Prepared source hash mismatch: ' + row['path'])
    return values


def write_fresh(output, values, receipt):
    output = output.resolve()
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Output must be absent, with an existing parent')
    for name in values:
        relative_path(name)
    # Only this function's newly created staging directory is cleaned on failure.
    with tempfile.TemporaryDirectory(prefix=output.name + '.prepare-', dir=output.parent) as staging:
        stage = Path(staging)
        payload = stage / 'payload'
        payload.mkdir()
        for name, data in sorted(values.items()):
            target = payload / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (payload / 'source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        if output.exists():
            raise ValueError('Output appeared during preparation')
        os.rename(payload, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application-repository', type=Path, required=True)
    parser.add_argument('--engine-repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, default=Path(__file__).with_name('native_manual_preview_source.json'))
    args = parser.parse_args()
    repositories = {'Application': args.application_repository.resolve(), 'XNBYEngine': args.engine_repository.resolve()}
    overlay_root = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    for protected in (*repositories.values(), overlay_root):
        if output == protected or output.is_relative_to(protected):
            raise ValueError('Output must be outside both checkouts and the overlay source tree')
    if output.exists():
        raise ValueError('Output already exists; no files were changed')
    raw = args.recipe.read_bytes()
    recipe = json.loads(raw)
    values = prepare_files(recipe, repositories, overlay_root)
    receipt = {'schema': SCHEMA, 'recipeSHA256': digest(raw), 'commits': recipe['commits'],
               'sourceFiles': len(values), 'sourceSHA256': {name: digest(data) for name, data in sorted(values.items())},
               'unpinnedWorktreeSourcesUsed': False, 'pinnedOwnOverlaysUsed': True,
               'GISOrRuntimeCopied': False, 'builtOrStarted': False}
    write_fresh(output, values, receipt)
    print(json.dumps({'prepared': True, 'sourceFiles': len(values), 'recipeSHA256': digest(raw),
                      'GISOrRuntimeCopied': False, 'builtOrStarted': False}))


if __name__ == '__main__':
    main()
