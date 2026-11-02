import {validatePreparedBc7Quality} from './prepared_bc7_quality.js';
import {rgbaMipBytes,sha256} from './prepared_bc7.js';
const SHA=/^[0-9a-f]{64}$/;
const require=(ok,message)=>{if(!ok)throw Error('Hybrid texture: '+message);};
const preparedIdentities=new WeakSet();
export const isValidatedHybridTexture=value=>preparedIdentities.has(value);
export const HYBRID_TEXTURE_SCHEMA='xnby.bc7_rgba_tail.v1';
export function describeHybridTexture(manifest,source){
 require(manifest?.schema===HYBRID_TEXTURE_SCHEMA&&manifest.format==='BC7_PREFIX_RGBA8_TAIL','unsupported schema');
 require(source&&SHA.test(source.sha256)&&manifest.sourceSHA256===source.sha256,'source identity differs');validatePreparedBc7Quality(manifest);
 const [width,height]=manifest.sourceSize??[];const original=rgbaMipBytes(width,height);require(width===source.width&&height===source.height&&width%4===0&&height%4===0,'source dimensions differ');
 const start=manifest.tailStartLevel,rows=manifest.mips;require(Number.isInteger(start)&&start>0&&start<rows.length,'prefix and tail must be nonempty');
 const components=manifest.components;require(components&&Object.keys(components).length===2&&components.bc7&&components.rgba8,'invalid components');
 for(const [kind,file] of [['bc7','prefix.bc7'],['rgba8','tail.rgba']]){const item=components[kind];require(item.file===file&&Number.isSafeInteger(item.bytes)&&item.bytes>0&&item.bytes<=8*1048576&&SHA.test(item.sha256),'component identity differs');}
 require(Number.isSafeInteger(manifest.payloadBytes)&&manifest.payloadBytes===components.bc7.bytes+components.rgba8.bytes&&manifest.payloadBytes<original&&SHA.test(manifest.payloadSHA256),'invalid total bytes');
 let w=width,h=height,complete=false;const offsets={bc7:0,rgba8:0},mips=[];
 for(let i=0;i<rows.length;i++){
  const row=rows[i],kind=i<start?'bc7':'rgba8',bytes=kind==='bc7'?Math.ceil(w/4)*Math.ceil(h/4)*16:w*h*4;
  require(!complete&&row.level===i&&row.width===w&&row.height===h&&row.offset===offsets[kind]&&row.bytes===bytes&&row.format===kind&&SHA.test(row.sha256)&&SHA.test(row.decodedRgbaSHA256),'invalid mip layout/proof');
  if(kind==='rgba8')require(row.sha256===row.decodedRgbaSHA256&&row.quality.rgbPSNR===999&&row.quality.rgbChannelP99===0&&row.quality.rgbMaxError===0,'tail must preserve exact mip bytes');
  mips.push({level:i,width:w,height:h,format:kind,offset:row.offset,bytes,sha256:row.sha256,decodedRgbaSHA256:row.decodedRgbaSHA256});offsets[kind]+=bytes;complete=w===1&&h===1;w=Math.max(1,w>>1);h=Math.max(1,h>>1);
 }
 require(complete&&offsets.bc7===components.bc7.bytes&&offsets.rgba8===components.rgba8.bytes,'incomplete or trailing chain');
 return {width,height,tailStartLevel:start,bytes:manifest.payloadBytes,payloadSHA256:manifest.payloadSHA256,sourceSHA256:source.sha256,components:structuredClone(components),mips};
}
export async function validateHybridTexture(manifest,prefix,tail,source){
 const descriptor=describeHybridTexture(manifest,source);
 for(const [kind,payload] of [['bc7',prefix],['rgba8',tail]])require(payload instanceof ArrayBuffer&&payload.byteLength===descriptor.components[kind].bytes&&await sha256(payload)===descriptor.components[kind].sha256,'component bytes differ');
 const combined=new Uint8Array(prefix.byteLength+tail.byteLength);combined.set(new Uint8Array(prefix));combined.set(new Uint8Array(tail),prefix.byteLength);require(await sha256(combined)===descriptor.payloadSHA256,'combined payload differs');
 const mips=[];
 for(const row of descriptor.mips){const buffer=row.format==='bc7'?prefix:tail,data=new Uint8Array(buffer,row.offset,row.bytes);require(await sha256(data)===row.sha256,'mip payload differs');if(row.format==='rgba8')for(let i=3;i<data.length;i+=4)require(data[i]===255,'tail is not opaque');mips.push({...row,data});}
 for(const component of Object.values(descriptor.components))Object.freeze(component);Object.freeze(descriptor.components);
 const prepared=Object.freeze({...descriptor,mips:Object.freeze(mips.map(Object.freeze))});preparedIdentities.add(prepared);return prepared;
}
// Shared by the hardware proof and the later scene-material adapter.
// Samples are linear values when both textures have SRGB internal formats.
export const HYBRID_EXPLICIT_LOD_GLSL=`
vec4 hybridAtLod(sampler2D prefixImage,sampler2D tailImage,vec2 uv,float lod,float tailStart){
 float bounded=max(0.0,lod),last=tailStart-1.0;
 if(bounded<=last)return textureLod(prefixImage,uv,bounded);
 if(bounded>=tailStart)return textureLod(tailImage,uv,bounded-tailStart);
 return mix(textureLod(prefixImage,uv,last),textureLod(tailImage,uv,0.0),bounded-last);
}`;
export function uploadHybridRaw(gl,prepared,{srgb=false,linear=false}={}){
 require(preparedIdentities.has(prepared),'unverified upload');require(!gl.isContextLost()&&gl.getError()===gl.NO_ERROR,'context unavailable');
 const extension=gl.getExtension('EXT_texture_compression_bptc');require(extension,'BC7 unavailable');
 const previous=gl.getParameter(gl.TEXTURE_BINDING_2D),states=[gl.UNPACK_ALIGNMENT,gl.UNPACK_FLIP_Y_WEBGL,gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,gl.UNPACK_COLORSPACE_CONVERSION_WEBGL].map(p=>[p,gl.getParameter(p)]),textures=[];
 const check=()=>require(!gl.isContextLost()&&gl.getError()===gl.NO_ERROR,'GPU rejected upload');
 const allocate=(kind,width,height,levels)=>{
  const texture=gl.createTexture();require(texture,'texture allocation failed');textures.push(texture);gl.bindTexture(gl.TEXTURE_2D,texture);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,linear?gl.LINEAR_MIPMAP_LINEAR:gl.NEAREST_MIPMAP_NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,linear?gl.LINEAR:gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAX_LEVEL,levels-1);
  const format=kind==='bc7'?(srgb?extension.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:extension.COMPRESSED_RGBA_BPTC_UNORM_EXT):(srgb?gl.SRGB8_ALPHA8:gl.RGBA8);
  gl.texStorage2D(gl.TEXTURE_2D,levels,format,width,height);check();return {texture,format};
 };
 try{
  gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);
  const prefix=allocate('bc7',prepared.width,prepared.height,prepared.tailStartLevel);
  for(const row of prepared.mips.filter(r=>r.format==='bc7')){gl.compressedTexSubImage2D(gl.TEXTURE_2D,row.level,0,0,row.width,row.height,prefix.format,row.data);check();}
  const base=prepared.mips[prepared.tailStartLevel],tail=allocate('rgba8',base.width,base.height,prepared.mips.length-prepared.tailStartLevel);
  for(const row of prepared.mips.filter(r=>r.format==='rgba8')){gl.texSubImage2D(gl.TEXTURE_2D,row.level-prepared.tailStartLevel,0,0,row.width,row.height,gl.RGBA,gl.UNSIGNED_BYTE,row.data);check();}
  let disposed=false;return {prefix:prefix.texture,tail:tail.texture,bytes:prepared.bytes,tailStartLevel:prepared.tailStartLevel,dispose(){if(!disposed){disposed=true;for(const texture of textures)gl.deleteTexture(texture);}}};
 }catch(error){for(const texture of textures)gl.deleteTexture(texture);throw error;}
 finally{gl.bindTexture(gl.TEXTURE_2D,previous);for(const [p,value] of states)gl.pixelStorei(p,value);}
}
