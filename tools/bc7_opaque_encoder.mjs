import {encodeOpaqueBc7Mode6} from './bc7_mode6_encoder.mjs';
import {BC7_PARTITION2,BC7_ANCHOR2} from './bc7_partitions.mjs';
export const BC7_OPAQUE_RECIPE='xnby.opaque_bc7_modes1_6.partition64_small_spread4_ls3.v3';
const w3=[0,9,18,27,37,46,55,64],w4=[0,4,9,13,17,21,26,30,34,38,43,47,51,55,60,64];
const members=BC7_PARTITION2.map(mask=>[0,1].map(s=>Array.from({length:16},(_,i)=>i).filter(i=>((mask>>>i)&1)===s)));
const expand=(q,p)=>{const v=q*2+p;return v*2+(v>>>6);};
function quantize(v,p){const guess=Math.max(0,Math.min(63,Math.round((v-p*2)/4)));let q=guess,error=Infinity;for(let i=Math.max(0,guess-1);i<=Math.min(63,guess+1);i++){const e=(expand(i,p)-v)**2;if(e<error){q=i;error=e;}}return q;}
function pairFit(pixels,list,parity){
 const mean=[0,0,0],cov=new Float64Array(9),indices=new Uint8Array(16);for(const i of list)for(let c=0;c<3;c++)mean[c]+=pixels[i*3+c]/list.length;
 for(const i of list)for(let c=0;c<3;c++)for(let d=0;d<3;d++)cov[c*3+d]+=(pixels[i*3+c]-mean[c])*(pixels[i*3+d]-mean[d]);
 const diagonal=[cov[0],cov[4],cov[8]];let axis=[0,0,0];axis[diagonal.indexOf(Math.max(...diagonal))]=1;
 for(let n=0;n<4;n++){const v=[0,1,2].map(c=>cov[c*3]*axis[0]+cov[c*3+1]*axis[1]+cov[c*3+2]*axis[2]),len=Math.hypot(...v);if(len<1e-10)break;axis=v.map(v=>v/len);}
 let first=list[0],last=list[0],low=Infinity,high=-Infinity;
 for(const i of list){const dot=pixels[i*3]*axis[0]+pixels[i*3+1]*axis[1]+pixels[i*3+2]*axis[2];if(dot<low){low=dot;first=i;}if(dot>high){high=dot;last=i;}}
 let a=Array.from(pixels.slice(first*3,first*3+3)),b=Array.from(pixels.slice(last*3,last*3+3)),best=null;
 for(let n=0;n<4;n++){
  const qa=a.map(v=>quantize(v,parity)),qb=b.map(v=>quantize(v,parity));a=qa.map(v=>expand(v,parity));b=qb.map(v=>expand(v,parity));
  let error=0;
  for(const i of list){let minimum=Infinity,index=0;for(let j=0;j<8;j++){let distance=0;for(let c=0;c<3;c++){const v=((64-w3[j])*a[c]+w3[j]*b[c]+32)>>6;distance+=(v-pixels[i*3+c])**2;}if(distance<minimum){minimum=distance;index=j;}}indices[i]=index;error+=minimum;}
  if(!best||error<best.error)best={qa,qb,indices:indices.slice(),error,parity};
  if(error===0)break;
  let aa=0,ab=0,bb=0;const ap=[0,0,0],bp=[0,0,0];
  for(const i of list){const y=w3[indices[i]]/64,x=1-y;aa+=x*x;ab+=x*y;bb+=y*y;for(let c=0;c<3;c++){ap[c]+=x*pixels[i*3+c];bp[c]+=y*pixels[i*3+c];}}
  const det=aa*bb-ab*ab;if(det<1e-9)break;
  a=ap.map((v,c)=>(v*bb-bp[c]*ab)/det);b=bp.map((v,c)=>(v*aa-ap[c]*ab)/det);
 }
 return best;
}
function fitPartition(pixels,partition){
 const pairs=members[partition].map(list=>{const a=pairFit(pixels,list,0),b=pairFit(pixels,list,1);return a.error<=b.error?a:b;});
 const anchors=[0,BC7_ANCHOR2[partition]];
 for(let s=0;s<2;s++)if(pairs[s].indices[anchors[s]]>=4){const pair=pairs[s];[pair.qa,pair.qb]=[pair.qb,pair.qa];for(const i of members[partition][s])pair.indices[i]=7-pair.indices[i];}
 return {partition,pairs,error:pairs[0].error+pairs[1].error};
}
function writePartition(fit,out,offset){
 let pos=0;const write=(v,n)=>{for(let i=0;i<n;i++,pos++)out[offset+(pos>>>3)]|=((v>>>i)&1)<<(pos&7);};
 write(2,2);write(fit.partition,6);
 for(let c=0;c<3;c++)for(let s=0;s<2;s++){write(fit.pairs[s].qa[c],6);write(fit.pairs[s].qb[c],6);}
 write(fit.pairs[0].parity,1);write(fit.pairs[1].parity,1);
 for(let i=0;i<16;i++){const s=(BC7_PARTITION2[fit.partition]>>>i)&1;write(fit.pairs[s].indices[i],i===0||i===BC7_ANCHOR2[fit.partition]?2:3);}
 if(pos!==128)throw Error('BC7 mode 1 layout error');
}
function mode6Error(pixels,bytes,offset){
 let pos=7;const read=n=>{const byte=offset+(pos>>>3),v=((bytes[byte]|((bytes[byte+1]??0)<<8))>>>(pos&7))&((1<<n)-1);pos+=n;return v;};
 const endpoints=[[],[]];for(let c=0;c<4;c++){endpoints[0][c]=read(7);endpoints[1][c]=read(7);}const parity=[read(1),read(1)];for(let e=0;e<2;e++)for(let c=0;c<3;c++)endpoints[e][c]=endpoints[e][c]*2+parity[e];
 let error=0;for(let i=0;i<16;i++){const w=w4[read(i===0?3:4)];for(let c=0;c<3;c++){const v=((64-w)*endpoints[0][c]+w*endpoints[1][c]+32)>>6;error+=(v-pixels[i*3+c])**2;}}return error;
}
function rankedPartitions(pixels){
 return BC7_PARTITION2.map((mask,partition)=>{
  const sum=[[0,0,0],[0,0,0]],square=[0,0],count=[0,0];
  for(let i=0;i<16;i++){const s=(mask>>>i)&1;count[s]++;for(let c=0;c<3;c++){const v=pixels[i*3+c];sum[s][c]+=v;square[s]+=v*v;}}
  let error=0;for(let s=0;s<2;s++)error+=square[s]-sum[s].reduce((n,v)=>n+v*v,0)/count[s];
  return {partition,error};
 }).sort((a,b)=>a.error-b.error||a.partition-b.partition);
}
export function encodeOpaqueBc7(rgba,width,height){
 const out=encodeOpaqueBc7Mode6(rgba,width,height),across=Math.ceil(width/4),pixels=new Float64Array(48);
 for(let by=0;by<Math.ceil(height/4);by++)for(let bx=0;bx<across;bx++){
  for(let y=0;y<4;y++)for(let x=0;x<4;x++){const from=(Math.min(height-1,by*4+y)*width+Math.min(width-1,bx*4+x))*4,to=(y*4+x)*3;for(let c=0;c<3;c++)pixels[to+c]=rgba[from+c];}
  const offset=(by*across+bx)*16;let bestError=mode6Error(pixels,out,offset),best=null;if(bestError<=192)continue;
  for(const {partition} of rankedPartitions(pixels).slice(0,width*height<=262144||bestError>3000?64:8)){const fit=fitPartition(pixels,partition);if(fit.error<bestError){bestError=fit.error;best=fit;}}
  if(best){out.fill(0,offset,offset+16);writePartition(best,out,offset);}
 }
 return out;
}
// Forced partition probe is used to compare every standard layout with Pillow.
export function encodeOpaqueBc7PartitionProbe(rgba,partition){
 if(!(rgba instanceof Uint8Array)||rgba.length!==64||!Number.isInteger(partition)||partition<0||partition>=64)throw Error('Invalid BC7 partition probe');
 const pixels=new Float64Array(48);for(let i=0;i<16;i++){if(rgba[i*4+3]!==255)throw Error('Opaque probe only');for(let c=0;c<3;c++)pixels[i*3+c]=rgba[i*4+c];}
 const fit=fitPartition(pixels,partition),out=new Uint8Array(16);writePartition(fit,out,0);return out;
}
