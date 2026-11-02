import {encodeOpaqueBc7} from './bc7_opaque_encoder.mjs';
import {BC7_PARTITION2,BC7_ANCHOR2} from './bc7_partitions.mjs';
import {BC7_PARTITION3,BC7_ANCHOR32,BC7_ANCHOR33} from './bc7_three_subset_partitions.mjs';

export const BC7_EXTENDED_RECIPE='xnby.opaque_bc7_modes0_1_2_3_6.tiny_mips_ls5.v2';
export const BC7_THREE_SUBSET_RECIPE='xnby.opaque_bc7_modes0_1_2_6.small_mips_ls5.v1';
const weights2=[0,21,43,64],weights3=[0,9,18,27,37,46,55,64];
const weights4=[0,4,9,13,17,21,26,30,34,38,43,47,51,55,60,64];
const members=BC7_PARTITION3.map(mask=>[0,1,2].map(s=>Array.from({length:16},(_,i)=>i).filter(i=>((mask>>>(i*2))&3)===s)));
const expand5=v=>(v<<3)|(v>>>2);
function quantizedEndpoint(values,mode){
 if(mode===3){let best=null;for(let p=0;p<2;p++){const q=values.map(v=>Math.max(0,Math.min(127,Math.round((v-p)/2)))),color=q.map(v=>v*2+p),error=color.reduce((n,v,c)=>n+(v-values[c])**2,0);if(!best||error<best.error)best={q,p,color,error};}return best;}
 if(mode===2){const q=values.map(v=>Math.max(0,Math.min(31,Math.round(v*31/255))));return {q,p:0,color:q.map(expand5)};}
 let best=null;
 for(let p=0;p<2;p++){
  const q=values.map(v=>{let bestQ=0,error=Infinity;for(let n=0;n<16;n++){const e=(expand5(n*2+p)-v)**2;if(e<error){error=e;bestQ=n;}}return bestQ;});
  const color=q.map(v=>expand5(v*2+p)),error=color.reduce((sum,v,c)=>sum+(v-values[c])**2,0);
  if(!best||error<best.error)best={q,p,color,error};
 }
 return best;
}
function fitPair(pixels,list,mode){
 const mean=[0,0,0],cov=new Float64Array(9),indices=new Uint8Array(16),weights=mode===0?weights3:weights2;
 for(const i of list)for(let c=0;c<3;c++)mean[c]+=pixels[i*3+c]/list.length;
 for(const i of list)for(let c=0;c<3;c++)for(let d=0;d<3;d++)cov[c*3+d]+=(pixels[i*3+c]-mean[c])*(pixels[i*3+d]-mean[d]);
 const diag=[cov[0],cov[4],cov[8]];let axis=[0,0,0];axis[diag.indexOf(Math.max(...diag))]=1;
 for(let n=0;n<4;n++){const v=[0,1,2].map(c=>cov[c*3]*axis[0]+cov[c*3+1]*axis[1]+cov[c*3+2]*axis[2]),len=Math.hypot(...v);if(len<1e-9)break;axis=v.map(x=>x/len);}
 let low=Infinity,high=-Infinity,first=list[0],last=list[0];
 for(const i of list){const dot=pixels[i*3]*axis[0]+pixels[i*3+1]*axis[1]+pixels[i*3+2]*axis[2];if(dot<low){low=dot;first=i;}if(dot>high){high=dot;last=i;}}
 let a=Array.from(pixels.slice(first*3,first*3+3)),b=Array.from(pixels.slice(last*3,last*3+3)),best=null;
 for(let n=0;n<6;n++){
  const ea=quantizedEndpoint(a,mode),eb=quantizedEndpoint(b,mode);a=ea.color;b=eb.color;let error=0;
  const palette=weights.map(w=>a.map((v,c)=>((64-w)*v+w*b[c]+32)>>6));
  for(const i of list){let closest=0,minimum=Infinity;for(let j=0;j<weights.length;j++){let e=0;for(let c=0;c<3;c++)e+=(palette[j][c]-pixels[i*3+c])**2;if(e<minimum){minimum=e;closest=j;}}indices[i]=closest;error+=minimum;}
  if(!best||error<best.error)best={qa:ea.q,qb:eb.q,pa:ea.p,pb:eb.p,indices:indices.slice(),error};
  if(error===0)break;
  let aa=0,ab=0,bb=0;const ap=[0,0,0],bp=[0,0,0];
  for(const i of list){const y=weights[indices[i]]/64,x=1-y;aa+=x*x;ab+=x*y;bb+=y*y;for(let c=0;c<3;c++){ap[c]+=x*pixels[i*3+c];bp[c]+=y*pixels[i*3+c];}}
  const det=aa*bb-ab*ab;if(det<1e-9)break;
  a=ap.map((v,c)=>(v*bb-bp[c]*ab)/det);b=bp.map((v,c)=>(v*aa-ap[c]*ab)/det);
 }
 return best;
}
function fitPartition(pixels,partition,mode,ceiling=Infinity){
 let error=0;const pairs=[];
 for(const list of members[partition]){const pair=fitPair(pixels,list,mode);pairs.push(pair);error+=pair.error;if(error>=ceiling)return null;}
 const anchors=[0,BC7_ANCHOR32[partition],BC7_ANCHOR33[partition]],half=mode===0?4:2,maximum=half*2-1;
 for(let s=0;s<3;s++)if(pairs[s].indices[anchors[s]]>=half){const pair=pairs[s];[pair.qa,pair.qb]=[pair.qb,pair.qa];[pair.pa,pair.pb]=[pair.pb,pair.pa];for(const i of members[partition][s])pair.indices[i]=maximum-pair.indices[i];}
 return {partition,mode,pairs,error};
}
function writePartition(fit,out,offset){
 const mode=fit.mode;let pos=0;const write=(v,n)=>{for(let i=0;i<n;i++,pos++)out[offset+(pos>>>3)]|=((v>>>i)&1)<<(pos&7);};
 write(1<<mode,mode+1);write(fit.partition,mode===0?4:6);
 for(let c=0;c<3;c++)for(let s=0;s<3;s++){write(fit.pairs[s].qa[c],mode===0?4:5);write(fit.pairs[s].qb[c],mode===0?4:5);}
 if(mode===0)for(const pair of fit.pairs){write(pair.pa,1);write(pair.pb,1);}
 for(let i=0;i<16;i++){const s=(BC7_PARTITION3[fit.partition]>>>(i*2))&3,anchor=i===0||i===BC7_ANCHOR32[fit.partition]||i===BC7_ANCHOR33[fit.partition];write(fit.pairs[s].indices[i],(mode===0?3:2)-(anchor?1:0));}
 if(pos!==128)throw Error('BC7 three-subset block boundary');
}


const twoMembers=BC7_PARTITION2.map(mask=>[0,1].map(s=>Array.from({length:16},(_,i)=>i).filter(i=>((mask>>>i)&1)===s)));
function fitMode3(pixels,partition,ceiling=Infinity){
 let error=0;const pairs=[];
 for(const list of twoMembers[partition]){const pair=fitPair(pixels,list,3);pairs.push(pair);error+=pair.error;if(error>=ceiling)return null;}
 for(let s=0;s<2;s++)if(pairs[s].indices[s===0?0:BC7_ANCHOR2[partition]]>=2){const pair=pairs[s];[pair.qa,pair.qb]=[pair.qb,pair.qa];[pair.pa,pair.pb]=[pair.pb,pair.pa];for(const i of twoMembers[partition][s])pair.indices[i]=3-pair.indices[i];}
 return {mode:3,partition,pairs,error};
}
function writeMode3(fit,out,offset){
 let pos=0;const write=(v,n)=>{for(let i=0;i<n;i++,pos++)out[offset+(pos>>>3)]|=((v>>>i)&1)<<(pos&7);};
 write(8,4);write(fit.partition,6);
 for(let c=0;c<3;c++)for(const pair of fit.pairs){write(pair.qa[c],7);write(pair.qb[c],7);}
 for(const pair of fit.pairs){write(pair.pa,1);write(pair.pb,1);}
 for(let i=0;i<16;i++){const subset=(BC7_PARTITION2[fit.partition]>>>i)&1;write(fit.pairs[subset].indices[i],i===0||i===BC7_ANCHOR2[fit.partition]?1:2);}
 if(pos!==128)throw Error('BC7 mode 3 block boundary');
}

// Deliberate small reference decoder; the acceptance decoder remains Pillow.
export function decodeOpaqueBc7Block(block){
 if(!(block instanceof Uint8Array)||block.length!==16)throw Error('Invalid block');
 let pos=0;const read=n=>{let v=0;for(let i=0;i<n;i++,pos++)v|=((block[pos>>>3]>>>(pos&7))&1)<<i;return v;};
 let mode=0;while(mode<8&&read(1)===0)mode++;if(![0,1,2,3,6].includes(mode))throw Error('Unsupported mode');
 const subsets=mode===6?1:(mode===1||mode===3)?2:3,partition=mode===6?0:read(mode===0?4:6),bits=mode===6?7:mode===1?6:mode===3?7:mode===0?4:5,channels=mode===6?4:3;
 const endpoints=Array.from({length:subsets*2},()=>[]);
 for(let c=0;c<channels;c++)for(const endpoint of endpoints)endpoint[c]=read(bits);
 let parity=[];if(mode===0||mode===3||mode===6)parity=endpoints.map(()=>read(1));else if(mode===1){const p=[read(1),read(1)];parity=[p[0],p[0],p[1],p[1]];}
 for(let e=0;e<endpoints.length;e++)for(let c=0;c<channels;c++){
  let v=endpoints[e][c],precision=bits;if(mode!==2){v=v*2+parity[e];precision++;}v<<=8-precision;endpoints[e][c]=v|(v>>>precision);
 }
 const weights=mode===6?weights4:mode===0||mode===1?weights3:weights2,ib=mode===6?4:(mode===2||mode===3)?2:3,out=new Uint8Array(64);
 for(let i=0;i<16;i++){
  const s=mode===6?0:(mode===1||mode===3)?(BC7_PARTITION2[partition]>>>i)&1:(BC7_PARTITION3[partition]>>>(i*2))&3;
  const anchor=i===0||((mode===1||mode===3)&&i===BC7_ANCHOR2[partition])||((mode===0||mode===2)&&(i===BC7_ANCHOR32[partition]||i===BC7_ANCHOR33[partition]));
  const w=weights[read(ib-(anchor?1:0))];for(let c=0;c<channels;c++)out[i*4+c]=((64-w)*endpoints[s*2][c]+w*endpoints[s*2+1][c]+32)>>6;if(channels===3)out[i*4+3]=255;
 }
 if(pos!==128)throw Error('Invalid decoded boundary');return out;
}
function squaredError(pixels,decoded){let error=0;for(let i=0;i<16;i++)for(let c=0;c<3;c++)error+=(pixels[i*3+c]-decoded[i*4+c])**2;return error;}
export function encodeOpaqueBc7ThreeSubset(rgba,width,height,{mode3=false}={}){
 const out=encodeOpaqueBc7(rgba,width,height);if(width*height>262144)return out;
 const pixels=new Float64Array(48),across=Math.ceil(width/4);
 for(let by=0;by<Math.ceil(height/4);by++)for(let bx=0;bx<across;bx++){
  for(let y=0;y<4;y++)for(let x=0;x<4;x++){const from=(Math.min(height-1,by*4+y)*width+Math.min(width-1,bx*4+x))*4,to=(y*4+x)*3;for(let c=0;c<3;c++)pixels[to+c]=rgba[from+c];}
  const offset=(by*across+bx)*16;let error=squaredError(pixels,decodeOpaqueBc7Block(out.subarray(offset,offset+16))),best=null;if(error<=192)continue;
  for(const mode of [0,2])for(let partition=0;partition<(mode===0?16:64);partition++){
   const fit=fitPartition(pixels,partition,mode,error);if(fit){error=fit.error;best=fit;}
  }
  if(mode3&&width*height<=16384)for(let partition=0;partition<64;partition++){const fit=fitMode3(pixels,partition,error);if(fit){error=fit.error;best=fit;}}
  if(best){out.fill(0,offset,offset+16);if(best.mode===3)writeMode3(best,out,offset);else writePartition(best,out,offset);}
 }
 return out;
}
export function encodeOpaqueBc7ThreeSubsetProbe(rgba,partition,mode){
 if(!(rgba instanceof Uint8Array)||rgba.length!==64||![0,2,3].includes(mode)||!Number.isInteger(partition)||partition<0||partition>=(mode===0?16:64))throw Error('Invalid three-subset probe');
 const pixels=new Float64Array(48);for(let i=0;i<16;i++){if(rgba[i*4+3]!==255)throw Error('Opaque probe only');for(let c=0;c<3;c++)pixels[i*3+c]=rgba[i*4+c];}
 const fit=mode===3?fitMode3(pixels,partition):fitPartition(pixels,partition,mode),out=new Uint8Array(16);if(mode===3)writeMode3(fit,out,0);else writePartition(fit,out,0);return out;
}

export function encodeOpaqueBc7Extended(rgba,width,height){return encodeOpaqueBc7ThreeSubset(rgba,width,height,{mode3:true});}
