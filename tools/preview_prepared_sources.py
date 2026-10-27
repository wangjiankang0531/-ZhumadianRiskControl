"""Explicit read-only resource roots with identical scene/catalog provenance."""
import hashlib
import json
from pathlib import Path
import re

from readonly_landscape_store import ReadOnlyLandscapeStore, owned, read_bytes, duplicates


class PreparedSources:
    def __init__(self, primary, additional=()):
        roots = [Path(primary).absolute(), *[Path(p).absolute() for p in additional]]
        if len(roots) > 4 or len({p.resolve() for p in roots}) != len(roots):
            raise ValueError('At most four distinct explicit prepared resource roots')
        self.stores = []
        self.catalog_sha256 = None
        self.catalogs = None
        for root in roots:
            store = ReadOnlyLandscapeStore(root)
            raw = read_bytes(owned(root, Path('data/showcase/zhumadian_native_hierarchy.json')), 16*1048576)
            digest = hashlib.sha256(raw).hexdigest()
            if self.catalog_sha256 is not None and digest != self.catalog_sha256:
                raise ValueError('Prepared resource roots describe different scenes')
            graph = json.loads(raw, object_pairs_hook=duplicates)
            rows = graph.get('root_records')
            if not isinstance(rows, list) or not 0 < len(rows) <= 2346:
                raise ValueError('Prepared source catalog is missing')
            catalogs = {}
            for row in rows:
                tile, sha = row.get('tile_id'), row.get('sha256')
                if type(tile) is not int or not 1 <= tile <= 2346 or tile in catalogs or not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
                    raise ValueError('Invalid prepared source catalog identity')
                catalogs[tile] = sha
            self.catalog_sha256, self.catalogs = digest, catalogs
            self.stores.append(store)

    def select(self, name, tile, **args):
        for store in self.stores:
            marker_path = owned(store.cache, Path(name)/'complete.json')
            if not marker_path.exists():
                continue
            # A present but corrupt primary is rejected, never silently bypassed.
            plan = store.plan(tile, **args)
            self.validate_catalog(plan['marker'], tile)
            return store, plan
        raise FileNotFoundError('No verified prepared bundle in the configured roots')

    def validate_catalog(self, marker, tile):
        if marker.get('stamp', {}).get('catalog_sha256') != self.catalogs.get(tile) or tile not in self.catalogs:
            raise ValueError('Prepared bundle source catalog differs from the scene')
