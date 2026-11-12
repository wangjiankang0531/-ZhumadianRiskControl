"""Transport-independent DLG synchronization; never treat missing layers as a merge import.

The base is a previously read authoritative snapshot, not a sample or a filtered
view. A server write must compare-and-swap the revision used by reconcile().
"""
import copy
import json
import hashlib
import os
from pathlib import Path
import tempfile
import heapq

from tools.landscape_layer_validation import validate_editor_layers


class SyncConflict(ValueError):
    def __init__(self, paths):
        self.paths = tuple(paths)
        super().__init__('LAYER_SYNC_CONFLICT')


def _equal(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(
        b, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _choose(base, local, remote, path, conflicts, choices=None):
    if _equal(local, remote) or _equal(remote, base):
        return copy.deepcopy(local)
    if _equal(local, base):
        return copy.deepcopy(remote)
    if choices is not None and path in choices:
        return copy.deepcopy(local if choices[path] == 'local' else remote)
    conflicts.append(path)
    return None


def _merged_order(base, local, remote, selected, path, conflicts, choices=None):
    """Preserve existing order and concurrent insertion positions, or conflict."""
    if choices is not None and path in choices:
        # Explicit ordering decision: keep this branch's order, then append
        # independently surviving IDs absent there in the other branch's order.
        first, second = (local, remote) if choices[path] == 'local' else (remote, local)
        return list(dict.fromkeys(key for branch in (first, second, base)
                                  for key in branch if key in selected))
    surviving = set(base) & set(selected)
    orders = [[key for key in branch if key in surviving] for branch in (base, local, remote)]
    original_order = _choose(*orders, path, conflicts)
    if original_order is None:
        return []
    edges = {key: set() for key in selected}
    incoming = {key: 0 for key in selected}
    def link(left, right):
        if right not in edges[left]:
            edges[left].add(right)
            incoming[right] += 1
    for left, right in zip(original_order, original_order[1:]):
        link(left, right)
    new_ids = set(selected) - set(base)
    priority = {}
    for document in (remote, local):
        branch = [key for key in document if key in selected]
        for left, right in zip(branch, branch[1:]):
            if left in new_ids or right in new_ids:
                link(left, right)
        for key in branch:
            if key not in priority:
                priority[key] = len(priority)
    ready = [(priority[key], key) for key, count in incoming.items() if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        _, key = heapq.heappop(ready)
        order.append(key)
        for target in edges[key]:
            incoming[target] -= 1
            if incoming[target] == 0:
                heapq.heappush(ready, (priority[target], target))
    if len(order) != len(selected):
        conflicts.append(path)
        return []
    return order


def _merge_existing_layer(base, local, remote, layer_id, conflicts, choices=None):
    # Header extensions are one atomic object; every feature is another atomic
    # object. Geometry, style, anchor and all label bindings stay together.
    if _equal(local, remote) or _equal(remote, base):
        return copy.deepcopy(local)
    if _equal(local, base):
        return copy.deepcopy(remote)
    header = lambda layer: {key: value for key, value in layer.items() if key != 'features'}
    result = _choose(*(header(layer) for layer in (base, local, remote)), ('layer', layer_id), conflicts, choices)
    indexes = [{f['id']: f for f in layer['features']} for layer in (base, local, remote)]
    selected = {}
    for feature_id in sorted(set().union(*(set(index) for index in indexes))):
        wrap = lambda index: {'value': index[feature_id]} if feature_id in index else {}
        chosen = _choose(*(wrap(index) for index in indexes), ('feature', feature_id), conflicts, choices)
        if chosen and 'value' in chosen:
            selected[feature_id] = chosen['value']
    order = _merged_order(*[[f['id'] for f in layer['features']] for layer in (base, local, remote)],
                          selected, ('featureOrder', layer_id), conflicts, choices)
    if result is not None:
        result['features'] = [selected[key] for key in order]
    return result


def merge_snapshots(base, local, remote, *, choices=None):
    """Merge independent stable feature IDs within existing layers.

    Features remain atomic: concurrent geometry/labels/styles for the same ID
    conflict. Layer creation/deletion and conflicting header edits also remain
    explicit conflicts; no polygon vertices or binding arrays are spliced.
    """
    for document in (base, local, remote):
        validate_editor_layers(document)
    if choices is not None:
        if (not isinstance(choices, dict) or any(not isinstance(p, tuple) or len(p) != 2
                or any(not isinstance(s, str) for s in p) or side not in ('local', 'remote')
                for p, side in choices.items())):
            raise ValueError('INVALID_CONFLICT_CHOICES')
        try:
            merge_snapshots(base, local, remote)
            required = set()
        except SyncConflict as error:
            required = set(error.paths)
        if set(choices) != required:
            raise ValueError('EXACT_CONFLICT_CHOICES_REQUIRED')
    if _equal(local, base):
        return copy.deepcopy(remote)
    if _equal(remote, base) or _equal(local, remote):
        return copy.deepcopy(local)
    conflicts = []
    result = {}
    for key in sorted((set(base) | set(local) | set(remote)) - {'layers'}):
        wrap = lambda d: {'value': d[key]} if key in d else {}
        chosen = _choose(wrap(base), wrap(local), wrap(remote), ('document', key), conflicts, choices)
        if chosen and 'value' in chosen:
            result[key] = chosen['value']
    indexes = [{layer['id']: layer for layer in document['layers']} for document in (base, local, remote)]
    selected = {}
    for layer_id in sorted(set().union(*(set(index) for index in indexes))):
        if all(layer_id in index for index in indexes):
            chosen = _merge_existing_layer(*(index[layer_id] for index in indexes), layer_id, conflicts, choices)
            if chosen is not None:
                selected[layer_id] = chosen
        else:
            # Two unrelated layers created under the same ID are not merged.
            wrap = lambda index: {'value': index[layer_id]} if layer_id in index else {}
            chosen = _choose(*(wrap(index) for index in indexes), ('layer', layer_id), conflicts, choices)
            if chosen and 'value' in chosen:
                selected[layer_id] = chosen['value']
    order = _merged_order(*[[layer['id'] for layer in doc['layers']] for doc in (base, local, remote)],
                          selected, ('document', 'layerOrder'), conflicts, choices)
    if choices:
        # An ID can be moved/created in different layers by the two branches.
        # Choosing that object also chooses its owner. Do not publish duplicates.
        owners = {}
        for path, side in choices.items():
            if path[0] == 'feature':
                branch = local if side == 'local' else remote
                owner = next((layer['id'] for layer in branch['layers']
                              if any(f['id'] == path[1] for f in layer['features'])), None)
                owners[path[1]] = owner
                if owner is not None and (owner not in selected or not any(
                        f['id'] == path[1] for f in selected[owner]['features'])):
                    raise ValueError('CONFLICT_CHOICES_INCOMPATIBLE')
        for layer_id, layer in selected.items():
            layer['features'] = [f for f in layer['features']
                                 if f['id'] not in owners or owners[f['id']] == layer_id]
            for index, feature in enumerate(layer['features']):
                path = ('feature', feature['id'])
                if path in choices:
                    branch = local if choices[path] == 'local' else remote
                    layer['features'][index] = copy.deepcopy(next(f for l in branch['layers']
                        for f in l['features'] if f['id'] == feature['id']))
    seen = set()
    for layer in selected.values():
        for feature in layer['features']:
            if feature['id'] in seen:
                conflicts.append(('feature', feature['id']))
            seen.add(feature['id'])
    if conflicts:
        raise SyncConflict(dict.fromkeys(conflicts))
    result['layers'] = [selected[layer_id] for layer_id in order]
    validate_editor_layers(result)
    return result


class SyncState:
    """State transitions only; caller owns durable outbox, authentication and I/O."""
    def __init__(self, remote, revision):
        self._revision(revision)
        validate_editor_layers(remote)
        self.base = copy.deepcopy(remote)
        self.local = copy.deepcopy(remote)
        self.revision = revision
        self.conflicts = ()

    @staticmethod
    def _revision(value):
        if type(value) is not int or not 0 <= value <= 2**31 - 1:
            raise ValueError('INVALID_REMOTE_REVISION')

    @property
    def pending(self):
        return not _equal(self.base, self.local)

    def edit(self, document):
        validate_editor_layers(document)
        self.local = copy.deepcopy(document)

    def reconcile(self, remote, revision):
        self._revision(revision)
        if revision < self.revision:
            raise ValueError('STALE_REMOTE_REVISION')
        if revision == self.revision and not _equal(remote, self.base):
            raise ValueError('REMOTE_REVISION_CONTENT_CHANGED')
        try:
            merged = merge_snapshots(self.base, self.local, remote)
        except SyncConflict as error:
            self.conflicts = error.paths
            raise
        self.base, self.local = copy.deepcopy(remote), merged
        self.revision, self.conflicts = revision, ()
        return copy.deepcopy(self.local)

    def submission(self):
        if self.conflicts:
            raise SyncConflict(self.conflicts)
        return self.revision, copy.deepcopy(self.local)

    def acknowledged(self, sent_document, expected_revision, new_revision):
        self._revision(expected_revision)
        self._revision(new_revision)
        validate_editor_layers(sent_document)
        if expected_revision != self.revision or new_revision not in (expected_revision, expected_revision + 1):
            raise ValueError('STALE_OR_INVALID_ACKNOWLEDGEMENT')
        if new_revision == expected_revision and not _equal(sent_document, self.base):
            raise ValueError('ACKNOWLEDGEMENT_DID_NOT_ADVANCE')
        # An edit made during the HTTP request stays pending against this new base.
        self.base = copy.deepcopy(sent_document)
        self.revision = new_revision
        self.conflicts = ()

    def checkpoint(self, destination):
        """Atomically persist pending edits without storing account credentials."""
        data = {'schema': 'xnby.layer-sync.state.v1', 'revision': self.revision,
                'base': self.base, 'local': self.local, 'conflicts': self.conflicts}
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False).encode('utf-8')
        envelope = json.dumps({'sha256': hashlib.sha256(payload).hexdigest(),
                               'payload': payload.decode('utf-8')}, ensure_ascii=False).encode('utf-8')
        if len(envelope) > 40 * 1048576:
            raise ValueError('SYNC_CHECKPOINT_TOO_LARGE')
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.layer-sync-', delete=False) as stream:
                temp_path = Path(stream.name)
                stream.write(envelope)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
            temp_path = None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    @classmethod
    def resume(cls, source):
        from services.common import loads
        with Path(source).open('rb') as stream:
            raw = stream.read(40 * 1048576 + 1)
        if len(raw) > 40 * 1048576:
            raise ValueError('SYNC_CHECKPOINT_TOO_LARGE')
        envelope = loads(raw)
        if not isinstance(envelope, dict) or set(envelope) != {'sha256', 'payload'}:
            raise ValueError('INVALID_SYNC_CHECKPOINT')
        payload = envelope['payload'].encode('utf-8')
        if hashlib.sha256(payload).hexdigest() != envelope['sha256']:
            raise ValueError('SYNC_CHECKPOINT_CORRUPT')
        data = loads(payload)
        if set(data) != {'schema', 'revision', 'base', 'local', 'conflicts'} or data['schema'] != 'xnby.layer-sync.state.v1':
            raise ValueError('INVALID_SYNC_CHECKPOINT')
        result = cls(data['base'], data['revision'])
        result.edit(data['local'])
        if not isinstance(data['conflicts'], list) or any(
                not isinstance(p, list) or len(p) != 2 or any(not isinstance(v, str) for v in p)
                for p in data['conflicts']):
            raise ValueError('INVALID_SYNC_CHECKPOINT')
        result.conflicts = tuple(tuple(p) for p in data['conflicts'])
        return result
