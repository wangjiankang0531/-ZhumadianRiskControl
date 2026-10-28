import test from 'node:test';
import assert from 'node:assert/strict';
import {sha256,describePreparedBc7} from '../src/prepared_bc7.js';
import {describeHybridTexture,validateHybridTexture,uploadHybridRaw} from '../src/prepared_hybrid_texture.js';
async function fixture(){
 const prefix=new Uint8Array(16).fill(31).buffer,tail=new Uint8Array(20);for(let i=0;i<5;i++)tail.set([31,47,63,255],i*4);
 const combined=new Uint8Array(36);combined.set(new Uint8Array(prefix));combined.set(tail,16);const source={sha256:'a'.repeat(64),width:4,height:4};
 const mips=[{level:0,width:4,height:4,format:'bc7',offset:0,bytes:16,sha256:await sha256(prefix),decodedRgbaSHA256:'b'.repeat(64),accepted:true,quality:{rgbPSNR:50,rgbChannelP99:1,rgbMaxError:2}}];
 for(const [level,size,offset,bytes] of [[1,2,0,16],[2,1,16,4]]){const digest=await sha256(tail.subarray(offset,offset+bytes));mips.push({level,width:size,height:size,format:'rgba8',offset,bytes,sha256:digest,decodedRgbaSHA256:digest,accepted:true,quality:{rgbPSNR:999,rgbChannelP99:0,rgbMaxError:0}});}
 return {prefix,tail:tail.buffer,source,manifest:{schema:'xnby.bc7_rgba_tail.v1',format:'BC7_PREFIX_RGBA8_TAIL',sourceSHA256:source.sha256,sourceSize:[4,4],tailStartLevel:1,components:{bc7:{file:'prefix.bc7',bytes:16,sha256:await sha256(prefix)},rgba8:{file:'tail.rgba',bytes:20,sha256:await sha256(tail)}},payloadBytes:36,payloadSHA256:await sha256(combined),mips,accepted:true,qualityThresholds:{rgbPSNRMin:40,rgbChannelP99Max:16,rgbMaxErrorMax:96}}};
}
test('hybrid complete chain accounts both components and freezes admitted metadata',async()=>{
 const f=await fixture(),prepared=await validateHybridTexture(f.manifest,f.prefix,f.tail,f.source);assert.equal(prepared.bytes,36);assert.equal(prepared.mips.length,3);assert.equal(prepared.mips[0].data.buffer,f.prefix);assert.equal(prepared.mips[1].data.buffer,f.tail);assert.ok(Object.isFrozen(prepared));assert.ok(Object.isFrozen(prepared.mips));assert.throws(()=>prepared.bytes=1);
});
test('incomplete chains shifted offsets failed quality and nonexact tails are rejected',async()=>{
 const f=await fixture();assert.throws(()=>describePreparedBc7(f.manifest,f.source),/Unsupported prepared BC7/);for(const mutate of [m=>m.schema='xnby.bc7.mip_chain.v1',m=>m.tailStartLevel=0,m=>m.tailStartLevel=3,m=>m.tailStartLevel=1.0+Number.EPSILON,m=>m.mips.pop(),m=>m.mips[1].offset=1,m=>m.mips[1].format='bc7',m=>m.mips[0].accepted=false,m=>m.mips[0].quality.rgbPSNR=39,m=>m.mips[1].quality.rgbPSNR=50,m=>m.mips[1].decodedRgbaSHA256='0'.repeat(64),m=>m.components.rgba8.file='../other',m=>m.payloadBytes++]){const value=structuredClone(f.manifest);mutate(value);assert.throws(()=>describeHybridTexture(value,f.source));}
});
test('component complete and per-mip digests are checked independently',async()=>{
 const f=await fixture();for(const mutate of [m=>m.components.bc7.sha256='0'.repeat(64),m=>m.components.rgba8.sha256='0'.repeat(64),m=>m.payloadSHA256='0'.repeat(64),m=>m.mips[0].sha256='0'.repeat(64)]){const value=structuredClone(f.manifest);mutate(value);await assert.rejects(validateHybridTexture(value,f.prefix,f.tail,f.source));}
});
test('even hash-consistent tail bytes must remain opaque',async()=>{
 const f=await fixture(),tail=new Uint8Array(f.tail);tail[3]=0;f.manifest.components.rgba8.sha256=await sha256(tail);f.manifest.mips[1].sha256=f.manifest.mips[1].decodedRgbaSHA256=await sha256(tail.subarray(0,16));const combined=new Uint8Array(36);combined.set(new Uint8Array(f.prefix));combined.set(tail,16);f.manifest.payloadSHA256=await sha256(combined);await assert.rejects(validateHybridTexture(f.manifest,f.prefix,f.tail,f.source),/opaque/);
});
function fakeGl(failSecond=false){
 const gl={};for(const name of ['TEXTURE_BINDING_2D','UNPACK_ALIGNMENT','UNPACK_FLIP_Y_WEBGL','UNPACK_PREMULTIPLY_ALPHA_WEBGL','UNPACK_COLORSPACE_CONVERSION_WEBGL','TEXTURE_2D','TEXTURE_MIN_FILTER','TEXTURE_MAG_FILTER','LINEAR_MIPMAP_LINEAR','NEAREST_MIPMAP_NEAREST','LINEAR','NEAREST','TEXTURE_WRAP_S','TEXTURE_WRAP_T','CLAMP_TO_EDGE','TEXTURE_MAX_LEVEL','SRGB8_ALPHA8','RGBA8','RGBA','UNSIGNED_BYTE','NONE'])gl[name]=name;
 const previous={old:true},states=new Map([[gl.UNPACK_ALIGNMENT,4],[gl.UNPACK_FLIP_Y_WEBGL,true],[gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true],[gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,'browser-default']]);let binding=previous,count=0,error=0;const deleted=[],storage=[];
 Object.assign(gl,{NO_ERROR:0,isContextLost:()=>false,getError:()=>{const old=error;error=0;return old;},getExtension:()=>({COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:17,COMPRESSED_RGBA_BPTC_UNORM_EXT:16}),getParameter:p=>p===gl.TEXTURE_BINDING_2D?binding:states.get(p),createTexture:()=>({id:++count}),deleteTexture:t=>deleted.push(t.id),bindTexture:(_t,v)=>binding=v,texParameteri(){},pixelStorei:(p,v)=>states.set(p,v),texStorage2D:(...args)=>{storage.push(args);if(failSecond&&storage.length===2)error=1285;},compressedTexSubImage2D(){},texSubImage2D(){}});
 return {gl,deleted,storage,restored:()=>binding===previous&&states.get(gl.UNPACK_ALIGNMENT)===4&&states.get(gl.UNPACK_FLIP_Y_WEBGL)===true&&states.get(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL)===true&&states.get(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL)==='browser-default'};
}
test('second texture failure releases both allocations and restores caller GL state',async()=>{
 const f=await fixture(),prepared=await validateHybridTexture(f.manifest,f.prefix,f.tail,f.source),gpu=fakeGl(true);assert.throws(()=>uploadHybridRaw(gpu.gl,prepared),/GPU rejected/);assert.deepEqual(gpu.deleted,[1,2]);assert.ok(gpu.restored());
});
test('owned texture pair is disposed once and unverified metadata cannot allocate',async()=>{
 const f=await fixture(),prepared=await validateHybridTexture(f.manifest,f.prefix,f.tail,f.source),gpu=fakeGl();assert.throws(()=>uploadHybridRaw(gpu.gl,{...prepared}),/unverified/);assert.equal(gpu.storage.length,0);const pair=uploadHybridRaw(gpu.gl,prepared,{srgb:true,linear:true});assert.equal(pair.bytes,36);assert.equal(gpu.storage[0][1],1);assert.equal(gpu.storage[1][1],2);assert.equal(gpu.storage[0][2],17);assert.equal(gpu.storage[1][2],gpu.gl.SRGB8_ALPHA8);assert.ok(gpu.restored());pair.dispose();pair.dispose();assert.deepEqual(gpu.deleted,[1,2]);
});
