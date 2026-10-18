"""Independently check source-family LOD rays against exact displayed glTF triangles.

QA-only: requires NumPy. Reads existing caches; never converts or repairs them.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reconstruct_cut(catalog, base_nodes, family_nodes):
    """Use the original tree, not the renderer's frontier implementation."""
    tree = {n['name']: n for n in catalog['nodes']}
    assert len(tree) == len(catalog['nodes'])
    depths = {}
    def visit(name, depth):
        assert name in tree and name not in depths, 'Missing child, cycle or multiple parents'
        depths[name] = depth
        children = tree[name]['children']
        assert len(set(children)) == len(children)
        for child in children:
            visit(child, depth + 1)
    visit(catalog['root'], 0)
    def validate(records):
        names = [n['name'] for n in records]
        assert len(names) == len(set(names))
        for n in records:
            original = tree[n['name']]
            assert n['depth'] == depths[n['name']]
            assert len(n['children']) == len(set(n['children']))
            assert set(n['children']) == set(original['children'])
            assert n['source_sha256'] == original['sha256']
        return set(names)
    def complete(selected):
        consumed = set()
        def cover(name):
            if name in selected:
                consumed.add(name)
                return
            children = tree[name]['children']
            assert children, 'Visible cut has a hole'
            for child in children:
                cover(child)
        cover(catalog['root'])
        assert consumed == selected, 'Visible cut overlaps an ancestor'
    selected = validate(base_nodes)
    complete(selected)
    parents = [p for p, _ in family_nodes]
    assert len(parents) == len(set(parents)), 'Duplicate family parent'
    for parent, records in sorted(family_nodes, key=lambda pair: depths[pair[0]]):
        children = validate(records)
        assert parent in selected and children and children == set(tree[parent]['children'])
        selected.remove(parent)
        selected.update(children)
        complete(selected)
    return selected


def main():
    import numpy as np
    import verify_landscape_surface_pick as reference
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--stats', type=Path, required=True)
    parser.add_argument('--reference-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-visibility', action='store_true')
    parser.add_argument('--prepared-assets', type=Path, help='Verify the sealed external generation named by native_lod.prepared_assets')
    args = parser.parse_args()
    package = args.package.resolve()
    reference_root = args.reference_root.resolve()
    assert not args.output.exists(), 'Do not overwrite an earlier verdict'
    data = read(args.stats)
    lod, probe = data['native_lod'], data['surface_pick']
    assert lod['picking_enabled'] and lod['settled'] and not lod['pending']
    assert not lod['partial_root_drawn'] and not lod['local_family_pending']
    assert not lod['local_family_error']
    assets = None
    if args.prepared_assets is not None:
        from verify_prepared_native_assets import PreparedAssets, require
        assets = PreparedAssets(package, args.prepared_assets)
        assets.require_runtime_identity(lod)
        require(not args.output.resolve().is_relative_to((assets.project/'Assets').resolve()),
                'Verification reports cannot be written into project assets')
    hierarchy = read(package / 'data/showcase/zhumadian_native_hierarchy.json')
    positions, indices = reference.mesh(reference_root / 'assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf')
    cp, ci = reference.mesh(reference_root / 'assets/showcase/runtime/zhumadian/context/context_fused.gltf')
    context = reference.reference_part(cp, ci, 0, 0)
    assert len(indices) == lod['base_indices']
    assert (len(indices) + len(ci)) // 3 == lod['base_picking_triangles']
    reference_inputs = []
    for kind, stem in [('full', 'zhumadian_full'), ('context', 'context_fused')]:
        for suffix in ('.gltf', '.bin'):
            path = reference_root / f'assets/showcase/runtime/zhumadian/{kind}/{stem}{suffix}'
            reference_inputs.append({'path': str(path), 'sha256': digest(path)})
    resident = {r['tile']: r for r in lod['resident']}
    assert len(resident) == len(lod['resident'])
    assert all(f['tile'] in resident for f in lod['local_families'])
    cache = assets.store if assets is not None else package / 'work/zhumadian_native_chunk_cache'
    def bundle_marker(folder):
        return assets.bundle(folder.name) if assets is not None else read(folder / 'complete.json')
    def evidence_path(path):
        return str(path) if assets is not None else str(path.relative_to(package))
    fine, hashes, cuts = [], [], []
    for tile, ready in resident.items():
        root = next(r for r in hierarchy['root_records'] if r['tile_id'] == tile)
        catalog_path = package / root['catalog']
        assert digest(catalog_path) == root['sha256']
        catalog = read(catalog_path)
        bundles = []
        base_folder = cache / f'tile_{tile}_depth_{ready["base_depth"]}'
        base = bundle_marker(base_folder)
        assert base['tile_id'] == tile and base['depth'] == ready['base_depth'] and base['complete_frontier']
        bundles.append((base_folder, base))
        families = []
        for family in (f for f in lod['local_families'] if f['tile'] == tile):
            parent = family['parent']
            key = hashlib.sha256(parent.encode('utf-8')).hexdigest()[:16]
            folder = cache / f'family_tile_{tile}_{key}'
            marker = bundle_marker(folder)
            assert marker['tile_id'] == tile and marker['replacement_parent'] == parent and marker['complete_sibling_family']
            assert marker['indices'] == family['triangles'] * 3
            families.append((parent, marker['source_nodes']))
            bundles.append((folder, marker))
        selected = reconstruct_cut(catalog, base['source_nodes'], families)
        assert len(selected) == ready['frontier']
        sources = {}
        for folder, marker in bundles:
            hashes.append({'path': evidence_path(folder / 'complete.json'), 'sha256': digest(folder / 'complete.json')})
            meshes = {}
            ownership = {}
            directories = [p['directory'] for p in marker['parts']]
            assert len(directories) == len(set(directories))
            for part in marker['parts']:
                directory = part['directory']
                assert (folder / directory).resolve().parent == folder.resolve()
                assert len(part['files']) == 3 and {f['name'] for f in part['files']} == {'geometry.gltf', 'geometry.bin', 'atlas.jpg'}
                for item in part['files']:
                    path = folder / directory / item['name']
                    assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256']
                    hashes.append({'path': evidence_path(path), 'sha256': item['sha256']})
                meshes[directory] = reference.mesh(folder / directory / 'geometry.gltf')
                ownership[directory] = []
            for node in marker['source_nodes']:
                assert node['name'] not in sources
                sources[node['name']] = node
                count = 0
                for span in node['spans']:
                    p, i = meshes[span['part']]
                    first, length = span['first'], span['count']
                    assert first >= 0 and length > 0 and first % 3 == length % 3 == 0 and first + length <= len(i)
                    ownership[span['part']].append((first, length))
                    count += length
                    if node['name'] in selected:
                        part = reference.reference_part(p, i[first:first+length], tile, node['depth'])
                        part['source_node'] = node['name']
                        fine.append(part)
                assert count == node['triangles'] * 3
            for directory, spans in ownership.items():
                cursor = 0
                for first, length in sorted(spans):
                    assert first == cursor, 'Source ownership gap or overlap'
                    cursor += length
                assert cursor == len(meshes[directory][1])
        assert sum(sources[n]['triangles'] for n in selected) == ready['triangles'] == ready['picking_triangles']
        cuts.append({'tile': tile, 'nodes': sorted(selected), 'triangles': ready['triangles']})
    assert sum(p['count'] for p in fine) * 3 == lod['drawn_child_indices']
    rows, max_error = [], 0.
    expected_fine = expected_changed = 0
    for sample in probe['samples']:
        origin, direction = np.array(sample['ray_origin']), np.array(sample['ray_direction'])
        assert np.isfinite(origin).all() and np.isfinite(direction).all()
        assert abs(np.linalg.norm(direction) - 1) < 1e-8
        bases = []
        for root in hierarchy['root_records']:
            if reference.possible(origin, direction, root['bounds_min'], root['bounds_max'], float('inf')):
                spans = np.concatenate([indices[first:first+count] for first, count in root['base_spans']])
                bases.append(reference.reference_part(positions, spans, root['tile_id'], 0))
        visible = [context, *fine, *(p for p in bases if p['tile'] not in resident)]
        expected = reference.closest(visible, origin, direction)
        actual = sample.get('hit')
        assert bool(expected) == bool(actual), sample['pixel']
        if expected:
            distance, part = expected
            expected_fine += int(part['depth'] > 0)
            error = abs(distance - actual['distance'])
            max_error = max(max_error, error)
            assert error < 1e-5
            assert actual['tile'] == part['tile'] and actual['depth'] == part['depth']
            if part.get('source_node'):
                assert actual['source'] == 'native-source' and actual['source_node'] == part['source_node']
            assert np.linalg.norm(origin + direction * distance - actual['point']) < 1e-5
        coarse = reference.closest([context, *bases], origin, direction)
        assert bool(coarse) == ('base_point' in sample)
        if coarse:
            expected_changed += int(bool(expected) and abs(coarse[0] - expected[0]) > .01)
            assert np.linalg.norm(origin + direction * coarse[0] - sample['base_point']) < 1e-5
        rows.append({'pixel': sample['pixel'], 'matched': True, 'hit': actual})
    assert len(rows) == 25 and expected_fine == probe['fine_hits'] > 0
    assert expected_changed == probe['different_from_base'] > 0
    visibility_rows = []
    if args.require_visibility:
        visibility = lod['visibility']
        assert visibility['enabled'] and visibility['samples'] > 0
        width, height = visibility['width'], visibility['height']
        assert width == 96 and 16 <= height <= 256
        rectangle = visibility.get('attention_rectangle')
        if rectangle is None:
            assert 'attention_weight' not in visibility and 'normalization_weight' not in visibility
            normalization = width*height  # Earlier uniform-weight GPU audit records remain readable.
        else:
            expected_rectangle = [width*3//10, height*3//10, width*7//10, height*7//10]
            assert rectangle == expected_rectangle and visibility['attention_weight'] == 4
            normalization = width*height+3*(rectangle[2]-rectangle[0])*(rectangle[3]-rectangle[1])
            assert visibility['normalization_weight'] == normalization
        keys = set()
        total_weight = 0.
        for source in visibility['sources']:
            key = (source['tile'], source['source_node'])
            assert key not in keys and np.isfinite(source['weight']) and source['weight'] > 0
            keys.add(key)
            bins = source['depth_bins']
            assert len({b for b, _ in bins}) == len(bins)
            assert all(isinstance(b, int) and 0 <= b <= 255 and np.isfinite(w) and w > 0 for b, w in bins)
            assert abs(sum(w for _, w in bins) - source['weight']) < 1e-10
            assert abs(source['weight']*normalization-round(source['weight']*normalization)) < 1e-8
            total_weight += source['weight']
        assert 0 < total_weight <= 1 + 1e-10
        view = visibility['view']
        camera = np.array(view['camera'])
        forward = np.array(view['target']) - camera
        forward /= np.linalg.norm(forward)
        for sample in visibility['probe_pixels']:
            x, y = sample['raster_pixel']
            if rectangle is not None:
                expected_weight = 4 if rectangle[0] <= x < rectangle[2] and rectangle[1] <= y < rectangle[3] else 1
                assert sample['pixel_weight'] == expected_weight
            origin, direction = np.array(sample['ray_origin']), np.array(sample['ray_direction'])
            assert np.isfinite(origin).all() and np.isfinite(direction).all()
            assert abs(np.linalg.norm(direction)-1) < 1e-8
            bases = []
            for root in hierarchy['root_records']:
                if root['tile_id'] not in resident and reference.possible(origin, direction, root['bounds_min'], root['bounds_max'], float('inf')):
                    spans = np.concatenate([indices[first:first+count] for first, count in root['base_spans']])
                    bases.append(reference.reference_part(positions, spans, root['tile_id'], 0))
            expected = reference.closest([context, *fine, *bases], origin, direction)
            tile, name = (expected[1]['tile'], expected[1].get('source_node', '')) if expected else (0, '')
            assert (sample['tile'], sample['source_node']) == (tile, name), ('GPU source mismatch', sample['raster_pixel'], tile, name, sample)
            expected_bin = None
            if expected:
                depth = max(.5, float((origin + direction*expected[0] - camera) @ forward))
                expected_bin = round(np.clip(np.log(depth/.5)/np.log(120000), 0, 1)*255)
                assert abs(expected_bin-sample['depth_bin']) <= 1, ('GPU depth mismatch', sample, expected_bin)
            visibility_rows.append({'rasterPixel': sample['raster_pixel'], 'tile': tile, 'sourceNode': name,
                                    'gpuDepthBin': sample['depth_bin'], 'referenceDepthBin': expected_bin, 'matched': True})
        assert len(visibility_rows) == 25
    result = {
        'passed': True,
        'scope': '25 screen rays at the recorded near view; direct float64 triangle '
                 'intersections, complete current source-family cut; no whole-area/performance claim',
        'statsSha256': digest(args.stats),
        'referenceInputs': reference_inputs,
        'geometryStore': str(cache),
        'preparedAssets': assets.identity() if assets is not None else None,
        'preparedSourceInputs': assets.source_inputs if assets is not None else [],
        'visibleCuts': cuts,
        'samples': rows,
        'maxDistanceErrorM': max_error,
        'fineHits': probe['fine_hits'],
        'differentFromBase': probe['different_from_base'],
        'verifiedFiles': hashes,
        'gpuVisibilitySamples': visibility_rows,
        'gpuVisibilityVerified': bool(visibility_rows),
    }
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({'passed': True, 'rays': len(rows), 'fineHits': probe['fine_hits'], 'maxDistanceErrorM': max_error}))


if __name__ == '__main__':
    main()
