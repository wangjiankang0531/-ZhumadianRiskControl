"""Prepare isolated tight-atlas candidates without changing production recipes/cache."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'work/geospatial_deps'))
import convert_zhumadian_native_chunks as chunks
import convert_zhumadian_native_family as families
import native_tight_atlas as tight

_LOCK = threading.RLock()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_cache(candidate):
    candidate = Path(candidate).resolve()
    if not candidate.is_relative_to((ROOT / 'work').resolve()) or not candidate.name.startswith('tight_atlas_candidate_'):
        raise ValueError('Candidate must be a named isolated directory below Application/work')
    candidate.mkdir(parents=True, exist_ok=True)
    cache = candidate / 'work/zhumadian_native_chunk_cache'
    cache.mkdir(parents=True, exist_ok=True)
    if chunks.cache_policy.linked(cache) or cache.resolve() != candidate / 'work/zhumadian_native_chunk_cache':
        raise ValueError('Candidate cache cannot follow a link')
    return cache


def present(candidate, tile, depth, marker, parent=None):
    cache = candidate_cache(candidate)
    name = f'family_tile_{tile}_{families.family_key(parent)}' if parent else f'tile_{tile}_depth_{depth}'
    folder = cache / name
    try:
        if marker['tile_id'] != tile or marker.get('atlas_layout_policy') != tight.POLICY or marker['stamp'].get('tight_layout_sha256') != sha(Path(tight.__file__)):
            return False
        if parent and marker['replacement_parent'] != parent or not parent and marker['depth'] != depth:
            return False
        marker_path = folder / 'complete.json'
        if chunks.cache_policy.linked(folder) or chunks.cache_policy.linked(marker_path) or not 0 < len(marker['parts']) <= 64 or not marker_path.is_file():
            return False
        directories = [part['directory'] for part in marker['parts']]
        if len(set(directories)) != len(directories):
            return False
        for part in marker['parts']:
            if not re.fullmatch(r'part_\d{3}', part['directory']) or part.get('atlas_layout_policy') != tight.POLICY:
                return False
            if chunks.cache_policy.linked(folder / part['directory']) or {item['name'] for item in part['files']} != {'geometry.gltf', 'geometry.bin', 'atlas.jpg'} or len(part['files']) != 3:
                return False
            for item in part['files']:
                if item['name'] not in {'geometry.gltf', 'geometry.bin', 'atlas.jpg'}:
                    return False
                path = folder / part['directory'] / item['name']
                if chunks.cache_policy.linked(path) or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
                    return False
        return True
    except (OSError, KeyError, ValueError, TypeError):
        return False


def verified_source_stamp(tile, depth, parent=None):
    native = chunks.native
    master = json.loads((ROOT / 'data/showcase/zhumadian_native_hierarchy.json').read_text(encoding='utf-8'))
    record = next(r for r in master['root_records'] if r['tile_id'] == tile)
    catalog_path = ROOT / record['catalog']
    if sha(catalog_path) != record['sha256']:
        raise ValueError('Source hierarchy changed')
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    if parent:
        forest = families.frontier.SourceForest(catalog)
        if parent not in forest.depths or not forest.nodes[parent]['children']:
            raise ValueError('Invalid source family')
        sources = [forest.nodes[name] for name in forest.nodes[parent]['children']]
    else:
        sources = native.frontier(catalog, depth)
    directory = (ROOT / catalog['source_directory']).resolve()
    if not directory.is_relative_to((ROOT / 'assets/驻马店园区').resolve()):
        raise ValueError('Source directory escapes GIS assets')
    for source in sources:
        path = directory / source['name']
        if path.parent != directory or path.stat().st_size != source['bytes'] or sha(path) != source['sha256']:
            raise ValueError('Original source changed')
    stamp = {'catalog_sha256': record['sha256'],
             'converter_sha256': sha(Path(chunks.__file__)),
             'texture_helper_sha256': sha(Path(chunks.textures.__file__)),
             'frontier_helper_sha256': sha(Path(chunks.source_frontier.__file__)),
             'native_helper_sha256': sha(Path(native.__file__)),
             'packer_sha256': sha(Path(native.full.__file__)),
             'exporter_sha256': sha(ROOT / 'work/osgb_exporter_build/Release/ht_osgb_exporter.exe'),
             'tight_layout_sha256': sha(Path(tight.__file__)),
             'atlas_recipe_sha256': sha(Path(chunks.recipes.__file__)),
             'atlas_layout_policy': tight.POLICY}
    if parent:
        stamp.update(parent=parent, children=sources, family_converter_sha256=sha(Path(families.__file__)))
    else:
        stamp.update(depth=depth, frontier=sources)
    return stamp


def cached_candidate(candidate, tile, depth=3, parent=None):
    cache = candidate_cache(candidate)
    name = f'family_tile_{tile}_{families.family_key(parent)}' if parent else f'tile_{tile}_depth_{depth}'
    folder = cache / name
    try:
        with chunks.cache_policy.bundle_lock(cache, name):
            marker_path = folder / 'complete.json'
            if chunks.cache_policy.linked(folder) or chunks.cache_policy.linked(marker_path):
                return None
            marker = json.loads(marker_path.read_text(encoding='utf-8'))
            valid_frontier = (marker.get('schema') == 'xnby.osgb_native_family.v1' and marker.get('complete_sibling_family') is True) if parent else (marker.get('schema') == 'hongtu.osgb_native_chunk_bundle.v1' and marker.get('complete_frontier') is True)
            if valid_frontier and marker.get('stamp') == verified_source_stamp(tile, depth, parent) and present(candidate, tile, depth, marker, parent):
                return marker
    except (OSError, KeyError, ValueError, TypeError, StopIteration):
        pass
    return None


def prepare(candidate, tile, depth=3, parent=None):
    if type(tile) is not int or not 1 <= tile <= 2346 or type(depth) is not int or not 1 <= depth <= 12:
        raise ValueError('Invalid candidate tile or depth')
    if parent and not re.fullmatch(rf'Tile_{tile}_L\d+_0[0-9u]+\.osgb', parent):
        raise ValueError('Invalid complete sibling parent')
    cache = candidate_cache(candidate)
    with _LOCK:
        ready = cached_candidate(candidate, tile, depth, parent)
        if ready is not None:
            print(json.dumps({'tight_cached': True, 'tile': tile, 'depth': depth, 'parent': parent}), flush=True)
            return ready
        marker = (families.convert(tile, parent, atlas_layout=tight.POLICY, cache_root=cache)
                  if parent else chunks.convert(tile, depth, atlas_layout=tight.POLICY, cache_root=cache))
        checked = cached_candidate(candidate, tile, depth, parent)
        if checked is None or checked != marker:
            raise RuntimeError('Published tight recipe marker or payload failed verification')
        return checked



def compare_to_baseline(candidate, baseline):
    from PIL import Image
    import array
    candidate, baseline = Path(candidate), Path(baseline)
    new = json.loads((candidate / 'complete.json').read_text(encoding='utf-8'))
    old = json.loads((baseline / 'complete.json').read_text(encoding='utf-8'))
    assert new['indices'] == old['indices'] and new['source_nodes'] != []
    assert len(new['parts']) == len(old['parts']), 'This fixture changed geometry partitions; needs a triangle-level audit'
    maximum_uv_pixel_error = 0
    for left, right in zip(old['parts'], new['parts']):
        assert left['source_face_counts'] == right['source_face_counts'] and left['source_spans'] == right['source_spans']
        assert left['indices'] == right['indices'] and left['vertices'] == right['vertices']
        ld, rd = baseline / left['directory'], candidate / right['directory']
        lg = json.loads((ld / 'geometry.gltf').read_text(encoding='utf-8'))
        rg = json.loads((rd / 'geometry.gltf').read_text(encoding='utf-8'))
        lb, rb = (ld / 'geometry.bin').read_bytes(), (rd / 'geometry.bin').read_bytes()
        for index in (0, 1, 3):
            a, b = lg['bufferViews'][index], rg['bufferViews'][index]
            assert lb[a['byteOffset']:a['byteOffset'] + a['byteLength']] == rb[b['byteOffset']:b['byteOffset'] + b['byteLength']]
        auv, buv = array.array('f'), array.array('f')
        for values, views, raw in [(auv, lg['bufferViews'], lb), (buv, rg['bufferViews'], rb)]:
            view = views[2]; values.frombytes(raw[view['byteOffset']:view['byteOffset'] + view['byteLength']])
        error = max(abs(a * left['atlas_size'] - b * right['atlas_size']) for a, b in zip(auv, buv))
        maximum_uv_pixel_error = max(maximum_uv_pixel_error, error)
        assert error < .00025
        with Image.open(ld / 'atlas.jpg') as a, Image.open(rd / 'atlas.jpg') as b:
            assert b.size == (right['atlas_size'], right['atlas_size'])
            assert a.crop((0, 0, b.width, b.height)).tobytes() == b.tobytes(), 'Decoded JPEG source canvas changed'
    return {'baselinePayloadBytes': old['gpu_payload_bytes'], 'tightPayloadBytes': new['gpu_payload_bytes'],
            'savedPayloadBytes': old['gpu_payload_bytes'] - new['gpu_payload_bytes'], 'parts': len(new['parts']),
            'sameTrianglesNormalsAndIndices': True, 'decodedCroppedJpegPixelsIdentical': True,
            'maximumUvPixelError': maximum_uv_pixel_error, 'sourceTextureScale': 1.0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--tile', type=int, required=True)
    parser.add_argument('--depth', type=int, default=3)
    parser.add_argument('--parent')
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    marker = prepare(args.candidate_root, args.tile, args.depth, args.parent)
    name = f'family_tile_{args.tile}_{families.family_key(args.parent)}' if args.parent else f'tile_{args.tile}_depth_{args.depth}'
    result = compare_to_baseline(candidate_cache(args.candidate_root) / name, args.baseline) if args.baseline else {'payloadBytes': marker['gpu_payload_bytes'], 'parts': len(marker['parts'])}
    print(json.dumps(result), flush=True)
