// Opaque BC7 mode 6, independently implemented from the Microsoft BC7 format.
// No native encoder, dependencies, executable loading or filesystem access.
export const BC7_MODE6_RECIPE='xnby.opaque_bc7_mode6.pca_ls3_spread4.v2';
const weights=Object.freeze([0,4,9,13,17,21,26,30,34,38,43,47,51,55,60,64]);
const odd=x=>Math.max(1,Math.min(255,Math.round((x-1)/2)*2+1));
const color=(a,b,i,c)=>((64-weights[i])*a[c]+weights[i]*b[c]+32)>>6;

function assign(pixels,a,b,indices){
 const d=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],norm=d[0]**2+d[1]**2+d[2]**2;
 let error=0;
 for(let p=0;p<16;p++){
  const off=p*3,t=norm?((pixels[off]-a[0])*d[0]+(pixels[off+1]-a[1])*d[1]+(pixels[off+2]-a[2])*d[2])/norm:0;
  const guess=Math.max(0,Math.min(15,Math.round(t*15)));let best=Infinity,index=0;
  for(let i=Math.max(0,guess-1);i<=Math.min(15,guess+1);i++){
   let e=0;for(let c=0;c<3;c++)e+=(pixels[off+c]-color(a,b,i,c))**2;
   if(e<best){best=e;index=i;}
  }
  indices[p]=index;error+=best;
 }
 return error;
}

function fit(pixels,a,b,indices){
 let aa=0,ab=0,bb=0;const ap=[0,0,0],bp=[0,0,0];
 for(let p=0;p<16;p++){
  const y=weights[indices[p]]/64,x=1-y;aa+=x*x;ab+=x*y;bb+=y*y;
  for(let c=0;c<3;c++){ap[c]+=x*pixels[p*3+c];bp[c]+=y*pixels[p*3+c];}
 }
 const determinant=aa*bb-ab*ab;if(determinant<1e-9)return;
 for(let c=0;c<3;c++){a[c]=odd((ap[c]*bb-bp[c]*ab)/determinant);b[c]=odd((bp[c]*aa-ap[c]*ab)/determinant);}
}

function endpoints(pixels){
 const mean=[0,0,0],low=[255,255,255],high=[0,0,0];
 for(let p=0;p<16;p++)for(let c=0;c<3;c++){const v=pixels[p*3+c];mean[c]+=v/16;low[c]=Math.min(low[c],v);high[c]=Math.max(high[c],v);}
 const cov=new Float64Array(9);
 for(let p=0;p<16;p++)for(let i=0;i<3;i++)for(let j=0;j<3;j++)cov[i*3+j]+=(pixels[p*3+i]-mean[i])*(pixels[p*3+j]-mean[j]);
 let axis=[1,1,1];const diagonal=[cov[0],cov[4],cov[8]],dominant=diagonal.indexOf(Math.max(...diagonal));axis=[0,0,0];axis[dominant]=1;
 for(let n=0;n<5;n++){const v=[0,1,2].map(i=>cov[i*3]*axis[0]+cov[i*3+1]*axis[1]+cov[i*3+2]*axis[2]),length=Math.hypot(...v);if(length<1e-10)break;axis=v.map(x=>x/length);}
 let min=Infinity,max=-Infinity,first=0,last=0;
 for(let p=0;p<16;p++){const v=axis[0]*pixels[p*3]+axis[1]*pixels[p*3+1]+axis[2]*pixels[p*3+2];if(v<min){min=v;first=p;}if(v>max){max=v;last=p;}}
 return [[Array.from(pixels.slice(first*3,first*3+3),odd),Array.from(pixels.slice(last*3,last*3+3),odd)],[low.map(odd),high.map(odd)]];
}

function encodeBlock(pixels,out,offset){
 let best=Infinity,bestA,bestB,bestIndices;const indices=new Uint8Array(16);
 const starts=endpoints(pixels);
 const trial=(a,b)=>{for(let iteration=0;iteration<4;iteration++){
  const error=assign(pixels,a,b,indices);
  if(error<best){best=error;bestA=[...a];bestB=[...b];bestIndices=indices.slice();}
  if(error===0)break;
  fit(pixels,a,b,indices);
 }};
 for(const [a,b] of starts)trial([...a],[...b]);
 // A narrow source range can use an interior section of the 16-entry palette.
 // Search those endpoint spreads instead of trapping least-squares at full-span indices.
 if(best>96){const [a,b]=starts[0],middle=a.map((v,c)=>(v+b[c])/2),half=a.map((v,c)=>(b[c]-v)/2);for(const spread of [.85,1.1,1.2,1.35])trial(middle.map((v,c)=>odd(v-half[c]*spread)),middle.map((v,c)=>odd(v+half[c]*spread)));}
 if(bestIndices[0]>=8){[bestA,bestB]=[bestB,bestA];for(let p=0;p<16;p++)bestIndices[p]=15-bestIndices[p];}
 let bit=0;
 const write=(value,count)=>{for(let i=0;i<count;i++,bit++)out[offset+(bit>>3)]|=((value>>>i)&1)<<(bit&7);};
 write(64,7);
 for(let c=0;c<4;c++){write(c===3?127:bestA[c]>>>1,7);write(c===3?127:bestB[c]>>>1,7);}
 write(1,1);write(1,1);
 for(let p=0;p<16;p++)write(bestIndices[p],p===0?3:4);
 if(bit!==128)throw Error('BC7 block layout error');
}

export function encodeOpaqueBc7Mode6(rgba,width,height){
 if(!(rgba instanceof Uint8Array)||![width,height].every(v=>Number.isSafeInteger(v)&&v>0&&v<=2048)||rgba.byteLength!==width*height*4)throw Error('Invalid bounded opaque image');
 for(let i=3;i<rgba.length;i+=4)if(rgba[i]!==255)throw Error('BC7 opaque recipe rejects transparency');
 const across=Math.ceil(width/4),down=Math.ceil(height/4),out=new Uint8Array(across*down*16),pixels=new Float64Array(48);
 for(let by=0;by<down;by++)for(let bx=0;bx<across;bx++){
  for(let y=0;y<4;y++)for(let x=0;x<4;x++){
   const off=(Math.min(height-1,by*4+y)*width+Math.min(width-1,bx*4+x))*4,p=(y*4+x)*3;
   pixels[p]=rgba[off];pixels[p+1]=rgba[off+1];pixels[p+2]=rgba[off+2];
  }
  encodeBlock(pixels,out,(by*across+bx)*16);
 }
 return out;
}
