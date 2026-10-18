// Verified WebGL layout only. Native/source manifest accounting is separate.
export const WEB_SOURCE_GEOMETRY_LAYOUT='three_float32_pnu_uint32_v1';
const require=(ok,message)=>{if(!ok)throw Error(message);};
export function webSourceGeometryBytes(part){
 require(Number.isSafeInteger(part.vertices)&&part.vertices>0&&Number.isSafeInteger(part.indices)&&part.indices>0&&part.indices%3===0,'Invalid WEB source geometry counts');
 const bytes=part.vertices*32+part.indices*4;require(Number.isSafeInteger(bytes)&&bytes>0&&bytes<=32*1048576,'Invalid WEB source geometry cost');return bytes;
}
export function validateSourceGltfGeometry(gltf,part,binary=null){
 const bytes=webSourceGeometryBytes(part),primitive=gltf.meshes?.[0]?.primitives?.[0];
 require(gltf.buffers?.length===1&&gltf.buffers[0].uri==='geometry.bin'&&gltf.buffers[0].byteLength===bytes&&gltf.accessors?.length===4&&gltf.bufferViews?.length===4,'Unsupported WEB geometry storage');
 require(gltf.nodes?.length===1&&JSON.stringify(gltf.nodes[0])==='{"mesh":0}'&&gltf.scene===0&&gltf.scenes?.length===1&&JSON.stringify(gltf.scenes[0])==='{"nodes":[0]}'&&!gltf.animations?.length&&!gltf.skins?.length&&!primitive?.targets&&!primitive?.extensions,'Unsupported WEB geometry scene');
 require(Object.keys(primitive.attributes??{}).sort().join(',')==='NORMAL,POSITION,TEXCOORD_0'&&primitive.mode===undefined,'Unsupported WEB geometry primitive');
 const specs=[['POSITION','VEC3',3,part.vertices,5126],['NORMAL','VEC3',3,part.vertices,5126],['TEXCOORD_0','VEC2',2,part.vertices,5126],['indices','SCALAR',1,part.indices,5125]],ranges=[],accessors=new Set(),views=new Set();
 for(const [name,type,components,count,componentType] of specs){
  const index=name==='indices'?primitive.indices:primitive.attributes[name],a=gltf.accessors[index],view=gltf.bufferViews[a?.bufferView],size=count*components*4,start=view?.byteOffset??0;
  require(Number.isInteger(index)&&!accessors.has(index)&&a&&view&&!views.has(a.bufferView)&&a.type===type&&a.componentType===componentType&&a.count===count&&!a.normalized&&!a.sparse&&(a.byteOffset??0)===0&&!view.byteStride&&view.buffer===0&&view.byteLength===size&&Number.isSafeInteger(start)&&start>=0&&start%4===0&&start+size<=bytes,'Unsupported WEB geometry accessor');
  require(view.target===undefined||view.target===(name==='indices'?34963:34962),'Unexpected WEB geometry buffer target');accessors.add(index);views.add(a.bufferView);ranges.push({start,end:start+size,name,count,components});
 }
 ranges.sort((a,b)=>a.start-b.start);let end=0;for(const r of ranges){require(r.start===end,'WEB geometry views overlap or leave unexplained bytes');end=r.end;}require(end===bytes,'WEB geometry trailing bytes');
 if(binary!==null){require(binary instanceof ArrayBuffer&&binary.byteLength===bytes,'WEB geometry binary length mismatch');for(const r of ranges){if(r.name==='indices')require(new Uint32Array(binary,r.start,r.count).every(i=>i<part.vertices),'WEB geometry index out of range');else require(new Float32Array(binary,r.start,r.count*r.components).every(Number.isFinite),'Non-finite WEB geometry attribute');}}
 return bytes;
}
export function validateLoadedSourceGeometry(geometry,part){
 const bytes=webSourceGeometryBytes(part);require(geometry?.isBufferGeometry&&!geometry.isInstancedBufferGeometry&&Object.keys(geometry.attributes).sort().join(',')==='normal,position,uv'&&!Object.keys(geometry.morphAttributes??{}).length,'Unexpected loaded WEB geometry attributes');
 let actual=0;const seen=new Set();
 for(const [name,itemSize] of [['position',3],['normal',3],['uv',2]]){const a=geometry.attributes[name];require(a?.isBufferAttribute&&!a.isInterleavedBufferAttribute&&!a.isInstancedBufferAttribute&&a.array instanceof Float32Array&&a.itemSize===itemSize&&a.count===part.vertices&&!a.normalized&&a.array.byteLength===part.vertices*itemSize*4&&!seen.has(a),'Unexpected loaded WEB geometry layout');seen.add(a);actual+=a.array.byteLength;}
 const index=geometry.index;require(index?.isBufferAttribute&&!index.isInterleavedBufferAttribute&&index.array instanceof Uint32Array&&index.itemSize===1&&index.count===part.indices&&!index.normalized&&index.array.byteLength===part.indices*4,'Unexpected loaded WEB geometry indices');actual+=index.array.byteLength;require(actual===bytes,'Loaded WEB geometry byte count mismatch');return actual;
}
