import test from 'node:test';
import assert from 'node:assert/strict';
import {PerspectiveCamera,Ray,Vector3} from 'three';
import {evaluateSourceGeometryGain,geometryDigest,buildGeometryBvh,intersectGeometryBvh} from '../src/source_geometry_gain.js';
import {SourceGeometryGainWorker,SourceGainUnavailable} from '../src/source_gain_client.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';

async function fixture(){
 const positions=new Float32Array([-1,-1,0,1,-1,0,0,1,0]),normals=new Float32Array([0,0,1,0,0,1,0,0,1]),uvs=new Float32Array(6),indices=new Uint32Array([0,1,2]),binary=new ArrayBuffer(108);let offset=0;const views=[];
 for(const value of [positions,normals,uvs,indices]){new Uint8Array(binary,offset,value.byteLength).set(new Uint8Array(value.buffer));views.push({buffer:0,byteOffset:offset,byteLength:value.byteLength});offset+=value.byteLength;}
 const g={asset:{version:'2.0'},buffers:[{uri:'geometry.bin',byteLength:108}],bufferViews:views,accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3'},{bufferView:1,componentType:5126,count:3,type:'VEC3'},{bufferView:2,componentType:5126,count:3,type:'VEC2'},{bufferView:3,componentType:5125,count:3,type:'SCALAR'}],meshes:[{primitives:[{attributes:{POSITION:0,NORMAL:1,TEXCOORD_0:2},indices:3,material:0}]}],nodes:[{mesh:0}],scenes:[{nodes:[0]}],scene:0};
 const json=new TextEncoder().encode(JSON.stringify(g)).buffer,part={directory:'part_000',vertices:3,indices:3,files:[{name:'geometry.gltf',bytes:json.byteLength,sha256:await geometryDigest(json)},{name:'geometry.bin',bytes:binary.byteLength,sha256:await geometryDigest(binary)}]},node={name:'child',triangles:1,longest_edge_p90_m:1,texel_world_p90_m:0,spans:[{part:'part_000',first:0,count:3}]};
 const camera=new PerspectiveCamera(52,1,.5,60000);camera.position.set(0,0,5);camera.updateMatrixWorld();
 const snapshot={schema:'xnby.visible_source_samples.v1',cameraKey:'fixed-camera',width:100,height:100,fov:52,cameraWorld:[...camera.matrixWorld.elements],viewMatrix:[...camera.matrixWorldInverse.elements],projectionInverse:[...camera.projectionMatrixInverse.elements],nodes:[{longest_edge_p90_m:10,texel_world_p90_m:0}],samples:new Float64Array([0,0,Math.round(Math.log2(10)/Math.log2(120000)*255),1,0])};
 return {marker:{parts:[part],source_nodes:[node],indices:3},packets:[{directory:'part_000',json,binary}],snapshot,identity:'fixture',g};
}
async function rewrite(f){const packet=f.packets[0];packet.json=new TextEncoder().encode(JSON.stringify(f.g)).buffer;const row=f.marker.parts[0].files[0];row.bytes=packet.json.byteLength;row.sha256=await geometryDigest(packet.json);}

test('pinned child triangle and actual hit depth determine gain, without GPU allocation',async()=>{
 const f=await fixture(),r=await evaluateSourceGeometryGain(f);assert.equal(r.samples,1);assert.equal(r.hits,1);assert.equal(r.missing,0);assert.ok(r.gain>0&&r.afterDeficit<r.beforeDeficit);assert.equal(r.gpuAllocations,0);assert.equal(r.nodeHits.child,1);assert.equal(r.identity,'fixture');
});
test('a visible parent pixel without a child hit retains its original deficit',async()=>{
 const f=await fixture();f.snapshot.samples[0]=.9;const r=await evaluateSourceGeometryGain(f);assert.equal(r.hits,0);assert.equal(r.missing,1);assert.equal(r.afterDeficit,r.beforeDeficit);assert.equal(r.gain,0);
});
test('child triangles outside the actual near/far clip range cannot earn invisible gain',async()=>{
 for(const z of [4.75,-70000]){const f=await fixture(),positions=new Float32Array(f.packets[0].binary,0,9);for(let i=2;i<positions.length;i+=3)positions[i]=z;f.marker.parts[0].files[1].sha256=await geometryDigest(f.packets[0].binary);f.snapshot.near=.5;f.snapshot.far=60000;const result=await evaluateSourceGeometryGain(f);assert.equal(result.hits,0);assert.equal(result.missing,1);assert.equal(result.gain,0);}
});
test('corrupt bytes, foreign dependencies, transforms and accessor escapes are rejected',async()=>{
 const bad=await fixture();new Uint8Array(bad.packets[0].binary)[0]^=1;await assert.rejects(evaluateSourceGeometryGain(bad),/digest mismatch/);
 for(const change of [g=>g.buffers[0].uri='https://outside.test/file',g=>g.nodes[0].translation=[1,0,0],g=>g.accessors[0].byteOffset=4,g=>g.bufferViews[3].byteOffset=99999,g=>g.accessors[3].componentType=5123,g=>g.bufferViews[0].byteStride=16]){const f=await fixture();change(f.g);await rewrite(f);await assert.rejects(evaluateSourceGeometryGain(f));}
});
test('overlapping, missing, unknown and mismatched triangle ownership is refused',async()=>{
 for(const change of [m=>m.source_nodes[0].spans[0].part='foreign',m=>m.source_nodes[0].triangles=2,m=>m.source_nodes.push({...m.source_nodes[0],name:'overlap'}),m=>{m.source_nodes[0].spans=[];m.source_nodes[0].triangles=0;}]){const f=await fixture();change(f.marker);await assert.rejects(evaluateSourceGeometryGain(f));}
});
test('invalid visible pixel indices, weights and matrices cannot admit a candidate',async()=>{
 for(const change of [s=>s.samples[3]=2,s=>s.samples[4]=1,s=>s.samples[0]=NaN,s=>s.cameraWorld[0]=Infinity]){const f=await fixture();change(f.snapshot);await assert.rejects(evaluateSourceGeometryGain(f));}
});
test('median BVH nearest-hit answers agree with independent brute-force ray triangles',()=>{
 const positions=[],indices=[],owners=[];for(let y=0;y<9;y++)for(let x=0;x<9;x++){const offset=positions.length/3,z=Math.sin(x+y)*.1;positions.push(x-4,y-4,z,x-3.2,y-4,z+.3,x-4,y-3.2,z-.2);indices.push(offset,offset+1,offset+2);owners.push(y*9+x);}
 const part={positions:new Float32Array(positions),indices:new Uint32Array(indices),owners:new Int32Array(owners)},tree=buildGeometryBvh(part),a=new Vector3(),b=new Vector3(),c=new Vector3(),point=new Vector3();
 for(let i=0;i<120;i++){const ray=new Ray(new Vector3((i*37%100)/10-5,(i*61%100)/10-5,i%2?5:.02),new Vector3(.01,-.03,-1).normalize());let expected=null,distance=Infinity;
  for(let triangle=0;triangle<indices.length/3;triangle++){a.fromArray(part.positions,indices[triangle*3]*3);b.fromArray(part.positions,indices[triangle*3+1]*3);c.fromArray(part.positions,indices[triangle*3+2]*3);if(ray.intersectTriangle(a,b,c,false,point)){const d=point.distanceTo(ray.origin);if(d<distance){distance=d;expected=triangle;}}}
  const hit=intersectGeometryBvh(tree,ray);assert.equal(hit?.node??null,expected);if(hit)assert.ok(Math.abs(hit.distance-distance)<1e-10);
 }
});
class CpuWorker{
 postMessage(message,transfer){const copy=structuredClone(message,{transfer});queueMicrotask(async()=>{try{const result=await evaluateSourceGeometryGain(copy);if(!this.stopped)this.onmessage({data:{id:copy.id,ok:true,result}});}catch(error){if(!this.stopped)this.onmessage({data:{id:copy.id,ok:false,error:error.message}});}});}
 terminate(){this.stopped=true;}
}
test('client transfers only candidate geometry and rejects foreign result identities',async()=>{
 const f=await fixture(),worker=new CpuWorker(),client=new SourceGeometryGainWorker({createWorker:()=>worker});const result=await client.measure({...f,isCurrent:()=>true,loadFile:async(part,name)=>f.packets[0][name==='geometry.gltf'?'json':'binary']});assert.equal(result.hits,1);assert.equal(f.packets[0].binary.byteLength,0);assert.equal(client.pending,null);client.dispose();
 const g=await fixture(),foreign={postMessage(data){queueMicrotask(()=>this.onmessage({data:{id:data.id,ok:true,result:{identity:'wrong',cameraKey:g.snapshot.cameraKey,gain:1}}}));},terminate(){this.stopped=true;}};const second=new SourceGeometryGainWorker({createWorker:()=>foreign});await assert.rejects(second.measure({...g,isCurrent:()=>true,loadFile:async(part,name)=>g.packets[0][name==='geometry.gltf'?'json':'binary']}),SourceGainUnavailable);assert.equal(foreign.stopped,true);
});
test('a cancelled loading job cannot overlap a second job or create its worker',async()=>{
 const f=await fixture();let complete,started,creations=0,reads=0;const began=new Promise(r=>started=r),client=new SourceGeometryGainWorker({createWorker:()=>{creations++;return new CpuWorker();}});
 const task=client.measure({...f,isCurrent:()=>true,loadFile:()=>{reads++;started();return new Promise(r=>complete=r);}});await began;await assert.rejects(client.measure({...f,isCurrent:()=>true}),/already active/);client.cancel();complete(f.packets[0].json);await assert.rejects(task,SourceLoadCancelled);assert.equal(reads,1);assert.equal(creations,0);assert.equal(client.busy,false);
});
test('unresponsive workers terminate on a bounded timeout without changing a live cut',async()=>{
 const f=await fixture(),worker={postMessage(){},terminate(){this.stopped=true;}},client=new SourceGeometryGainWorker({createWorker:()=>worker,timeout:20});await assert.rejects(client.measure({...f,isCurrent:()=>true,loadFile:async(part,name)=>f.packets[0][name==='geometry.gltf'?'json':'binary']}),/timed out/);assert.equal(worker.stopped,true);assert.equal(client.pending,null);assert.equal(client.busy,false);
});

test('exact captured inputs reuse a verified result without reading geometry; changed visibility computes again',async()=>{
 const client=new SourceGeometryGainWorker({createWorker:()=>new CpuWorker()});let reads=0;
 const run=async f=>client.measure({...f,isCurrent:()=>true,loadFile:async(part,name)=>{reads++;return f.packets[0][name==='geometry.gltf'?'json':'binary'];}});
 const first=await run(await fixture());assert.equal(first.memoHit,false);assert.equal(reads,2);
 const same=await fixture();same.marker.cache_lease='new transport';const second=await run(same);assert.equal(second.memoHit,true);assert.equal(reads,2);assert.equal(second.gain,first.gain);assert.equal(same.packets[0].binary.byteLength,108);
 const changed=await fixture();changed.snapshot.samples[0]=.9;const third=await run(changed);assert.equal(third.memoHit,false);assert.equal(reads,4);assert.equal(third.hits,0);
 await assert.rejects(client.measure({...await fixture(),isCurrent:()=>false,loadFile:()=>{throw Error('must not read');}}),SourceLoadCancelled);
 client.dispose();assert.equal(client.memo.bytes,0);
});

test('planning memo probes never pretend to be geometry loads or create workers',async()=>{
 let creations=0;const client=new SourceGeometryGainWorker({createWorker:()=>{creations++;return new CpuWorker();}}),cold=await fixture();
 const task=client.peek({marker:cold.marker,snapshot:cold.snapshot,isCurrent:()=>true});assert.equal(client.probing,true);assert.equal(!!client.busy,false);await assert.rejects(client.measure({...cold,isCurrent:()=>true}),/already active/);assert.equal(await task,null);assert.equal(creations,0);assert.equal(cold.packets[0].binary.byteLength,108);
 const first=await fixture(),result=await client.measure({...first,isCurrent:()=>true,loadFile:async(part,name)=>first.packets[0][name==='geometry.gltf'?'json':'binary']});const next=await fixture();const hit=await client.peek({marker:next.marker,snapshot:next.snapshot,isCurrent:()=>true});assert.equal(hit.gain,result.gain);assert.equal(creations,1);assert.equal(next.packets[0].binary.byteLength,108);
 const moved=await fixture();moved.snapshot.samples[0]=.9;assert.equal(await client.peek({marker:moved.marker,snapshot:moved.snapshot,isCurrent:()=>true}),null);
 await assert.rejects(client.peek({marker:next.marker,snapshot:next.snapshot,isCurrent:()=>false}),SourceLoadCancelled);assert.equal(client.probing,false);client.dispose();
});
