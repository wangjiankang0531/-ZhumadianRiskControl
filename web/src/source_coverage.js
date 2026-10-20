import {WebGLRenderTarget,MeshBasicMaterial,DoubleSide,NoBlending,Color,NearestFilter} from 'three';
import {ensureSourceWanted} from './lod_transaction.js';

export function coverageDimensions(width,height){if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>4096||height>2160)throw Error('Source coverage viewport exceeds bound');return {width,height,bytes:width*height*8};}
// Same independent 2-pixel interior criterion as the native guard. Screen edges
// use clipped neighborhoods, so a large corner hole is not an ignored border.
export function coverageInteriorLoss(parent,child,width,height){
 coverageDimensions(width,height);if(!(parent instanceof Uint8Array)||!(child instanceof Uint8Array)||parent.length!==width*height*4||child.length!==parent.length)throw Error('Invalid geometric coverage masks');
 const stride=width+1,p=new Uint32Array(stride*(height+1)),c=new Uint32Array(p.length);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const at=(y+1)*stride+x+1,pixel=(y*width+x)*4;p[at]=(parent[pixel]!==0)+p[at-1]+p[at-stride]-p[at-stride-1];c[at]=(child[pixel]!==0)+c[at-1]+c[at-stride]-c[at-stride-1];}
 const sum=(a,x0,y0,x1,y1)=>a[y1*stride+x1]-a[y0*stride+x1]-a[y1*stride+x0]+a[y0*stride+x0];let loss=0,parentPixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){parentPixels+=parent[(y*width+x)*4]!==0;const x0=Math.max(0,x-2),y0=Math.max(0,y-2),x1=Math.min(width,x+3),y1=Math.min(height,y+3);if(sum(p,x0,y0,x1,y1)===(x1-x0)*(y1-y0)&&sum(c,x0,y0,x1,y1)===0)loss++;}
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
 constructor({renderer,scene,photoGroup,contextGroup,reserve}){Object.assign(this,{renderer,scene,photoGroup,contextGroup,reserve});this.target=null;this.reservation=null;this.width=0;this.height=0;this.bytes=0;this.black=new MeshBasicMaterial({color:0,side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false});this.white=new MeshBasicMaterial({color:0xffffff,side:DoubleSide,toneMapped:false,blending:NoBlending,fog:false});}
 resize(width,height){const d=coverageDimensions(width,height);if(this.target&&this.width===width&&this.height===height)return;this.release();const reservation=this.reserve({format:'coverage_target',bytes:d.bytes});try{this.target=new WebGLRenderTarget(width,height,{minFilter:NearestFilter,magFilter:NearestFilter,depthBuffer:true,stencilBuffer:false,generateMipmaps:false});this.reservation=reservation;this.width=width;this.height=height;this.bytes=d.bytes;}catch(error){reservation.release();throw error;}}
 release(){this.target?.dispose();this.target=null;this.reservation?.release();this.reservation=null;this.width=0;this.height=0;this.bytes=0;}
 dispose(){this.release();this.black.dispose();this.white.dispose();}
 check({camera,candidate,parentSpans,stillWanted=()=>true}){
  if(!this.target||candidate.parent)throw Error('Source coverage staging identity differs');ensureSourceWanted(stillWanted);
  const renderer=this.renderer,scene=this.scene,saved=[],priorContext=this.contextGroup.visible,background=scene.background,priorTarget=renderer.getRenderTarget(),color=renderer.getClearColor(new Color()).clone(),alpha=renderer.getClearAlpha(),autoClear=renderer.autoClear;
  const save=mesh=>{if(!mesh.isMesh)return;const groups=coverageGroups(mesh.geometry.groups,parentSpans.get(mesh)??[],mesh.geometry.index.count,{singleMaterial:!Array.isArray(mesh.material)});saved.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible,split:groups});mesh.geometry.groups=groups;mesh.material=[this.black,this.white];};
  const before=new Uint8Array(this.width*this.height*4),after=new Uint8Array(before.length);
  let added=false;try{
   this.photoGroup.traverse(save);this.contextGroup.visible=false;scene.background=null;renderer.autoClear=true;renderer.setRenderTarget(this.target);renderer.setClearColor(0,0);renderer.clear();renderer.render(scene,camera);renderer.readRenderTargetPixels(this.target,0,0,this.width,this.height,before);
   for(const state of saved){state.mesh.geometry.groups=state.split.filter(g=>g.materialIndex===0).map(g=>({...g,materialIndex:0}));state.mesh.material=[this.white];state.mesh.visible=state.visible&&state.mesh.geometry.groups.length>0;}
   candidate.traverse(mesh=>{if(!mesh.isMesh)return;saved.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible,candidate:true});const groups=coverageGroups(mesh.geometry.groups,[],mesh.geometry.index.count,{singleMaterial:!Array.isArray(mesh.material)});mesh.geometry.groups=groups.map(g=>({...g,materialIndex:0}));mesh.material=[this.white];});
   this.photoGroup.add(candidate);added=true;renderer.clear();renderer.render(scene,camera);renderer.readRenderTargetPixels(this.target,0,0,this.width,this.height,after);ensureSourceWanted(stillWanted);
   return {...coverageInteriorLoss(before,after,this.width,this.height),width:this.width,height:this.height,targetBytes:this.bytes,tolerance:2,scope:'visible_parent_vs_complete_original_landscape_no_context'};
  }finally{
   if(added)this.photoGroup.remove(candidate);for(const s of saved){s.mesh.material=s.material;s.mesh.geometry.groups=s.groups;s.mesh.visible=s.visible;}this.contextGroup.visible=priorContext;scene.background=background;renderer.setRenderTarget(priorTarget);renderer.setClearColor(color,alpha);renderer.autoClear=autoClear;
  }
 }
}
