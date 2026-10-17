"""Explicit native atlas recipes and format-bound disposable cache namespaces."""
from pathlib import Path
import hashlib
import json
import re
import threading
if __package__:
    from . import native_texture_parts as textures, native_tight_atlas as tight, native_cache_policy as cache_policy, native_edge_clamp_atlas as edge, native_rectangular_atlas as rectangular
else:
    import native_texture_parts as textures
    import native_tight_atlas as tight
    import native_cache_policy as cache_policy
    import native_edge_clamp_atlas as edge
    import native_rectangular_atlas as rectangular

LEGACY = 'legacy_pot_gutter4_v1'
TIGHT = tight.POLICY
EDGE_CLAMP = edge.POLICY
RECTANGULAR = rectangular.POLICY
LAYOUTS = (LEGACY, TIGHT, EDGE_CLAMP, RECTANGULAR)
BUILD_LOCK = threading.RLock()


def policy(value=None):
    value = LEGACY if value is None else value
    if value not in LAYOUTS:
        raise ValueError('Unsupported native atlas recipe')
    return value


def layouts(sizes, atlas_layout=None):
    selected = policy(atlas_layout)
    if selected == RECTANGULAR:
        return rectangular.layouts(sizes)
    if selected == EDGE_CLAMP:
        return edge.layouts(sizes)
    original = textures.atlas_layouts(sizes)
    return tight.tight_layouts(original) if selected == TIGHT else original


def extent(size):
    values = (size, size) if type(size) is int else size
    if not isinstance(values, (tuple, list)) or len(values) != 2 or any(type(n) is not int or n <= 0 or n > 2048 for n in values):
        raise ValueError('Invalid native atlas extent')
    return tuple(values)


def mip_bytes(size):
    width, height = extent(size)
    result = 0
    while True:
        result += width * height * 4
        if width == height == 1:
            return result
        width, height = max(1, width // 2), max(1, height // 2)


def stamp(atlas_layout=None):
    selected = policy(atlas_layout)
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    result = {'atlas_recipe_sha256': sha(__file__)}
    if selected in (TIGHT, EDGE_CLAMP, RECTANGULAR):
        result.update(atlas_layout_policy=selected, tight_layout_sha256=sha(tight.__file__))
    if selected in (EDGE_CLAMP, RECTANGULAR):
        result["edge_layout_sha256"] = sha(edge.__file__)
    if selected == RECTANGULAR:
        result["rectangular_layout_sha256"] = sha(rectangular.__file__)
    return result


def save_atlas(mapping, output, size, atlas_layout=None):
    if policy(atlas_layout) == RECTANGULAR:
        return rectangular.save(mapping, output, extent(size))
    if policy(atlas_layout) == EDGE_CLAMP:
        return edge.save(mapping, output, size)
    return textures.save_atlas(mapping, output, size)


def apply_sampler(gltf, atlas_layout=None):
    if policy(atlas_layout) in (EDGE_CLAMP, RECTANGULAR):
        gltf["samplers"] = [dict(edge.SAMPLER)]
        gltf["textures"][0]["sampler"] = 0


def cache_directory(root, legacy, atlas_layout=None, override=None):
    root, legacy = Path(root), Path(legacy)
    selected = policy(atlas_layout)
    if selected == LEGACY and (override is None or Path(override) == legacy):
        return legacy
    folder = Path(override) if override is not None else root / 'work/native_recipe_cache' / selected
    if not folder.is_absolute():
        folder = root / folder
    work = (root / 'work').resolve()
    if not folder.resolve().is_relative_to(work) or folder.resolve() == work:
        raise ValueError('Explicit recipe cache must stay below this project work directory')
    for item in [folder, *folder.parents]:
        if item == root / 'work':
            break
        if cache_policy.linked(item):
            raise ValueError('Explicit recipe cache cannot traverse links')
    return folder


def bind_cache(cache, atlas_layout=None):
    """Never rewrite another format in place; refuse a conflicting binding."""
    selected = policy(atlas_layout)
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    descriptor = {'schema': 'xnby.native.cache_recipe.v1', 'atlas_layout_policy': selected}
    path = cache / '.atlas_recipe.json'
    with cache_policy.FileLock(cache / '.locks/atlas_recipe.lock', exclusive=True):
        if cache_policy.linked(path):
            raise ValueError('Cache recipe marker cannot be a link')
        if path.exists():
            if json.loads(path.read_text('utf-8')) != descriptor:
                raise ValueError('Cache belongs to a different native atlas recipe; select its own namespace')
            return
        for folder in cache.iterdir():
            if not cache_policy.BUNDLE.fullmatch(folder.name):
                continue
            marker = folder / 'complete.json'
            if cache_policy.linked(folder) or cache_policy.linked(marker):
                raise ValueError('Existing cache bundle cannot be a link')
            if marker.exists():
                previous = json.loads(marker.read_text('utf-8'))
                if previous.get('atlas_layout_policy', LEGACY) != selected:
                    raise ValueError('Existing native bundles use another atlas recipe')
        pending = cache / '.atlas_recipe.pending.json'
        if cache_policy.linked(pending):
            raise ValueError('Pending cache recipe cannot be a link')
        pending.write_text(json.dumps(descriptor, indent=2), encoding='utf-8')
        pending.replace(path)

def payload_present(folder, marker):
    """Validate every physical page before reusing a published bundle."""
    folder = Path(folder)
    try:
        if cache_policy.linked(folder) or cache_policy.linked(folder / 'complete.json'):
            return False
        parts = marker['parts']
        if not 0 < len(parts) <= 64:
            return False
        directories = [p['directory'] for p in parts]
        if len(set(directories)) != len(directories):
            return False
        for part in parts:
            directory = part['directory']
            if not re.fullmatch(r'part_\d{3}', directory) or cache_policy.linked(folder / directory):
                return False
            if len(part['files']) != 3 or {f['name'] for f in part['files']} != {'geometry.gltf','geometry.bin','atlas.jpg'}:
                return False
            for item in part['files']:
                path = folder / directory / item['name']
                if cache_policy.linked(path) or path.stat().st_size != item['bytes']:
                    return False
                if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                    return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def writable_bundle(folder):
    folder = Path(folder)
    if cache_policy.linked(folder):
        raise ValueError('Derived bundle directory cannot be a link')
    folder.mkdir(parents=True, exist_ok=True)
    for name in ('complete.json', 'complete.pending.json', 'failure.json', 'rejected.json'):
        if cache_policy.linked(folder / name):
            raise ValueError('Derived bundle metadata cannot be a link')


def resolve_cache(root, legacy, atlas_layout=None, cache_root=None):
    """A version's explicit release declaration selects its own physical cache."""
    root = Path(root)
    config = root / 'data/showcase/zhumadian_native_recipe.json'
    if atlas_layout is None and (config.exists() or cache_policy.linked(config)):
        if cache_policy.linked(config):
            raise ValueError('Release recipe declaration cannot be a link')
        declaration = json.loads(config.read_text('utf-8'))
        if (not isinstance(declaration, dict)
                or set(declaration) != {'schema', 'atlas_layout_policy', 'cache_relative_path'}
                or declaration['schema'] != 'xnby.native.atlas.release.v1'
                or declaration['cache_relative_path'] != 'work/zhumadian_native_chunk_cache'):
            raise ValueError('Invalid version-owned native recipe declaration')
        atlas_layout = policy(declaration['atlas_layout_policy'])
        if cache_root is None:
            cache_root = root / declaration['cache_relative_path']
    selected = policy(atlas_layout)
    return selected, cache_directory(root, legacy, selected, cache_root)
