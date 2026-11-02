import {memoryImageInfo,CROP_SOURCE_FORMAT,SOURCE_CENTROID_POLICY} from './source_page_format.js';
import {validateSourceGltfGeometry} from './source_geometry_layout.js';
const verified=new WeakSet(),require=(ok,message)=>{if(!ok)throw Error(message);};
const digest=async raw=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(n=>n.toString(16).padStart(2,'0')).join('');
function freeze(value){if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value);}return value;}

// Experimental representation plan, never a GPU budget grant. Original PNG,
// geometry, indices and source dimensions retain their SHA-pinned identity.
export async function planClientSourceCrop({part,jsonBytes,binary}){
 const info=memoryImageInfo(part);
 require(part.source_format===CROP_SOURCE_FORMAT,'Client crop requires the explicit original-image contract');
 for(const [name,raw,limit] of [['geometry.gltf',jsonBytes,1048576],['geometry.bin',binary,32*1048576]]){
  const file=part.files.find(f=>f.name===name);
  require(raw instanceof ArrayBuffer&&raw.byteLength>0&&raw.byteLength<=limit&&raw.byteLength===file.bytes&&await digest(raw)===file.sha256,'Client crop geometry SHA differs');
 }
 const gltf=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(jsonBytes));validateSourceGltfGeometry(gltf,part,binary);
 const image=part.source_image,sampler=info.sampler,ow=image.original_width,oh=image.original_height,old=image.source_rect;
 const finish=(rect,reason)=>{
  const [x,y,width,height]=rect,changed=rect.some((v,i)=>v!==old[i]);
  const plan=freeze({schema:'xnby.client_source_crop.v1',changed,reason,
   sourcePNG_SHA256:info.sha256,geometryGLTF_SHA256:part.files.find(f=>f.name==='geometry.gltf').sha256,
   geometryBIN_SHA256:part.files.find(f=>f.name==='geometry.bin').sha256,
   originalDimensions:[ow,oh],inputDimensions:[info.width,info.height],inputRect:[...old],sourceRect:[...rect],
   bitmapRect:[x-old[0],y-old[1],width,height],transform:[ow/width,oh/height,x===0?0:-x/width,y===0?0:-y/height],
   sampler:{...sampler},savedTextureBytes:(old[2]*old[3]-width*height)*4,
   scope:'verified_representation_only_not_GPU_admission'});
  verified.add(plan);return plan;
 };
 if(info.generateMipmaps)return finish(old,'mipmapped_source');
 if(sampler.minFilter!==9729||sampler.magFilter!==9729)return finish(old,'nonlinear_sampler_retained');
 const primitive=gltf.meshes[0].primitives[0];
 const values=(accessor,kind,components)=>{const a=gltf.accessors[accessor],v=gltf.bufferViews[a.bufferView];return new kind(binary,v.byteOffset??0,a.count*components);};
 const uv=values(primitive.attributes.TEXCOORD_0,Float32Array,2),indices=values(primitive.indices,Uint32Array,1);
 const low=[Infinity,Infinity],high=[-Infinity,-Infinity];
 // Repeated references do not change extrema. Do not allocate a vertex set or
 // simplify triangles/UVs, including unreferenced outlier vertices.
 for(const index of indices)for(let axis=0;axis<2;axis++){
  const value=uv[index*2+axis]*(axis===0?ow:oh)-.5;
  low[axis]=Math.min(low[axis],value);high[axis]=Math.max(high[axis],value);
 }
 for(let axis=0;axis<2;axis++){
  const dim=axis===0?ow:oh,wrap=axis===0?sampler.wrapS:sampler.wrapT;
  if(wrap===33071){low[axis]=Math.max(-.5,Math.min(dim-.5,low[axis]));high[axis]=Math.max(-.5,Math.min(dim-.5,high[axis]));}
  else if(low[axis]<1||high[axis]>dim-2)return finish(old,'periodic_seam_or_border');
 }
 const x=Math.max(old[0],Math.floor(low[0])-1),y=Math.max(old[1],Math.floor(low[1])-1),
       right=Math.min(old[0]+old[2],Math.ceil(high[0])+2),top=Math.min(old[1]+old[3],Math.ceil(high[1])+2);
 require(right>x&&top>y,'Client source footprint is outside delivered image');
 return finish([x,y,right-x,top-y],null);
}
export function verifiedClientSourceCrop(plan){return verified.has(plan);}
export function canClientSourceCrop(part){
 if(part.source_format!==CROP_SOURCE_FORMAT)return false;
 const info=memoryImageInfo(part);return !info.generateMipmaps&&info.sampler.minFilter===9729&&info.sampler.magFilter===9729;
}
export function validateClientSourceCropForPart(plan,part){
 require(verified.has(plan),'Unverified client crop plan');
 const info=memoryImageInfo(part),image=part.source_image;
 require(part.source_format===CROP_SOURCE_FORMAT&&plan.sourcePNG_SHA256===info.sha256&&
  plan.geometryGLTF_SHA256===part.files.find(f=>f.name==='geometry.gltf').sha256&&
  plan.geometryBIN_SHA256===part.files.find(f=>f.name==='geometry.bin').sha256&&
  plan.originalDimensions[0]===image.original_width&&plan.originalDimensions[1]===image.original_height&&
  plan.inputDimensions[0]===info.width&&plan.inputDimensions[1]===info.height&&
  plan.inputRect.every((n,i)=>n===image.source_rect[i])&&
  Object.keys(info.sampler).every(k=>plan.sampler[k]===info.sampler[k]),'Client crop source identity differs');
 return plan;
}

// A vertex-UV footprint does not cover legacy MSAA interpolation outside a
// thin triangle. Keep the full image until a separately identified centroid
// runtime policy is integrated and qualified; never turn off antialiasing here.
export function clientCropRasterGate({requested=false,bitmapAvailable=false,samples=null,samplingProfile=null}={}){
 require(typeof requested==='boolean'&&typeof bitmapAvailable==='boolean','Invalid client crop raster opt-in');
 require(samplingProfile===null||samplingProfile===SOURCE_CENTROID_POLICY,'Unknown source sampling profile');
 const valid=Number.isInteger(samples)&&samples>=0&&samples<=64,rasterSamples=valid?samples:null;
 const blockedReason=!requested?null:!bitmapAvailable?'bitmap_crop_unavailable':!valid?'raster_samples_unknown':samples>0&&samplingProfile!==SOURCE_CENTROID_POLICY?'multisample_pixel_center_footprint_unproven':null;
 return Object.freeze({requested,enabled:requested&&blockedReason===null,bitmapAvailable,rasterSamples,samplingProfile,blockedReason,scope:'legacy_pixel_center_interpolation; no_centroid_runtime_policy_implied'});
}
