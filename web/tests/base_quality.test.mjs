import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {baseGeometryDescriptor,preparedQualityRecord,validatePreparedQuality,resolveBaseQuality,measureBaseQualityAsync} from '../src/base_quality.js';
import {measureBaseEdges,measureBaseTexels} from '../src/lod_policy.js';
const sha=bytes=>crypto.createHash('sha256').update(new Uint8Array(bytes.buffer??bytes,bytes.byteOffset??0,bytes.byteLength)).digest('hex');
function fixture(roots=2){
 const positions=new Float32Array([0,0,0,10,0,0,0,10,0]),uvs=new Float32Array([0,0,1,0,0,1]),indices=new Uint32Array(Array.from({length:roots},()=>[0,1,2]).flat());
 const buffer=Buffer.concat([Buffer.from(positions.buffer),Buffer.from(uvs.buffer),Buffer.from(indices.buffer)]),catalog={root_records:Array.from({length:roots},(_,i)=>({tile_id:i+1,base_spans:[[i*3,3]]}))},catalogBytes=Buffer.from(JSON.stringify(catalog));
 const gltf={buffers:[{uri:'base.bin',byteLength:buffer.length}],bufferViews:[{buffer:0,byteOffset:0},{buffer:0,byteOffset:36},{buffer:0,byteOffset:60}],accessors:[{bufferView:0,type:'VEC3',componentType:5126,count:3},{bufferView:1,type:'VEC2',componentType:5126,count:3},{bufferView:2,type:'SCALAR',componentType:5125,count:indices.length}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2}]}]},geometry={positions,uvs,indices,textureWidth:100,textureHeight:100};
 const record=preparedQualityRecord(catalog,geometry,baseGeometryDescriptor(gltf),{catalog:sha(catalogBytes),buffer:sha(buffer)});
 return{catalog,catalogBytes,gltf,geometry,record,buffer:async()=>buffer,digest:async bytes=>sha(bytes),fetchPrepared:async()=>record,yieldControl:async()=>{}};
}
test('prepared quality equals actual triangle measurements for every complete base root',async()=>{
 const f=fixture(),result=await resolveBaseQuality(f);assert.equal(result.source,'prepared');assert.deepEqual(result.edges,measureBaseEdges(f.catalog,f.geometry.positions,f.geometry.indices));assert.deepEqual(result.texels,measureBaseTexels(f.catalog,f.geometry.positions,f.geometry.indices,f.geometry.uvs,100,100));
});
test('both binary content and catalog spans are bound before adopting prepared values',async()=>{
 for(const field of ['buffer_sha256','catalog_sha256']){const f=fixture();f.record[field]='f'.repeat(64);assert.equal((await resolveBaseQuality(f)).source,'measured');}
});
test('invalid metadata falls back before hashing the large base buffer',async()=>{
 for(const mutate of [r=>r.roots.pop(),r=>r.roots[1].tile_id=1,r=>r.roots[0].edge_p90_m=-1,r=>r.roots[0].texel_p90_m=NaN,r=>r.texture_width=200,r=>r.policy='different']){const f=fixture();mutate(f.record);let hashed=false;f.digest=async()=>{hashed=true;return'';};assert.equal((await resolveBaseQuality(f)).source,'measured');assert.equal(hashed,false);}
});
test('missing metadata, unavailable crypto and truncated buffer preserve a measured fallback',async()=>{
 for(const field of ['fetchPrepared','digest','buffer']){const f=fixture();f[field]=async()=>{throw Error('unavailable');};const result=await resolveBaseQuality(f);assert.equal(result.source,'measured');assert.equal(result.edges.size,2);}
 const f=fixture();f.buffer=async()=>new ArrayBuffer(1);assert.equal((await resolveBaseQuality(f)).source,'measured');
});
test('fallback yields between batches and retains exact same P90 values',async()=>{
 const f=fixture(20);let yields=0;const result=await measureBaseQualityAsync(f.catalog,f.geometry,async()=>{yields++;});assert.equal(yields,2);assert.deepEqual(result.edges,measureBaseEdges(f.catalog,f.geometry.positions,f.geometry.indices));
});
test('zero UV scale remains zero instead of inventing positive texture precision',()=>{
 const f=fixture();f.geometry.uvs.fill(0);const record=preparedQualityRecord(f.catalog,f.geometry,baseGeometryDescriptor(f.gltf),{catalog:sha(f.catalogBytes),buffer:'a'.repeat(64)});assert.equal(record.roots[0].texel_p90_m,0);assert.equal(validatePreparedQuality(record,f.catalog,baseGeometryDescriptor(f.gltf),100,100).texels.size,0);
});
test('unsupported interleaved accessors use actual geometry fallback',async()=>{
 const f=fixture();f.gltf.bufferViews[0].byteStride=16;assert.throws(()=>baseGeometryDescriptor(f.gltf));assert.equal((await resolveBaseQuality(f)).source,'measured');
});

test('default fallback scheduling completes without requiring animation frames',async()=>{
 const f=fixture(20),result=await measureBaseQualityAsync(f.catalog,f.geometry);assert.equal(result.edges.size,20);assert.equal(result.source,'measured');
});
