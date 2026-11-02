import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {clientSourcePageFixture} from './fixtures/client_source_page.mjs';
import {planClientSourceCrop,validateClientSourceCropForPart} from '../src/source_client_crop.js';
import {planPreparedSourceBundle,stagePreparedSourceBundle,stageReplannedSourceBundle,sourceMetadataBudgetCost,SourcePagePlanChanged,sourcePageClientCrop,originalSourceBundle,subsetPreparedSourcePlan} from '../src/prepared_source_page.js';
import {SourcePageBudget} from '../src/source_page_budget.js';import {SourceFrontier,validateSourcePart} from '../src/source_frontier.js';import {sourceBundleIdentity} from '../src/source_residency.js';import {originalImageStats} from '../src/original_image.js';
async function withBitmapTransport(run,decode=null){
 const oldBitmap=globalThis.createImageBitmap,oldProgress=globalThis.ProgressEvent;let opened=0,closed=0;
 globalThis.createImageBitmap=decode??(async(...args)=>{const cropped=args.length===6;opened++;return {width:cropped?args[3]:16,height:cropped?args[4]:12,close(){closed++;}};});
 if(!globalThis.ProgressEvent)globalThis.ProgressEvent=class{constructor(type,values){this.type=type;Object.assign(this,values);}};
 try{return await run(()=>({opened,closed}));}finally{if(oldBitmap===undefined)delete globalThis.createImageBitmap;else globalThis.createImageBitmap=oldBitmap;if(oldProgress===undefined)delete globalThis.ProgressEvent;else globalThis.ProgressEvent=oldProgress;}
}
const renderer={capabilities:{maxTextureSize:8192}};
async function cropPlan(f){const crop=await planClientSourceCrop(f);return {crop,plan:await planPreparedSourceBundle({marker:f.marker,clientCrop:async()=>crop})};}
test('geometry-verified crop is costed before staging and actual GLTF page has the same admitted identity',()=>withBitmapTransport(async counts=>{
 const f=await clientSourcePageFixture(),before=structuredClone(f.marker),{crop,plan}=await cropPlan(f),ledger=new SourcePageBudget(600);assert.equal(plan.marker.gpu_payload_bytes,552);assert.equal(plan.marker.parts[0].runtime_texture.textureBytes,480);assert.equal(ledger.held,0);
 const staged=await stagePreparedSourceBundle({THREE,renderer,marker:f.marker,plan,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),upload:()=>{}});assert.equal(ledger.held,552);const part=staged.marker.parts[0],mesh=staged.meshes.get('part_000');validateSourcePart(part,mesh);assert.equal(sourcePageClientCrop(part.runtime_texture),crop);assert.equal(new SourceFrontier(staged.marker,staged.meshes).bytes,552);assert.deepEqual(originalSourceBundle(staged.marker),before);assert.equal(mesh.geometry.attributes.uv.array[0],new Float32Array(f.binary,36,6)[0]);assert.deepEqual([mesh.material.map.image.width,mesh.material.map.image.height],[12,10]);
 mesh.material.map.repeat.x++;assert.throws(()=>validateSourcePart(part,mesh),/transform/);mesh.material.map.repeat.x--;staged.dispose();staged.dispose();assert.equal(ledger.held,0);assert.deepEqual(counts(),{opened:1,closed:1});
}));
test('retired parent crop proof survives planning and restores the exact parent representation before rollback',()=>withBitmapTransport(async counts=>{
 const f=await clientSourcePageFixture(),{plan}=await cropPlan(f),ledger=new SourcePageBudget(1200);
 const load=(marker,plan)=>stagePreparedSourceBundle({THREE,renderer,marker,plan,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),upload:()=>{}});
 const root=await load(f.marker,plan),frontier=new SourceFrontier(root.marker,root.meshes),rootBundle=frontier.bundles.get('$root'),identity=root.marker.parts[0].runtime_texture;
 const childMarker={...structuredClone(f.marker),schema:'zhumadian.osgb_source_family.v2',replacement_parent:'parent',parent_source_sha256:'c'.repeat(64),complete_sibling_family:true,family_key:'d'.repeat(16),source_nodes:[{...structuredClone(f.marker.source_nodes[0]),name:'child',children:[],depth:1}]};
 const childPlan=await planPreparedSourceBundle({marker:childMarker,clientCrop:async()=>sourcePageClientCrop(identity)}),child=await load(childMarker,childPlan);const ticket=frontier.begin(child.marker,1200-frontier.bytes);frontier.markReady(ticket,0);assert.equal(frontier.commit(ticket,child.meshes),true);frontier.releaseHiddenPages();assert.equal(rootBundle.meshes.size,0);assert.equal(ledger.held,552);
 assert.equal(frontier.copyForPlanning().bundles.get('$root').marker.parts[0].runtime_texture,identity);const proof=sourcePageClientCrop(identity);assert.ok(proof);
 const restoredPlan=await planPreparedSourceBundle({marker:f.marker,clientCrop:async p=>validateClientSourceCropForPart(proof,p)});assert.equal(sourceBundleIdentity(restoredPlan.marker),sourceBundleIdentity(root.marker));const subset=subsetPreparedSourcePlan(restoredPlan,['part_000']);const restored=await load(subset.marker,subset.plan);assert.equal(ledger.held,1104);frontier.restorePages(rootBundle,restored.meshes);assert.equal(frontier.rollback('parent').length,1);child.dispose();frontier.applyMasks();assert.deepEqual([...frontier.visible],['parent']);assert.equal(frontier.bytes,552);restored.dispose();root.dispose();assert.equal(ledger.held,0);assert.deepEqual(counts(),{opened:3,closed:3});
}));
test('unsupported crop unwinds small leases and requires fresh full-image admission instead of spending the small ticket',()=>withBitmapTransport(async()=>{
 const f=await clientSourcePageFixture(),{plan}=await cropPlan(f),ledger=new SourcePageBudget(600);let cropCalls=0,uploads=0;
 const old=globalThis.createImageBitmap;globalThis.createImageBitmap=async()=>{cropCalls++;throw Error('crop overload unsupported');};
 const admitted=[];let cancelled=0,replanned=0;const result=await stageReplannedSourceBundle({THREE,renderer,marker:f.marker,clientCrop:async()=>planClientSourceCrop(f),loadFile:f.loadFile,reserve:r=>ledger.reserve(r),upload:()=>uploads++,admit:async marker=>{assert.equal(ledger.held,0);admitted.push(marker.gpu_payload_bytes);return marker.gpu_payload_bytes<=ledger.limit;},cancelAttempt:()=>{assert.equal(ledger.held,0);cancelled++;},onReplan:(error,part)=>{assert.equal(error.reason,'client_crop_unavailable');assert.equal(part,f.part);replanned++;}});
 assert.equal(result,null);assert.deepEqual(admitted,[552,840]);assert.equal(cancelled,1);assert.equal(replanned,1);assert.equal(ledger.held,0);assert.equal(uploads,0);assert.equal(cropCalls,1);
 const full=await planPreparedSourceBundle({marker:f.marker,forceRgbaParts:new Set(['part_000']),clientCrop:()=>{throw Error('forced full page must skip crop');}});assert.equal(full.marker.gpu_payload_bytes,840);assert.ok(full.marker.gpu_payload_bytes>ledger.limit);assert.equal(full.marker.parts[0].runtime_texture.clientCropContract,undefined);globalThis.createImageBitmap=old;
 const fullLedger=new SourcePageBudget(900),staged=await stagePreparedSourceBundle({THREE,renderer,marker:f.marker,plan:full,loadFile:f.loadFile,reserve:r=>fullLedger.reserve(r),upload:()=>uploads++});assert.equal(fullLedger.held,840);assert.equal(uploads,1);staged.dispose();assert.equal(fullLedger.held,0);
}));
test('proof and PNG identity cannot be cloned or substituted to obtain a smaller plan',async()=>{
 const f=await clientSourcePageFixture(),{crop}=await cropPlan(f);await assert.rejects(planPreparedSourceBundle({marker:f.marker,clientCrop:async()=>structuredClone(crop)}),/Unverified/);const altered=structuredClone(f.marker);altered.parts[0].files.find(x=>x.name==='texture.png').sha256='f'.repeat(64);await assert.rejects(planPreparedSourceBundle({marker:altered,clientCrop:async()=>crop}),/source identity differs/);
});
test('camera cancellation during crop planning or preparation releases reservations and preserves the live object',()=>withBitmapTransport(async()=>{
 const f=await clientSourcePageFixture();let wanted=true;await assert.rejects(planPreparedSourceBundle({marker:f.marker,stillWanted:()=>wanted,clientCrop:async()=>{const crop=await planClientSourceCrop(f);wanted=false;return crop;}}),/no longer wanted/);
 wanted=true;const {plan}=await cropPlan(f),ledger=new SourcePageBudget(600),before=originalImageStats().owned;let uploads=0;await assert.rejects(stagePreparedSourceBundle({THREE,renderer,marker:f.marker,plan,loadFile:f.loadFile,reserve:r=>ledger.reserve(r),prepare:()=>{wanted=false;},stillWanted:()=>wanted,upload:()=>uploads++}));assert.equal(uploads,0);assert.equal(ledger.held,0);assert.equal(originalImageStats().owned,before);
}));

test('metadata preserves unknown crop cost without accepting invalid descriptors or using original size as crop cost',async()=>{
 const f=await clientSourcePageFixture();assert.equal(await sourceMetadataBudgetCost({marker:f.marker,clientCropEnabled:true}),null);assert.equal(await sourceMetadataBudgetCost({marker:f.marker,clientCropEnabled:false}),840);
 const nearest=structuredClone(f.marker);nearest.parts[0].source_image.sampler.minFilter=9728;nearest.parts[0].source_image.sampler.magFilter=9728;assert.equal(await sourceMetadataBudgetCost({marker:nearest,clientCropEnabled:true}),840);
 const bad=structuredClone(f.marker);bad.gpu_payload_bytes++;await assert.rejects(sourceMetadataBudgetCost({marker:bad,clientCropEnabled:true}),/original cost/);
});
