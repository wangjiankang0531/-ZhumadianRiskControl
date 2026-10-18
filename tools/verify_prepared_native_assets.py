"""Independent read-only verification of sealed native geometry/JPEG asset packages.

Standard library only. Does not import producers, repair assets, launch programs,
or treat file integrity as rendered image/LOD acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re


class AssetVerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AssetVerificationError(message)


def linked(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def sha_file(path):
    before = path.stat()
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            'File changed during verification: ' + str(path))
    return value.hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path, limit=16*1048576):
    require(path.is_file() and not linked(path), 'Missing or linked control file: ' + str(path))
    require(0 < path.stat().st_size <= limit, 'Control file size exceeds bound')
    with path.open('r', encoding='utf-8') as stream:
        return json.load(stream, object_pairs_hook=no_duplicates)


def owned(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and path.parts and all(x not in ('.', '..') for x in path.parts),
            'Asset reference escapes its owner')
    target = root / path
    for item in [target, *target.parents]:
        require(not linked(item), 'Asset reference traverses a link: ' + str(item))
        if item == root:
            break
    require(target.resolve().is_relative_to(root.resolve()), 'Resolved asset escapes its owner')
    return target


class PreparedAssets:
    def __init__(self, package, store):
        self.package, self.store = Path(os.path.abspath(package)), Path(os.path.abspath(store))
        projects = [p for p in [self.package, *self.package.parents]
                    if (p/'Application').is_dir() and (p/'Assets/Runtime').is_dir()]
        require(bool(projects), 'Cannot identify the consuming project')
        self.project = projects[0]
        allowed = self.project/'Assets/Runtime/PreparedScenes'
        require(self.store.parent == allowed and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', self.store.name),
                'Prepared assets must belong to this project namespace')
        for item in (self.store, allowed, allowed.parent, allowed.parent.parent):
            require(item.is_dir() and not linked(item), 'Missing or linked asset namespace')
        self.descriptor = read_json(self.store/'.asset_package.json', 65536)
        descriptor = self.descriptor
        require(set(descriptor) == {'schema', 'state', 'storage_limit_bytes', 'plan_sha256', 'manifest_sha256'},
                'Unexpected asset descriptor fields')
        require(descriptor['schema'] == 'xnby.native.asset_package.v1' and descriptor['state'] == 'sealed',
                'Rendering requires a sealed asset package')
        require(type(descriptor['storage_limit_bytes']) is int and 0 < descriptor['storage_limit_bytes'] <= 8*1024**3,
                'Invalid finite asset storage budget')
        for key in ('plan_sha256', 'manifest_sha256'):
            require(isinstance(descriptor[key], str) and re.fullmatch('[0-9a-f]{64}', descriptor[key]),
                    'Invalid asset digest')
        binding = read_json(self.store/'preparation.plan.json')
        canonical = json.dumps(binding, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        require(hashlib.sha256(canonical).hexdigest() == descriptor['plan_sha256'], 'Preparation plan digest mismatch')
        require(set(binding) == {'plan', 'atlas_layout_policy'}, 'Unexpected preparation binding')
        self.plan, self.layout = binding['plan'], binding['atlas_layout_policy']
        self.source_inputs = self.verify_plan()
        self.manifest = read_json(self.store/'.asset_manifest.json')
        require(sha_file(self.store/'.asset_manifest.json') == descriptor['manifest_sha256'], 'Manifest digest mismatch')
        manifest = self.manifest
        require(manifest.get('schema') == 'xnby.native.asset_manifest.v1'
                and manifest.get('complete') is True and manifest.get('plan_sha256') == descriptor['plan_sha256'],
                'Manifest identity or completeness mismatch')
        require(manifest.get('codecs') == ['rgba8'], 'This independent verifier currently covers prepared RGBA8 geometry/JPEG only')
        jobs = {job['directory']: job for job in self.plan['jobs']}
        rows = manifest['bundles']
        self.bundles = {row['directory']: row for row in rows}
        require(len(self.bundles) == len(rows) == len(jobs) and set(self.bundles) == set(jobs),
                'Manifest has duplicate, missing or unplanned bundles')
        self.jobs = jobs
        self.verified_files = []

    def source_input(self, relative):
        # Existing frozen packages intentionally link their source catalogs/exporter.
        # These are read-only SHA-pinned inputs, never output payloads.
        path = Path(relative)
        require(not path.is_absolute() and path.parts and '..' not in path.parts,
                'Source reference escapes its package')
        target = self.package / path
        require(target.resolve().is_relative_to(self.project.resolve()) and target.is_file(),
                'Source input escapes this project or is missing')
        return target

    def verify_plan(self):
        plan = self.plan
        require(plan.get('schema') == 'xnby.native.preparation_plan.v1', 'Unsupported preparation plan')
        require(type(plan['base_depth']) is int and type(plan['max_depth']) is int
                and 0 <= plan['base_depth'] <= plan['max_depth'] <= 32, 'Invalid preparation depths')
        hierarchy_path = self.source_input('data/showcase/zhumadian_native_hierarchy.json')
        require(sha_file(hierarchy_path) == plan['hierarchy_sha256'], 'Source hierarchy digest mismatch')
        hierarchy = read_json(hierarchy_path)
        roots = {row['tile_id']: row for row in hierarchy['root_records']}
        catalogs = {row['tile']: row for row in plan['catalogs']}
        require(len(catalogs) == len(plan['catalogs']) and set(catalogs) == set(plan['tiles'])
                and len(set(plan['tiles'])) == len(plan['tiles']), 'Duplicate or missing source catalog')
        inputs = [dict(path=str(hierarchy_path), sha256=plan['hierarchy_sha256'])]
        expected_jobs = {}
        for tile, record in catalogs.items():
            require(type(tile) is int and 1 <= tile <= 2346 and tile in roots, 'Invalid source tile')
            require(record['path'] == roots[tile]['catalog'] and record['sha256'] == roots[tile]['sha256'],
                    'Source catalog identity differs from hierarchy')
            path = self.source_input(record['path'])
            require(sha_file(path) == record['sha256'], 'Source catalog digest mismatch')
            catalog = read_json(path)
            nodes = {row['name']: row for row in catalog['nodes']}
            require(len(nodes) == len(catalog['nodes']), 'Duplicate source node')
            depths = {}
            pending = [(catalog['root'], 0)]
            while pending:
                name, depth = pending.pop()
                require(name in nodes and name not in depths, 'Source tree has missing nodes, cycles or multiple parents')
                depths[name] = depth
                children = nodes[name]['children']
                require(len(children) == len(set(children)), 'Duplicate source child')
                pending.extend((child, depth+1) for child in children)
            base = min(plan['base_depth'], catalog['max_descendant_depth'])
            last = min(plan['max_depth'], catalog['max_descendant_depth'])
            for depth in range(1, base+1) if base else [0]:
                name = f'tile_{tile}_depth_{depth}'
                expected_jobs[name] = dict(tile=tile, depth=depth, directory=name)
            for name, depth in depths.items():
                if base <= depth < last and nodes[name]['children']:
                    key = hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]
                    directory = f'family_tile_{tile}_{key}'
                    require(directory not in expected_jobs, 'Source family key collision')
                    expected_jobs[directory] = dict(tile=tile, parent=name, depth=depth+1, directory=directory)
            inputs.append(dict(path=str(path), sha256=record['sha256']))
        jobs = {row['directory']: row for row in plan['jobs']}
        require(len(jobs) == len(plan['jobs']) and jobs == expected_jobs, 'Preparation plan omits or changes required source jobs')
        for name, digest in plan['producer_sha256'].items():
            require(Path(name).name == name and name.endswith('.py'), 'Invalid producer identity')
            path = self.source_input('tools/'+name)
            require(sha_file(path) == digest, 'Frozen producer digest mismatch: ' + name)
            inputs.append(dict(path=str(path), sha256=digest))
        exporter = self.source_input('work/osgb_exporter_build/Release/ht_osgb_exporter.exe')
        require(sha_file(exporter) == plan['exporter_sha256'], 'Frozen exporter digest mismatch')
        inputs.append(dict(path=str(exporter), sha256=plan['exporter_sha256']))
        return inputs

    def bundle(self, name):
        require(name in self.bundles, 'Requested bundle is not declared in the sealed manifest')
        row, job = self.bundles[name], self.jobs[name]
        folder = owned(self.store, name)
        path = owned(folder, 'complete.json')
        marker = read_json(path)
        require(sha_file(path) == row['marker_sha256'], 'Bundle marker digest mismatch')
        require(marker['tile_id'] == job['tile'], 'Bundle tile differs from planned source')
        if 'parent' in job:
            require(marker['replacement_parent'] == job['parent'] and marker['complete_sibling_family'] is True,
                    'Incomplete or wrong source family')
        else:
            require(marker['depth'] == job['depth'] and marker['complete_frontier'] is True,
                    'Incomplete or wrong source frontier')
        require(marker.get('atlas_layout_policy', 'legacy_pot_gutter4_v1') == self.layout, 'Atlas recipe differs from sealed plan')
        parts = marker['parts']
        require(type(row['parts']) is int and 0 < len(parts) == row['parts'] <= 64, 'Invalid physical page count')
        require([p['directory'] for p in parts] == [f'part_{n:03d}' for n in range(len(parts))],
                'Physical page identity is not unique and contiguous')
        require(marker['gpu_payload_bytes'] == row['gpu_payload_bytes'] == sum(p['gpu_payload_bytes'] for p in parts),
                'Physical page budget differs from manifest')
        files = [dict(path=str(path), sha256=row['marker_sha256'])]
        for part in parts:
            require(type(part['gpu_payload_bytes']) is int and 0 < part['gpu_payload_bytes'] <= 32*1048576,
                    'Physical page exceeds upload budget')
            directory = owned(folder, part['directory'])
            records = part['files']
            require(len(records) == 3 and {r['name'] for r in records} == {'geometry.gltf', 'geometry.bin', 'atlas.jpg'},
                    'Unexpected physical page payload files')
            for record in records:
                payload = owned(directory, record['name'])
                require(type(record['bytes']) is int and record['bytes'] > 0 and payload.stat().st_size == record['bytes']
                        and sha_file(payload) == record['sha256'], 'Payload size or digest mismatch: ' + str(payload))
                files.append(dict(path=str(payload), sha256=record['sha256'], bytes=record['bytes']))
            gltf = read_json(owned(directory, 'geometry.gltf'))
            require(len(gltf['buffers']) == 1 and gltf['buffers'][0]['uri'] == 'geometry.bin'
                    and gltf['buffers'][0]['byteLength'] == (directory/'geometry.bin').stat().st_size
                    and len(gltf['images']) == 1 and gltf['images'][0]['uri'] == 'atlas.jpg',
                    'glTF references escape the verified physical page')
        self.verified_files.extend(files)
        return marker

    def identity(self):
        return dict(directory=str(self.store), manifest_sha256=self.descriptor['manifest_sha256'],
                    plan_sha256=self.descriptor['plan_sha256'])

    def require_runtime_identity(self, lod):
        require(lod.get('cache_access') == 'read_only', 'External prepared asset statistics require read_only access')
        identity = lod.get('prepared_assets')
        require(isinstance(identity, dict) and Path(os.path.abspath(identity.get('directory', ''))) == self.store
                and identity.get('manifest_sha256') == self.descriptor['manifest_sha256']
                and identity.get('plan_sha256') == self.descriptor['plan_sha256'],
                'Render statistics do not identify this sealed asset generation')

    def audit(self):
        parts = payload_bytes = 0
        for name in self.bundles:
            marker = self.bundle(name)
            parts += len(marker['parts'])
            payload_bytes += sum(f['bytes'] for p in marker['parts'] for f in p['files'])
        return dict(passed=True, scope='Sealed plan/source identity and geometry/JPEG file integrity only; no rendered LOD, pixels or performance acceptance',
                    preparedAssets=self.identity(), bundles=len(self.bundles), physicalParts=parts,
                    payloadBytes=payload_bytes, verifiedFiles=self.verified_files, sourceInputs=self.source_inputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assets = PreparedAssets(args.package, args.store)
    require(not args.output.absolute().resolve().is_relative_to((assets.project/'Assets').resolve()),
            'Verification reports cannot be written into project assets')
    result = assets.audit()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ('passed', 'scope', 'bundles', 'physicalParts', 'payloadBytes')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
