import {texelAwareSourceGain} from '../src/source_geometry_gain.js';
import test from 'node:test';import assert from 'node:assert/strict';
import {chooseFeasibleSourceCandidate,SourceAllocationScan} from '../src/source_allocation.js';
import {depthWeightedTexelPriority,SourceVisibility} from '../src/source_visibility.js';
const c=(key,score,cost,textureScore=0)=>({key,kind:'family',id:1,score,cost,textureScore});
const options={indexed:true,hasRoot:()=>true,feasible:()=>true};
test('texture-first tier precedes geometry-only metadata while disabled ordering stays original',()=>{
 const texture=c('texture',.1,100,.01),geometry=c('geometry',100,null);const before=structuredClone([texture,geometry]);assert.equal(chooseFeasibleSourceCandidate([geometry,texture],options),geometry);assert.equal(chooseFeasibleSourceCandidate([geometry,texture],{...options,textureFirst:true}),texture);assert.deepEqual([texture,geometry],before);
});
test('uncovered roots retain first priority and each texture tier retains original gain per byte',()=>{
 const root={...c('root',.01,1000),kind:'root',id:2},large=c('large',20,40,1),small=c('small',8,8,.1);assert.equal(chooseFeasibleSourceCandidate([large,small,root],{...options,hasRoot:id=>id!==2,textureFirst:true}),root);assert.equal(chooseFeasibleSourceCandidate([large,small],{...options,textureFirst:true}),small);
});
test('infeasible texture needs yield to admissible geometry rather than blocking the queue',()=>{
 const texture=c('texture',1,100,.2),geometry=c('geometry',2,50),probes=[];const result=chooseFeasibleSourceCandidate([geometry,texture],{...options,textureFirst:true,feasible:c=>{probes.push(c.key);return c.key==='geometry';}});assert.equal(result,geometry);assert.deepEqual(probes,['texture','geometry']);
});
test('unknown texture metadata does not allocate and invalid tier scores fail closed',()=>{
 const texture=c('texture',.1,null,.1),geometry=c('geometry',100,1);assert.equal(chooseFeasibleSourceCandidate([geometry,texture],{...options,textureFirst:true,feasible:()=>{throw Error('metadata must not allocate');}}),texture);for(const textureScore of [-1,NaN,Infinity])assert.throws(()=>chooseFeasibleSourceCandidate([c('bad',1,1,textureScore)],{...options,textureFirst:true}));assert.throws(()=>chooseFeasibleSourceCandidate([texture],{...options,textureFirst:1}));
});
test('texture-tier scan preserves bounded slices and cancels its result when camera changes',()=>{
 const texture=c('texture',1,100,.1),geometry=c('geometry',2,50);let now=0;const scan=new SourceAllocationScan([geometry,texture],{...options,textureFirst:true,feasible:c=>{now+=5;return c===geometry;}});const first=scan.step({budgetMs:4,clock:()=>now});assert.equal(first.done,false);assert.equal(first.cursor,1);const cancelled=scan.step({clock:()=>now,isCurrent:()=>false});assert.equal(cancelled.cancelled,true);assert.equal(cancelled.candidate,null);
});
test('texture deficit is independent of a large triangle edge and respects actual depth bins',()=>{
 const node={bounds_min:[0,0,0],longest_edge_p90_m:1e6,texel_world_p90_m:.001},bins=new Map([[0,1]]);assert.equal(depthWeightedTexelPriority(node,bins,{fov:90},100),0);const coarse={...node,texel_world_p90_m:.02};const near=depthWeightedTexelPriority(coarse,bins,{fov:90},100);assert.ok(near>0);assert.equal(depthWeightedTexelPriority(coarse,new Map([[255,1]]),{fov:90},100),0);assert.ok(Math.abs(depthWeightedTexelPriority(coarse,new Map([[0,.25],[255,.75]]),{fov:90},100)-near*.25)<1e-12);
});

test('texture-aware gain refuses regression of either proxy and keeps legacy replies compatible',()=>{
 const valid={gain:1,signedGain:1,beforeTexelDeficit:2,afterTexelDeficit:0,texelGain:2,signedTexelGain:2,texelModel:'visible_texel_deficit_v1'};assert.equal(texelAwareSourceGain(valid),2);assert.equal(texelAwareSourceGain({...valid,signedGain:-.1,gain:0}),0);assert.equal(texelAwareSourceGain({...valid,signedTexelGain:-.1,texelGain:0}),0);assert.equal(texelAwareSourceGain({gain:.5}),.5);assert.throws(()=>texelAwareSourceGain({...valid,texelGain:NaN}));
});
test('budget retirement sees a texture loss hidden by an unchanged large edge',()=>{
 const visibility=Object.create(SourceVisibility.prototype);visibility.depthBins=new Map([['node/1/fine',new Map([[0,1]])]]);const fine={bounds_min:[0,0,0],longest_edge_p90_m:100,texel_world_p90_m:.001},replacement={...fine,texel_world_p90_m:.02},nodes=new Map([['fine',{node:fine}]]);assert.equal(visibility.retirementLoss(1,replacement,['fine'],nodes,{fov:90},100),0);assert.ok(visibility.textureRetirementLoss(1,replacement,['fine'],nodes,{fov:90},100)>0);
});
