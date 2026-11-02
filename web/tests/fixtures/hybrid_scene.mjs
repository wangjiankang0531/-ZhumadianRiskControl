import {validateHybridTexture} from '../../src/prepared_hybrid_texture.js';
import {validateHybridOverlap} from '../../src/prepared_hybrid_overlap.js';
import {sha256} from '../../src/prepared_bc7.js';
export async function hybridFixture(){
 const source={sha256:'a'.repeat(64),width:16,height:16},prefix=new Uint8Array(336).fill(31),tail=new Uint8Array(20),overlapPayload=new Uint8Array(320),mips=[];
 for(const a of [tail,overlapPayload])for(let i=0;i<a.length;i+=4)a.set([31,47,63,255],i);
 let offset=0;for(let level=0,size=16;level<5;level++,size>>=1){const kind=level<3?'bc7':'rgba8';if(level===3)offset=0;const bytes=kind==='bc7'?Math.ceil(size/4)**2*16:size*size*4,payload=kind==='bc7'?prefix:tail,digest=await sha256(payload.subarray(offset,offset+bytes));mips.push({level,width:size,height:size,format:kind,offset,bytes,sha256:digest,decodedRgbaSHA256:kind==='bc7'?'b'.repeat(64):digest,accepted:true,quality:{rgbPSNR:kind==='bc7'?50:999,rgbChannelP99:kind==='bc7'?1:0,rgbMaxError:kind==='bc7'?2:0}});offset+=bytes;}
 const combined=new Uint8Array(356);combined.set(prefix);combined.set(tail,336);
 const manifest={schema:'xnby.bc7_rgba_tail.v1',format:'BC7_PREFIX_RGBA8_TAIL',sourceSHA256:source.sha256,sourceSize:[16,16],tailStartLevel:3,components:{bc7:{file:'prefix.bc7',bytes:336,sha256:await sha256(prefix)},rgba8:{file:'tail.rgba',bytes:20,sha256:await sha256(tail)}},payloadBytes:356,payloadSHA256:await sha256(combined),mips,accepted:true,qualityThresholds:{rgbPSNRMin:40,rgbChannelP99Max:16,rgbMaxErrorMax:96}};
 const prepared=await validateHybridTexture(manifest,prefix.buffer,tail.buffer,source),overlapMips=[];offset=0;
 for(const level of [1,2]){const size=16>>level,bytes=size*size*4,digest=await sha256(overlapPayload.subarray(offset,offset+bytes));overlapMips.push({level,width:size,height:size,offset,bytes,sha256:digest,sourceRgbaSHA256:digest,accepted:true,quality:{rgbPSNR:999,rgbChannelP99:0,rgbMaxError:0}});offset+=bytes;}
 const overlapManifest={schema:'xnby.bc7_rgba_overlap.v1',sourceSHA256:source.sha256,basePayloadSHA256:prepared.payloadSHA256,startLevel:1,payloadBytes:320,payloadSHA256:await sha256(overlapPayload),mips:overlapMips};
 return {manifest,prefix:prefix.buffer,tail:tail.buffer,prepared,overlap:await validateHybridOverlap(prepared,overlapManifest,overlapPayload.buffer),overlapManifest,overlapPayload:overlapPayload.buffer};
}
