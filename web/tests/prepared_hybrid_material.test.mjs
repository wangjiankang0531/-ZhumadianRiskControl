import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {validateHybridTexture} from '../src/prepared_hybrid_texture.js';
import {validateHybridOverlap} from '../src/prepared_hybrid_overlap.js';
import {sha256,PreparedTextureCancelled,PreparedTextureContextError} from '../src/prepared_bc7.js';
import {SourcePageBudget} from '../src/source_page_budget.js';
import {createHybridSceneContext,applyHybridSceneMaterial,hybridSceneTextureIdentity,HYBRID_LOD_ORACLE_BYTES} from '../src/prepared_hybrid_material.js';
import {hybridFixture as fixture} from './fixtures/hybrid_scene.mjs';
function environment({limit=2*HYBRID_LOD_ORACLE_BYTES,failAt=0,onInit=()=>{}}={}){
 const budget=new SourcePageBudget(limit),uploads=[],deleted=[];let error=0;
 const gl={NO_ERROR:0,isContextLost:()=>false,getError:()=>{const value=error;error=0;return value;}};
 const renderer={capabilities:{maxTextureSize:2048,getMaxAnisotropy:()=>16},extensions:{has:()=>true},getContext:()=>gl,initTexture(texture){uploads.push(texture);texture.addEventListener('dispose',()=>deleted.push(texture));if(uploads.length===failAt)error=1285;onInit(texture,uploads.length);}};
 const context=createHybridSceneContext({THREE,renderer,reserve:q=>budget.reserve(q)});
 return {budget,uploads,deleted,renderer,context};
}
const load=(context,f,extra={})=>context.load(f.prepared,{overlap:f.overlap,...extra});
test('all live pairs share one admitted oracle and preserve full anisotropy/sRGB/mip accounting',async()=>{
 const e=environment(),f=await fixture(),[a,b]=await Promise.all([load(e.context,f),load(e.context,f)]);
 assert.equal(e.budget.held,HYBRID_LOD_ORACLE_BYTES+1352);assert.equal(e.uploads.length,5);assert.equal(e.context.snapshot().oracleReferences,2);assert.equal(a.identity.oracle,b.identity.oracle);
 assert.equal(a.texture.anisotropy,16);assert.equal(a.tail.anisotropy,16);assert.equal(a.identity.oracle.anisotropy,16);assert.equal(a.texture.colorSpace,THREE.SRGBColorSpace);assert.equal(a.tail.colorSpace,THREE.SRGBColorSpace);assert.equal(a.texture.mipmaps.length,3);assert.equal(a.tail.mipmaps.length,4);assert.equal(a.identity.blendStartLevel,1);assert.equal(hybridSceneTextureIdentity(a.texture),a.identity);
 a.texture.dispose();assert.equal(e.budget.held,HYBRID_LOD_ORACLE_BYTES+676);a.dispose();assert.equal(e.budget.held,HYBRID_LOD_ORACLE_BYTES+676);
 b.dispose();assert.equal(e.budget.held,0);assert.equal(e.deleted.length,5);assert.equal(e.context.snapshot().oracleReferences,0);e.context.dispose();
});
test('binding survives MeshBasicMaterial replacement and does not double-patch or own unrelated maps',async()=>{
 const e=environment(),pair=await load(e.context,await fixture()),material=new THREE.MeshBasicMaterial({map:pair.texture});
 assert.equal(applyHybridSceneMaterial(material),true);const compile=material.onBeforeCompile;assert.equal(applyHybridSceneMaterial(material),true);assert.equal(material.onBeforeCompile,compile);
 const shader={uniforms:{},fragmentShader:THREE.ShaderLib.basic.fragmentShader};material.onBeforeCompile(shader,e.renderer);
 assert.equal(shader.uniforms.xnbyHybridTail.value,pair.tail);assert.equal(shader.uniforms.xnbyHybridLevels.value,pair.identity.oracle);assert.ok(shader.fragmentShader.includes('diffuseColor *= xnbyHybridSample(vMapUv)'));assert.equal(material.map,pair.texture);
 assert.equal(applyHybridSceneMaterial(new THREE.MeshBasicMaterial()),false);material.map=null;assert.throws(()=>applyHybridSceneMaterial(material),/map changed/);material.dispose();assert.equal(e.budget.held,HYBRID_LOD_ORACLE_BYTES+676);pair.dispose();assert.equal(e.budget.held,0);
});
test('second-pair tail upload error cleans only its pair while a resident still owns the shared oracle',async()=>{
 const e=environment({failAt:5}),f=await fixture(),first=await load(e.context,f);
 await assert.rejects(load(e.context,f),PreparedTextureContextError);assert.equal(e.budget.held,HYBRID_LOD_ORACLE_BYTES+676);assert.equal(e.context.snapshot().pairs,1);assert.equal(e.deleted.length,2);
 first.dispose();assert.equal(e.budget.held,0);assert.equal(e.deleted.length,5);
});
test('cancellation after prefix upload releases its lease, prefix and otherwise-unused oracle',async()=>{
 let wanted=true;const e=environment({onInit:(_t,n)=>{if(n===2)wanted=false;}});
 await assert.rejects(load(e.context,await fixture(),{stillWanted:()=>wanted}),PreparedTextureCancelled);assert.equal(e.budget.held,0);assert.equal(e.uploads.length,2);assert.equal(e.deleted.length,2);assert.equal(e.context.snapshot().pairs,0);
});
test('the shared oracle cannot evade the page budget and invalid or changed data allocates nothing',async()=>{
 const f=await fixture(),e=environment({limit:HYBRID_LOD_ORACLE_BYTES+675});await assert.rejects(load(e.context,f),/budget exceeded/);assert.equal(e.budget.held,0);assert.equal(e.deleted.length,1);
 const other=environment();await assert.rejects(other.context.load({...f.prepared},{overlap:f.overlap}),/unverified/);await assert.rejects(other.context.load(f.prepared),/verified original overlap/);f.prepared.mips[0].data[0]^=1;await assert.rejects(load(other.context,f),/mip changed/);assert.equal(other.budget.held,0);assert.equal(other.uploads.length,0);
});
test('context disposal drains all owned pairs and later loads fail before admission',async()=>{
 const e=environment(),f=await fixture();await load(e.context,f);await load(e.context,f);e.context.dispose();e.context.dispose();assert.equal(e.budget.held,0);assert.equal(e.deleted.length,5);await assert.rejects(load(e.context,f),/context closed/);
});
test('overlap requires exact source identity, both consecutive levels, bounded offsets and exact original proof',async()=>{
 const f=await fixture();for(const change of [m=>m.schema='xnby.bc7_rgba_tail.v1',m=>m.sourceSHA256='0'.repeat(64),m=>m.basePayloadSHA256='0'.repeat(64),m=>m.startLevel=0,m=>m.mips.pop(),m=>m.mips[0].offset++,m=>m.mips[1].level=3,m=>m.mips[1].quality.rgbPSNR=50,m=>m.mips[1].sourceRgbaSHA256='0'.repeat(64),m=>m.payloadSHA256='0'.repeat(64)]){const m=structuredClone(f.overlapManifest);change(m);await assert.rejects(validateHybridOverlap(f.prepared,m,f.overlapPayload));}
});
test('a mutated overlap view cannot upload and opaque checks remain necessary even with self-consistent hashes',async()=>{
 const f=await fixture(),e=environment();f.overlap.mips[0].data[3]=0;await assert.rejects(load(e.context,f),/mip changed/);assert.equal(e.uploads.length,0);
 const payload=new Uint8Array(f.overlapPayload),m=structuredClone(f.overlapManifest);m.payloadSHA256=await sha256(payload);m.mips[0].sha256=m.mips[0].sourceRgbaSHA256=await sha256(payload.subarray(0,256));await assert.rejects(validateHybridOverlap(f.prepared,m,payload.buffer),/not opaque/);
});
