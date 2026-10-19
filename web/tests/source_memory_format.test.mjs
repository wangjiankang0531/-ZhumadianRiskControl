import test from 'node:test';
import assert from 'node:assert/strict';
import {BufferGeometry,BufferAttribute,PerspectiveCamera} from 'three';
import {MEMORY_SOURCE_FORMAT,MEMORY_GEOMETRY_LAYOUT,MEMORY_ROOT_SCHEMA,memoryImageInfo,sourceImageMipBytes,isMemorySourcePart} from '../src/source_page_format.js';
import {webSourceGeometryBytes,validateSourceGltfGeometry,validateLoadedSourceGeometry} from '../src/source_geometry_layout.js';
import {sourcePageSource,planPreparedSourceBundle,sourcePageGeometryBytes,loadPreparedSourcePage} from '../src/prepared_source_page.js';
import {SOURCE_PLAN_SCHEMA,readSourcePlan,verifyPlannedSource,SourcePlanChanged} from '../src/source_descriptor_plan.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
import {geometryDigest,evaluateSourceGeometryGain} from '../src/source_geometry_gain.js';

async function fixture(){
 const positions=new Float32Array([-1,-1,0,1,-1,0,0,1,0]),uv=new Float32Array([0,0,1,0,0,1]),indices=new Uint32Array([0,1,2]),binary=new ArrayBuffer(72);let at=0;const views=[];
 for(const a of [positions,uv,indices]){new Uint8Array(binary,at,a.byteLength).set(new Uint8Array(a.buffer));views.push({buffer:0,byteOffset:at,byteLength:a.byteLength});at+=a.byteLength;}
 const gltf={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2,material:0}]}],buffers:[{uri:'geometry.bin',byteLength:72}],bufferViews:views,accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3'},{bufferView:1,componentType:5126,count:3,type:'VEC2'},{bufferView:2,componentType:5125,count:3,type:'SCALAR'}],images:[{uri:'texture.png'}],textures:[{source:0,sampler:0}],samplers:[{wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729}],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}]};
 const json=new TextEncoder().encode(JSON.stringify(gltf)).buffer,part={directory:'part_000',source_format:MEMORY_SOURCE_FORMAT,geometry_layout:MEMORY_GEOMETRY_LAYOUT,vertices:3,indices:3,gpu_payload_bytes:sourcePageGeometryBytes({vertices:3,indices:3})+sourceImageMipBytes(3,5),source_image:{file:'texture.png',width:3,height:5,opaque:true,row_order:'source_storage',source_origin:'bottom_left',sampler:gltf.samplers[0]},files:[{name:'geometry.gltf',bytes:json.byteLength,sha256:await geometryDigest(json)},{name:'geometry.bin',bytes:72,sha256:await geometryDigest(binary)},{name:'texture.png',bytes:100,sha256:'a'.repeat(64)}]};
 const marker={schema:MEMORY_ROOT_SCHEMA,source_format:MEMORY_SOURCE_FORMAT,tile_id:1,depth:1,complete_frontier:true,texture_policy:'original_pixels_v1',parts:[part],gpu_payload_bytes:part.gpu_payload_bytes,indices:3,source_nodes:[{name:'child',triangles:1,longest_edge_p90_m:1,texel_world_p90_m:0,spans:[{part:'part_000',first:0,count:3}]}]};
 const geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(positions,3));geometry.setAttribute('uv',new BufferAttribute(uv,2));geometry.setIndex(new BufferAttribute(indices,1));
 return {part,marker,gltf,json,binary,geometry};
}
test('explicit original-image page uses exact PU layout and full non-square mip accounting',async()=>{
 const f=await fixture();assert.equal(isMemorySourcePart(f.part),true);assert.equal(webSourceGeometryBytes(f.part),72);assert.equal(validateSourceGltfGeometry(f.gltf,f.part,f.binary),72);assert.equal(validateLoadedSourceGeometry(f.geometry,f.part),72);assert.equal(memoryImageInfo(f.part).bytes,72);assert.equal(sourcePageSource(f.part).width,3);
});
test('new source format cannot weaken the legacy normal/atlas contract',async()=>{
 const f=await fixture(),legacy=structuredClone(f.part);delete legacy.source_format;delete legacy.geometry_layout;assert.throws(()=>validateSourceGltfGeometry(f.gltf,legacy,f.binary));assert.throws(()=>sourcePageSource(legacy));delete f.part.source_format;assert.throws(()=>isMemorySourcePart(f.part),/Unversioned/);
});
test('mixed atlas fields, unexpected files, alpha, sampler and image limits are rejected',async()=>{
 for(const mutate of [p=>p.atlas_size=1024,p=>p.atlas_extent=[3,5],p=>p.files.push({...p.files[2]}),p=>p.source_image.opaque=false,p=>p.source_image.width=8193,p=>p.source_image.sampler.wrapS=10496,p=>p.source_image.row_order='flipped',p=>p.files[2].name='atlas.jpg',p=>p.source_image.url='https://external.test',p=>p.geometry_layout='other']){
  const f=await fixture();mutate(f.part);assert.throws(()=>memoryImageInfo(f.part));
 }
});
test('original image planning never probes BC7 and records real runtime geometry cost',async()=>{
 const f=await fixture();let probes=0;const plan=await planPreparedSourceBundle({marker:f.marker,supported:true,loadManifest:()=>{probes++;throw Error('not a prepared BC7 page');}});
 assert.equal(probes,0);assert.equal(plan.marker.parts[0].runtime_texture.geometryLayout,MEMORY_GEOMETRY_LAYOUT);assert.equal(plan.marker.parts[0].runtime_texture.geometryBytes,72);assert.equal(plan.marker.gpu_payload_bytes,144);assert.equal(f.marker.gpu_payload_bytes,276);
});
test('wrong source-native cost or PU index is refused before image or GPU reservation',async()=>{
 const f=await fixture(),wrong=structuredClone(f.part);wrong.gpu_payload_bytes--;assert.throws(()=>sourcePageSource(wrong));
 new Uint32Array(f.binary,60)[2]=3;f.part.files[1].sha256=await geometryDigest(f.binary);let reservations=0,images=0;
 await assert.rejects(loadPreparedSourcePage({part:f.part,loadFile:async name=>{if(name==='texture.png')images++;return name==='geometry.gltf'?f.json:f.binary;},reserve:()=>{reservations++;throw Error('must not reserve');}}),/index out of range/);
 assert.equal(images,0);assert.equal(reservations,0);
});
test('CPU visible-pixel gain consumes exact original PU geometry without creating normals',async()=>{
 const f=await fixture(),camera=new PerspectiveCamera(52,1,.5,60000);camera.position.set(0,0,5);camera.updateMatrixWorld();
 const snapshot={schema:'xnby.visible_source_samples.v1',cameraKey:'fixed',width:100,height:100,fov:52,cameraWorld:[...camera.matrixWorld.elements],viewMatrix:[...camera.matrixWorldInverse.elements],projectionInverse:[...camera.projectionMatrixInverse.elements],nodes:[{longest_edge_p90_m:10,texel_world_p90_m:0}],samples:new Float64Array([0,0,Math.round(Math.log2(10)/Math.log2(120000)*255),1,0])};
 const result=await evaluateSourceGeometryGain({marker:f.marker,packets:[{directory:'part_000',json:f.json,binary:f.binary}],snapshot,identity:'memory-pu'});
 assert.equal(result.hits,1);assert.ok(result.gain>0);assert.equal(result.gpuAllocations,0);
});
test('preparing response yields one pinned new-format plan; source identity change is rejected',async()=>{
 const f=await fixture(),wrapper={schema:SOURCE_PLAN_SCHEMA,verification:'metadata_only',availabilityVerified:false,markerSHA256:'b'.repeat(64),marker:f.marker};let calls=0;
 const plan=await readSourcePlan({request:{id:1,depth:1},fetcher:async()=>++calls===1?Response.json({status:'preparing_source_memory'},{status:202}):Response.json(wrapper)});
 assert.equal(calls,2);const response=new Response(null,{headers:{'X-XNBY-Source-Marker-SHA256':'b'.repeat(64)}}),actual={...f.marker,cache_lease:'c'.repeat(32)};assert.equal(verifyPlannedSource(plan,response,actual),true);
 const changed=structuredClone(actual);changed.parts[0].source_image.width=4;assert.throws(()=>verifyPlannedSource(plan,response,changed),SourcePlanChanged);
});
test('cancelled preparation stops metadata polling before payloads or leases',async()=>{
 let wanted=true,calls=0;await assert.rejects(readSourcePlan({request:{id:1,depth:1},stillWanted:()=>wanted,fetcher:async()=>{calls++;wanted=false;return new Response(null,{status:202});}}),SourceLoadCancelled);assert.equal(calls,1);
});
test('new marker schema requires every page to opt in; legacy/new mixtures are refused',async()=>{
 const f=await fixture();for(const mutate of [m=>delete m.source_format,m=>delete m.parts[0].source_format,m=>m.source_format='future_format',m=>m.schema='hongtu.osgb_native_chunk_bundle.v1']){
  const m=structuredClone(f.marker);mutate(m);await assert.rejects(readSourcePlan({request:{id:1,depth:1},fetcher:async()=>Response.json({schema:SOURCE_PLAN_SCHEMA,verification:'metadata_only',availabilityVerified:false,markerSHA256:'b'.repeat(64),marker:m})}));
 }
});

