import {coverageRegion} from './source_coverage_region.js';
import {WebGLRenderTarget,MeshBasicMaterial,DoubleSide,NoBlending,Color,NearestFilter} from 'three';
import {ensureSourceWanted} from './lod_transaction.js';

export function coverageDimensions(width,height){if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>4096||height>2160)throw Error('Source coverage viewport exceeds bound');return {width,height,bytes:width*height*8};}
// Same independent 2-pixel interior criterion as the native guard. Screen edges
// use clipped neighborhoods, so a large corner hole is not an ignored border.
// A lost pixel has no violation in its clipped 5x5 neighborhood, where a
// violation is absent parent coverage OR present replacement coverage.
// Separable dilation needs five row flags and two width-sized byte buffers.
export function coverageInteriorLoss(parent,child,width,height){
 coverageDimensions(width,height);if(!(parent instanceof Uint8Array)||!(child instanceof Uint8Array)||parent.length!==width*height*4||child.length!==parent.length)throw Error('Invalid geometric coverage masks');
 const rows=new Uint8Array(width*5),bad=new Uint8Array(width),columns=new Uint8Array(width);let firstRow=0,nextRow=0,loss=0,parentPixels=0;
 for(let y=0;y<height;y++){
  const first=Math.max(0,y-2),last=Math.min(height-1,y+2);
  while(firstRow<first){const offset=(firstRow%5)*width;for(let x=0;x<width;x++)columns[x]-=rows[offset+x];firstRow++;}
  while(nextRow<=last){const offset=(nextRow%5)*width,source=nextRow*width*4;
   for(let x=0;x<width;x++){const pixel=source+x*4,present=parent[pixel]!==0;parentPixels+=present;bad[x]=!present||child[pixel]!==0?1:0;}
   let count=0;for(let x=0;x<Math.min(width,3);x++)count+=bad[x];
   for(let x=0;x<width;x++){const bit=count>0?1:0;rows[offset+x]=bit;columns[x]+=bit;if(x>=2)count-=bad[x-2];if(x+3<width)count+=bad[x+3];}
   nextRow++;
  }
  for(let x=0;x<width;x++)if(columns[x]===0)loss++;
 }
 return {loss,parentPixels};
}

// Partition current live spans exactly. Material 1 is the replacement parent;
// material 0 is every other original landscape surface (depth occluders).
export function coverageGroups(groups,targets,indexCount,{singleMaterial=false}={}){
 const active=singleMaterial?[{start:0,count:indexCount}]:groups;
 if(!Number.isSafeInteger(indexCount)||indexCount<0||indexCount%3)throw Error('Invalid coverage geometry');
 for(const s of targets)if(!Number.isInteger(s.first)||!Number.isInteger(s.count)||s.first<0||s.count<0||s.first%3||s.count%3||s.first+s.count>indexCount)throw Error('Invalid coverage parent span');
 const out=[];for(const g of active){if(g.start<0||g.count<0||g.start%3||g.count%3||g.start+g.count>indexCount)throw Error('Invalid live coverage span');const end=g.start+g.count,points=new Set([g.start,end]);for(const s of targets){if(s.first>g.start&&s.first<end)points.add(s.first);if(s.first+s.count>g.start&&s.first+s.count<end)points.add(s.first+s.count);}const sorted=[...points].sort((a,b)=>a-b);for(let i=1;i<sorted.length;i++){const start=sorted[i-1],count=sorted[i]-start;if(count)out.push({start,count,materialIndex:targets.some(s=>start>=s.first&&start<s.first+s.count)?1:0});}}
 return out;
}

export class SourceCoverageGuard{
 constructor({renderer,scene,photoGroup,contextGroup,reserve,reference=false,measure=(name,fn)=>fn()}){Object.assign(this,{renderer,scene,photoGroup,contextGroup,reserve,reference,measure});this.referenceChecks=0;this.referenceMismatches=0;this.target=null;this.reservation=null;this.width=0;this.height=0;this.bytes=0;this.black=new MeshBasicMaterial({color:0,side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false});this.white=new MeshBasicMaterial({color:0xffffff,side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false});}
 resize(width,height){const d=coverageDimensions(width,height);if(this.target&&this.width===width&&this.height===height)return;this.release();const reservation=this.reserve({format:'coverage_target',bytes:d.bytes});try{this.target=new WebGLRenderTarget(width,height,{minFilter:NearestFilter,magFilter:NearestFilter,depthBuffer:true,stencilBuffer:false,generateMipmaps:false});this.reservation=reservation;this.width=width;this.height=height;this.bytes=d.bytes;}catch(error){reservation.release();throw error;}}
 release(){this.target?.dispose();this.target=null;this.reservation?.release();this.reservation=null;this.width=0;this.height=0;this.bytes=0;}
 dispose(){this.release();this.black.dispose();this.white.dispose();}
 check(args){
  const {camera,candidate,parentSpans,stillWanted=()=>true}=args;if(!this.target||candidate.parent)throw Error('Source coverage staging identity differs');ensureSourceWanted(stillWanted);
  this.scene.updateMatrixWorld(true);const region=coverageRegion({camera,parentSpans,width:this.width,height:this.height}),result=this.checkRegion(args,region);
  if(this.reference){const reference=this.checkRegion(args,{x:0,y:0,width:this.width,height:this.height,pixels:this.width*this.height,fullPixels:this.width*this.height,reason:'full_viewport_reference'});this.referenceChecks++;if(reference.loss!==result.loss||reference.parentPixels!==result.parentPixels){this.referenceMismatches++;throw Error('Regional source coverage differs from full viewport');}result.fullReference={loss:reference.loss,parentPixels:reference.parentPixels};}
  return result;
 }
 checkRegion({camera,candidate,parentSpans,stillWanted=()=>true},region){
  if(!this.target||candidate.parent)throw Error('Source coverage staging identity differs');ensureSourceWanted(stillWanted);
  const renderer=this.renderer,scene=this.scene,saved=[],priorContext=this.contextGroup.visible,background=scene.background,priorTarget=renderer.getRenderTarget(),color=renderer.getClearColor(new Color()).clone(),alpha=renderer.getClearAlpha(),autoClear=renderer.autoClear;
  const save=mesh=>{if(!mesh.isMesh)return;const groups=coverageGroups(mesh.geometry.groups,parentSpans.get(mesh)??[],mesh.geometry.index.count,{singleMaterial:!Array.isArray(mesh.material)});saved.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible,split:groups});mesh.geometry.groups=groups;mesh.material=[this.black,this.white];};
  const before=new Uint8Array(region.pixels*4),after=new Uint8Array(before.length),scissor=this.target.scissor.clone(),scissorTest=this.target.scissorTest;
  let added=false;try{
   this.target.scissor.set(region.x,region.y,region.width,region.height);this.target.scissorTest=true;this.photoGroup.traverse(save);this.contextGroup.visible=false;scene.background=null;renderer.autoClear=true;renderer.setRenderTarget(this.target);renderer.setClearColor(0,0);renderer.clear();this.measure('coverage_draw',()=>renderer.render(scene,camera));this.measure('coverage_readback',()=>renderer.readRenderTargetPixels(this.target,region.x,region.y,region.width,region.height,before));
   for(const state of saved){state.mesh.geometry.groups=state.split.filter(g=>g.materialIndex===0).map(g=>({...g,materialIndex:0}));state.mesh.material=[this.white];state.mesh.visible=state.visible&&state.mesh.geometry.groups.length>0;}
   candidate.traverse(mesh=>{if(!mesh.isMesh)return;saved.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible,candidate:true});const groups=coverageGroups(mesh.geometry.groups,[],mesh.geometry.index.count,{singleMaterial:!Array.isArray(mesh.material)});mesh.geometry.groups=groups.map(g=>({...g,materialIndex:0}));mesh.material=[this.white];});
   this.photoGroup.add(candidate);added=true;renderer.clear();this.measure('coverage_draw',()=>renderer.render(scene,camera));this.measure('coverage_readback',()=>renderer.readRenderTargetPixels(this.target,region.x,region.y,region.width,region.height,after));ensureSourceWanted(stillWanted);
   return {...this.measure('coverage_compute',()=>coverageInteriorLoss(before,after,region.width,region.height)),region,readbackBytes:before.length+after.length,width:this.width,height:this.height,targetBytes:this.bytes,tolerance:2,scope:'visible_parent_vs_complete_original_landscape_no_context'};
  }finally{
   if(added)this.photoGroup.remove(candidate);for(const s of saved){s.mesh.material=s.material;s.mesh.geometry.groups=s.groups;s.mesh.visible=s.visible;}this.target.scissor.copy(scissor);this.target.scissorTest=scissorTest;this.contextGroup.visible=priorContext;scene.background=background;renderer.setRenderTarget(priorTarget);renderer.setClearColor(color,alpha);renderer.autoClear=autoClear;
  }
 }
}
