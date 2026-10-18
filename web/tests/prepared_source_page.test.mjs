import test from 'node:test';
import assert from 'node:assert/strict';
import {sourcePageSource,sourcePageGeometryBytes,loadPreparedSourcePage,runtimeSourceBundle,validateRuntimeSourceTexture,planPreparedSourceBundle,stagePreparedSourceBundle,SourcePagePlanChanged} from '../src/prepared_source_page.js';
import {sha256} from '../src/prepared_bc7.js';
const part=()=>({directory:'part_000',vertices:3,indices:3,atlas_size:16,atlas_extent:[16,16],gpu_payload_bytes:1568,files:[{name:'atlas.jpg',sha256:'a'.repeat(64),bytes:1}]});
test('source storage cost includes geometry and every original mip',()=>{
 const p=part();assert.equal(sourcePageGeometryBytes(p),204);assert.deepEqual(sourcePageSource(p),{width:16,height:16,sha256:'a'.repeat(64)});
});
test('runtime cost cannot replace the immutable original cost declaration',()=>{
 const p=part();p.gpu_payload_bytes=300;assert.throws(()=>sourcePageSource(p),/storage cost/);p.source_gpu_payload_bytes=1568;assert.equal(sourcePageSource(p).width,16);p.source_gpu_payload_bytes--;assert.throws(()=>sourcePageSource(p),/storage cost/);
});
test('geometry overflow, invalid indices, duplicate source photos are rejected',()=>{
 for(const change of [p=>p.indices=4,p=>p.vertices=Number.MAX_SAFE_INTEGER,p=>p.files.push({...p.files[0]}),p=>p.files[0].sha256='invalid']){const p=part();change(p);assert.throws(()=>sourcePageSource(p));}
});
test('caller-provided texture metadata does not prove a loaded runtime page',()=>{
 const p=part(),texture={isCompressedTexture:true,userData:{sourceSHA256:'a'.repeat(64)}},mesh={material:{map:texture}};
 assert.throws(()=>runtimeSourceBundle({parts:[p]},new Map([['part_000',mesh]])),/identity missing/);
 assert.throws(()=>validateRuntimeSourceTexture({...p,runtime_texture:{format:'bc7'}},texture),/identity mismatch/);
});
test('source GLTF bytes are SHA checked before any budget or GPU work',async()=>{
 const p=part(),bytes=new Uint8Array([1,2,3]).buffer;p.files.push({name:'geometry.gltf',bytes:3,sha256:await sha256(bytes)});let reserved=0;
 await assert.rejects(loadPreparedSourcePage({part:p,loadFile:async()=>new Uint8Array([1,2,4]).buffer,reserve:()=>{reserved++;throw Error('must not reserve');}}),/content mismatch/);assert.equal(reserved,0);
});
test('unsupported GLTF external files are rejected before geometry download',async()=>{
 const p=part(),raw=new TextEncoder().encode(JSON.stringify({asset:{version:'2.0'},buffers:[{uri:'https://external.test/data.bin'}]})).buffer;p.files.push({name:'geometry.gltf',bytes:raw.byteLength,sha256:await sha256(raw)});let downloads=0;
 await assert.rejects(loadPreparedSourcePage({part:p,loadFile:async name=>{downloads++;assert.equal(name,'geometry.gltf');return raw;},reserve:()=>{throw Error('must not reserve');}}),/GLTF files/);assert.equal(downloads,1);
});

function plannedFixture(){
 const p=part(),manifest={schema:'xnby.bc7.mip_chain.v1',format:'BC7_UNORM_BLOCK',sourceSHA256:'a'.repeat(64),sourceSize:[16,16],payloadSHA256:'b'.repeat(64),mips:[]};let size=16,offset=0;
 for(let level=0;;level++){const bytes=Math.ceil(size/4)**2*16;manifest.mips.push({level,width:size,height:size,offset,bytes,sha256:'c'.repeat(64)});offset+=bytes;if(size===1)break;size=Math.max(1,Math.floor(size/2));}manifest.payloadBytes=offset;
 return {p,manifest,marker:{parts:[p],gpu_payload_bytes:p.gpu_payload_bytes}};
}
test('descriptor preflight costs every compressed mip without reading geometry or payload',async()=>{
 const f=plannedFixture(),before=structuredClone(f.marker);let calls=0;const plan=await planPreparedSourceBundle({marker:f.marker,supported:true,loadManifest:async p=>{calls++;assert.equal(p,f.p);return f.manifest;}});
 assert.equal(calls,1);assert.equal(plan.marker.gpu_payload_bytes,572);assert.equal(plan.marker.parts[0].source_gpu_payload_bytes,1568);assert.equal(plan.marker.parts[0].runtime_texture.payloadSHA256,'b'.repeat(64));assert.deepEqual(f.marker,before);assert.ok(Object.isFrozen(plan.marker.parts[0].runtime_texture));assert.deepEqual(plan.fallbacks,[]);
});
test('unsupported, invalid descriptor and explicit fallback plans retain original whole-mip cost',async()=>{
 for(const mode of ['unsupported','invalid','explicit']){const f=plannedFixture();if(mode==='invalid')f.manifest.mips.pop();let calls=0;const plan=await planPreparedSourceBundle({marker:f.marker,supported:mode!=='unsupported',forceRgbaParts:new Set(mode==='explicit'?['part_000']:[]),loadManifest:async()=>{calls++;return f.manifest;}});assert.equal(plan.marker.gpu_payload_bytes,1568);assert.equal(plan.marker.parts[0].runtime_texture.format,'rgba8');assert.equal(calls,mode==='invalid'?1:0);assert.equal(plan.fallbacks.length,1);}
});
test('cancellation while descriptors load cannot silently become an original-image plan',async()=>{
 const f=plannedFixture();let wanted=true;await assert.rejects(planPreparedSourceBundle({marker:f.marker,supported:true,stillWanted:()=>wanted,loadManifest:async()=>{wanted=false;return f.manifest;}}),/plan no longer wanted/);
});
test('unknown forced pages and mismatched original family cost are rejected before staging',async()=>{
 const f=plannedFixture();await assert.rejects(planPreparedSourceBundle({marker:f.marker,supported:false,forceRgbaParts:new Set(['part_999'])}),/Unknown/);f.marker.gpu_payload_bytes++;await assert.rejects(planPreparedSourceBundle({marker:f.marker,supported:false}),/original cost/);
});
test('forged or changed plans are refused before scene creation or any download',async()=>{
 const f=plannedFixture(),plan=await planPreparedSourceBundle({marker:f.marker,supported:false});let groups=0;const THREE={Group:class{constructor(){groups++;throw Error('must not allocate');}}};
 await assert.rejects(stagePreparedSourceBundle({THREE,marker:f.marker,plan:{marker:plan.marker}}),/plan identity/);f.marker.parts[0].vertices++;await assert.rejects(stagePreparedSourceBundle({THREE,marker:f.marker,plan}),/plan identity/);assert.equal(groups,0);
});
test('an admitted compressed page must replan before original JPEG download or reservation',async()=>{
 const f=plannedFixture(),p=f.p,binary=new ArrayBuffer(36),gltf={asset:{version:'2.0'},buffers:[{uri:'geometry.bin',byteLength:36}],images:[{uri:'atlas.jpg'}],textures:[{source:0,sampler:0}],samplers:[{wrapS:33071,wrapT:33071,minFilter:9987,magFilter:9729}],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}],meshes:[{primitives:[{material:0,attributes:{POSITION:0,NORMAL:1,TEXCOORD_0:2},indices:3}]}],accessors:[{count:3},{count:3},{count:3},{count:3}]},raw=new TextEncoder().encode(JSON.stringify(gltf)).buffer;
 p.files.push({name:'geometry.gltf',bytes:raw.byteLength,sha256:await sha256(raw)},{name:'geometry.bin',bytes:36,sha256:await sha256(binary)});let held=0,jpeg=0;const reservations=[];
 await assert.rejects(loadPreparedSourcePage({part:p,supported:true,expectedIdentity:{format:'bc7'},loadFile:async name=>{if(name==='atlas.jpg'){jpeg++;throw Error('must not download original');}return name==='geometry.gltf'?raw:binary;},loadManifest:async()=>{throw Error('descriptor no longer available');},reserve:async({format,bytes})=>{reservations.push(format);held+=bytes;return {release(){held-=bytes;}};}}),SourcePagePlanChanged);
 assert.equal(held,0);assert.equal(jpeg,0);assert.deepEqual(reservations,['geometry']);
});
