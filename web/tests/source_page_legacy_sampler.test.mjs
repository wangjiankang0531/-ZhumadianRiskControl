import test from 'node:test';
import assert from 'node:assert/strict';
import {validateSourcePageGltf} from '../src/prepared_source_page.js';
import {geometryFixture} from './fixtures/source_geometry.mjs';
const fixture=()=>({part:{vertices:3,indices:3},gltf:geometryFixture().gltf});
test('historical atlas without sampler is accepted without changing source JSON',()=>{
 const {part,gltf}=fixture();delete gltf.textures[0].sampler;delete gltf.samplers;
 const before=JSON.stringify(gltf);validateSourcePageGltf(gltf,part);assert.equal(JSON.stringify(gltf),before);
});
test('explicit edge-clamped atlas sampler still passes',()=>{const {part,gltf}=fixture();validateSourcePageGltf(gltf,part);});
test('dangling explicit sampler indices never become legacy defaults',()=>{
 for(const index of [0,1,-1,null,'0']){const {part,gltf}=fixture();delete gltf.samplers;gltf.textures[0].sampler=index;assert.throws(()=>validateSourcePageGltf(gltf,part),/sampler/);}
});
test('an empty or null sampler collection is not historical omission',()=>{
 for(const samplers of [[],null]){const {part,gltf}=fixture();delete gltf.textures[0].sampler;gltf.samplers=samplers;assert.throws(()=>validateSourcePageGltf(gltf,part),/sampler/);}
});
test('explicit incompatible atlas sampling is still rejected',()=>{
 for(const [key,value] of [['wrapS',10497],['wrapT',33648],['minFilter',9728],['magFilter',9728]]){const {part,gltf}=fixture();gltf.samplers[0][key]=value;assert.throws(()=>validateSourcePageGltf(gltf,part),/sampler/);}
});
test('versioned original image pages cannot enter legacy atlas compatibility',()=>{
 const {part,gltf}=fixture();part.source_format='osgb_memory_png_v1';part.geometry_layout='three_float32_pu_uint32_v1';gltf.images[0].uri='texture.png';delete gltf.meshes[0].primitives[0].attributes.NORMAL;delete gltf.textures[0].sampler;delete gltf.samplers;
 assert.throws(()=>validateSourcePageGltf(gltf,part),/sampler/);
});
test('legacy sampler compatibility does not weaken file or extension validation',()=>{
 for(const change of [g=>g.images[0].uri='https://unrelated.invalid/a.jpg',g=>g.extensionsRequired=['unknown']]){const {part,gltf}=fixture();delete gltf.textures[0].sampler;delete gltf.samplers;change(gltf);assert.throws(()=>validateSourcePageGltf(gltf,part));}
});
