// Verify every mip before requesting compressed bytes or reserving GPU memory.
export const PREPARED_BC7_QUALITY_POLICY='xnby.bc7.opaque_quality_psnr40_p99_16_max96.v1';
export function validatePreparedBc7Quality(manifest){
 const require=(ok,message)=>{if(!ok)throw Error('Prepared BC7 quality: '+message);};
 require(manifest?.accepted===true,'complete chain was not accepted');
 const limits=manifest.qualityThresholds;require(limits&&typeof limits==='object','missing declared thresholds');
 const {rgbPSNRMin:psnr,rgbChannelP99Max:p99,rgbMaxErrorMax:maximum}=limits;
 require(Number.isFinite(psnr)&&psnr>=40&&psnr<=999&&Number.isFinite(p99)&&p99>=0&&p99<=16&&Number.isFinite(maximum)&&maximum>=0&&maximum<=96,'missing, nonfinite or relaxed thresholds');
 require(Array.isArray(manifest.mips)&&manifest.mips.length>0&&manifest.mips.length<=12,'missing mip evidence');
 for(const row of manifest.mips){
  require(row?.accepted===true,'a mip was not accepted');const q=row.quality;require(q&&typeof q==='object','missing mip quality');
  require(Number.isFinite(q.rgbPSNR)&&q.rgbPSNR>=psnr&&q.rgbPSNR<=999&&Number.isInteger(q.rgbChannelP99)&&q.rgbChannelP99>=0&&q.rgbChannelP99<=p99&&Number.isInteger(q.rgbMaxError)&&q.rgbMaxError>=q.rgbChannelP99&&q.rgbMaxError<=maximum,'mip failed declared quality thresholds');
 }
 return true;
}
