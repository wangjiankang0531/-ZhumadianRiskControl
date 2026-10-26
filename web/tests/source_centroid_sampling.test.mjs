import test from 'node:test';import assert from 'node:assert/strict';
import {MeshBasicMaterial,Texture,ShaderChunk,SRGBColorSpace,LinearFilter} from 'three';
import {clientSourcePageFixture} from './fixtures/client_source_page.mjs';
import {SOURCE_CENTROID_POLICY,applySourceCentroidSampling,sourceCentroidSampling,patchSourceCentroidShader} from '../src/source_centroid_sampling.js';
async function fixture(){const {part}=await clientSourcePageFixture(),map=new Texture();Object.assign(map,{colorSpace:SRGBColorSpace,minFilter:LinearFilter,magFilter:LinearFilter,generateMipmaps:false,anisotropy:1,flipY:false});return {part,map,material:new MeshBasicMaterial({map})};}
test('disabled sampling has no mutation and cannot silently enable a new raster policy',()=>{assert.equal(applySourceCentroidSampling(null),null);assert.throws(()=>applySourceCentroidSampling(null,{enabled:1}),/opt-in/);});
test('centroid hook retains the previous hook receiver, uniforms and texture while declaring distinct program identity',async()=>{
 const {part,map,material}=await fixture();const oldChunk=ShaderChunk.uv_pars_vertex;let invoked=0;material.onBeforeCompile=function(shader,r){assert.equal(this,material);assert.equal(r,17);invoked++;shader.uniforms.kept=9;};material.customProgramCacheKey=()=> 'previous-policy';const oldTextureVersion=map.version;
 const p=applySourceCentroidSampling(material,{enabled:true,part}),shader={vertexShader:'#include <uv_pars_vertex>\nvoid main(){}',fragmentShader:'#include <uv_pars_fragment>\nvoid main(){}',uniforms:{}};material.onBeforeCompile(shader,17);
 assert.equal(invoked,1);assert.equal(shader.uniforms.kept,9);assert.match(shader.vertexShader,/centroid varying vec2 vMapUv;/);assert.match(shader.fragmentShader,/centroid varying vec2 vMapUv;/);assert.equal(ShaderChunk.uv_pars_vertex,oldChunk);assert.equal(material.map,map);assert.equal(map.version,oldTextureVersion);assert.equal(material.customProgramCacheKey(),'previous-policy|'+SOURCE_CENTROID_POLICY);assert.equal(sourceCentroidSampling(material),p);assert.equal(p.sourceSHA256,part.files.find(f=>f.name==='texture.png').sha256);assert.ok(Object.isFrozen(p));
});
test('same source installation is idempotent, and a different source cannot reuse the material proof',async()=>{
 const {part,material}=await fixture(),p=applySourceCentroidSampling(material,{enabled:true,part}),hook=material.onBeforeCompile;assert.equal(applySourceCentroidSampling(material,{enabled:true,part}),p);assert.equal(material.onBeforeCompile,hook);const other=structuredClone(part);other.files.find(f=>f.name==='texture.png').sha256='a'.repeat(64);assert.throws(()=>applySourceCentroidSampling(material,{enabled:true,part:other}),/identity differs/);assert.equal(material.onBeforeCompile,hook);
});
test('unknown shader includes or chunk declaration shapes reject before either shader field is rewritten',()=>{
 for(const chunks of [{...ShaderChunk,uv_pars_fragment:'unknown'},{...ShaderChunk,uv_pars_vertex:'varying vec2 vMapUv;\nvarying vec2 vMapUv;'}]){const shader={vertexShader:'#include <uv_pars_vertex>',fragmentShader:'#include <uv_pars_fragment>'},before={...shader};assert.throws(()=>patchSourceCentroidShader(shader,chunks),/contract differs/);assert.deepEqual(shader,before);}
 assert.throws(()=>patchSourceCentroidShader({vertexShader:'unknown',fragmentShader:'#include <uv_pars_fragment>'}),/contract differs/);
});
test('unsupported mip, filter, colorspace or anisotropy never installs a material policy',async()=>{
 for(const change of [{generateMipmaps:true},{minFilter:1008},{colorSpace:''},{anisotropy:4},{flipY:true}]){const {part,map,material}=await fixture(),hook=material.onBeforeCompile;Object.assign(map,change);assert.throws(()=>applySourceCentroidSampling(material,{enabled:true,part}),/parameters differ/);assert.equal(sourceCentroidSampling(material),null);assert.equal(material.onBeforeCompile,hook);}
});
test('an incompatible source or malformed chunk cannot partially install a policy or program key',async()=>{
 const {part,material}=await fixture(),hook=material.onBeforeCompile,key=material.customProgramCacheKey;assert.throws(()=>applySourceCentroidSampling(material,{enabled:true,part,chunks:{}}),/contract differs/);assert.equal(material.onBeforeCompile,hook);assert.equal(material.customProgramCacheKey,key);const source=structuredClone(part);source.source_image.sampler.minFilter=9728;assert.throws(()=>applySourceCentroidSampling(material,{enabled:true,part:source}),/eligible/);assert.equal(sourceCentroidSampling(material),null);
});
