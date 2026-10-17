import test from 'node:test';
import assert from 'node:assert/strict';
import {stageSourceParts,SourceLoadCancelled} from '../src/lod_transaction.js';
import {LeasedDownloads} from '../src/lod_downloads.js';

const token='a'.repeat(32);
function setup(count=3){
 const parts=Array.from({length:count},(_,i)=>({directory:`part_${String(i).padStart(3,'0')}`,gpu_payload_bytes:1024})),loaded=[],disposed=[],ready=[],uploaded=[],scenes=[];
 const state={wanted:true,loaded,disposed,ready,uploaded,scenes};
 const options={marker:{parts,gpu_payload_bytes:count*1024},downloads:{load:async url=>{loaded.push(url);return {scene:{url}};}},urlForPart:p=>p.directory,group:{add:scene=>scenes.push(scene)},prepare:()=>{},upload:model=>uploaded.push(model.scene.url),stillWanted:()=>state.wanted,dispose:scene=>disposed.push(scene.url),onReady:i=>ready.push(i),yieldFrame:async()=>{}};
 return {state,options};
}

test('wanted source parts stage in order and ownership transfers only after upload',async()=>{
 const {state,options}=setup();await stageSourceParts(options);
 assert.deepEqual(state.loaded,['part_000','part_001','part_002']);assert.deepEqual(state.uploaded,state.loaded);assert.deepEqual(state.ready,[0,1,2]);assert.equal(state.scenes.length,3);assert.deepEqual(state.disposed,[]);
});

test('a stale request does not issue its first part request',async()=>{
 const {state,options}=setup();state.wanted=false;await assert.rejects(()=>stageSourceParts(options),SourceLoadCancelled);assert.deepEqual(state.loaded,[]);assert.deepEqual(state.scenes,[]);
});

test('camera movement while a part is in flight disposes the late model and never fetches the next part',async()=>{
 const {state,options}=setup();let complete,started;
 const began=new Promise(resolve=>{started=resolve;});
 options.downloads.load=url=>{state.loaded.push(url);started();return new Promise(resolve=>{complete=resolve;});};
 const task=stageSourceParts(options);await began;state.wanted=false;complete({scene:{url:'late-part'}});
 await assert.rejects(task,SourceLoadCancelled);assert.deepEqual(state.loaded,['part_000']);assert.deepEqual(state.disposed,['late-part']);assert.deepEqual(state.uploaded,[]);assert.deepEqual(state.scenes,[]);assert.deepEqual(state.ready,[]);
});

test('disabling detail between frames stops later parts and lets owner clean staged parts once',async()=>{
 const {state,options}=setup();options.yieldFrame=async()=>{state.wanted=false;};
 let releases=0;const lease=new LeasedDownloads(token,'http://127.0.0.1:8767/',async()=>{releases++;return {ok:true};});
 try{await assert.rejects(()=>stageSourceParts(options),SourceLoadCancelled);}finally{for(const scene of state.scenes)options.dispose(scene);await lease.release();}
 assert.deepEqual(state.loaded,['part_000']);assert.deepEqual(state.ready,[0]);assert.deepEqual(state.disposed,['part_000']);assert.equal(releases,1);
});

test('cancellation on the final frame still rejects the transaction before caller commit',async()=>{
 const {state,options}=setup(1);options.yieldFrame=async()=>{state.wanted=false;};await assert.rejects(()=>stageSourceParts(options),SourceLoadCancelled);assert.equal(state.scenes.length,1);
});

test('prepare and upload failures dispose unowned models exactly once and stop reads',async()=>{
 for(const phase of ['prepare','upload']){
  const {state,options}=setup();options[phase]=()=>{throw Error('upload failure');};
  await assert.rejects(()=>stageSourceParts(options),/upload failure/);assert.deepEqual(state.disposed,['part_000']);assert.deepEqual(state.loaded,['part_000']);assert.deepEqual(state.scenes,[]);
 }
});

test('a cancellation during preparation never uploads or attaches the model',async()=>{
 const {state,options}=setup();options.prepare=()=>{state.wanted=false;};await assert.rejects(()=>stageSourceParts(options),SourceLoadCancelled);assert.deepEqual(state.disposed,['part_000']);assert.deepEqual(state.uploaded,[]);assert.deepEqual(state.ready,[]);
});

test('malformed or mismatched part payloads fail before network or GPU work',async()=>{
 for(const mutate of [m=>m.parts[1].directory=m.parts[0].directory,m=>m.parts[1].gpu_payload_bytes=NaN,m=>m.parts[1].gpu_payload_bytes=33*1048576,m=>m.gpu_payload_bytes++,m=>m.parts=[]]){
  const {state,options}=setup();mutate(options.marker);await assert.rejects(()=>stageSourceParts(options),/资源账目/);assert.deepEqual(state.loaded,[]);assert.deepEqual(state.uploaded,[]);
 }
});
