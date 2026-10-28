import test from 'node:test';import assert from 'node:assert/strict';
import {SourceWorkScheduler} from '../src/source_work_scheduler.js';
const flush=async()=>{for(let i=0;i<24;i++)await Promise.resolve();};
function fixture({enabled=true,max=4}={}){
 let now=0,runs=0,wanted=true;const tasks=[],timers=[],errors=[];
 const s=new SourceWorkScheduler({mode:'task',metadataContinuation:enabled,metadataMaxSteps:max,run:()=>{runs++;return false;},onError:e=>errors.push(e),clock:()=>now,taskScheduler:{wait:()=>new Promise((resolve,reject)=>tasks.push({resolve,reject})),snapshot:()=>({pending:tasks.length}),dispose(){tasks.splice(0).forEach(t=>t.reject(Error('disposed')));}},setTimer:(fn,ms)=>{const t={fn,ms};timers.push(t);return t;},clearTimer:t=>{timers.splice(timers.indexOf(t),1);}});
 return {s,tasks,timers,errors,get runs(){return runs;},set now(v){now=v;},get now(){return now;},set wanted(v){wanted=v;},request(){s.requestMetadataContinuation(()=>wanted);},async task(){await flush();assert.ok(tasks.length,'a browser task must yield before work');tasks.shift().resolve();await flush();},async timer(){assert.equal(timers.length,1);const t=timers.shift();now+=t.ms;t.fn();await flush();}};
}
test('cache-only completions can continue after a browser task with no interval timer',async()=>{
 const f=fixture();f.s.request();await f.task();f.now=1;f.request();await f.task();assert.equal(f.runs,2);assert.equal(f.timers.length,0);assert.equal(f.s.snapshot().metadataFastRuns,1);f.s.dispose();
});
test('four continuations are the maximum even when a fake clock never advances',async()=>{
 const f=fixture();f.s.request();await f.task();for(let i=0;i<4;i++){f.request();await f.task();}assert.equal(f.runs,5);f.request();await flush();assert.equal(f.tasks.length,0);assert.equal(f.timers.length,1);await f.timer();await f.task();assert.equal(f.s.snapshot().metadataFastRuns,4);assert.equal(f.s.snapshot().metadataFallbacks,1);f.s.dispose();
});
test('time expiring in the task queue restores ordinary pacing before work',async()=>{
 const f=fixture();f.s.request();await f.task();f.now=3.9;f.request();await flush();assert.equal(f.tasks.length,1);f.now=4;await f.task();assert.equal(f.runs,1);assert.equal(f.timers.length,1);await f.timer();await f.task();assert.equal(f.runs,2);assert.equal(f.s.snapshot().metadataFastRuns,0);f.s.dispose();
});
test('camera/cut guard invalidation while yielding cannot accelerate stale work',async()=>{
 const f=fixture();f.s.request();await f.task();f.now=1;f.request();await flush();f.wanted=false;await f.task();assert.equal(f.runs,1);await f.timer();await f.task();assert.equal(f.runs,2);assert.equal(f.s.snapshot().metadataFastRuns,0);f.s.dispose();
});
test('ordinary completion and disabled QA flag retain the interval floor',async()=>{
 for(const enabled of [true,false]){const f=fixture({enabled});f.s.request();await f.task();f.now=1;if(enabled)f.s.request();else f.request();await flush();assert.equal(f.tasks.length,0);await f.timer();await f.task();assert.equal(f.s.snapshot().metadataFastRuns,0);f.s.dispose();}
});
test('dispose during a queued metadata task releases it without another run',async()=>{
 const f=fixture();f.s.request();await f.task();f.now=1;f.request();await flush();f.s.dispose();await flush();assert.equal(f.runs,1);assert.equal(f.errors.length,0);assert.equal(f.s.snapshot().scheduled,false);f.request();assert.equal(f.tasks.length,0);
});
test('invalid or throwing metadata guards fail once and never spin',async()=>{
 const f=fixture();assert.throws(()=>f.s.requestMetadataContinuation(null),/guard/);f.s.request();await f.task();f.s.requestMetadataContinuation(()=>{throw Error('stale guard');});await flush();assert.equal(f.errors.length,1);assert.equal(f.s.snapshot().scheduled,false);assert.equal(f.tasks.length+f.timers.length,0);f.s.dispose();
 for(const options of [{metadataContinuation:1},{metadataSliceMs:4.1},{metadataSliceMs:0},{metadataMaxSteps:5},{metadataMaxSteps:0}])assert.throws(()=>new SourceWorkScheduler({run:()=>false,...options}),/Invalid/);
});

test('context guard CPU time is charged before authorizing another metadata step',async()=>{
 const f=fixture();f.s.request();await f.task();f.now=3.9;f.s.requestMetadataContinuation(()=>{f.now=4.1;return true;});await flush();assert.equal(f.tasks.length,0);assert.equal(f.timers.length,1);await f.timer();await f.task();assert.equal(f.s.snapshot().metadataFastRuns,0);f.s.dispose();
});
