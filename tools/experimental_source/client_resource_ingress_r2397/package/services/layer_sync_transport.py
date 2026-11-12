"""Pinned existing-project HTTPS transport; credentials are provided in memory."""
import http.client
import json
import time
import re
from services.common import loads
from tools.landscape_layer_validation import validate_editor_layers

HOST = 'www.joinlinksmart.com'
PATH = '/zhumadian/api/spatial-sync/v1/project/layers'
ACCOUNT_PATH = '/zhumadian/api/spatial-sync/v2/project/layers'
LIMIT = 17 * 1048576


class SyncHTTPError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__('LAYER_SYNC_HTTP_' + str(status))


class CloudTransport:
    def __init__(self, credential_provider, *, credential_guard=None, account_key=None):
        if account_key is not None and (not isinstance(account_key,str) or not re.fullmatch("[0-9a-f]{64}",account_key)):
            raise ValueError("INVALID_SYNC_ACCOUNT_KEY")
        if account_key is not None and not callable(credential_guard):
            raise ValueError("ACCOUNT_VERIFICATION_REQUIRED")
        self.credential_provider = credential_provider
        self.credential_guard, self.account_key = credential_guard, account_key

    def _request(self, method, payload=None):
        token = self.credential_provider()
        if not isinstance(token, str) or not token.strip() or len(token) > 16384 or any(c in token for c in '\r\n\x00'):
            raise SyncHTTPError(401)
        if self.credential_guard is not None: self.credential_guard(token)
        headers = {'Authorization': token, 'Accept': 'application/json'}
        if self.account_key is not None: headers['X-XNBY-Sync-Account'] = self.account_key
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
            if len(body) > 16 * 1048576:
                raise ValueError('LAYER_DOCUMENT_TOO_LARGE')
            headers['Content-Type'] = 'application/json'
        conn = http.client.HTTPSConnection(HOST, timeout=8)
        try:
            conn.request(method, ACCOUNT_PATH if self.account_key is not None else PATH, body=body, headers=headers)
            response = conn.getresponse()
            if response.status != 200:
                # No automatic redirects or POST retries, including 409/401.
                raise SyncHTTPError(response.status)
            data = []; size = 0; deadline = time.monotonic() + 10
            while size <= LIMIT:
                if time.monotonic() > deadline:
                    raise TimeoutError('LAYER_SYNC_TIMEOUT')
                chunk = response.read1(min(16384, LIMIT + 1 - size))
                if not chunk:
                    break
                data.append(chunk); size += len(chunk)
            if size > LIMIT:
                raise ValueError('LAYER_SYNC_RESPONSE_TOO_LARGE')
            return loads(b''.join(data))
        finally:
            conn.close()

    def fetch(self):
        reply = self._request('GET')
        if not isinstance(reply, dict) or set(reply) != {'document', 'revision', 'sha256'}:
            raise ValueError('INVALID_REMOTE_SNAPSHOT')
        if type(reply['revision']) is not int or not 0 <= reply['revision'] <= 2**31 - 1:
            raise ValueError('INVALID_REMOTE_REVISION')
        validate_editor_layers(reply['document'])
        return reply['document'], reply['revision']

    def submit(self, document, expected_revision):
        validate_editor_layers(document)
        if type(expected_revision) is not int or not 0 <= expected_revision <= 2**31 - 2:
            raise ValueError('INVALID_REMOTE_REVISION')
        reply = self._request('POST', {'expectedRevision': expected_revision, 'document': document})
        revision = reply.get('revision') if isinstance(reply, dict) else None
        if type(revision) is not int or revision not in (expected_revision, expected_revision + 1):
            raise ValueError('INVALID_SUBMISSION_RECEIPT')
        return revision
