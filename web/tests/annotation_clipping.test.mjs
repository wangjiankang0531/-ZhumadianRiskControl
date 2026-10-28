import test from 'node:test';
import assert from 'node:assert/strict';
import {PerspectiveCamera, Matrix4, Vector3, Vector4} from 'three';
import {clipAnnotationGeometry as clip, traceAnnotationPaths} from '../src/annotation_clipping.js';
import {buildHitTarget, pickAnnotation, insideRing, distanceToSegment} from '../src/annotation_interaction.js';
const camera = new PerspectiveCamera(90, 1, .5, 10); camera.updateMatrixWorld();
const matrix = new Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse).elements;
const identity = new Matrix4().elements;
const close = (actual, expected, epsilon = 1e-7) => assert.ok(Math.abs(actual - expected) <= epsilon, `${actual} != ${expected}`);
const feature = (type, extra = {}) => ({id:type, type, style:{opacity:1, fillOpacity:0, widthPx:4, sizePx:32, ...extra}});
const hit = (f, g, p) => pickAnnotation([buildHitTarget(f, {name:'synthetic'}, [], null, g)].filter(Boolean), p)?.feature.id ?? null;
const result = (type, positions, m = matrix, pad = 0) => clip(type, positions, m, 400, 400, pad);

test('near-plane crossing keeps the visible line and its hit target', () => {
  const g = result('line', [[-.5,0,-2],[.5,0,1]]);
  assert.equal(g.strokePaths.length, 1); assert.deepEqual(g.fillRings, []);
  close(g.strokePaths[0][0][0], 150); close(g.strokePaths[0][1][0], 200);
  assert.equal(hit(feature('line'),g,[160,200]),'line'); assert.equal(hit(feature('line'),g,[230,200]),null);
});
test('far-plane crossing is trimmed rather than dropping the visible segment', () => {
  const g = result('line', [[-.5,0,-2],[1,0,-20]]);
  assert.equal(g.strokePaths.length, 1); close(g.strokePaths[0][0][0],150);close(g.strokePaths[0][1][0],200+10/3);
});
test('lines fully behind, beyond far, or outside the side planes produce no paths', () => {
  for (const points of [[[0,0,1],[1,0,2]],[[0,0,-11],[1,0,-20]],[[20,0,-1],[30,0,-2]]])
    assert.deepEqual(result('line',points),{strokePaths:[],fillRings:[]});
});
test('clipped-out polyline intervals are never bridged or selectable', () => {
  const g=result('line',[[0,0,0],[2,0,0],[2,.5,0],[0,.5,0]],identity);
  assert.equal(g.strokePaths.length,2);assert.equal(hit(feature('line'),g,[399,150]),null);
  assert.equal(hit(feature('line'),g,[300,200]),'line');assert.equal(hit(feature('line'),g,[300,100]),'line');
});
test('region filling has no invented outline or hit edge on the clipping plane', () => {
  const g=result('region',[[0,0,0],[2,0,0],[2,.5,0],[0,.5,0]],identity);
  assert.equal(g.fillRings.length,1);
  assert.equal(hit(feature('region'),g,[399,150]),null);
  assert.equal(hit(feature('region',{fillOpacity:.3}),g,[399,150]),'region');
  assert.equal(hit(feature('region'),g,[200,150]),'region');
});
test('near-clipped region remains filled while its artificial near edge is not stroked', () => {
  const g=result('region',[[-1,-1,-2],[1,-1,-2],[1,1,1],[-1,1,1]]);
  assert.equal(g.fillRings.length,1);assert.equal(hit(feature('region'),g,[200,201]),null);
  assert.equal(hit(feature('region',{fillOpacity:.4}),g,[200,201]),'region');
  assert.equal(hit(feature('region',{opacity:0,fillOpacity:0}),g,[200,250]),null);
});
function winding(point, ring) {
  let count=0;
  for(let i=0;i<ring.length;i++){
    const a=ring[i],b=ring[(i+1)%ring.length],cross=(b[0]-a[0])*(point[1]-a[1])-(point[0]-a[0])*(b[1]-a[1]);
    if(a[1]<=point[1]&&b[1]>point[1]&&cross>0)count++;
    if(a[1]>point[1]&&b[1]<=point[1]&&cross<0)count--;
  }
  return count!==0;
}
test('concave disconnected clipped lobes preserve the gap for both windings', () => {
  const polygon=[[-.9,-2,0],[.9,-2,0],[.9,.9,0],[.4,.9,0],[.4,-1.5,0],[-.4,-1.5,0],[-.4,.9,0],[-.9,.9,0]];
  for(const ring of [polygon,[...polygon].reverse()]){
    const g=result('region',ring,identity);assert.equal(g.fillRings.length,1);
    for(let ix=0;ix<19;ix++)for(let iy=0;iy<19;iy++){
      const p=[-.94+ix*.101,-.94+iy*.101],screen=[(p[0]+1)*200,(1-p[1])*200];
      assert.equal(g.fillRings.some(r=>insideRing(screen,r)),winding(p,ring));
    }
    assert.equal(hit(feature('region',{opacity:0,fillOpacity:.3}),g,[200,200]),null);
  }
});
test('region covering the viewport has fill without any false viewport-border outline', () => {
  const g=result('region',[[-2,-2,0],[2,-2,0],[2,2,0],[-2,2,0]],identity);
  assert.equal(g.strokePaths.length,0);assert.equal(g.fillRings[0].length,4);
  assert.equal(hit(feature('region'),g,[1,200]),null);
  assert.equal(hit(feature('region',{fillOpacity:.5}),g,[1,200]),'region');
});
test('stroke padding preserves a wide offscreen-centred line at the viewport edge', () => {
  assert.equal(result('line',[[1.02,-.5,0],[1.02,.5,0]],identity).strokePaths.length,0);
  const g=result('line',[[1.02,-.5,0],[1.02,.5,0]],identity,12);
  assert.equal(g.strokePaths.length,1);assert.equal(hit(feature('line',{widthPx:16}),g,[399,200]),'line');
});
test('same input data and projection matrices are not mutated', () => {
  const p=[[-1,-1,-2],[1,-1,-2],[1,1,1],[-1,1,1]],m=[...matrix],before=JSON.stringify([p,m]);
  result('region',p,m);assert.equal(JSON.stringify([p,m]),before);
});
test('rigid camera motion agrees with a known camera-space line', () => {
  const c=new PerspectiveCamera(90,1,.5,10);c.up.set(0,0,1);c.position.set(120,-300,80);c.lookAt(10,30,15);c.updateMatrixWorld();
  const points=[[-.5,0,-2],[.5,0,1]].map(p=>new Vector3(...p).applyMatrix4(c.matrixWorld).toArray());
  const g=result('line',points,new Matrix4().multiplyMatrices(c.projectionMatrix,c.matrixWorldInverse).elements);
  close(g.strokePaths[0][0][0],150,1e-6);close(g.strokePaths[0][1][0],200,1e-6);
});
test('random independently projected visible samples lie on the retained segment', () => {
  let seed=0x13572468,covered=0;const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
  for(let i=0;i<250;i++){
    const points=Array.from({length:2},()=>[(rand()-.5)*12,(rand()-.5)*12,-15+rand()*20]);
    const g=result('line',points),parts=g.strokePaths.flatMap(path=>path.slice(1).map((p,j)=>[path[j],p]));
    for(let j=0;j<=40;j++){
      const t=j/40,p=points[0].map((v,k)=>v+(points[1][k]-v)*t),v=new Vector4(...p,1).applyMatrix4(new Matrix4().fromArray(matrix));
      if(v.w<=0||Math.abs(v.x)>v.w||Math.abs(v.y)>v.w||Math.abs(v.z)>v.w)continue;
      covered++;const screen=[(v.x/v.w+1)*200,(1-v.y/v.w)*200];
      assert.ok(parts.some(([a,b])=>distanceToSegment(screen,a,b)<1e-6));
    }
    for(const path of g.strokePaths)for(const p of path)assert.ok(p.every(Number.isFinite)&&p[0]>=-1e-7&&p[0]<=400+1e-7&&p[1]>=-1e-7&&p[1]<=400+1e-7);
  }
  assert.ok(covered>1000);
});
test('path tracing keeps ordinary region closure and does not invent closing strokes for clipped pieces', () => {
  const calls=[],ctx={moveTo:(...p)=>calls.push(['M',...p]),lineTo:(...p)=>calls.push(['L',...p]),closePath:()=>calls.push(['Z'])};
  traceAnnotationPaths(ctx,[[[1,1],[2,1],[2,2],[1,1]]],true);
  assert.deepEqual(calls,[['M',1,1],['L',2,1],['L',2,2],['Z']]);calls.length=0;
  traceAnnotationPaths(ctx,[[[0,1],[2,1]],[[2,3],[0,3]]],true);
  assert.equal(calls.filter(c=>c[0]==='Z').length,0);assert.equal(calls.filter(c=>c[0]==='M').length,2);
});
test('invalid projection input fails without returning non-finite geometry', () => {
  for(const [type,p,m,w,h,pad] of [['point',[[0,0,0]],identity,400,400,0],['line',[[0,0,0],[NaN,0,0]],identity,400,400,0],['line',[[0,0,0],[1,1,0]],identity,0,400,0],['line',[[0,0,0],[1,1,0]],[...identity.slice(0,15),Infinity],400,400,0],['line',[[0,0,0],[1,1,0]],identity,400,400,-1]])
    assert.throws(()=>clip(type,p,m,w,h,pad),/clipping input/);
});
test('labels stay independently selectable while clipped geometry has no visible part', () => {
  const f=feature('line'),g=result('line',[[0,0,1],[1,0,2]]),t=buildHitTarget(f,{name:'synthetic'},[],[10,10,80,30],g);
  assert.equal(pickAnnotation([t],[30,20]).feature.id,'line');assert.equal(pickAnnotation([t],[100,20]),null);
});
