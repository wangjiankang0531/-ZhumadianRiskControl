import {sha256} from '../../src/prepared_bc7.js';
export async function clientSourcePageFixture({directory='part_000',uv=[.2,.2,.7,.2,.2,.7]}={}){
 const positions=new Float32Array([-1,-1,0,1,-1,0,0,1,0]),texture=new Float32Array(uv),indices=new Uint32Array([0,1,2]),binary=new ArrayBuffer(72),views=[];let offset=0;
 for(const value of [positions,texture,indices]){new Uint8Array(binary,offset,value.byteLength).set(new Uint8Array(value.buffer));views.push({buffer:0,byteOffset:offset,byteLength:value.byteLength});offset+=value.byteLength;}
 const sampler={wrapS:33071,wrapT:33071,minFilter:9729,magFilter:9729};
 const gltf={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0,TEXCOORD_0:1},indices:2,material:0}]}],buffers:[{uri:'geometry.bin',byteLength:72}],bufferViews:views,accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3'},{bufferView:1,componentType:5126,count:3,type:'VEC2'},{bufferView:2,componentType:5125,count:3,type:'SCALAR'}],images:[{uri:'texture.png'}],textures:[{source:0,sampler:0}],samplers:[sampler],materials:[{pbrMetallicRoughness:{baseColorTexture:{index:0}}}]};
 const jsonBytes=new TextEncoder().encode(JSON.stringify(gltf)).buffer;
 // Header-only PNG transport fixture; Node tests stub bitmap decode and make
 // no image/pixel/GPU claim. GLTFLoader and typed geometry parsing remain real.
 const png=new ArrayBuffer(33),header=new DataView(png);for(const [offset,value] of [[0,0x89504e47],[4,0x0d0a1a0a],[8,13],[12,0x49484452],[16,16],[20,12]])header.setUint32(offset,value);header.setUint8(24,8);header.setUint8(25,6);
 const part={directory,source_format:'osgb_memory_png_crop_v2',geometry_layout:'three_float32_pu_uint32_v1',vertices:3,indices:3,gpu_payload_bytes:972,source_image:{file:'texture.png',width:16,height:12,original_width:16,original_height:12,opaque:true,row_order:'source_storage',source_origin:'bottom_left',source_rect:[0,0,16,12],uv_transform:[1,1,0,0],mip_levels:1,sampler:{...sampler}},files:[]};
 const files={'geometry.gltf':jsonBytes,'geometry.bin':binary,'texture.png':png};for(const [name,data] of Object.entries(files))part.files.push({name,bytes:data.byteLength,sha256:await sha256(data)});
 const node={name:'parent',children:['child'],source_sha256:'c'.repeat(64),depth:0,triangles:1,bounds_min:[-1,-1,0],bounds_max:[1,1,0],longest_edge_p90_m:1,texel_world_p90_m:.1,spans:[{part:directory,first:0,count:3}]};
 const marker={schema:'zhumadian.osgb_source_frontier.v2',source_format:part.source_format,texture_policy:'original_pixels_v1',tile_id:1,parts:[part],indices:3,gpu_payload_bytes:972,source_nodes:[node]};
 return {part,marker,jsonBytes,binary,files,loadFile:async(p,name)=>files[name]};
}
