import test,{mock} from 'node:test';import * as THREE from 'three';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';
import {BufferGeometry,BufferAttribute,Mesh,MeshBasicMaterial,DataTexture,SRGBColorSpace,ClampToEdgeWrapping,LinearFilter} from 'three';
import {SourceFrontier} from '../src/source_frontier.js';
import {validateLevelTile,validateIndexedSourceReplacement} from '../src/source_level_index.js';
import {MEMORY_SOURCE_FORMAT,MEMORY_GEOMETRY_LAYOUT,MEMORY_ROOT_SCHEMA,INDEXED_FAMILY_SCHEMA} from '../src/source_page_format.js';
import {loadPreparedSourcePage,runtimeSourceBundle} from '../src/prepared_source_page.js';
import {SOURCE_PLAN_SCHEMA,sourcePlanURL,readSourcePlan,verifyPlannedSource,IndexedSourceQualityLimit,SourcePlanCache} from '../src/source_descriptor_plan.js';
const hash='a'.repeat(64),P='Tile_1_L16_0u.osgb',A='Tile_1_L17_0uu.osgb',B='Tile_1_L17_0u0.osgb',G='Tile_1_L18_0uuu.osgb',H='Tile_1_L18_0uu0.osgb',I='Tile_1_L19_0uuuu.osgb',J='Tile_1_L19_0uuu0.osgb';
const rows=[[P,[A,B],0],[A,[G,H],1],[B,[],1],[G,[I,J],2],[H,[],2],[I,[],3],[J,[],3]];
function topology(){const nodes=rows.map(([name,children,depth])=>({name,children,depth,level:depth+16,sourceSHA256:hash,sourceBytes:100,triangles:1,boundsMin:[-1,-1,0],boundsMax:[1,1,0],subtreeMin:[-1,-1,0],subtreeMax:[1,1,0],edgeP90:1,texelP90:.1}));const data={schema:'zhumadian.level_bounds.tile.v1',tile:1,complete:true,sourceManifestSHA256:hash,catalogSHA256:hash,root:P,roots:[P],nodes};validateLevelTile(data,{tile:1,sourceManifestSHA256:hash,catalogSHA256:hash,sourceNodes:7,rootBounds:{boundsMin:[-1,-1,0],boundsMax:[1,1,0]}});return data;}
function bundle(names,parent=null){const source_nodes=names.map((name,i)=>{const row=rows.find(r=>r[0]===name);return{name,children:row[1],depth:row[2],source_sha256:hash,triangles:1,longest_edge_p90_m:1,texel_world_p90_m:.1,bounds_min:[-1,-1,0],bounds_max:[1,1,0],spans:[{part:`part_${String(i).padStart(3,'0')}`,first:0,count:3}]};});
 const parts=source_nodes.map((n,i)=>({directory:n.spans[0].part,source_format:MEMORY_SOURCE_FORMAT,geometry_layout:MEMORY_GEOMETRY_LAYOUT,vertices:3,indices:3,gpu_payload_bytes:208,source_image:{file:'texture.png',width:1,height:1,opaque:true,row_order:'source_storage',source_origin:'bottom_left',sampler:{wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729}},files:[{name:'geometry.gltf',bytes:100,sha256:hash},{name:'geometry.bin',bytes:72,sha256:hash},{name:'texture.png',bytes:10,sha256:hash}]}));
 return {schema:parent?INDEXED_FAMILY_SCHEMA:MEMORY_ROOT_SCHEMA,source_format:MEMORY_SOURCE_FORMAT,tile_id:1,texture_policy:'original_pixels_v1',parts,source_nodes,indices:parts.length*3,gpu_payload_bytes:parts.length*208,...(parent?{replacement_parent:parent,parent_source_sha256:hash,complete_source_cut:true,source_cut_key:hash,min_depth:Math.min(...source_nodes.map(n=>n.depth)),max_depth:Math.max(...source_nodes.map(n=>n.depth)),family_key:'b'.repeat(16)}:{depth:1,complete_frontier:true})};}
if(!globalThis.ProgressEvent)globalThis.ProgressEvent=class ProgressEvent{constructor(type,values){this.type=type;Object.assign(this,values);}};
// Node has no browser image decoder. Stub only that platform boundary; the real
// loader still checks PNG/header/file SHA, PU geometry and private texture identity.
mock.method(THREE.TextureLoader.prototype,'loadAsync',async()=>new THREE.Texture({width:1,height:1}));
const sha=raw=>createHash('sha256').update(new Uint8Array(raw)).digest('hex');
async function runtime(input){
 const marker=structuredClone(input),binary=new ArrayBuffer(72);new Float32Array(binary,0,9).set([-1,-1,0,1,-1,0,0,1,0]);new Float32Array(binary,36,6).set([0,0,1,0,0,1]);new Uint32Array(binary,60,3).set([0,1,2]);
 const gltf={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2,material:0}]}],buffers:[{uri:'geometry.bin',byteLength:72}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:24},{buffer:0,byteOffset:60,byteLength:12}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[-1,-1,0],max:[1,1,0]},{bufferView:1,componentType:5126,count:3,type:'VEC2'},{bufferView:2,componentType:5125,count:3,type:'SCALAR'}],images:[{uri:'texture.png'}],textures:[{source:0,sampler:0}],samplers:[{wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729}],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}]};
 const json=new TextEncoder().encode(JSON.stringify(gltf)).buffer,png=Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64')).buffer,files={'geometry.gltf':json,'geometry.bin':binary,'texture.png':png},meshes=new Map();
 for(const part of marker.parts){part.files=Object.entries(files).map(([name,raw])=>({name,bytes:raw.byteLength,sha256:sha(raw)}));const page=await loadPreparedSourcePage({THREE,renderer:{capabilities:{maxTextureSize:8192}},part,supported:false,loadFile:async name=>files[name],reserve:()=>({release(){}})});meshes.set(part.directory,page.mesh);}
 return {marker:runtimeSourceBundle(marker,meshes),meshes};
}
test('a complete mixed-depth cut skips intermediate uploads and rolls nested descendants back through the sealed tree',async()=>{
 const tree=topology(),initial=await runtime(bundle([P])),frontier=new SourceFrontier(initial.marker,initial.meshes,{topology:tree}),cut=await runtime(bundle([G,H,B],P)),t=frontier.begin(cut.marker,1024*1024);
 cut.marker.parts.forEach((_,i)=>frontier.markReady(t,i));assert.equal(frontier.commit(t,cut.meshes),true);assert.equal(frontier.nodes.has(A),false);assert.equal(frontier.maxDepth,2);
 const deeper=await runtime(bundle([I,J],G)),u=frontier.begin(deeper.marker,1024*1024);deeper.marker.parts.forEach((_,i)=>frontier.markReady(u,i));frontier.commit(u,deeper.meshes);
 const plan=frontier.rollbackPlan(P);assert.ok(plan.subtree.has(A));assert.ok(plan.subtree.has(I));assert.equal(frontier.rollback(P).length,2);assert.deepEqual([...frontier.visible],[P]);assert.equal(frontier.bundles.size,1);
});
test('a mixed cut needs the verified same tree, every descendant branch, original hash/depth and complete upload',async()=>{
 const tree=topology(),root=await runtime(bundle([P])),frontier=new SourceFrontier(root.marker,root.meshes,{topology:tree}),valid=bundle([G,H,B],P);
 for(const mutate of [m=>m.source_nodes.pop(),m=>m.source_nodes[0].source_sha256='c'.repeat(64),m=>m.source_nodes[0].depth=1,m=>m.parent_source_sha256='c'.repeat(64),m=>m.complete_source_cut=false,m=>m.min_depth=99]){const m=structuredClone(valid);mutate(m);assert.throws(()=>validateIndexedSourceReplacement(tree,m,P));}
 const noTree=new SourceFrontier(root.marker,root.meshes);assert.throws(()=>noTree.begin(valid,1024*1024));const cut=await runtime(valid),t=frontier.begin(cut.marker,1024*1024);frontier.markReady(t,0);assert.equal(frontier.commit(t,cut.meshes),false);assert.deepEqual([...frontier.visible],[P]);frontier.cancel(t);assert.throws(()=>frontier.begin(cut.marker,1));
});
const view=[0,-10,12,0,0,0,52,1.5,720,6],request={id:1,parent:P,view};
const envelope=marker=>({schema:SOURCE_PLAN_SCHEMA,verification:'metadata_only',availabilityVerified:false,markerSHA256:hash,marker,indexedRequest:'b'.repeat(32),requestedPixels:6,selectedPixels:6,queryStats:{},selectionLimitedByBudget:false,selectedMaxDepth:null});
test('indexed request pins a bounded exact view, returns only a derived token URL, and verifies the real leased marker',async()=>{
 const tree=topology(),m=bundle([G,H,B],P),calls=[];const cache=new SourcePlanCache();const plan=await cache.read({request,topology:tree,fetcher:async url=>{calls.push(url);return Response.json(envelope(m));}});assert.ok(calls[0].endsWith('&wait_ms=200'));assert.equal(plan.bundleURL,'api/lod-index-family/1/'+'b'.repeat(32));assert.deepEqual(plan.sourceRequest,request);
 assert.equal(verifyPlannedSource(plan,new Response(null,{headers:{'X-XNBY-Source-Marker-SHA256':hash}}),{...m,cache_lease:'c'.repeat(32)}),true);
 await assert.rejects(readSourcePlan({request,topology:tree,fetcher:async()=>{const v=envelope(m);v.indexedRequest='../private';return Response.json(v);}}));
 for(const bad of [[...view.slice(0,9),513],view.map((v,i)=>i===8?1.5:v),view.map((v,i)=>i===6?180:v)])assert.throws(()=>sourcePlanURL({...request,view:bad}));
});
test('known original texture/page quality limits retain the parent without inventing a resource cut or lease',async()=>{
 const marker={schema:'zhumadian.indexed_quality_limit.v1',tile_id:1,replacement_parent:P,complete_parent_retained:true,index_identity:hash,reason_code:'lossless_texture_or_page_limit'};
 await assert.rejects(readSourcePlan({request,topology:topology(),fetcher:async()=>Response.json(envelope(marker))}),IndexedSourceQualityLimit);
});
