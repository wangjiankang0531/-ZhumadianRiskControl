"""Loopback DLG sync adapter for the existing project HTTPS ingress.

This candidate is not installed by importing/running tests. Every operation asks
the original platform CurrentUser endpoint; no tokens or account passwords persist.
"""
import copy
import hashlib
import http.client
import http.server
import json
import re
import threading
import time
import sqlite3
from urllib.parse import urlsplit

from services.common import ApiError, loads
from services.layer_sync_identity import ACCOUNT_HEADER, account_key
from tools.landscape_layer_validation import validate_editor_layers

LIMIT = 16 * 1048576
ROUTE = '/v1/project/layers'
ACCOUNT_ROUTE = '/v2/project/layers'
ORIGIN = 'https://www.joinlinksmart.com'


def empty_document():
    return {'schema': 'hongtu.landscape.layers.v1', 'scene': 'zhumadian',
            'coordinates': {'srs': 'EPSG:32650', 'unit': 'metre', 'axes': 'east,north,up',
                            'origin': [225319.5, 3648440.1, 30.9]}, 'layers': []}


class OriginalPlatformAccess:
    """Current-session check plus an explicit project read/write ACL.

    Role IDs and subject IDs come from server configuration, not request input.
    Administrator access is off unless explicitly enabled for this installation.
    """
    def __init__(self, platform_port, *, readers=(), writers=(), read_roles=(), write_roles=(), administrators=False):
        if type(platform_port) is not int or not 1024 <= platform_port <= 65535:
            raise ValueError('EXPLICIT_PLATFORM_LOOPBACK_PORT_REQUIRED')
        self.port = platform_port
        self.readers, self.writers = set(readers), set(writers)
        self.read_roles, self.write_roles = set(read_roles), set(write_roles)
        if type(administrators) is not bool:
            raise ValueError('INVALID_PROJECT_ACL')
        for values in (self.readers, self.writers, self.read_roles, self.write_roles):
            if any(not isinstance(v, str) or not v or len(v) > 256 for v in values):
                raise ValueError('INVALID_PROJECT_ACL')
        self.administrators = administrators

    def check(self, authorization, write=False):
        if not isinstance(authorization, str) or not authorization.strip() or len(authorization) > 16384 or re.search(r'[\r\n\x00]', authorization):
            raise ApiError(401, 'LOGIN_REQUIRED')
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        try:
            conn.request('GET', '/api/oauth/CurrentUser', headers={'Authorization': authorization, 'Accept': 'application/json'})
            response = conn.getresponse()
            if response.status in (401, 403):
                raise ApiError(401, 'LOGIN_REQUIRED')
            if response.status != 200:
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            parts = []; count = 0; deadline = time.monotonic() + 5
            while count <= 1048576:
                if time.monotonic() > deadline:
                    raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
                chunk = response.read1(min(16384, 1048577 - count))
                if not chunk:
                    break
                parts.append(chunk); count += len(chunk)
            raw = b''.join(parts)
            if len(raw) > 1048576:
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            reply = loads(raw)
            if not isinstance(reply, dict) or type(reply.get('code')) is not int:
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            if reply['code'] in (600, 401, 200001):
                raise ApiError(401, 'LOGIN_REQUIRED')
            if reply['code'] != 200:
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            data = reply.get('data')
            info = data.get('userInfo') if isinstance(data, dict) else None
            if not isinstance(info, dict) or not isinstance(info.get('userId'), str) or not info['userId'].strip():
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            roles = info.get('roleIds', [])
            if not isinstance(roles, list) or any(not isinstance(v, str) for v in roles):
                raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE')
            admin = info.get('isAdministrator')
            allowed_admin = self.administrators and (admin is True or type(admin) is int and admin == 1
                                                     or isinstance(admin, str) and admin.lower() in ('true', '1'))
            subjects = self.writers if write else self.readers | self.writers
            allowed_roles = self.write_roles if write else self.read_roles | self.write_roles
            if not (allowed_admin or info['userId'] in subjects or set(roles) & allowed_roles):
                raise ApiError(403, 'PROJECT_LAYER_ACCESS_DENIED')
            return info['userId']
        except ApiError:
            raise
        except (OSError, http.client.HTTPException, ValueError, TypeError, KeyError):
            raise ApiError(503, 'LOGIN_CHECK_UNAVAILABLE') from None
        finally:
            conn.close()


def checked_project_origin(value=None):
    """Exactly one origin, chosen by trusted configuration, never a request header."""
    if value is None or value == ORIGIN:
        return ORIGIN
    if not isinstance(value, str) or not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{4,5}', value):
        raise ValueError('EXACT_CANONICAL_OR_EXPLICIT_LOOPBACK_ORIGIN_REQUIRED')
    port = int(value.rsplit(':', 1)[1])
    if not 1024 <= port <= 65535 or value != 'http://127.0.0.1:' + str(port):
        raise ValueError('EXACT_LOOPBACK_ORIGIN_PORT_REQUIRED')
    return value


class LayerSyncServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port, repository, access, *, project_files=None, origin=None,scene_projects=None):
        self.project_origin = checked_project_origin(origin)
        self.repository, self.access = repository, access
        self.project_files = project_files
        self.scene_projects = scene_projects
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(('127.0.0.1', port), LayerSyncHandler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class LayerSyncHandler(http.server.BaseHTTPRequestHandler):
    server_version = 'XNBY-LayerSync'
    def setup(self):
        super().setup()
        self.connection.settimeout(8)

    def log_message(self, *args):
        pass

    def output(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Vary', 'Authorization')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def scene_read_authorization(self, write=False):
        # Nginx auth_request calls this loopback endpoint; no layer/database read.
        try:
            if write or self.command not in ('GET','HEAD'):
                raise ApiError(405, 'METHOD_NOT_ALLOWED')
            values = self.headers.get_all('Authorization', [])
            if len(values) != 1:
                raise ApiError(401, 'LOGIN_REQUIRED')
            origins = self.headers.get_all('Origin', [])
            if origins and origins != [self.server.project_origin]:
                raise ApiError(403, 'PROJECT_ORIGIN_REQUIRED')
            if self.headers.get('Transfer-Encoding') or self.headers.get_all('Content-Length', []) not in ([], ['0']):
                raise ApiError(400, 'INVALID_REQUEST')
            self.server.access.check(values[0], False)
            self.send_response(204)
            self.send_header('Content-Length', '0')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Vary', 'Authorization, Origin')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
        except ApiError as error:
            return self.output(error.status, {'error': error.code})

    def perform(self, write=False):
        if self.path=='/v2/project/scenes'or self.path.startswith('/v2/project/scenes/'):
            from services.scene_projects import serve_scene_projects
            return serve_scene_projects(self,write)
        if self.path == '/v2/project/scene-read':
            return self.scene_read_authorization(write)
        if self.path=='/v2/project/files'or self.path.startswith('/v2/project/files/'):
            from services.project_files_api import serve_project_files
            return serve_project_files(self,write)
        try:
            if self.path not in (ROUTE,ACCOUNT_ROUTE):
                raise ApiError(404, 'NOT_FOUND')
            values = self.headers.get_all('Authorization', [])
            if len(values) != 1:
                raise ApiError(401, 'LOGIN_REQUIRED')
            origins = self.headers.get_all('Origin', [])
            if origins and origins != [self.server.project_origin]:
                raise ApiError(403, 'PROJECT_ORIGIN_REQUIRED')
            bindings = self.headers.get_all(ACCOUNT_HEADER, [])
            if self.path==ACCOUNT_ROUTE and not bindings:
                raise ApiError(403,'ACCOUNT_BINDING_REQUIRED')
            if bindings and (len(bindings)!=1 or not re.fullmatch("[0-9a-f]{64}",bindings[0])):
                raise ApiError(403,"ACCOUNT_BINDING_MISMATCH")
            subject = self.server.access.check(values[0], write)
            if bindings and bindings[0]!=account_key(subject):
                raise ApiError(403,"ACCOUNT_BINDING_MISMATCH")
            lengths = self.headers.get_all('Content-Length', [])
            if self.headers.get('Transfer-Encoding') or len(lengths) > 1:
                raise ApiError(400, 'INVALID_REQUEST')
            if write:
                if len(lengths) != 1 or not re.fullmatch('[0-9]{1,8}', lengths[0]):
                    raise ApiError(400, 'CONTENT_LENGTH_REQUIRED')
                size = int(lengths[0])
                if not 1 <= size <= LIMIT:
                    raise ApiError(413, 'LAYER_DOCUMENT_TOO_LARGE')
                if self.headers.get_all('Content-Type', []) not in (['application/json'], ['application/json; charset=utf-8']):
                    raise ApiError(415, 'JSON_REQUIRED')
                parts = []; count = 0; deadline = time.monotonic() + 8
                while count < size:
                    if time.monotonic() > deadline:
                        raise ApiError(408, 'REQUEST_TIMEOUT')
                    chunk = self.rfile.read1(min(16384, size - count))
                    if not chunk:
                        break
                    parts.append(chunk); count += len(chunk)
                raw = b''.join(parts)
                if len(raw) != size:
                    raise ApiError(400, 'INVALID_REQUEST')
                request = loads(raw)
                if not isinstance(request, dict) or set(request) != {'document', 'expectedRevision'}:
                    raise ApiError(400, 'INVALID_REQUEST')
                if type(request['expectedRevision']) is not int or not 0 <= request['expectedRevision'] <= 2**31 - 2:
                    raise ApiError(400, 'INVALID_REVISION')
                validate_editor_layers(request['document'])
                payload = json.dumps(request['document'], ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
                result = self.server.repository.import_bytes('zhumadian', 'default', payload, request['expectedRevision'])
                return self.output(200, result)
            if lengths and lengths != ['0']:
                raise ApiError(400, 'INVALID_REQUEST')
            try:
                result = self.server.repository.get('zhumadian', 'default')
            except ApiError as error:
                if error.code != 'LAYER_DOCUMENT_NOT_FOUND':
                    raise
                result = {'revision': 0, 'sha256': None, 'document': empty_document()}
            return self.output(200, {k: result[k] for k in ('revision', 'sha256', 'document')})
        except ApiError as error:
            return self.output(error.status, {'error': error.code})
        except (ValueError, TypeError, KeyError):
            return self.output(422, {'error': 'INVALID_LAYER_DOCUMENT'})
        except (OSError, TimeoutError, sqlite3.Error):
            return self.output(503, {'error': 'LAYER_SYNC_UNAVAILABLE'})

    def do_GET(self): self.perform()
    def do_HEAD(self): self.perform()
    def do_POST(self): self.perform(write=True)
    def do_PUT(self): self.output(405, {'error': 'METHOD_NOT_ALLOWED'})
    do_DELETE = do_PATCH = do_OPTIONS = do_PUT
