import {validateRuntimeSourceTexture,sourcePageGeometryBytes} from './prepared_source_page.js';
import {webSourceGeometryBytes,validateLoadedSourceGeometry} from './source_geometry_layout.js';
import {sourceRestorationFootprint} from './source_page_budget.js';
import {Vector3,Box3,Frustum,Matrix4,ClampToEdgeWrapping} from 'three';

export function validateSourcePart(part,mesh){if(!mesh?.geometry?.index||mesh.geometry.index.count!==part.indices||mesh.geometry.attributes.position.count!==part.vertices||!/^part_\d{3}$/.test(part.directory)||!Number.isFinite(part.gpu_payload_bytes)||part.gpu_payload_bytes<=0||part.gpu_payload_bytes>32*1048576)throw Error('源模型分批不一致');
    const side=part.atlas_size,texture=(Array.isArray(mesh.material)?mesh.material[0]:mesh.material)?.map,image=texture?.source?.data;
    const rectangular=['edge_clamped_rect_v1','edge_packed_rect_v1'].includes(part.atlas_layout_policy);
    if(Object.hasOwn(part,'atlas_extent')!==rectangular)throw Error('矩形源纹理需要显式格式');
    const extent=rectangular?part.atlas_extent:[side,side];
    const bounded=Array.isArray(extent)&&extent.length===2&&extent.every(n=>Number.isInteger(n)&&n>=16&&n<=2048&&n%8===0)&&Math.max(...extent)===side;
    const declared=['tight_square_gutter4_v1','edge_clamped_square_v1','edge_clamped_rect_v1','edge_packed_rect_v1'].includes(part.atlas_layout_policy);
    if(!bounded||(![1024,2048].includes(side)&&!declared)||image?.width!==extent[0]||image?.height!==extent[1])throw Error('源纹理尺寸不一致');
    if(['edge_clamped_square_v1','edge_clamped_rect_v1','edge_packed_rect_v1'].includes(part.atlas_layout_policy)&&(texture.wrapS!==ClampToEdgeWrapping||texture.wrapT!==ClampToEdgeWrapping))throw Error('源纹理采样方式不一致');
    let textureBytes=0,w=extent[0],h=extent[1];if(part.runtime_texture){validateLoadedSourceGeometry(mesh.geometry,part);textureBytes=validateRuntimeSourceTexture(part,texture);}else{if(part.source_gpu_payload_bytes!==undefined||texture?.isCompressedTexture)throw Error('未协商压缩源页');for(;;){textureBytes+=w*h*4;if(w===1&&h===1)break;w=Math.max(1,Math.floor(w/2));h=Math.max(1,Math.floor(h/2));}}
    if(part.gpu_payload_bytes!==(part.runtime_texture?webSourceGeometryBytes(part):sourcePageGeometryBytes(part))+textureBytes)throw Error('实际纹理及几何资源账目不一致');
}

function retireSourceGpu(mesh){if(mesh.userData.sourceGpuResident===false)return;mesh.geometry.dispose();const material=mesh.userData.sourceMaterial??(Array.isArray(mesh.material)?mesh.material[0]:mesh.material);material.map?.dispose();material.dispose();mesh.userData.sourceGpuResident=false;}

export function validateSourceBundle(marker,meshes){
  if(!Array.isArray(marker.source_nodes)||!marker.source_nodes.length||!Array.isArray(marker.parts)||!marker.parts.length||marker.parts.length>64)throw Error('源节点信息不完整');
  const names=new Set(),ownership=new Map(marker.parts.map(p=>[p.directory,[]]));let total=0;
  for(const node of marker.source_nodes){
    if(typeof node.name!=='string'||names.has(node.name)||!Array.isArray(node.children)||new Set(node.children).size!==node.children.length||!Number.isInteger(node.depth)||node.depth<0||!Number.isInteger(node.triangles)||node.triangles<0||!Number.isFinite(node.longest_edge_p90_m)||!Number.isFinite(node.texel_world_p90_m)||node.longest_edge_p90_m<0||node.texel_world_p90_m<0)throw Error('源节点身份无效');
    if(node.triangles&&(!Array.isArray(node.bounds_min)||!Array.isArray(node.bounds_max)||node.bounds_min.length!==3||node.bounds_max.length!==3||node.bounds_min.some((v,i)=>!Number.isFinite(v)||!Number.isFinite(node.bounds_max[i])||v>node.bounds_max[i])))throw Error('源节点包围盒无效');names.add(node.name);let count=0;
    for(const span of node.spans??[]){if(!ownership.has(span.part)||!Number.isInteger(span.first)||!Number.isInteger(span.count)||span.first<0||span.count<=0||span.first%3||span.count%3)throw Error('源索引跨度无效');ownership.get(span.part).push(span);count+=span.count;}
    if(count!==node.triangles*3)throw Error('源三角形归属不一致');total+=count;
  }
  let payload=0;
  for(const part of marker.parts){validateSourcePart(part,meshes.get(part.directory));
    let first=0;for(const span of ownership.get(part.directory).sort((a,b)=>a.first-b.first)){if(span.first!==first)throw Error('源索引存在重叠或孔洞');first+=span.count;}
    if(first!==part.indices)throw Error('源索引覆盖不完整');payload+=part.gpu_payload_bytes;
  }
  if(total!==marker.indices||payload!==marker.gpu_payload_bytes)throw Error('源模型资源账目不一致');
}

// Initial cut was audited against the complete source forest by the converter.
// Every later edit replaces exactly one visible parent with all direct children.
export class SourceFrontier {
  constructor(marker,meshes){validateSourceBundle(marker,meshes);this.bundles=new Map([['$root',{marker,meshes}]]);this.visible=new Set(marker.source_nodes.map(n=>n.name));this.pending=null;this.sequence=0;this.cutVersion=0;}
  get bytes(){return this.bytesFor(this.visible);}
  get retainedPayloadBytes(){return [...this.bundles.values()].reduce((n,b)=>n+b.marker.parts.filter(p=>b.meshes.has(p.directory)).reduce((sum,p)=>sum+p.gpu_payload_bytes,0),0);}
  bytesFor(visible,bundles=this.bundles){let total=0;for(const bundle of bundles.values()){const active=new Set(bundle.marker.source_nodes.filter(n=>visible.has(n.name)).flatMap(n=>n.spans.map(s=>s.part)));for(const part of bundle.marker.parts)if(active.has(part.directory))total+=part.gpu_payload_bytes;}return total;}
  copyForPlanning(){return Object.assign(Object.create(Object.getPrototypeOf(this)),this,{bundles:new Map(this.bundles),visible:new Set(this.visible),pending:null,planningOnly:true});}
  rollbackPlan(parent){
    if(!this.bundles.has(parent))return null;
    const nodes=this.nodes,subtree=new Set();const visit=name=>{if(subtree.has(name))return;subtree.add(name);for(const child of nodes.get(name)?.node.children??[])visit(child);};visit(parent);
    const visible=new Set(this.visible);for(const name of subtree)visible.delete(name);visible.add(parent);
    const bundles=new Map([...this.bundles].filter(([key])=>!subtree.has(key)));
    const missingPages=[];for(const bundle of bundles.values()){const needed=new Set(bundle.marker.source_nodes.filter(n=>visible.has(n.name)).flatMap(n=>n.spans.map(s=>s.part)));for(const part of bundle.marker.parts)if(needed.has(part.directory)&&!bundle.meshes.has(part.directory))missingPages.push({bundle,part});}
    return {visible,bundles,subtree,missingPages,bytes:this.bytesFor(visible,bundles)};
  }
  get nodes(){const out=new Map();for(const bundle of this.bundles.values())for(const node of bundle.marker.source_nodes){if(out.has(node.name))throw Error('重复源节点');out.set(node.name,{node,bundle});}return out;}
  get maxDepth(){const nodes=this.nodes;return Math.max(...[...this.visible].map(n=>nodes.get(n).node.depth));}
  begin(marker,remainingBytes){
    const parent=this.nodes.get(marker.replacement_parent)?.node,children=marker.source_nodes?.map(n=>n.name)??[];
    if(this.pending||!parent||!this.visible.has(parent.name)||marker.schema!=='xnby.osgb_native_family.v1'||!marker.complete_sibling_family||marker.texture_policy!=='original_pixels_v1'||marker.parent_source_sha256!==parent.source_sha256||children.length!==parent.children.length||new Set(children).size!==children.length||children.some(n=>!parent.children.includes(n))||!marker.parts?.length||marker.parts.length>64||!Number.isSafeInteger(marker.gpu_payload_bytes)||marker.gpu_payload_bytes<=0||marker.gpu_payload_bytes>remainingBytes)throw Error('完整源节点族或资源预算不满足');
    const ticket=++this.sequence;this.pending={ticket,marker,ready:new Set()};return ticket;
  }
  markReady(ticket,index){if(this.pending?.ticket!==ticket||index<0||index>=this.pending.marker.parts.length)return false;this.pending.ready.add(index);return true;}
  commit(ticket,meshes){
    const state=this.pending;if(state?.ticket!==ticket||state.ready.size!==state.marker.parts.length||!this.visible.has(state.marker.replacement_parent))return false;
    validateSourceBundle(state.marker,meshes);
    const next=new Set(this.visible);next.delete(state.marker.replacement_parent);for(const node of state.marker.source_nodes)next.add(node.name);
    this.bundles.set(state.marker.replacement_parent,{marker:state.marker,meshes});this.visible=next;this.pending=null;this.cutVersion++;return true;
  }
  cancel(ticket){if(this.pending?.ticket!==ticket)return false;this.pending=null;return true;}
  rollback(parent,extraBytes=Infinity){
    const plan=this.rollbackPlan(parent);if(!plan||plan.bytes>this.bytes+extraBytes||!this.planningOnly&&plan.missingPages.length)return[];
    const retired=[...this.bundles].filter(([key])=>plan.subtree.has(key)).map(([,bundle])=>bundle);
    this.bundles=plan.bundles;this.visible=plan.visible;this.pending=null;this.cutVersion++;return retired;
  }
  reset(){const rootPages=this.bundles.get('$root');if(rootPages.marker.parts.some(p=>!rootPages.meshes.has(p.directory)))throw Error('基础源页尚未恢复，保留当前细层');const retired=[...this.bundles].filter(([key])=>key!=='$root').map(([,b])=>b);const root=this.bundles.get('$root');this.bundles=new Map([['$root',root]]);this.visible=new Set(root.marker.source_nodes.map(n=>n.name));this.pending=null;this.cutVersion++;return retired;}
  releaseHiddenPages(){
    let pages=0,bytes=0;
    for(const bundle of this.bundles.values()){
      const needed=new Set(bundle.marker.source_nodes.filter(n=>this.visible.has(n.name)).flatMap(n=>n.spans.map(s=>s.part)));
      for(const part of bundle.marker.parts)if(!needed.has(part.directory)&&bundle.meshes.has(part.directory)){
        const mesh=bundle.meshes.get(part.directory);retireSourceGpu(mesh);const material=mesh.userData.sourceMaterial??(Array.isArray(mesh.material)?mesh.material[0]:mesh.material);material.map?.source?.data?.close?.();mesh.removeFromParent();bundle.meshes.delete(part.directory);pages++;bytes+=part.gpu_payload_bytes;
      }
    }return {pages,bytes};
  }
  restorePages(bundle,meshes){
    if(![...this.bundles.values()].includes(bundle))throw Error('源包已退役');
    for(const [directory,mesh] of meshes){const part=bundle.marker.parts.find(p=>p.directory===directory);if(!part||bundle.meshes.has(directory))throw Error('源页恢复归属无效');validateSourcePart(part,mesh);}
    for(const [directory,mesh] of meshes)bundle.meshes.set(directory,mesh);
  }
  applyMasks(){
    for(const bundle of this.bundles.values())for(const part of bundle.marker.parts){const mesh=bundle.meshes.get(part.directory),ranges=bundle.marker.source_nodes.filter(n=>this.visible.has(n.name)).flatMap(n=>n.spans.filter(s=>s.part===part.directory)).sort((a,b)=>a.first-b.first);
      if(!mesh){if(ranges.length)throw Error('可见源页尚未恢复');continue;}
      mesh.geometry.clearGroups();for(const span of ranges)mesh.geometry.addGroup(span.first,span.count,0);
      mesh.visible=ranges.length>0;
      // Visibility changes first retire GPU pages; releaseHiddenPages drops CPU ownership separately.
      if(!mesh.visible)retireSourceGpu(mesh);
      mesh.userData.sourceGpuResident=mesh.visible;
      mesh.userData.sourceMaterial??=Array.isArray(mesh.material)?mesh.material[0]:mesh.material;mesh.material=[mesh.userData.sourceMaterial];
    }
  }
}

export function pickVisibleSource(frontier,ray){
  const a=new Vector3(),b=new Vector3(),c=new Vector3(),hit=new Vector3(),boxHit=new Vector3();let selected=null,distance=Infinity;
  const nodes=frontier.nodes;
  for(const name of frontier.visible){const {node,bundle}=nodes.get(name);if(!node.bounds_min||!node.bounds_max)continue;const box=new Box3(new Vector3(...node.bounds_min),new Vector3(...node.bounds_max));if(box.distanceToPoint(ray.origin)**2>distance||!ray.intersectBox(box,boxHit))continue;
    for(const span of node.spans){const mesh=bundle.meshes.get(span.part),positions=mesh.geometry.attributes.position.array,indices=mesh.geometry.index.array;
      for(let i=span.first;i<span.first+span.count;i+=3){a.fromArray(positions,indices[i]*3);b.fromArray(positions,indices[i+1]*3);c.fromArray(positions,indices[i+2]*3);
        if(ray.intersectTriangle(a,b,c,false,hit)){const d=hit.distanceToSquared(ray.origin);if(d<distance){distance=d;selected={node,distance:Math.sqrt(d),point:hit.clone()};}}
      }
    }
  }return selected;
}

export function sourceRefinementScore(quality,diameter,height,centerDistance,canRefine=true){if(!canRefine||![quality,diameter,height,centerDistance].every(Number.isFinite)||quality<=6||diameter<=0||height<=0||centerDistance<0)return 0;const coverage=Math.min(2,diameter/height);return Math.log2(1+quality/6)*coverage*coverage/(1+centerDistance);}
export function sourceViewPriority(node,camera,height){
 if(!node?.bounds_min)return 0;camera.updateMatrixWorld();
 const box=new Box3(new Vector3(...node.bounds_min),new Vector3(...node.bounds_max)),frustum=new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));if(!frustum.intersectsBox(box))return 0;
 const scale=height/(2*Math.tan(camera.fov*Math.PI/360)),distance=Math.max(1,box.distanceToPoint(camera.position)),projected=box.getCenter(new Vector3()).project(camera),centerDistance=Number.isFinite(projected.x)&&Number.isFinite(projected.y)?Math.hypot(projected.x,projected.y):2;
 return sourceRefinementScore(Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*scale/distance,box.getSize(new Vector3()).length()*scale/distance,height,centerDistance);
}
export function visibleSourceCandidates(frontier,camera,height,centerName=''){
 camera.updateMatrixWorld();const frustum=new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse)),scale=height/(2*Math.tan(camera.fov*Math.PI/360)),output=[],registry=frontier.nodes;
 for(const name of frontier.visible){const node=registry.get(name).node;if(!node.children.length||!node.bounds_min)continue;const box=new Box3(new Vector3(...node.bounds_min),new Vector3(...node.bounds_max));if(!frustum.intersectsBox(box))continue;const distance=Math.max(1,box.distanceToPoint(camera.position)),quality=Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*scale/distance,diameter=box.getSize(new Vector3()).length()*scale/distance,projected=box.getCenter(new Vector3()).project(camera),centerDistance=Number.isFinite(projected.x)&&Number.isFinite(projected.y)?Math.hypot(projected.x,projected.y):2,score=sourceRefinementScore(quality,diameter,height,centerDistance);if(score>0)output.push({node,score,center:name===centerName});
 }return output;
}

export function rankSourceCandidates(candidates){return [...candidates].sort((a,b)=>b.score-a.score||Number(b.center)-Number(a.center));}

// Plan all coarsenings before changing any live draw cut. Independent siblings
// within one root may jointly make room; failed admission changes nothing.
export function planSourceBudget(residents,request,cost,limit,priority,rootPriority=null,{checkRestorePeak=true}={}){
 let used=[...residents.values()].reduce((sum,r)=>sum+r.frontier.bytes,0);if(used+cost<=limit)return[];
 const candidates=[];
 for(const [root,ready] of residents)for(const parent of ready.frontier.bundles.keys())if(parent!=='$root'){
   const plan=ready.frontier.rollbackPlan(parent);if(root===request.id&&plan.subtree.has(request.parent))continue;
   const benefit=priority(root,ready.frontier.nodes.get(parent).node,plan.subtree);
   if(plan.bytes<ready.frontier.bytes&&benefit*2<request.score)candidates.push({root,parent,benefit});
 }
 if(rootPriority)for(const [root,ready] of residents)if(root!==request.id){const benefit=rootPriority(root,new Set(ready.frontier.visible));if(benefit*2<request.score)candidates.push({root,parent:null,benefit});}
 const totalLoss=actions=>actions.reduce((sum,action)=>sum+(candidates.find(c=>c.root===action.root&&c.parent===action.parent)?.benefit??Infinity),0);
 candidates.sort((a,b)=>a.benefit-b.benefit);const copies=new Map(),actions=[];
 for(const candidate of candidates){let copy=copies.get(candidate.root);if(copy===null)continue;if(!copy){copy=residents.get(candidate.root).frontier.copyForPlanning();copies.set(candidate.root,copy);}
   if(candidate.parent===null){used-=copy.bytes;copies.set(candidate.root,null);actions.splice(0,actions.length,...actions.filter(a=>a.root!==candidate.root));actions.push({root:candidate.root,parent:null});if(used+cost<=limit&&totalLoss(actions)*2<request.score)return actions;continue;}
   const plan=copy.rollbackPlan(candidate.parent);if(!plan||plan.bytes>=copy.bytes)continue;
   const proposed=[...actions.filter(a=>a.root!==candidate.root||!plan.subtree.has(a.parent)),{root:candidate.root,parent:candidate.parent}];
   if(checkRestorePeak&&sourceRestorationFootprint(residents,proposed)>limit)continue;
   used+=plan.bytes-copy.bytes;copy.rollback(candidate.parent);actions.splice(0,actions.length,...actions.filter(a=>a.root!==candidate.root||!plan.subtree.has(a.parent)));actions.push({root:candidate.root,parent:candidate.parent});if(used+cost<=limit&&totalLoss(actions)*2<request.score)return actions;
 }
 return null;
}
