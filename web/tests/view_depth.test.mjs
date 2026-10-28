import test from 'node:test';
import assert from 'node:assert/strict';
import {Box3,Vector3,PerspectiveCamera,Frustum,Matrix4} from 'three';
import {boundsViewDepth,selectDepth} from '../src/lod_policy.js';
import {sourceViewPriority,visibleSourceCandidates} from '../src/source_frontier.js';
import {initialIndexedCoverageDepth} from '../src/source_level_index.js';
const close=(a,b)=>assert.ok(Math.abs(a-b)<=1e-9*(1+Math.abs(b)),`${a} != ${b}`);
const cameraAt=(p=[0,0,0],target=[0,0,-1],up=[0,1,0])=>{const c=new PerspectiveCamera(52,1280/585,.5,60000);c.up.set(...up);c.position.set(...p);c.lookAt(...target);c.updateMatrixWorld();return c;};
const box857=()=>new Box3(new Vector3(588.35400390625,-2210.24609375,30.876001358032227),new Vector3(658.6461181640625,-2139.953857421875,51.344993591308594));
const camera857=()=>cameraAt([-509.5,-2198,393],[-317,-1988,43],[0,0,1]);
test('actual upper-right root857 is requested when radial distance previously hid its projected deficit',()=>{
 const c=camera857(),b=box857(),f=585/(2*Math.tan(c.fov*Math.PI/360)),radial=b.distanceToPoint(c.position),depth=boundsViewDepth(b,c),edge=10.024267307233053,texel=2.8090257815948254;
 const choose=d=>selectDepth(b.getSize(new Vector3()).length()*f/d,edge*f/d,edge*f/d,0,6,0,texel*f/d,texel*f/d,0);
 assert.equal(new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(c.projectionMatrix,c.matrixWorldInverse)).intersectsBox(b),true);
 assert.equal(choose(radial),0);assert.equal(choose(depth),3);assert.ok(texel*f/depth>1.5);
 // Independent perspective projection of a view-horizontal one-metre segment.
 const z=1000,p=new Vector3(500,0,-z).applyMatrix4(c.matrixWorld),q=new Vector3(501,0,-z).applyMatrix4(c.matrixWorld);
 close(Math.abs(q.project(c).x-p.project(c).x)*1280/2,f/z);
});
test('lateral translation cannot make equal-depth screen detail artificially sharper',()=>{
 const c=cameraAt(),a=new Box3(new Vector3(-5,-5,-105),new Vector3(5,5,-95)),b=a.clone().translate(new Vector3(70,0,0));
 close(boundsViewDepth(a,c),95);close(boundsViewDepth(b,c),95);assert.ok(b.distanceToPoint(c.position)>a.distanceToPoint(c.position));
});
test('nearest projected AABB plane agrees with independent eight-corner transforms for rotated cameras',()=>{
 for(const [p,t,u] of [[[0,0,10],[0,0,0],[0,1,0]],[[20,-30,40],[0,5,0],[0,0,1]],[[-509.5,-2198,393],[-317,-1988,43],[0,0,1]]]){
  const c=cameraAt(p,t,u);
  for(let n=0;n<24;n++){
   const lo=new Vector3(-110+n*11,-240+n*7,-20+n),hi=lo.clone().add(new Vector3(10+n,30,5+n)),b=new Box3(lo,hi),values=[];
   for(const x of [lo.x,hi.x])for(const y of [lo.y,hi.y])for(const z of [lo.z,hi.z])values.push(-new Vector3(x,y,z).applyMatrix4(c.matrixWorldInverse).z);
   close(boundsViewDepth(b,c),Math.max(c.near,Math.min(...values)));
  }
 }
});
test('near-plane and camera-crossing bounds stay finite and conservative',()=>{
 const c=cameraAt();for(const b of [new Box3(new Vector3(-1,-1,-2),new Vector3(1,1,2)),new Box3(new Vector3(-1,-1,-.7),new Vector3(1,1,-.2))])close(boundsViewDepth(b,c),c.near);
 const b=new Box3(new Vector3(-1,-1,-9),new Vector3(1,1,-7));close(boundsViewDepth(b,c),7);
});
test('a shared scene translation preserves projected bounds depth',()=>{
 const c=camera857(),b=box857(),delta=new Vector3(100000,-90000,55000),shift=cameraAt(c.position.clone().add(delta).toArray(),new Vector3(-317,-1988,43).add(delta).toArray(),[0,0,1]);
 close(boundsViewDepth(b,c),boundsViewDepth(b.clone().translate(delta),shift));
});
test('family candidate gating and fallback priority retain the actual off-axis source',()=>{
 const c=camera857(),b=box857(),node={name:'visible-parent',children:['child'],bounds_min:b.min.toArray(),bounds_max:b.max.toArray(),longest_edge_p90_m:10.024267307233053,texel_world_p90_m:2.8090257815948254},frontier={visible:new Set([node.name]),nodes:new Map([[node.name,{node}]])};
 const rows=visibleSourceCandidates(frontier,c,585);assert.equal(rows.length,1);assert.ok(rows[0].score>0);close(rows[0].score,sourceViewPriority(node,c,585));
});
test('projection correction never bypasses offscreen rejection or terminal-family exclusion',()=>{
 const c=cameraAt(),node={name:'behind',children:['child'],bounds_min:[-1,-1,5],bounds_max:[1,1,10],longest_edge_p90_m:100,texel_world_p90_m:100},frontier={visible:new Set([node.name]),nodes:new Map([[node.name,{node}]])};
 assert.equal(visibleSourceCandidates(frontier,c,585).length,0);assert.equal(sourceViewPriority(node,c,585),0);
 node.bounds_min=[-1,-1,-10];node.bounds_max=[1,1,-5];node.children=[];assert.equal(visibleSourceCandidates(frontier,c,585).length,0);
});
test('measured complete coverage tier uses the same corrected depth without forcing maximum detail',()=>{
 const c=camera857(),depth=boundsViewDepth(box857(),c),f=585/(2*Math.tan(c.fov*Math.PI/360)),r={coverageTiers:[{depth:1,sourceCount:1,maxTexel:.5082881650502618},{depth:2,sourceCount:1,maxTexel:.25771288499882494},{depth:3,sourceCount:1,maxTexel:.12959174657504333}]};
 assert.equal(initialIndexedCoverageDepth(r,3,f,depth),1);
});
