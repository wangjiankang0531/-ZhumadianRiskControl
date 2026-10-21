import test from 'node:test';
import assert from 'node:assert/strict';
import {SourceAllocationScan,chooseFeasibleSourceCandidate} from '../src/source_allocation.js';
import {sameAllocationBudgetState} from '../src/source_allocation_memo.js';
const candidates=n=>Array.from({length:n},(_,i)=>({key:`family/${i}`,id:i+1,kind:'family',score:n-i,cost:1}));

test('cooperative slices visit every failed candidate exactly once and continue to the last winner',()=>{
 const list=candidates(501),visited=[];let time=0;
 const scan=new SourceAllocationScan(list,{feasible:c=>{visited.push(c.key);time+=3;return c===list.at(-1);}});
 let result=scan.step({budgetMs:4,clock:()=>time});assert.equal(result.done,false);assert.equal(result.probes,2);assert.equal(result.yields,1);
 while(!result.done)result=scan.step({budgetMs:4,clock:()=>time});
 assert.equal(result.candidate,list.at(-1));assert.equal(result.probes,501);assert.equal(result.slices,251);assert.equal(result.yields,250);assert.deepEqual(visited,list.map(c=>c.key));
 scan.step({clock:()=>{throw Error('terminal cursor must not touch clock');}});assert.equal(visited.length,501);
});

test('5000 random complete priority orders and time partitions preserve the synchronous exact winner and probe prefix',()=>{
 let seed=1231023;const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
 for(let trial=0;trial<5000;trial++){
  const list=Array.from({length:Math.floor(random()*120)},(_,i)=>({key:`candidate/${i}`,id:i+1,kind:random()<.5?'root':'family',score:Math.floor(random()*10),cost:random()<.1?null:1+Math.floor(random()*8)})),truth=new Map(list.map(c=>[c,random()<.07])),resident=new Set(list.filter(()=>random()<.5).map(c=>c.id)),indexed=trial%2===0,hasRoot=id=>resident.has(id),expectedProbes=[];
  const expected=chooseFeasibleSourceCandidate(list,{indexed,hasRoot,feasible:c=>{expectedProbes.push(c);return truth.get(c);}});
  let time=0;const actualProbes=[],scan=new SourceAllocationScan(list,{indexed,hasRoot,feasible:c=>{actualProbes.push(c);time+=1+random()*12;return truth.get(c);}});let result;
  do{result=scan.step({budgetMs:.1+random()*9,clock:()=>time});}while(!result.done);
  assert.equal(result.candidate,expected);assert.deepEqual(actualProbes,expectedProbes);assert.ok(result.slices<=Math.max(1,list.length));
 }
});

test('changed state cancels before another probe and never publishes a stale winner',()=>{
 const list=candidates(20);let current=true,time=0,probes=0;const scan=new SourceAllocationScan(list,{feasible:()=>{probes++;time+=8;return false;}});
 assert.equal(scan.step({clock:()=>time,isCurrent:()=>current}).done,false);current=false;
 const result=scan.step({clock:()=>{throw Error('invalid state must not read clock');},isCurrent:()=>current});assert.equal(result.cancelled,true);assert.equal(result.candidate,null);assert.equal(probes,1);
 const winner=new SourceAllocationScan(list,{feasible:()=>true});assert.equal(winner.step().candidate,list[0]);assert.equal(winner.step({isCurrent:()=>false}).candidate,null);
});

test('one indivisible slow probe yields before its successor instead of hiding a candidate cap',()=>{
 const list=candidates(3),visited=[];let time=0;const scan=new SourceAllocationScan(list,{feasible:c=>{visited.push(c);time+=19;return false;}});
 assert.equal(scan.step({clock:()=>time}).cursor,1);assert.equal(scan.step({clock:()=>time}).cursor,2);const end=scan.step({clock:()=>time});assert.equal(end.done,true);assert.equal(end.candidate,null);assert.deepEqual(visited,list);
});

test('unknown metadata needs no budget probe and empty or zero-gain scans finish normally',()=>{
 const unknown={key:'metadata',id:100,kind:'family',score:.01,cost:null},scan=new SourceAllocationScan([...candidates(5),unknown],{feasible:()=>{throw Error('must not pre-probe known lower priority');}});assert.equal(scan.step().candidate,unknown);assert.equal(scan.probes,0);
 for(const list of [[],[{key:'zero',score:0,cost:null}]]){const empty=new SourceAllocationScan(list,{feasible:()=>true});assert.equal(empty.step().done,true);assert.equal(empty.probes,0);}
});

test('invalid candidates, clocks, slice limits and asynchronous or throwing probes fail closed',()=>{
 assert.throws(()=>new SourceAllocationScan([{key:'a',score:1,cost:0}],{feasible:()=>true}));
 for(const feasible of [()=>Promise.resolve(true),()=>{throw Error('probe');},()=>null]){const scan=new SourceAllocationScan(candidates(1),{feasible});assert.throws(()=>scan.step());assert.equal(scan.cancelled,true);assert.equal(scan.candidate,null);}
 for(const budgetMs of [0,-1,Infinity,NaN])assert.throws(()=>new SourceAllocationScan([],{feasible:()=>true}).step({budgetMs}));
 assert.throws(()=>new SourceAllocationScan([],{feasible:()=>true}).step({clock:()=>NaN}));
});

test('scan state equality requires exact serialized inputs and visibility/frontier identities without bounded-cache dependence',()=>{
 const visibility={},f={},state={visibility,frontiers:[f],state:'exact'};assert.equal(sameAllocationBudgetState(state,{...state,frontiers:[f]}),true);
 for(const other of [null,{...state,state:'changed'},{...state,visibility:{}},{...state,frontiers:[{}]},{...state,frontiers:[]}])assert.equal(sameAllocationBudgetState(state,other),false);
 assert.equal(sameAllocationBudgetState(null,null),false);const large={...state,state:'x'.repeat(1100000)};assert.equal(sameAllocationBudgetState(large,{...large}),true);
});
