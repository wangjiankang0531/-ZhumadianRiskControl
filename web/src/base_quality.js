import {measureBaseEdges,measureBaseTexels} from './lod_policy.js';

const policy='triangle_max_edge_p90_texel_edge_p90_v1';
function yieldBrowser(){return new Promise(resolve=>{const channel=new MessageChannel();channel.port1.onmessage=()=>{channel.port1.close();channel.port2.close();resolve();};channel.port2.postMessage(null);});}
export function baseGeometryDescriptor(gltf){
  if(gltf.buffers?.length!==1||gltf.meshes?.length!==1||gltf.meshes[0].primitives?.length!==1)throw Error('unsupported base layout');
  const primitive=gltf.meshes[0].primitives[0];if((primitive.mode??4)!==4)throw Error('base must contain triangles');
  const field=(id,type,componentType)=>{const a=gltf.accessors[id],v=gltf.bufferViews[a.bufferView];if(a.sparse||a.normalized||a.type!==type||a.componentType!==componentType||v.buffer!==0||v.byteStride)throw Error('unsupported base accessor');return{type,componentType,count:a.count,byteOffset:(v.byteOffset??0)+(a.byteOffset??0)};};
  return{buffer_bytes:gltf.buffers[0].byteLength,buffer_uri:gltf.buffers[0].uri,position:field(primitive.attributes.POSITION,'VEC3',5126),uv:field(primitive.attributes.TEXCOORD_0,'VEC2',5126),indices:field(primitive.indices,'SCALAR',5125)};
}
export function preparedQualityRecord(catalog,geometry,descriptor,fingerprints){
  const edges=measureBaseEdges(catalog,geometry.positions,geometry.indices),texels=measureBaseTexels(catalog,geometry.positions,geometry.indices,geometry.uvs,geometry.textureWidth,geometry.textureHeight);
  return{schema:'xnby.base.lod.quality.v1',policy,descriptor,catalog_sha256:fingerprints.catalog,buffer_sha256:fingerprints.buffer,texture_width:geometry.textureWidth,texture_height:geometry.textureHeight,roots:catalog.root_records.map(root=>({tile_id:root.tile_id,edge_p90_m:edges.get(root.tile_id),texel_p90_m:texels.get(root.tile_id)??0}))};
}
export function validatePreparedQuality(record,catalog,descriptor,textureWidth,textureHeight){
  if(record?.schema!=='xnby.base.lod.quality.v1'||record.policy!==policy||JSON.stringify(record.descriptor)!==JSON.stringify(descriptor)||record.texture_width!==textureWidth||record.texture_height!==textureHeight||!Array.isArray(record.roots)||record.roots.length!==catalog.root_records.length||!/^[a-f0-9]{64}$/.test(record.catalog_sha256)||!/^[a-f0-9]{64}$/.test(record.buffer_sha256))throw Error('prepared quality identity mismatch');
  const edges=new Map(),texels=new Map();
  for(let i=0;i<record.roots.length;i++){const row=record.roots[i];if(row.tile_id!==catalog.root_records[i].tile_id||edges.has(row.tile_id)||!Number.isFinite(row.edge_p90_m)||row.edge_p90_m<=0||!Number.isFinite(row.texel_p90_m)||row.texel_p90_m<0)throw Error('invalid prepared quality root');edges.set(row.tile_id,row.edge_p90_m);if(row.texel_p90_m>0)texels.set(row.tile_id,row.texel_p90_m);}
  return{edges,texels};
}
export async function measureBaseQualityAsync(catalog,geometry,yieldControl=yieldBrowser){
  const edges=new Map(),texels=new Map();
  for(let offset=0;offset<catalog.root_records.length;offset+=8){
    const part={root_records:catalog.root_records.slice(offset,offset+8)};
    for(const [id,value] of measureBaseEdges(part,geometry.positions,geometry.indices))edges.set(id,value);
    for(const [id,value] of measureBaseTexels(part,geometry.positions,geometry.indices,geometry.uvs,geometry.textureWidth,geometry.textureHeight))texels.set(id,value);
    if(offset+8<catalog.root_records.length)await yieldControl();
  }
  return{edges,texels,source:'measured'};
}
export async function resolveBaseQuality({catalog,catalogBytes,gltf,buffer,geometry,fetchPrepared,digest,yieldControl}){
  try{
    const record=await fetchPrepared(),descriptor=baseGeometryDescriptor(gltf);
    const result=validatePreparedQuality(record,catalog,descriptor,geometry.textureWidth,geometry.textureHeight);
    const bytes=await buffer();if(bytes.byteLength!==descriptor.buffer_bytes)throw Error('base buffer length changed');
    const [catalogSha,bufferSha]=await Promise.all([digest(catalogBytes),digest(bytes)]);
    if(catalogSha!==record.catalog_sha256||bufferSha!==record.buffer_sha256)throw Error('prepared quality content changed');
    return{...result,source:'prepared'};
  }catch(error){
    const result=await measureBaseQualityAsync(catalog,geometry,yieldControl);return{...result,fallbackReason:String(error.message)};
  }
}
