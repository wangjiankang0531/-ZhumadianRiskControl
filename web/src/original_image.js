import {PreparedTextureCancelled} from './prepared_bc7.js';
const stats={bitmap:0,html:0,fallbacks:0,owned:0,peakOwned:0,closedBitmaps:0};
export const originalImageStats=()=>({...stats,scope:'image_ownership_counts_not_browser_heap_bytes'});
export async function decodeOriginalImage({blob,width,height,stillWanted=()=>true,preferBitmap=true,decodeBitmap=typeof createImageBitmap==='function'?((...args)=>createImageBitmap(...args)):null,loadImage}){
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Original source image no longer wanted');};
 const valid=image=>image?.width===width&&image?.height===height;
 wanted();let image=null,kind='html';
 if(preferBitmap&&decodeBitmap){try{image=await decodeBitmap(blob,{imageOrientation:'from-image',premultiplyAlpha:'none',colorSpaceConversion:'none'});wanted();if(!valid(image))throw Error('Bitmap image dimensions differ');kind='bitmap';}
  catch(error){image?.close?.();image=null;wanted();stats.fallbacks++;}}
 if(!image){image=await loadImage(blob);wanted();if(!valid(image))throw Error('Decoded source image size mismatch');}
 stats[kind]++;stats.owned++;stats.peakOwned=Math.max(stats.peakOwned,stats.owned);let disposed=false;
 return {image,kind,dispose(){if(disposed)return;disposed=true;stats.owned--;if(kind==='bitmap'){image.close();stats.closedBitmaps++;}}};
}
export function ownOriginalImageTexture(texture,decoded){texture.userData.ownedOriginalImage=true;texture.addEventListener('dispose',()=>decoded.dispose());return texture;}
