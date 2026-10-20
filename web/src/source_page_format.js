// Explicit opt-in for original source images; legacy atlas descriptors keep their own contract.
export const MEMORY_SOURCE_FORMAT='osgb_memory_png_v1';
export const CROP_SOURCE_FORMAT='osgb_memory_png_crop_v2';
export const isMemoryFormat=format=>[MEMORY_SOURCE_FORMAT,CROP_SOURCE_FORMAT].includes(format);
export const MEMORY_GEOMETRY_LAYOUT='three_float32_pu_uint32_v1';
export const MEMORY_ROOT_SCHEMA='zhumadian.osgb_source_frontier.v2';
export const MEMORY_FAMILY_SCHEMA='zhumadian.osgb_source_family.v2';
export const INDEXED_FAMILY_SCHEMA='zhumadian.osgb_source_descendants.v3';
export const isIndexedMemoryFamily=marker=>marker?.schema===INDEXED_FAMILY_SCHEMA;
const require=(ok,message)=>{if(!ok)throw Error(message);};
export function isMemorySourcePart(part){
 if(!Object.hasOwn(part,'source_format')){require(!Object.hasOwn(part,'geometry_layout'),'Unversioned source geometry layout');return false;}
 require(isMemoryFormat(part.source_format)&&part.geometry_layout===MEMORY_GEOMETRY_LAYOUT,'Unknown original source page format');return true;
}
export function sourceImageMipBytes(width,height){
 require([width,height].every(n=>Number.isSafeInteger(n)&&n>0&&n<=8192),'Invalid original source image size');let bytes=0;
 for(;;){bytes+=width*height*4;if(width===1&&height===1)return bytes;width=Math.max(1,Math.floor(width/2));height=Math.max(1,Math.floor(height/2));}
}
export function memoryImageInfo(part){
 require(isMemorySourcePart(part)&&!['atlas_size','atlas_extent','atlas_layout_policy'].some(k=>Object.hasOwn(part,k)),'Mixed original-image and atlas formats');
 const crop=part.source_format===CROP_SOURCE_FORMAT,image=part.source_image;const keys=crop?'file,height,mip_levels,opaque,original_height,original_width,row_order,sampler,source_origin,source_rect,uv_transform,width':'file,height,opaque,row_order,sampler,source_origin,width';require(image&&Object.keys(image).sort().join(',')===keys&&image.file==='texture.png'&&image.opaque===true&&image.row_order==='source_storage'&&['bottom_left','top_left'].includes(image.source_origin),'Invalid original image descriptor');
 const fullBytes=sourceImageMipBytes(image.width,image.height),s=image.sampler;let bytes=fullBytes,mipLevels=1+Math.floor(Math.log2(Math.max(image.width,image.height))),transform=[1,1,0,0],cropContract;
 require(s&&Object.keys(s).sort().join(',')==='magFilter,minFilter,wrapS,wrapT'&&[s.wrapS,s.wrapT].every(n=>[10497,33071,33648].includes(n))&&[9728,9729,9984,9985,9986,9987].includes(s.minFilter)&&[9728,9729].includes(s.magFilter),'Invalid original image sampler');
 if(crop){
  const ow=image.original_width,oh=image.original_height,r=image.source_rect,t=image.uv_transform;
  require([ow,oh].every(n=>Number.isSafeInteger(n)&&n>0&&n<=8192)&&Array.isArray(r)&&r.length===4&&r.every(Number.isSafeInteger)&&r[0]>=0&&r[1]>=0&&r[2]===image.width&&r[3]===image.height&&r[0]+r[2]<=ow&&r[1]+r[3]<=oh,'Invalid original source crop bounds');
  transform=[ow/r[2],oh/r[3],-r[0]/r[2],-r[1]/r[3]];
  require(Array.isArray(t)&&t.length===4&&t.every((n,i)=>Number.isFinite(n)&&n===transform[i]),'Original source UV transform mismatch');
  const noMips=[9728,9729].includes(s.minFilter);if(noMips)mipLevels=1;else require(r[0]===0&&r[1]===0&&r[2]===ow&&r[3]===oh,'Mipmapped crop gutters are unsupported');
  require(image.mip_levels===mipLevels,'Original source mip allocation mismatch');bytes=mipLevels===1?image.width*image.height*4:fullBytes;
  cropContract=JSON.stringify([part.source_format,ow,oh,r,t,mipLevels,[s.wrapS,s.wrapT,s.minFilter,s.magFilter],image.source_origin]);
 }
 require(Array.isArray(part.files)&&part.files.length===3&&new Set(part.files.map(f=>f.name)).size===3&&['geometry.gltf','geometry.bin','texture.png'].every(name=>part.files.some(f=>f.name===name)),'Invalid original page files');
 const file=part.files.find(f=>f.name==='texture.png');require(Number.isSafeInteger(file.bytes)&&file.bytes>0&&file.bytes<=32*1048576&&/^[0-9a-f]{64}$/.test(file.sha256),'Invalid original PNG identity');
 return {width:image.width,height:image.height,sha256:file.sha256,bytes,sampler:s,mipLevels,transform,generateMipmaps:crop?mipLevels>1:true,...(crop?{cropContract}:{})};
}
export function isMemoryFamily(marker){return (marker?.schema===MEMORY_FAMILY_SCHEMA||isIndexedMemoryFamily(marker))&&isMemoryFormat(marker.source_format);}
