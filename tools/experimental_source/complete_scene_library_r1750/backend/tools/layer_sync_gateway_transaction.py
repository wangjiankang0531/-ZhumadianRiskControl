"""Journaled single-file gateway update; no automatic installation or startup.

Callers supply real owner revalidation, syntax checks, reload and live probes.
Windows ReplaceFile retains the file actually displaced, so a racing writer is
detected before reload. This is not an OS compare-and-swap primitive.
"""
import ctypes
from contextlib import contextmanager
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

from tools.layer_sync_server_owner import loads, plain, read, sha


class RecoveryRequired(ValueError):
    pass


def _port(value):
    if type(value) is not int or not 1024 <= value <= 65535:
        raise ValueError('EXPLICIT_SYNC_PORT_REQUIRED')
    return value


def route_candidate(original, port, nonce, *, project_files=False,project_scenes=False):
    """Insert one exact route in the server containing the existing serv mount.

    Tokenization understands quoted values, escapes and comments; arbitrary
    unsupported structure is rejected rather than searching inside text values.
    All original bytes outside the insertion remain byte-for-byte intact.
    """
    if type(project_files)is not bool or type(project_scenes)is not bool:raise ValueError('EXPLICIT_PROJECT_FILES_MODE_REQUIRED')
    _port(port)
    if not re.fullmatch('[0-9a-f]{32}', nonce):
        raise ValueError('EXPLICIT_ROUTE_ID_REQUIRED')
    if not isinstance(original, bytes) or len(original) > 1048576:
        raise ValueError('BOUNDED_NGINX_CONFIG_REQUIRED')
    text = original.decode('utf-8-sig')
    if '/zhumadian/api/spatial-sync/' in text or 'XNBY-LAYER-SYNC' in text:
        raise ValueError('EXISTING_SYNC_ROUTE_REQUIRES_EXPLICIT_UPDATE')
    # Tokens retain source offsets. Nginx strings/comments must not create blocks.
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text[i] == '#':
            i = text.find('\n', i)
            if i < 0:
                break
            continue
        start = i
        if text[i] in '{};':
            tokens.append((text[i], start, True))
            i += 1
            continue
        word = []
        quote = None
        quoted = False
        while i < len(text):
            char = text[i]
            if char == '\\':
                if i + 1 >= len(text):
                    raise ValueError('UNTERMINATED_NGINX_ESCAPE')
                word.extend(text[i:i+2])
                i += 2
                continue
            if quote:
                if char == quote:
                    quote = None
                else:
                    word.append(char)
                i += 1
                continue
            if char in ('"', "'"):
                quoted = True
                quote = char
                i += 1
                continue
            if char.isspace() or char in '{};#':
                break
            word.append(char)
            i += 1
        if quote or not word and not quoted:
            raise ValueError('UNSUPPORTED_NGINX_TOKEN')
        tokens.append((''.join(word), start, False))
    stack = []
    pending = []
    anchors = []
    server_listeners = {}
    for token, offset, structural in tokens:
        if structural and token == '{':
            header = tuple(t for t, _ in pending)
            if not header:
                raise ValueError('INVALID_NGINX_BLOCK')
            if header == ('server',):
                if not stack or stack[-1][0] != ('http',):
                    raise ValueError('EXPECTED_HTTP_SERVER_REQUIRED')
                server_listeners[offset] = []
            if header == ('location', '^~', '/zhumadian/api/serv/'):
                if not stack or stack[-1][0] != ('server',):
                    raise ValueError('SERV_ROUTE_MUST_BELONG_TO_SERVER')
                anchors.append((pending[0][1], stack[-1][1]))
            stack.append((header, offset))
            pending = []
        elif structural and token == ';':
            if pending and pending[0][0] == 'listen' and stack and stack[-1][0] == ('server',):
                server_listeners[stack[-1][1]].append(tuple(t for t, _ in pending[1:]))
            pending = []
        elif structural and token == '}':
            if pending or not stack:
                raise ValueError('INVALID_NGINX_BLOCK')
            stack.pop()
        else:
            pending.append((token, offset))
    if stack or pending or len(anchors) != 1:
        raise ValueError('UNIQUE_EXISTING_PROJECT_SERV_ROUTE_REQUIRED')
    offset, server = anchors[0]
    listeners = server_listeners[server]
    if len(listeners) != 1 or len(listeners[0]) != 1 or not re.fullmatch('127\\.0\\.0\\.1:[1-9][0-9]{3,4}', listeners[0][0]):
        raise ValueError('SINGLE_LOOPBACK_PROJECT_SERVER_REQUIRED')
    gateway_port = int(listeners[0][0].split(':')[1])
    if gateway_port == port:
        raise ValueError('GATEWAY_CANNOT_PROXY_TO_ITSELF')
    line = text.rfind('\n', 0, offset) + 1
    if text[line:offset].strip():
        raise ValueError('SERV_ROUTE_MUST_START_ON_OWN_LINE')
    newline = '\r\n' if '\r\n' in text else '\n'
    fragment = [' # XNBY-LAYER-SYNC ' + nonce]
    routes=[('=', 'v1/project/layers','GET'),('=', 'v2/project/layers','GET POST')]
    if project_files:routes.extend([('=', 'v2/project/files','GET POST'),('^~', 'v2/project/files/','GET')])
    if project_scenes:routes.extend([('=', 'v2/project/scenes','GET POST'),('^~', 'v2/project/scenes/','GET')])
    for match,route,methods in routes:
        fragment.extend([
            ' location '+match+' /zhumadian/api/spatial-sync/'+route+' {',
            '  client_max_body_size 16m;',
            '  proxy_pass http://127.0.0.1:' + str(port) + '/'+route+';',
            '  proxy_http_version 1.1;',
            '  proxy_set_header Host 127.0.0.1:' + str(port) + ';',
            '  proxy_set_header Authorization $http_authorization;',
            '  proxy_set_header X-XNBY-Sync-Account $http_x_xnby_sync_account;',
            '  proxy_set_header Connection "";',
            '  proxy_request_buffering on;',
            '  proxy_buffering off;',
            '  proxy_cache off;',
            '  proxy_next_upstream off;',
            '  proxy_intercept_errors off;',
            '  proxy_connect_timeout 3s;',
            '  proxy_read_timeout 15s;',
            '  proxy_send_timeout 15s;',
            '  add_header X-XNBY-Layer-Sync-Deployment ' + nonce + ' always;',
            '  limit_except '+methods+' { deny all; }',
            ' }',
        ])
    # UTF-8 BOM and every byte of the original are preserved.
    byte_offset = len(text[:line].encode('utf-8')) + (3 if original.startswith(b'\xef\xbb\xbf') else 0)
    return original[:byte_offset] + (newline.join(fragment) + newline).encode('utf-8') + original[byte_offset:]


def _write_new(path, raw):
    with plain(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _journal(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    pending = path.with_name(path.name + '.' + secrets.token_hex(16) + '.pending')
    try:
        _write_new(pending, raw)
        os.replace(pending, plain(path))
    finally:
        if pending.exists():
            pending.unlink()


def replace_preserving(target, replacement, displaced):
    """Atomic Windows replacement retains the exact displaced file in displaced."""
    if os.name != 'nt':
        raise ValueError('WINDOWS_REPLACE_REQUIRED')
    target, replacement, displaced = map(plain, (target, replacement, displaced))
    if displaced.exists() or target.anchor != replacement.anchor or target.anchor != displaced.anchor:
        raise ValueError('FRESH_SAME_VOLUME_DISPLACED_PATH_REQUIRED')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.ReplaceFileW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                    wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
    kernel.ReplaceFileW.restype = wintypes.BOOL
    if not kernel.ReplaceFileW(str(target), str(replacement), str(displaced), 0, None, None):
        raise OSError(ctypes.get_last_error(), 'GATEWAY_REPLACE_FAILED')


def _owner_key(value):
    # Workers can change after a successful graceful reload; master/controller cannot.
    if not isinstance(value, dict) or not {'controller', 'gatewayMaster'} <= set(value):
        raise ValueError('VERIFIED_OWNER_IDENTITIES_REQUIRED')
    result = {}
    for name in ('controller', 'gatewayMaster'):
        row = value[name]
        if (not isinstance(row, dict) or set(row) != {'pid', 'creation'} or type(row['pid']) is not int
                or not 0 < row['pid'] < 2**32 or not isinstance(row['creation'], str)
                or not re.fullmatch('[0-9]{1,20}', row['creation'])):
            raise ValueError('VERIFIED_OWNER_IDENTITIES_REQUIRED')
        result[name] = row
    return result


def checked_target(app,config,root,kind):
    if any('..' in path.parts for path in (app,config,root)):
        raise ValueError('CANONICAL_INGRESS_TRANSACTION_PATH_REQUIRED')
    if kind=='gateway':
        relative=config.relative_to(app/'UserData/OriginalServer/runs')
        if len(relative.parts)!=3 or not re.fullmatch('j[1-9][0-9]{0,3}',relative.parts[0]) or relative.parts[1:]!=('gateway','nginx.conf'):
            raise ValueError('EXACT_PROJECT_GATEWAY_PATH_REQUIRED')
    elif kind=='iis-header':
        if config!=app/'iis/App_Code/XnbyReferenceProxy.cs':raise ValueError('EXACT_PROJECT_IIS_PROXY_PATH_REQUIRED')
    else:raise ValueError('EXPLICIT_INGRESS_FILE_KIND_REQUIRED')
    if root.is_relative_to(config.parent) or root.anchor!=config.anchor:
        raise ValueError('SEPARATE_SAME_VOLUME_TRANSACTION_REQUIRED')


class GatewayTransaction:
    """A reviewable plan plus durable phases; reopening requires its exact plan SHA.

    probe(configSHA) must perform current owner verification, never load a cached
    pass report. syntax(path), reload() and live(mode, nonce) must return bool.
    """
    def __init__(self, root, plan_sha, probe, syntax, reload, live):
        self.root = plain(root)
        raw = read(self.root / 'plan.json', 65536)
        if sha(raw) != plan_sha:
            raise ValueError('TRANSACTION_PLAN_CHANGED')
        self.plan = loads(raw)
        p = self.plan
        if set(p) != {'schema', 'application', 'config', 'before', 'after', 'owner', 'nonce','kind'} or p['schema'] != 'xnby.layer-sync.gateway-plan.v2':
            raise ValueError('INVALID_GATEWAY_PLAN')
        self.app = plain(p['application'])
        self.config = plain(p['config'])
        checked_target(self.app,self.config,self.root,p['kind'])
        if not re.fullmatch('[0-9a-f]{32}', p['nonce']):
            raise ValueError('INVALID_GATEWAY_PLAN')
        _owner_key(p['owner'])
        self.before = read(self.root / 'before.conf')
        self.after = read(self.root / 'after.conf')
        if sha(self.before) != p['before'] or sha(self.after) != p['after']:
            raise ValueError('TRANSACTION_PREIMAGE_OR_CANDIDATE_CHANGED')
        self.probe, self.syntax, self.reload, self.live = probe, syntax, reload, live
        self._leased = False
        self.status = loads(read(self.root / 'journal.json', 65536))
        if (not isinstance(self.status, dict) or self.status.get('schema') != 'xnby.layer-sync.gateway-journal.v1'
                or self.status.get('planSHA256') != plan_sha):
            raise ValueError('TRANSACTION_JOURNAL_CHANGED')

    @classmethod
    def prepare(cls, application, config, root, expected_sha, candidate, nonce, probe, syntax, reload, live, *, kind="gateway"):
        config, root, app = map(plain, (config, root, application))
        if root.exists():
            raise ValueError('NEW_TRANSACTION_DIRECTORY_REQUIRED')
        before = read(config)
        if sha(before) != expected_sha or not isinstance(candidate, bytes) or len(candidate) > 1048576 or candidate == before:
            raise ValueError('MATCHING_PREIMAGE_AND_DISTINCT_CANDIDATE_REQUIRED')
        owner = _owner_key(probe(expected_sha))
        if read(config) != before:
            raise ValueError('GATEWAY_CHANGED_DURING_PLAN')
        plan = {'schema': 'xnby.layer-sync.gateway-plan.v2', 'kind':kind,'application': str(app), 'config': str(config),
                'before': expected_sha, 'after': sha(candidate), 'owner': owner, 'nonce': nonce}
        checked_target(app,config,root,kind)
        raw = json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()
        root.mkdir(parents=True)
        _write_new(root / 'before.conf', before)
        _write_new(root / 'after.conf', candidate)
        _write_new(root / 'plan.json', raw)
        _journal(root / 'journal.json', {'schema': 'xnby.layer-sync.gateway-journal.v1',
                                        'planSHA256': sha(raw), 'phase': 'prepared'})
        return cls(root, sha(raw), probe, syntax, reload, live)

    def _save(self, phase):
        self.status['phase'] = phase
        _journal(self.root / 'journal.json', self.status)

    @contextmanager
    def _lease(self):
        if self._leased:
            yield
            return
        import msvcrt
        with plain(self.root / 'owner.lock').open('a+b') as stream:
            if not stream.seek(0, os.SEEK_END):
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                actual = loads(read(self.root / 'journal.json', 65536))
                if actual != self.status:
                    raise RecoveryRequired('TRANSACTION_ADVANCED_REOPEN_REQUIRED')
                self._leased = True
                yield
            finally:
                self._leased = False
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def _check(self, expected):
        if sha(read(self.config)) != expected:
            raise RecoveryRequired('GATEWAY_CHANGED_OUTSIDE_TRANSACTION')
        if _owner_key(self.probe(expected)) != self.plan['owner']:
            raise RecoveryRequired('GATEWAY_OWNER_CHANGED')
        if sha(read(self.config)) != expected:
            raise RecoveryRequired('GATEWAY_CHANGED_DURING_OWNER_CHECK')

    def _replace(self, raw, expected, label):
        self._check(expected)
        pending = self.root / (label + '.pending')
        displaced = self.root / (label + '.displaced')
        if pending.exists() or displaced.exists():
            raise RecoveryRequired('PRIOR_REPLACEMENT_ARTIFACT_RETAINED')
        _write_new(pending, raw)
        self._check(expected)
        replace_preserving(self.config, pending, displaced)
        actual = read(displaced)
        if sha(actual) != expected:
            # No explicit reload callback has occurred. IIS App_Code can activate
            # automatically on a file change; that possibility is journaled.
            # Retain the actual competing bytes and stop for publisher review.
            self.status['unexpectedDisplacedSHA256'] = sha(actual)
            self._save('concurrent-replacement-detected')
            self._check(sha(raw))
            restore = self.root / (label + '.concurrent-restore.pending')
            saved = self.root / (label + '.concurrent-restore.displaced')
            _write_new(restore, actual)
            replace_preserving(self.config, restore, saved)
            if sha(read(saved)) != sha(raw):
                raise RecoveryRequired('ADDITIONAL_RACING_WRITE_PRESERVED')
            self._save('concurrent-write-restored-without-explicit-reload' if self.plan['kind']=='iis-header' else 'concurrent-write-restored-without-reload')
            raise RecoveryRequired('CONCURRENT_REPLACEMENT_REQUIRES_REVIEW')
        if read(self.config) != raw:
            raise RecoveryRequired('GATEWAY_CHANGED_AFTER_REPLACEMENT')

    def apply(self):
        with self._lease():
            return self._apply()

    def _apply(self):
        if self.status['phase'] != 'prepared':
            raise ValueError('PREPARED_TRANSACTION_REQUIRED')
        try:
            self._check(self.plan['before'])
            if self.syntax(self.root / 'after.conf') is not True:
                raise ValueError('CANDIDATE_SYNTAX_REJECTED')
            self._check(self.plan['before'])
            self._save('install-intent')
            if self.plan['kind']=='iis-header':
                self.status['automaticIISActivationMayHaveOccurred']=True
                self._save('install-intent')
            self._replace(self.after, self.plan['before'], 'install')
            self._save('installed')
            self._check(self.plan['after'])
            self._save('reload-intent')
            if self.reload() is not True:
                raise ValueError('RELOAD_NOT_CONFIRMED')
            self._save('reload-requested')
            if self.live('installed', self.plan['nonce']) is not True:
                raise ValueError('NEW_ROUTE_NOT_OBSERVED')
            self._check(self.plan['after'])
            self._save('validated')
            return dict(self.status)
        except RecoveryRequired:
            # Foreign bytes/owner are never overwritten by ordinary rollback.
            if self.status['phase'] not in ('concurrent-write-restored-without-reload','concurrent-write-restored-without-explicit-reload'):
                self._save('recovery-required')
            raise
        except Exception:
            self.recover()
            raise

    def recover(self):
        """Explicit recovery after failure/crash, retaining all data and evidence."""
        with self._lease():
            return self._recover()

    def _recover(self):
        phase = self.status['phase']
        if phase in ('restored', 'aborted-before-install'):
            return dict(self.status)
        try:
            current = sha(read(self.config))
            for label, expected in [('install', self.plan['before']), ('restore', self.plan['after'])]:
                displaced = self.root / (label + '.displaced')
                if displaced.exists() and sha(read(displaced)) != expected:
                    raise RecoveryRequired('UNEXPECTED_DISPLACED_FILE_REQUIRES_REVIEW')
            if current == self.plan['before'] and phase in ('prepared', 'install-intent'):
                self._check(self.plan['before'])
                self._save('aborted-before-install')
                return dict(self.status)
            # An install-intent can survive a crash between ReplaceFile and journal.
            if current != self.plan['after'] and not (current == self.plan['before'] and phase in ('restore-intent', 'restore-installed', 'restore-reload-intent')):
                raise RecoveryRequired('UNKNOWN_CURRENT_GATEWAY_RETAINED')
            self._check(current)
            if self.syntax(self.root / 'before.conf') is not True:
                raise RecoveryRequired('RESTORE_SYNTAX_NOT_VERIFIED')
            if current == self.plan['after']:
                self._save('restore-intent')
                self._replace(self.before, self.plan['after'], 'restore')
            self._save('restore-installed')
            self._check(self.plan['before'])
            self._save('restore-reload-intent')
            if self.reload() is not True or self.live('restored', self.plan['nonce']) is not True:
                raise RecoveryRequired('RESTORED_ROUTE_NOT_CONFIRMED')
            self._check(self.plan['before'])
            self._save('restored')
            return dict(self.status)
        except Exception:
            self._save('recovery-required')
            raise


class NginxCommands:
    """Existing nginx only. Query ownership immediately before each command."""
    def __init__(self, executable, executable_sha, prefix, config, check):
        self.executable, self.prefix, self.config = map(plain, (executable, prefix, config))
        self.pin, self.check = executable_sha, check

    def _run(self, config, option):
        self.check()
        with self.executable.open('rb') as stream:
            if hashlib_file(stream) != self.pin:
                raise RecoveryRequired('NGINX_EXECUTABLE_CHANGED')
        result = subprocess.run([str(self.executable), '-p', str(self.prefix) + os.sep,
                                 '-c', str(plain(config)), *option], cwd=self.prefix,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), close_fds=True)
        # No -T/config dump and no command stderr containing private paths in reports.
        self.check()
        return result.returncode == 0

    def syntax(self, candidate):
        return self._run(candidate, ['-t'])

    def reload(self):
        return self._run(self.config, ['-s', 'reload'])


def hashlib_file(stream):
    import hashlib
    return hashlib.file_digest(stream, 'sha256').hexdigest()
