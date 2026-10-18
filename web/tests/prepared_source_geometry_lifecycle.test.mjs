import test from 'node:test';
import assert from 'node:assert/strict';
import {TextureLoader,DataTexture,Group} from 'three';
import * as THREE from 'three';
import {geometryFixture} from './fixtures/source_geometry.mjs';
import {sha256} from '../src/prepared_bc7.js';
import {SourcePageBudget} from '../src/source_page_budget.js';
import {SourceFrontier} from '../src/source_frontier.js';
import {planPreparedSourceBundle,stagePreparedSourceBundle,originalSourceBundle} from '../src/prepared_source_page.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
async function fixture(){
 const f=geometryFixture(),json=new TextEncoder().encode(JSON.stringify(f.gltf)).buffer,jpeg=new Uint8Array([255,216,255,217]).buffer;
 const part={...f.part,directory:'part_000',atlas_size:16,atlas_extent:[16,16],atlas_layout_policy:'edge_packed_rect_v1',gpu_payload_bytes:1568,files:[]};for(const [name,data] of [['geometry.gltf',json],['geometry.bin',f.binary],['atlas.jpg',jpeg]])part.files.push({name,bytes:data.byteLength,sha256:await sha256(data)});
 return {marker:{parts:[part],indices:3,gpu_payload_bytes:1568,source_nodes:[{name:'synthetic',children:[],depth:3,triangles:1,bounds_min:[-1,-1,0],bounds_max:[1,1,0],longest_edge_p90_m:1,texel_world_p90_m:.1,spans:[{part:'part_000',first:0,count:3}]}]},loadFile:async(part,name)=>({'geometry.gltf':json,'geometry.bin':f.binary,'atlas.jpg':jpeg})[name]};
}
// Only JPEG transport is stubbed. Real GLTFLoader parses the pinned typed arrays;
// no WebGL/GPU claim is made by these transaction/lifecycle tests.
async function withPhotoTransport(run){
 const descriptor=Object.getOwnPropertyDescriptor(TextureLoader.prototype,'loadAsync'),oldProgress=globalThis.ProgressEvent;
 TextureLoader.prototype.loadAsync=async()=>{const texture=new DataTexture(new Uint8Array(16*16*4),16,16);texture.generateMipmaps=true;texture.needsUpdate=true;return texture;};
 if(!globalThis.ProgressEvent)globalThis.ProgressEvent=class{constructor(type,values){this.type=type;Object.assign(this,values);}};
 try{return await run();}finally{if(descriptor)Object.defineProperty(TextureLoader.prototype,'loadAsync',descriptor);else delete TextureLoader.prototype.loadAsync;if(oldProgress===undefined)delete globalThis.ProgressEvent;else globalThis.ProgressEvent=oldProgress;}
}
test('real parsed WEB layout keeps original storage identity and releases geometry/photo once',()=>withPhotoTransport(async()=>{
 const f=await fixture(),before=structuredClone(f.marker),plan=await planPreparedSourceBundle({marker:f.marker,supported:false}),ledger=new SourcePageBudget(4096);let uploads=0;
 const staged=await stagePreparedSourceBundle({THREE,marker:f.marker,plan,supported:false,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),upload:()=>{uploads++;}});
 assert.equal(uploads,1);assert.equal(staged.marker.gpu_payload_bytes,1472);assert.equal(ledger.held,1472);assert.equal(new SourceFrontier(staged.marker,staged.meshes).bytes,1472);assert.deepEqual(originalSourceBundle(staged.marker),before);assert.equal(staged.marker.parts[0].runtime_texture.geometryLayout,'three_float32_pnu_uint32_v1');staged.dispose();staged.dispose();assert.equal(ledger.held,0);
}));
test('a prepare callback changing actual WEB layout is rejected before upload and returns all reservations',()=>withPhotoTransport(async()=>{
 const f=await fixture(),plan=await planPreparedSourceBundle({marker:f.marker,supported:false}),ledger=new SourcePageBudget(4096),oldCut=new Group(),child=new Group();oldCut.add(child);let uploads=0;
 await assert.rejects(stagePreparedSourceBundle({THREE,marker:f.marker,plan,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),prepare:model=>{model.scene.children[0].geometry.attributes.uv.itemSize=3;},upload:()=>{uploads++;}}),/WEB geometry layout/);
 assert.equal(uploads,0);assert.equal(ledger.held,0);assert.deepEqual(oldCut.children,[child]);
}));
test('cancellation after actual parse but before upload returns new geometry/photo leases and never attaches a page',()=>withPhotoTransport(async()=>{
 const f=await fixture(),plan=await planPreparedSourceBundle({marker:f.marker,supported:false}),ledger=new SourcePageBudget(4096);let wanted=true,uploads=0;
 await assert.rejects(stagePreparedSourceBundle({THREE,marker:f.marker,plan,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),stillWanted:()=>wanted,prepare:()=>{wanted=false;},upload:()=>{uploads++;}}),SourceLoadCancelled);assert.equal(uploads,0);assert.equal(ledger.held,0);
}));
