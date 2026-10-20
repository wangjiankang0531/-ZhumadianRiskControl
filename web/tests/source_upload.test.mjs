import test from 'node:test';
import assert from 'node:assert/strict';
import {Group,Mesh,BoxGeometry,MeshBasicMaterial,PerspectiveCamera,Frustum,Matrix4,Vector3} from 'three';
import {uploadSourceScene} from '../src/source_upload.js';

function fixture(failure){
 const scene=new Group(),inside=new Mesh(new BoxGeometry(),new MeshBasicMaterial()),outside=new Mesh(new BoxGeometry(),new MeshBasicMaterial());outside.position.set(1000,0,0);outside.frustumCulled=false;scene.add(inside,outside);
 const prior={prior:true},target={upload:true},camera=new PerspectiveCamera(52,1,.5,100),state={current:prior,calls:0,uploadScene:null};camera.position.set(0,0,10);camera.lookAt(new Vector3());camera.updateMatrixWorld();
 const renderer={getRenderTarget:()=>state.current,setRenderTarget:t=>{if(failure==='target'&&t===target)throw Error('target failed');state.current=t;},render:(s,c)=>{state.calls++;state.uploadScene=s;assert.equal(c,camera);assert.equal(state.current,target);assert.equal(scene.parent,s);assert.equal(inside.frustumCulled,false);assert.equal(outside.frustumCulled,false);if(failure==='render')throw Error('GPU failed');}};
 return {scene,inside,outside,prior,target,camera,state,renderer};
}
for(const failure of [null,'render','target'])test(`source upload restores mixed culling flags, detached ownership and render target: ${failure??'success'}`,()=>{
 const f=fixture(failure);if(failure)assert.throws(()=>uploadSourceScene(f),/failed/);else uploadSourceScene(f);
 assert.equal(f.scene.parent,null);assert.equal(f.inside.frustumCulled,true);assert.equal(f.outside.frustumCulled,false);assert.equal(f.state.current,f.prior);assert.equal(f.state.uploadScene?.children.length??0,0);
 // The actual Three frustum again rejects an off-screen mesh whose original
 // policy was true; leave an intentionally uncullable mesh unchanged.
 f.inside.position.set(1000,0,0);f.scene.updateMatrixWorld(true);const frustum=new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(f.camera.projectionMatrix,f.camera.matrixWorldInverse));assert.equal(frustum.intersectsObject(f.inside),false);
});
test('source upload rejects live-scene ownership before any renderer mutation',()=>{const f=fixture(),parent=new Group();parent.add(f.scene);assert.throws(()=>uploadSourceScene(f),/detached/);assert.equal(f.scene.parent,parent);assert.equal(f.inside.frustumCulled,true);assert.equal(f.state.current,f.prior);assert.equal(f.state.calls,0);});
