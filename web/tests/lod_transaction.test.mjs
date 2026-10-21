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

const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function windowSetup(count=4){
 const {state,options}=setup(count),requests=[];options.loadConcurrency=2;
 options.downloads.load=(url,wanted)=>{const d=deferred();requests.push({url,wanted,...d});state.loaded.push(url);return d.promise;};
 const resolve=i=>requests[i].resolve({scene:{url:requests[i].url}});
 return {state,options,requests,resolve};
}
test('two preparation slots overlap out of order reads but upload and attach in source order',async()=>{
 const {state,options,requests,resolve}=windowSetup();const task=stageSourceParts(options);await tick();assert.equal(requests.length,2);
 resolve(1);await tick();assert.deepEqual(state.uploaded,[]);assert.equal(requests.length,2);
 resolve(0);await tick();assert.deepEqual(state.uploaded,['part_000','part_001']);assert.equal(requests.length,4);
 resolve(3);await tick();assert.equal(state.uploaded.length,2);resolve(2);await task;
 assert.deepEqual(state.uploaded,state.loaded);assert.deepEqual(state.ready,[0,1,2,3]);assert.deepEqual(state.disposed,[]);
});
test('the next two-page window is filled only after upload transfers the current model',async()=>{
 const {state,options,requests,resolve}=windowSetup();const hold=deferred();options.upload=async model=>{state.uploaded.push(model.scene.url);if(model.scene.url==='part_000')await hold.promise;};
 const task=stageSourceParts(options);await tick();resolve(0);resolve(1);await tick();assert.equal(requests.length,2);assert.equal(state.scenes.length,0);
 state.wanted=false;hold.resolve();await assert.rejects(task,SourceLoadCancelled);assert.equal(requests.length,2);assert.deepEqual(state.disposed,['part_000','part_001']);assert.equal(state.scenes.length,0);
});
test('a failed prefetched page aborts the batch and drains the earlier in-flight page before rejecting',async()=>{
 const {state,options,requests,resolve}=windowSetup();let settled=false;const failure=Error('prefetch failed');const task=stageSourceParts(options);const checked=assert.rejects(task,error=>error===failure).then(()=>{settled=true;});
 await tick();requests[1].reject(failure);await tick();assert.equal(settled,false);assert.equal(requests[0].wanted(),false);
 resolve(0);await checked;assert.equal(requests.length,2);assert.deepEqual(state.disposed,['part_000']);assert.deepEqual(state.uploaded,[]);
});
test('upload failure drains and disposes the late prefetched model once while preserving the original error',async()=>{
 const {state,options,requests,resolve}=windowSetup();const failure=Error('GPU upload failed');options.upload=()=>{throw failure;};let settled=false;
 const task=stageSourceParts(options);const checked=assert.rejects(task,error=>error===failure).then(()=>{settled=true;});await tick();resolve(0);await tick();assert.equal(settled,false);assert.equal(requests[1].wanted(),false);
 resolve(1);await checked;assert.deepEqual(state.disposed,['part_000','part_001']);assert.equal(state.scenes.length,0);assert.equal(requests.length,2);
});
test('camera cancellation drains both reads without attachment or further requests',async()=>{
 const {state,options,requests,resolve}=windowSetup();const task=stageSourceParts(options);const checked=assert.rejects(task,SourceLoadCancelled);await tick();state.wanted=false;resolve(1);await tick();assert.equal(requests[0].wanted(),false);resolve(0);await checked;
 assert.deepEqual(state.disposed,['part_000','part_001']);assert.deepEqual(state.ready,[]);assert.equal(requests.length,2);
});
test('failure after attachment leaves transferred pages to the group owner and disposes speculative pages once',async()=>{
 const {state,options,requests,resolve}=windowSetup();options.yieldFrame=async()=>{state.wanted=false;};const task=stageSourceParts(options);const checked=assert.rejects(task,SourceLoadCancelled);await tick();resolve(0);resolve(1);await tick();
 // Page 2 can have been requested before the yield invalidates demand.
 for(let i=2;i<requests.length;i++)resolve(i);await checked;
 for(const scene of state.scenes)options.dispose(scene);
 assert.equal(state.scenes.length,1);assert.deepEqual([...state.disposed].sort(),[...state.loaded].sort());assert.equal(new Set(state.disposed).size,state.disposed.length);
});
test('cleanup keeps draining all prepared models when one disposer throws',async()=>{
 const {state,options,requests,resolve}=windowSetup();const failure=Error('prepare failed');options.prepare=()=>{throw failure;};options.dispose=scene=>{state.disposed.push(scene.url);if(scene.url==='part_000')throw Error('cleanup failed');};
 const task=stageSourceParts(options);const checked=assert.rejects(task,e=>e===failure);await tick();resolve(0);resolve(1);await checked;assert.deepEqual(state.disposed,['part_000','part_001']);
});
test('invalid preparation concurrency rejects before IO while one remains the default',async()=>{
 for(const value of [0,3,1.5,'2',null]){const {state,options}=setup();options.loadConcurrency=value;await assert.rejects(stageSourceParts(options),/concurrency/);assert.deepEqual(state.loaded,[]);}
});
