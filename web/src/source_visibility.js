import {visibilityRegionWeights} from './visibility_region_weights.js';
import {WebGLRenderTarget,MeshBasicMaterial,ShaderMaterial,Color,Vector3,Box3,Frustum,Matrix4,DoubleSide,NoBlending,LinearSRGBColorSpace} from 'three';

const surfaceDepths=Float64Array.from({length:256},(_,bin)=>.5*120000**(bin/255));
// A comparison key only: the ray snapshot retains the original full matrices.
// Ignore roundoff from repeated OrbitControls updates, never quantize geometry.
export const visibilityCameraKey=(camera,width,height)=>JSON.stringify([camera.matrixWorld.elements.map(n=>Number(n.toPrecision(12))),camera.projectionMatrix.elements.map(n=>Number(n.toPrecision(12))),width,height]);
export function matchesVisibilityCamera(snapshot,camera,width,height){
 return snapshot?.width===width&&snapshot.height===height&&snapshot.cameraWorld.every((n,i)=>Math.abs(n-camera.matrixWorld.elements[i])<=(i>=12&&i<=14?1e-8:1e-12))&&snapshot.projectionInverse.every((n,i)=>Math.abs(n-camera.projectionMatrixInverse.elements[i])<=1e-12*(1+Math.abs(n)));
}
export function visiblePixelSamples(bytes,width,height,weights,registry){
 const total=weights.reduce((sum,n)=>sum+n,0),result=new Map();if(!(total>0))throw Error('Empty visible sample weights');
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const offset=y*width+x,id=bytes[offset*4]|bytes[offset*4+1]<<8|bytes[offset*4+2]<<16,weight=weights[offset]/total;if(!id||!weight)continue;const key=registry.get(id);if(!key)throw Error('Unknown visible sample source');if(!result.has(key))result.set(key,[]);result.get(key).push((x+.5)/width*2-1,(y+.5)/height*2-1,bytes[offset*4+3],weight);}
 return result;
}
export const visibilityKey=(root,name='')=>name?'node/'+root+'/'+name:'root/'+root;
export function encodeVisibilityId(id){if(!Number.isInteger(id)||id<0||id>0xffffff)throw Error('Invalid visibility id');return [id&255,(id>>>8)&255,(id>>>16)&255];}
export function countVisibilityPixels(bytes,width,height,weights=null){
 if(bytes.length!==width*height*4||weights&&weights.length!==width*height)throw Error('Invalid visibility raster');
 const counts=new Map(),depths=new Map(),depthBins=new Map();let total=0;
 for(let i=0;i<width*height;i++){const id=bytes[i*4]|bytes[i*4+1]<<8|bytes[i*4+2]<<16,weight=weights?.[i]??1,bin=bytes[i*4+3];if(!Number.isFinite(weight)||weight<0)throw Error('Invalid visibility weight');total+=weight;if(id&&weight>0){counts.set(id,(counts.get(id)??0)+weight);depths.set(id,Math.min(depths.get(id)??Infinity,surfaceDepths[bin]));if(!depthBins.has(id))depthBins.set(id,new Map());const bins=depthBins.get(id);bins.set(bin,(bins.get(bin)??0)+weight);}}
 return {counts,total,depths,depthBins};
}
export function visiblePixelPriority(node,weight,camera,height,visibleDepth=null){
 if(!node?.bounds_min||!(weight>0))return 0;
 const distance=visibleDepth>0?Math.max(.5,visibleDepth):Math.max(1,new Box3(new Vector3(...node.bounds_min),new Vector3(...node.bounds_max)).distanceToPoint(camera.position));
 const quality=Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*height/(2*Math.tan(camera.fov*Math.PI/360)*distance);
 return quality>6?Math.log2(1+quality/6)*weight:0;
}

// Sum the actual per-pixel quality deficit. A tiny near sliver must not apply
// its distance to the entire, mostly distant coverage of a shared source node.
export function depthWeightedPriority(node,bins,camera,height){
 if(!node?.bounds_min||!bins?.size)return 0;
 const scale=Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*height/(2*Math.tan(camera.fov*Math.PI/360));if(!Number.isFinite(scale)||scale<=0)return 0;
 let score=0;for(const [bin,weight] of bins){const quality=scale/surfaceDepths[bin];if(quality>6)score+=Math.log2(1+quality/6)*weight;}return score;
}

// A small depth-tested ID pass measures actual visible triangles, including occlusion.
// It reuses geometry buffers, restores all render state, and never draws the IDs on screen.
export class SourceVisibility {
 constructor(renderer,scene,context){this.renderer=renderer;this.scene=scene;this.context=context;this.target=new WebGLRenderTarget(96,64);this.materials=new Map();this.black=new MeshBasicMaterial({color:0,side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false});this.weights=new Map();this.depths=new Map();this.depthBins=new Map();}
 weight(root,name=''){return this.weights.get(visibilityKey(root,name))??0;}
 depth(root,name=''){return this.depths.get(visibilityKey(root,name))??null;}
 capture(root,names,camera,height){
  const state=this.visibleSnapshot;if(!state||!matchesVisibilityCamera(state,camera,state.width,height))throw Error('Visible sample camera is stale');
  const nodes=[],samples=[];
  for(const name of new Set(names)){const key=visibilityKey(root,name),rows=state.samples.get(key);if(!rows)continue;const node=state.metrics.get(key);if(!node)throw Error('Visible sample metadata missing');const index=nodes.length;nodes.push({longest_edge_p90_m:node.longest_edge_p90_m,texel_world_p90_m:node.texel_world_p90_m??0});for(let i=0;i<rows.length;i+=4)samples.push(...rows.slice(i,i+4),index);}
  return {schema:'xnby.visible_source_samples.v1',cameraKey:state.cameraKey,width:state.width,height:state.height,fov:camera.fov,near:camera.near,far:camera.far,cameraWorld:[...state.cameraWorld],projectionInverse:[...state.projectionInverse],viewMatrix:[...state.viewMatrix],nodes,samples:new Float64Array(samples)};
 }
 priority(root,node,camera,height,names=null){let score=0;for(const name of new Set(names??[node.name??'']))score+=depthWeightedPriority(node,this.depthBins.get(visibilityKey(root,name)),camera,height);return score;}
 retirementLoss(root,replacement,names,currentNodes,camera,height){
  let loss=0;for(const name of new Set(names)){const bins=this.depthBins.get(visibilityKey(root,name));if(!bins?.size)continue;const before=currentNodes.get(name)?.node;if(!before)return Infinity;loss+=Math.max(0,depthWeightedPriority(replacement,bins,camera,height)-depthWeightedPriority(before,bins,camera,height));}return loss;
 }
 sample({camera,width,height,base,catalog,residents,obscured=[],baseQuality=null,balancedRegions=false}){
  this.visibleSnapshot=null;
  const renderer=this.renderer,rw=96,rh=Math.max(16,Math.round(rw*height/width)),frustum=new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
  this.target.setSize(rw,rh);const registry=new Map(),metrics=new Map(),saved=[],used=new Set();let next=1;
  const record=(key,node)=>{const id=next++;metrics.set(key,node);if(id>0xffffff)throw Error('Visibility id overflow');registry.set(id,key);this.weights.set(key,0);used.add(key);
   let material=this.materials.get(key);if(!material){material=new ShaderMaterial({side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false,uniforms:{idColor:{value:new Color()}},vertexShader:'varying float viewDepth; void main(){vec4 viewPosition=modelViewMatrix*vec4(position,1.0);viewDepth=-viewPosition.z;gl_Position=projectionMatrix*viewPosition;}',fragmentShader:'uniform vec3 idColor; varying float viewDepth; void main(){float depth=clamp(log2(max(viewDepth,0.5)/0.5)/log2(120000.0),0.0,1.0);gl_FragColor=vec4(idColor,depth);}'});this.materials.set(key,material);}const c=encodeVisibilityId(id);material.uniforms.idColor.value.setRGB(c[0]/255,c[1]/255,c[2]/255,LinearSRGBColorSpace);return material;};
  const override=(mesh,entries)=>{saved.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible});mesh.geometry.groups=[];const materials=[];
   for(const {material,spans} of entries){const index=materials.length;materials.push(material);for(const span of spans)mesh.geometry.addGroup(span.first,span.count,index);}
   mesh.material=materials;mesh.visible=mesh.visible&&materials.length>0;
  };
  const entries=[];this.weights=new Map();this.depths=new Map();this.depthBins=new Map();
  for(const root of catalog.root_records){if(residents.has(root.tile_id))continue;const box=new Box3(new Vector3(...root.bounds_min),new Vector3(...root.bounds_max));if(!frustum.intersectsBox(box))continue;
   entries.push({material:record(visibilityKey(root.tile_id),{...root,longest_edge_p90_m:baseQuality?.edges.get(root.tile_id),texel_world_p90_m:baseQuality?.texels.get(root.tile_id)??0}),spans:root.base_spans.map(([first,count])=>({first,count}))});}
  override(base,entries);
  for(const [root,ready] of residents)if(ready.frontier){const nodes=ready.frontier.nodes,byMesh=new Map();
   for(const name of ready.frontier.visible){const {node,bundle}=nodes.get(name),material=record(visibilityKey(root,name),node);for(const span of node.spans){const mesh=bundle.meshes.get(span.part);if(!byMesh.has(mesh))byMesh.set(mesh,[]);byMesh.get(mesh).push({material,spans:[span]});}}
   for(const [mesh,entries] of byMesh)override(mesh,entries);
  }
  const contextMaterials=[];this.context.traverse(n=>{if(n.isMesh){contextMaterials.push([n,n.material]);n.material=this.black;}});
  const target=renderer.getRenderTarget(),color=renderer.getClearColor(new Color()).clone(),alpha=renderer.getClearAlpha(),autoClear=renderer.autoClear,background=this.scene.background;
  try{this.scene.background=null;renderer.autoClear=true;renderer.setRenderTarget(this.target);renderer.setClearColor(0,1);renderer.clear();renderer.render(this.scene,camera);
   const pixels=new Uint8Array(rw*rh*4);renderer.readRenderTargetPixels(this.target,0,0,rw,rh,pixels);
   const regional=visibilityRegionWeights({pixels,rasterWidth:rw,rasterHeight:rh,width,height,obscured,balanced:balancedRegions}),weights=regional.weights;
   const sampled=countVisibilityPixels(pixels,rw,rh,weights);for(const [id,count] of sampled.counts){const key=registry.get(id);if(!key)throw Error('Invalid GPU visibility color');this.weights.set(key,count/sampled.total);this.depths.set(key,sampled.depths.get(id));this.depthBins.set(key,new Map([...sampled.depthBins.get(id)].map(([bin,weight])=>[bin,weight/sampled.total])));}
   const weightedQualityDeficit=[...metrics].reduce((sum,[key,node])=>sum+depthWeightedPriority(node,this.depthBins.get(key),camera,height),0);
   this.visibleSnapshot={cameraKey:visibilityCameraKey(camera,width,height),width,height,cameraWorld:[...camera.matrixWorld.elements],projectionInverse:[...camera.projectionMatrixInverse.elements],viewMatrix:[...camera.matrixWorldInverse.elements],metrics,samples:visiblePixelSamples(pixels,rw,rh,weights,registry)};
   return {width:rw,height:rh,visibleSources:sampled.counts.size,weightedQualityDeficit,weightingPolicy:regional.policy,regions:regional.cells};
  }finally{renderer.setRenderTarget(target);renderer.setClearColor(color,alpha);renderer.autoClear=autoClear;this.scene.background=background;
   for(const {mesh,material,groups,visible} of saved){mesh.material=material;mesh.geometry.groups=groups;mesh.visible=visible;}
   for(const [mesh,material] of contextMaterials)mesh.material=material;
   for(const [key,material] of this.materials)if(!used.has(key)){material.dispose();this.materials.delete(key);}
  }
 }
 dispose(){this.target.dispose();this.black.dispose();for(const material of this.materials.values())material.dispose();this.materials.clear();}
}
