"""Compose explicit local editor layer sources in RAM; never modify source DLG."""
import copy
import hashlib
import json
from pathlib import Path
import stat

from landscape_layer_validation import validate_editor_layers
from readonly_landscape_store import duplicates

LIMIT = 16 * 1048576


def snapshot(path):
    for item in (path, *path.parents):
        info = item.lstat()
        if getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Layer source traverses a link')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= LIMIT:
        raise ValueError('Layer source size or type is invalid')
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


class ReadOnlyLayerSet:
    def __init__(self, primary, additional):
        self.paths = [Path(primary).absolute(), *[Path(p).absolute() for p in additional]]
        if not 2 <= len(self.paths) <= 4 or len({p.resolve() for p in self.paths}) != len(self.paths):
            raise ValueError('Choose two to four distinct layer sources')
        self.read()  # Refuse an invalid initial composition before publishing a service.

    def read(self):
        before = [snapshot(p) for p in self.paths]
        if sum(row[2] for row in before) > LIMIT:
            raise ValueError('Combined layer source exceeds 16 MiB')
        documents, sources = [], []
        def invalid(value):
            raise ValueError('Layer source contains a non-finite JSON number')
        for path, identity in zip(self.paths, before):
            with path.open('rb') as stream:
                raw = stream.read(identity[2]+1)
            if len(raw) != identity[2]:
                raise ValueError('Layer source changed while reading')
            document = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=duplicates, parse_constant=invalid)
            validate_editor_layers(document)
            documents.append(document)
            sources.append(dict(name=path.name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                                metadata={key:copy.deepcopy(value) for key,value in document.items() if key!='layers'}))
        if before != [snapshot(p) for p in self.paths]:
            raise ValueError('Layer sources changed during the combined read')
        result = copy.deepcopy(documents[0])
        result['layers'] = [copy.deepcopy(layer) for document in documents for layer in document['layers']]
        # Validate the complete set as a single transaction. In particular, never
        # rename or drop colliding IDs: business references must retain identity.
        validate_editor_layers(result)
        if 'viewerSourceDocuments' in result:
            raise ValueError('Layer source uses reserved composition metadata')
        result['viewerSourceDocuments'] = dict(schema='xnby.viewer.layer_sources.v1', readOnly=True, sources=sources)
        raw = json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(raw) > LIMIT:
            raise ValueError('Composed layer document exceeds 16 MiB')
        return raw


class ReadOnlyBusinessRecords:
    """Keep the original snapshot time/TTL and let the UI show its stale status."""
    def __init__(self, path):
        self.path = Path(path).absolute()
        self.read()

    def read(self):
        from services.data import validate_records
        before = snapshot(self.path)
        with self.path.open('rb') as stream:
            raw = stream.read(before[2]+1)
        if len(raw) != before[2] or snapshot(self.path) != before:
            raise ValueError('Business snapshot changed while reading')
        def invalid(value):
            raise ValueError('Business snapshot contains non-finite JSON')
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=duplicates, parse_constant=invalid)
        validate_records(value)
        return raw
