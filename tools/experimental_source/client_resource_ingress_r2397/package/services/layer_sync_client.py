"""Durable asynchronous coordinator for an editor/viewer of one cloud project.

All network I/O runs outside the state lock. The UI gets generation-tagged
snapshots, submits completed edits, and supplies an earlier snapshot when an
edit overlaps a background update. Credentials belong to the transport only.
"""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import threading
import time

from services.common import loads
from tools.landscape_layer_validation import validate_editor_layers
from services.layer_sync_state import SyncState, SyncConflict, merge_snapshots, _equal
from services.layer_sync_transport import SyncHTTPError, HOST, PATH
from services.layer_sync_resolution import comparison_mode, comparison_page, choices_map, paths_for, value_at

TARGET = 'https://' + HOST + PATH
MAX_CHECKPOINT_BYTES = 128 * 1048576


class CheckpointError(OSError):
    pass


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()


def _pack(state):
    return {'base': copy.deepcopy(state.base), 'local': copy.deepcopy(state.local),
            'revision': state.revision, 'conflicts': [list(p) for p in state.conflicts]}


def _unpack(value):
    if not isinstance(value, dict) or set(value) != {'base', 'local', 'revision', 'conflicts'}:
        raise ValueError('INVALID_CLIENT_CLOUD_STATE')
    result = SyncState(value['base'], value['revision'])
    result.edit(value['local'])
    paths = value['conflicts']
    if not isinstance(paths, list) or any(not isinstance(p, list) or len(p) != 2 or
                                        any(not isinstance(v, str) for v in p) for p in paths):
        raise ValueError('INVALID_CLIENT_CONFLICT_PATHS')
    result.conflicts = tuple(tuple(p) for p in paths)
    return result


class LayerSyncClient:
    def __init__(self, transport, checkpoint, *, initial_document=None, publish_if_empty=False,
                 coalesce_seconds=.3, poll_seconds=2, account_key=None):
        if account_key is not None and (not isinstance(account_key,str) or not re.fullmatch("[0-9a-f]{64}",account_key)):
            raise ValueError("INVALID_CLIENT_ACCOUNT_KEY")
        self.account_key = account_key
        checkpoint = Path(checkpoint).absolute()
        lease_path = checkpoint.with_name(checkpoint.name + '.lock')
        for path in (checkpoint, lease_path):
            for item in (*reversed(path.parents), path):
                if item.exists() and (item.is_symlink() or getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
                    raise ValueError('CLIENT_CHECKPOINT_REDIRECTION_REJECTED')
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        lease = lease_path.open('a+b')
        try:
            if not lease_path.stat().st_size:
                lease.write(b'0'); lease.flush()
            lease.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lease, self._closed = lease, False
            self._initialize(transport, checkpoint, initial_document=initial_document, publish_if_empty=publish_if_empty,
                             coalesce_seconds=coalesce_seconds, poll_seconds=poll_seconds)
        except BaseException:
            lease.close()
            raise

    def _initialize(self, transport, checkpoint, *, initial_document, publish_if_empty,
                    coalesce_seconds, poll_seconds):
        if type(publish_if_empty) is not bool or not 0 <= coalesce_seconds <= 5 or not .02 <= poll_seconds <= 60:
            raise ValueError('INVALID_CLIENT_OPTIONS')
        if initial_document is not None:
            validate_editor_layers(initial_document)
        self.transport = transport
        self.checkpoint = Path(checkpoint)
        self._expected_checkpoint_sha = None
        self.coalesce_seconds, self.poll_seconds = coalesce_seconds, poll_seconds
        self._cv = threading.Condition(threading.RLock())
        self._thread = None
        self._stop = False
        self._paused = False
        self._epoch = 0
        self._next_due = time.monotonic()
        self._last_edit = time.monotonic()
        self._retry_until = 0
        self._failures = 0
        self._error = None
        self._busy = False
        from services.layer_sync_import import ImportPlans
        self._import_plans = ImportPlans()
        if self.checkpoint.exists():
            with self.checkpoint.open('rb') as stream:
                raw = stream.read(MAX_CHECKPOINT_BYTES + 1)
            if len(raw) > MAX_CHECKPOINT_BYTES:
                raise ValueError('CLIENT_CHECKPOINT_TOO_LARGE')
            envelope = loads(raw)
            if not isinstance(envelope, dict) or set(envelope) != {'payload', 'sha256'} or not isinstance(envelope['payload'], str):
                raise ValueError('INVALID_CLIENT_CHECKPOINT')
            payload = envelope['payload'].encode()
            if hashlib.sha256(payload).hexdigest() != envelope['sha256']:
                raise ValueError('CLIENT_CHECKPOINT_CORRUPT')
            self._data = loads(payload)
            self._validate(self._data)
            if self._data.get("accountKey") != self.account_key:
                raise ValueError("CLIENT_ACCOUNT_BINDING_CHANGED")
            self._expected_checkpoint_sha = hashlib.sha256(raw).hexdigest()
            if initial_document is not None and not _equal(initial_document, self._document(self._data)):
                raise ValueError('RESUMED_EDITOR_DOCUMENT_REQUIRES_EXPLICIT_RECONCILIATION')
        else:
            self._data = {'schema': 'xnby.layer-sync.client.v1', 'target': TARGET, 'generation': 0,
                          'cloud': None, 'bootstrapDocument': copy.deepcopy(initial_document),
                          'publishIfEmpty': publish_if_empty, 'conflict': None}
            if self.account_key is not None:
                self._data.update(schema='xnby.layer-sync.client.v2',accountKey=self.account_key)
            self._write(self._data)
        self._pending_cache = self._calculate_pending(self._data)
        self._status = 'conflict' if self._data['conflict'] else 'connecting'

    @staticmethod
    def _document(data):
        conflict = data['conflict']
        if conflict and conflict['source'] == 'editor':
            return conflict['draftDocument']
        return data['cloud']['local'] if data['cloud'] is not None else data['bootstrapDocument']

    @staticmethod
    def _validate(data):
        if not isinstance(data, dict): raise ValueError('INVALID_CLIENT_CHECKPOINT')
        modern = data.get('schema') == 'xnby.layer-sync.client.v3'
        bound = data.get('schema') == 'xnby.layer-sync.client.v2' or modern and data.get('accountKey') is not None
        fields = {'schema', 'target', 'generation', 'cloud', 'bootstrapDocument', 'publishIfEmpty', 'conflict'}
        if bound or modern: fields.add('accountKey')
        if set(data) != fields or bound and (not isinstance(data['accountKey'],str) or not re.fullmatch('[0-9a-f]{64}',data['accountKey'])):
            raise ValueError('INVALID_CLIENT_CHECKPOINT')
        if data['schema'] not in ('xnby.layer-sync.client.v1','xnby.layer-sync.client.v2','xnby.layer-sync.client.v3') or data['target'] != TARGET:
            raise ValueError('CLIENT_PROJECT_BINDING_CHANGED')
        if type(data['generation']) is not int or not 0 <= data['generation'] < 2**63 or type(data['publishIfEmpty']) is not bool:
            raise ValueError('INVALID_CLIENT_CHECKPOINT')
        if data['cloud'] is not None:
            _unpack(data['cloud'])
            if data['bootstrapDocument'] is not None:
                raise ValueError('INVALID_CLIENT_BOOTSTRAP_STATE')
        elif data['bootstrapDocument'] is not None:
            validate_editor_layers(data['bootstrapDocument'])
        conflict = data['conflict']
        if conflict is not None:
            if not isinstance(conflict, dict) or conflict.get('source') not in ('cloud', 'editor', 'bootstrap'):
                raise ValueError('INVALID_CLIENT_CONFLICT')
            conflict_fields = {'source', 'remoteDocument', 'remoteRevision', 'draftDocument', 'paths'}
            if modern: conflict_fields.update(('basisDocument', 'comparisonDocument'))
            if set(conflict) != conflict_fields:
                raise ValueError('INVALID_CLIENT_CONFLICT')
            if modern:
                if ((conflict['source'] == 'bootstrap') != (conflict['basisDocument'] is None)
                        or (conflict['source'] == 'bootstrap') != (data['cloud'] is None)):
                    raise ValueError('INVALID_CLIENT_CONFLICT')
                validate_editor_layers(conflict['comparisonDocument'])
                if conflict['basisDocument'] is None:
                    if conflict['source'] != 'bootstrap': raise ValueError('INVALID_CLIENT_CONFLICT')
                else:
                    validate_editor_layers(conflict['basisDocument'])
            validate_editor_layers(conflict['remoteDocument'])
            validate_editor_layers(conflict['draftDocument'])
            SyncState._revision(conflict['remoteRevision'])
            if not isinstance(conflict['paths'], list) or any(not isinstance(p, list) or len(p) != 2 or
                    any(not isinstance(v, str) for v in p) for p in conflict['paths']):
                raise ValueError('INVALID_CLIENT_CONFLICT')

    def _write(self, data):
        self._validate(data)
        payload = _encode(data)
        raw = _encode({'payload': payload.decode(), 'sha256': hashlib.sha256(payload).hexdigest()})
        if len(raw) > MAX_CHECKPOINT_BYTES:
            raise CheckpointError('CLIENT_CHECKPOINT_TOO_LARGE')
        temp_path = None
        try:
            if self.checkpoint.exists():
                with self.checkpoint.open('rb') as original:
                    current = original.read(MAX_CHECKPOINT_BYTES + 1)
                if self._expected_checkpoint_sha is None or hashlib.sha256(current).hexdigest() != self._expected_checkpoint_sha:
                    raise CheckpointError('CLIENT_CHECKPOINT_CHANGED_EXTERNALLY')
            elif self._expected_checkpoint_sha is not None:
                raise CheckpointError('CLIENT_CHECKPOINT_REMOVED_EXTERNALLY')
            self.checkpoint.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.checkpoint.parent, prefix='.layer-client-', delete=False) as stream:
                temp_path = Path(stream.name)
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp_path, self.checkpoint)
            self._expected_checkpoint_sha = hashlib.sha256(raw).hexdigest()
            temp_path = None
        except OSError:
            raise CheckpointError('CLIENT_CHECKPOINT_WRITE_FAILED') from None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _commit(self, data, *, force_generation=False):
        if force_generation or not _equal(self._document(data), self._document(self._data)):
            data['generation'] = self._data['generation'] + 1
        if not _equal(data, self._data):
            self._write(data)  # Durability precedes publishing the new in-memory state.
            self._data = data
            self._pending_cache = self._calculate_pending(data)
        self._cv.notify_all()

    @staticmethod
    def _calculate_pending(data):
        if data['conflict'] is not None:
            return True
        if data['cloud'] is None:
            return data['bootstrapDocument'] is not None
        return not _equal(data['cloud']['base'], data['cloud']['local'])

    def _pending(self):
        return self._pending_cache

    def summary(self):
        """Small UI poll; does not copy/serialize the document or conflict drafts."""
        with self._cv:
            conflict = self._data['conflict']
            document = self._document(self._data)
            return {'generation': self._data['generation'],
                    'revision': None if self._data['cloud'] is None else self._data['cloud']['revision'],
                    'status': self._status, 'pending': self._pending_cache, 'error': self._error,
                    'conflict': None if not conflict else {'source': conflict['source'],
                        'paths': [list(p) for p in conflict['paths'][:32]], 'pathCount': len(conflict['paths'])},
                    'documentAvailable': document is not None,
                    'layerCount': 0 if document is None else len(document['layers']),
                    'networkBusy': self._busy, 'paused': self._paused,
                    'running': self._thread is not None and self._thread.is_alive()}

    def view(self):
        with self._cv:
            return {'document': copy.deepcopy(self._document(self._data)), 'generation': self._data['generation'],
                    'revision': None if self._data['cloud'] is None else self._data['cloud']['revision'],
                    'status': self._status, 'pending': self._pending(), 'error': self._error,
                    'conflict': copy.deepcopy(self._data['conflict']), 'networkBusy': self._busy,
                    'coordinatorDocument': copy.deepcopy(self._data['cloud']['local']) if self._data['cloud'] else None,
                    'running': self._thread is not None and self._thread.is_alive()}

    def edit(self, document, generation, *, basis_document=None):
        validate_editor_layers(document)
        with self._cv:
            if self._closed: raise ValueError('CLIENT_ALREADY_CLOSED')
            if type(generation) is not int or not 0 <= generation <= self._data['generation']:
                raise ValueError('INVALID_EDITOR_GENERATION')
            data = copy.deepcopy(self._data)
            current = self._document(data)
            # A receipt's generation need not describe the editor's displayed document.
            # Whenever a basis is supplied, merge it even if the numeric generation matches.
            if basis_document is not None or generation != data['generation']:
                if basis_document is None or current is None:
                    raise ValueError('EDITOR_BASIS_REQUIRED')
                validate_editor_layers(basis_document)
                try:
                    document = merge_snapshots(basis_document, document, current)
                except SyncConflict as error:
                    if data['cloud'] is None:
                        raise ValueError('EDITOR_INITIAL_SELECTION_REQUIRED') from None
                    if data['conflict'] is not None:
                        raise ValueError('CONFLICT_REQUIRES_RESOLUTION') from None
                    self._capture_conflict(data, {'source': 'editor', 'remoteDocument': copy.deepcopy(data['cloud']['base']),
                                        'remoteRevision': data['cloud']['revision'],
                                        'draftDocument': copy.deepcopy(document),
                                        'paths': [list(p) for p in error.paths]}, basis_document, current)
                    self._commit(data, force_generation=True)
                    self._status = 'conflict'
                    raise
            if data['conflict'] and data['conflict']['source'] == 'editor':
                data['conflict']['draftDocument'] = copy.deepcopy(document)
            elif data['cloud'] is None:
                data['bootstrapDocument'] = copy.deepcopy(document)
            else:
                state = _unpack(data['cloud']); state.edit(document); data['cloud'] = _pack(state)
            if data['conflict']:
                data['conflict']['draftDocument'] = copy.deepcopy(document)
                if comparison_mode(data['conflict']) == 'items':
                    data['conflict']['paths'] = paths_for(data['conflict'])
            self._commit(data)
            self._last_edit = time.monotonic()
            self._next_due = self._last_edit + self.coalesce_seconds
            self._status = 'conflict' if data['conflict'] else 'pending'
            self._cv.notify_all()
            return self.view()

    @staticmethod
    def _capture_conflict(data, conflict, basis, comparison):
        # New context must not masquerade as the older five-field schema. Old
        # readers fail closed on v3 instead of discarding the missing basis.
        data.update(schema='xnby.layer-sync.client.v3', accountKey=data.get('accountKey'))
        conflict.update(basisDocument=copy.deepcopy(basis), comparisonDocument=copy.deepcopy(comparison))
        data['conflict'] = conflict

    def _checked_conflict(self, generation):
        if self._closed: raise ValueError('CLIENT_ALREADY_CLOSED')
        if type(generation) is not int or generation != self._data['generation'] or not self._data['conflict']:
            raise ValueError('CURRENT_CONFLICT_GENERATION_REQUIRED')
        return self._data['conflict']

    def _comparison_conflict(self, generation):
        conflict = self._checked_conflict(generation)
        if 'comparisonDocument' not in conflict and conflict['source'] == 'editor':
            # Legacy records have no genuine common basis; show the preserved
            # coordinator separately, but never infer a three-way merge basis.
            conflict = dict(conflict, comparisonDocument=self._data['cloud']['local'])
        return conflict

    def compare_conflict(self, generation, *, offset=0, limit=8):
        with self._cv:
            return comparison_page(self._comparison_conflict(generation), generation, offset, limit)

    def conflict_value(self, generation, path, side):
        with self._cv:
            conflict = self._comparison_conflict(generation)
            if not isinstance(path, list) or path not in paths_for(conflict):
                raise ValueError('INVALID_CONFLICT_PATH')
            return {'generation': generation, 'path': copy.deepcopy(path), 'side': side,
                    **value_at(conflict, path, side)}

    def resolve_choices(self, choices, generation):
        decisions = choices_map(choices)
        with self._cv:
            conflict = self._checked_conflict(generation)
            if comparison_mode(conflict) != 'items':
                raise ValueError('CONFLICT_BASIS_UNAVAILABLE')
            document = merge_snapshots(conflict['basisDocument'], conflict['draftDocument'],
                                       conflict['comparisonDocument'], choices=decisions)
            self.resolve(document, generation)

    def resolve_project_choice(self, side, generation, *, acknowledge_whole_project=False):
        with self._cv:
            conflict = self._comparison_conflict(generation)
            if acknowledge_whole_project is not True or side not in ('local', 'remote'):
                raise ValueError('EXPLICIT_WHOLE_PROJECT_CHOICE_REQUIRED')
            if comparison_mode(conflict) != 'whole-project':
                raise ValueError('ITEM_CHOICES_REQUIRED')
            document = value_at(conflict, ['document', 'initialSelection'], side)['value']
            self.resolve(document, generation)

    def resolve(self, document, generation):
        validate_editor_layers(document)
        with self._cv:
            self._checked_conflict(generation)
            data = copy.deepcopy(self._data); conflict = data['conflict']
            state = SyncState(conflict['remoteDocument'], conflict['remoteRevision'])
            state.edit(document)
            data.update(cloud=_pack(state), bootstrapDocument=None, conflict=None)
            self._commit(data, force_generation=True)
            self._status, self._error = 'pending', None
            self._last_edit = time.monotonic(); self._next_due = self._last_edit + self.coalesce_seconds
            self._cv.notify_all()

    def import_status(self):
        with self._cv:
            reason = None
            if self._closed: reason = 'CLIENT_ALREADY_CLOSED'
            elif self._data['cloud'] is None: reason = 'IMPORT_CURRENT_PROJECT_REQUIRED'
            elif self._data['conflict']: reason = 'RESOLVE_CONFLICT_BEFORE_IMPORT'
            return {'generation': self._data['generation'], 'ready': reason is None, 'reason': reason,
                    'status': self._status, 'pending': self._pending_cache}

    def _import_generation(self, generation):
        if type(generation) is not int or generation != self._data['generation']:
            raise ValueError('CURRENT_IMPORT_GENERATION_REQUIRED')
        status = self.import_status()
        if not status['ready']: raise ValueError(status['reason'])

    def import_prepare(self, file_data, file_sha256, name, generation):
        from services.layer_sync_import import read_file, ImportPlan
        incoming, size = read_file(file_data, file_sha256, name)
        with self._cv:
            self._import_generation(generation)
            plan = ImportPlan(self._document(self._data), incoming, generation, name, file_sha256, size)
            self._import_plans.add(plan)
            return plan.page()

    def _import_plan(self, plan_id, generation):
        self._import_generation(generation)
        plan = self._import_plans.get(plan_id)
        if plan.generation != generation: raise ValueError('CURRENT_IMPORT_GENERATION_REQUIRED')
        if plan.applied: raise ValueError('IMPORT_PLAN_ALREADY_APPLIED')
        return plan

    def import_compare(self, plan_id, generation, *, offset=0, limit=8):
        with self._cv:
            return self._import_plan(plan_id, generation).page(offset, limit)

    def import_value(self, plan_id, generation, path, side):
        with self._cv:
            plan = self._import_plan(plan_id, generation)
            return {'planId': plan.id, 'generation': generation, 'path': copy.deepcopy(path), 'side': side,
                    **plan.value(path, side)}

    def import_apply(self, plan_id, generation, choices):
        with self._cv:
            plan = self._import_plan(plan_id, generation)
            document = plan.merged(choices)
            self.edit(document, generation, basis_document=plan.current)
            plan.applied = True  # Only after durable edit; a failed write retains the preview.

    def credentials_changed(self):
        with self._cv:
            if self._closed: raise ValueError('CLIENT_ALREADY_CLOSED')
            self._epoch += 1; self._paused = False; self._error = None
            self._retry_until = 0; self._failures = 0; self._next_due = time.monotonic()
            self._status = 'conflict' if self._data['conflict'] else 'connecting'
            self._cv.notify_all()

    def pause(self, *, login_required=False):
        with self._cv:
            if self._closed: raise ValueError('CLIENT_ALREADY_CLOSED')
            self._epoch += 1; self._paused = True; self._error = None
            self._status = 'login-required' if login_required else 'paused'
            self._cv.notify_all()

    def start(self):
        with self._cv:
            if self._closed: raise ValueError('CLIENT_ALREADY_CLOSED')
            if self._thread is not None and self._thread.is_alive():
                raise ValueError('CLIENT_WORKER_ALREADY_RUNNING')
            self._stop = False
            self._thread = threading.Thread(target=self._run, name='xnby-layer-sync', daemon=True)
            self._thread.start()

    def stop(self, timeout=30):
        with self._cv:
            self._stop = True; self._cv.notify_all(); thread = self._thread
        if thread is not None:
            thread.join(timeout)
            if thread.is_alive():
                raise TimeoutError('CLIENT_NETWORK_STOP_PENDING')
        with self._cv:
            self._status = 'stopped'; self._cv.notify_all()
            if not self._closed:
                self._lease.close(); self._closed = True

    def _sync_once(self):
        with self._cv:
            if self._paused or self._data['conflict'] or self._stop:
                return
            epoch = self._epoch; self._busy = True; self._status = 'syncing'
        try:
            remote, revision = self.transport.fetch()
            validate_editor_layers(remote); SyncState._revision(revision)
            with self._cv:
                if epoch != self._epoch or self._stop or self._data['conflict']:
                    return
                data = copy.deepcopy(self._data)
                if data['cloud'] is None:
                    state = SyncState(remote, revision)
                    local = data['bootstrapDocument']
                    if local is not None and not _equal(local, remote):
                        if revision == 0 and data['publishIfEmpty']:
                            state.edit(local)
                        else:
                            self._capture_conflict(data, {'source': 'bootstrap', 'remoteDocument': copy.deepcopy(remote),
                                                'remoteRevision': revision, 'draftDocument': copy.deepcopy(local),
                                                'paths': [['document', 'initialSelection']]}, None, remote)
                            self._commit(data)
                            self._status = 'conflict'; return
                    data.update(cloud=_pack(state), bootstrapDocument=None)
                else:
                    state = _unpack(data['cloud'])
                    try:
                        state.reconcile(remote, revision)
                    except SyncConflict as error:
                        data['cloud'] = _pack(state)
                        self._capture_conflict(data, {'source': 'cloud', 'remoteDocument': copy.deepcopy(remote),
                                            'remoteRevision': revision, 'draftDocument': copy.deepcopy(state.local),
                                            'paths': [list(p) for p in error.paths]}, state.base, remote)
                        self._commit(data); self._status = 'conflict'; return
                    data['cloud'] = _pack(state)
                self._commit(data)
                if not state.pending:
                    self._status, self._error = 'synced', None
                    self._failures = 0; self._retry_until = 0
                    return
                if time.monotonic() < self._last_edit + self.coalesce_seconds:
                    self._status = 'pending'; return
                expected, sent = state.submission()
            with self._cv:
                if epoch != self._epoch or self._stop: return
            new_revision = self.transport.submit(sent, expected)
            with self._cv:
                if epoch != self._epoch:
                    return  # Next fetch reconciles the uncertain delivery; no blind resend.
                data = copy.deepcopy(self._data); state = _unpack(data['cloud'])
                state.acknowledged(sent, expected, new_revision)
                data['cloud'] = _pack(state); self._commit(data)
                self._status = 'conflict' if data['conflict'] else 'pending' if state.pending else 'synced'
                self._error = None; self._failures = 0; self._retry_until = 0
        except SyncHTTPError as error:
            with self._cv:
                if epoch != self._epoch: return
                self._error = 'HTTP_' + str(error.status)
                if error.status in (401, 403, 404):
                    self._paused = True
                    self._status = {401: 'login-required', 403: 'access-denied', 404: 'service-not-installed'}[error.status]
                elif error.status == 409:
                    self._status = 'pending'; self._retry_until = time.monotonic() + .3
                else:
                    self._retry('offline')
        except CheckpointError:
            with self._cv:
                self._error = 'CHECKPOINT_WRITE_FAILED'; self._status = 'storage-error'; self._paused = True
        except (OSError, TimeoutError):
            with self._cv:
                if epoch != self._epoch: return
                self._error = 'CONNECTION_UNAVAILABLE'; self._retry('offline')
        except (ValueError, TypeError, KeyError):
            with self._cv:
                if epoch != self._epoch: return
                self._error = 'INVALID_SYNC_RESPONSE'; self._status = 'error'; self._paused = True
        finally:
            with self._cv:
                self._busy = False; self._cv.notify_all()

    def _retry(self, status):
        self._status = status; self._failures += 1
        self._retry_until = time.monotonic() + min(30, 2 ** min(self._failures - 1, 5))

    def _run(self):
        while True:
            with self._cv:
                if self._stop: return
                if self._paused or self._data['conflict']:
                    self._cv.wait(.5); continue
                due = max(self._next_due, self._retry_until)
                delay = due - time.monotonic()
                if delay > 0:
                    self._cv.wait(min(delay, .5)); continue
            try:
                self._sync_once()
            except Exception:
                with self._cv:
                    self._error = 'CLIENT_INTERNAL_ERROR'; self._status = 'error'; self._paused = True
                    self._cv.notify_all()
            with self._cv:
                now = time.monotonic()
                self._next_due = now + self.poll_seconds
                if self._pending() and not self._paused and not self._data['conflict']:
                    self._next_due = min(self._next_due, max(now + .05, self._last_edit + self.coalesce_seconds))
