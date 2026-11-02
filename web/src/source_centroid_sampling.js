import {ShaderChunk,SRGBColorSpace,LinearFilter} from 'three';
import {canClientSourceCrop} from './source_client_crop.js';
import {memoryImageInfo,SOURCE_CENTROID_POLICY} from './source_page_format.js';
export {SOURCE_CENTROID_POLICY} from './source_page_format.js';

const policies=new WeakMap(),bindings=new WeakMap(),require=(v,m)=>{if(!v)throw Error(m);};
// This is a different raster sampling policy, not byte-equivalence to legacy
// pixel-center interpolation. Both full and crop references must opt in.
export function patchSourceCentroidShader(shader,chunks=ShaderChunk){
 const result={};
 for(const [field,chunk] of [['vertexShader','uv_pars_vertex'],['fragmentShader','uv_pars_fragment']]){
  const include='#include <'+chunk+'>',text=chunks?.[chunk],varying='varying vec2 vMapUv;';
  require(typeof shader?.[field]==='string'&&shader[field].split(include).length===2&&typeof text==='string'&&text.split(varying).length===2,'Source centroid shader contract differs');
  result[field]=shader[field].replace(include,text.replace(varying,'centroid '+varying));
 }
 return result;
}
export function sourceCentroidSampling(material){return policies.get(material)??null;}
// Experimental material-only hook. It does not enable cropping, change a source
// descriptor, waive runtime admission, or rewrite application/default materials.
export function applySourceCentroidSampling(material,{enabled=false,part,chunks=ShaderChunk}={}){
 require(typeof enabled==='boolean','Invalid source centroid opt-in');if(!enabled)return null;
 require(material?.isMeshBasicMaterial===true&&material.map?.isTexture===true&&!material.map.isCompressedTexture&&canClientSourceCrop(part),'Source centroid requires an eligible original-image basic material');
 const map=material.map,info=memoryImageInfo(part);
 require(map.colorSpace===SRGBColorSpace&&map.minFilter===LinearFilter&&map.magFilter===LinearFilter&&map.generateMipmaps===false&&map.anisotropy===1&&map.flipY===false,'Source centroid sampling parameters differ');
 const policy=Object.freeze({schema:'xnby.source_map_sampling.v1',interpolation:SOURCE_CENTROID_POLICY,sourceSHA256:info.sha256,originalSamplingContract:info.cropContract});
 const existing=policies.get(material);if(existing){require(JSON.stringify(existing)===JSON.stringify(policy),'Source centroid material identity differs');validateSourceRasterMaterial({ ...part,runtime_texture:{rasterSamplingContract:SOURCE_CENTROID_POLICY}},material);return existing;}
 // Validate both chunk contracts before modifying hooks or the program key.
 patchSourceCentroidShader({vertexShader:'#include <uv_pars_vertex>',fragmentShader:'#include <uv_pars_fragment>'},chunks);
 require(typeof material.onBeforeCompile==='function'&&typeof material.customProgramCacheKey==='function','Source centroid material hooks unavailable');
 const previous=material.onBeforeCompile,key=String(material.customProgramCacheKey());
 material.onBeforeCompile=function(shader,renderer){previous.call(this,shader,renderer);const patched=patchSourceCentroidShader(shader,chunks);shader.vertexShader=patched.vertexShader;shader.fragmentShader=patched.fragmentShader;};
 material.customProgramCacheKey=()=>key+'|'+SOURCE_CENTROID_POLICY;material.needsUpdate=true;policies.set(material,policy);bindings.set(material,{map,hook:material.onBeforeCompile,key:material.customProgramCacheKey,programKey:material.customProgramCacheKey()});return policy;
}

export function sourceRasterContract(part,samplingProfile=null){
 require(samplingProfile===null||samplingProfile===SOURCE_CENTROID_POLICY,'Unknown source sampling profile');
 return samplingProfile&&canClientSourceCrop(part)?SOURCE_CENTROID_POLICY:null;
}
// One scene owns the monotonic sequence. Each attempt keeps at most 64 page
// assignments; retries reuse them and restorations use the saved identities.
export class SourceDrawOrder {
 #next=1;
 bundle(){const pages=new Map();return part=>{if(!pages.has(part.directory)){require(pages.size<64&&this.#next<=2147483647,'Source draw order exhausted');pages.set(part.directory,this.#next++);}return pages.get(part.directory);};}
}
export function validateSourceDrawOrder(part,mesh){
 const order=part.runtime_texture?.drawOrder;
 if(order===undefined)return;
 require(Number.isInteger(order)&&order>0&&order<=2147483647&&mesh.renderOrder===order,'Source draw order identity differs');
}
export function validateSourceSamplingProfile(marker){
 const profile=marker.runtime_sampling_profile??null;require(profile===null||profile===SOURCE_CENTROID_POLICY,'Unknown source sampling profile');
 const orders=new Set();for(const part of marker.parts){const expected=sourceRasterContract(part,profile);require((part.runtime_texture?.rasterSamplingContract??null)===expected,'Source bundle raster sampling identity mismatch');const order=part.runtime_texture?.drawOrder;require(profile?Number.isInteger(order)&&order>0&&order<=2147483647&&!orders.has(order):order===undefined,'Source bundle draw order identity mismatch');orders.add(order);}
 return profile;
}
export function validateSourceRasterMaterial(part,material){
 const expected=part.runtime_texture?.rasterSamplingContract??null,policy=policies.get(material),binding=bindings.get(material);
 if(expected===null){require(!policy,'Unexpected centroid source material');return null;}
 require(expected===SOURCE_CENTROID_POLICY&&policy&&binding,'Source centroid material proof missing');
 const info=memoryImageInfo(part);require(policy.sourceSHA256===info.sha256&&policy.originalSamplingContract===info.cropContract&&binding.map===material.map&&binding.hook===material.onBeforeCompile&&binding.key===material.customProgramCacheKey&&binding.programKey===material.customProgramCacheKey(),'Source centroid material identity differs');
 return policy;
}
