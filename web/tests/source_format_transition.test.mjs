import test,{mock} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {SourceFrontier} from '../src/source_frontier.js';
import {validateLevelTile} from '../src/source_level_index.js';
import {loadPreparedSourcePage,runtimeSourceBundle} from '../src/prepared_source_page.js';
import {withSourceRestorations} from '../src/source_residency.js';
import {MEMORY_SOURCE_FORMAT,CROP_SOURCE_FORMAT,MEMORY_GEOMETRY_LAYOUT,MEMORY_ROOT_SCHEMA,MEMORY_FAMILY_SCHEMA} from '../src/source_page_format.js';
const hash='a'.repeat(64),P='Tile_1_L16_0u.osgb',A='Tile_1_L17_0uu.osgb',B='Tile_1_L17_0u0.osgb',rows=[[P,[A,B],0],[A,[],1],[B,[],1]];
function topology(){
 const nodes=rows.map(([name,children,depth])=>({name,children:[...children],depth,level:16+depth,sourceSHA256:hash,sourceBytes:100,triangles:1,boundsMin:[-1,-1,0],boundsMax:[1,1,0],subtreeMin:[-1,-1,0],subtreeMax:[1,1,0],edgeP90:1,texelP90:.1}));
 const t={schema:'zhumadian.level_bounds.tile.v1',tile:1,complete:true,sourceManifestSHA256:hash,catalogSHA256:hash,root:P,roots:[P],nodes};validateLevelTile(t,{tile:1,sourceManifestSHA256:hash,catalogSHA256:hash,sourceNodes:3,rootBounds:{boundsMin:[-1,-1,0],boundsMax:[1,1,0]}});return t;
}
function node(name,i){const row=rows.find(r=>r[0]===name);return{name,children:[...row[1]],depth:row[2],source_sha256:hash,triangles:1,longest_edge_p90_m:1,texel_world_p90_m:.1,bounds_min:[-1,-1,0],bounds_max:[1,1,0],spans:[{part:`part_${String(i).padStart(3,'0')}`,first:0,count:3}]};}
function geometry(){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([-1,-1,0,1,-1,0,0,1,0],3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,0,1],2));g.setIndex([0,1,2]);return g;}
function legacy(names=[P],parent=null){
 const meshes=new Map(),parts=names.map((name,i)=>{const directory=`part_${String(i).padStart(3,'0')}`,map=new THREE.DataTexture(new Uint8Array(4),1024,1024);meshes.set(directory,new THREE.Mesh(geometry(),new THREE.MeshBasicMaterial({map})));return{directory,vertices:3,indices:3,atlas_size:1024,gpu_payload_bytes:3*64+12+5592404};});
 const marker={schema:parent?'xnby.osgb_native_family.v1':'hongtu.osgb_native_chunk_bundle.v1',tile_id:1,texture_policy:'original_pixels_v1',parts,source_nodes:names.map(node),indices:3*parts.length,gpu_payload_bytes:parts.reduce((s,p)=>s+p.gpu_payload_bytes,0),...(parent?{replacement_parent:parent,parent_source_sha256:hash,complete_sibling_family:true}:{depth:1,complete_frontier:true})};return{marker,meshes};
}
if(!globalThis.ProgressEvent)globalThis.ProgressEvent=class ProgressEvent{constructor(type,v){this.type=type;Object.assign(this,v);}};
// Only the Node image-decoder boundary is mocked. The real GLTF/PNG byte SHA,
// PU layout, private texture identity and material validation still run.
mock.method(THREE.TextureLoader.prototype,'loadAsync',async()=>new THREE.Texture({width:1,height:1}));
async function memory(names=[A,B],parent=P,format=CROP_SOURCE_FORMAT){
 const sampler={wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729},binary=new ArrayBuffer(72);new Float32Array(binary,0,9).set([-1,-1,0,1,-1,0,0,1,0]);new Float32Array(binary,36,6).set([0,0,1,0,0,1]);new Uint32Array(binary,60,3).set([0,1,2]);
 const gltf={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2,material:0}]}],buffers:[{uri:'geometry.bin',byteLength:72}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:24},{buffer:0,byteOffset:60,byteLength:12}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[-1,-1,0],max:[1,1,0]},{bufferView:1,componentType:5126,count:3,type:'VEC2'},{bufferView:2,componentType:5125,count:3,type:'SCALAR'}],images:[{uri:'texture.png'}],textures:[{source:0,sampler:0}],samplers:[sampler],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}]};
 const files={'geometry.gltf':new TextEncoder().encode(JSON.stringify(gltf)).buffer,'geometry.bin':binary,'texture.png':Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64')).buffer};
 const parts=names.map((name,i)=>({directory:`part_${String(i).padStart(3,'0')}`,source_format:format,geometry_layout:MEMORY_GEOMETRY_LAYOUT,vertices:3,indices:3,gpu_payload_bytes:208,source_image:{file:'texture.png',width:1,height:1,opaque:true,row_order:'source_storage',source_origin:'bottom_left',sampler,...(format===CROP_SOURCE_FORMAT?{original_width:1,original_height:1,source_rect:[0,0,1,1],uv_transform:[1,1,0,0],mip_levels:1}:{})},files:Object.entries(files).map(([name,b])=>({name,bytes:b.byteLength,sha256:createHash('sha256').update(new Uint8Array(b)).digest('hex')}))}));
 const marker={schema:parent?MEMORY_FAMILY_SCHEMA:MEMORY_ROOT_SCHEMA,source_format:format,tile_id:1,texture_policy:'original_pixels_v1',parts,source_nodes:names.map(node),indices:parts.length*3,gpu_payload_bytes:parts.length*208,...(parent?{replacement_parent:parent,parent_source_sha256:hash,complete_sibling_family:true}:{depth:1,complete_frontier:true})},meshes=new Map();
 for(const part of parts){const page=await loadPreparedSourcePage({THREE,renderer:{capabilities:{maxTextureSize:8192}},part,supported:false,loadFile:async name=>files[name],reserve:()=>({release(){}})});meshes.set(part.directory,page.mesh);}
 return{marker:runtimeSourceBundle(marker,meshes),meshes};
}
function frontier(root=legacy(),tree=topology()){return new SourceFrontier(root.marker,root.meshes,{topology:tree,allowOriginalFormatTransition:true});}
function commit(f,c){const ticket=f.begin(c.marker,128*1048576);c.marker.parts.forEach((_,i)=>f.markReady(ticket,i));assert.equal(f.commit(ticket,c.meshes),true);return ticket;}
test('original format boundaries remain refused by default even with a verified tree',async()=>{const r=legacy(),c=await memory(),f=new SourceFrontier(r.marker,r.meshes,{topology:topology()});assert.throws(()=>f.begin(c.marker,128*1048576));assert.deepEqual([...f.visible],[P]);assert.equal(f.pending,null);});
test('explicit transition requires a verified same source tree and a boolean opt-in',()=>{
 const r=legacy();for(const options of [{allowOriginalFormatTransition:true},{topology:structuredClone(topology()),allowOriginalFormatTransition:true},{topology:topology(),allowOriginalFormatTransition:'yes'}])assert.throws(()=>new SourceFrontier(r.marker,r.meshes,options));
 const tree=topology();tree.nodes[0].sourceSHA256='b'.repeat(64);assert.throws(()=>frontier(r,tree));
});
test('complete PNG children replace a prepared parent only after every page is validated and ready',async()=>{
 const r=legacy(),f=frontier(r),c=await memory(),t=f.begin(c.marker,128*1048576);f.applyMasks();f.markReady(t,0);assert.equal(f.commit(t,c.meshes),false);assert.deepEqual([...f.visible],[P]);assert.equal(r.meshes.get('part_000').visible,true);
 f.markReady(t,1);assert.equal(f.commit(t,c.meshes),true);f.applyMasks();assert.deepEqual([...f.visible],[A,B]);assert.equal(r.meshes.get('part_000').visible,false);assert.equal(f.bytes,c.marker.gpu_payload_bytes);
});
test('the reverse PNG-parent to prepared-child boundary uses the same sealed proof',async()=>{const r=await memory([P],null),f=frontier(r),c=legacy([A,B],P);commit(f,c);assert.deepEqual([...f.visible],[A,B]);assert.equal(f.rollback(P).length,1);assert.deepEqual([...f.visible],[P]);});
test('same-origin opt-in cannot waive child hashes, depths, triangles or direct sibling completeness',async()=>{
 const c=await memory();for(const mutate of [m=>m.source_nodes[0].source_sha256='b'.repeat(64),m=>m.source_nodes[0].depth=2,m=>m.source_nodes[0].triangles=2,m=>m.source_nodes.pop(),m=>m.source_nodes[1].name=A,m=>m.parent_source_sha256='b'.repeat(64),m=>m.complete_sibling_family=false,m=>m.texture_policy='resampled_pixels']){
  const f=frontier(),bad=structuredClone(c.marker);mutate(bad);assert.throws(()=>f.begin(bad,128*1048576));assert.deepEqual([...f.visible],[P]);assert.equal(f.pending,null);
 }
});
test('original format boundaries cannot waive unknown formats or a raw policy change',async()=>{
 const root=await memory([P],null,MEMORY_SOURCE_FORMAT),c=await memory(),f=frontier(root);assert.throws(()=>f.begin(c.marker,128*1048576));
 const g=frontier(),bad=structuredClone(c.marker);bad.source_format='future_format';assert.throws(()=>g.begin(bad,128*1048576));assert.deepEqual([...g.visible],[P]);
});
test('staging budget refusal and cancellation keep the complete prepared parent',async()=>{
 const f=frontier(),c=await memory();assert.throws(()=>f.begin(c.marker,c.marker.gpu_payload_bytes-1));const t=f.begin(c.marker,c.marker.gpu_payload_bytes);f.markReady(t,0);assert.equal(f.cancel(t),true);assert.equal(f.commit(t,c.meshes),false);assert.deepEqual([...f.visible],[P]);
});
test('an unverified replacement texture is refused at commit without replacing the parent',async()=>{
 const f=frontier(),c=await memory(),t=f.begin(c.marker,128*1048576);c.marker.parts.forEach((_,i)=>f.markReady(t,i));c.meshes.get('part_001').material.map=new THREE.Texture({width:1,height:1});assert.throws(()=>f.commit(t,c.meshes));assert.deepEqual([...f.visible],[P]);f.cancel(t);
});
test('metadata changed after begin is revalidated before the live cut changes',async()=>{
 for(const mutate of [m=>m.parent_source_sha256='b'.repeat(64),m=>m.complete_sibling_family=false,m=>m.source_nodes[0].source_sha256='b'.repeat(64)]){const f=frontier(),c=await memory(),t=f.begin(c.marker,128*1048576);c.marker.parts.forEach((_,i)=>f.markReady(t,i));mutate(c.marker);assert.throws(()=>f.commit(t,c.meshes));assert.deepEqual([...f.visible],[P]);f.cancel(t);}
});
test('released prepared parent must be restored before a mixed family can roll back',async()=>{
 const f=frontier(),c=await memory();commit(f,c);f.applyMasks();const released=f.releaseHiddenPages();assert.equal(released.pages,1);assert.deepEqual(f.rollback(P),[]);assert.deepEqual([...f.visible],[A,B]);const root=f.bundles.get('$root');f.restorePages(root,legacy().meshes);assert.equal(f.rollback(P).length,1);f.applyMasks();assert.deepEqual([...f.visible],[P]);assert.equal(f.bytes,root.marker.gpu_payload_bytes);
});
test('mixed restoration obeys the live-children plus parent staging peak before reading',async()=>{
 const f=frontier(),c=await memory();commit(f,c);f.applyMasks();f.releaseHiddenPages();let reads=0;const parentBytes=f.bundles.get('$root').marker.gpu_payload_bytes;
 await assert.rejects(withSourceRestorations({actions:[{root:1,parent:P}],residents:new Map([[1,{frontier:f}]]),load:async()=>{reads++;},stillWanted:()=>true,apply:()=>{},limit:parentBytes}));assert.equal(reads,0);assert.deepEqual([...f.visible],[A,B]);
});
test('a fully validated restored parent atomically rolls back and disposes staging once',async()=>{
 const f=frontier(),c=await memory();commit(f,c);f.applyMasks();f.releaseHiddenPages();let disposed=0;
 await withSourceRestorations({actions:[{root:1,parent:P}],residents:new Map([[1,{frontier:f}]]),load:async({bundle})=>({marker:structuredClone(bundle.marker),meshes:legacy().meshes,dispose(){disposed++;}}),stillWanted:()=>true,limit:128*1048576,apply:batches=>{for(const b of batches)f.restorePages(b.bundle,b.meshes);f.rollback(P);f.applyMasks();}});
 assert.deepEqual([...f.visible],[P]);assert.equal(disposed,1);
});
test('changed restored identity leaves the complete live PNG child cut intact',async()=>{
 const f=frontier(),c=await memory();commit(f,c);f.applyMasks();f.releaseHiddenPages();let disposed=0;
 await assert.rejects(withSourceRestorations({actions:[{root:1,parent:P}],residents:new Map([[1,{frontier:f}]]),load:async({bundle})=>({marker:{...structuredClone(bundle.marker),tile_id:2},meshes:legacy().meshes,dispose(){disposed++;}}),stillWanted:()=>true,limit:128*1048576,apply:()=>assert.fail('must preserve live children')}));
 assert.deepEqual([...f.visible],[A,B]);assert.equal(disposed,1);assert.equal(f.bundles.get('$root').meshes.size,0);
});
