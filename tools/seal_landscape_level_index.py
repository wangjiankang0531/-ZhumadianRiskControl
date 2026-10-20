"""Seal a complete exact LEVEL index for immutable, lazy-verified deployment."""
import argparse
from collections import Counter
import json
from pathlib import Path

from build_landscape_level_index import write
from landscape_level_index import bounds, union
from native_source_frontier import SourceForest
from osgb_memory_pages import sha
from readonly_source_memory_store import PinnedCatalogs


def seal(directory, resources):
    directory, resources = Path(directory), Path(resources)
    phase = json.loads((directory/'build_phase.json').read_text('utf-8'))
    catalogs = PinnedCatalogs(resources)
    master = json.loads((resources/'data/showcase/zhumadian_native_hierarchy.json').read_text('utf-8'))
    if (phase['status'] != 'verified' or phase['sourceManifestSHA256'] != catalogs.identity or
            set(phase['completedTiles']) != set(catalogs.records)):
        raise ValueError('the whole source forest has not completed exact indexing')
    files, roots, levels = [], [], Counter()
    total = 0
    for row in master['root_records']:
        tile = row['tile_id']
        path = directory/f'tile_{tile}.json'
        raw = path.read_bytes()
        data = json.loads(raw)
        catalog = catalogs(tile)
        forest = SourceForest(catalog)
        expected = {name for name in forest.depths if forest.nodes[name]['level'] is not None}
        nodes = {n['name']: n for n in data['nodes']}
        if (data.get('complete') is not True or data['tile'] != tile or data['catalogSHA256'] != row['sha256'] or
                data['sourceManifestSHA256'] != catalogs.identity or set(nodes) != expected or
                len(nodes) != len(data['nodes'])):
            raise ValueError(f'incomplete or mismatched level metadata for tile {tile}')
        for name, n in nodes.items():
            if n['sourceSHA256'] != forest.nodes[name]['sha256'] or n['sourceBytes'] != forest.nodes[name]['bytes']:
                raise ValueError('indexed node source identity changed')
            bounds(n['boundsMin'], n['boundsMax'])
            bounds(n['subtreeMin'], n['subtreeMax'])
            levels[n['level']] += 1
        low, high = union([bounds(data['boundsMin'], data['boundsMax']), bounds(row['bounds_min'], row['bounds_max'])])
        roots.append(dict(id=tile, tile=tile, level=0, boundsMin=low, boundsMax=high,
                          catalogSHA256=row['sha256']))
        files.append(dict(tile=tile, path=path.name, bytes=len(raw), sha256=sha(raw), sourceNodes=len(nodes)))
        total += len(nodes)
    root_index = dict(schema='zhumadian.level_bounds.roots.v1', sourceManifestSHA256=catalogs.identity,
                      coordinateSystem='source_local_metres', boundsSource='union_of_original_subtree_geometry', roots=roots)
    write(directory/'root_index.json', root_index)
    manifest = dict(schema='zhumadian.level_bounds.manifest.v1', sourceManifestSHA256=catalogs.identity,
                    tiles=files, sourceNodes=total, levelCounts=dict(sorted(levels.items())),
                    rootIndexSHA256=sha((directory/'root_index.json').read_bytes()),
                    boundsSource='exact_original_geometry', sourceWrites=0)
    write(directory/'index_manifest.json', manifest)
    return dict(roots=len(roots), sourceNodes=total, levelCounts=manifest['levelCounts'],
                manifestSHA256=sha((directory/'index_manifest.json').read_bytes()),
                bytes=sum(r['bytes'] for r in files), sourceWrites=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--resources', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(seal(args.index, args.resources), ensure_ascii=False, indent=2))
