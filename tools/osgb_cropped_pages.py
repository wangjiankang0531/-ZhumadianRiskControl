"""Versioned, read-only original-pixel crops; original triangles and UVs survive.

A crop changes material coordinates, never mesh coordinates. Interior LINEAR/
NEAREST source footprints only; periodic seams and mipmapped crops are refused.
All image production is stdout -> RAM -> lossless PNG, with no asset-file writes.
"""
from __future__ import annotations
import array
import copy
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from osgb_memory_reader import _parse_frame, parse_frame, MAX_HEADER, MAX_PAYLOAD, MAX_SOURCE
from readonly_source_memory_store import PinnedMemoryReader, ordinary
from osgb_memory_pages import (MIB, canonical, sha, floats, mip_bytes, mesh_metrics,
                               page as original_page, build_bundle as original_bundle)

FORMAT = "osgb_memory_png_crop_v2"


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate crop descriptor key")
        result[key] = value
    return result


def parse_geometry_frame(raw, node, source_bytes):
    return _parse_frame(raw, node, source_bytes, geometry_only=True)


def parse_crop_frame(raw, node, source_bytes, image_id, image, crop):
    if len(raw) < 24 or raw[:8] != b"ZMDROI01":
        raise ValueError("invalid original-pixel crop frame magic")
    header_size, size = struct.unpack_from("<QQ", raw, 8)
    if not 0 < header_size <= MAX_HEADER or not 0 < size <= 32*MIB or len(raw) != 24+header_size+size:
        raise ValueError("invalid original-pixel crop frame size")
    desc = json.loads(raw[24:24+header_size], object_pairs_hook=unique_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite crop metadata")))
    expected = dict(schema="zhumadian.osgb.rgba_crop.v1", node=node, sourceBytes=source_bytes,
                    sourceImage=image_id, sourceWidth=image["width"], sourceHeight=image["height"],
                    sourceOrigin=image["sourceOrigin"], rowOrder="source_storage", format="rgba8",
                    crop=list(crop), payloadBytes=crop[2]*crop[3]*4, externalReadAttempts=0, writeAttempts=0)
    # Canonical JSON comparison also distinguishes bool from integer and extra fields.
    if canonical(desc) != canonical(expected) or size != expected["payloadBytes"]:
        raise ValueError("crop response differs from the pinned source request")
    pixels = memoryview(raw)[24+header_size:]
    if any(alpha != 255 for alpha in pixels[3::4]):
        raise ValueError("nonopaque crop needs a separate material adapter")
    return pixels


def plan_mesh(mesh, image, payload):
    uv, indices = floats(payload, mesh["uv"], "f"), floats(payload, mesh["indices"], "I")
    width, height = image["width"], image["height"]
    sampler = mesh["sampler"]
    pages = []
    all_ids = list(range(len(indices)//3))
    no_mips = sampler["minFilter"] in (9728, 9729)

    def footprint(ids):
        refs = sorted({indices[t*3+k] for t in ids for k in range(3)})
        x = [uv[i*2]*width-.5 for i in refs]
        y = [uv[i*2+1]*height-.5 for i in refs]
        low,high=[min(x),min(y)],[max(x),max(y)]
        # Use the same legacy CLAMP -> CLAMP_TO_EDGE contract as MemoryGltf.
        # Only planning footprints are clamped; original float32 UVs stay unchanged.
        for axis,(key,dim) in enumerate(zip(('wrapS','wrapT'),(width,height))):
            if sampler[key] in (10496,33071):
                low[axis]=max(-.5,min(dim-.5,low[axis]))
                high[axis]=max(-.5,min(dim-.5,high[axis]))
        return refs,low,high

    def split(ids):
        refs, low, high = footprint(ids)
        full_cost = len(refs)*64 + len(ids)*12 + mip_bytes(width, height)
        # A large mesh can split while retaining its complete bounded image.
        # Mipmapped crop refusal applies only when the image itself is too large.
        if mip_bytes(width,height) <= 32*MIB and width*height*4 <= 32*MIB:
            crop = (0, 0, width, height)
        else:
            if not no_mips:
                raise ValueError("mipmapped original image requires per-mip crop gutters")
            if any((a<1 or b>dim-2) and sampler[key] not in (10496,33071)
                   for a,b,dim,key in zip(low,high,(width,height),('wrapS','wrapT'))):
                raise ValueError("source UV footprint crosses a periodic or image seam")
            x, y = max(0, math.floor(low[0])-1), max(0, math.floor(low[1])-1)
            right, top = min(width, math.ceil(high[0])+2), min(height, math.ceil(high[1])+2)
            crop = (x, y, right-x, top-y)
        cost = len(refs)*64 + len(ids)*12 + mip_bytes(crop[2],crop[3])
        if cost <= 32*MIB and crop[2]*crop[3]*4 <= 32*MIB:
            pages.append((ids, refs, crop))
            if len(pages)>64:
                raise ValueError("source mesh exceeds unchanged physical-page count")
            return
        if len(ids)<2:
            raise ValueError("one original triangle cannot fit the unchanged page limit")
        centers = {t: tuple(sum(uv[indices[t*3+k]*2+a] for k in range(3))*dim/3
                           for a,dim in enumerate((width,height))) for t in ids}
        spreads = [max(centers[t][a] for t in ids)-min(centers[t][a] for t in ids) for a in range(2)]
        axis = 1 if spreads[1]>spreads[0] else 0
        ordered = sorted(ids, key=lambda t: centers[t][axis])
        half = len(ordered)//2
        split(ordered[:half]); split(ordered[half:])
    split(all_ids)
    if sorted(t for ids,_,_ in pages for t in ids) != all_ids:
        raise ValueError("crop page plan lost or duplicated original triangles")
    return pages


def segment(blob, data, count):
    while len(blob)%4:
        blob.append(0)
    result = dict(offset=len(blob), bytes=len(data), count=count)
    blob.extend(data)
    if len(blob)>MAX_PAYLOAD:
        raise ValueError("complete source node exceeds unchanged RAM payload limit")
    return result


class SourceImageNeedsCrop(RuntimeError):
    """The pinned reader explicitly refused only the full-image size, not IO/security."""


class PinnedCropReader(PinnedMemoryReader):
    def _invoke(self, node, record, mode=None):
        self.verify_runtime()
        if not re.fullmatch(r"(Tile_[0-9]+)/\1_L[0-9]+_0[0-9u]+\.osgb", node):
            raise ValueError("invalid original source node")
        source = ordinary(self.source_root/node, self.source_root)
        stat = source.stat()
        before = (stat.st_size, stat.st_mtime_ns, sha(source.read_bytes()))
        if not 0<before[0]<=MAX_SOURCE or before[0]!=record["bytes"] or before[2]!=record["sha256"]:
            raise ValueError("original source differs from the pinned catalog")
        env = {k:os.environ[k] for k in ("SystemRoot","WINDIR","SystemDrive") if k in os.environ}
        env["PATH"] = str(self.runtime)+os.pathsep+str(Path(os.environ.get("SystemRoot","C:/Windows"))/"System32")
        result = subprocess.run([str(self.executable), str(self.source_root), node,
                                 str(self.runtime/"osgPlugins-3.6.5"), *([] if mode is None else [mode])],
                                executable=str(self.executable), cwd=self.runtime, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45,
                                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0), check=False)
        stat = source.stat()
        if before != (stat.st_size,stat.st_mtime_ns,sha(source.read_bytes())):
            raise RuntimeError("original source changed while reading")
        if result.returncode==1 and mode is None and not result.stdout and result.stderr.strip()==b"embedded image exceeds byte budget":
            raise SourceImageNeedsCrop("original source image requires bounded crop delivery")
        if result.returncode:
            raise RuntimeError(f"read-only crop reader returned {result.returncode}: "+result.stderr.decode('utf-8',errors='replace')[:2000])
        return result.stdout

    def __call__(self, tile, name, record):
        if type(tile) is not int or not 1<=tile<=2346 or not isinstance(name,str) or not name.startswith(f"Tile_{tile}_L"):
            raise ValueError("crop reader source belongs to another root")
        node = f"Tile_{tile}/{name}"
        full_pixels = False
        try:
            desc,payload = parse_frame(self._invoke(node,record),node,record["bytes"])
            full_pixels = True
        except SourceImageNeedsCrop:
            desc,payload = parse_geometry_frame(self._invoke(node,record,"--geometry-only"),node,record["bytes"])
        # Ordinary already-bounded sources need one helper invocation and no
        # compact/rebuild roundtrip. Every vertex must be referenced so this
        # returns exactly the same physical geometry as the compact crop path.
        if full_pixels and all(m["positions"]["count"]//3*64+m["indices"]["bytes"]+
                               mip_bytes(desc["images"][m["image"]]["width"],desc["images"][m["image"]]["height"])<=32*MIB and
                               len(set(floats(payload,m["indices"],"I")))==m["positions"]["count"]//3
                               for m in desc["meshes"]):
            images=[{**image,"originalWidth":image["width"],"originalHeight":image["height"],
                     "sourceRect":[0,0,image["width"],image["height"]]} for image in desc["images"]]
            return {**desc,"schema":"zhumadian.osgb.crop_memory.v1","images":images},payload
        planned=[(mesh,plan_mesh(mesh,desc['images'][mesh['image']],payload)) for mesh in desc['meshes']]
        # Geometry-only plans determine the exact compact RAM size before any
        # oversized source-image crop is requested or accumulated.
        if sum(len(pages) for _,pages in planned)>64:
            raise ValueError('source exceeds unchanged physical-page count')
        estimated=sum(len(refs)*20+len(triangles)*12+crop[2]*crop[3]*4
                      for _,pages in planned for triangles,refs,crop in pages)
        if estimated>MAX_PAYLOAD:
            raise ValueError('complete source node exceeds unchanged RAM payload limit')
        images, meshes, blob = [], [], bytearray()
        for mesh,mesh_pages in planned:
            image = desc["images"][mesh["image"]]
            original_positions = payload[mesh["positions"]["offset"]:mesh["positions"]["offset"]+mesh["positions"]["bytes"]]
            original_uv = payload[mesh["uv"]["offset"]:mesh["uv"]["offset"]+mesh["uv"]["bytes"]]
            original_indices = floats(payload,mesh["indices"],"I")
            for triangles,refs,crop in mesh_pages:
                if full_pixels:
                    x,y,w,h=crop;stride=image['width']*4;offset=image['offset']
                    pixels=b''.join(payload[offset+(y+row)*stride+x*4:offset+(y+row)*stride+(x+w)*4] for row in range(h))
                else:
                    pixels = parse_crop_frame(self._invoke(node,record,"--crop="+','.join(map(str,(mesh['image'],*crop)))),
                                              node,record['bytes'],mesh['image'],image,crop)
                selected = copy.deepcopy(mesh); selected['image']=len(images)
                local = {v:i for i,v in enumerate(refs)}
                # Copy exact float32 bytes: no float roundtrip and no UV rewriting.
                positions = b''.join(original_positions[i*12:i*12+12] for i in refs)
                uv = b''.join(original_uv[i*8:i*8+8] for i in refs)
                indices = array.array('I',(local[original_indices[t*3+k]] for t in triangles for k in range(3)))
                if sys.byteorder!='little': indices.byteswap()
                selected['positions']=segment(blob,positions,len(refs)*3)
                selected['uv']=segment(blob,uv,len(refs)*2)
                selected['indices']=segment(blob,indices.tobytes(),len(triangles)*3)
                points=list(struct.iter_unpack('<fff',positions))
                selected['boundsMin']=[min(p[a] for p in points) for a in range(3)]
                selected['boundsMax']=[max(p[a] for p in points) for a in range(3)]
                selected['originalTriangleIds']=triangles
                new_image={k:v for k,v in image.items() if k not in ('pixelsOmitted',)}
                new_image.update(width=crop[2],height=crop[3],originalWidth=image['width'],originalHeight=image['height'],sourceRect=list(crop))
                new_image.update(segment(blob,pixels,len(pixels)))
                images.append(new_image);meshes.append(selected)
                if len(meshes)>64:raise ValueError('source exceeds unchanged physical-page count')
        result={**desc,'schema':'zhumadian.osgb.crop_memory.v1','images':images,'meshes':meshes,
                'payloadBytes':len(blob),'vertices':sum(m['positions']['count']//3 for m in meshes)}
        if sum(m['indices']['count']//3 for m in meshes)!=desc['triangles']:
            raise ValueError('crop delivery lost original triangles')
        return result,memoryview(bytes(blob))


def page(descriptor,payload,mesh,directory,source_name):
    image = descriptor['images'][mesh['image']]
    part,resources,metrics = original_page(descriptor,payload,mesh,directory,source_name,
                                          metric_image=dict(width=image['originalWidth'],height=image['originalHeight']))
    width,height=image['width'],image['height']
    ow,oh=image['originalWidth'],image['originalHeight']
    x,y,w,h=image['sourceRect']
    s=part['source_image']['sampler']
    levels=1
    if s['minFilter'] not in (9728,9729):
        if (x,y,w,h)!=(0,0,ow,oh):raise ValueError('mipmapped crop is unsupported')
        levels=1+int(math.floor(math.log2(max(width,height))))
    part['source_format']=FORMAT
    part['source_image'].update(original_width=ow,original_height=oh,source_rect=[x,y,w,h],
                                uv_transform=[ow/w,oh/h,-x/w,-y/h],mip_levels=levels)
    part['gpu_payload_bytes']=part['vertices']*64+part['indices']*4+(w*h*4 if levels==1 else mip_bytes(w,h))
    return part,resources,metrics


def build_bundle(*args,**kwargs):
    return original_bundle(*args,**kwargs,page_builder=page,source_format=FORMAT)


def builder_identity():
    return sha(Path(__file__).read_bytes())
