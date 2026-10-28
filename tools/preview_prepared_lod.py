"""Read verified existing GLTF pages only. No converter, executable or cache writes."""
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
import hashlib
import json
import re

from preview_prepared_sources import PreparedSources
from native_cache_leases import LeaseRegistry


class PreviewPreparedLOD:
    def __init__(self, resources, additional_resources=()):
        self.sources = PreparedSources(resources, additional_resources)
        self.owners = {}
        self.leases = LeaseRegistry(read_only=True)
        self.requests = self.loaded = self.unavailable = 0

    def close(self):
        self.leases.close()

    def health(self):
        return dict(application='xnby.landscape.web.v1', status='prepared-preview',
                    lodAccess='read_only', conversionEnabled=False, nativeReaderEnabled=False,
                    descriptorPlanSchema='xnby.source_bundle_plan.v1',
                    scope='existing_verified_bundles_only', sourceCoveragePolicy='prepared_visible_roots_first_v1', requests=self.requests,
                    loaded=self.loaded, unavailable=self.unavailable, preparedSourceCount=len(self.sources.stores))

    def handle(self, handler):
        parsed = urlsplit(handler.path)
        route = unquote(parsed.path)
        if route == '/api/health':
            handler.reply(200, json.dumps(self.health()).encode())
            return True
        if route == '/api/prepared-textures':
            handler.reply(200, b'{"schema":"xnby.prepared_texture_index.v1","entries":[]}')
            return True
        if not route.startswith(('/api/lod', '/native/')):
            return False
        token = None
        try:
            # Only lease release is writable HTTP; it changes process RAM, never files.
            release = re.fullmatch(r'/api/lod-lease/([0-9a-f]{32})/release', route)
            if release:
                if handler.command != 'POST' or parsed.query:
                    handler.reply(405, b'{"error":"POST_REQUIRED"}')
                    return True
                self.leases.release(release[1])
                self.owners.pop(release[1], None)
                handler.reply(204, b'')
                return True
            if handler.command not in ('GET', 'HEAD'):
                handler.reply(405, b'{"error":"READ_ONLY"}')
                return True
            payload = re.fullmatch(r'/native/((?:tile_\d+_depth_\d+|family_tile_\d+_[0-9a-f]{16}))/(part_\d{3})/(geometry\.gltf|geometry\.bin|atlas\.jpg)', route)
            if payload:
                query = parse_qs(parsed.query, strict_parsing=True, max_num_fields=1)
                values = query.get('lease', [])
                if set(query) != {'lease'} or len(values) != 1 or not re.fullmatch('[0-9a-f]{32}', values[0]):
                    raise ValueError('A matching live lease is required')
                name, part, filename = payload.groups()
                store = self.owners.get(values[0])
                if store is None:raise PermissionError('No live bundle owner')
                with self.leases.use(values[0], store.cache, name):
                    raw = store.payload(name, part, filename)
                handler.reply(200, raw, 'model/gltf+json' if filename.endswith('gltf') else 'image/jpeg' if filename.endswith('jpg') else 'application/octet-stream')
                return True
            root = re.fullmatch(r'/api/lod(-plan)?/(\d{1,4})/(\d{1,2})', route)
            family = re.fullmatch(r'/api/lod-family(-plan)?/(\d{1,4})/(Tile_\d+_L\d+_0[0-9u]+\.osgb)', route)
            if not root and not family:
                handler.reply(404, b'{"error":"NOT_FOUND"}')
                return True
            plan, tile, value = (root or family).groups()
            if parsed.query and not (plan and parsed.query == 'wait_ms=200'):
                raise ValueError('Unexpected query')
            tile = int(tile)
            args = {'depth': int(value)} if root else {'parent': value}
            if not 1 <= tile <= 2346 or (root and not 1 <= int(value) <= 12) or (family and not re.fullmatch(r'Tile_'+str(tile)+r'_L\d+_0[0-9u]+\.osgb', value)):
                raise ValueError('Invalid source identity')
            self.requests += 1
            name = f'tile_{tile}_depth_{value}' if root else f'family_tile_{tile}_'+hashlib.sha256(value.encode()).hexdigest()[:16]
            store, selected_plan = self.sources.select(name, tile, **args)
            if plan:
                result = selected_plan
            else:
                loaded = {}
                def validate():
                    loaded['marker'], loaded['sha'] = store.describe_with_identity(tile, **args)
                    self.sources.validate_catalog(loaded['marker'], tile)
                    if loaded['sha'] != selected_plan['markerSHA256']:raise ValueError('Prepared marker changed before admission')
                    return True
                token = self.leases.grant(store.cache, name, validate)
                with self.leases.lock:
                    active = set(self.leases.entries)
                for stale in list(self.owners):
                    if stale not in active:self.owners.pop(stale, None)
                self.owners[token] = store
                result = dict(loaded['marker'], cache_lease=token)
                self.loaded += 1
                handler.source_marker_sha256 = loaded['sha']
            handler.reply(200, json.dumps(result, allow_nan=False).encode())
        except (OSError, TimeoutError):
            if token:
                self.leases.release(token)
            self.unavailable += 1
            handler.reply(409, b'{"error":"PREPARED_LOD_UNAVAILABLE","keepParent":true,"conversionEnabled":false}')
        except (ValueError, RuntimeError, KeyError, TypeError):
            if token:
                self.leases.release(token)
            self.unavailable += 1
            handler.reply(422, b'{"error":"PREPARED_LOD_VALIDATION_FAILED","keepParent":true,"conversionEnabled":false}')
        return True
