import {residualRegionFactors} from './source_region_residual.js';
// A bounded, exposure-based objective. Equal screen cells retain comparable
// influence even when side panels leave less usable area in the outer cells.
// It changes priorities only; it never changes geometry or coverage admission.
export function visibilityRegionWeights({pixels,rasterWidth,rasterHeight,width,height,obscured=[],balanced=false,residuals=null}) {
 if(!(pixels instanceof Uint8Array)||![rasterWidth,rasterHeight,width,height].every(n=>Number.isInteger(n)&&n>0)||rasterWidth*rasterHeight>65536||pixels.length!==rasterWidth*rasterHeight*4)throw Error('Invalid regional visibility raster');
 const cells=Array.from({length:9},()=>({visiblePhotoSamples:0,factor:1})),weights=new Float32Array(rasterWidth*rasterHeight),visible=new Uint8Array(weights.length),addresses=new Uint8Array(weights.length);
 for(let y=0;y<rasterHeight;y++)for(let x=0;x<rasterWidth;x++){
  const i=y*rasterWidth+x,px=(x+.5)*width/rasterWidth,py=(rasterHeight-y-.5)*height/rasterHeight,c=Math.min(2,Math.floor(py/height*3))*3+Math.min(2,Math.floor(px/width*3));addresses[i]=c;
  const hidden=obscured.some(r=>px>=r.left&&px<r.right&&py>=r.top&&py<r.bottom),photo=pixels[i*4]||pixels[i*4+1]||pixels[i*4+2];
  weights[i]=hidden?.2:1;
  if(!hidden&&photo){visible[i]=1;cells[c].visiblePhotoSamples++;}
 }
 let residualPolicy=null;if(residuals){residualPolicy=residualRegionFactors({cells,visible,addresses,residuals});for(let i=0;i<weights.length;i++)if(visible[i])weights[i]*=cells[addresses[i]].factor;}
 else if(balanced){const occupied=cells.filter(c=>c.visiblePhotoSamples>0),mean=occupied.reduce((s,c)=>s+c.visiblePhotoSamples,0)/Math.max(1,occupied.length);
  for(const c of occupied)c.factor=Math.max(.5,Math.min(2,mean/c.visiblePhotoSamples));
  for(let i=0;i<weights.length;i++)if(visible[i])weights[i]*=cells[addresses[i]].factor;
 }
 return {weights,cells,policy:residualPolicy??(balanced?'bounded_equal_exposed_cell_v1':'visible_pixel_area_v1')};
}
