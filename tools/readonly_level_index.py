"""Deliver an existing sealed LEVEL index without readers, conversion or writes."""
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from landscape_level_index import bounds, union
from native_source_frontier import SourceForest
from readonly_landscape_store import duplicates, owned, read_bytes

MIB = 1048576
SHA = re.compile(r'[0-9a-f]{64}')
FILE = re.compile(r'/api/level-index/files/(index_manifest\.json|root_index\.json|tile_[1-9][0-9]{0,3}\.json)')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def invalid(value):
        raise ValueError('Non-finite LEVEL JSON value')
    return json.loads(raw, object_pairs_hook=duplicates, parse_constant=invalid)


class ReadOnlyLevelIndex:
    def __init__(self, directory, resources):
        self.directory = Path(directory).absolute()
        self.resources = Path(resources).absolute()
        source_raw = self.read_source('data/showcase/zhumadian_native_hierarchy.json')
        self.source_identity = digest(source_raw)
        source = parse(source_raw)
        rows = source['root_records']
        self.sources = {r['tile_id']: r for r in rows}
        require(len(rows) == len(self.sources) == 2346 and set(self.sources) == set(range(1, 2347)),
                'LEVEL source forest must contain all 2346 roots')
        raw = self.read_index('index_manifest.json', 4*MIB)
        manifest = parse(raw)
        require(manifest.get('schema') == 'zhumadian.level_bounds.manifest.v1'
                and manifest.get('sourceManifestSHA256') == self.source_identity
                and manifest.get('boundsSource') == 'exact_original_geometry'
                and type(manifest.get('sourceWrites')) is int and manifest['sourceWrites'] == 0,
                'LEVEL manifest source identity differs')
        rows = manifest['tiles']
        require(isinstance(rows, list) and len(rows) == 2346, 'Incomplete LEVEL manifest')
        self.records = {}
        for row in rows:
            tile = row['tile']
            require(type(tile) is int and tile in self.sources and tile not in self.records
                    and row['path'] == f'tile_{tile}.json'
                    and type(row['bytes']) is int and 0 < row['bytes'] <= 16*MIB
                    and type(row['sourceNodes']) is int and row['sourceNodes'] > 0
                    and isinstance(row['sha256'], str) and SHA.fullmatch(row['sha256']),
                    'Invalid LEVEL file identity')
            self.records[tile] = dict(row)
        require(type(manifest.get('sourceNodes')) is int
                and manifest['sourceNodes'] == sum(r['sourceNodes'] for r in rows),
                'LEVEL source count differs')
        self.identity = digest(raw)
        self.root_identity = manifest['rootIndexSHA256']
        require(isinstance(self.root_identity, str) and SHA.fullmatch(self.root_identity),
                'Invalid LEVEL root identity')
        root_raw = self.read_index('root_index.json', 4*MIB)
        require(digest(root_raw) == self.root_identity, 'LEVEL root SHA differs')
        root = parse(root_raw)
        require(root.get('schema') == 'zhumadian.level_bounds.roots.v1'
                and root.get('sourceManifestSHA256') == self.source_identity
                and root.get('coordinateSystem') == 'source_local_metres'
                and root.get('boundsSource') == 'union_of_original_subtree_geometry'
                and isinstance(root.get('roots'), list) and len(root['roots']) == 2346,
                'Invalid LEVEL root index')
        self.roots = {}
        for row in root['roots']:
            tile = row['tile']
            require(type(tile) is int and tile in self.sources and tile not in self.roots
                    and type(row['id']) is int and row['id'] == tile
                    and row['catalogSHA256'] == self.sources[tile]['sha256'],
                    'LEVEL root catalog differs')
            box = bounds(row['boundsMin'], row['boundsMax'])
            base = self.sources[tile]
            require(union([box, bounds(base['bounds_min'], base['bounds_max'])]) == box,
                    'LEVEL root excludes base geometry')
            tiers = row.get('coverageTiers')
            require(isinstance(tiers, list) and len(tiers) == 3, 'Missing measured LEVEL coverage tiers')
            for depth, tier in enumerate(tiers, 1):
                require(type(tier.get('depth')) is int and tier['depth'] == depth
                        and type(tier.get('sourceCount')) is int and tier['sourceCount'] > 0
                        and type(tier.get('maxTexel')) in (int, float)
                        and math.isfinite(tier['maxTexel']) and tier['maxTexel'] > 0,
                        'Invalid measured LEVEL coverage tier')
            self.roots[tile] = row

    def read_source(self, relative):
        return read_bytes(owned(self.resources, Path(relative)), 16*MIB)

    def read_index(self, name, limit):
        return read_bytes(owned(self.directory, Path(name)), limit)

    def verify_manifest(self):
        require(digest(self.read_index('index_manifest.json', 4*MIB)) == self.identity,
                'Sealed LEVEL manifest changed')

    def file(self, name):
        self.verify_manifest()
        if name == 'index_manifest.json':
            raw = self.read_index(name, 4*MIB)
            require(digest(raw) == self.identity, 'Sealed LEVEL manifest changed')
            return raw
        if name == 'root_index.json':
            raw = self.read_index(name, 4*MIB)
            require(digest(raw) == self.root_identity, 'LEVEL root SHA differs')
            return raw
        match = re.fullmatch(r'tile_([1-9][0-9]{0,3})\.json', name)
        require(match is not None and int(match[1]) in self.records, 'Unlisted LEVEL file')
        tile = int(match[1])
        entry = self.records[tile]
        raw = self.read_index(name, 16*MIB)
        require(len(raw) == entry['bytes'] and digest(raw) == entry['sha256'], 'LEVEL tile SHA differs')
        self.validate_tile(tile, parse(raw))
        return raw

    def validate_tile(self, tile, data):
        record = self.sources[tile]
        require(record['catalog'] == f'assets/showcase/runtime/zhumadian/native_hierarchy/tile_{tile}.json',
                'Unexpected LEVEL catalog path')
        raw = self.read_source(record['catalog'])
        require(digest(raw) == record['sha256'], 'LEVEL source catalog SHA differs')
        forest = SourceForest(parse(raw))
        require(data.get('schema') == 'zhumadian.level_bounds.tile.v1' and data.get('complete') is True
                and data.get('tile') == tile and data.get('sourceManifestSHA256') == self.source_identity
                and data.get('catalogSHA256') == record['sha256'] and data.get('root') == forest.root
                and data.get('roots') == [forest.root], 'LEVEL tile source identity differs')
        nodes = {n['name']: n for n in data['nodes']}
        require(len(nodes) == len(data['nodes']) == self.records[tile]['sourceNodes']
                and set(nodes) == set(forest.depths), 'Incomplete LEVEL topology')
        for name, n in nodes.items():
            original = forest.nodes[name]
            require(n['sourceSHA256'] == original['sha256'] and n['sourceBytes'] == original['bytes']
                    and n['children'] == original['children'] and n['depth'] == forest.depths[name]
                    and n['level'] == original['level'], 'LEVEL node source identity differs')
            require(all(type(n.get(k)) in (int, float) and math.isfinite(n[k]) and n[k] > 0
                        for k in ('edgeP90', 'texelP90')), 'Invalid LEVEL detail metric')
            own = bounds(n['boundsMin'], n['boundsMax'])
            envelope = union([own] + [bounds(nodes[c]['subtreeMin'], nodes[c]['subtreeMax']) for c in n['children']])
            require(bounds(n['subtreeMin'], n['subtreeMax']) == envelope, 'LEVEL subtree envelope differs')
        root = self.roots[tile]
        box = bounds(root['boundsMin'], root['boundsMax'])
        require(union([box, bounds(data['boundsMin'], data['boundsMax']),
                       bounds(nodes[forest.root]['subtreeMin'], nodes[forest.root]['subtreeMax'])]) == box,
                'LEVEL root excludes descendants')
        cut = {forest.root}
        for depth in range(1, 4):
            cut = {child for name in cut for child in forest.nodes[name]['children'] or [name]}
            forest.validate_cut(cut)
            require(root['coverageTiers'][depth-1] == dict(depth=depth, sourceCount=len(cut),
                    maxTexel=max(nodes[name]['texelP90'] for name in cut)), 'LEVEL coverage tier differs')

    def handle(self, handler):
        parsed = urlsplit(handler.path)
        if not parsed.path.startswith('/api/level-index'):
            return False
        if handler.command not in ('GET', 'HEAD'):
            handler.reply(405, b'{"error":"READ_ONLY_LEVEL_INDEX"}')
            return True
        match = FILE.fullmatch(parsed.path)
        if parsed.query or parsed.fragment or (parsed.path != '/api/level-index/status' and match is None):
            handler.reply(400, b'{"error":"INVALID_LEVEL_INDEX_ROUTE"}')
            return True
        try:
            if match:
                raw = self.file(match[1])
            else:
                self.verify_manifest()
                raw = json.dumps(dict(schema='zhumadian.level_bounds.status.v1', identity=self.identity,
                                      roots=len(self.records), exactBounds=True, sourceWrites=False)).encode()
            handler.reply(200, raw, headers={'X-XNBY-Level-Index-SHA256': self.identity})
        except (ValueError, KeyError, TypeError, OSError, RecursionError):
            handler.reply(422, b'{"error":"SEALED_LEVEL_INDEX_UNAVAILABLE"}')
        return True
