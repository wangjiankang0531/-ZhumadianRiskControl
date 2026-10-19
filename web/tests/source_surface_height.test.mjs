import test from 'node:test';
import assert from 'node:assert/strict';
import {sourceSurfaceHeight} from '../src/source_surface_height.js';
function frontier({z=2,visible=true,order=[0,1,2],span={first:0,count:3},selected=true}={}){
 const mesh={visible,geometry:{attributes:{position:{array:new Float32Array([0,0,z,1,0,z+1,0,1,z+2])}},index:{array:new Uint32Array(order)}}};
 const node={bounds_min:[0,0,z],bounds_max:[1,1,z+2],spans:[{...span,part:'part_000'}]};
 return {nodes:new Map([['source',{node,bundle:{meshes:new Map([['part_000',mesh]])}}]]),visible:new Set(selected?['source']:[])};
}
test('barycentric surface uses fixed XY and original source height for either winding',()=>{
 for(const order of [[0,1,2],[0,2,1]]){const f=frontier({order});assert.equal(sourceSurfaceHeight([f],.25,.25),2.75);assert.equal(sourceSurfaceHeight([f],0,0),2);}
});
test('only currently visible source nodes and spans contribute; holes preserve the caller fallback',()=>{
 assert.equal(sourceSurfaceHeight([frontier({visible:false})],.25,.25),null);
 assert.equal(sourceSurfaceHeight([frontier({selected:false})],.25,.25),null);
 assert.equal(sourceSurfaceHeight([frontier({span:{first:0,count:0}})],.25,.25),null);
 assert.equal(sourceSurfaceHeight([frontier()],.8,.8),null);
 assert.equal(sourceSurfaceHeight([frontier()],2,2),null);
});
test('overlapping surfaces choose the highest displayed face; unloaded cuts can return the original anchor',()=>{
 assert.equal(sourceSurfaceHeight([frontier({z:-5}),frontier({z:-3})],.25,.25),-2.25);
 assert.equal(sourceSurfaceHeight([],.25,.25),null);
 const f=frontier();f.nodes.get('source').bundle.meshes.clear();assert.equal(sourceSurfaceHeight([f],.25,.25),null);
});
test('degenerate vertical projections and non-finite source samples do not lift the sign',()=>{
 for(const data of [[0,0,0,0,0,1,0,0,2],[0,0,NaN,1,0,1,0,1,2]]){
  const f=frontier();f.nodes.get('source').bundle.meshes.get('part_000').geometry.attributes.position.array=new Float32Array(data);assert.equal(sourceSurfaceHeight([f],.25,.25),null);
 }
});

