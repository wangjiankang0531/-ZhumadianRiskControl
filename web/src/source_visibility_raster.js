// The worker contract accepts at most 16384 rays. Keep the ID pass aspect
// proportional and bound RGBA8 + single depth storage before any allocation.
export const VISIBILITY_RASTER_SAMPLES=16384;
export const VISIBILITY_RASTER_BYTES=VISIBILITY_RASTER_SAMPLES*8;
export function boundedVisibilityRaster(width,height){
 if(![width,height].every(n=>Number.isSafeInteger(n)&&n>=1&&n<=32768))throw Error('Invalid visibility viewport dimensions');
 const scale=Math.min(160/width,160/height,Math.sqrt(VISIBILITY_RASTER_SAMPLES/(width*height)));
 const w=Math.max(1,Math.floor(width*scale)),h=Math.max(1,Math.floor(height*scale));
 if(w*h>VISIBILITY_RASTER_SAMPLES)throw Error('Visibility worker sample limit exceeded');
 return {width:w,height:h};
}
export function visibilityRasterPolicy({requested,verified,width,height}){
 if(typeof requested!=='boolean'||typeof verified!=='boolean')throw Error('Invalid visibility raster capability');
 return requested&&verified?boundedVisibilityRaster(width,height):null;
}
