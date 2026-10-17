"""Select a complete EXE/WEB pair atomically; user data stays outside version folders.

The CLI requires an explicit state file. Existing default launch scripts are not
changed by preparing or testing a selection. Running web owns a fresh foreground
server; an occupied port fails rather than attaching to an unrelated service.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'xnby.release.selection.v1'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1048576), b''):
            h.update(block)
    return h.hexdigest()


def relative_file(folder, name):
    part = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or part.is_absolute() or '..' in part.parts:
        raise ValueError('Invalid package-relative file')
    path = folder.joinpath(*part.parts)
    if not path.resolve().is_relative_to(folder.resolve()) or not path.is_file():
        raise ValueError('Missing or escaped package file: ' + name)
    return path


class Catalog:
    def __init__(self, root, state):
        self.root = Path(root).resolve()
        self.state = Path(state).absolute()
        if self.state.is_symlink() or self.state.is_junction():
            raise ValueError('Selection cannot be a link')
        if not self.state.resolve().is_relative_to(self.root):
            raise ValueError('Selection must stay below Application')

    def read(self):
        if not self.state.exists():
            return {'schema': SCHEMA, 'revision': 0, 'selected': None, 'history': []}
        state = json.loads(self.state.read_text('utf-8'))
        if state.get('schema') != SCHEMA or type(state.get('revision')) is not int or state['revision'] < 1:
            raise ValueError('Invalid selection state')
        if not isinstance(state.get('selected'), dict) or not isinstance(state.get('history'), list):
            raise ValueError('Invalid selection history')
        return state

    def package(self, name, expected=None, full=False):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Use an Application-relative package folder')
        folder = self.root / path
        if not folder.resolve().is_relative_to(self.root) or folder.is_symlink() or folder.is_junction():
            raise ValueError('Package must be an owned folder below Application')
        manifest = relative_file(folder, 'package.json')
        manifest_sha = digest(manifest)
        if expected and expected != manifest_sha:
            raise ValueError('Selected package manifest changed; select and validate again')
        release = json.loads(manifest.read_text('utf-8'))
        if release.get('schema') != 'xnby.zhumadian.release.v1':
            raise ValueError('Unsupported package schema')
        executable = release['activeExecutable']
        if '/' in executable or '\\' in executable:
            raise ValueError('Editor executable must be at package root')
        required = {executable, 'apps/landscape_web/dist/viewer.js', 'tools/landscape_web_server.py'}
        records = release['files']
        if len({r['path'] for r in records}) != len(records):
            raise ValueError('Duplicate package file record')
        if not required.issubset({r['path'] for r in records}):
            raise ValueError('EXE and WEB must both be hash-bound')
        for record in records:
            if full or record['path'] in required:
                target = relative_file(folder, record['path'])
                if target.stat().st_size != record['bytes'] or digest(target) != record['sha256']:
                    raise ValueError('Package content changed: ' + record['path'])
        return folder, release, manifest_sha

    @contextmanager
    def writer(self):
        self.state.parent.mkdir(parents=True, exist_ok=True)
        lock = self.state.with_name(self.state.name + '.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise RuntimeError('Selection writer already exists; inspect its process before recovery') from error
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(str(os.getpid())); stream.flush(); os.fsync(stream.fileno())
            yield
        finally:
            lock.unlink()

    def write(self, state):
        pending = self.state.with_name(self.state.name + '.' + uuid.uuid4().hex + '.pending')
        try:
            with pending.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(state, stream, ensure_ascii=False, indent=2)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(pending, self.state)
        finally:
            pending.unlink(missing_ok=True)

    def select(self, package, layers, database, expected_revision, candidate=False):
        # Never copy packaged project seeds over shared user data.
        layers = Path(layers).resolve(); database = Path(database).resolve()
        if not layers.is_file() or layers == database:
            raise ValueError('A separate, existing shared layer file is required')
        with self.writer():
            state = self.read()
            if state['revision'] != expected_revision:
                raise ValueError('Selection revision conflict')
            folder, release, sha = self.package(package, full=True)
            if any(path.is_relative_to(folder.resolve()) or path.is_relative_to(self.root/'Packages') for path in (layers,database)):
                raise ValueError('Shared data must stay outside package folders')
            if not candidate and not (release.get('verified') is True or release.get('verifiedAt')):
                raise ValueError('Candidate package requires explicit candidate selection')
            selected = {'package': folder.relative_to(self.root).as_posix(), 'manifestSha256': sha,
                        'editorVersion': release['editorVersion'], 'webVersion': release['webVersion'],
                        'apiVersion': release['apiVersion'], 'candidate': candidate,
                        'data': {k: Path(os.path.relpath(v, self.root)).as_posix()
                                 for k, v in [('layers', layers), ('database', database)]}}
            history = (state['history'] + [state['selected']])[-20:] if state['selected'] else []
            result = {'schema': SCHEMA, 'revision': state['revision'] + 1,
                      'selected': selected, 'history': history}
            self.write(result)
            return result

    def rollback(self, expected_revision):
        with self.writer():
            state = self.read()
            if state['revision'] != expected_revision:
                raise ValueError('Selection revision conflict')
            if not state['history']:
                raise ValueError('No previous selection')
            previous = state['history'][-1]
            self.package(previous['package'], previous['manifestSha256'], full=True)
            # Data binding belongs to the installation, not the historical version.
            previous = dict(previous, data=state['selected']['data'])
            result = {'schema': SCHEMA, 'revision': state['revision'] + 1,
                      'selected': previous, 'history': state['history'][:-1]}
            self.write(result)
            return result

    def plan(self, kind, port=8767, extra=()):
        state = self.read(); selected = state['selected']
        if selected is None:
            raise ValueError('No selected release')
        if not 1 <= port <= 65535:
            raise ValueError('Invalid port')
        if any(arg.split('=', 1)[0] in ('--layers', '--layer-database', '--host', '--port') for arg in extra):
            raise ValueError('Shared data and server binding cannot be overridden')
        folder, release, _ = self.package(selected['package'], selected['manifestSha256'])
        layers = (self.root / selected['data']['layers']).resolve()
        database = (self.root / selected['data']['database']).resolve()
        if not layers.is_file():
            raise ValueError('Shared layers missing')
        if kind == 'editor':
            command = [str(folder / release['activeExecutable']), '--layers=' + str(layers), *extra]
        elif kind == 'web':
            python = relative_file(folder, 'runtime/python/python.exe' if os.name == 'nt' else 'runtime/python/bin/python3')
            server = relative_file(folder, 'tools/landscape_web_server.py')
            command = [str(python), '-X', 'utf8', str(server), '--host', '127.0.0.1',
                       '--port', str(port), '--layers', str(layers), '--layer-database', str(database), *extra]
        else:
            raise ValueError('Unknown application kind')
        return {'revision': state['revision'], 'selected': selected, 'cwd': str(folder), 'command': command}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, required=True)
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('show')
    choose = sub.add_parser('select'); choose.add_argument('package')
    choose.add_argument('--layers', type=Path, required=True); choose.add_argument('--database', type=Path, required=True)
    choose.add_argument('--expected-revision', type=int, required=True); choose.add_argument('--candidate', action='store_true')
    back = sub.add_parser('rollback'); back.add_argument('--expected-revision', type=int, required=True)
    for action in ('plan', 'run'):
        execute = sub.add_parser(action); execute.add_argument('kind', choices=('editor', 'web'))
        execute.add_argument('--port', type=int, default=8767)
    a, extra = p.parse_known_args()
    if extra and a.action not in ('plan', 'run'): p.error('Unrecognized arguments: ' + ' '.join(extra))
    catalog = Catalog(ROOT, a.state)
    if a.action == 'show': result = catalog.read()
    elif a.action == 'select': result = catalog.select(a.package, a.layers, a.database, a.expected_revision, a.candidate)
    elif a.action == 'rollback': result = catalog.rollback(a.expected_revision)
    else:
        extra = extra[1:] if extra[:1] == ['--'] else extra
        result = catalog.plan(a.kind, a.port, extra)
        if a.action == 'run':
            print(json.dumps(result, ensure_ascii=False), flush=True)
            return subprocess.call(result['command'], cwd=result['cwd'])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
