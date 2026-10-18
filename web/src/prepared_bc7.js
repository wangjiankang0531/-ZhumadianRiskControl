// Read-only prepared texture consumption. Never encodes or repairs a resource.
import {SourceLoadCancelled} from './lod_transaction.js';
export class PreparedTextureContextError extends Error {}
export class PreparedTextureCancelled extends SourceLoadCancelled {constructor(message){super();this.name='PreparedTextureCancelled';this.message=message;}}
const SHA=/^[0-9a-f]{64}$/;
const require=(ok,message)=>{if(!ok)throw Error(message);};
const positive=n=>Number.isSafeInteger(n)&&n>0;
export function rgbaMipBytes(width,height){
 require(positive(width)&&positive(height)&&width<=2048&&height<=2048,'Invalid prepared texture size');
 let bytes=0;
 for(;;){bytes+=width*height*4;if(width===1&&height===1)return bytes;width=Math.max(1,Math.floor(width/2));height=Math.max(1,Math.floor(height/2));}
}
export async function sha256(bytes){
 const result=await crypto.subtle.digest('SHA-256',bytes);
 return [...new Uint8Array(result)].map(n=>n.toString(16).padStart(2,'0')).join('');
}
// Descriptor checks are usable before allocating a page or downloading its payload.
// Content hashes are still verified separately against the actual bytes at load time.
export function describePreparedBc7(manifest,source){
 require(manifest?.schema==='xnby.bc7.mip_chain.v1'&&manifest.format==='BC7_UNORM_BLOCK','Unsupported prepared BC7 descriptor');
 require(source&&SHA.test(source.sha256)&&manifest.sourceSHA256===source.sha256,'Prepared BC7 source identity mismatch');
 const [width,height]=manifest.sourceSize??[];rgbaMipBytes(width,height);
 require(width===source.width&&height===source.height&&width%4===0&&height%4===0,'Prepared BC7 dimensions do not match the source or WebGL format');
 require(positive(manifest.payloadBytes)&&manifest.payloadBytes<=32*1048576&&SHA.test(manifest.payloadSHA256),'Invalid prepared BC7 payload size or digest');
 require(Array.isArray(manifest.mips)&&manifest.mips.length>0&&manifest.mips.length<=12,'Invalid prepared BC7 mip count');
 let w=width,h=height,offset=0,complete=false;const mips=[];
 for(let i=0;i<manifest.mips.length;i++){
  const row=manifest.mips[i],bytes=Math.ceil(w/4)*Math.ceil(h/4)*16;
  require(row&&!complete&&row.level===i&&row.width===w&&row.height===h&&row.offset===offset&&row.bytes===bytes&&offset+bytes<=manifest.payloadBytes&&SHA.test(row.sha256),'Prepared BC7 mip layout mismatch');
  mips.push({level:i,width:w,height:h,offset,bytes,sha256:row.sha256});offset+=bytes;complete=w===1&&h===1;
  w=Math.max(1,Math.floor(w/2));h=Math.max(1,Math.floor(h/2));
 }
 require(complete&&offset===manifest.payloadBytes,'Prepared BC7 mip chain is incomplete or has trailing bytes');
 return {mips,width,height,bytes:manifest.payloadBytes,sourceSHA256:source.sha256,payloadSHA256:manifest.payloadSHA256};
}
export async function validatePreparedBc7(manifest,payload,source){
 const descriptor=describePreparedBc7(manifest,source);
 require(payload instanceof ArrayBuffer&&payload.byteLength===descriptor.bytes,'Invalid prepared BC7 payload size');
 require(await sha256(payload)===descriptor.payloadSHA256,'Prepared BC7 payload digest mismatch');
 const mips=[];
 for(const row of descriptor.mips){const data=new Uint8Array(payload,row.offset,row.bytes);require(await sha256(data)===row.sha256,'Prepared BC7 mip digest mismatch');mips.push({data,width:row.width,height:row.height});}
 return {...descriptor,mips};
}
export function supportsPreparedBc7(renderer){
 return renderer.extensions.has('EXT_texture_compression_bptc')===true;
}
export function uploadPreparedBc7(THREE,renderer,prepared){
 require(supportsPreparedBc7(renderer),'Prepared BC7 is unsupported');
 const gl=renderer.getContext();
 if(gl.isContextLost?.()||gl.getError()!==gl.NO_ERROR)throw new PreparedTextureContextError('WebGL context is lost or already has an error');
 const texture=new THREE.CompressedTexture(prepared.mips,prepared.width,prepared.height,THREE.RGBA_BPTC_Format,THREE.UnsignedByteType);
 texture.colorSpace=THREE.SRGBColorSpace;texture.flipY=false;texture.generateMipmaps=false;
 texture.minFilter=THREE.LinearMipmapLinearFilter;texture.magFilter=THREE.LinearFilter;
 texture.wrapS=THREE.ClampToEdgeWrapping;texture.wrapT=THREE.ClampToEdgeWrapping;texture.needsUpdate=true;
 try{renderer.initTexture(texture);if(gl.isContextLost?.())throw new PreparedTextureContextError('WebGL context lost during texture upload');require(gl.getError()===gl.NO_ERROR,'WebGL rejected prepared BC7 upload');return texture;}
 catch(error){texture.dispose();throw error;}
}
export async function loadPreparedPhotograph({supported,source,loadManifest,loadPayload,upload,loadFallback,reserve,stillWanted=()=>true,onFallback=()=>{}}){
 require(typeof reserve==='function','A shared GPU budget reservation is required');
 const originalBytes=rgbaMipBytes(source.width,source.height);
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Texture request no longer wanted');};
 const lease=async(format,bytes)=>{wanted();const owned=await reserve({format,bytes});require(typeof owned?.release==='function','Invalid texture budget reservation');return owned;};
 const finish=(texture,owned,format,bytes,fallbackReason,payloadSHA256=null)=>{
  let released=false;const release=()=>{if(!released){released=true;owned.release();}};
  texture.addEventListener?.('dispose',release);
  return {texture,format,bytes,fallbackReason,payloadSHA256,dispose(){if(released)return;try{texture.dispose?.();}finally{release();}}};
 };
 const fallback=async(reason,error)=>{
  wanted();onFallback(reason,error);
  // RGBA may cost more than BC7. Re-admit it before even starting the fallback.
  const owned=await lease('rgba8',originalBytes);let texture;
  try{wanted();texture=await loadFallback();wanted();return finish(texture,owned,'rgba8',originalBytes,reason);}
  catch(error){texture?.dispose?.();owned.release();throw error;}
 };
 wanted();if(!supported)return fallback('unsupported');
 let prepared;
 try{const manifest=await loadManifest();wanted();const payload=await loadPayload(manifest);wanted();prepared=await validatePreparedBc7(manifest,payload,source);wanted();}
 catch(error){if(error instanceof PreparedTextureCancelled)throw error;return fallback('prepared_unavailable_or_invalid',error);}
 const owned=await lease('bc7',prepared.bytes);let texture;
 try{wanted();texture=await upload(prepared);wanted();return finish(texture,owned,'bc7',prepared.bytes,null,prepared.payloadSHA256);}
 catch(error){texture?.dispose?.();owned.release();if(error instanceof PreparedTextureContextError||error instanceof PreparedTextureCancelled)throw error;prepared=null;return fallback('upload_failed',error);}
}
