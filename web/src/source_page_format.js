// Explicit opt-in for original source images; legacy atlas descriptors keep their own contract.
export const MEMORY_SOURCE_FORMAT='osgb_memory_png_v1';
export const MEMORY_GEOMETRY_LAYOUT='three_float32_pu_uint32_v1';
export const MEMORY_ROOT_SCHEMA='zhumadian.osgb_source_frontier.v2';
export const MEMORY_FAMILY_SCHEMA='zhumadian.osgb_source_family.v2';
const require=(ok,message)=>{if(!ok)throw Error(message);};
export function isMemorySourcePart(part){
 if(!Object.hasOwn(part,'source_format')){require(!Object.hasOwn(part,'geometry_layout'),'Unversioned source geometry layout');return false;}
 require(part.source_format===MEMORY_SOURCE_FORMAT&&part.geometry_layout===MEMORY_GEOMETRY_LAYOUT,'Unknown original source page format');return true;
}
export function sourceImageMipBytes(width,height){
 require([width,height].every(n=>Number.isSafeInteger(n)&&n>0&&n<=8192),'Invalid original source image size');let bytes=0;
 for(;;){bytes+=width*height*4;if(width===1&&height===1)return bytes;width=Math.max(1,Math.floor(width/2));height=Math.max(1,Math.floor(height/2));}
}
export function memoryImageInfo(part){
 require(isMemorySourcePart(part)&&!['atlas_size','atlas_extent','atlas_layout_policy'].some(k=>Object.hasOwn(part,k)),'Mixed original-image and atlas formats');
 const image=part.source_image;require(image&&Object.keys(image).sort().join(',')==='file,height,opaque,row_order,sampler,source_origin,width'&&image.file==='texture.png'&&image.opaque===true&&image.row_order==='source_storage'&&['bottom_left','top_left'].includes(image.source_origin),'Invalid original image descriptor');
 const bytes=sourceImageMipBytes(image.width,image.height),s=image.sampler;
 require(s&&Object.keys(s).sort().join(',')==='magFilter,minFilter,wrapS,wrapT'&&[s.wrapS,s.wrapT].every(n=>[10497,33071,33648].includes(n))&&[9728,9729,9984,9985,9986,9987].includes(s.minFilter)&&[9728,9729].includes(s.magFilter),'Invalid original image sampler');
 require(Array.isArray(part.files)&&part.files.length===3&&new Set(part.files.map(f=>f.name)).size===3&&['geometry.gltf','geometry.bin','texture.png'].every(name=>part.files.some(f=>f.name===name)),'Invalid original page files');
 const file=part.files.find(f=>f.name==='texture.png');require(Number.isSafeInteger(file.bytes)&&file.bytes>0&&file.bytes<=32*1048576&&/^[0-9a-f]{64}$/.test(file.sha256),'Invalid original PNG identity');
 return {width:image.width,height:image.height,sha256:file.sha256,bytes,sampler:s};
}
export function isMemoryFamily(marker){return marker?.schema===MEMORY_FAMILY_SCHEMA&&marker.source_format===MEMORY_SOURCE_FORMAT;}
