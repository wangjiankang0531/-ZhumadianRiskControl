import test from 'node:test';
import assert from 'node:assert/strict';
import {visibilityRegionWeights} from '../src/visibility_region_weights.js';
function fixture(w=12,h=12){const pixels=new Uint8Array(w*h*4);for(let i=0;i<w*h;i++)pixels[i*4]=1;return {pixels,rasterWidth:w,rasterHeight:h,width:w,height:h};}
test('legacy mode reproduces area weighting including panel intersections',()=>{
 const a=fixture(),obscured=[{left:0,right:3,top:0,bottom:12}],r=visibilityRegionWeights({...a,obscured});
 assert.equal(r.policy,'visible_pixel_area_v1');assert.equal(r.weights[0],Math.fround(.2));assert.equal(r.weights[3],1);assert.ok(r.cells.every(c=>c.factor===1));
});
test('unobscured equal-area cells are unchanged by regional balance',()=>{
 const a=fixture(),r=visibilityRegionWeights({...a,balanced:true});assert.ok(r.weights.every(v=>v===1));assert.equal(r.cells.reduce((s,c)=>s+c.visiblePhotoSamples,0),144);
});
test('side panels no longer reduce every exposed outer cell below central influence',()=>{
 const a=fixture(),obscured=[{left:0,right:2,top:0,bottom:12},{left:10,right:12,top:0,bottom:12}],r=visibilityRegionWeights({...a,obscured,balanced:true});
 const totals=r.cells.map(c=>c.visiblePhotoSamples*c.factor);for(const n of totals)assert.ok(Math.abs(n-totals[4])<1e-12);
 assert.equal(r.weights[0],Math.fround(.2));assert.ok(r.weights[2]>r.weights[5]);
});
test('sky-only cells and tiny exposed slivers cannot create unbounded scores',()=>{
 const a=fixture();a.pixels.fill(0);a.pixels[0]=1;const r=visibilityRegionWeights({...a,balanced:true});assert.ok(r.weights.every(Number.isFinite));assert.equal(r.cells.filter(c=>c.visiblePhotoSamples).length,1);assert.ok(r.cells.every(c=>c.factor>=.5&&c.factor<=2));
 const b=fixture();for(let y=8;y<12;y++)for(let x=0;x<4;x++)b.pixels[(y*12+x)*4]=0;b.pixels[(8*12)*4]=1;
 const z=visibilityRegionWeights({...b,balanced:true});assert.equal(z.cells[0].factor,2);assert.ok(z.weights.every(v=>v<=2));
});
test('weights do not depend on root/depth identity and cannot mutate the source raster',()=>{
 const a=fixture(),before=a.pixels.slice(),one=visibilityRegionWeights({...a,balanced:true});for(let i=0;i<a.pixels.length;i+=4)a.pixels[i]=14;const two=visibilityRegionWeights({...a,balanced:true});assert.deepEqual(one.weights,two.weights);assert.equal(before[0],1);assert.equal(a.pixels[0],14);
 assert.throws(()=>visibilityRegionWeights({...a,pixels:new Uint8Array(3)}));
});
