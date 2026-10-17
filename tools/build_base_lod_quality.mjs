import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {preparedQualityRecord,baseGeometryDescriptor} from '../web/src/base_quality.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),folder=path.join(root,'assets/showcase/runtime/zhumadian/full');
const catalogBytes=fs.readFileSync(path.join(root,'data/showcase/zhumadian_native_hierarchy.json')),catalog=JSON.parse(catalogBytes),gltf=JSON.parse(fs.readFileSync(path.join(folder,'zhumadian_full.gltf'))),descriptor=baseGeometryDescriptor(gltf),buffer=fs.readFileSync(path.join(folder,'zhumadian_full.bin'));
if(descriptor.buffer_uri!=='zhumadian_full.bin'||descriptor.buffer_bytes!==buffer.length)throw Error('base buffer identity mismatch');
function accessor(field,width,Type){return new Type(buffer.buffer,buffer.byteOffset+field.byteOffset,field.count*width);}
function jpegDimensions(bytes){
 if(bytes.readUInt16BE(0)!==0xffd8)throw Error('expected JPEG base atlas');
 for(let offset=2;offset+8<bytes.length;){
  if(bytes[offset++]!==0xff)throw Error('invalid JPEG marker');
  let marker=bytes[offset++];while(marker===0xff)marker=bytes[offset++];
  if(marker===0xd9||marker===0xda)break;if(marker===1||marker>=0xd0&&marker<=0xd7)continue;
  const length=bytes.readUInt16BE(offset);if(length<2||offset+length>bytes.length)throw Error('invalid JPEG segment');
  if([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker))return{width:bytes.readUInt16BE(offset+5),height:bytes.readUInt16BE(offset+3)};
  offset+=length;
 }
 throw Error('JPEG size missing');
}
if(gltf.images?.length!==1||gltf.images[0].uri!=='zhumadian_full_atlas.jpg')throw Error('unexpected base atlas');
const dimensions=jpegDimensions(fs.readFileSync(path.join(folder,gltf.images[0].uri)));
const geometry={positions:accessor(descriptor.position,3,Float32Array),uvs:accessor(descriptor.uv,2,Float32Array),indices:accessor(descriptor.indices,1,Uint32Array),textureWidth:dimensions.width,textureHeight:dimensions.height};
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex'),start=performance.now();
const result=preparedQualityRecord(catalog,geometry,descriptor,{catalog:sha(catalogBytes),buffer:sha(buffer)}),output=path.join(folder,'base_lod_quality.json');
fs.writeFileSync(output+'.pending',JSON.stringify(result));fs.renameSync(output+'.pending',output);
console.log(JSON.stringify({output,roots:result.roots.length,bytes:fs.statSync(output).size,seconds:(performance.now()-start)/1000,buffer_sha256:result.buffer_sha256}));
