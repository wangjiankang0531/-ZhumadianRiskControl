"""Bind one editor helper and its durable drafts to one verified project user.

The original project gateway maps /zhumadian/api/jnpf/ to platform /api/.
Account keys are project-scoped digests of CurrentUser.userInfo.userId; they
are identifiers, never Authorization values. Neither login passwords nor
Authorization values are written to the workspace.
"""
import hashlib
import http.client
import json
import re
import time

from services.common import loads
from services.layer_sync_transport import HOST, PATH, SyncHTTPError

CURRENT_USER_PATH = '/zhumadian/api/jnpf/oauth/CurrentUser'
ACCOUNT_HEADER = 'X-XNBY-Sync-Account'
TARGET = 'https://' + HOST + PATH


def checked_account_key(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('VERIFIED_PROJECT_ACCOUNT_KEY_REQUIRED')
    return value


def account_key(subject):
    if (not isinstance(subject, str) or not 1 <= len(subject) <= 256
            or subject != subject.strip() or any(ord(c) < 32 or ord(c) == 127 for c in subject)):
        raise ValueError('INVALID_PROJECT_SUBJECT')
    raw = json.dumps([TARGET, subject], ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


class AccountIdentityMismatch(SyncHTTPError):
    def __init__(self):
        super().__init__(403)


class ProjectAccountIdentity:
    def __init__(self, expected_key):
        self.expected_key = checked_account_key(expected_key)

    def verify(self, authorization):
        if (not isinstance(authorization, str) or not authorization or authorization != authorization.strip()
                or len(authorization) > 16384 or any(not 32 <= ord(c) <= 126 for c in authorization)):
            raise SyncHTTPError(401)
        connection = http.client.HTTPSConnection(HOST, timeout=8)
        try:
            connection.request('GET', CURRENT_USER_PATH,
                               headers={'Authorization': authorization, 'Accept': 'application/json'})
            response = connection.getresponse()
            if response.status in (401, 403): raise SyncHTTPError(401)
            if response.status != 200: raise SyncHTTPError(503)
            blocks = []; count = 0; deadline = time.monotonic() + 10
            while count <= 1048576:
                if time.monotonic() > deadline: raise SyncHTTPError(503)
                block = response.read1(min(16384, 1048577-count))
                if not block: break
                blocks.append(block); count += len(block)
            if count > 1048576: raise SyncHTTPError(503)
            reply = loads(b''.join(blocks))
            if not isinstance(reply, dict) or type(reply.get('code')) is not int: raise SyncHTTPError(503)
            if reply['code'] in (600, 401, 200001): raise SyncHTTPError(401)
            if reply['code'] != 200: raise SyncHTTPError(503)
            data = reply.get('data'); info = data.get('userInfo') if isinstance(data, dict) else None
            actual = account_key(info.get('userId') if isinstance(info, dict) else None)
            if actual != self.expected_key: raise AccountIdentityMismatch()
            return actual
        except SyncHTTPError:
            raise
        except (http.client.HTTPException, OSError, ValueError, TypeError, KeyError):
            raise SyncHTTPError(503) from None
        finally:
            connection.close()
