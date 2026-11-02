import {PreparedTextureCancelled} from './prepared_bc7.js';
const stats={bitmap:0,html:0,fallbacks:0,owned:0,peakOwned:0,closedBitmaps:0,cropBitmaps:0,cropFailures:0};
export const originalImageStats=()=>({...stats,scope:'image_ownership_counts_not_browser_heap_bytes'});
export class OriginalImageCropUnavailable extends Error{}
export async function decodeOriginalImage({blob,width,height,crop=null,stillWanted=()=>true,preferBitmap=true,decodeBitmap=typeof createImageBitmap==='function'?((...args)=>createImageBitmap(...args)):null,loadImage}){
 const wanted=()=>{if(!stillWanted())throw new PreparedTextureCancelled('Original source image no longer wanted');};
 const rect=crop===null?null:Array.isArray(crop)?[...crop]:[];
 if(rect&&(![width,height].every(n=>Number.isSafeInteger(n)&&n>0&&n<=8192)||rect.length!==4||!rect.every(Number.isSafeInteger)||rect[0]<0||rect[1]<0||rect[2]<=0||rect[3]<=0||rect[0]+rect[2]>width||rect[1]+rect[3]>height))throw Error('Invalid original image crop');
 const valid=image=>image?.width===(rect?rect[2]:width)&&image?.height===(rect?rect[3]:height);
 wanted();let image=null,kind='html';
 if(preferBitmap&&decodeBitmap){try{const options={imageOrientation:'from-image',premultiplyAlpha:'none',colorSpaceConversion:'none'};image=await decodeBitmap(...(rect?[blob,...rect,options]:[blob,options]));wanted();if(!valid(image))throw Error('Bitmap image dimensions differ');kind='bitmap';}
  catch(error){image?.close?.();image=null;wanted();if(rect){stats.cropFailures++;throw new OriginalImageCropUnavailable('Original image crop requires full-image replanning');}stats.fallbacks++;}}
 if(!image&&rect){stats.cropFailures++;throw new OriginalImageCropUnavailable('Original bitmap crop is unavailable; full-image replanning required');}
 if(!image){image=await loadImage(blob);wanted();if(!valid(image))throw Error('Decoded source image size mismatch');}
 if(rect)stats.cropBitmaps++;
 stats[kind]++;stats.owned++;stats.peakOwned=Math.max(stats.peakOwned,stats.owned);let disposed=false;
 return {image,kind,dispose(){if(disposed)return;disposed=true;stats.owned--;if(kind==='bitmap'){image.close();stats.closedBitmaps++;}}};
}
export function ownOriginalImageTexture(texture,decoded){texture.userData.ownedOriginalImage=true;texture.addEventListener('dispose',()=>decoded.dispose());return texture;}
