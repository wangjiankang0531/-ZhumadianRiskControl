import {Color,Vector4} from 'three';
import {SourceVisibility} from './source_visibility.js';
import {collectCompletionPixels,COMPLETION_SAMPLE_LIMIT} from './source_completion_samples.js';
// One idle, full-view observation. It never changes the source cut, stages
// source pages or grants admission; all temporary GPU storage is ledger-owned.
export function captureSourceCompletion({renderer,scene,context,base,catalog,residents,camera,baseQuality,obscured=[],cssWidth,cssHeight,ledger,primary,roots,visibilityFactory=(...args)=>new SourceVisibility(...args)}){
 const width=renderer.domElement.width,height=renderer.domElement.height,pixels=width*height,bytes=pixels*8;
 if(![width,height].every(n=>Number.isSafeInteger(n)&&n>0)||width>4096||height>2160||pixels>2097152)return {status:'refused',reason:'viewport_bound'};
 if(renderer.getRenderTarget()||renderer.getScissorTest())return {status:'refused',reason:'non_default_target'};
 const viewport=Array.from(renderer.getContext().getParameter(renderer.getContext().VIEWPORT));if(viewport.some((v,i)=>v!==[0,0,width,height][i]))return {status:'refused',reason:'non_full_viewport'};
 if(!primary?.samples||primary.surfaceDepths)return {status:'refused',reason:'unsupported_primary_snapshot'};
 const count=[...primary.samples.values()].reduce((s,rows)=>s+rows.length/4,0);if(count>COMPLETION_SAMPLE_LIMIT)throw Error('Primary snapshot already exceeds worker bound');
 if(ledger.held+bytes>ledger.limit)return {status:'refused',reason:'source_budget_headroom',bytes};
 const old={target:renderer.getRenderTarget(),viewport:renderer.getViewport(new Vector4()).clone(),scissor:renderer.getScissor(new Vector4()).clone(),scissorTest:renderer.getScissorTest(),color:renderer.getClearColor(new Color()).clone(),alpha:renderer.getClearAlpha(),autoClear:renderer.autoClear,background:scene.background,info:{...renderer.info.render}},meshes=[];
 scene.traverse(mesh=>{if(mesh.isMesh)meshes.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible});});
 const projection=[...camera.projectionMatrix.elements],world=[...camera.matrixWorld.elements],held=ledger.held,start=performance.now();let lease=null,probe=null;
 try{
  lease=ledger.reserve({format:'source_completion_rgba8_depth',bytes});probe=visibilityFactory(renderer,scene,context);
  const result=probe.sample({camera,width:cssWidth,height:cssHeight,base,catalog,residents,baseQuality,raster:{width,height},readback:raw=>collectCompletionPixels({...raw,width,height,cssWidth,cssHeight,roots,obscured,remaining:COMPLETION_SAMPLE_LIMIT-count})});
  if(!projection.every((v,i)=>v===camera.projectionMatrix.elements[i])||!world.every((v,i)=>v===camera.matrixWorld.elements[i]))throw Error('Completion observation changed camera');
  return {...result,width,height,bytes,heldBefore:held,milliseconds:performance.now()-start};
 }finally{
  try{for(const {mesh,material,groups,visible} of meshes){mesh.material=material;mesh.geometry.groups=groups;mesh.visible=visible;}scene.background=old.background;renderer.autoClear=old.autoClear;renderer.setRenderTarget(old.target);renderer.setViewport(old.viewport);renderer.setScissor(old.scissor);renderer.setScissorTest(old.scissorTest);renderer.setClearColor(old.color,old.alpha);Object.assign(renderer.info.render,old.info);}
  finally{try{probe?.dispose();}finally{lease?.release();}}
 }
}
