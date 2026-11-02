import test from 'node:test';
import assert from 'node:assert/strict';
import {planClientSourceCrop,verifiedClientSourceCrop} from '../src/source_client_crop.js';
const digest=async bytes=>Buffer.from(await crypto.subtle.digest('SHA-256',bytes)).toString('hex');
async function fixture({uv=[.2,.2,.7,.2,.2,.7],indices=[0,1,2],old=[0,0,16,12],sampler={wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729}}={}){
 const vertices=uv.length/2,positions=new Float32Array(vertices*3),texture=new Float32Array(uv),index=new Uint32Array(indices),binary=new ArrayBuffer(positions.byteLength+texture.byteLength+index.byteLength),views=[];
 let offset=0;for(const value of [positions,texture,index]){new Uint8Array(binary,offset,value.byteLength).set(new Uint8Array(value.buffer));views.push({buffer:0,byteOffset:offset,byteLength:value.byteLength});offset+=value.byteLength;}
 const gltf={asset:{version:'2.0'},buffers:[{uri:'geometry.bin',byteLength:binary.byteLength}],bufferViews:views,accessors:[{bufferView:0,type:'VEC3',componentType:5126,count:vertices},{bufferView:1,type:'VEC2',componentType:5126,count:vertices},{bufferView:2,type:'SCALAR',componentType:5125,count:indices.length}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2}]}],nodes:[{mesh:0}],scene:0,scenes:[{nodes:[0]}]},jsonBytes=new TextEncoder().encode(JSON.stringify(gltf)).buffer;
 const mips=sampler.minFilter===9729||sampler.minFilter===9728?1:1+Math.floor(Math.log2(Math.max(old[2],old[3])));
 const part={directory:'part_000',source_format:'osgb_memory_png_crop_v2',geometry_layout:'three_float32_pu_uint32_v1',vertices,indices:indices.length,source_image:{file:'texture.png',width:old[2],height:old[3],original_width:16,original_height:12,opaque:true,row_order:'source_storage',source_origin:'bottom_left',source_rect:old,uv_transform:[16/old[2],12/old[3],-old[0]/old[2],-old[1]/old[3]],mip_levels:mips,sampler},files:[{name:'geometry.gltf',bytes:jsonBytes.byteLength,sha256:await digest(jsonBytes)},{name:'geometry.bin',bytes:binary.byteLength,sha256:await digest(binary)},{name:'texture.png',bytes:100,sha256:'a'.repeat(64)}]};
 return {part,jsonBytes,binary};
}
test('pinned referenced UV footprint keeps original identities and exact source/local rectangles',async()=>{
 const f=await fixture(),before=JSON.stringify(f.part),binary=Buffer.from(f.binary).toString('hex'),plan=await planClientSourceCrop(f);
 assert.equal(plan.changed,true);assert.deepEqual(plan.sourceRect,[1,0,12,10]);assert.deepEqual(plan.bitmapRect,[1,0,12,10]);assert.deepEqual(plan.transform,[16/12,12/10,-1/12,0]);assert.equal(plan.savedTextureBytes,(16*12-12*10)*4);
 assert.equal(plan.sourcePNG_SHA256,'a'.repeat(64));assert.equal(plan.geometryBIN_SHA256,await digest(f.binary));assert.equal(JSON.stringify(f.part),before);assert.equal(Buffer.from(f.binary).toString('hex'),binary);assert.equal(verifiedClientSourceCrop(plan),true);assert.equal(verifiedClientSourceCrop(structuredClone(plan)),false);
 assert.throws(()=>plan.sourceRect[0]=9,TypeError);assert.throws(()=>plan.sampler.wrapS=0,TypeError);
});
test('existing nonzero source crop maps to bitmap-local bounds without rewriting UVs',async()=>{
 const f=await fixture({old:[1,0,14,11]}),plan=await planClientSourceCrop(f);assert.deepEqual(plan.sourceRect,[1,0,12,10]);assert.deepEqual(plan.bitmapRect,[0,0,12,10]);assert.deepEqual(plan.inputDimensions,[14,11]);
});
test('unreferenced UV outliers do not expand footprint and repeated references keep it unchanged',async()=>{
 const a=await fixture(),b=await fixture({uv:[.2,.2,.7,.2,.2,.7,1e6,-1e6],indices:[0,1,2,2,1,0]});assert.deepEqual((await planClientSourceCrop(a)).sourceRect,(await planClientSourceCrop(b)).sourceRect);
});
test('nearest and mipmapped sampling retain the entire original image',async()=>{
 for(const [min,mag,reason] of [[9728,9728,'nonlinear_sampler_retained'],[9729,9728,'nonlinear_sampler_retained'],[9987,9729,'mipmapped_source']]){
  const f=await fixture({sampler:{wrapS:33071,wrapT:33071,minFilter:min,magFilter:mag}}),plan=await planClientSourceCrop(f);assert.equal(plan.changed,false);assert.equal(plan.reason,reason);assert.equal(plan.savedTextureBytes,0);assert.deepEqual(plan.sourceRect,f.part.source_image.source_rect);
 }
});
test('periodic seam footprints retain source while interior footprints can crop',async()=>{
 for(const wrap of [10497,33648]){const sampler={wrapS:wrap,wrapT:wrap,minFilter:9729,magFilter:9729};const inside=await planClientSourceCrop(await fixture({sampler}));assert.equal(inside.changed,true);const seam=await planClientSourceCrop(await fixture({sampler,uv:[-.1,.2,.7,.2,.2,.7]}));assert.equal(seam.changed,false);assert.equal(seam.reason,'periodic_seam_or_border');}
});
test('clamp edge coordinates keep required borders and reject impossible delivered crops',async()=>{
 const whole=await planClientSourceCrop(await fixture({uv:[-1,-1,2,-1,-1,2]}));assert.equal(whole.changed,false);assert.deepEqual(whole.sourceRect,[0,0,16,12]);
 await assert.rejects(planClientSourceCrop(await fixture({old:[14,10,2,2]})),/outside delivered image/);
});
test('corrupt geometry, wrong counts and escaped accessors never produce verified plans',async()=>{
 const bad=await fixture();new Uint8Array(bad.binary)[0]^=1;await assert.rejects(planClientSourceCrop(bad),/SHA differs/);
 const badJSON=await fixture();new Uint8Array(badJSON.jsonBytes)[0]^=1;await assert.rejects(planClientSourceCrop(badJSON),/SHA differs/);
 const count=await fixture();count.part.vertices++;await assert.rejects(planClientSourceCrop(count),/geometry/);
 const index=await fixture({indices:[0,1,9]});await assert.rejects(planClientSourceCrop(index),/index out of range/);
});
test('unversioned geometry and unknown sampling contract fail before any decision',async()=>{
 for(const mutate of [f=>f.part.source_format='osgb_memory_png_v1',f=>f.part.source_image.uv_transform[0]=2,f=>f.part.source_image.sampler.wrapS=0]){const f=await fixture();mutate(f);await assert.rejects(planClientSourceCrop(f));}
});
