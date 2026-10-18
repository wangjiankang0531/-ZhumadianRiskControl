"""Consume existing complete landscape bundles without producers or cache writes."""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import re
import threading

PRODUCERS = {
    'converter_sha256':'convert_zhumadian_native_chunks.py',
    'family_converter_sha256':'convert_zhumadian_native_family.py',
    'texture_helper_sha256':'native_texture_parts.py',
    'frontier_helper_sha256':'native_source_frontier.py',
    'atlas_recipe_sha256':'native_atlas_recipe.py',
    'native_helper_sha256':'convert_zhumadian_native_root.py',
    'packer_sha256':'build_zhumadian_full_stage.py',
    'tight_layout_sha256':'native_tight_atlas.py',
    'edge_layout_sha256':'native_edge_clamp_atlas.py',
    'rectangular_layout_sha256':'native_rectangular_atlas.py',
    'packed_layout_sha256':'native_packed_rect_atlas.py',
}
SHA = re.compile('[0-9a-f]{64}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def duplicates(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result, 'Duplicate bundle JSON field')
        result[key] = value
    return result


def owned(root, relative):
    path = root/relative
    require(path.resolve().is_relative_to(root.resolve()), 'Read-only source escapes owner')
    for item in [path,*path.parents]:
        require(not item.is_symlink() and not (hasattr(item,'is_junction') and item.is_junction()), 'Read-only source traverses link')
        if item == root:
            break
    return path


def read_bytes(path, maximum):
    before = path.stat()
    require(0 < before.st_size <= maximum, 'Read-only resource exceeds limit')
    with path.open('rb') as stream:
        raw = stream.read(maximum+1)
    after = path.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns) and len(raw)==before.st_size, 'Resource changed while reading')
    return raw


class ReadOnlyLandscapeStore:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.cache = owned(self.root,Path('work/zhumadian_native_chunk_cache'))
        require(self.cache.is_dir(), 'Prepared cache does not exist')
        self.producers = {}
        for key,name in PRODUCERS.items():
            path = owned(self.root,Path('tools')/name)
            if path.is_file():
                self.producers[key] = hashlib.sha256(read_bytes(path,4*1048576)).hexdigest()
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def describe(self, tile, *, depth=None, parent=None):
        return self.describe_with_identity(tile,depth=depth,parent=parent)[0]

    def describe_with_identity(self, tile, *, depth=None, parent=None):
        return self._inspect_bundle(tile,depth=depth,parent=parent,verify_payloads=True)

    def plan(self, tile, *, depth=None, parent=None):
        marker,digest = self._inspect_bundle(tile,depth=depth,parent=parent,verify_payloads=False)
        require('cache_lease' not in marker,'Plan must not carry a resource lease')
        return dict(schema='xnby.source_bundle_plan.v1',verification='metadata_only',availabilityVerified=False,markerSHA256=digest,marker=marker)

    def _inspect_bundle(self, tile, *, depth=None, parent=None, verify_payloads):
        require(type(tile) is int and 1<=tile<=2346 and (depth is None)!=(parent is None), 'Invalid source request')
        if parent is None:
            require(type(depth) is int and 1<=depth<=12, 'Invalid frontier depth')
            name = f'tile_{tile}_depth_{depth}'
        else:
            require(isinstance(parent,str) and re.fullmatch(r'Tile_'+str(tile)+r'_L\d+_0[0-9u]+\.osgb',parent), 'Invalid source parent')
            name = f'family_tile_{tile}_'+hashlib.sha256(parent.encode()).hexdigest()[:16]
        folder = owned(self.cache,Path(name))
        raw = read_bytes(owned(folder,Path('complete.json')),16*1048576)
        marker = json.loads(raw,object_pairs_hook=duplicates)
        require(marker.get('tile_id')==tile and marker.get('texture_policy')=='original_pixels_v1', 'Source identity differs')
        if parent is None:
            require(marker.get('schema')=='hongtu.osgb_native_chunk_bundle.v1' and marker.get('complete_frontier') is True and marker.get('depth')==depth,'Incomplete frontier')
        else:
            require(marker.get('schema')=='xnby.osgb_native_family.v1' and marker.get('complete_sibling_family') is True and marker.get('replacement_parent')==parent and marker.get('family_key')==name.rsplit('_',1)[1],'Incomplete source family')
        stamp = marker.get('stamp',{})
        required = {'converter_sha256','texture_helper_sha256','frontier_helper_sha256','atlas_recipe_sha256'}
        if parent is not None:
            required.add('family_converter_sha256')
        require(required<=set(stamp),'Missing frozen producer identity')
        for key in set(stamp)&set(PRODUCERS):
            require(SHA.fullmatch(str(stamp[key])) and self.producers.get(key)==stamp[key], 'Frozen producer identity differs: '+key)
        parts = marker.get('parts')
        require(isinstance(parts,list) and 0<len(parts)<=64 and [p.get('directory') for p in parts]==[f'part_{i:03d}' for i in range(len(parts))], 'Invalid complete physical pages')
        payload = 0
        files = {}
        for part in parts:
            cost = part.get('gpu_payload_bytes')
            require(type(cost) is int and 0<cost<=32*1048576,'Physical page exceeds upload limit')
            payload += cost
            records = part.get('files')
            require(isinstance(records,list) and len(records)==3 and {r.get('name') for r in records}=={'geometry.gltf','geometry.bin','atlas.jpg'},'Invalid physical page files')
            for row in records:
                require(type(row.get('bytes')) is int and 0<row['bytes']<=32*1048576 and SHA.fullmatch(str(row.get('sha256'))),'Invalid physical file identity')
                relative = Path(part['directory'])/row['name']
                if verify_payloads:
                    content = read_bytes(owned(folder,relative),32*1048576)
                    require(len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'],'Physical file digest differs')
                files[relative.as_posix()] = dict(bytes=row['bytes'],sha256=row['sha256'])
        require(marker.get('gpu_payload_bytes')==payload and payload<=(384 if parent is None else 256)*1048576,'Complete bundle exceeds original budget')
        digest = hashlib.sha256(raw).hexdigest()
        if verify_payloads:
            with self.lock:
                self.entries[name] = dict(markerSHA256=digest,files=files)
                self.entries.move_to_end(name)
                while len(self.entries)>256:
                    self.entries.popitem(last=False)
        return marker,digest

    def payload(self, name, part, filename):
        require(re.fullmatch(r'(?:tile_\d+_depth_\d+|family_tile_\d+_[0-9a-f]{16})',name) and re.fullmatch(r'part_\d{3}',part) and filename in ('geometry.gltf','geometry.bin','atlas.jpg'),'Invalid physical file route')
        with self.lock:
            entry = self.entries.get(name)
        require(entry is not None,'Read-only bundle has not been admitted')
        folder = owned(self.cache,Path(name))
        require(hashlib.sha256(read_bytes(owned(folder,Path('complete.json')),16*1048576)).hexdigest()==entry['markerSHA256'],'Admitted marker changed')
        key = part+'/'+filename
        require(key in entry['files'],'Unlisted source file')
        record = entry['files'][key]
        content = read_bytes(owned(folder,Path(part)/filename),32*1048576)
        require(len(content)==record['bytes'] and hashlib.sha256(content).hexdigest()==record['sha256'],'Admitted source payload changed')
        return content
