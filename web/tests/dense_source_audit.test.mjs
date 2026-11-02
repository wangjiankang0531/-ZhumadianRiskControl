import test from 'node:test';import assert from 'node:assert/strict';
import {Scene,Group,Mesh,BoxGeometry,MeshBasicMaterial,PerspectiveCamera,Color,Vector4} from 'three';
import {auditDenseSource} from '../src/dense_source_audit.js';
import {SourcePageBudget} from '../src/source_page_budget.js';

function fixture({throwSample=false,mismatch=false,limit=10_000_000}={}){
 const width=97,height=65,scene=new Scene(),context=new Group(),group=new Group(),base=new Mesh(new BoxGeometry(),new MeshBasicMaterial());scene.add(base,context,group);
 const material=base.material,groups=base.geometry.groups,camera=new PerspectiveCamera(52,width/height,.5,60000);camera.updateMatrixWorld();
 const viewport=new Vector4(0,0,width,height),scissor=new Vector4(1,2,3,4),color=new Color(.1,.2,.3),info={calls:11,triangles:17};
 const renderer={domElement:{width,height},info:{render:info},autoClear:false,getRenderTarget:()=>null,getScissorTest:()=>false,getContext:()=>({VIEWPORT:1,getParameter:()=>[0,0,width,height]}),getViewport:v=>v.copy(viewport),getScissor:v=>v.copy(scissor),getClearColor:v=>v.copy(color),getClearAlpha:()=>.3,setRenderTarget(){},setViewport(v){viewport.copy(v);},setScissor(v){scissor.copy(v);},setScissorTest(){},setClearColor(v){color.copy(v);}};
 let disposed=0,calls=0;
 const visibilityFactory=()=>({dispose(){disposed++;},sample({raster,viewport:v,residents,readback}){
  calls++;if(throwSample){base.material=null;base.geometry.groups=[];base.visible=false;group.visible=false;renderer.autoClear=true;throw Error('injected setup failure');}
  const pixels=new Uint8Array(raster.width*raster.height*4),depthPixels=new Uint8Array(pixels.length),key=residents.size?'node/1/fine':'root/1';
  const code=Math.round(Math.log(100/.5)/Math.log(120000)*16777215),bin=Math.round(code/16777215*255);
  for(let y=0;y<raster.height;y++)for(let x=0;x<raster.width;x++){const off=(y*raster.width+x)*4,gx=x-v.x,gy=height-1-(y-v.y);if(gx===0&&gy===0&&residents.size)continue;pixels[off]=1;pixels[off+3]=bin;depthPixels[off]=code&255;depthPixels[off+1]=(code>>8)&255;depthPixels[off+2]=code>>16;depthPixels[off+3]=255;}
  if(mismatch&&calls===9)pixels[4]=0;
  return readback({pixels,depthPixels,registry:new Map([[1,key]]),metrics:new Map([[key,{longest_edge_p90_m:100,texel_world_p90_m:.1}]])});
 }});
 const ledger=new SourcePageBudget(limit),args={renderer,scene,context,base,catalog:{root_records:[]},residents:new Map([[1,{group}]]),camera,baseQuality:{edges:new Map(),texels:new Map()},cssWidth:width,cssHeight:height,obscured:[{left:0,right:10,top:0,bottom:65}],ledger,reference:true,visibilityFactory};
 return {args,check(){assert.equal(base.material,material);assert.equal(base.geometry.groups,groups);assert.equal(base.visible,true);assert.equal(group.visible,true);assert.equal(renderer.autoClear,false);assert.deepEqual(info,{calls:11,triangles:17});assert.equal(ledger.held,0);},get disposed(){return disposed;},get calls(){return calls;}};
}
test('dense audit counts all pixels and exposed cells, detects relative coverage and matches an independent full target',()=>{const f=fixture(),r=auditDenseSource(f.args);assert.equal(r.pixels,6305);assert.equal(r.full.reduce((s,c)=>s+c.pixels,0),6305);assert.equal(r.full.reduce((s,c)=>s+c.detail,0),6304);assert.equal(r.exposed.reduce((s,c)=>s+c.pixels,0),87*65);assert.equal(r.coverage.rawLoss,1);assert.equal(r.coverage.exposed.rawLoss,0);assert.equal(r.reference.status,'matched');assert.equal(r.reference.mismatches,0);assert.equal(r.roots[0].over,6304);assert.equal(f.calls,9);assert.equal(f.disposed,2);f.check();});
test('full target disagreement is retained as a mismatch, never normalized into a pass',()=>{const f=fixture({mismatch:true}),r=auditDenseSource(f.args);assert.equal(r.reference.status,'mismatch');assert.equal(r.reference.mismatches,1);assert.equal(r.reference.examples.length,1);f.check();});
test('outer restoration recovers scene mutation even when the visibility setup throws before its own finally',()=>{const f=fixture({throwSample:true});assert.throws(()=>auditDenseSource(f.args),/injected setup/);assert.equal(f.disposed,1);f.check();});
test('budget exhaustion refuses full reference while preserving tiled evidence and releases the small target',()=>{const f=fixture({limit:49152}),r=auditDenseSource(f.args);assert.equal(r.reference.status,'refused');assert.equal(r.pixels,6305);assert.equal(f.calls,8);f.check();});
test('unaffordable tile target rejects before probe creation or scene mutation',()=>{const f=fixture({limit:49151});assert.throws(()=>auditDenseSource(f.args),/budget exceeded/);assert.equal(f.disposed,0);assert.equal(f.calls,0);f.check();});
