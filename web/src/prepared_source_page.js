import {SOURCE_CENTROID_POLICY,sourceRasterContract,validateSourceSamplingProfile,applySourceCentroidSampling,validateSourceRasterMaterial,validateSourceDrawOrder} from './source_centroid_sampling.js';
import {decodeOriginalImage,ownOriginalImageTexture,OriginalImageCropUnavailable} from './original_image.js';
import {canClientSourceCrop,validateClientSourceCropForPart} from './source_client_crop.js';
import {isMemorySourcePart,memoryImageInfo,sourceImageMipBytes} from './source_page_format.js';
// A native source page reserves geometry and the negotiated photograph together.
// Source manifests remain immutable; runtime choice is tracked separately.
import {LoadingManager,TextureLoader,SRGBColorSpace,ClampToEdgeWrapping,LinearMipmapLinearFilter,LinearFilter,RepeatWrapping,MirroredRepeatWrapping,NearestFilter,NearestMipmapNearestFilter,NearestMipmapLinearFilter,LinearMipmapNearestFilter} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {loadPreparedPhotograph,uploadPreparedBc7,sha256,rgbaMipBytes,PreparedTextureCancelled,describePreparedBc7} from './prepared_bc7.js';
import {describeScenePhotograph,loadScenePhotograph,hybridPhotographIdentity} from './prepared_hybrid_scene.js';
import {hybridSceneTextureIdentity} from './prepared_hybrid_material.js';
import {stageSourceParts,ensureSourceWanted} from './lod_transaction.js';
import {WEB_SOURCE_GEOMETRY_LAYOUT,webSourceGeometryLayout,webSourceGeometryBytes,validateSourceGltfGeometry,validateLoadedSourceGeometry} from './source_geometry_layout.js';
const identities=new WeakMap(),plans=new WeakMap(),identityCrops=new WeakMap();
export class SourcePagePlanChanged extends Error{
 constructor(directory,reason){super('Source page requires budget replanning: '+directory+' / '+reason);this.name='SourcePagePlanChanged';this.directory=directory;this.reason=reason;this.retryFormat='rgba8';}
}
function pageIdentity(source,geometryBytes,format,textureBytes,payloadSHA256=null,geometryLayout=WEB_SOURCE_GEOMETRY_LAYOUT,crop=null,rasterSamplingContract=null,drawOrder=null){const identity=Object.freeze({schema:'xnby.source_page.texture.v1',format,sourceSHA256:source.sha256,width:source.width,height:source.height,textureBytes,payloadSHA256,geometryLayout,geometryBytes,totalBytes:textureBytes+geometryBytes,...(source.cropContract?{samplingContract:source.cropContract}:{}),...(rasterSamplingContract?{rasterSamplingContract}:{}),...(drawOrder!==null?{drawOrder}:{}),...(crop?{clientCropContract:JSON.stringify(crop),textureWidth:crop.bitmapRect[2],textureHeight:crop.bitmapRect[3]}:{})});if(crop)identityCrops.set(identity,crop);return identity;}
function immutable(value){if(value&&typeof value==='object'){for(const child of Object.values(value))immutable(child);Object.freeze(value);}return value;}
function sameIdentity(a,b){return a&&b&&Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>a[k]===b[k]);}
// Default planning is descriptor-only. Explicit clientCrop may verify geometry;
// it never decodes images, reserves GPU memory or grants upload admission.
export async function planPreparedSourceBundle({marker,supported,loadManifest,forceRgbaParts=new Set(),stillWanted=()=>true,clientCrop=null,samplingProfile=null,drawOrder=null}){
 sourceRasterContract({},samplingProfile);require(samplingProfile?typeof drawOrder==='function':drawOrder===null,'Source sampling requires explicit draw order allocation');
 require(clientCrop===null||typeof clientCrop==='function','Invalid client crop planner');
 require(Array.isArray(marker.parts)&&marker.parts.length>0&&marker.parts.length<=64&&new Set(marker.parts.map(p=>p.directory)).size===marker.parts.length,'Invalid source bundle plan');
 require([...forceRgbaParts].every(name=>marker.parts.some(p=>p.directory===name)),'Unknown original-image fallback page');
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Source plan no longer wanted');};
 const choices=new Map(),parts=[],fallbacks=[],orders=new Set();let originalTotal=0;
 for(const part of marker.parts){
  wanted();const source=sourcePageSource(part),geometry=webSourceGeometryBytes(part);originalTotal+=part.source_gpu_payload_bytes??part.gpu_payload_bytes;
  let manifest=null,crop=null,format='rgba8',bytes=originalTextureBytes(part,source),payload=null,reason='unsupported';
  if(forceRgbaParts.has(part.directory))reason='explicit_budget_replan';
  else if(clientCrop&&canClientSourceCrop(part)){const selected=validateClientSourceCropForPart(await clientCrop(part),part);wanted();if(selected.changed){crop=selected;bytes=crop.bitmapRect[2]*crop.bitmapRect[3]*4;reason=null;}}
  else if(!isMemorySourcePart(part)&&(typeof supported==='function'?supported(part):supported)){
   try{manifest=structuredClone(await loadManifest(part));wanted();const info=describeScenePhotograph(manifest,source);format=info.format;bytes=info.bytes;payload=info.payloadSHA256;reason=null;}
   catch(error){if(error instanceof PreparedTextureCancelled)throw error;manifest=null;reason='prepared_descriptor_unavailable_or_invalid';}
  }
  wanted();const order=samplingProfile?drawOrder(part):null;require(samplingProfile?Number.isInteger(order)&&order>0&&order<=2147483647&&!orders.has(order):order===null,'Invalid source draw order');orders.add(order);const identity=pageIdentity(source,geometry,format,bytes,payload,webSourceGeometryLayout(part),crop,sourceRasterContract(part,samplingProfile),order);require(identity.totalBytes<=32*1048576,'Planned source page exceeds upload limit');
  choices.set(part.directory,{identity,crop,manifest:manifest&&immutable(manifest)});if(reason)fallbacks.push({directory:part.directory,reason});
  parts.push({...structuredClone(part),source_gpu_payload_bytes:part.source_gpu_payload_bytes??part.gpu_payload_bytes,gpu_payload_bytes:identity.totalBytes,runtime_texture:identity});
 }
 require(originalTotal===marker.gpu_payload_bytes,'Source bundle original cost mismatch');
 const plan=Object.freeze({marker:immutable({...structuredClone(marker),...(samplingProfile?{runtime_sampling_profile:samplingProfile}:{}),parts,gpu_payload_bytes:parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)}),fallbacks:immutable(fallbacks)});
 plans.set(plan,{source:JSON.stringify(marker),choices,samplingProfile});return plan;
}
// Descriptor validation still runs for unknown crop cost. Its complete-image
// byte count is an upper representation, never a crop admission or rejection.
export async function sourceMetadataBudgetCost(options){
 sourceRasterContract({},options.samplingProfile??null);const plan=await planPreparedSourceBundle({...options,samplingProfile:null,drawOrder:null});
 return options.clientCropEnabled===true&&options.marker.parts.some(canClientSourceCrop)?null:plan.marker.gpu_payload_bytes;
}
export function originalSourceBundle(marker){
 const parts=marker.parts.map(part=>{const next=structuredClone(part);next.gpu_payload_bytes=part.source_gpu_payload_bytes??part.gpu_payload_bytes;delete next.source_gpu_payload_bytes;delete next.runtime_texture;return next;});
 const original={...structuredClone(marker),parts,gpu_payload_bytes:parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)};delete original.runtime_sampling_profile;return original;
}
export function subsetPreparedSourcePlan(plan,directories){
 const internal=plans.get(plan);require(internal&&Array.isArray(directories)&&directories.length&&new Set(directories).size===directories.length&&directories.every(n=>internal.choices.has(n)),'Invalid prepared source plan subset');
 const original=JSON.parse(internal.source),selected=new Set(directories),parts=original.parts.filter(p=>selected.has(p.directory)),runtime=plan.marker.parts.filter(p=>selected.has(p.directory));
 const marker={...original,parts,gpu_payload_bytes:parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)};
 const subset=Object.freeze({marker:immutable({...structuredClone(plan.marker),parts:structuredClone(runtime),gpu_payload_bytes:runtime.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)}),fallbacks:immutable(plan.fallbacks.filter(f=>selected.has(f.directory)))});
 plans.set(subset,{source:JSON.stringify(marker),samplingProfile:internal.samplingProfile,choices:new Map([...internal.choices].filter(([name])=>selected.has(name)))});return {marker,plan:subset};
}
function disposeMaterials(mesh){for(const material of new Set(Array.isArray(mesh.material)?mesh.material:[mesh.material]))material?.dispose();}
const require=(ok,message)=>{if(!ok)throw Error(message);};
export function sourcePageTextureIdentity(texture){return identities.get(texture);}
export function sourcePageClientCrop(identity){return identityCrops.get(identity)??null;}
// Original source/native descriptor accounting remains unchanged.
export function sourcePageGeometryBytes(part){
 require(Number.isSafeInteger(part.vertices)&&part.vertices>0&&Number.isSafeInteger(part.indices)&&part.indices>0&&part.indices%3===0,'Invalid source page geometry');
 const bytes=part.vertices*64+part.indices*4;require(Number.isSafeInteger(bytes)&&bytes>0&&bytes<=32*1048576,'Invalid source page geometry cost');return bytes;
}
const originalTextureBytes=(part,source)=>isMemorySourcePart(part)?memoryImageInfo(part).bytes:rgbaMipBytes(source.width,source.height);
export function sourcePageSource(part){
 if(isMemorySourcePart(part)){const source=memoryImageInfo(part),geometry=sourcePageGeometryBytes(part);require((part.source_gpu_payload_bytes??part.gpu_payload_bytes)===geometry+source.bytes&&geometry+source.bytes<=32*1048576,'Original source page cost mismatch');return {width:source.width,height:source.height,sha256:source.sha256,...(source.cropContract?{cropContract:source.cropContract}:{})};}
 const extent=part.atlas_extent??[part.atlas_size,part.atlas_size];
 require(Array.isArray(extent)&&extent.length===2,'Invalid source page extent');
 const [width,height]=extent;const original=rgbaMipBytes(width,height),geometry=sourcePageGeometryBytes(part);
 require((part.source_gpu_payload_bytes??part.gpu_payload_bytes)===geometry+original&&geometry+original<=32*1048576,'Source page storage cost mismatch');
 const photos=part.files?.filter(file=>file.name==='atlas.jpg')??[];
 require(photos.length===1&&/^[0-9a-f]{64}$/.test(photos[0].sha256),'Source JPEG digest is missing');
 return {width,height,sha256:photos[0].sha256};
}
async function checkedFile(part,name,load){
 const files=part.files?.filter(file=>file.name===name)??[];require(files.length===1,'Source page file identity missing');
 const bytes=await load(name);require(bytes instanceof ArrayBuffer&&bytes.byteLength===files[0].bytes&&await sha256(bytes)===files[0].sha256,'Source page file content mismatch: '+name);return bytes;
}
function validPageSampler(part,sampler,texture,samplers){
 // Historical atlas pages omit the sampler entirely. They use the same fixed
 // edge-clamped mip sampling as loadPreparedPhotograph; do not treat a dangling
 // explicit index or a versioned original-image page as this legacy contract.
 if(!sampler)return !isMemorySourcePart(part)&&!Object.hasOwn(texture,'sampler')&&samplers===undefined;
const expected=isMemorySourcePart(part)?memoryImageInfo(part).sampler:{wrapS:33071,wrapT:33071,minFilter:9987,magFilter:9729};
 return Object.keys(expected).every(key=>sampler[key]===expected[key]);
}
const wrapConstants=new Map([[10497,RepeatWrapping],[33071,ClampToEdgeWrapping],[33648,MirroredRepeatWrapping]]),filterConstants=new Map([[9728,NearestFilter],[9729,LinearFilter],[9984,NearestMipmapNearestFilter],[9985,LinearMipmapNearestFilter],[9986,NearestMipmapLinearFilter],[9987,LinearMipmapLinearFilter]]);
function setOriginalSampling(texture,part,crop=null){const info=memoryImageInfo(part),s=info.sampler,t=crop?.transform??info.transform;texture.wrapS=wrapConstants.get(s.wrapS);texture.wrapT=wrapConstants.get(s.wrapT);texture.minFilter=filterConstants.get(s.minFilter);texture.magFilter=filterConstants.get(s.magFilter);texture.generateMipmaps=info.generateMipmaps;if(info.cropContract)texture.anisotropy=1;texture.repeat.set(t[0],t[1]);texture.offset.set(t[2],t[3]);texture.updateMatrix();}
async function loadMemoryPhotograph({THREE,part,renderer,loadFile,reserve,stillWanted,crop=null}){
 const source=memoryImageInfo(part),bytes=crop?crop.bitmapRect[2]*crop.bitmapRect[3]*4:source.bytes,width=crop?.bitmapRect[2]??source.width,height=crop?.bitmapRect[3]??source.height;require(width<=renderer.capabilities.maxTextureSize&&height<=renderer.capabilities.maxTextureSize,'Original source image exceeds this device capability');
 const owned=await reserve({format:'rgba8',bytes});let texture,decoded,released=false;const release=()=>{if(!released){released=true;owned.release();}};
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Original source page no longer wanted');};
 try{wanted();const original=await checkedFile(part,'texture.png',loadFile);wanted();const header=new DataView(original);require(original.byteLength>=33&&header.getUint32(0)===0x89504e47&&header.getUint32(4)===0x0d0a1a0a&&header.getUint32(8)===13&&header.getUint32(12)===0x49484452&&header.getUint32(16)===source.width&&header.getUint32(20)===source.height&&header.getUint8(24)===8&&header.getUint8(25)===6&&header.getUint8(26)===0&&header.getUint8(27)===0&&header.getUint8(28)===0,'Invalid original RGBA PNG header');
  decoded=await decodeOriginalImage({blob:new Blob([original],{type:'image/png'}),width:source.width,height:source.height,...(crop?{crop:crop.bitmapRect}:{}),stillWanted,loadImage:async blob=>{const url=URL.createObjectURL(blob);try{const loaded=await new TextureLoader().loadAsync(url);const image=loaded.image;loaded.dispose();return image;}finally{URL.revokeObjectURL(url);}}});wanted();texture=ownOriginalImageTexture(new THREE.Texture(decoded.image),decoded);texture.needsUpdate=true;texture.flipY=false;texture.colorSpace=SRGBColorSpace;setOriginalSampling(texture,part,crop);texture.addEventListener('dispose',release);
  return {texture,format:'rgba8',bytes,payloadSHA256:null,crop,dispose(){try{texture.dispose();}finally{release();}}};
 }catch(error){texture?.dispose();decoded?.dispose();release();if(crop&&error instanceof OriginalImageCropUnavailable)throw new SourcePagePlanChanged(part.directory,'client_crop_unavailable');throw error;}
}
export function validateSourcePageGltf(json,part){
 require(json.asset?.version==='2.0'&&json.buffers?.length===1&&json.buffers[0].uri==='geometry.bin'&&json.images?.length===1&&json.images[0].uri===(isMemorySourcePart(part)?'texture.png':'atlas.jpg'),'Unsupported source page GLTF files');
 require(json.textures?.length===1&&json.textures[0].source===0&&json.materials?.length===1&&json.meshes?.length===1&&json.meshes[0].primitives?.length===1,'Unsupported source page GLTF shape');
 require(!json.extensionsRequired?.length&&!json.extensionsUsed?.length,'Unexpected source page GLTF extensions');
 const primitive=json.meshes[0].primitives[0],sampler=json.samplers?.[json.textures[0].sampler];
 require(primitive.material===0&&primitive.mode===undefined&&Object.keys(primitive.attributes??{}).sort().join(',')===(isMemorySourcePart(part)?'POSITION,TEXCOORD_0':'NORMAL,POSITION,TEXCOORD_0'),'Unexpected source page primitive');
 require(json.materials[0].pbrMetallicRoughness?.baseColorTexture?.index===0&&!json.materials[0].pbrMetallicRoughness.baseColorTexture.texCoord&&validPageSampler(part,sampler,json.textures[0],json.samplers),'Unexpected source page sampler');
 require(json.accessors?.[primitive.indices]?.count===part.indices&&json.accessors?.[primitive.attributes.POSITION]?.count===part.vertices,'Source page GLTF geometry counts mismatch');
 validateSourceGltfGeometry(json,part);
}
// loadFile serves only the three SHA-pinned source files. Prepared loads are read-only.
// Caller must provide the same budget allocator used by all live/staged pages.
export async function loadPreparedSourcePage({THREE,renderer,part,supported,loadFile,loadManifest,loadPayload,reserve,stillWanted=()=>true,expectedIdentity,metrics=null,crop=null,hybridContext=null}){
 require(typeof reserve==='function','A shared page budget is required');
 if(crop)require(validateClientSourceCropForPart(crop,part).changed,'Client crop did not change the source page');
 const source=sourcePageSource(part),geometryBytes=webSourceGeometryBytes(part);let geometryLease,photo,model,objectURL;
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Source page is no longer wanted');};
 let released=false;const releaseGeometry=()=>{if(!released){released=true;geometryLease?.release();}};
 try{
  wanted();const jsonBytes=await checkedFile(part,'geometry.gltf',loadFile);wanted();const json=metrics?metrics.measure('source_json',()=>{const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(jsonBytes));validateSourcePageGltf(value,part);return value;}):JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(jsonBytes));if(!metrics)validateSourcePageGltf(json,part);
  const binary=await checkedFile(part,'geometry.bin',loadFile);wanted();require(json.buffers[0].byteLength===binary.byteLength,'GLTF buffer length mismatch');if(metrics)metrics.measure('source_geometry',()=>validateSourceGltfGeometry(json,part,binary));else validateSourceGltfGeometry(json,part,binary);
  geometryLease=await reserve({format:'geometry',bytes:geometryBytes});require(typeof geometryLease?.release==='function','Invalid geometry budget lease');wanted();
  photo=isMemorySourcePart(part)?await loadMemoryPhotograph({THREE,part,renderer,loadFile,reserve,stillWanted,crop}):await loadScenePhotograph({hybridContext,supported,source,loadManifest,loadPayload,reserve:async request=>{require(geometryBytes+request.bytes<=32*1048576,'Source page exceeds upload limit');return reserve(request);},stillWanted,
   upload:prepared=>uploadPreparedBc7(THREE,renderer,prepared),
   onFallback:reason=>{if(expectedIdentity&&expectedIdentity.format!=='rgba8')throw new SourcePagePlanChanged(part.directory,reason);},
   loadFallback:async()=>{
    const original=await checkedFile(part,'atlas.jpg',loadFile);wanted();const url=URL.createObjectURL(new Blob([original],{type:'image/jpeg'}));
    try{const texture=await new TextureLoader().loadAsync(url);if(!stillWanted()){texture.dispose();wanted();}texture.flipY=false;texture.colorSpace=SRGBColorSpace;texture.wrapS=texture.wrapT=ClampToEdgeWrapping;texture.minFilter=LinearMipmapLinearFilter;texture.magFilter=LinearFilter;return texture;}
    finally{URL.revokeObjectURL(url);}
   }});
  wanted();objectURL=URL.createObjectURL(new Blob([binary],{type:'application/octet-stream'}));
  const manager=new LoadingManager();manager.setURLModifier(url=>{require(url==='geometry.bin','Unexpected source page dependency');return objectURL;});
  const loader=new GLTFLoader(manager);loader.register(parser=>({name:'XNBY_prepared_source_photograph',loadTexture(index){require(index===0,'Unexpected source texture index');parser.associations.set(photo.texture,{textures:index});return Promise.resolve(photo.texture);}}));
  model=await (metrics?metrics.measureAsync('source_model_wait',()=>loader.parseAsync(json,'')):loader.parseAsync(json,''));wanted();
  const meshes=[];model.scene.traverse(node=>{if(node.isMesh)meshes.push(node);});require(meshes.length===1,'Unexpected source page mesh count');
  const mesh=meshes[0];require(mesh.geometry.index.count===part.indices&&mesh.geometry.attributes.position.count===part.vertices&&mesh.material.map===photo.texture,'Loaded source page mismatch');validateLoadedSourceGeometry(mesh.geometry,part);
  mesh.geometry.addEventListener('dispose',releaseGeometry);
  const identity=pageIdentity(source,geometryBytes,photo.format,photo.bytes,photo.payloadSHA256,webSourceGeometryLayout(part),photo.crop??null,expectedIdentity?.rasterSamplingContract??null,expectedIdentity?.drawOrder??null);
  if(expectedIdentity&&!sameIdentity(identity,expectedIdentity))throw new SourcePagePlanChanged(part.directory,'loaded_identity_changed');
  identities.set(photo.texture,identity);
  let disposed=false;
  return {model,mesh,identity,dispose(){if(disposed)return;disposed=true;try{mesh.geometry.dispose();}finally{try{photo.dispose();}finally{try{disposeMaterials(mesh);}finally{model.scene.removeFromParent();releaseGeometry();}}}}};
 }catch(error){try{if(model)model.scene.traverse(node=>{if(node.isMesh){node.geometry.dispose();disposeMaterials(node);}});photo?.dispose();}finally{releaseGeometry();}throw error;}
 finally{if(objectURL)URL.revokeObjectURL(objectURL);}
}

export function runtimeSourceBundle(marker,meshes,{samplingProfile=null}={}){
 require(marker.parts?.length&&meshes.size===marker.parts.length,'Incomplete runtime source bundle');
 const parts=marker.parts.map(part=>{const mesh=meshes.get(part.directory),material=Array.isArray(mesh?.material)?mesh.material[0]:mesh?.material,identity=sourcePageTextureIdentity(material?.map);require(identity&&identity.sourceSHA256===sourcePageSource(part).sha256,'Runtime source page identity missing');const runtimePart={...part,source_gpu_payload_bytes:part.source_gpu_payload_bytes??part.gpu_payload_bytes,gpu_payload_bytes:identity.totalBytes,runtime_texture:identity};validateSourceRasterMaterial(runtimePart,material);validateSourceDrawOrder(runtimePart,mesh);return runtimePart;});
 const runtime={...marker,...(samplingProfile?{runtime_sampling_profile:samplingProfile}:{}),parts,gpu_payload_bytes:parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)};validateSourceSamplingProfile(runtime);return runtime;
}
export function validateRuntimeSourceTexture(part,texture){
 const identity=sourcePageTextureIdentity(texture),claimed=part.runtime_texture;require(identity&&claimed&&Object.keys(identity).length===Object.keys(claimed).length&&Object.keys(identity).every(k=>identity[k]===claimed[k]),'Runtime texture identity mismatch');
 const source=sourcePageSource(part),crop=identityCrops.get(identity);if(crop)validateClientSourceCropForPart(crop,part);require(Boolean(identity.clientCropContract)===Boolean(crop)&&(!crop||identity.clientCropContract===JSON.stringify(crop)&&identity.textureWidth===crop.bitmapRect[2]&&identity.textureHeight===crop.bitmapRect[3]),'Runtime client crop identity mismatch');require(identity.sourceSHA256===source.sha256&&identity.width===source.width&&identity.height===source.height&&identity.geometryLayout===webSourceGeometryLayout(part)&&identity.geometryBytes===webSourceGeometryBytes(part)&&part.gpu_payload_bytes===identity.totalBytes,'Runtime source page cost mismatch');
 if(identity.format==='bc7')require(texture.isCompressedTexture===true&&/^[0-9a-f]{64}$/.test(identity.payloadSHA256)&&texture.mipmaps?.reduce((sum,m)=>sum+m.data.byteLength,0)===identity.textureBytes,'Runtime compressed mip identity mismatch');
 else if(identity.format==='bc7_rgba_overlap'){const proof=hybridPhotographIdentity(texture),pair=hybridSceneTextureIdentity(texture);require(proof&&pair&&proof.payloadSHA256===identity.payloadSHA256&&proof.sourceSHA256===source.sha256&&proof.bytes===identity.textureBytes&&pair.bytes===identity.textureBytes,'Runtime hybrid texture identity mismatch');}
 else require(identity.format==='rgba8'&&!texture.isCompressedTexture&&identity.payloadSHA256===null&&identity.textureBytes===(crop?crop.bitmapRect[2]*crop.bitmapRect[3]*4:originalTextureBytes(part,source)),'Runtime original texture identity mismatch');
 if(isMemorySourcePart(part)){const info=memoryImageInfo(part),sampler=info.sampler,t=crop?.transform??info.transform;require(identity.format==='rgba8'&&texture.flipY===false&&texture.wrapS===wrapConstants.get(sampler.wrapS)&&texture.wrapT===wrapConstants.get(sampler.wrapT)&&texture.minFilter===filterConstants.get(sampler.minFilter)&&texture.magFilter===filterConstants.get(sampler.magFilter),'Runtime original source sampler mismatch');require(texture.generateMipmaps===info.generateMipmaps&&texture.colorSpace===SRGBColorSpace&&texture.rotation===0&&texture.center.x===0&&texture.center.y===0&&texture.matrixAutoUpdate===true&&texture.repeat.x===t[0]&&texture.repeat.y===t[1]&&texture.offset.x===t[2]&&texture.offset.y===t[3]&&identity.samplingContract===info.cropContract&&(!info.cropContract||texture.anisotropy===1),'Runtime original source transform or mip mismatch');texture.updateMatrix();}
 return identity.textureBytes;
}

// A staged bundle owns every page until the caller atomically commits the whole cut.
// Failure/cancellation cannot attach a partial family to the live scene.
export async function stagePreparedSourceBundle({THREE,renderer,marker,plan,supported,loadFile,loadManifest,loadPayload,reserve,stillWanted=()=>true,prepare=()=>{},upload,onReady,yieldFrame=()=>Promise.resolve(),metrics=null,loadConcurrency=1,hybridContext=null}){
 require(loadConcurrency===1||loadConcurrency===2,'Source preparation concurrency must be 1 or 2');
 // Prepared compressed uploads may execute renderer work during load. Only
 // original memory PNG pages are CPU-only until the ordered upload callback.
 const preparationSlots=marker.parts.every(isMemorySourcePart)?loadConcurrency:1;
 const planned=plan&&plans.get(plan);if(plan)require(planned&&planned.source===JSON.stringify(marker),'Source bundle plan identity mismatch');
 const group=new THREE.Group(),meshes=new Map(),pages=[];let disposed=false;
 const dispose=()=>{if(disposed)return;disposed=true;try{for(const page of pages)page.dispose();}finally{group.removeFromParent();group.clear();}};
 try{
  await stageSourceParts({marker,group,stillWanted,loadConcurrency:preparationSlots,prepare:model=>{prepare(model);const page=pages.find(p=>p.model===model);require(page,'Unknown prepared source material');const part=marker.parts.find(p=>meshes.get(p.directory)===page.mesh),material=Array.isArray(page.mesh.material)?page.mesh.material[0]:page.mesh.material;require(part,'Unknown prepared source part');if(page.identity.drawOrder!==undefined)page.mesh.renderOrder=page.identity.drawOrder;if(page.identity.rasterSamplingContract)applySourceCentroidSampling(material,{enabled:true,part});validateSourceRasterMaterial({...part,runtime_texture:page.identity},material);validateSourceDrawOrder({...part,runtime_texture:page.identity},page.mesh);},upload:async(model,index)=>{const part=marker.parts[index],page=pages.find(p=>p.model===model);require(page,'Unknown prepared upload');if(metrics)metrics.measure('source_loaded_geometry',()=>validateLoadedSourceGeometry(page.mesh.geometry,part));else validateLoadedSourceGeometry(page.mesh.geometry,part);await upload?.(model,index);},onReady,yieldFrame,urlForPart:part=>part.directory,
   downloads:{load:async (directory,batchWanted=stillWanted)=>{
    const part=marker.parts.find(p=>p.directory===directory);require(part,'Unknown staged source page');
    const choice=planned?.choices.get(directory);
    const load=()=>loadPreparedSourcePage({THREE,renderer,part,metrics,hybridContext,supported:choice?choice.identity.format!=='rgba8':typeof supported==='function'?supported(part):supported,expectedIdentity:choice?.identity,crop:choice?.crop??null,loadFile:name=>loadFile(part,name),loadManifest:()=>choice?choice.manifest:loadManifest(part),loadPayload:()=>loadPayload(part),reserve,stillWanted:()=>stillWanted()&&batchWanted()});const page=await (metrics?metrics.measureAsync('source_load_wait',load):load());
    pages.push(page);meshes.set(directory,page.mesh);return page.model;
   }},
   dispose:scene=>{const page=pages.find(p=>p.model.scene===scene);page?.dispose();}});
  const runtime=runtimeSourceBundle(marker,meshes,{samplingProfile:planned?.samplingProfile??null});
  if(plan)require(runtime.gpu_payload_bytes===plan.marker.gpu_payload_bytes&&runtime.parts.every((p,i)=>sameIdentity(p.runtime_texture,plan.marker.parts[i].runtime_texture)),'Loaded bundle differs from admitted plan');
  return {marker:runtime,meshes,group,pages,dispose};
 }catch(error){dispose();throw error;}
}

// Negotiate again after a representation fails. The previous staging operation
// has drained/disposed all pages before the ticket is cancelled or a larger
// full-image representation can ask for fresh admission.
export async function stageReplannedSourceBundle(options){
 const {marker,admit,cancelAttempt,onReplan,stillWanted=()=>true}=options;
 require(typeof admit==='function','Source staging requires representation admission');
 const forceRgbaParts=new Set();
 for(let attempt=0;attempt<=marker.parts.length;attempt++){
  ensureSourceWanted(stillWanted);
  const plan=await planPreparedSourceBundle({...options,forceRgbaParts,stillWanted});
  if(!await admit(plan.marker))return null;
  try{return await stagePreparedSourceBundle({...options,plan,stillWanted});}
  catch(error){
   cancelAttempt?.();
   if(!(error instanceof SourcePagePlanChanged)||forceRgbaParts.has(error.directory))throw error;
   const part=marker.parts.find(part=>part.directory===error.directory);require(part,'Unknown source page replan');
   forceRgbaParts.add(error.directory);onReplan?.(error,part);
  }
 }
 throw Error('Source representation replanning exhausted');
}
