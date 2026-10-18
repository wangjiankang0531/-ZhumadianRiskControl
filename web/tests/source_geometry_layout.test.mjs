import test from 'node:test';
import assert from 'node:assert/strict';
import {BufferAttribute,InterleavedBuffer,InterleavedBufferAttribute} from 'three';
import {WEB_SOURCE_GEOMETRY_LAYOUT,webSourceGeometryBytes,validateSourceGltfGeometry,validateLoadedSourceGeometry} from '../src/source_geometry_layout.js';
import {sourcePageGeometryBytes,loadPreparedSourcePage} from '../src/prepared_source_page.js';
import {sha256} from '../src/prepared_bc7.js';
import {geometryFixture} from './fixtures/source_geometry.mjs';

test('WEB Float32 position/normal/UV and Uint32 index bytes agree with actual BufferGeometry; source manifest remains native64',()=>{
 const f=geometryFixture();assert.equal(WEB_SOURCE_GEOMETRY_LAYOUT,'three_float32_pnu_uint32_v1');assert.equal(validateSourceGltfGeometry(f.gltf,f.part,f.binary),108);assert.equal(validateLoadedSourceGeometry(f.geometry,f.part),108);assert.equal(webSourceGeometryBytes(f.part),108);assert.equal(sourcePageGeometryBytes(f.part),204);
});
test('stride, aliasing, normalized/sparse, wrong component counts and overlapping source views are refused',()=>{
 const changes=[f=>f.gltf.bufferViews[0].byteStride=16,f=>f.gltf.meshes[0].primitives[0].attributes.NORMAL=0,f=>f.gltf.accessors[1].normalized=true,f=>f.gltf.accessors[2].sparse={},f=>f.gltf.accessors[2].componentType=5123,f=>f.gltf.accessors[1].count=2,f=>f.gltf.bufferViews[1].byteOffset=0,f=>f.gltf.accessors[0].byteOffset=4,f=>f.gltf.bufferViews[3].target=34962];
 for(const change of changes){const f=geometryFixture();change(f);assert.throws(()=>validateSourceGltfGeometry(f.gltf,f.part,f.binary));}
});
test('extra scene transforms, skins, morph targets, trailing storage and unexplained dependencies do not acquire WEB identity',()=>{
 for(const change of [f=>f.gltf.nodes[0].scale=[2,2,2],f=>f.gltf.skins=[{}],f=>f.gltf.meshes[0].primitives[0].targets=[],f=>f.gltf.buffers[0].byteLength++,f=>f.gltf.buffers[0].uri='other.bin']){const f=geometryFixture();change(f);assert.throws(()=>validateSourceGltfGeometry(f.gltf,f.part,f.binary));}
});
test('non-finite coordinates and out-of-range indices are rejected from the SHA-pinned binary',()=>{
 for(const mutate of [f=>new Float32Array(f.binary)[0]=NaN,f=>new Float32Array(f.binary)[10]=Infinity,f=>new Uint32Array(f.binary,96)[2]=3]){const f=geometryFixture();mutate(f);assert.throws(()=>validateSourceGltfGeometry(f.gltf,f.part,f.binary));}
});
test('actual parsed attributes cannot switch type, stride, count, normalized mode or add another GPU buffer',()=>{
 const changes=[g=>g.setAttribute('normal',new BufferAttribute(new Uint8Array(9),3)),g=>g.setAttribute('uv',new InterleavedBufferAttribute(new InterleavedBuffer(new Float32Array(9),3),2,0)),g=>g.attributes.position.count=2,g=>g.attributes.normal.normalized=true,g=>g.setAttribute('color',new BufferAttribute(new Float32Array(9),3)),g=>g.setIndex(new BufferAttribute(new Uint16Array([0,1,2]),1)),g=>g.morphAttributes.position=[g.attributes.position]];
 for(const change of changes){const f=geometryFixture();change(f.geometry);assert.throws(()=>validateLoadedSourceGeometry(f.geometry,f.part));}
});
test('WEB geometry arithmetic overflow, negative counts and non-triangle indices are refused',()=>{
 for(const p of [{vertices:Number.MAX_SAFE_INTEGER,indices:3},{vertices:0,indices:3},{vertices:3,indices:4}])assert.throws(()=>webSourceGeometryBytes(p));
});
test('a newly pinned invalid index is refused before any reservation, photograph or GPU load',async()=>{
 const f=geometryFixture();new Uint32Array(f.binary,96)[2]=3;const json=new TextEncoder().encode(JSON.stringify(f.gltf)).buffer;
 const p={...f.part,atlas_size:16,gpu_payload_bytes:1568,files:[{name:'atlas.jpg',sha256:'a'.repeat(64),bytes:1},{name:'geometry.gltf',bytes:json.byteLength,sha256:await sha256(json)},{name:'geometry.bin',bytes:f.binary.byteLength,sha256:await sha256(f.binary)}]};let reserved=0,photos=0;
 await assert.rejects(loadPreparedSourcePage({part:p,supported:false,loadFile:async name=>{if(name==='atlas.jpg')photos++;return name==='geometry.gltf'?json:f.binary;},reserve:()=>{reserved++;throw Error('must not reserve');}}),/index out of range/);assert.equal(reserved,0);assert.equal(photos,0);
});
