import test from 'node:test';
import assert from 'node:assert/strict';
import {SourcePlanLookahead} from '../src/source_plan_lookahead.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('disabled lookahead performs no speculative work',async()=>{
 const q=new SourcePlanLookahead();assert.equal(q.start({key:'a',read:()=>{throw Error('must not read');},stillWanted:()=>true}),false);assert.equal(await q.take('a',()=>true),null);assert.equal(q.snapshot().started,0);
});
test('one pending plan is shared with its matching foreground consumer',async()=>{
 const q=new SourcePlanLookahead({enabled:true}),d=deferred(),plan=Object.freeze({marker:'verified'});let reads=0;
 assert.equal(q.start({key:'root/1/viewA',read:()=>{reads++;return d.promise;},stillWanted:()=>true}),true);assert.equal(q.start({key:'root/2/viewA',read:()=>{reads++;},stillWanted:()=>true}),false);
 const taken=q.take('root/1/viewA',()=>true);await tick();assert.equal(reads,1);assert.equal(q.snapshot().claimed,true);assert.equal(await q.take('root/1/viewA',()=>true),null);d.resolve(plan);assert.equal((await taken).plan,plan);assert.equal(q.snapshot().taken,1);assert.equal(q.snapshot().pending,false);
});
test('a different camera or request cannot consume a prefetched plan',async()=>{
 const q=new SourcePlanLookahead({enabled:true}),d=deferred();q.start({key:'root/1/viewA',read:()=>d.promise,stillWanted:()=>true});assert.equal(await q.take('root/1/viewB',()=>true),null);assert.equal(q.snapshot().taken,0);d.resolve({marker:'A'});await tick();assert.equal(q.snapshot().ready,true);assert.equal((await q.take('root/1/viewA',()=>true)).plan.marker,'A');
});
test('camera cancellation retains the single slot until the late read settles',async()=>{
 const q=new SourcePlanLookahead({enabled:true}),d=deferred();let wanted=true,readWanted;
 q.start({key:'a',read:w=>{readWanted=w;return d.promise;},stillWanted:()=>wanted});await tick();wanted=false;q.refresh();assert.equal(readWanted(),false);assert.equal(q.snapshot().cancelledPending,true);assert.equal(q.start({key:'b',read:async()=>({}),stillWanted:()=>true}),false);d.resolve({});await tick();assert.equal(q.snapshot().pending,false);assert.equal(q.snapshot().key,null);assert.equal(q.start({key:'b',read:async()=>({}),stillWanted:()=>true}),true);await q.cancel();assert.equal(q.snapshot().pending,false);
});
test('a failed prefetch is handled immediately and the foreground sees the original error once',async()=>{
 const q=new SourcePlanLookahead({enabled:true}),failure=Error('HTTP failed');q.start({key:'a',read:async()=>{throw failure;},stillWanted:()=>true});await tick();assert.equal(q.snapshot().failed,1);await assert.rejects(q.take('a',()=>true),e=>e===failure);assert.equal(await q.take('a',()=>true),null);
});
test('a foreground camera change while awaiting a plan cannot adopt its late result',async()=>{
 const q=new SourcePlanLookahead({enabled:true}),d=deferred();let foreground=true;q.start({key:'a',read:()=>d.promise,stillWanted:()=>true});const taken=q.take('a',()=>foreground),checked=assert.rejects(taken,SourceLoadCancelled);await tick();foreground=false;d.resolve({});await checked;assert.equal(q.snapshot().taken,0);assert.equal(q.snapshot().key,null);
});
test('a completed unused plan can be replaced without overlapping metadata work',async()=>{
 const q=new SourcePlanLookahead({enabled:true});q.start({key:'a',read:async()=>({value:'A'}),stillWanted:()=>true});await tick();assert.equal(q.start({key:'b',read:async()=>({value:'B'}),stillWanted:()=>true}),true);assert.equal(q.snapshot().discarded,1);assert.equal((await q.take('b',()=>true)).plan.value,'B');assert.equal(q.snapshot().started,2);
});
