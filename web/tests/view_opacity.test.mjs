import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {opacityFromTransparency,annotationWithOpacity,applyModelOpacity} from '../src/view_opacity.js';
import {drawLabel} from '../src/labels.js';
import {buildHitTarget,pickAnnotation} from '../src/annotation_interaction.js';
const layer={id:'risk',visible:true};
const feature={id:'region',type:'region',name:'风险区',positions:[[0,0,0],[100,0,0],[100,100,0],[0,100,0]],
  style:{opacity:.8,fillOpacity:.3,sizePx:32,widthPx:4},label:{visible:true,text:'区域',opacity:.6,fontPx:12,color:'#fff',offset:[0,0]}};
test('transparency has unambiguous opaque/transparent endpoints and rejects nonfinite/out of range values',()=>{
  assert.equal(opacityFromTransparency(0),1);assert.equal(opacityFromTransparency('100'),0);assert.equal(opacityFromTransparency(25),.75);
  for(const value of [-1,101,NaN,Infinity,'oops'])assert.throws(()=>opacityFromTransparency(value),RangeError);
});
test('layer alpha composes with outline, fill and label without changing DLG or geometry/business identity',()=>{
  const before=JSON.stringify(feature),half=annotationWithOpacity(feature,.5);
  assert.equal(half.style.opacity,.4);assert.equal(half.style.fillOpacity,.15);assert.equal(half.label.opacity,.3);
  assert.equal(half.positions,feature.positions);assert.equal(JSON.stringify(feature),before);
  const restored=annotationWithOpacity(feature,1);assert.deepEqual(restored,feature);
});
test('fully transparent layer does not intercept scene clicks, even filled regions and labels',()=>{
  const invisible=annotationWithOpacity(feature,0),projected=feature.positions.map(p=>p.slice(0,2));
  const canvas={};assert.equal(drawLabel(canvas,invisible,p=>p.slice(0,2)),undefined);
  assert.equal(buildHitTarget(invisible,layer,projected),null);
  const visible=buildHitTarget(feature,layer,projected);
  assert.equal(pickAnnotation([visible],[50,50]).feature,feature);
});
test('layer alpha also affects independent visible text when geometry opacity is zero',()=>{
  const labelOnly={...feature,style:{...feature.style,opacity:0,fillOpacity:0}};
  const values=[],canvas={save(){},restore(){},measureText(){return{width:40}},fillRect(){values.push(this.globalAlpha)},fillText(){values.push(this.globalAlpha)}};
  const rendered=annotationWithOpacity(labelOnly,.25),box=drawLabel(canvas,rendered,p=>p.slice(0,2));
  assert.deepEqual(values,[.15,.15]);assert.ok(box);
  assert.equal(buildHitTarget(rendered,layer,[null],box).body,false);
});
test('model transparency updates real Three materials including base material arrays, and restores depth writes',()=>{
  const group=new THREE.Group(),one=new THREE.MeshBasicMaterial(),two=new THREE.MeshBasicMaterial();
  const mesh=new THREE.Mesh(new THREE.BufferGeometry(),[one,two]);group.add(mesh);
  applyModelOpacity(group,.4);
  for(const material of [one,two]){assert.equal(material.opacity,.4);assert.equal(material.transparent,true);assert.equal(material.depthWrite,false);}
  const version=one.version;applyModelOpacity(group,.4);assert.equal(one.version,version);
  applyModelOpacity(group,1);
  for(const material of [one,two]){assert.equal(material.opacity,1);assert.equal(material.transparent,false);assert.equal(material.depthWrite,true);}
});
test('zero alpha and unchecked scene controls hide models independently, then restore without changing checked state',()=>{
  const group=new THREE.Group();group.add(new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial()));
  applyModelOpacity(group,0);assert.equal(group.visible,false);
  applyModelOpacity(group,.8,false);assert.equal(group.visible,false);
  applyModelOpacity(group,.8,true);assert.equal(group.visible,true);
});
test('new streamed LOD meshes inherit current alpha, while base geometry/groups remain untouched',()=>{
  const group=new THREE.Group(),base=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
  base.geometry.addGroup(0,30,0);group.add(base);applyModelOpacity(group,.3);
  const newTier=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());group.add(newTier);applyModelOpacity(group,.3);
  assert.equal(base.material.opacity,.3);assert.equal(newTier.material.opacity,.3);assert.deepEqual(base.geometry.groups,[{start:0,count:30,materialIndex:0}]);
});
