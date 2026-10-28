"""One pinned, read-only public index for complete BC7 and hybrid textures."""
import json
import re
from urllib.parse import urlsplit

from readonly_texture_store import ReadOnlyTextureStore
from readonly_hybrid_store import ReadOnlyHybridStore

FULL = re.compile(r'/prepared-textures/([0-9a-f]{64})/([0-9a-f]{64})/(manifest\.json|texture\.bc7)')
HYBRID = re.compile(r'/prepared-hybrid-textures/([0-9a-f]{64})/([0-9a-f]{64})/(manifest\.json|prefix\.bc7|tail\.rgba|overlap\.rgba)')


class ReadOnlyTextureUnion:
    def __init__(self, complete_configuration, hybrid_configuration=None):
        self.complete = ReadOnlyTextureStore(complete_configuration)
        self.hybrid = ReadOnlyHybridStore(hybrid_configuration) if hybrid_configuration else None
        self._index = []
        seen = set()
        for store, kind in ((self.complete, 'bc7'), (self.hybrid, 'bc7_rgba_overlap')):
            if store is None:
                continue
            for row in store.index()['entries']:
                source = row['sourceSHA256']
                if source in seen:
                    raise ValueError('A source texture has competing prepared representations')
                seen.add(source)
                self._index.append(dict(sourceSHA256=source, payloadSHA256=row['payloadSHA256'], format=kind))
        if len(self._index) > 4096:
            raise ValueError('Combined prepared texture index exceeds bounds')
        self._index.sort(key=lambda row: row['sourceSHA256'])

    def index(self):
        return dict(schema='xnby.prepared_texture_index.v2', entries=[dict(row) for row in self._index])

    def handle(self, handler):
        parsed = urlsplit(handler.path)
        recognized = parsed.path == '/api/prepared-textures' or parsed.path.startswith(('/prepared-textures/', '/prepared-hybrid-textures/'))
        if not recognized:
            return False
        if handler.command not in ('GET', 'HEAD'):
            handler.reply(405, b'{"error":"READ_ONLY_TEXTURES"}')
            return True
        full, hybrid = FULL.fullmatch(parsed.path), HYBRID.fullmatch(parsed.path)
        if parsed.query or parsed.fragment or parsed.path != '/api/prepared-textures' and not (full or hybrid):
            handler.reply(400, b'{"error":"INVALID_TEXTURE_ROUTE"}')
            return True
        try:
            if parsed.path == '/api/prepared-textures':
                handler.reply(200, json.dumps(self.index()).encode())
            elif full:
                source, digest, name = full.groups()
                if name == 'manifest.json':
                    handler.reply(200, json.dumps(self.complete.descriptor(source, digest)).encode())
                else:
                    handler.reply(200, self.complete.payload(source, digest), 'application/octet-stream')
            else:
                if self.hybrid is None:
                    raise ValueError('Hybrid texture is not configured')
                source, digest, name = hybrid.groups()
                if name == 'manifest.json':
                    handler.reply(200, json.dumps(self.hybrid.descriptor(source, digest)).encode())
                else:
                    handler.reply(200, self.hybrid.payload(source, digest, name), 'application/octet-stream')
        except (OSError, ValueError, KeyError, TypeError):
            handler.reply(409, b'{"error":"PREPARED_TEXTURE_UNAVAILABLE"}')
        return True
