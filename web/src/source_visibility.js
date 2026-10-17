import {WebGLRenderTarget,MeshBasicMaterial,ShaderMaterial,Color,Vector3,Box3,Frustum,Matrix4,DoubleSide,NoBlending,LinearSRGBColorSpace} from 'three';

const surfaceDepths=Float64Array.from({length:256},(_,bin)=>.5*120000**(bin/255));
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
 priority(root,node,camera,height,names=null){let score=0;for(const name of new Set(names??[node.name??'']))score+=depthWeightedPriority(node,this.depthBins.get(visibilityKey(root,name)),camera,height);return score;}
 sample({camera,width,height,base,catalog,residents,obscured=[],baseQuality=null}){
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
   const pixels=new Uint8Array(rw*rh*4),weights=new Float32Array(rw*rh);renderer.readRenderTargetPixels(this.target,0,0,rw,rh,pixels);
   for(let y=0;y<rh;y++)for(let x=0;x<rw;x++){const px=(x+.5)*width/rw,py=(rh-y-.5)*height/rh;weights[y*rw+x]=obscured.some(r=>px>=r.left&&px<r.right&&py>=r.top&&py<r.bottom)?.2:1;}
   const sampled=countVisibilityPixels(pixels,rw,rh,weights);for(const [id,count] of sampled.counts){const key=registry.get(id);if(!key)throw Error('Invalid GPU visibility color');this.weights.set(key,count/sampled.total);this.depths.set(key,sampled.depths.get(id));this.depthBins.set(key,new Map([...sampled.depthBins.get(id)].map(([bin,weight])=>[bin,weight/sampled.total])));}
   const weightedQualityDeficit=[...metrics].reduce((sum,[key,node])=>sum+depthWeightedPriority(node,this.depthBins.get(key),camera,height),0);
   return {width:rw,height:rh,visibleSources:sampled.counts.size,weightedQualityDeficit};
  }finally{renderer.setRenderTarget(target);renderer.setClearColor(color,alpha);renderer.autoClear=autoClear;this.scene.background=background;
   for(const {mesh,material,groups,visible} of saved){mesh.material=material;mesh.geometry.groups=groups;mesh.visible=visible;}
   for(const [mesh,material] of contextMaterials)mesh.material=material;
   for(const [key,material] of this.materials)if(!used.has(key)){material.dispose();this.materials.delete(key);}
  }
 }
 dispose(){this.target.dispose();this.black.dispose();for(const material of this.materials.values())material.dispose();this.materials.clear();}
}
