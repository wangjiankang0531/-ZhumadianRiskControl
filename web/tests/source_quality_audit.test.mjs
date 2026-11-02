import test from 'node:test';import assert from 'node:assert/strict';
import {ProjectedQualityAudit,captureSourceLoadState} from '../src/source_quality_audit.js';
import {visibilityWitnessGrid} from '../src/startup_witness.js';

test('edge-only, texel-only, joint and satisfied samples remain distinct',()=>{
 const a=new ProjectedQualityAudit({height:100,fov:90});
 for(const [edge,texel] of [[.2,.001],[.001,.02],[.2,.02],[.001,.001]])a.record(0,{longest_edge_p90_m:edge,texel_world_p90_m:texel},0);
 const c=a.snapshot().cells[0];assert.equal(c.knownSamples,4);assert.equal(c.edgeOnlySamples,1);assert.equal(c.texelOnlySamples,1);assert.equal(c.bothSamples,1);assert.equal(c.neitherSamples,1);assert.ok(Math.abs(c.edgePixels.max-20)<1e-10);assert.ok(Math.abs(c.texelPixels.max-2)<1e-10);
});
test('unknown metadata stays unknown, snapshots detach and sampling is bounded',()=>{
 const a=new ProjectedQualityAudit({height:100,fov:60,maxSamples:2});a.record(0,null,0);a.record(1,{longest_edge_p90_m:0,texel_world_p90_m:0},255);
 const s=a.snapshot();assert.equal(s.cells[0].unknownSamples,1);assert.equal(s.cells[0].edgePixels.p90,null);s.cells[1].edgePixels.max=999;assert.equal(a.snapshot().cells[1].edgePixels.max,0);assert.throws(()=>a.record(2,{},0));assert.throws(()=>new ProjectedQualityAudit({height:0,fov:60}));
});
test('witness decomposition uses the same unobscured raster without altering existing quality',()=>{
 const samples=new Map([['root/1',[-2/3,2/3,0,1]],['node/2/x',[2/3,2/3,0,1]]]),metrics=new Map([['root/1',{bounds_min:[0,0,0],longest_edge_p90_m:.2,texel_world_p90_m:.001}],['node/2/x',{bounds_min:[0,0,0],longest_edge_p90_m:.001,texel_world_p90_m:.02}]]),args={samples,metrics,fov:90,width:300,height:100,rasterWidth:3,rasterHeight:3,obscured:[{left:0,top:0,right:100,bottom:40}]};
 const old=visibilityWitnessGrid(args),current=visibilityWitnessGrid({...args,qualityComponents:true});const {qualityComponents,...rest}=current;assert.deepEqual(rest,old);assert.equal(qualityComponents.samples,1);assert.equal(qualityComponents.cells[2].texelOnlySamples,1);assert.equal(qualityComponents.cells[0].knownSamples,0);
});
test('current failure audit preserves counts and bounds keys without exposing payloads',()=>{
 const failed=new Set(Array.from({length:40},(_,i)=>`${i}/1`)),empty=new Set();const args={failed,familyFailed:empty,coverageRejected:empty,restoreFailed:empty,lastGain:{root:2,gain:1,packets:new Uint8Array(100)},allocationChoice:{key:'root/2/1',gain:1,bytes:12}};const s=captureSourceLoadState(args);assert.equal(s.roots.count,40);assert.equal(s.roots.keys.length,32);assert.equal(s.roots.truncated,true);assert.equal('packets' in s.lastGain,false);s.roots.keys[0]='changed';assert.equal(captureSourceLoadState(args).roots.keys[0],'0/1');
});

test('visible photo with unavailable metric remains unknown in the integrated audit',()=>{
 const grid=visibilityWitnessGrid({samples:new Map([['root/1',[-2/3,2/3,0,1]]]),width:300,height:100,rasterWidth:3,rasterHeight:3,fov:90,qualityComponents:true});assert.equal(grid.cells[0].qualitySamples,0);assert.equal(grid.qualityComponents.samples,1);assert.equal(grid.qualityComponents.cells[0].unknownSamples,1);assert.equal(grid.qualityComponents.cells[0].neitherSamples,0);
});
