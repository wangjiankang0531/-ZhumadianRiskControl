import {encodeOpaqueBc7Extended,decodeOpaqueBc7Block} from './bc7_three_subset_encoder.mjs';

export const BC7_SEPARATED_RECIPE='xnby.opaque_bc7_modes0_1_2_3_4_5_6.separated_small_valid_ls5.v1';
const weights2=[0,21,43,64],weights3=[0,9,18,27,37,46,55,64];
const expanded=(q,bits)=>{const v=q<<(8-bits);return v|(v>>>bits);};
const quantized=(value,bits)=>Math.max(0,Math.min((1<<bits)-1,Math.round(value*((1<<bits)-1)/255)));
function fitVectors(pixels,channels,precision,indexBits,valid){
 const weights=indexBits===2?weights2:weights3,n=channels.length,mean=Array(n).fill(0),cov=new Float64Array(n*n);
 for(const i of valid)for(let c=0;c<n;c++)mean[c]+=pixels[i*4+channels[c]]/valid.length;
 for(const i of valid)for(let c=0;c<n;c++)for(let d=0;d<n;d++)cov[c*n+d]+=(pixels[i*4+channels[c]]-mean[c])*(pixels[i*4+channels[d]]-mean[d]);
 let axis=Array(n).fill(0),diagonal=Array.from({length:n},(_,i)=>cov[i*n+i]);axis[diagonal.indexOf(Math.max(...diagonal))]=1;
 for(let turn=0;turn<4;turn++){const v=Array.from({length:n},(_,c)=>axis.reduce((sum,a,d)=>sum+a*cov[c*n+d],0)),length=Math.hypot(...v);if(length<1e-9)break;axis=v.map(v=>v/length);}
 let low=Infinity,high=-Infinity,first=valid[0],last=valid[0];
 for(const i of valid){const projection=axis.reduce((sum,v,c)=>sum+v*pixels[i*4+channels[c]],0);if(projection<low){low=projection;first=i;}if(projection>high){high=projection;last=i;}}
 const originalA=channels.map(c=>pixels[first*4+c]),originalB=channels.map(c=>pixels[last*4+c]),indices=new Uint8Array(16);let best=null;
 for(const spread of [1,0.75,1.25]){
  let a=originalA.map((v,c)=>(v+originalB[c])/2+(v-originalB[c])*spread/2),b=originalB.map((v,c)=>(v+originalA[c])/2+(v-originalA[c])*spread/2);
  for(let iteration=0;iteration<6;iteration++){
   const qa=a.map(v=>quantized(v,precision)),qb=b.map(v=>quantized(v,precision));a=qa.map(v=>expanded(v,precision));b=qb.map(v=>expanded(v,precision));
   const palette=weights.map(w=>a.map((v,c)=>((64-w)*v+w*b[c]+32)>>6));
   for(let i=0;i<16;i++){let closest=0,error=Infinity;for(let j=0;j<weights.length;j++){let e=0;for(let c=0;c<n;c++)e+=(palette[j][c]-pixels[i*4+channels[c]])**2;if(e<error){error=e;closest=j;}}indices[i]=closest;}
   let error=0;for(const i of valid)for(let c=0;c<n;c++)error+=(palette[indices[i]][c]-pixels[i*4+channels[c]])**2;
   if(!best||error<best.error)best={qa,qb,indices:indices.slice(),error,indexBits};if(error===0)break;
   let aa=0,ab=0,bb=0;const ap=Array(n).fill(0),bp=Array(n).fill(0);
   for(const i of valid){const y=weights[indices[i]]/64,x=1-y;aa+=x*x;ab+=x*y;bb+=y*y;for(let c=0;c<n;c++){ap[c]+=x*pixels[i*4+channels[c]];bp[c]+=y*pixels[i*4+channels[c]];}}
   const det=aa*bb-ab*ab;if(det<1e-9)break;
   a=ap.map((v,c)=>(v*bb-bp[c]*ab)/det);b=bp.map((v,c)=>(v*aa-ap[c]*ab)/det);
  }
 }
 if(best.indices[0]>=(1<<(indexBits-1))){[best.qa,best.qb]=[best.qb,best.qa];const maximum=(1<<indexBits)-1;for(let i=0;i<16;i++)best.indices[i]=maximum-best.indices[i];}
 return best;
}
function encodeCandidate(rgba,mode,rotation,selection,valid){
 const swapped=rgba.slice();if(rotation)for(let i=0;i<16;i++){const p=i*4,c=p+rotation-1;[swapped[c],swapped[p+3]]=[swapped[p+3],swapped[c]];}
 const rgb=fitVectors(swapped,[0,1,2],mode===4?5:7,mode===4&&selection===1?3:2,valid);
 const alpha=fitVectors(swapped,[3],mode===4?6:8,mode===4&&selection===0?3:2,valid);
 const out=new Uint8Array(16);let pos=0;const write=(v,n)=>{for(let i=0;i<n;i++,pos++)out[pos>>>3]|=((v>>>i)&1)<<(pos&7);};
 write(1<<mode,mode+1);write(rotation,2);if(mode===4)write(selection,1);
 for(let c=0;c<3;c++){write(rgb.qa[c],mode===4?5:7);write(rgb.qb[c],mode===4?5:7);}write(alpha.qa[0],mode===4?6:8);write(alpha.qb[0],mode===4?6:8);
 const streams=mode===4&&selection===1?[alpha,rgb]:[rgb,alpha];
 for(const stream of streams)for(let i=0;i<16;i++)write(stream.indices[i],stream.indexBits-(i===0?1:0));
 if(pos!==128)throw Error('BC7 separated-channel boundary');return out;
}
export function decodeOpaqueBc7SeparatedBlock(block){
 if(!(block instanceof Uint8Array)||block.length!==16)throw Error('Invalid BC7 block');
 let pos=0;const read=n=>{let v=0;for(let i=0;i<n;i++,pos++)v|=((block[pos>>>3]>>>(pos&7))&1)<<i;return v;};
 let mode=0;while(mode<8&&read(1)===0)mode++;if(mode!==4&&mode!==5)return decodeOpaqueBc7Block(block);
 const rotation=read(2),selection=mode===4?read(1):0,endpoints=[[],[]];
 for(let c=0;c<3;c++)for(let e=0;e<2;e++)endpoints[e][c]=expanded(read(mode===4?5:7),mode===4?5:7);
 for(let e=0;e<2;e++)endpoints[e][3]=expanded(read(mode===4?6:8),mode===4?6:8);
 const first=Array.from({length:16},(_,i)=>read(i===0?1:2)),secondBits=mode===4?3:2,second=Array.from({length:16},(_,i)=>read(secondBits-(i===0?1:0))),out=new Uint8Array(64);
 for(let i=0;i<16;i++){
  const rgbIndex=selection?second[i]:first[i],alphaIndex=selection?first[i]:second[i],rgbWeights=mode===4&&selection?weights3:weights2,alphaWeights=mode===4&&!selection?weights3:weights2;
  for(let c=0;c<4;c++){const w=c===3?alphaWeights[alphaIndex]:rgbWeights[rgbIndex];out[i*4+c]=((64-w)*endpoints[0][c]+w*endpoints[1][c]+32)>>6;}
  if(rotation){const p=i*4,c=p+rotation-1;[out[c],out[p+3]]=[out[p+3],out[c]];}
 }
 if(pos!==128)throw Error('Invalid separated decode boundary');return out;
}
function errorOnSource(rgba,decoded,valid){let error=0;for(const i of valid){if(decoded[i*4+3]!==255)return Infinity;for(let c=0;c<3;c++)error+=(rgba[i*4+c]-decoded[i*4+c])**2;}return error;}
export function encodeOpaqueBc7Separated(rgba,width,height){
 const out=encodeOpaqueBc7Extended(rgba,width,height);if(width*height>16384)return out;
 const across=Math.ceil(width/4),block=new Uint8Array(64);
 for(let by=0;by<Math.ceil(height/4);by++)for(let bx=0;bx<across;bx++){
  const valid=[];for(let y=0;y<4;y++)for(let x=0;x<4;x++){const i=y*4+x,from=(Math.min(height-1,by*4+y)*width+Math.min(width-1,bx*4+x))*4;block.set(rgba.subarray(from,from+4),i*4);if(by*4+y<height&&bx*4+x<width)valid.push(i);}
  const offset=(by*across+bx)*16;let bestError=errorOnSource(block,decodeOpaqueBc7SeparatedBlock(out.subarray(offset,offset+16)),valid),best=null;
  if(bestError<=valid.length*3)continue;
  for(const mode of [4,5])for(let rotation=0;rotation<4;rotation++)for(let selection=0;selection<(mode===4?2:1);selection++){
   const encoded=encodeCandidate(block,mode,rotation,selection,valid),error=errorOnSource(block,decodeOpaqueBc7SeparatedBlock(encoded),valid);if(error<bestError){bestError=error;best=encoded;}
  }
  if(best)out.set(best,offset);
 }
 return out;
}
export function encodeOpaqueBc7SeparatedProbe(rgba,mode,rotation,selection=0){
 if(!(rgba instanceof Uint8Array)||rgba.length!==64||![4,5].includes(mode)||!Number.isInteger(rotation)||rotation<0||rotation>3||!Number.isInteger(selection)||selection<0||selection>(mode===4?1:0)||Array.from({length:16},(_,i)=>rgba[i*4+3]).some(v=>v!==255))throw Error('Invalid opaque separated probe');
 return encodeCandidate(rgba,mode,rotation,selection,Array.from({length:16},(_,i)=>i));
}
