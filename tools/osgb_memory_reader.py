"""Validate a bounded read-only OSGB stdout frame; never create converted asset files."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess

MAX_PAYLOAD = 128 * 1024 * 1024
MAX_HEADER = 1024 * 1024
# Original input bytes are distinct from decoded frames and GPU upload pages.
MAX_SOURCE = 128 * 1024 * 1024


def integer(value, name, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"invalid {name}")
    return value


def parse_frame(data, expected_node, expected_source_bytes):
    return _parse_frame(data, expected_node, expected_source_bytes)


def _parse_frame(data, expected_node, expected_source_bytes, *, geometry_only=False):
    if len(data) < 24 or data[:8] != (b"ZMDGEO01" if geometry_only else b"ZMDOSGB1"):
        raise ValueError("invalid OSGB memory frame magic")
    header_size, payload_size = struct.unpack_from("<QQ", data, 8)
    if not 0 < header_size <= MAX_HEADER or not 0 < payload_size <= MAX_PAYLOAD or len(data) != 24 + header_size + payload_size:
        raise ValueError("invalid OSGB memory frame length")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate memory descriptor key")
            result[key] = value
        return result
    descriptor = json.loads(data[24:24+header_size], object_pairs_hook=unique_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite descriptor")))
    if (descriptor.get("schema") != ("zhumadian.osgb.geometry.v1" if geometry_only else "zhumadian.osgb.memory.v1") or descriptor.get("node") != expected_node
        or descriptor.get("sourceBytes") != expected_source_bytes or descriptor.get("payloadBytes") != payload_size
        or type(descriptor.get("externalReadAttempts")) is not int or descriptor.get("externalReadAttempts") != 0
        or type(descriptor.get("writeAttempts")) is not int or descriptor.get("writeAttempts") != 0
        or descriptor.get("coordinates") != "source_local_metres" or descriptor.get("uv") != "source_unchanged"
        or descriptor.get("littleEndian") is not True):
        raise ValueError("memory descriptor identity or access mode mismatch")
    payload = memoryview(data)[24+header_size:]
    ranges = []
    def segment(value, width, label):
        offset = integer(value.get("offset"), label+" offset", payload_size)
        amount = integer(value.get("bytes"), label+" bytes", payload_size)
        count = integer(value.get("count"), label+" count", MAX_PAYLOAD)
        if not amount or offset % 4 or amount != count*width or offset+amount > payload_size:
            raise ValueError("invalid "+label+" segment")
        span = (offset, offset+amount)
        if any(span[0] < old[1] and old[0] < span[1] for old in ranges):
            raise ValueError("overlapping memory segments")
        ranges.append(span)
        return payload[offset:offset+amount]
    images = descriptor.get("images")
    meshes = descriptor.get("meshes")
    if not isinstance(images, list) or not 0 < len(images) <= 1024 or not isinstance(meshes, list) or not 0 < len(meshes) <= 2048:
        raise ValueError("invalid memory mesh/image list")
    for image in images:
        width = integer(image.get("width"), "image width", 8192)
        height = integer(image.get("height"), "image height", 8192)
        if (not width or not height or (not geometry_only and width*height*4 > 32*1024*1024) or image.get("format") != "rgba8"
            or image.get("rowOrder") != "source_storage" or image.get("sourceOrigin") not in ("top_left", "bottom_left")
            or (not geometry_only and image.get("bytes") != width*height*4)):
            raise ValueError("invalid memory image")
        if geometry_only:
            if image.get("pixelsOmitted") is not True or any(k in image for k in ("offset", "bytes", "count")):
                raise ValueError("geometry frame contains unexpected image payload")
        else:
            segment(image, 1, "image")
    vertices = triangles = 0
    for mesh in meshes:
        positions = segment(mesh["positions"], 4, "positions")
        uv = segment(mesh["uv"], 4, "uv")
        indices = segment(mesh["indices"], 4, "indices")
        count = len(positions)//12
        if not count or len(positions)%12 or len(uv) != count*8 or len(indices)%12 or mesh.get("unlit") is not True:
            raise ValueError("invalid source triangle arrays")
        if mesh.get("vertexColorsWhite") is not True:
            raise ValueError("source needs a vertex color material adapter")
        sampler = mesh.get("sampler")
        if not isinstance(sampler, dict) or set(sampler) != {"wrapS","wrapT","minFilter","magFilter"} or any(type(v) is not int for v in sampler.values()):
            raise ValueError("invalid source sampler")
        integer(mesh.get("image"), "mesh image", len(images)-1)
        if any(not math.isfinite(value[0]) for value in struct.iter_unpack("<f", positions)) or any(not math.isfinite(value[0]) for value in struct.iter_unpack("<f", uv)):
            raise ValueError("nonfinite source arrays")
        if any(index[0] >= count for index in struct.iter_unpack("<I", indices)):
            raise ValueError("source index exceeds vertex count")
        for key in ("boundsMin", "boundsMax"):
            if not isinstance(mesh.get(key), list) or len(mesh[key]) != 3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in mesh[key]):
                raise ValueError("invalid source bounds")
        vertices += count
        triangles += len(indices)//12
    integer(descriptor.get("vertices"), "total vertices", 2000000)
    integer(descriptor.get("triangles"), "total triangles", 2000000)
    if vertices != descriptor.get("vertices") or triangles != descriptor.get("triangles") or vertices > 2000000 or triangles*3 > 6000000:
        raise ValueError("source totals do not match")
    ordered = sorted(ranges)
    if ordered[0][0] != 0 or ordered[-1][1] != payload_size or any(0 > right[0]-left[1] or right[0]-left[1] > 3 for left,right in zip(ordered,ordered[1:])):
        raise ValueError("memory payload has unclaimed segments")
    return descriptor, payload


def read_node(executable, source_root, node, expected_sha256, *, executable_sha256, timeout=30):
    executable, source_root = Path(executable).resolve(strict=True), Path(source_root).resolve(strict=True)
    match = re.fullmatch(r"(Tile_[0-9]+)/(Tile_[0-9]+_L[0-9]+_0[0-9u]+\.osgb)", node)
    if not match or not match.group(2).startswith(match.group(1)+"_L") or source_root.name != "Data":
        raise ValueError("invalid relative source node")
    source = source_root / match.group(1) / match.group(2)
    for item in (source_root, source.parent, source):
        stat = item.lstat()
        if item.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError("source links and junctions are forbidden")
    if not source.resolve(strict=True).is_relative_to(source_root):
        raise ValueError("source outside configured Data root")
    size = source.stat().st_size
    if not 0 < size <= MAX_SOURCE:
        raise ValueError("source size outside bounds")
    before = (source.stat().st_size, source.stat().st_mtime_ns, hashlib.sha256(source.read_bytes()).hexdigest())
    if before[2] != expected_sha256 or hashlib.sha256(executable.read_bytes()).hexdigest() != executable_sha256:
        raise ValueError("source or executable SHA mismatch")
    environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "SystemDrive") if key in os.environ}
    environment["PATH"] = str(executable.parent) + os.pathsep + str(Path(os.environ.get("SystemRoot", "C:/Windows"))/"System32")
    completed = subprocess.run([str(executable), str(source_root), node, str(executable.parent/"osgPlugins-3.6.5")],
                               cwd=executable.parent, executable=str(executable), env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    after = (source.stat().st_size, source.stat().st_mtime_ns, hashlib.sha256(source.read_bytes()).hexdigest())
    if before != after:
        raise RuntimeError("source changed while decoding")
    if completed.returncode:
        raise RuntimeError(f"read-only decoder returned {completed.returncode}: {completed.stderr.decode('utf-8',errors='replace')[:2000]}")
    descriptor, payload = parse_frame(completed.stdout, node, size)
    return descriptor, payload, {"sourceUnchanged": True, "sourceSha256": before[2], "frameSha256": hashlib.sha256(completed.stdout).hexdigest(), "stderr": completed.stderr.decode('utf-8',errors='replace')[:2000]}
