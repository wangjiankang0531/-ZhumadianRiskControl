import test from 'node:test';import assert from 'node:assert/strict';
import {Scene,Group,Mesh,BufferGeometry,BufferAttribute,MeshBasicMaterial,PerspectiveCamera,Vector3,Color} from 'three';
import {coverageRegion} from '../src/source_coverage_region.js';
import {coverageInteriorLoss,SourceCoverageGuard} from '../src/source_coverage.js';
import {SourcePageBudget} from '../src/source_page_budget.js';
const camera=()=>{const c=new PerspectiveCamera(52,1,.5,100000);c.position.set(0,0,10);c.lookAt(new Vector3());c.updateMatrixWorld(true);return c;};
function meshFor(values=[-1,-1,0,1,-1,0,0,1,0]){const g=new BufferGeometry();g.setAttribute('position',new BufferAttribute(new Float32Array(values),3));g.setIndex(Array.from({length:values.length/3},(_,i)=>i));return new Mesh(g,new MeshBasicMaterial());}
const request=(mesh,c=camera(),width=512,height=512,spans=[{first:0,count:3}])=>({camera:c,parentSpans:new Map([[mesh,spans]]),width,height});
function crop(mask,fullWidth,r){const out=new Uint8Array(r.width*r.height*4);for(let y=0;y<r.height;y++)out.set(mask.subarray(((r.y+y)*fullWidth+r.x)*4,((r.y+y)*fullWidth+r.x+r.width)*4),y*r.width*4);return out;}

test('coverage region uses exact parent index spans, ignores other geometry, and includes four pixels of padding',()=>{const mesh=meshFor([-1,-1,0,1,-1,0,0,1,0,10000,10000,0,11000,10000,0,10000,11000,0]),r=coverageRegion(request(mesh));assert.equal(r.reason,'original_parent_span_bounds');assert.ok(r.pixels<r.fullPixels/10);for(let i=0;i<3;i++){const p=new Vector3().fromBufferAttribute(mesh.geometry.attributes.position,i).project(camera());const x=(p.x+1)*256,y=(p.y+1)*256;assert.ok(x>=r.x+3&&x<r.x+r.width-3&&y>=r.y+3&&y<r.y+r.height-3);}assert.equal(r.pixels,r.width*r.height);});

test('near-plane crossings, unsupported deformation, empty spans and invalid geometry conservatively use full viewport',()=>{const c=camera();c.position.set(0,0,0);c.lookAt(0,0,-1);c.updateMatrixWorld(true);const m=meshFor([-1,-1,-.25,1,-1,-2,0,1,-2]);assert.equal(coverageRegion(request(m,c)).reason,'near_plane_or_numerical');m.geometry.morphAttributes.position=[m.geometry.attributes.position];assert.equal(coverageRegion(request(m)).reason,'unsupported_parent_geometry');delete m.geometry.morphAttributes.position;assert.equal(coverageRegion({...request(m),parentSpans:new Map()}).pixels,512*512);assert.equal(coverageRegion(request(m,c,512,512,[{first:1,count:3}])).pixels,512*512);assert.throws(()=>coverageRegion(request(m,c,4097,512)));});

test('parent bound cache follows actual position and index upload versions',()=>{const m=meshFor([-1,-1,0,1,-1,0,0,1,0,3,-1,0,5,-1,0,4,1,0]),a=coverageRegion(request(m));m.geometry.attributes.position.setX(0,-3);m.geometry.attributes.position.needsUpdate=true;const b=coverageRegion(request(m));assert.ok(b.x<a.x);m.geometry.index.set([3,4,5],0);m.geometry.index.needsUpdate=true;const d=coverageRegion(request(m));assert.ok(d.x>b.x);});

test('projected bounds contain independently projected random triangle interiors and float32 shader positions',()=>{
 let seed=4931,points=0;const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32),f=Math.fround;
 const gpuDot=(e,row,v)=>{let n=f(e[row]*v[0]);for(let k=1;k<4;k++)n=f(n+f(e[k*4+row]*v[k]));return n;};
 for(let trial=0;trial<240;trial++){const c=camera(),m=meshFor();m.position.set((rnd()-.5)*8,(rnd()-.5)*8,(rnd()-.5)*12);m.rotation.set(rnd()*3,rnd()*3,rnd()*3);m.scale.set(.1+rnd()*3,.1+rnd()*3,.1+rnd()*3);const parent=new Group();parent.position.set(100000,200000,0);parent.add(m);c.position.add(parent.position);c.lookAt(parent.position);c.updateMatrixWorld(true);parent.updateMatrixWorld(true);const q=request(m,c,640,480),r=coverageRegion(q);
  for(let k=0;k<80;k++){let u=rnd(),v=rnd();if(u+v>1){u=1-u;v=1-v;}const local=new Vector3(-1+2*u+v,-1+2*v,0),p=local.clone().applyMatrix4(m.matrixWorld).project(c);if(p.z>=-1&&p.z<=1&&p.x>=-1&&p.x<=1&&p.y>=-1&&p.y<=1){const x=(p.x+1)*320,y=(p.y+1)*240;assert.ok(x>=r.x&&x<=r.x+r.width&&y>=r.y&&y<=r.y+r.height);points++;}
   m.modelViewMatrix.multiplyMatrices(c.matrixWorldInverse,m.matrixWorld);const mv=m.modelViewMatrix.elements.map(f),pr=c.projectionMatrix.elements.map(f),lv=[f(local.x),f(local.y),0,1],vp=[0,1,2,3].map(row=>gpuDot(mv,row,lv)),clip=[0,1,2,3].map(row=>gpuDot(pr,row,vp));if(clip[3]>0&&Math.abs(clip[2])<=clip[3]){const x=(clip[0]/clip[3]+1)*320,y=(clip[1]/clip[3]+1)*240;if(x>=0&&x<=640&&y>=0&&y<=480)assert.ok(x>=r.x&&x<=r.x+r.width&&y>=r.y&&y<=r.y+r.height);}
  }
 }assert.ok(points>10000);
});

test('cropped two-pixel criterion exactly matches full masks at viewport corners and arbitrary padded regions',()=>{
 let seed=811,losses=0;const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
 for(let trial=0;trial<400;trial++){const width=31+Math.floor(rnd()*97),height=29+Math.floor(rnd()*67),x0=trial%4===0?0:5+Math.floor(rnd()*8),y0=trial%5===0?0:5+Math.floor(rnd()*8),x1=trial%4===1?width:width-5-Math.floor(rnd()*6),y1=trial%5===1?height:height-5-Math.floor(rnd()*6),p=new Uint8Array(width*height*4),c=p.slice();for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++)p[(y*width+x)*4]=255;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)c[(y*width+x)*4]=(rnd()<.03)*255;
  const r={x:Math.max(0,x0-4),y:Math.max(0,y0-4),width:Math.min(width,x1+4)-Math.max(0,x0-4),height:Math.min(height,y1+4)-Math.max(0,y0-4)},expected=coverageInteriorLoss(p,c,width,height),actual=coverageInteriorLoss(crop(p,width,r),crop(c,width,r),r.width,r.height);assert.deepEqual(actual,expected);losses+=actual.loss;
 }assert.ok(losses>1000);
});

test('regional GPU reads use full projection with target scissor, compare full reference and restore target state',()=>{
 for(const failure of ['none','read','mismatch']){const scene=new Scene(),photo=new Group(),context=new Group(),parent=meshFor(),candidate=new Group();scene.add(photo,context);photo.add(parent);candidate.add(meshFor());const c=camera(),width=128,height=128,full=new Uint8Array(width*height*4),after=full.slice(),r=coverageRegion(request(parent,c,width,height));for(let y=56;y<72;y++)for(let x=56;x<72;x++){full[(y*width+x)*4]=255;after[(y*width+x)*4]=255;}for(let y=59;y<69;y++)for(let x=59;x<69;x++)after[(y*width+x)*4]=0;
  const ledger=new SourcePageBudget(200000),prior={id:'prior'},renderer={target:prior,color:new Color(0x123456),alpha:.4,autoClear:false,renders:0,reads:[],getRenderTarget(){return this.target;},setRenderTarget(t){this.target=t;},getClearColor(v){return v.copy(this.color);},getClearAlpha(){return this.alpha;},setClearColor(v,a){this.color.set(v);this.alpha=a;},clear(){},render(){this.renders++;assert.equal(context.visible,false);},readRenderTargetPixels(target,x,y,w,h,bytes){this.reads.push([x,y,w,h]);assert.equal(target.scissorTest,true);assert.deepEqual(target.scissor.toArray(),[x,y,w,h]);if(failure==='read'&&this.reads.length===2)throw Error('injected read failure');bytes.set(crop(this.renders%2?full:after,width,{x,y,width:w,height:h}));if(failure==='mismatch'&&w===width)bytes[0]=255;}};
  const guard=new SourceCoverageGuard({renderer,scene,photoGroup:photo,contextGroup:context,reserve:r=>ledger.reserve(r),reference:true});guard.resize(width,height);const originalScissor=guard.target.scissor.clone(),call=()=>guard.check({camera:c,candidate,parentSpans:new Map([[parent,[{first:0,count:3}]]])});
  if(failure==='none'){const out=call();assert.equal(out.loss,36);assert.deepEqual(out.fullReference,{loss:36,parentPixels:256});assert.equal(out.region.pixels,r.pixels);assert.ok(out.readbackBytes<width*height*8);assert.equal(guard.referenceChecks,1);assert.equal(guard.referenceMismatches,0);assert.equal(renderer.reads.length,4);}else assert.throws(call,failure==='read'?/injected read/:/differs from full/);
  assert.equal(candidate.parent,null);assert.equal(parent.visible,true);assert.equal(renderer.target,prior);assert.equal(renderer.alpha,.4);assert.equal(renderer.autoClear,false);assert.equal(context.visible,true);assert.equal(guard.target.scissorTest,false);assert.deepEqual(guard.target.scissor.toArray(),originalScissor.toArray());guard.release();assert.equal(ledger.held,0);
 }
});
