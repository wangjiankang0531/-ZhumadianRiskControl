"""Capability-protected loopback RPC between the editor and its sync worker.

The local capability is unrelated to the public-project Authorization value.
Public credentials remain in memory; the private binding contains only the
local connection capability and the identity of this helper process.
"""
from collections import OrderedDict
import hashlib
import hmac
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time
from urllib.parse import urlsplit

from services.common import loads
from services.layer_sync_client import CheckpointError, TARGET
from services.layer_sync_state import SyncConflict
from services.layer_sync_identity import AccountIdentityMismatch
from services.layer_sync_transport import SyncHTTPError
from tools.landscape_layer_validation import validate_editor_layers

CAP_HEADER = 'X-XNBY-Layer-Sync'
MAX_BODY = 40 * 1048576
MAX_DOCUMENT = 16 * 1048576


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode()


class CredentialVault:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = None

    def get(self):
        with self._lock: return self._value

    def present(self):
        with self._lock: return self._value is not None

    @staticmethod
    def checked(value):
        if (not isinstance(value, str) or not value or value != value.strip() or len(value) > 16384
                or any(not 32 <= ord(c) <= 126 for c in value)):
            raise ValueError('INVALID_AUTHORIZATION_VALUE')
        return value

    def set(self,value):
        checked=self.checked(value)
        with self._lock: self._value = checked

    def clear(self):
        with self._lock: self._value = None


def checked_origin(value):
    if value == 'https://www.joinlinksmart.com': return value
    if not isinstance(value, str) or not re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}', value):
        raise ValueError('EXPLICIT_PROJECT_OR_LOOPBACK_ORIGIN_REQUIRED')
    if not 1 <= urlsplit(value).port <= 65535:
        raise ValueError('INVALID_LOCAL_ORIGIN')
    return value


class BridgeError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


class LayerSyncBridge(http.server.ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, client, vault, *, port=0, allowed_origins=(), credential_verifier=None, review_enabled=False, import_enabled=False):
        if type(port) is not int or not 0 <= port <= 65535: raise ValueError('INVALID_LOCAL_PORT')
        if type(review_enabled) is not bool: raise ValueError('INVALID_REVIEW_OPTION')
        if type(import_enabled) is not bool or import_enabled and not review_enabled: raise ValueError('INVALID_IMPORT_OPTION')
        self.import_enabled = import_enabled
        self.review_enabled = review_enabled
        self.review_requested = threading.Event()
        self.client, self.vault = client, vault
        self.credential_verifier = credential_verifier
        self.allowed_origins = frozenset(checked_origin(o) for o in allowed_origins)
        self.capability, self.instance_id = secrets.token_hex(32), secrets.token_hex(16)
        self.slots = threading.BoundedSemaphore(8)
        self.receipts = OrderedDict()
        self.mutation_lock = threading.Lock()
        super().__init__(('127.0.0.1', port), BridgeHandler)
        if review_enabled: self.allowed_origins = self.allowed_origins | {self.endpoint}

    @property
    def endpoint(self): return 'http://127.0.0.1:' + str(self.server_port)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close(); return
        try: super().process_request(request, address)
        except BaseException:
            self.slots.release(); raise

    def process_request_thread(self, request, address):
        try: super().process_request_thread(request, address)
        finally: self.slots.release()

    def handle_error(self, request, client_address):
        pass  # No request headers/body or credential-bearing exceptions in logs.


class BridgeHandler(http.server.BaseHTTPRequestHandler):
    server_version = 'XNBY-LayerSync-Bridge'
    def setup(self):
        super().setup(); self.connection.settimeout(8)

    def log_message(self, *args): pass

    def _origin(self):
        origins = self.headers.get_all('Origin', [])
        if origins and (len(origins) != 1 or origins[0] not in self.server.allowed_origins):
            raise BridgeError(403, 'LOCAL_ORIGIN_DENIED')
        return origins[0] if origins else None

    def _host(self):
        if self.client_address[0] != '127.0.0.1' or self.headers.get_all('Host', []) != ['127.0.0.1:' + str(self.server.server_port)]:
            raise BridgeError(403, 'LOCAL_HOST_DENIED')

    def _authorized(self):
        self._host(); self._origin()
        values = self.headers.get_all(CAP_HEADER, [])
        if (len(values) != 1 or not re.fullmatch('[0-9a-f]{64}', values[0])
                or not hmac.compare_digest(values[0], self.server.capability)):
            raise BridgeError(403, 'LOCAL_ACCESS_DENIED')

    def output(self, status, value=None, *, etag=None):
        raw = b'' if value is None else encode(value)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        if status not in (204, 304): self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Vary', 'Origin')
        origins = self.headers.get_all('Origin', [])
        if len(origins) == 1 and origins[0] in self.server.allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origins[0])
            self.send_header('Access-Control-Expose-Headers', 'ETag')
        if etag is not None: self.send_header('ETag', etag)
        self.end_headers()
        if self.command != 'HEAD' and raw: self.wfile.write(raw)

    def _body(self):
        if self.headers.get('Transfer-Encoding'):
            raise BridgeError(400, 'INVALID_REQUEST_FRAMING')
        lengths = self.headers.get_all('Content-Length', [])
        if len(lengths) != 1 or not re.fullmatch('[0-9]{1,8}', lengths[0]):
            raise BridgeError(400, 'CONTENT_LENGTH_REQUIRED')
        size = int(lengths[0])
        limit = 32768 if self.path in ('/v1/credentials','/v1/disconnect','/v1/conflict/compare','/v1/conflict/value') else MAX_BODY
        if not 1 <= size <= limit: raise BridgeError(413, 'LOCAL_REQUEST_TOO_LARGE')
        if self.headers.get_all('Content-Type', []) not in (['application/json'], ['application/json; charset=utf-8']):
            raise BridgeError(415, 'JSON_REQUIRED')
        chunks = []; count = 0; deadline = time.monotonic() + 8
        while count < size:
            if time.monotonic() > deadline: raise BridgeError(408, 'REQUEST_TIMEOUT')
            part = self.rfile.read1(min(16384, size - count))
            if not part: raise BridgeError(400, 'TRUNCATED_REQUEST')
            chunks.append(part); count += len(part)
        value = loads(b''.join(chunks))
        if not isinstance(value, dict): raise BridgeError(422, 'JSON_OBJECT_REQUIRED')
        return value

    @staticmethod
    def _document(value):
        validate_editor_layers(value)
        if len(encode(value)) > MAX_DOCUMENT: raise BridgeError(413, 'LAYER_DOCUMENT_TOO_LARGE')

    def _status(self):
        result = self.server.client.summary()
        result.update(instanceId=self.server.instance_id, target=TARGET, credentialPresent=self.server.vault.present())
        return result

    def _mutation(self, value):
        import_edit = self.path == '/v1/import/apply'
        project_choice = self.path == '/v1/resolve-project-choice'
        required = {'requestId', 'generation', 'side', 'acknowledgeWholeProject'} if project_choice else {'requestId', 'generation', 'choices' if self.path == '/v1/resolve-choices' else 'document'}
        if import_edit: required = {'requestId', 'generation', 'planId', 'choices'}
        allowed = required | ({'basisDocument'} if self.path == '/v1/edits' else set())
        if set(value) - allowed or not required <= set(value):
            raise BridgeError(422, 'INVALID_EDIT_FIELDS')
        request_id = value['requestId']
        if not isinstance(request_id, str) or not re.fullmatch('[0-9a-f]{32}', request_id):
            raise BridgeError(422, 'INVALID_REQUEST_ID')
        if type(value['generation']) is not int or not 0 <= value['generation'] < 2**63:
            raise BridgeError(422, 'INVALID_EDITOR_GENERATION')
        if 'document' in value: self._document(value['document'])
        if 'basisDocument' in value: self._document(value['basisDocument'])
        digest = hashlib.sha256(encode(value)).hexdigest()
        key = (self.path, request_id)
        with self.server.mutation_lock:
            receipt = self.server.receipts.get(key)
            if receipt is not None:
                if receipt['digest'] != digest: raise BridgeError(409, 'REQUEST_ID_REUSED')
                self.server.receipts.move_to_end(key)
                return receipt['status'], dict(receipt['result'], duplicate=True)
            try:
                if import_edit:
                    self.server.client.import_apply(value['planId'], value['generation'], value['choices'])
                elif self.path == '/v1/edits':
                    self.server.client.edit(value['document'], value['generation'], basis_document=value.get('basisDocument'))
                elif project_choice:
                    self.server.client.resolve_project_choice(value['side'], value['generation'], acknowledge_whole_project=value['acknowledgeWholeProject'])
                elif self.path == '/v1/resolve-choices':
                    self.server.client.resolve_choices(value['choices'], value['generation'])
                else:
                    self.server.client.resolve(value['document'], value['generation'])
                status = 200
                result = {'requestId': request_id, 'acceptedGeneration': self.server.client.summary()['generation'],
                          'draftSaved': True, 'duplicate': False}
            except SyncConflict:
                status = 409
                saved = self.path == '/v1/edits'
                result = {'requestId': request_id, 'error': 'EDIT_CONFLICT' if saved else 'RESOLUTION_CONFLICT', 'draftSaved': saved,
                          'acceptedGeneration': self.server.client.summary()['generation'], 'duplicate': False}
            self.server.receipts[key] = {'digest': digest, 'status': status, 'result': result}
            if len(self.server.receipts) > 256: self.server.receipts.popitem(last=False)
            return status, result

    def _review_asset(self):
        if not self.server.review_enabled: raise BridgeError(404, 'NOT_FOUND')
        from services.layer_sync_conflict_page import asset, CSP
        raw, kind = asset(self.path)
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(raw)

    def perform(self):
        try:
            self._authorized()
            if self.command in ('GET', 'HEAD'):
                if self.headers.get('Transfer-Encoding') or self.headers.get_all('Content-Length', []) not in ([], ['0']):
                    raise BridgeError(400, 'GET_BODY_NOT_ALLOWED')
                if self.path in ('/review/', '/review/app.mjs', '/review/import.mjs'): return self._review_asset()
                if self.path == '/v1/import/status':
                    return self.output(200, {'enabled': self.server.import_enabled, **self.server.client.import_status()})
                if self.path == '/v1/status': return self.output(200, self._status())
                if self.path == '/v1/document':
                    summary = self.server.client.summary()
                    tag = '"' + self.server.instance_id + ':' + str(summary['generation']) + '"'
                    if self.headers.get_all('If-None-Match', []) == [tag]: return self.output(304, etag=tag)
                    view = self.server.client.view()
                    tag = '"' + self.server.instance_id + ':' + str(view['generation']) + '"'
                    return self.output(200, {k: view[k] for k in ('document', 'generation', 'revision')}, etag=tag)
                if self.path.startswith(('/v1/receipts/', '/v1/choice-receipts/', '/v1/project-choice-receipts/', '/v1/import-receipts/')):
                    prefix = '/v1/import-receipts/' if self.path.startswith('/v1/import-receipts/') else '/v1/project-choice-receipts/' if self.path.startswith('/v1/project-choice-receipts/') else '/v1/choice-receipts/' if self.path.startswith('/v1/choice-receipts/') else '/v1/receipts/'
                    request_id = self.path[len(prefix):]
                    if not re.fullmatch('[0-9a-f]{32}', request_id):
                        raise BridgeError(404, 'NOT_FOUND')
                    with self.server.mutation_lock:
                        mutation = '/v1/import/apply' if prefix == '/v1/import-receipts/' else '/v1/resolve-project-choice' if prefix == '/v1/project-choice-receipts/' else '/v1/resolve-choices' if prefix == '/v1/choice-receipts/' else '/v1/edits'
                        item = self.server.receipts.get((mutation, request_id))
                        # Lookup does not extend the bounded receipt lifetime or mutate edits.
                        result = {'found': False} if item is None else {
                            'found': True, 'status': item['status'], 'receipt': dict(item['result'])}
                    return self.output(200, result)
                if self.path == '/v1/conflict':
                    view = self.server.client.view()
                    return self.output(200, {k: view[k] for k in ('generation', 'conflict', 'coordinatorDocument')})
                raise BridgeError(404, 'NOT_FOUND')
            if self.command != 'POST': raise BridgeError(405, 'METHOD_NOT_ALLOWED')
            if self.path.startswith('/v1/import/') and not self.server.import_enabled:
                raise BridgeError(403, 'IMPORT_NOT_ENABLED')
            if self.path in ('/v1/import/prepare', '/v1/import/compare', '/v1/import/value'):
                value = self._body()
                if self.path == '/v1/import/prepare':
                    if set(value) != {'fileData', 'fileSHA256', 'fileName', 'generation'}: raise BridgeError(422, 'INVALID_IMPORT_FIELDS')
                    result = self.server.client.import_prepare(value['fileData'], value['fileSHA256'], value['fileName'], value['generation'])
                elif self.path == '/v1/import/compare':
                    if set(value) - {'planId', 'generation', 'offset', 'limit'} or not {'planId', 'generation'} <= set(value): raise BridgeError(422, 'INVALID_IMPORT_FIELDS')
                    result = self.server.client.import_compare(value['planId'], value['generation'], offset=value.get('offset', 0), limit=value.get('limit', 8))
                else:
                    if set(value) != {'planId', 'generation', 'path', 'side'}: raise BridgeError(422, 'INVALID_IMPORT_FIELDS')
                    result = self.server.client.import_value(value['planId'], value['generation'], value['path'], value['side'])
                return self.output(200, result)
            if self.path not in ('/v1/import/apply', '/v1/edits', '/v1/resolve', '/v1/resolve-choices', '/v1/resolve-project-choice', '/v1/review/open', '/v1/conflict/compare', '/v1/conflict/value', '/v1/credentials', '/v1/disconnect'):
                raise BridgeError(404, 'NOT_FOUND')
            value = self._body()
            if self.path in ('/v1/import/apply', '/v1/edits', '/v1/resolve', '/v1/resolve-choices', '/v1/resolve-project-choice'):
                status, result = self._mutation(value)
                return self.output(status, result)
            if self.path == '/v1/review/open':
                if value: raise BridgeError(422, 'EMPTY_OBJECT_REQUIRED')
                if not self.server.review_enabled: raise BridgeError(503, 'REVIEW_NOT_ENABLED')
                self.server.review_requested.set()
                return self.output(200, {'requested': True})
            if self.path == '/v1/conflict/compare':
                if set(value) - {'generation', 'offset', 'limit'} or 'generation' not in value:
                    raise BridgeError(422, 'INVALID_CONFLICT_FIELDS')
                return self.output(200, self.server.client.compare_conflict(value['generation'],
                                   offset=value.get('offset', 0), limit=value.get('limit', 8)))
            if self.path == '/v1/conflict/value':
                if set(value) != {'generation', 'path', 'side'}:
                    raise BridgeError(422, 'INVALID_CONFLICT_FIELDS')
                return self.output(200, self.server.client.conflict_value(value['generation'], value['path'], value['side']))
            if self.path == '/v1/credentials':
                if set(value) != {'authorization'}: raise BridgeError(422, 'INVALID_CREDENTIAL_FIELDS')
                authorization = CredentialVault.checked(value['authorization'])
                with self.server.mutation_lock:
                    self.server.client.pause(login_required=True)
                    self.server.vault.clear()
                    if self.server.credential_verifier is None:
                        raise BridgeError(503,'ACCOUNT_VERIFIER_REQUIRED')
                    try: self.server.credential_verifier(authorization)
                    except AccountIdentityMismatch:
                        raise BridgeError(409,'ACCOUNT_SWITCH_REQUIRES_NEW_HELPER') from None
                    except SyncHTTPError as error:
                        raise BridgeError(error.status,'ACCOUNT_VERIFICATION_FAILED') from None
                    except (OSError,ValueError,TypeError):
                        raise BridgeError(503,'ACCOUNT_VERIFICATION_UNAVAILABLE') from None
                    self.server.vault.set(authorization)
                    self.server.client.credentials_changed()
                return self.output(200, {'updated': True, 'verification': 'verified'})
            if value: raise BridgeError(422, 'EMPTY_OBJECT_REQUIRED')
            with self.server.mutation_lock:
                self.server.vault.clear(); self.server.client.pause(login_required=True)
            return self.output(200, {'disconnected': True})
        except BridgeError as error: return self.output(error.status, {'error': error.code})
        except CheckpointError: return self.output(507, {'error': 'LOCAL_CHECKPOINT_WRITE_FAILED', 'draftSaved': False})
        except ValueError as error:
            code = error.args[0] if error.args else None
            if code in ('INVALID_EDITOR_GENERATION', 'EDITOR_BASIS_REQUIRED', 'EDITOR_INITIAL_SELECTION_REQUIRED',
                        'CURRENT_CONFLICT_GENERATION_REQUIRED', 'CONFLICT_REQUIRES_RESOLUTION',
                        'CONFLICT_BASIS_UNAVAILABLE', 'EXACT_CONFLICT_CHOICES_REQUIRED', 'CONFLICT_CHOICES_INCOMPATIBLE',
                        'EXPLICIT_WHOLE_PROJECT_CHOICE_REQUIRED', 'ITEM_CHOICES_REQUIRED',
                        'CURRENT_IMPORT_GENERATION_REQUIRED','IMPORT_CURRENT_PROJECT_REQUIRED','RESOLVE_CONFLICT_BEFORE_IMPORT',
                        'IMPORT_PREVIEW_EXPIRED','IMPORT_PLAN_ALREADY_APPLIED','EXACT_IMPORT_CHOICES_REQUIRED'):
                return self.output(409, {'error': code, 'draftSaved': False})
            if code in ('IMPORT_FILE_TOO_LARGE','IMPORT_RESULT_TOO_LARGE','IMPORT_PREVIEW_TOO_LARGE','IMPORT_RESULT_LIMIT_EXCEEDED'):
                return self.output(413, {'error': code, 'draftSaved': False})
            if code in ('INVALID_IMPORT_DOCUMENT','IMPORT_FILE_CHANGED','IMPORT_BASENAME_REQUIRED','IMPORT_FILE_HASH_REQUIRED','INVALID_IMPORT_ENCODING','INVALID_IMPORT_PATH','INVALID_IMPORT_PAGE','INVALID_IMPORT_CHOICES'):
                return self.output(422, {'error': code, 'draftSaved': False})
            return self.output(422, {'error': 'INVALID_LOCAL_SYNC_DATA', 'draftSaved': False})
        except (OSError, TimeoutError): return self.output(503, {'error': 'LOCAL_SYNC_UNAVAILABLE'})
        except Exception: return self.output(500, {'error': 'LOCAL_SYNC_INTERNAL_ERROR'})

    def do_GET(self): self.perform()
    def do_HEAD(self): self.perform()
    def do_POST(self): self.perform()
    do_PUT = do_PATCH = do_DELETE = do_POST

    def do_OPTIONS(self):
        try:
            self._host(); origin = self._origin()
            methods = self.headers.get_all('Access-Control-Request-Method', [])
            if origin is None or len(methods) != 1 or methods[0] not in ('GET', 'HEAD', 'POST'):
                raise BridgeError(403, 'LOCAL_PREFLIGHT_DENIED')
            receipt_route = re.fullmatch('/v1/(?:(?:project-)?choice-|import-)?receipts/[0-9a-f]{32}', self.path)
            if not receipt_route and self.path not in ('/v1/import/status','/v1/import/prepare','/v1/import/compare','/v1/import/value','/v1/import/apply','/v1/status','/v1/document','/v1/conflict','/v1/edits','/v1/resolve',
                    '/v1/resolve-choices','/v1/resolve-project-choice','/v1/review/open','/v1/conflict/compare','/v1/conflict/value','/v1/credentials','/v1/disconnect'):
                raise BridgeError(404, 'NOT_FOUND')
            headers = self.headers.get_all('Access-Control-Request-Headers', [])
            if len(headers) > 1: raise BridgeError(403, 'LOCAL_PREFLIGHT_DENIED')
            requested = {v.strip().lower() for v in headers[0].split(',')} if headers else set()
            if requested - {'content-type', CAP_HEADER.lower(), 'if-none-match'}:
                raise BridgeError(403, 'LOCAL_PREFLIGHT_DENIED')
            self.send_response(204)
            self.send_header('Cache-Control','no-store')
            self.send_header('Access-Control-Allow-Origin',origin)
            self.send_header('Access-Control-Allow-Methods','GET, HEAD, POST')
            self.send_header('Access-Control-Allow-Headers',CAP_HEADER+', Content-Type, If-None-Match')
            self.send_header('Vary','Origin');self.end_headers()
        except BridgeError as error:self.output(error.status,{'error':error.code})


def process_creation(pid):
    """Read process birth identity without signals, termination, or CIM commands."""
    if type(pid) is not int or not 0 < pid <= 2**32-1: raise ValueError('INVALID_BINDING_OWNER')
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        handle = kernel.OpenProcess(0x1000 | 0x100000, False, pid)
        if not handle:
            if ctypes.get_last_error() in (87, 1168): return None
            raise ValueError('BINDING_OWNER_UNVERIFIED')
        try:
            waited = kernel.WaitForSingleObject(handle, 0)
            if waited == 0: return None
            if waited != 258: raise ValueError('BINDING_OWNER_UNVERIFIED')
            created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
            if not kernel.GetProcessTimes(handle, *[ctypes.byref(v) for v in (created, exited, system, user)]):
                raise ValueError('BINDING_OWNER_UNVERIFIED')
            return str((created.dwHighDateTime << 32) | created.dwLowDateTime)
        finally: kernel.CloseHandle(handle)
    path = Path('/proc') / str(pid) / 'stat'
    try: raw = path.read_text()
    except FileNotFoundError:return None
    parts = raw[raw.rfind(')') + 2:].split()
    return None if parts[0] == 'Z' else parts[19]


def write_binding(path, bridge):
    """Caller holds its checkpoint lease and uses a private per-user directory."""
    path = Path(path).absolute()
    for item in (*reversed(path.parents), path):
        if item.exists() and (item.is_symlink() or getattr(item.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('LOCAL_BINDING_REDIRECTION_REJECTED')
    previous = None
    if path.exists():
        with path.open('rb') as stream:previous=stream.read(16385)
        if len(previous)>16384:raise ValueError('INVALID_LOCAL_BINDING')
        old=loads(previous)
        if (not isinstance(old,dict) or set(old)!={'schema','target','instanceId','endpoint','capability','owner'}
                or old.get('schema')!='xnby.layer-sync.binding.v1' or old.get('target')!=TARGET
                or not isinstance(old.get('owner'),dict) or set(old['owner'])!={'pid','creation'}
                or not isinstance(old['owner'].get('creation'),str) or not re.fullmatch('[0-9]{1,20}',old['owner']['creation'])
                or not isinstance(old.get('instanceId'),str) or not re.fullmatch('[0-9a-f]{32}',old['instanceId'])
                or not isinstance(old.get('capability'),str) or not re.fullmatch('[0-9a-f]{64}',old['capability'])
                or not isinstance(old.get('endpoint'),str) or not re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}',old['endpoint'])):
            raise ValueError('UNKNOWN_LOCAL_BINDING_RETAINED')
        actual=process_creation(old['owner'].get('pid'))
        if actual is not None and actual==old['owner']['creation']:
            raise ValueError('PRIOR_LOCAL_HELPER_STILL_ALIVE')
    value={'schema':'xnby.layer-sync.binding.v1','target':TARGET,'instanceId':bridge.instance_id,
           'endpoint':bridge.endpoint,'capability':bridge.capability,
           'owner':{'pid':os.getpid(),'creation':process_creation(os.getpid())}}
    raw=encode(value);temporary=None
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.local-binding-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        if (previous is None and path.exists()) or (previous is not None and path.read_bytes()!=previous):
            raise ValueError('LOCAL_BINDING_CHANGED')
        os.replace(temporary,path);temporary=None
        return raw
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def remove_binding(path, expected):
    path=Path(path)
    if path.exists() and path.read_bytes()==expected:path.unlink()
