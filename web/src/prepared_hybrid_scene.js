import {describeHybridTexture,validateHybridTexture} from './prepared_hybrid_texture.js';
import {describeHybridOverlap,validateHybridOverlap} from './prepared_hybrid_overlap.js';
import {describePreparedBc7,loadPreparedPhotograph,sha256,PreparedTextureCancelled,PreparedTextureContextError} from './prepared_bc7.js';
const require=(ok,message)=>{if(!ok)throw Error('Hybrid scene: '+message);},identities=new WeakMap();
export function describeScenePhotograph(manifest,source){
 if(manifest?.schema!=='xnby.prepared_hybrid_scene.v1')return {...describePreparedBc7(manifest,source),format:'bc7'};
 require(manifest.format==='BC7_RGBA_OVERLAP'&&manifest.sourceSHA256===source.sha256&&manifest.sourceSize?.[0]===source.width&&manifest.sourceSize?.[1]===source.height,'source identity differs');
 const base=describeHybridTexture(manifest.texture,source),overlap=describeHybridOverlap(base,manifest.overlap),bytes=base.bytes+overlap.bytes;
 require(manifest.payloadBytes===bytes&&/^[0-9a-f]{64}$/.test(manifest.payloadSHA256),'combined identity differs');
 return {format:'bc7_rgba_overlap',width:base.width,height:base.height,sourceSHA256:source.sha256,payloadSHA256:manifest.payloadSHA256,bytes};
}
export async function validateScenePhotograph(manifest,payloads,source){
 const descriptor=describeScenePhotograph(manifest,source);require(descriptor.format==='bc7_rgba_overlap','not a hybrid scene payload');
 const prepared=await validateHybridTexture(manifest.texture,payloads?.prefix,payloads?.tail,source),overlap=await validateHybridOverlap(prepared,manifest.overlap,payloads?.overlap);
 const combined=new Uint8Array(descriptor.bytes);let offset=0;for(const data of [payloads.prefix,payloads.tail,payloads.overlap]){combined.set(new Uint8Array(data),offset);offset+=data.byteLength;}
 require(offset===descriptor.bytes&&await sha256(combined)===descriptor.payloadSHA256,'combined content differs');return {descriptor,prepared,overlap};
}
export const hybridPhotographIdentity=texture=>identities.get(texture)??null;
export async function loadScenePhotograph(options){
 const {supported,source,loadManifest,loadPayload,hybridContext,stillWanted=()=>true}=options;
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Hybrid scene photograph no longer wanted');};
 wanted();if(!supported)return loadPreparedPhotograph(options);
 let manifest;
 try{manifest=await loadManifest();wanted();}
 catch(error){if(error instanceof PreparedTextureCancelled)throw error;return loadPreparedPhotograph({...options,loadManifest:async()=>{throw error;}});}
 if(manifest?.schema!=='xnby.prepared_hybrid_scene.v1')return loadPreparedPhotograph({...options,loadManifest:async()=>manifest});
 let pair;
 try{
  require(hybridContext,'hybrid context unavailable');describeScenePhotograph(manifest,source);const payloads=await loadPayload(manifest);wanted();const checked=await validateScenePhotograph(manifest,payloads,source);wanted();
  pair=await hybridContext.load(checked.prepared,{overlap:checked.overlap,stillWanted});wanted();require(pair.bytes===checked.descriptor.bytes,'uploaded bytes differ');
  const identity=Object.freeze(checked.descriptor);identities.set(pair.texture,identity);pair.texture.addEventListener('dispose',()=>identities.delete(pair.texture));
  return {texture:pair.texture,format:identity.format,bytes:identity.bytes,payloadSHA256:identity.payloadSHA256,dispose:()=>pair.dispose()};
 }catch(error){pair?.dispose();if(error instanceof PreparedTextureContextError||error instanceof PreparedTextureCancelled)throw error;wanted();return loadPreparedPhotograph({...options,supported:false,onFallback:(_reason)=>options.onFallback?.('hybrid_unavailable_or_invalid',error)});}
}
