import test from 'node:test';
import assert from 'node:assert/strict';
import {SourceFrontier,planSourceBudget} from '../src/source_frontier.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
import {planSourceRecoverySequence,applySourceRecoverySequence,sourceRecoverySnapshot} from '../src/source_recovery_plan.js';

// Metadata units only: P=10, its two children A/B=6 each, A's G/H=6 each.
// Live G/H/B=18. Under limit24, restoring P needs28 and is impossible in one
// upload, but A can recover at24, then P at22; final P plus incoming13 is23.
function fixture(){
 const node=(name,children,depth,part)=>({name,children,depth,spans:[{part,first:0,count:3}]}),page=(directory,gpu_payload_bytes)=>({directory,gpu_payload_bytes});
 const bundles=new Map([
  ['$root',{marker:{source_nodes:[node('P',['A','B'],0,'p')],parts:[page('p',10)]},meshes:new Map()}],
  ['P',{marker:{source_nodes:[node('A',['G','H'],1,'a'),node('B',[],1,'b')],parts:[page('a',6),page('b',6)]},meshes:new Map([['b',{}]])}],
  ['A',{marker:{source_nodes:[node('G',[],2,'g'),node('H',[],2,'h')],parts:[page('g',6),page('h',6)]},meshes:new Map([['g',{}],['h',{}]])}],
 ]);
 const frontier=Object.assign(Object.create(SourceFrontier.prototype),{bundles,visible:new Set(['G','H','B']),cutVersion:7,sequence:0,pending:null});
 return new Map([[1,{frontier}]]);
}
const request={id:2,parent:'incoming',score:100},priority=(root,node)=>node.name==='A'?1:2;

test('a verified smaller parent unlocks an otherwise impossible complete ancestor recovery',()=>{
 const states=fixture(),before=sourceRecoverySnapshot(states),maps=[...states.get(1).frontier.bundles.values()].map(b=>[...b.meshes]);
 assert.equal(planSourceBudget(states,request,13,24,priority),null);
 const sequence=planSourceRecoverySequence(states,request,13,24,priority);
 assert.deepEqual(sequence.targets,[{root:1,parent:'P'}]);assert.deepEqual(sequence.steps.map(s=>[s.parent,s.uploadPeakBytes]),[['A',24],['P',22]]);assert.equal(sequence.finalBytes,10);assert.equal(sequence.peakBytes,24);
 assert.equal(sourceRecoverySnapshot(states),before);assert.deepEqual([...states.get(1).frontier.bundles.values()].map(b=>[...b.meshes]),maps);
});
test('no partial plan is admitted when no first recovery page fits',()=>{
 const states=fixture(),before=sourceRecoverySnapshot(states);assert.equal(planSourceRecoverySequence(states,request,13,23,priority),null);assert.equal(sourceRecoverySnapshot(states),before);
});
test('later ancestor scoring retains original descendant pixel coverage after a simulated child retirement',()=>{
 const sequence=planSourceRecoverySequence(fixture(),request,13,24,(root,node,names)=>{if(node.name==='P'){assert.ok(names.has('G'));assert.ok(names.has('H'));}return priority(root,node);});
 assert.equal(sequence.steps.length,2);assert.deepEqual(sequence.steps.map(s=>s.estimatedTotalLoss),[1,2]);
});
test('a feasible bridge outside the cheapest final target can unlock the complete candidate',()=>{
 const states=fixture(),f=states.get(1).frontier;f.bundles.get('P').marker.parts[0].gpu_payload_bytes=8;
 const other=Object.assign(Object.create(SourceFrontier.prototype),{bundles:new Map([['$root',{marker:{source_nodes:[{name:'Q',children:['leaf'],depth:0,spans:[{part:'q'}]}],parts:[{directory:'q',gpu_payload_bytes:1}]},meshes:new Map()}],['Q',{marker:{source_nodes:[{name:'leaf',children:[],depth:1,spans:[{part:'l'}]}],parts:[{directory:'l',gpu_payload_bytes:6}]},meshes:new Map([['l',{}]])}]]),visible:new Set(['leaf']),cutVersion:0,pending:null});states.set(2,{frontier:other});
 const benefit=(root,node)=>root===2?3:priority(root,node),incoming={id:3,parent:'incoming',score:100};
 assert.deepEqual(planSourceBudget(states,incoming,11,27,benefit,null,{checkRestorePeak:false}),[{root:1,parent:'P'}]);
 const sequence=planSourceRecoverySequence(states,incoming,11,27,benefit);assert.deepEqual(sequence.steps.map(s=>[s.root,s.parent,s.uploadPeakBytes]),[[2,'Q',25],[1,'A',27]]);assert.equal(sequence.finalBytes+sequence.cost,26);assert.deepEqual(sequence.steps.map(s=>s.estimatedTotalLoss),[3,4]);assert.equal(f.bytes,18);
});
test('a temporary step cannot exceed the quality loss allowed for its final ancestor',()=>{
 assert.equal(planSourceRecoverySequence(fixture(),request,13,24,(root,node)=>node.name==='A'?3:2),null);
});
test('coarsening an incoming replacement parent or its ancestor remains forbidden',()=>{
 assert.equal(planSourceRecoverySequence(fixture(),{id:1,parent:'G',score:100},13,24,priority),null);
});
test('stale or cancelled plans issue no restore or candidate upload',async()=>{
 const states=fixture(),sequence=planSourceRecoverySequence(states,request,13,24,priority);let applied=0;
 await assert.rejects(applySourceRecoverySequence({sequence,residents:states,stillWanted:()=>false,apply:()=>{applied++;}}),SourceLoadCancelled);
 states.get(1).frontier.cutVersion++;
 await assert.rejects(applySourceRecoverySequence({sequence,residents:states,stillWanted:()=>true,apply:()=>{applied++;}}),SourceLoadCancelled);assert.equal(applied,0);
});
test('combined independent losses must satisfy the two-times margin as a whole',()=>{
 const make=(name)=>{const root={marker:{source_nodes:[{name,children:['x'],spans:[{part:'p'}]}],parts:[{directory:'p',gpu_payload_bytes:1}]},meshes:new Map([['p',{}]])},child={marker:{source_nodes:[{name:'x',children:[],spans:[{part:'c'}]}],parts:[{directory:'c',gpu_payload_bytes:6}]},meshes:new Map([['c',{}]])};return {frontier:Object.assign(Object.create(SourceFrontier.prototype),{bundles:new Map([['$root',root],[name,child]]),visible:new Set(['x']),cutVersion:0})};};
 const states=new Map([[1,make('one')],[2,make('two')]]);
 assert.equal(planSourceBudget(states,{id:3,parent:'incoming',score:10},9,12,()=>3),null);
 assert.equal(planSourceRecoverySequence(states,{id:3,parent:'incoming',score:10},9,12,()=>3),null);
 assert.equal(planSourceBudget(states,{id:3,parent:'incoming',score:10},9,12,()=>2).length,2);
});
