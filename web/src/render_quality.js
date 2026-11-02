// This is a bounded estimate for drawing-buffer cost, not total physical VRAM.
// Keep the established standard device ratio; high quality only adds raster samples.
export const RENDER_QUALITY_BUFFER_BUDGET=128*1048576;
export function planRenderQuality({mode='standard',width,height,devicePixelRatio=1,maxRenderbufferSize,samples=0,budgetBytes=RENDER_QUALITY_BUFFER_BUDGET}){
 if(!['standard','high'].includes(mode)||![width,height,maxRenderbufferSize,budgetBytes].every(v=>Number.isSafeInteger(v)&&v>0)||!Number.isFinite(devicePixelRatio)||devicePixelRatio<=0||devicePixelRatio>16||!Number.isSafeInteger(samples)||samples<0||samples>64)throw Error('Invalid render quality limits');
 const standard=Math.min(devicePixelRatio,1.5),bytesPerPixel=8*Math.max(1,samples)+12;
 const estimate=ratio=>{const drawWidth=Math.max(1,Math.floor(width*ratio)),drawHeight=Math.max(1,Math.floor(height*ratio));return {drawWidth,drawHeight,estimatedFramebufferBytes:drawWidth*drawHeight*bytesPerPixel};};
 const cap=Math.min(2,maxRenderbufferSize/width,maxRenderbufferSize/height,Math.sqrt(budgetBytes/(width*height*bytesPerPixel)));
 // Round downward before applying the estimate, avoiding device-limit overflow.
 const high=Math.max(standard,Math.floor(cap*1000)/1000),available=high>standard+1e-6;
 const ratio=mode==='high'&&available?high:standard,result=estimate(ratio);
 if(mode==='high'&&available&&(result.drawWidth>maxRenderbufferSize||result.drawHeight>maxRenderbufferSize||result.estimatedFramebufferBytes>budgetBytes))throw Error('High quality exceeds estimated drawing-buffer limits');
 return {schema:'xnby.render_quality.v1',mode,ratio,standardRatio:standard,highAvailable:available,limited:mode==='high'&&ratio<2,width,height,...result,samples,bytesPerPixel,budgetBytes,scope:'drawing_buffer_estimate_only; unchanged_source_geometry_textures_and_LOD; not_total_VRAM'};
}

// Avoid setPixelRatio's implicit allocation at the old logical window size.
// Shrink axes before growing either, bounding intermediate canvas area by the
// larger of the previous and final drawing buffers (driver allocation is opaque).
export function applyRenderQualityPlan(renderer,plan){
 const canvas=renderer.domElement;
 if(canvas.width>plan.drawWidth)canvas.width=plan.drawWidth;
 if(canvas.height>plan.drawHeight)canvas.height=plan.drawHeight;
 renderer.setDrawingBufferSize(plan.width,plan.height,plan.ratio);
 canvas.style.width=plan.width+'px';canvas.style.height=plan.height+'px';
}
