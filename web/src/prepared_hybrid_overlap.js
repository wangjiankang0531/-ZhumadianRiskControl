import {isValidatedHybridTexture} from './prepared_hybrid_texture.js';
import {sha256,rgbaMipBytes} from './prepared_bc7.js';
const validated=new WeakSet(),SHA=/^[0-9a-f]{64}$/;
const require=(ok,message)=>{if(!ok)throw Error('Hybrid overlap: '+message);};
export const isValidatedHybridOverlap=value=>validated.has(value);
// A separate extension identity. The original complete hybrid v1 contract is
// not weakened and cannot mistake these extra original mips for BC7 payload.
export function describeHybridOverlap(base,manifest){
 require(manifest?.schema==='xnby.bc7_rgba_overlap.v1'&&manifest.sourceSHA256===base.sourceSHA256&&manifest.basePayloadSHA256===base.payloadSHA256,'source or base identity differs');
 const start=base.tailStartLevel-2;require(start>=0&&manifest.startLevel===start&&Array.isArray(manifest.mips)&&manifest.mips.length===2,'requires two prefix overlap levels');
 require(Number.isSafeInteger(manifest.payloadBytes)&&manifest.payloadBytes>0&&manifest.payloadBytes<=8*1048576&&SHA.test(manifest.payloadSHA256),'payload identity differs');
 let offset=0;const mips=[];
 for(let i=0;i<2;i++){
  const row=manifest.mips[i],level=start+i,source=base.mips[level],bytes=source.width*source.height*4;
  require(row.level===level&&row.width===source.width&&row.height===source.height&&row.offset===offset&&row.bytes===bytes&&row.accepted===true&&row.quality?.rgbPSNR===999&&row.quality?.rgbChannelP99===0&&row.quality?.rgbMaxError===0&&SHA.test(row.sha256)&&row.sha256===row.sourceRgbaSHA256,'invalid original overlap mip');
  mips.push(Object.freeze({level,width:row.width,height:row.height,offset,bytes,sha256:row.sha256}));offset+=bytes;
 }
 require(offset===manifest.payloadBytes&&base.bytes+offset<rgbaMipBytes(base.width,base.height),'trailing or oversized overlap');
 return {sourceSHA256:base.sourceSHA256,basePayloadSHA256:base.payloadSHA256,payloadSHA256:manifest.payloadSHA256,startLevel:start,bytes:offset,mips};
}
export async function validateHybridOverlap(base,manifest,payload){
 require(isValidatedHybridTexture(base),'unverified base texture');const info=describeHybridOverlap(base,manifest);
 require(payload instanceof ArrayBuffer&&payload.byteLength===info.bytes&&await sha256(payload)===info.payloadSHA256,'payload identity differs');
 const mips=[];for(const row of info.mips){const data=new Uint8Array(payload,row.offset,row.bytes);require(await sha256(data)===row.sha256,'mip hash differs');for(let a=3;a<data.length;a+=4)require(data[a]===255,'overlap not opaque');mips.push(Object.freeze({...row,data}));}
 const result=Object.freeze({...info,mips:Object.freeze(mips)});validated.add(result);return result;
}
