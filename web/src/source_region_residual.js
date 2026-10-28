// Observation/priority only. P90 projection is not geometric error, and these
// weights never grant source admission, budget or an incomplete replacement.
export function sourceRegionResiduals(pixels,registry,metrics,scale){
 if(!(pixels instanceof Uint8Array)||pixels.length%4||!Number.isFinite(scale)||scale<=0)throw Error('Invalid residual observation');
 const values=new Float64Array(pixels.length/4),base=new Uint8Array(values.length);
 for(let i=0;i<values.length;i++){
  const off=i*4,id=pixels[off]|pixels[off+1]<<8|pixels[off+2]<<16;if(!id)continue;
  const key=registry.get(id),node=metrics.get(key);if(!key)throw Error('Unknown residual source');base[i]=key.startsWith('root/')?1:0;
  if(!Number.isFinite(node?.longest_edge_p90_m)||node.longest_edge_p90_m<0||!Number.isFinite(node?.texel_world_p90_m)||node.texel_world_p90_m<=0){values[i]=NaN;continue;}
  const depth=.5*120000**(pixels[off+3]/255),quality=Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*scale/depth;
  values[i]=quality>6?Math.log2(1+quality/6):0;
 }return {values,base};
}

export function residualRegionFactors({cells,visible,addresses,residuals}){
 const {values,base}=residuals??{};
 if(!(values instanceof Float64Array)||!(base instanceof Uint8Array)||values.length!==visible.length||base.length!==visible.length||values.some(v=>!Number.isNaN(v)&&(!Number.isFinite(v)||v<0))||base.some(v=>v>1))throw Error('Invalid regional residuals');
 const coarse=visible.some((on,i)=>on&&base[i]&&values[i]>0);
 for(const cell of cells){cell.residualMax=0;cell.unknownSamples=0;}
 for(let i=0;i<values.length;i++)if(visible[i]){const cell=cells[addresses[i]];if(Number.isNaN(values[i]))cell.unknownSamples++;else if(!coarse||base[i])cell.residualMax=Math.max(cell.residualMax,values[i]);}
 const occupied=cells.filter(c=>c.visiblePhotoSamples>0),meanPixels=occupied.reduce((s,c)=>s+c.visiblePhotoSamples,0)/Math.max(1,occupied.length),meanDeficit=occupied.reduce((s,c)=>s+c.residualMax,0)/Math.max(1,occupied.length);
 for(const cell of occupied){const area=meanPixels/cell.visiblePhotoSamples;if(meanDeficit>0&&!cell.unknownSamples)cell.factor=Math.max(.5,Math.min(4,area*cell.residualMax/meanDeficit));else cell.factor=Math.max(.5,Math.min(2,area));}
 return coarse?'bounded_coarse_residual_cells_v1':'bounded_source_residual_cells_v1';
}
