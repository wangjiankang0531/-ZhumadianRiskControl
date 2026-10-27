import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {hybridFixture} from './fixtures/hybrid_scene.mjs';
import {sha256,rgbaMipBytes,PreparedTextureCancelled} from '../src/prepared_bc7.js';
import {describeScenePhotograph,validateScenePhotograph,loadScenePhotograph,hybridPhotographIdentity} from '../src/prepared_hybrid_scene.js';
import {PreparedTextureIndex} from '../src/prepared_texture_index.js';
import {planPreparedSourceBundle} from '../src/prepared_source_page.js';
import {SourcePageBudget} from '../src/source_page_budget.js';
import {createHybridSceneContext,HYBRID_LOD_ORACLE_BYTES} from '../src/prepared_hybrid_material.js';
async function fixture(){const f=await hybridFixture(),all=new Uint8Array(676);all.set(new Uint8Array(f.prefix));all.set(new Uint8Array(f.tail),336);all.set(new Uint8Array(f.overlapPayload),356);return {...f,source:{sha256:'a'.repeat(64),width:16,height:16},manifest:{schema:'xnby.prepared_hybrid_scene.v1',format:'BC7_RGBA_OVERLAP',sourceSHA256:'a'.repeat(64),sourceSize:[16,16],payloadBytes:676,payloadSHA256:await sha256(all),texture:f.manifest,overlap:f.overlapManifest},payloads:{prefix:f.prefix,tail:f.tail,overlap:f.overlapPayload}};}
test('source planning prices the complete pair and binds its combined content identity',async()=>{
 const f=await fixture(),info=describeScenePhotograph(f.manifest,f.source);assert.equal(info.bytes,676);assert.equal(info.format,'bc7_rgba_overlap');
 const part={directory:'part_000',vertices:3,indices:3,atlas_extent:[16,16],gpu_payload_bytes:rgbaMipBytes(16,16)+3*64+3*4,files:[{name:'atlas.jpg',bytes:10,sha256:f.source.sha256}]},marker={parts:[part],gpu_payload_bytes:part.gpu_payload_bytes};
 const plan=await planPreparedSourceBundle({marker,supported:true,loadManifest:async()=>f.manifest});assert.equal(plan.marker.parts[0].runtime_texture.textureBytes,676);assert.equal(plan.marker.parts[0].runtime_texture.payloadSHA256,f.manifest.payloadSHA256);assert.equal(plan.marker.gpu_payload_bytes,676+108);
 for(const change of [m=>m.payloadBytes--,m=>m.sourceSize[0]=12,m=>m.texture.mips[2].accepted=false,m=>m.overlap.startLevel=0]){const m=structuredClone(f.manifest);change(m);assert.throws(()=>describeScenePhotograph(m,f.source));}
});
test('combined hashes and all three payload identities are verified before scene admission',async()=>{
 const f=await fixture();assert.equal((await validateScenePhotograph(f.manifest,f.payloads,f.source)).descriptor.bytes,676);
 const bad=structuredClone(f.manifest);bad.payloadSHA256='0'.repeat(64);await assert.rejects(validateScenePhotograph(bad,f.payloads,f.source),/combined content/);const tail=f.tail.slice(0);new Uint8Array(tail)[0]^=1;await assert.rejects(validateScenePhotograph(f.manifest,{...f.payloads,tail},f.source));
});
test('the context owns pair admission once and the public photograph identity ends on disposal',async()=>{
 const f=await fixture(),texture=new THREE.Texture();let calls=0,disposals=0;
 const photo=await loadScenePhotograph({supported:true,source:f.source,loadManifest:async()=>f.manifest,loadPayload:async()=>f.payloads,reserve:()=>{throw Error('duplicate reservation');},hybridContext:{load:async()=>{calls++;return {bytes:676,texture,dispose(){disposals++;texture.dispose();}};}}});
 assert.equal(calls,1);assert.equal(photo.bytes,676);assert.equal(hybridPhotographIdentity(texture).payloadSHA256,f.manifest.payloadSHA256);photo.dispose();assert.equal(disposals,1);assert.equal(hybridPhotographIdentity(texture),null);
});
test('a failed hybrid is repriced at complete RGBA cost before fallback starts',async()=>{
 const f=await fixture(),ledger=new SourcePageBudget(2048);let loadCalls=0,heldAtDecode=0;const bad=structuredClone(f.manifest);bad.payloadSHA256='0'.repeat(64);
 const photo=await loadScenePhotograph({supported:true,source:f.source,loadManifest:async()=>bad,loadPayload:async()=>f.payloads,reserve:q=>ledger.reserve(q),hybridContext:{load:async()=>{loadCalls++;}},loadFallback:async()=>{heldAtDecode=ledger.held;return new THREE.Texture();}});
 assert.equal(loadCalls,0);assert.equal(heldAtDecode,rgbaMipBytes(16,16));assert.equal(photo.format,'rgba8');photo.dispose();assert.equal(ledger.held,0);
});
test('cancellation after payload fetch neither uploads nor silently falls back',async()=>{
 const f=await fixture();let wanted=true,calls=0;await assert.rejects(loadScenePhotograph({supported:true,source:f.source,stillWanted:()=>wanted,loadManifest:async()=>f.manifest,loadPayload:async()=>{wanted=false;return f.payloads;},hybridContext:{load:async()=>{calls++;}},loadFallback:async()=>{calls++;},reserve:()=>{calls++;}}),PreparedTextureCancelled);assert.equal(calls,0);
});
test('v2 index restricts component routes and binds descriptor type as well as hashes',async()=>{
 const f=await fixture(),part={files:[{name:'atlas.jpg',sha256:f.source.sha256}]},urls=[];let descriptor=f.manifest;
 const index=new PreparedTextureIndex({schema:'xnby.prepared_texture_index.v2',entries:[{sourceSHA256:f.source.sha256,payloadSHA256:f.manifest.payloadSHA256,format:'bc7_rgba_overlap'}]},'http://127.0.0.1:1234/sub/',async url=>{urls.push(url);return {ok:true,json:async()=>descriptor,arrayBuffer:async()=>new ArrayBuffer(0)};});
 assert.equal(index.hybridCount,1);assert.equal((await index.manifest(part)).schema,'xnby.prepared_hybrid_scene.v1');await index.payload(part);assert.equal(urls.length,4);assert.ok(urls.every(url=>url.startsWith('http://127.0.0.1:1234/sub/prepared-hybrid-textures/')));assert.throws(()=>index.url(part,'../../config.json'));
 descriptor={...f.manifest,schema:'xnby.bc7.mip_chain.v1'};await assert.rejects(index.manifest(part),/differs from index/);index.rejectHybrids();assert.equal(index.hybridCount,0);assert.equal(index.has(part),false);
});
test('a lifetime oracle pin stays in the shared ledger while all source pages are absent',async()=>{
 const f=await fixture(),ledger=new SourcePageBudget(HYBRID_LOD_ORACLE_BYTES+676),gl={NO_ERROR:0,getError:()=>0,isContextLost:()=>false},renderer={capabilities:{maxTextureSize:2048,getMaxAnisotropy:()=>16},extensions:{has:()=>true},getContext:()=>gl,initTexture(){}};
 const context=createHybridSceneContext({THREE,renderer,reserve:q=>ledger.reserve(q)}),pin=await context.pin();assert.equal(ledger.held,HYBRID_LOD_ORACLE_BYTES);const pair=await context.load(f.prepared,{overlap:f.overlap});assert.equal(ledger.held,HYBRID_LOD_ORACLE_BYTES+676);pair.dispose();assert.equal(ledger.held,HYBRID_LOD_ORACLE_BYTES);context.dispose();assert.equal(ledger.held,0);pin.release();assert.equal(ledger.held,0);
});
