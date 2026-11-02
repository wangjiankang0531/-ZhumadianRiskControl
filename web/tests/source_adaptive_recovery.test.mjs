import test from 'node:test';import assert from 'node:assert/strict';
import {observedSourceRecoveryHeadroom} from '../src/source_adaptive_recovery.js';
import {sourceRecoveryAdmissionCost,SOURCE_RECOVERY_HEADROOM} from '../src/source_recovery_headroom.js';
import {SourceFrontier,planSourceBudget} from '../src/source_frontier.js';
import {sourceRestorationFootprint} from '../src/source_page_budget.js';
const M=1048576;
const bundle=(sizes,loaded=true)=>({marker:{gpu_payload_bytes:sizes.reduce((s,n)=>s+n,0),parts:sizes.map((bytes,i)=>({directory:'part_'+String(i).padStart(3,'0'),gpu_payload_bytes:bytes})),source_nodes:[{name:'P',spans:sizes.map((_,i)=>({part:'part_'+String(i).padStart(3,'0')})),children:[]}]},meshes:new Map(loaded?sizes.map((_,i)=>['part_'+String(i).padStart(3,'0'),{}]):[])});
const ready=(root,children=null)=>({frontier:Object.assign(Object.create(SourceFrontier.prototype),{bundles:new Map([['$root',root],...(children?[['P',children]]:[])]),visible:new Set(children?['C']:['P']),cutVersion:1})});
test('observed reserve admits a useful small complete root refused solely by a fixed 64MiB spare',()=>{
 const s=new Map([1,2,3].map(id=>[id,ready(bundle([30*M]))])),request={id:4,parent:null,score:0.0001},cost=8*M,limit=150*M;
 assert.equal(planSourceBudget(s,request,sourceRecoveryAdmissionCost(cost,SOURCE_RECOVERY_HEADROOM),limit,()=>Infinity),null);
 const spare=observedSourceRecoveryHeadroom({residents:s,incomingCost:cost});assert.equal(spare,30*M);
 assert.deepEqual(planSourceBudget(s,request,sourceRecoveryAdmissionCost(cost,spare),limit,()=>Infinity),[]);
 assert.ok(90*M+cost+spare<=limit);assert.equal(s.size,3);
});
test('hidden complete parent bytes remain reserved even after all their meshes are released',()=>{
 const parent=bundle([20*M,18*M],false),child=bundle([4*M]);child.marker.source_nodes=[{name:'C',spans:[{part:'part_000'}],children:[]}];parent.marker.source_nodes[0].children=['C'];
 const s=new Map([[1,ready(parent,child)]]);assert.equal(observedSourceRecoveryHeadroom({residents:s,incomingCost:1}),38*M);
 const restore=sourceRestorationFootprint(s,[{root:1,parent:'P'}])-s.get(1).frontier.bytes;assert.equal(restore,38*M);
});
test('incoming complete bundle is included before it can retire its own future parent pages',()=>{assert.equal(observedSourceRecoveryHeadroom({residents:new Map([[1,ready(bundle([4*M]))]]),incomingCost:20*M}),20*M);});
test('a spare larger than 64MiB stays larger instead of silently truncating protection',()=>{assert.equal(observedSourceRecoveryHeadroom({residents:new Map([[1,ready(bundle([32*M,32*M,4*M]))]])}),68*M);});
test('sum of physical pages is checked against the complete immutable byte declaration',()=>{
 for(const change of [b=>b.marker.gpu_payload_bytes++,b=>delete b.marker.gpu_payload_bytes,b=>b.marker.parts[0].gpu_payload_bytes=NaN,b=>b.marker.parts[0].gpu_payload_bytes=33*M,b=>b.marker.parts.push({...b.marker.parts[0]})]){const b=bundle([1]);change(b);assert.throws(()=>observedSourceRecoveryHeadroom({residents:new Map([[1,ready(b)]])}));}
});
test('missing, empty, over-bound and invalid graphs fail closed rather than claim zero cost',()=>{
 for(const residents of [null,new Map([[1,{}]]),new Map([[1,{frontier:{bundles:new Map()}}]]),new Map([[1,ready(bundle([]))]])])assert.throws(()=>observedSourceRecoveryHeadroom({residents}));
 for(const incomingCost of [-1,NaN,Infinity,0.5])assert.throws(()=>observedSourceRecoveryHeadroom({residents:new Map(),incomingCost}));
 assert.equal(observedSourceRecoveryHeadroom({residents:new Map()}),0);
});
test('observed metadata inspection leaves live mesh maps and byte declarations unchanged',()=>{const b=bundle([3,5]),s=new Map([[1,ready(b)]]),before=JSON.stringify(b.marker),meshes=[...b.meshes];observedSourceRecoveryHeadroom({residents:s,incomingCost:10});assert.equal(JSON.stringify(b.marker),before);assert.deepEqual([...b.meshes],meshes);});
test('hard budget and strict quality margin still refuse an infeasible incoming bundle',()=>{
 const s=new Map([[1,ready(bundle([30*M]))]]),cost=65*M,headroom=observedSourceRecoveryHeadroom({residents:s,incomingCost:cost});assert.equal(planSourceBudget(s,{id:2,parent:null,score:1},sourceRecoveryAdmissionCost(cost,headroom),100*M,()=>0),null);
});
