import {DataTexture,RedIntegerFormat,UnsignedIntType,NearestFilter,NoColorSpace,RGBAFormat,UnsignedByteType,SRGBColorSpace,Vector2,ShaderChunk} from 'three';
import {patchSourceCentroidShader} from './source_centroid_sampling.js';
const packets=new WeakMap(),textures=new WeakMap(),materials=new WeakMap(),decodeLUTs=new WeakMap(),require=(v,m)=>{if(!v)throw Error(m);};
export const SOURCE_RGB24_POLICY='source_rgb24_centroid_srgb_lut_fraction_precision_v1';
// Experimental opaque RGB byte storage. It does not grant source admission or
// replace the source PNG identity. Runtime integration is intentionally separate.
export function packOpaqueSourceRGB24(rgba,width,height,{maxTextureSize=8192}={}){
 require(Number.isInteger(maxTextureSize)&&maxTextureSize>=1&&maxTextureSize<=16384&&[width,height].every(n=>Number.isInteger(n)&&n>=1&&n<=8192&&n<=maxTextureSize),'Invalid RGB24 extent');
 const pixels=width*height;require(rgba instanceof Uint8Array&&rgba.byteLength===pixels*4&&rgba.byteLength<=32*1048576,'Invalid RGB24 RGBA payload');
 for(let i=3;i<rgba.length;i+=4)require(rgba[i]===255,'RGB24 requires verified opaque alpha');
 const words=Math.ceil(pixels*3/4),storageWidth=Math.min(maxTextureSize,Math.ceil(Math.sqrt(words))),storageHeight=Math.ceil(words/storageWidth);require(storageHeight<=maxTextureSize,'RGB24 storage exceeds device extent');
 const data=new Uint32Array(storageWidth*storageHeight);let b=0;for(let i=0;i<rgba.length;i+=4)for(let c=0;c<3;c++,b++)data[b>>>2]|=rgba[i+c]<<((b&3)*8);
 const packet=Object.freeze({schema:'xnby.source_rgb24.v1',width,height,storageWidth,storageHeight,storageBytes:data.byteLength,originalRGBABytes:rgba.byteLength,savedBytes:rgba.byteLength-data.byteLength,policy:SOURCE_RGB24_POLICY});packets.set(packet,{data});return packet;
}
export function createPackedRGB24Texture(packet){
 const stored=packets.get(packet);require(stored,'Unverified RGB24 packet');
 const texture=new DataTexture(stored.data,packet.storageWidth,packet.storageHeight,RedIntegerFormat,UnsignedIntType);texture.internalFormat='R32UI';texture.minFilter=texture.magFilter=NearestFilter;texture.generateMipmaps=false;texture.colorSpace=NoColorSpace;texture.flipY=false;texture.unpackAlignment=1;texture.needsUpdate=true;textures.set(texture,{packet,data:stored.data});return texture;
}
// A shared 1 KiB sRGB ramp keeps decoding on the same hardware texture path.
// It remains explicit and budgeted by the caller; no per-material allocation.
export function createPackedRGB24DecodeLUT(){
 const data=new Uint8Array(1024);for(let i=0;i<256;i++){data[i*4]=data[i*4+1]=data[i*4+2]=i;data[i*4+3]=255;}
 const texture=new DataTexture(data,256,1,RGBAFormat,UnsignedByteType);texture.internalFormat='SRGB8_ALPHA8';texture.colorSpace=SRGBColorSpace;texture.minFilter=texture.magFilter=NearestFilter;texture.generateMipmaps=false;texture.flipY=false;texture.needsUpdate=true;decodeLUTs.set(texture,data);return texture;
}
function validateDecodeLUT(lut){const data=decodeLUTs.get(lut);require(data&&lut.image?.data===data&&lut.image.width===256&&lut.image.height===1&&lut.format===RGBAFormat&&lut.type===UnsignedByteType&&lut.internalFormat==='SRGB8_ALPHA8'&&lut.colorSpace===SRGBColorSpace&&lut.minFilter===NearestFilter&&lut.magFilter===NearestFilter&&!lut.generateMipmaps&&!lut.flipY,'RGB24 sRGB lookup differs');return lut;}
const shaderMap=`
#ifdef USE_MAP
uniform highp usampler2D map;
uniform vec2 xnbyRGB24ImageSize;
uniform int xnbyRGB24StorageWidth;
uniform highp sampler2D xnbyRGB24DecodeLUT;
uniform float xnbyRGB24FractionScale;
uint xnbyRGB24Word(uint index){return texelFetch(map,ivec2(int(index)%xnbyRGB24StorageWidth,int(index)/xnbyRGB24StorageWidth),0).r;}
vec3 xnbyRGB24Pixel(ivec2 point){
 uint byteIndex=uint((point.y*int(xnbyRGB24ImageSize.x)+point.x)*3),offset=byteIndex&3u,index=byteIndex>>2u;
 uint value=xnbyRGB24Word(index)>>(offset*8u);
 if(offset>1u)value|=xnbyRGB24Word(index+1u)<<((4u-offset)*8u);
 return vec3(texelFetch(xnbyRGB24DecodeLUT,ivec2(int(value&255u),0),0).r,texelFetch(xnbyRGB24DecodeLUT,ivec2(int((value>>8u)&255u),0),0).r,texelFetch(xnbyRGB24DecodeLUT,ivec2(int((value>>16u)&255u),0),0).r);
}
lowp vec4 xnbyRGB24Sample(vec2 uv){
 vec2 p=clamp(uv*xnbyRGB24ImageSize-vec2(0.5),vec2(0.0),xnbyRGB24ImageSize-vec2(1.0));ivec2 a=ivec2(floor(p)),b=min(a+ivec2(1),ivec2(xnbyRGB24ImageSize)-ivec2(1));vec2 f=floor(fract(p)*xnbyRGB24FractionScale+vec2(0.5))/xnbyRGB24FractionScale;
 return vec4(mix(mix(xnbyRGB24Pixel(a),xnbyRGB24Pixel(ivec2(b.x,a.y)),f.x),mix(xnbyRGB24Pixel(ivec2(a.x,b.y)),xnbyRGB24Pixel(b),f.x),f.y),1.0);
}
#endif
`;
export function patchSourceRGB24Shader(shader,{chunks=ShaderChunk}={}){
 const patched=patchSourceCentroidShader(shader,chunks),pars='#include <map_pars_fragment>',body='#include <map_fragment>';
 require(patched.fragmentShader.split(pars).length===2&&patched.fragmentShader.split(body).length===2&&chunks.map_pars_fragment?.split('uniform sampler2D map;').length===2&&chunks.map_fragment?.split('texture2D( map, vMapUv )').length===2,'RGB24 shader contract differs');
 return {...patched,fragmentShader:patched.fragmentShader.replace(pars,shaderMap).replace(body,'#ifdef USE_MAP\n diffuseColor *= xnbyRGB24Sample(vMapUv);\n#endif')};
}
function validateTexture(material,packet){
 require(packets.has(packet),'Unverified RGB24 packet');
 const map=material?.map,stored=textures.get(map);require(material?.isMeshBasicMaterial&&stored?.packet===packet&&map.image?.data===stored.data&&map.image.width===packet.storageWidth&&map.image.height===packet.storageHeight&&map.format===RedIntegerFormat&&map.type===UnsignedIntType&&map.internalFormat==='R32UI'&&map.minFilter===NearestFilter&&map.magFilter===NearestFilter&&map.generateMipmaps===false&&map.colorSpace===NoColorSpace&&map.flipY===false,'RGB24 material storage differs');return map;
}
export function validatePackedRGB24Material(material,packet){const map=validateTexture(material,packet),b=materials.get(material);if(b)validateDecodeLUT(b.decodeLUT);require(b&&b.packet===packet&&b.map===map&&b.hook===material.onBeforeCompile&&b.key===material.customProgramCacheKey&&b.programKey===material.customProgramCacheKey(),'RGB24 material proof differs');return packet;}
export function applyPackedRGB24Sampling(material,packet,{decodeLUT,fractionBits}={}){
 const map=validateTexture(material,packet);validateDecodeLUT(decodeLUT);require(Number.isInteger(fractionBits)&&fractionBits>=8&&fractionBits<=16,'RGB24 hardware fraction profile unavailable');if(materials.has(material)){require(materials.get(material).decodeLUT===decodeLUT&&materials.get(material).fractionBits===fractionBits,'RGB24 lookup identity differs');return validatePackedRGB24Material(material,packet);}
 patchSourceRGB24Shader({vertexShader:'#include <uv_pars_vertex>',fragmentShader:'#include <uv_pars_fragment>\n#include <map_pars_fragment>\n#include <map_fragment>'});
 const previous=material.onBeforeCompile,key=String(material.customProgramCacheKey());
 material.onBeforeCompile=function(shader,renderer){previous.call(this,shader,renderer);const p=patchSourceRGB24Shader(shader);shader.vertexShader=p.vertexShader;shader.fragmentShader=p.fragmentShader;shader.uniforms.xnbyRGB24ImageSize={value:new Vector2(packet.width,packet.height)};shader.uniforms.xnbyRGB24StorageWidth={value:packet.storageWidth};shader.uniforms.xnbyRGB24DecodeLUT={value:decodeLUT};shader.uniforms.xnbyRGB24FractionScale={value:2**fractionBits};};
 material.customProgramCacheKey=()=>key+'|'+SOURCE_RGB24_POLICY+'/fraction_bits/'+fractionBits;material.needsUpdate=true;materials.set(material,{packet,map,decodeLUT,fractionBits,hook:material.onBeforeCompile,key:material.customProgramCacheKey,programKey:material.customProgramCacheKey()});return packet;
}
