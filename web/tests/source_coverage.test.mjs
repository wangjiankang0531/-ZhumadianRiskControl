import {Scene,Group,Mesh,BufferGeometry,BufferAttribute,MeshBasicMaterial,Color,PerspectiveCamera} from 'three';
import {SourcePageBudget} from '../src/source_page_budget.js';
import test from 'node:test';import assert from 'node:assert/strict';
import {coverageInteriorLoss,coverageGroups,coverageDimensions,SourceCoverageGuard} from '../src/source_coverage.js';
test('large interior and screen-corner holes are rejected, two-pixel raster fringes are tolerated',()=>{
 const w=32,h=32,p=new Uint8Array(w*h*4);for(let i=0;i<p.length;i+=4)p[i]=255;let c=p.slice();for(let y=11;y<21;y++)for(let x=11;x<21;x++)c[(y*w+x)*4]=0;assert.equal(coverageInteriorLoss(p,c,w,h).loss,36);
 c=p.slice();for(let y=0;y<10;y++)for(let x=0;x<10;x++)c[(y*w+x)*4]=0;assert.equal(coverageInteriorLoss(p,c,w,h).loss,64);
 c=p.slice();for(let x=0;x<w;x++)c[(14*w+x)*4]=0;assert.equal(coverageInteriorLoss(p,c,w,h).loss,0);
});
test('integral mask comparison matches an independent neighborhood oracle',()=>{
 let seed=20261020,checks=0;const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
 for(let trial=0;trial<180;trial++){const w=1+Math.floor(rnd()*47),h=1+Math.floor(rnd()*31),p=new Uint8Array(w*h*4),c=p.slice();for(let i=0;i<p.length;i+=4){p[i]=(rnd()<.99)*255;c[i]=(rnd()<.35)*255;}let expected=0;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){let inside=true,child=false;for(let yy=Math.max(0,y-2);yy<Math.min(h,y+3);yy++)for(let xx=Math.max(0,x-2);xx<Math.min(w,x+3);xx++){inside&&=p[(yy*w+xx)*4]!==0;child||=c[(yy*w+xx)*4]!==0;checks++;}expected+=inside&&!child;}
  assert.equal(coverageInteriorLoss(p,c,w,h).loss,expected);
 }assert.ok(checks>1000000);
});
test('coverage parent spans partition live source triangles without filling hidden geometry',()=>{
 const groups=[{start:3,count:18,materialIndex:0},{start:24,count:6,materialIndex:0}],target=[{first:9,count:6}];assert.deepEqual(coverageGroups(groups,target,30),[{start:3,count:6,materialIndex:0},{start:9,count:6,materialIndex:1},{start:15,count:6,materialIndex:0},{start:24,count:6,materialIndex:0}]);assert.deepEqual(coverageGroups([],target,30),[]);assert.equal(coverageGroups([],target,30,{singleMaterial:true}).reduce((n,g)=>n+g.count,0),30);assert.throws(()=>coverageGroups(groups,[{first:1,count:3}],30));
});
test('coverage target color and depth storage have an explicit unchanged-budget reservation',()=>{assert.equal(coverageDimensions(1280,573).bytes,1280*573*8);assert.throws(()=>coverageDimensions(4097,2160));assert.throws(()=>coverageDimensions(1280,0));});

test('coverage success and a render failure both restore every live draw and renderer state',()=>{
 for(const fail of [false,true]){
  const scene=new Scene(),photo=new Group(),context=new Group(),candidate=new Group(),geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(new Float32Array([-1,-1,0,1,-1,0,0,1,0]),3));geometry.setIndex([0,1,2]);const material=new MeshBasicMaterial(),mesh=new Mesh(geometry,material);photo.add(mesh);candidate.add(new Mesh(geometry.clone(),new MeshBasicMaterial()));scene.add(photo,context);scene.background=new Color('#123456');const background=scene.background,groups=geometry.groups,target={original:true},ledger=new SourcePageBudget(8192);
  const renderer={target,color:new Color('#345678'),alpha:.3,autoClear:false,renders:0,getRenderTarget(){return this.target;},setRenderTarget(v){this.target=v;},getClearColor(v){return v.copy(this.color);},getClearAlpha(){return this.alpha;},setClearColor(v,a){this.color.set(v);this.alpha=a;},clear(){},render(){assert.equal(context.visible,false);this.renders++;if(fail&&this.renders===2)throw Error('injected GPU failure');},readRenderTargetPixels(t,x,y,w,h,bytes){for(let i=0;i<bytes.length;i+=4){bytes[i]=255;bytes[i+3]=255;}}};const color=renderer.color.getHex();
  const guard=new SourceCoverageGuard({renderer,scene,photoGroup:photo,contextGroup:context,reserve:r=>ledger.reserve(r)});guard.resize(16,16);assert.equal(ledger.held,2048);
  const check=()=>guard.check({camera:new PerspectiveCamera(),candidate,parentSpans:new Map([[mesh,[{first:0,count:3}]]])});if(fail)assert.throws(check,/injected GPU failure/);else assert.equal(check().loss,0);
  assert.equal(mesh.material,material);assert.equal(mesh.geometry.groups,groups);assert.equal(mesh.visible,true);assert.equal(candidate.parent,null);assert.equal(context.visible,true);assert.equal(scene.background,background);assert.equal(renderer.target,target);assert.equal(renderer.autoClear,false);assert.equal(renderer.alpha,.3);assert.equal(renderer.color.getHex(),color);guard.release();assert.equal(ledger.held,0);
 }
});
