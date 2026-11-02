import test from 'node:test';
import assert from 'node:assert/strict';
import {Scene,Mesh,BufferGeometry,Float32BufferAttribute,MeshBasicMaterial,PerspectiveCamera,Color} from 'three';
import {encodeVisibilityId,countVisibilityPixels,visiblePixelPriority,depthWeightedPriority,SourceVisibility,visiblePixelSamples,visibilityCameraKey,matchesVisibilityCamera} from '../src/source_visibility.js';

test('visibility ID raster keeps 24-bit identity and discounts obscured dashboard pixels',()=>{
 const pixels=new Uint8Array(12);pixels.set([...encodeVisibilityId(65537),255],0);pixels.set([...encodeVisibilityId(65537),255],4);pixels.set([...encodeVisibilityId(255),255],8);
 const result=countVisibilityPixels(pixels,3,1,new Float32Array([1,.25,1]));assert.equal(result.counts.get(65537),1.25);assert.equal(result.counts.get(255),1);assert.equal(result.total,2.25);
 assert.throws(()=>encodeVisibilityId(0x1000000));assert.throws(()=>countVisibilityPixels(pixels,4,1));
});
test('zero actually visible pixels suppresses an overlapping source box',()=>{
 const camera=new PerspectiveCamera(52,991/683,.5,60000);camera.position.set(0,-10,12);camera.lookAt(0,0,0);
 const node={bounds_min:[-100,-100,-100],bounds_max:[100,100,100],longest_edge_p90_m:5,texel_world_p90_m:1};
 assert.equal(visiblePixelPriority(node,0,camera,683),0);assert.ok(visiblePixelPriority(node,.5,camera,683)>visiblePixelPriority(node,.01,camera,683));
});
test('visible samples preserve GPU lower-left orientation, source ID, depth and global occlusion weights',()=>{
 const bytes=new Uint8Array([1,0,0,10,2,0,0,20,0,0,0,30,1,0,0,40]),registry=new Map([[1,'root/1'],[2,'node/2/other']]),samples=visiblePixelSamples(bytes,2,2,new Float32Array([1,.2,1,1]),registry);
 assert.equal(samples.get('root/1').length,8);assert.deepEqual(samples.get('root/1').slice(0,3),[-.5,-.5,10]);assert.deepEqual(samples.get('root/1').slice(4,7),[.5,.5,40]);assert.equal(samples.get('node/2/other').length,4);assert.ok(Math.abs(samples.get('root/1')[3]-1/3.2)<1e-8);
});
function fixture(failRead=false){
 const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute([-1,-1,0,1,-1,0,0,1,0],3));geometry.setIndex([0,1,2]);geometry.addGroup(0,3,0);
 const base=new Mesh(geometry,new MeshBasicMaterial()),context=new Scene(),ground=new Mesh(geometry,new MeshBasicMaterial());context.add(ground);const scene=new Scene();scene.background=new Color('#809ab0');scene.add(base,context);
 const state={target:{original:true},color:new Color('#123456'),alpha:.7,autoClear:false},renderer={autoClear:false,getRenderTarget:()=>state.target,setRenderTarget:v=>state.target=v,getClearColor:c=>c.copy(state.color),getClearAlpha:()=>state.alpha,setClearColor:(c,a)=>{state.color=c instanceof Color?c.clone():new Color(c);state.alpha=a;},clear(){},render(){assert.notEqual(base.material,material);assert.equal(base.geometry.groups.length,1);},readRenderTargetPixels(t,x,y,w,h,bytes){if(failRead)throw Error('read failed');for(let i=0;i<w*h;i++)bytes.set([1,0,0,255],i*4);}};
 const material=base.material,groups=geometry.groups,background=scene.background,groundMaterial=ground.material,target=state.target,color=state.color.clone(),camera=new PerspectiveCamera(52,1,.5,100);camera.position.set(0,0,5);camera.lookAt(0,0,0);camera.updateMatrixWorld();
 const sampler=new SourceVisibility(renderer,scene,context),args={camera,width:991,height:683,base,catalog:{root_records:[{tile_id:1,bounds_min:[-1,-1,0],bounds_max:[1,1,0],base_spans:[[0,3]]}]},residents:new Map()};
 return {sampler,args,check:()=>{assert.equal(base.material,material);assert.equal(geometry.groups,groups);assert.equal(ground.material,groundMaterial);assert.equal(scene.background,background);assert.equal(state.target,target);assert.ok(state.color.equals(color));assert.equal(state.alpha,.7);assert.equal(renderer.autoClear,false);}};
}
test('ID pass restores genuine draw groups, materials, context, target and clear state',()=>{const f=fixture();assert.equal(f.sampler.sample(f.args).visibleSources,1);assert.equal(f.sampler.weight(1),1);f.check();f.sampler.dispose();});
test('readback failure restores the visible rendering state before bounds fallback',()=>{const f=fixture(true);assert.throws(()=>f.sampler.sample(f.args),/read failed/);f.check();f.sampler.dispose();});
test('gain snapshots copy only genuinely visible source samples and reject a moved camera',()=>{
 const f=fixture();f.args.baseQuality={edges:new Map([[1,10]]),texels:new Map([[1,0]])};f.sampler.sample(f.args);const snapshot=f.sampler.capture(1,[''],f.args.camera,683);assert.ok(snapshot.samples.length>0);assert.equal(snapshot.nodes.length,1);snapshot.samples[0]=999;snapshot.cameraWorld[12]=999;
 const again=f.sampler.capture(1,[''],f.args.camera,683);assert.notEqual(again.samples[0],999);assert.notEqual(again.cameraWorld[12],999);assert.equal(f.sampler.capture(2,[''],f.args.camera,683).samples.length,0);
 f.args.camera.position.x++;f.args.camera.updateMatrixWorld();assert.throws(()=>f.sampler.capture(1,[''],f.args.camera,683),/stale/);f.sampler.dispose();
});
test('camera comparison ignores floating roundoff while preserving full ray matrices and real movement',()=>{
 const f=fixture();f.args.camera.position.set(-404.14709360453753,-2083.0695566594954,201.44926109873967);f.args.camera.updateMatrixWorld();const key=visibilityCameraKey(f.args.camera,991,683),exact=f.args.camera.matrixWorld.elements[14];
 f.args.camera.position.z+=1e-12;f.args.camera.updateMatrixWorld();assert.equal(visibilityCameraKey(f.args.camera,991,683),key);assert.notEqual(f.args.camera.matrixWorld.elements[14],exact);
 f.args.camera.position.x+=.001;f.args.camera.updateMatrixWorld();assert.notEqual(visibilityCameraKey(f.args.camera,991,683),key);f.sampler.dispose();
});
test('pose comparison uses bounded matrix differences even across a rounded-key boundary',()=>{
 const camera=new PerspectiveCamera(52,1,.5,60000);camera.position.set(1.0000000000049,0,5);camera.updateMatrixWorld();const key=visibilityCameraKey(camera,991,683),snapshot={width:991,height:683,cameraWorld:[...camera.matrixWorld.elements],projectionInverse:[...camera.projectionMatrixInverse.elements]};
 camera.position.x+=.0000000000002;camera.updateMatrixWorld();assert.notEqual(visibilityCameraKey(camera,991,683),key);assert.equal(matchesVisibilityCamera(snapshot,camera,991,683),true);
 camera.position.x+=.001;camera.updateMatrixWorld();assert.equal(matchesVisibilityCamera(snapshot,camera,991,683),false);assert.equal(matchesVisibilityCamera(snapshot,camera,992,683),false);
});


test('logarithmic depth distinguishes a nearby visible surface from a camera-containing box',()=>{
 const camera=new PerspectiveCamera(52,1,.5,60000);camera.position.set(0,0,0);
 const node={bounds_min:[-100,-100,-100],bounds_max:[100,100,100],longest_edge_p90_m:5,texel_world_p90_m:1};
 assert.ok(visiblePixelPriority(node,.2,camera,683,10)>visiblePixelPriority(node,.2,camera,683,100));
 const bytes=new Uint8Array([1,0,0,128]);const sample=countVisibilityPixels(bytes,1,1);assert.ok(sample.depths.get(1)>100&&sample.depths.get(1)<300);
});


test('depth histogram conserves weighted visible pixels and excludes background or zero weights',()=>{
 const bytes=new Uint8Array([1,0,0,0,1,0,0,255,2,0,0,128,0,0,0,255]);const result=countVisibilityPixels(bytes,4,1,new Float32Array([1,.25,0,1]));
 assert.deepEqual([...result.depthBins.get(1)],[[0,1],[255,.25]]);assert.equal(result.depthBins.has(2),false);assert.equal(result.counts.get(1),1.25);assert.equal(result.total,2.25);
 assert.throws(()=>countVisibilityPixels(bytes,4,1,new Float32Array([1,-1,1,1])),/weight/);
});

test('a tiny near sliver cannot lend its depth to a mostly distant source surface',()=>{
 const camera=new PerspectiveCamera(52,1,.5,60000),node={bounds_min:[-1,-1,-1],bounds_max:[1,1,1],longest_edge_p90_m:1,texel_world_p90_m:0};
 const fullNear=visiblePixelPriority(node,1,camera,1000,.5),sliver=depthWeightedPriority(node,new Map([[0,.01],[255,.99]]),camera,1000),other=depthWeightedPriority(node,new Map([[64,.2]]),camera,1000);
 assert.ok(Math.abs(sliver-fullNear*.01)<1e-12);assert.ok(fullNear>other);assert.ok(sliver<other);
});

test('uniform-depth coverage agrees with the existing surface projection metric',()=>{
 const camera=new PerspectiveCamera(52,1,.5,60000),node={bounds_min:[-1,-1,-1],bounds_max:[1,1,1],longest_edge_p90_m:5,texel_world_p90_m:.1},bin=96,depth=.5*120000**(bin/255);
 assert.ok(Math.abs(depthWeightedPriority(node,new Map([[bin,.3]]),camera,683)-visiblePixelPriority(node,.3,camera,683,depth))<1e-12);
});

test('parent eviction sums disjoint child depth coverage without using a global nearest sample',()=>{
 const f=fixture(),node={name:'parent',bounds_min:[-1,-1,-1],bounds_max:[1,1,1],longest_edge_p90_m:1,texel_world_p90_m:0};
 f.sampler.depthBins.set('node/1/a',new Map([[0,.01],[255,.49]]));f.sampler.depthBins.set('node/1/b',new Map([[64,.2]]));
 const merged=depthWeightedPriority(node,new Map([[0,.01],[255,.49],[64,.2]]),f.args.camera,683);
 assert.ok(Math.abs(f.sampler.priority(1,node,f.args.camera,683,['a','b','a','hidden'])-merged)<1e-12);assert.equal(f.sampler.priority(1,node,f.args.camera,683,['hidden']),0);f.sampler.dispose();
});

test('rendered quality audit uses the same weighted depth samples and restores scene state',()=>{
 const f=fixture();f.args.baseQuality={edges:new Map([[1,1000]]),texels:new Map([[1,0]])};const stats=f.sampler.sample(f.args),node={...f.args.catalog.root_records[0],longest_edge_p90_m:1000,texel_world_p90_m:0};
 const expected=visiblePixelPriority(node,1,f.args.camera,683,60000);assert.ok(expected>0);assert.ok(Math.abs(stats.weightedQualityDeficit-expected)<1e-12);assert.ok(Math.abs(f.sampler.priority(1,node,f.args.camera,683)-expected)<1e-12);f.check();f.sampler.dispose();
});

test('retirement measures the marginal loss against the current visible cut',()=>{
 const f=fixture(),camera=f.args.camera,parent={name:'parent',bounds_min:[-1,-1,-1],bounds_max:[1,1,1],longest_edge_p90_m:5,texel_world_p90_m:0},child={...parent,name:'child',longest_edge_p90_m:2};
 f.sampler.depthBins.set('node/1/child',new Map([[96,.3]]));const nodes=new Map([['child',{node:child}]]);
 const expected=f.sampler.priority(1,parent,camera,683,['child'])-f.sampler.priority(1,child,camera,683);
 assert.ok(expected>0);assert.ok(Math.abs(f.sampler.retirementLoss(1,parent,['child'],nodes,camera,683)-expected)<1e-12);
 assert.equal(f.sampler.retirementLoss(1,child,['child'],nodes,camera,683),0);assert.equal(f.sampler.retirementLoss(1,parent,['child'],new Map(),camera,683),Infinity);f.sampler.dispose();
});

test('optional precise pass uses the same target and restores modes, groups and immutable captures',()=>{const f=fixture();f.sampler.preciseDepth=true;f.args.baseQuality={edges:new Map([[1,10]]),texels:new Map([[1,0]])};let reads=0;const code=Math.round(128/255*16777215);f.sampler.renderer.readRenderTargetPixels=(t,x,y,w,h,bytes)=>{reads++;for(let i=0;i<w*h;i++)bytes.set(reads===1?[1,0,0,128]:[code&255,code>>8&255,code>>16&255,255],i*4);};f.sampler.sample(f.args);assert.equal(reads,2);const s=f.sampler.capture(1,[''],f.args.camera,683);assert.equal(s.surfaceDepths.length,s.samples.length/5);assert.ok(s.surfaceDepths.length>0);s.surfaceDepths[0]=-1;assert.ok(f.sampler.capture(1,[''],f.args.camera,683).surfaceDepths[0]>0);assert.equal([...f.sampler.materials.values()][0].uniforms.captureDepth.value,0);f.check();f.sampler.dispose();});
test('a failed precise readback restores both depth mode and the real scene before propagating',()=>{const f=fixture();f.sampler.preciseDepth=true;let reads=0;f.sampler.renderer.readRenderTargetPixels=(t,x,y,w,h,bytes)=>{if(++reads===2)throw Error('precise read failed');for(let i=0;i<w*h;i++)bytes.set([1,0,0,128],i*4);};assert.throws(()=>f.sampler.sample(f.args),/precise read failed/);assert.equal([...f.sampler.materials.values()][0].uniforms.captureDepth.value,0);f.check();f.sampler.dispose();});

test('switching the optional depth policy invalidates old ID materials and requires a fresh snapshot',()=>{const f=fixture();f.sampler.sample(f.args);const old=[...f.sampler.materials.values()][0];let disposed=0;old.addEventListener('dispose',()=>disposed++);assert.equal(f.sampler.setPreciseDepth(false),false);assert.equal(disposed,0);assert.equal(f.sampler.setPreciseDepth(true),true);assert.equal(disposed,1);assert.equal(f.sampler.materials.size,0);assert.equal(f.sampler.visibleSnapshot,null);assert.throws(()=>f.sampler.capture(1,[''],f.args.camera,683),/stale/);assert.equal(f.sampler.setPreciseDepth(false),true);assert.throws(()=>f.sampler.setPreciseDepth(1),/policy/);f.check();f.sampler.dispose();});
