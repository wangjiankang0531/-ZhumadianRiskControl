import {isMemorySourcePart} from './source_page_format.js';
// CPU-only, SHA-pinned geometry. No renderer, texture, DOM, network or file IO.
import {Vector3,Ray,Box3,Matrix4} from 'three';
const require=(ok,message)=>{if(!ok)throw Error(message);},shaPattern=/^[0-9a-f]{64}$/;
export const geometryPacketLimit=384*1048576;
export async function geometryDigest(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');}
export const sampleDepth=bin=>.5*120000**(bin/255);
const depthBin=depth=>Math.max(0,Math.min(255,Math.round(Math.log2(Math.max(depth,.5)/.5)/Math.log2(120000)*255)));
const scaleFor=(node,fov,height)=>Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*height/(2*Math.tan(fov*Math.PI/360));
const deficit=(scale,depth,weight)=>scale/depth>6?Math.log2(1+scale/depth/6)*weight:0;
function validMetric(node){return Number.isFinite(node?.longest_edge_p90_m)&&node.longest_edge_p90_m>=0&&Number.isFinite(node?.texel_world_p90_m)&&node.texel_world_p90_m>=0;}

function accessor(gltf,index,binary,type,componentType,count){
 const a=gltf.accessors[index],v=gltf.bufferViews[a?.bufferView],components={VEC3:3,VEC2:2,SCALAR:1}[type];
 require(a&&v&&a.type===type&&a.componentType===componentType&&a.count===count&&!a.normalized&&!a.sparse&&!v.byteStride&&v.buffer===0,'Unsupported geometry accessor');
 const start=v.byteOffset??0,relative=a.byteOffset??0,size=count*components*4;
 require([start,relative,v.byteLength].every(Number.isSafeInteger)&&start>=0&&relative>=0&&start%4===0&&relative%4===0&&relative+size<=v.byteLength&&start+v.byteLength<=binary.byteLength,'Geometry accessor exceeds pinned buffer');
 const value=componentType===5125?new Uint32Array(binary,start+relative,count):new Float32Array(binary,start+relative,count*components);
 return {value,start,end:start+v.byteLength};
}
async function checked(part,name,raw){
 const records=part.files?.filter(f=>f.name===name)??[];
 require(records.length===1&&shaPattern.test(records[0].sha256)&&raw instanceof ArrayBuffer&&raw.byteLength===records[0].bytes&&raw.byteLength>0&&raw.byteLength<=32*1048576,'Invalid pinned geometry bytes');
 require(await geometryDigest(raw)===records[0].sha256,'Pinned geometry digest mismatch');return raw;
}
async function geometryPart(part,packet,sourceNodes){
 require(packet.directory===part.directory&&/^part_\d{3}$/.test(part.directory)&&Number.isSafeInteger(part.vertices)&&part.vertices>0&&Number.isSafeInteger(part.indices)&&part.indices>0&&part.indices%3===0,'Invalid geometry part identity');
 const raw=await checked(part,'geometry.gltf',packet.json);require(raw.byteLength<=1048576,'Geometry descriptor exceeds limit');const g=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));const binary=await checked(part,'geometry.bin',packet.binary);
 require(g.asset?.version==='2.0'&&g.buffers?.length===1&&g.buffers[0].uri==='geometry.bin'&&g.buffers[0].byteLength===binary.byteLength&&!g.extensionsRequired?.length&&!g.extensionsUsed?.length,'Unsupported geometry dependencies');
 require(g.nodes?.length===1&&JSON.stringify(g.nodes[0])==='{"mesh":0}'&&g.scene===0&&g.scenes?.length===1&&JSON.stringify(g.scenes[0])==='{"nodes":[0]}'&&g.meshes?.length===1&&g.meshes[0].primitives?.length===1,'Unsupported geometry transforms');
 const memory=isMemorySourcePart(part),primitive=g.meshes[0].primitives[0];require(primitive.mode===undefined&&primitive.material===0&&Object.keys(primitive.attributes??{}).sort().join(',')===(memory?'POSITION,TEXCOORD_0':'NORMAL,POSITION,TEXCOORD_0')&&g.accessors?.length===(memory?3:4)&&g.bufferViews?.length===(memory?3:4),'Unsupported geometry primitive');
 const p=accessor(g,primitive.attributes.POSITION,binary,'VEC3',5126,part.vertices),normal=memory?null:accessor(g,primitive.attributes.NORMAL,binary,'VEC3',5126,part.vertices),uv=accessor(g,primitive.attributes.TEXCOORD_0,binary,'VEC2',5126,part.vertices),indices=accessor(g,primitive.indices,binary,'SCALAR',5125,part.indices);
 const ranges=[p,...(normal?[normal]:[]),uv,indices].sort((a,b)=>a.start-b.start);let end=0;for(const range of ranges){require(range.start===end,'Geometry views overlap or contain unexplained bytes');end=range.end;}require(end===binary.byteLength,'Geometry buffer contains trailing bytes');
 require(p.value.every(Number.isFinite)&&(!normal||normal.value.every(Number.isFinite))&&uv.value.every(Number.isFinite)&&indices.value.every(i=>i<part.vertices),'Invalid geometry coordinates or indices');
 const owners=new Int32Array(part.indices/3).fill(-1);
 for(let n=0;n<sourceNodes.length;n++)for(const span of sourceNodes[n].spans??[])if(span.part===part.directory){
  require(Number.isSafeInteger(span.first)&&Number.isSafeInteger(span.count)&&span.first>=0&&span.count>0&&span.first%3===0&&span.count%3===0&&span.first+span.count<=part.indices,'Invalid source triangle span');
  for(let i=span.first/3;i<(span.first+span.count)/3;i++){require(owners[i]===-1,'Source triangle ownership overlaps');owners[i]=n;}
 }
 require(owners.every(n=>n>=0),'Source triangles are unowned');return {positions:p.value,indices:indices.value,owners};
}

// Median-split BVH stores only triangle IDs and boxes; all vertices remain views
// into the transferred, verified original buffer. It never changes the indices.
export function buildGeometryBvh(part){
 const {positions:p,indices}=part,ids=Uint32Array.from({length:indices.length/3},(_,i)=>i),a=new Vector3(),b=new Vector3(),c=new Vector3();
 const center=(id,axis)=>(p[indices[id*3]*3+axis]+p[indices[id*3+1]*3+axis]+p[indices[id*3+2]*3+axis])/3;
 function median(start,end,mid,axis){let lo=start,hi=end-1;while(lo<hi){const pivot=center(ids[(lo+hi)>>>1],axis);let i=lo,j=hi;while(i<=j){while(center(ids[i],axis)<pivot)i++;while(center(ids[j],axis)>pivot)j--;if(i<=j){const swap=ids[i];ids[i++]=ids[j];ids[j--]=swap;}}if(mid<=j)hi=j;else if(mid>=i)lo=i;else break;}}
 function build(start,end){const box=new Box3();for(let i=start;i<end;i++){const offset=ids[i]*3;box.expandByPoint(a.fromArray(p,indices[offset]*3));box.expandByPoint(b.fromArray(p,indices[offset+1]*3));box.expandByPoint(c.fromArray(p,indices[offset+2]*3));}
  if(end-start<=24)return {box,start,end};const extent=box.getSize(a),axis=extent.x>=extent.y&&extent.x>=extent.z?0:extent.y>=extent.z?1:2,mid=(start+end)>>>1;median(start,end,mid,axis);return {box,left:build(start,mid),right:build(mid,end)};}
 return {...part,ids,tree:build(0,ids.length)};
}
export function intersectGeometryBvh(part,ray,maximum=Infinity,minimum=0){
 const a=new Vector3(),b=new Vector3(),c=new Vector3(),point=new Vector3(),entry=new Vector3();let distance=maximum,hit=null;
 const visit=node=>{if(!ray.intersectBox(node.box,entry)||!node.box.containsPoint(ray.origin)&&entry.distanceToSquared(ray.origin)>distance*distance)return;
  if(node.left){visit(node.left);visit(node.right);return;}
  for(let i=node.start;i<node.end;i++){const triangle=part.ids[i],offset=triangle*3;a.fromArray(part.positions,part.indices[offset]*3);b.fromArray(part.positions,part.indices[offset+1]*3);c.fromArray(part.positions,part.indices[offset+2]*3);if(ray.intersectTriangle(a,b,c,false,point)){const d=point.distanceTo(ray.origin);if(d>=minimum&&d<distance){distance=d;hit={distance,node:part.owners[triangle],point:point.clone()};}}}
 };visit(part.tree);return hit;
}
function validateSnapshot(snapshot){
 require(snapshot?.schema==='xnby.visible_source_samples.v1'&&typeof snapshot.cameraKey==='string'&&snapshot.cameraKey.length<8192&&Number.isFinite(snapshot.fov)&&snapshot.fov>0&&snapshot.fov<180&&Number.isInteger(snapshot.width)&&snapshot.width>0&&Number.isInteger(snapshot.height)&&snapshot.height>0,'Invalid visible source snapshot');
 for(const key of ['cameraWorld','projectionInverse','viewMatrix'])require(Array.isArray(snapshot[key])&&snapshot[key].length===16&&snapshot[key].every(Number.isFinite),'Invalid snapshot camera matrix');
 const near=snapshot.near??.5,far=snapshot.far??60000;require(Number.isFinite(near)&&near>0&&Number.isFinite(far)&&far>near,'Invalid snapshot clipping range');
 require(Array.isArray(snapshot.nodes)&&snapshot.nodes.length<=8192&&snapshot.nodes.every(validMetric)&&snapshot.samples instanceof Float64Array&&snapshot.samples.length%5===0&&snapshot.samples.length/5<=16384,'Invalid visible source pixels');
 let total=0;for(let i=0;i<snapshot.samples.length;i+=5){const [x,y,bin,weight,node]=snapshot.samples.subarray(i,i+5);require(Number.isFinite(x)&&Math.abs(x)<1&&Number.isFinite(y)&&Math.abs(y)<1&&Number.isInteger(bin)&&bin>=0&&bin<=255&&Number.isFinite(weight)&&weight>0&&Number.isInteger(node)&&node>=0&&node<snapshot.nodes.length,'Invalid source pixel');total+=weight;}require(total<=1+1e-6,'Visible pixel weight exceeds viewport');
}
export async function evaluateSourceGeometryGain({marker,packets,snapshot,identity}){
 const start=performance.now();validateSnapshot(snapshot);require(typeof identity==='string'&&identity.length<=16384,'Invalid geometry job identity');
 require(Array.isArray(marker.parts)&&marker.parts.length>0&&marker.parts.length<=64&&Array.isArray(packets)&&packets.length===marker.parts.length&&new Set(marker.parts.map(p=>p.directory)).size===marker.parts.length,'Incomplete geometry job');
 require(Array.isArray(marker.source_nodes)&&marker.source_nodes.length>0&&marker.source_nodes.length<=8192&&marker.source_nodes.every(validMetric)&&new Set(marker.source_nodes.map(n=>n.name)).size===marker.source_nodes.length,'Invalid candidate sources');
 const directories=new Set(marker.parts.map(p=>p.directory));let sourceIndices=0;
 for(const node of marker.source_nodes){require(Number.isSafeInteger(node.triangles)&&node.triangles>=0&&Array.isArray(node.spans),'Invalid source triangle count');let count=0;for(const span of node.spans){require(directories.has(span.part)&&Number.isSafeInteger(span.count)&&span.count>0,'Unknown source physical page');count+=span.count;}require(count===node.triangles*3,'Source triangle count differs');sourceIndices+=count;}
 require(sourceIndices===marker.indices&&marker.parts.reduce((sum,p)=>sum+p.indices,0)===marker.indices,'Candidate complete geometry count differs');
 require(packets.reduce((sum,p)=>sum+(p.json?.byteLength??Infinity)+(p.binary?.byteLength??Infinity),0)<=geometryPacketLimit,'Candidate CPU geometry exceeds limit');
 const parts=[];for(let i=0;i<marker.parts.length;i++)parts.push(buildGeometryBvh(await geometryPart(marker.parts[i],packets[i],marker.source_nodes)));
 const projection=new Matrix4().fromArray(snapshot.projectionInverse),world=new Matrix4().fromArray(snapshot.cameraWorld),view=new Matrix4().fromArray(snapshot.viewMatrix),origin=new Vector3().setFromMatrixPosition(world),direction=new Vector3(),ray=new Ray();
 const beforeScales=snapshot.nodes.map(n=>scaleFor(n,snapshot.fov,snapshot.height)),afterScales=marker.source_nodes.map(n=>scaleFor(n,snapshot.fov,snapshot.height));
 let beforeDeficit=0,afterDeficit=0,hits=0,missing=0;const mapped=new Map();
 for(let i=0;i<snapshot.samples.length;i+=5){const [x,y,bin,weight,node]=snapshot.samples.subarray(i,i+5),before=deficit(beforeScales[node],sampleDepth(bin),weight);beforeDeficit+=before;
  direction.set(x,y,.5).applyMatrix4(projection).applyMatrix4(world).sub(origin).normalize();ray.set(origin,direction);let closest=null;
  const forwardDepth=-(view.elements[2]*direction.x+view.elements[6]*direction.y+view.elements[10]*direction.z),minimum=(snapshot.near??.5)/forwardDepth,maximum=(snapshot.far??60000)/forwardDepth;
  if(forwardDepth>0)for(const part of parts){const hit=intersectGeometryBvh(part,ray,closest?.distance??maximum,minimum);if(hit)closest=hit;}
  if(!closest){missing++;afterDeficit+=before;continue;}hits++;const depth=-closest.point.applyMatrix4(view).z;afterDeficit+=deficit(afterScales[closest.node],sampleDepth(depthBin(depth)),weight);mapped.set(marker.source_nodes[closest.node].name,(mapped.get(marker.source_nodes[closest.node].name)??0)+1);
 }
 return {identity,cameraKey:snapshot.cameraKey,samples:snapshot.samples.length/5,hits,missing,beforeDeficit,afterDeficit,signedGain:beforeDeficit-afterDeficit,gain:Math.max(0,beforeDeficit-afterDeficit),triangles:parts.reduce((sum,p)=>sum+p.indices.length/3,0),geometryBytes:packets.reduce((sum,p)=>sum+p.json.byteLength+p.binary.byteLength,0),nodeHits:Object.fromEntries(mapped),milliseconds:performance.now()-start,model:'gpu_visible_pixels_cpu_child_triangles_v1',gpuAllocations:0};
}
