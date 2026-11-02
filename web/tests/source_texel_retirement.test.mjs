import test from 'node:test';import assert from 'node:assert/strict';
import {PerspectiveCamera,Scene} from 'three';
import {sourceTexelRetirementPriority as priority} from '../src/source_texel_retirement.js';
import {SourceVisibility} from '../src/source_visibility.js';
import {planSourceBudget} from '../src/source_frontier.js';
import {planSourceRecoverySequence} from '../src/source_recovery_plan.js';
test('disabled protection preserves the existing maximum of combined and texture loss',()=>{
 for(const combinedLoss of [0,.01,1,Infinity])for(const texelLoss of [0,.001,2,Infinity])assert.equal(priority({combinedLoss,texelLoss}),Math.max(combinedLoss,texelLoss));
});
test('even a tiny positive visible texel loss cannot be outweighed by a different detail gain',()=>{
 assert.equal(priority({combinedLoss:0,texelLoss:Number.MIN_VALUE,protectTexels:true}),Infinity);
 assert.equal(priority({combinedLoss:.01,texelLoss:Infinity,protectTexels:true}),Infinity);
});
test('geometry-only loss remains eligible and invalid loss never masquerades as safe',()=>{
 assert.equal(priority({combinedLoss:.1,texelLoss:0,protectTexels:true}),.1);
 assert.equal(priority({combinedLoss:Infinity,texelLoss:0,protectTexels:true}),Infinity);
 for(const bad of [NaN,-1,undefined,'0'])assert.throws(()=>priority({combinedLoss:bad,protectTexels:true}));
 assert.throws(()=>priority({combinedLoss:0,protectTexels:1}));
});
function fixture(){const make=()=>({bytes:120,cutVersion:1,visible:new Set(['a']),bundles:new Map([['$root',{meshes:new Map()}]]),nodes:new Map(),copyForPlanning(){return {...this,visible:new Set(this.visible),bundles:new Map(this.bundles)};}});return new Map([[1,{frontier:make()}],[2,{frontier:make()}]]);}
test('direct budget plan excludes unsafe root eviction without mutating the live cut',()=>{
 const r=fixture(),request={id:1,parent:'a',score:1},rootPriority=protectTexels=>()=>priority({combinedLoss:.01,texelLoss:.001,protectTexels});
 assert.deepEqual(planSourceBudget(r,request,50,240,()=>0,rootPriority(false)),[{root:2,parent:null}]);
 assert.equal(planSourceBudget(r,request,50,240,()=>0,rootPriority(true)),null);assert.equal(r.size,2);assert.equal(r.get(2).frontier.bytes,120);
});
test('multi-step detail recovery cannot bypass texture protection',()=>{
 const r=fixture(),request={id:1,parent:'a',score:1},rootPriority=protectTexels=>()=>priority({combinedLoss:.01,texelLoss:.001,protectTexels});
 assert.equal(planSourceRecoverySequence(r,request,50,240,()=>0,rootPriority(true)),null);
 const old=planSourceRecoverySequence(r,request,50,240,()=>0,rootPriority(false));assert.equal(old.steps.length,1);assert.equal(old.steps[0].root,2);assert.equal(r.size,2);
});
test('invisible or still-sufficient replacement texels stay reclaimable while real near deficits are protected',()=>{
 const v=new SourceVisibility({},new Scene(),new Scene()),camera=new PerspectiveCamera(52,1,.5,60000),node=texel=>({bounds_min:[0,0,0],bounds_max:[1,1,1],longest_edge_p90_m:10,texel_world_p90_m:texel});
 const nodes=new Map([['a',{node:node(.001)}]]),names=new Set(['a']);
 assert.equal(v.textureRetirementLoss(2,node(1),names,nodes,camera,573),0);
 v.depthBins.set('node/2/a',new Map([[255,1]]));assert.equal(v.textureRetirementLoss(2,node(1),names,nodes,camera,573),0);
 v.depthBins.set('node/2/a',new Map([[96,.1],[255,.9]]));const loss=v.textureRetirementLoss(2,node(1),names,nodes,camera,573);assert.ok(loss>0);
 assert.equal(priority({combinedLoss:.01,texelLoss:loss,protectTexels:true}),Infinity);v.dispose();
});
