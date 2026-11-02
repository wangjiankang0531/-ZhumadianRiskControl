// PNG container preflight shared with native/png_icon.hpp. Raster decoding remains
// the image decoder's job; a structurally valid IDAT can still fail to inflate.
export const maximumPNGIconBytes=4*1048576;
export const maximumPNGIconDimension=2048;
const prefix='data:image/png;base64,';
const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function invalid(){throw Error('自定义图标须为有效 PNG，文件不超过 4 MiB、尺寸不超过 2048×2048');}
export function validatePNGIconData(data){
  if(typeof data!=='string'||!data.startsWith(prefix))invalid();
  const text=data.slice(prefix.length);
  if(!text.length||text.length>Math.ceil(maximumPNGIconBytes/3)*4||text.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(text))invalid();
  const padding=text.endsWith('==')?2:text.endsWith('=')?1:0;
  if((padding===2&&(alphabet.indexOf(text.at(-3))&15))||(padding===1&&(alphabet.indexOf(text.at(-2))&3)))invalid();
  let decoded;try{decoded=atob(text);}catch{invalid();}
  const bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));
  if(bytes.length>maximumPNGIconBytes||bytes.length<57||[137,80,78,71,13,10,26,10].some((v,i)=>bytes[i]!==v))invalid();
  const view=new DataView(bytes.buffer),word=offset=>view.getUint32(offset,false);
  let offset=8,width=0,height=0,color=0,idat=false,palette=false,ended=false;
  while(offset<bytes.length){
    if(bytes.length-offset<12)invalid();
    const size=word(offset);if(size>bytes.length-offset-12)invalid();
    const end=offset+8+size,type=String.fromCharCode(...bytes.subarray(offset+4,offset+8));
    if(!/^[A-Za-z]{4}$/.test(type))invalid();
    let crc=0xffffffff;for(let i=offset+4;i<end;i++)crc=crcTable[(crc^bytes[i])&255]^(crc>>>8);
    if(((crc^0xffffffff)>>>0)!==word(end))invalid();
    if(offset===8){
      if(type!=='IHDR'||size!==13)invalid();
      width=word(offset+8);height=word(offset+12);const depth=bytes[offset+16];color=bytes[offset+17];
      const depths={0:[1,2,4,8,16],2:[8,16],3:[1,2,4,8],4:[8,16],6:[8,16]};
      if(!width||!height||width>maximumPNGIconDimension||height>maximumPNGIconDimension||!depths[color]?.includes(depth)||bytes[offset+18]!==0||bytes[offset+19]!==0||bytes[offset+20]>1)invalid();
    }else if(type==='IHDR')invalid();
    if(type==='PLTE'){if(idat||!size||size%3||size>768)invalid();palette=true;}
    if(type==='IDAT'){if(color===3&&!palette)invalid();idat=true;}
    offset=end+4;
    if(type==='IEND'){if(size||!idat||offset!==bytes.length)invalid();ended=true;break;}
  }
  if(!ended)invalid();
  return {bytes,width,height};
}
