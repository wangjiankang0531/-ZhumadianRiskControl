import test from 'node:test';
import assert from 'node:assert/strict';
import {selectDepth,measureBaseTexels,prioritizeDetail,pickFocusRoot} from '../src/lod_policy.js';
test('magnified base texels trigger refinement even when geometry already looks dense',()=>{assert.equal(selectDepth(300,2,0,0,7),0);assert.equal(selectDepth(300,2,0,0,7,0,2),3);});
test('resident texture magnification drives next tier and prevents premature coarsening',()=>{assert.equal(selectDepth(300,10,2,4,7,0,0,2),5);assert.equal(selectDepth(300,10,1,6,7,3,0,.1,2),6);assert.equal(selectDepth(300,10,1,6,7,3,0,.1,.1),5);});
test('center refinement runs before initial neighbor detail while safe coarsening remains first',()=>{const residents=new Map([[1,{depth:3}],[3,{depth:5}]]);assert.deepEqual(prioritizeDetail([{id:2,depth:3},{id:1,depth:4},{id:3,depth:4}],residents,1).map(x=>x.id),[3,1,2]);});
test('texel scale measures world geometry against actual UV and rectangular texture dimensions',()=>{const c={root_records:[{tile_id:1,base_spans:[[0,3]]}]},p=[0,0,0,10,0,0,0,10,0],i=[0,1,2],uv=[0,0,1,0,0,1];assert.equal(measureBaseTexels(c,p,i,uv,100,100).get(1),.1);assert.equal(measureBaseTexels(c,p,i,uv,200,200).get(1),.05);});

test('view center follows the actual source surface rather than a closer empty bounding box center',async()=>{
 const {Ray,Vector3}=await import('three'),c={root_records:[{bounds_min:[-1,-1,1],bounds_max:[1,1,3],base_spans:[[0,3]]},{bounds_min:[-1,-1,0],bounds_max:[1,1,1],base_spans:[[3,3]]}]};
 const positions=[.5,.5,2,.8,.5,2,.5,.8,2,-1,-1,0,1,-1,0,0,1,0];
 assert.equal(pickFocusRoot([{id:1},{id:2}],c,positions,[0,1,2,3,4,5],new Ray(new Vector3(0,0,5),new Vector3(0,0,-1))).id,2);
});

test('a camera inside overlapping bounds still selects the nearest source triangle',async()=>{
 const {Ray,Vector3}=await import('three'),c={root_records:[{bounds_min:[-2,-2,-4],bounds_max:[2,2,2],base_spans:[[0,3]]},{bounds_min:[-2,-2,-10],bounds_max:[2,2,2],base_spans:[[3,3]]}]};
 const positions=[-1,-1,-3,1,-1,-3,0,1,-3,-1,-1,-1,1,-1,-1,0,1,-1];
 assert.equal(pickFocusRoot([{id:1},{id:2}],c,positions,[0,1,2,3,4,5],new Ray(new Vector3(0,0,0),new Vector3(0,0,-1))).id,2);
});
