"""Indexed complete descendant cuts, using the existing bounded RAM lease store."""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import re
from urllib.parse import parse_qs, urlsplit

from landscape_level_index import Camera, select_cut
from native_source_frontier import SourceForest
from osgb_cropped_pages import build_bundle
from osgb_memory_pages import SourceBundle, canonical, sha
from readonly_source_memory_store import MemorySourceStore, MemoryStoreBusy, ordinary
from source_memory_http import MemorySourceHTTP


class LevelIndexProvider:
    def __init__(self, directory, catalogs):
        self.directory = Path(directory).resolve(strict=True)
        raw = ordinary(self.directory/'index_manifest.json', self.directory).read_bytes()
        if len(raw) > 4*1048576:
            raise ValueError('level index manifest exceeds bounds')
        manifest = json.loads(raw)
        if manifest.get('schema') != 'zhumadian.level_bounds.manifest.v1' or manifest.get('sourceManifestSHA256') != catalogs.identity:
            raise ValueError('level index belongs to another source forest')
        self.identity = sha(raw)
        self.manifest = manifest
        self.records = {r['tile']: r for r in manifest['tiles']}
        if len(self.records) != len(manifest['tiles']) or set(self.records) != set(catalogs.records):
            raise ValueError('level index must cover all source roots')
        self.catalogs = catalogs
        self.cache = OrderedDict()

    def index_file(self, name):
        """Return only a SHA-pinned public index record, never a source path."""
        if name == 'index_manifest.json':
            identity, limit, size = self.identity, 4*1048576, None
        elif name == 'root_index.json':
            identity, limit, size = self.manifest['rootIndexSHA256'], 4*1048576, None
        else:
            match = re.fullmatch(r'tile_([1-9][0-9]{0,3})\.json', name)
            if match is None or int(match[1]) not in self.records:
                raise ValueError('index file is not in sealed manifest')
            record = self.records[int(match[1])]
            if record['path'] != name:
                raise ValueError('index file path differs')
            identity, limit, size = record['sha256'], 16*1048576, record['bytes']
        if not re.fullmatch(r'[0-9a-f]{64}', identity):
            raise ValueError('index file identity unavailable')
        path = ordinary(self.directory/name, self.directory)
        if path.stat().st_size > limit:
            raise ValueError('index file exceeds delivery bound')
        with path.open('rb') as stream:
            raw = stream.read(limit+1)
        if len(raw) > limit or (size is not None and len(raw) != size) or sha(raw) != identity:
            raise ValueError('sealed index file SHA differs')
        return raw

    def tile(self, tile):
        if tile in self.cache:
            self.cache.move_to_end(tile)
            return self.cache[tile]
        entry = self.records[tile]
        if entry['path'] != f'tile_{tile}.json':
            raise ValueError('invalid indexed tile path')
        raw = ordinary(self.directory/entry['path'], self.directory).read_bytes()
        if len(raw) > 16*1048576 or len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
            raise ValueError('exact level index SHA differs')
        data = json.loads(raw)
        catalog = self.catalogs(tile)
        forest = SourceForest(catalog)
        nodes = {n['name']: n for n in data['nodes']}
        expected = {n for n in forest.depths if forest.nodes[n].get('level') is not None}
        if (data.get('schema') != 'zhumadian.level_bounds.tile.v1' or data.get('complete') is not True or
                data.get('tile') != tile or data.get('catalogSHA256') != self.catalogs.records[tile]['sha256'] or
                set(nodes) != expected or len(nodes) != len(data['nodes'])):
            raise ValueError('incomplete or different indexed source graph')
        for name, n in nodes.items():
            original = forest.nodes[name]
            if (n['sourceSHA256'] != original['sha256'] or n['sourceBytes'] != original['bytes'] or
                    n['children'] != original['children'] or n['depth'] != forest.depths[name]):
                raise ValueError('indexed source identity or topology differs')
        self.cache[tile] = data
        while len(self.cache) > 16:
            self.cache.popitem(last=False)
        return data


class IndexedFamilyStore(MemorySourceStore):
    def __init__(self, catalogs, reader, index_provider, **options):
        self.index_provider = index_provider
        self.index_requests = OrderedDict()
        def builder(tile, catalog, source_reader, *, depth=None, parent=None, recipe_identity):
            if parent is not None and parent.startswith('indexed-'):
                request = self.index_requests[parent]
                while True:
                    try:
                        return build_bundle(tile, catalog, source_reader, parent=request['parent'],
                                            selection=request['selection'], recipe_identity=recipe_identity)
                    except ValueError as error:
                        limits=('64-page bound', 'delivery bound', 'bundle budget',
                                'source UV footprint crosses a periodic or image seam',
                                'mipmapped original image requires per-mip crop gutters',
                                'source mesh exceeds unchanged physical-page count',
                                'source exceeds unchanged physical-page count',
                                'one original triangle cannot fit the unchanged page limit',
                                'complete source node exceeds unchanged RAM payload limit')
                        if not any(text in str(error) for text in limits):
                            raise
                        data = self.index_provider.tile(tile)
                        nodes = {n['name']: n for n in data['nodes']}
                        direct = nodes[request['parent']]['children']
                        if set(request['selection']) == set(direct):
                            with self.lock:
                                request['selectionLimitedByBudget']=True
                            raw=canonical(dict(schema='zhumadian.indexed_quality_limit.v1',tile_id=tile,
                                               replacement_parent=request['parent'],complete_parent_retained=True,
                                               reason_code='lossless_texture_or_page_limit',index_identity=index_provider.identity))
                            # A successful metadata-only outcome, without a lease or fake source cut.
                            return SourceBundle(raw,MappingProxyType({}),
                                                f"family_tile_{tile}_{sha(request['parent'].encode())[:16]}",len(raw))
                        max_depth = max(nodes[n]['depth'] for n in request['selection'])-1
                        selected, stats = select_cut({**data, 'roots': direct}, request['camera'],
                                                     request['selectedPixels'], max_depth=max_depth)
                        with self.lock:
                            request.update(selection=selected, queryStats=stats, selectedMaxDepth=max_depth,
                                           selectionLimitedByBudget=True)
            return build_bundle(tile, catalog, source_reader, depth=depth, parent=parent, recipe_identity=recipe_identity)
        identity = sha(Path(__file__).read_bytes()+index_provider.identity.encode())
        super().__init__(catalogs, reader, builder=builder, builder_identity=identity, **options)

    @staticmethod
    def key(tile, depth, parent):
        if type(tile) is int and 1 <= tile <= 2346 and depth is None and isinstance(parent, str) and re.fullmatch(r'indexed-[0-9a-f]{32}', parent):
            return tile, None, parent
        return MemorySourceStore.key(tile, depth, parent)

    def register_view(self, tile, parent, camera, target_pixels=6.0):
        with self.lock:
            data = self.index_provider.tile(tile)
            nodes = {n['name']: n for n in data['nodes']}
            if parent not in nodes or not nodes[parent]['children']:
                raise ValueError('indexed refinement requires a nonterminal original source')
            view = [*camera.position, *camera.target, camera.fov, camera.aspect, camera.height, target_pixels]
            token = sha(canonical(dict(tile=tile, parent=parent, view=view, index=self.index_provider.identity)))[:32]
            key = 'indexed-'+token
            if key in self.index_requests:
                self.index_requests.move_to_end(key)
                return key
            branch = {**data, 'roots': nodes[parent]['children']}
            pixels = target_pixels
            while True:
                selected, stats = select_cut(branch, camera, pixels)
                if len(selected) <= 16:
                    break
                pixels *= 2
                if pixels > 65536:
                    raise ValueError('complete indexed branch exceeds source-count bound')
            while len(self.index_requests) >= 256:
                idle = next((k for k, r in self.index_requests.items()
                             if self.key(r['tile'], None, k) not in self.jobs and
                             not self.entries.get(self.key(r['tile'], None, k), {}).get('refs', 0)), None)
                if idle is None:
                    raise MemoryStoreBusy('all indexed view requests are leased or preparing')
                previous = self.index_requests.pop(idle)
                self.entries.pop(self.key(previous['tile'], None, idle), None)
            self.index_requests[key] = dict(tile=tile, parent=parent, selection=selected,
                                            requestedPixels=target_pixels, selectedPixels=pixels, queryStats=stats, camera=camera,
                                            selectionLimitedByBudget=False)
            return key


class IndexedFamilyHTTP(MemorySourceHTTP):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path.startswith('/api/level-index/files/'):
            match = re.fullmatch(r'/api/level-index/files/(index_manifest\.json|root_index\.json|tile_[1-9][0-9]{0,3}\.json)', parsed.path)
            if parsed.query or match is None:
                return self.send_error(400)
            try:
                raw = self.memory_sources.index_provider.index_file(match[1])
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(raw)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-XNBY-Level-Index-SHA256', self.memory_sources.index_provider.identity)
                self.end_headers()
                self.wfile.write(raw)
            except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
                self._memory_error(error)
            return
        if parsed.path == '/api/level-index/status':
            if parsed.query:
                return self.send_error(400)
            provider = self.memory_sources.index_provider
            return self._memory_json(dict(schema='zhumadian.level_bounds.status.v1', identity=provider.identity,
                                          roots=len(provider.records), exactBounds=True, sourceWrites=False))
        plan = re.fullmatch(r'/api/lod-index-family-plan/([0-9]+)/(Tile_[0-9]+_L[0-9]+_0[0-9u]+\.osgb)', parsed.path)
        bundle = re.fullmatch(r'/api/lod-index-family/([0-9]+)/([0-9a-f]{32})', parsed.path)
        if plan:
            try:
                query = parse_qs(parsed.query, strict_parsing=True, max_num_fields=2, keep_blank_values=True)
                if set(query) not in ({'view'}, {'view', 'wait_ms'}) or len(query['view']) != 1 or len(query['view'][0]) > 512:
                    raise ValueError('one bounded indexed view is required')
                wait_ms = self._plan_wait_ms(query)
                values = [float(n) for n in query['view'][0].split(',')]
                if (len(values) != 10 or any(not (-1e7 <= n <= 1e7) for n in values[:6]) or
                        not 1 <= values[8] <= 16384 or values[8] != int(values[8]) or not .25 <= values[9] <= 512):
                    raise ValueError('invalid indexed view values')
                camera = Camera(tuple(values[:3]), tuple(values[3:6]), values[6], values[7], int(values[8]))
                tile = int(plan[1])
                key = self.memory_sources.register_view(tile, plan[2], camera, values[9])
                result = self.memory_sources.plan(tile, parent=key, wait_ms=wait_ms)
                request = self.memory_sources.index_requests[key]
                self._memory_json({**(result or {'status': 'preparing_indexed_source'}),
                                   'indexedRequest': key[8:], 'requestedPixels': request['requestedPixels'],
                                   'selectedPixels': request['selectedPixels'], 'queryStats': request['queryStats'],
                                   'selectionLimitedByBudget': request['selectionLimitedByBudget'],
                                   'selectedMaxDepth': request.get('selectedMaxDepth')},
                                  200 if result is not None else 202,
                                  plan_wait_ms=wait_ms if "wait_ms" in query else None)
            except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
                self._memory_error(error)
            return
        if bundle:
            # Common RAM bundle handler validates the optional bounded wait.
            return self._readonly_bundle(int(bundle[1]), parent='indexed-'+bundle[2])
        return super().do_GET()
