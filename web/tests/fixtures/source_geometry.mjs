import {BufferGeometry,BufferAttribute} from 'three';
export function geometryFixture(){
 const positions=new Float32Array([-1,-1,0,1,-1,0,0,1,0]),normals=new Float32Array([0,0,1,0,0,1,0,0,1]),uv=new Float32Array([0,0,1,0,.5,1]),indices=new Uint32Array([0,1,2]),binary=new ArrayBuffer(108),views=[];let offset=0;
 for(const a of [positions,normals,uv,indices]){new Uint8Array(binary,offset,a.byteLength).set(new Uint8Array(a.buffer));views.push({buffer:0,byteOffset:offset,byteLength:a.byteLength,target:a===indices?34963:34962});offset+=a.byteLength;}
 const gltf={asset:{version:'2.0'},buffers:[{uri:'geometry.bin',byteLength:108}],bufferViews:views,accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3'},{bufferView:1,componentType:5126,count:3,type:'VEC3'},{bufferView:2,componentType:5126,count:3,type:'VEC2'},{bufferView:3,componentType:5125,count:3,type:'SCALAR'}],images:[{uri:'atlas.jpg'}],textures:[{source:0,sampler:0}],samplers:[{wrapS:33071,wrapT:33071,minFilter:9987,magFilter:9729}],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}],meshes:[{primitives:[{material:0,attributes:{POSITION:0,NORMAL:1,TEXCOORD_0:2},indices:3}]}],nodes:[{mesh:0}],scenes:[{nodes:[0]}],scene:0};
 const geometry=new BufferGeometry();for(const [name,a,size] of [['position',positions,3],['normal',normals,3],['uv',uv,2]])geometry.setAttribute(name,new BufferAttribute(a,size));geometry.setIndex(new BufferAttribute(indices,1));
 return {part:{vertices:3,indices:3},binary,gltf,geometry};
}
