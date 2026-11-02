import test from 'node:test';import assert from 'node:assert/strict';
import {SourceWorkScheduler} from '../src/source_work_scheduler.js';
import {stageSourceParts,SourceLoadCancelled} from '../src/lod_transaction.js';
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
function fixture(run,mode='task'){
 const callbacks=[],timers=new Map();let now=0,next=0,disposed=0;
 const tasks={wait:()=>new Promise((resolve,reject)=>callbacks.push({resolve,reject})),dispose(){disposed++;callbacks.splice(0).forEach(x=>x.reject(Error('closed')));},snapshot:()=>({pending:callbacks.length})};
 const errors=[],s=new SourceWorkScheduler({mode,run,onError:e=>errors.push(e),clock:()=>now,intervalMs:32,taskScheduler:tasks,setTimer:(f,ms)=>{const id=++next;timers.set(id,{f,ms});return id;},clearTimer:id=>timers.delete(id)});
 return {s,callbacks,timers,errors,get disposed(){return disposed;},async task(){assert.ok(callbacks.length);callbacks.shift().resolve();await flush();},async timer(){assert.equal(timers.size,1);const [id,t]=[...timers][0];now+=t.ms;timers.delete(id);t.f();await flush();}};
}
test('source work coalesces notifications and advances scan slices without animation frames',async()=>{
 let runs=0;const f=fixture(()=>++runs<3);for(let i=0;i<100;i++)f.s.request();assert.equal(f.callbacks.length,1);await f.task();assert.equal(runs,1);assert.equal(f.timers.size,1);for(let i=0;i<20;i++)f.s.request();await f.timer();assert.equal(f.callbacks.length,1);await f.task();await f.timer();await f.task();assert.equal(runs,3);assert.equal(f.callbacks.length,0);assert.equal(f.s.snapshot().scheduled,false);assert.equal(f.s.snapshot().runs,3);f.s.dispose();
});
test('dispose cancels a rate-limit timer and no late task can restart source work',async()=>{
 let runs=0;const f=fixture(()=>{runs++;return true;});f.s.request();await f.task();assert.equal(f.timers.size,1);f.s.dispose();await flush();assert.equal(f.timers.size,0);assert.equal(f.s.snapshot().scheduled,false);assert.equal(runs,1);f.s.request();assert.equal(f.callbacks.length,0);assert.equal(f.disposed,1);await assert.rejects(f.s.yield(),/closed/);
});
test('a thrown source scan is observed once and does not create a retry loop',async()=>{
 const f=fixture(()=>{throw Error('probe failed');});f.s.request();await f.task();assert.equal(f.errors.length,1);assert.equal(f.timers.size,0);assert.equal(f.s.snapshot().errors,1);f.s.dispose();assert.throws(()=>new SourceWorkScheduler({run:()=>false,intervalMs:0}),/Invalid/);
});
test('frame control retains page yields but never creates a work pump',async()=>{
 let runs=0;const f=fixture(()=>{runs++;return false;},'frame');f.s.request();assert.equal(f.callbacks.length,0);const pending=f.s.yield();await f.task();await pending;assert.equal(runs,0);assert.equal(f.s.snapshot().pageYields,1);f.s.dispose();
});
test('task page preparation preserves ordered attachment and never commits after cancellation',async()=>{
 const f=fixture(()=>false),parts=[0,1].map(i=>({directory:'part_00'+i,gpu_payload_bytes:16})),marker={parts,gpu_payload_bytes:32},attached=[],disposed=[];let wanted=true;
 const staging=stageSourceParts({marker,downloads:{load:async name=>({scene:name})},urlForPart:p=>p.directory,group:{add:n=>attached.push(n)},prepare:()=>{},upload:async()=>{},stillWanted:()=>wanted,dispose:n=>disposed.push(n),yieldFrame:()=>f.s.yield()});
 const result=assert.rejects(staging,SourceLoadCancelled);await flush();assert.deepEqual(attached,['part_000']);wanted=false;await f.task();await result;assert.deepEqual(attached,['part_000']);assert.deepEqual(disposed,[]);f.s.dispose();
});
test('browser default timers retain their global receiver when rate limiting and disposing',async()=>{
 const oldSet=globalThis.setTimeout,oldClear=globalThis.clearTimeout;let captured,cleared=0,runs=0;const callbacks=[];
 try{
  globalThis.setTimeout=function(f){assert.equal(this,globalThis);captured=f;return 77;};globalThis.clearTimeout=function(id){assert.equal(this,globalThis);assert.equal(id,77);cleared++;};
  const s=new SourceWorkScheduler({mode:'task',run:()=>++runs===1,clock:()=>0,taskScheduler:{wait:()=>new Promise(resolve=>callbacks.push(resolve)),snapshot:()=>({}),dispose(){}}});
  s.request();callbacks.shift()();await flush();assert.equal(typeof captured,'function');assert.equal(runs,1);s.dispose();await flush();assert.equal(cleared,1);assert.equal(s.snapshot().scheduled,false);
 }finally{globalThis.setTimeout=oldSet;globalThis.clearTimeout=oldClear;}
});
