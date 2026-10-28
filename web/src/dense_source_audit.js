import {Color,Vector4} from 'three';
import {SourceVisibility} from './source_visibility.js';
import {denseAuditLayout,denseTileViewport,denseCellIndex,projectedSourceQuality} from './dense_audit_tiles.js';
import {coverageInteriorLoss} from './source_coverage.js';

// QA observation only. P90 source metadata is a projection proxy, not measured
// geometric error or a texture/readability acceptance test. No cut is committed.
export function auditDenseSource({renderer,scene,context,base,catalog,residents,camera,baseQuality,obscured=[],cssWidth,cssHeight,ledger,reference=false,visibilityFactory=(...args)=>new SourceVisibility(...args)}){
 const width=renderer.domElement.width,height=renderer.domElement.height,layout=denseAuditLayout(width,height);
 if(renderer.getRenderTarget()||renderer.getScissorTest())throw Error('Dense audit requires an unscissored default target');
 if(!(cssWidth>0&&cssHeight>0)||camera.near<.5||camera.far>60000)throw Error('Unsupported dense audit view');
 const gl=renderer.getContext(),viewport=Array.from(gl.getParameter(gl.VIEWPORT));
 const old={target:renderer.getRenderTarget(),viewport:renderer.getViewport(new Vector4()).clone(),scissor:renderer.getScissor(new Vector4()).clone(),scissorTest:renderer.getScissorTest(),color:renderer.getClearColor(new Color()).clone(),alpha:renderer.getClearAlpha(),autoClear:renderer.autoClear,background:scene.background,info:{...renderer.info.render}};
 const meshes=[];scene.traverse(mesh=>{if(mesh.isMesh)meshes.push({mesh,material:mesh.material,groups:mesh.geometry.groups,visible:mesh.visible});});
 const groups=[...residents.values()].map(ready=>[ready.group,ready.group.visible]);
 const projection=[...camera.projectionMatrix.elements],world=[...camera.matrixWorld.elements],held=ledger.held;
 let lease=null,probe=null,oracleLease=null;
 const labels=new Uint32Array(layout.pixels),coarse=new Uint8Array(layout.pixels),registry=new Map(),keys=[''];
 const labelFor=key=>{if(!registry.has(key)){registry.set(key,keys.length);keys.push(key);}return registry.get(key);};
 const blank=()=>({pixels:0,photo:0,base:0,detail:0,unknown:0,over:0,geometryOver:0,texelOver:0,maxGeometry:0,maxTexel:0});
 const full=Array.from({length:9},blank),exposed=Array.from({length:9},blank),roots=new Map();
 const hidden=(x,y)=>obscured.some(r=>(x+.5)*cssWidth/width>=r.left&&(x+.5)*cssWidth/width<r.right&&(y+.5)*cssHeight/height>=r.top&&(y+.5)*cssHeight/height<r.bottom);
 const scale=Math.max(Math.abs(projection[0])*viewport[2],Math.abs(projection[5])*viewport[3])/2;
 const add=(cell,key,q)=>{cell.pixels++;if(!key)return;cell.photo++;cell[key.startsWith('root/')?'base':'detail']++;if(q.unknown)cell.unknown++;if(q.over)cell.over++;if(q.geometry>6)cell.geometryOver++;if(q.texel>1.5)cell.texelOver++;cell.maxGeometry=Math.max(cell.maxGeometry,q.geometry??0);cell.maxTexel=Math.max(cell.maxTexel,q.texel??0);};
 const start=performance.now();
 const restoreGroups=()=>{for(const [group,visible] of groups)group.visible=visible;};
 const sample=(tile,current,readback)=>probe.sample({camera,width:cssWidth,height:cssHeight,base,catalog,residents:current?residents:new Map(),baseQuality,raster:{width:tile.width,height:tile.height},viewport:denseTileViewport(tile,height,viewport),readback});
 const observe=({pixels,depthPixels,registry:ids,metrics},tile,output,cells,visibleCells,rootCounts)=>{
  for(let row=0;row<tile.height;row++)for(let col=0;col<tile.width;col++){
   const local=row*tile.width+col,off=local*4,x=tile.x+col,y=tile.y+tile.height-1-row,index=y*width+x,id=pixels[off]|pixels[off+1]<<8|pixels[off+2]<<16,key=id?ids.get(id):null;
   if(id&&!key)throw Error('Unknown dense source ID');
   let q={geometry:null,texel:null,over:false,unknown:false};
   if(key){if(!depthPixels||depthPixels[off+3]!==255)throw Error('Dense depth missing');const code=depthPixels[off]|depthPixels[off+1]<<8|depthPixels[off+2]<<16;if(Math.abs(code/16777215*255-pixels[off+3])>1.01)throw Error('Dense ID/depth disagreement');q=projectedSourceQuality(metrics.get(key),.5*120000**(code/16777215),scale);output[index]=labelFor(key);const root=key.split('/')[1];if(!rootCounts.has(root))rootCounts.set(root,{root,base:0,detail:0,over:0});const r=rootCounts.get(root);r[key.startsWith('root/')?'base':'detail']++;if(q.over)r.over++;}
   const cell=denseCellIndex(x,y,width,height);add(cells[cell],key,q);if(!hidden(x,y))add(visibleCells[cell],key,q);
  }
 };
 try{
  lease=ledger.reserve({format:'dense_audit_rgba8_depth',bytes:layout.targetBytes});
  probe=visibilityFactory(renderer,scene,context,{preciseDepth:true});
  for(const tile of layout.tiles){
   if(performance.now()-start>30000)throw Error('Dense audit exceeded 30 second work bound');
   sample(tile,true,raster=>observe(raster,tile,labels,full,exposed,roots));
  }
  // Compare against complete coarse photograph at the same camera and viewport.
  // This is relative coverage evidence, not proof that coarse geometry is truth.
  for(const [group] of groups)group.visible=false;
  for(const tile of layout.tiles){
   if(performance.now()-start>30000)throw Error('Dense audit exceeded 30 second work bound');
   sample(tile,false,({pixels})=>{for(let row=0;row<tile.height;row++)for(let col=0;col<tile.width;col++){const off=(row*tile.width+col)*4;coarse[(tile.y+tile.height-1-row)*width+tile.x+col]=pixels[off]||pixels[off+1]||pixels[off+2]?1:0;}});
  }
  restoreGroups();
  const before=new Uint8Array(layout.pixels*4),after=new Uint8Array(before.length);let rawLoss=0,exposedRawLoss=0;
  for(let i=0;i<labels.length;i++){before[i*4]=coarse[i];after[i*4]=labels[i]?1:0;if(coarse[i]&&!labels[i])rawLoss++;}
  const coverage=coverageInteriorLoss(before,after,width,height);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){const i=y*width+x;if(hidden(x,y)){before[i*4]=0;after[i*4]=0;}else if(coarse[i]&&!labels[i])exposedRawLoss++;}
  const exposedCoverage=coverageInteriorLoss(before,after,width,height);
  const oracle={requested:reference,status:'not-requested'};
  if(reference){
   const bytes=layout.pixels*8;
   if(layout.pixels>2097152)Object.assign(oracle,{status:'refused',reason:'independent full target exceeds pixel bound',bytes});
   else if(ledger.held+bytes>ledger.limit)Object.assign(oracle,{status:'refused',reason:'source budget has insufficient headroom',bytes});
   else{
    oracleLease=ledger.reserve({format:'dense_audit_full_reference',bytes});
    // Dispose the small target before replacing it; keep its budget reserved.
    probe.dispose();probe=null;probe=visibilityFactory(renderer,scene,context,{preciseDepth:true});
    let mismatches=0;const examples=[],oracleLabels=new Uint32Array(layout.pixels),oracleFull=Array.from({length:9},blank),oracleExposed=Array.from({length:9},blank),oracleRoots=new Map();
    sample({x:0,y:0,width,height},true,raster=>observe(raster,{x:0,y:0,width,height},oracleLabels,oracleFull,oracleExposed,oracleRoots));
    for(let i=0;i<labels.length;i++)if(oracleLabels[i]!==labels[i]){mismatches++;if(examples.length<8)examples.push({x:i%width,y:Math.floor(i/width),tiled:keys[labels[i]],full:keys[oracleLabels[i]]});}
    Object.assign(oracle,{status:mismatches?'mismatch':'matched',pixels:layout.pixels,mismatches,examples,bytes,full:oracleFull,exposed:oracleExposed,roots:[...oracleRoots.values()].sort((a,b)=>b.over-a.over),scope:'independent full-target source identity and depth; P90 proxy only'});
   }
  }
  if(!projection.every((v,i)=>v===camera.projectionMatrix.elements[i])||!world.every((v,i)=>v===camera.matrixWorld.elements[i]))throw Error('Dense audit changed camera');
  return {schema:'xnby.dense_source_audit.v1',status:'complete',scope:'drawing-buffer pixel-center single-sample source identity and projected P90 metadata; excludes texture content and MSAA appearance',width,height,pixels:layout.pixels,tiles:layout.tiles.length,viewport,scale,thresholds:{geometryP90:6,texelP90:1.5},targetBytes:layout.targetBytes,ledgerBefore:held,full,exposed,roots:[...roots.values()].sort((a,b)=>b.over-a.over),coverage:{scope:'relative to complete coarse photograph; not absolute geometry truth',rawLoss,...coverage,exposed:{rawLoss:exposedRawLoss,...exposedCoverage}},reference:oracle,cameraUnchanged:true,elapsedMs:performance.now()-start};
 }finally{
  try{
   for(const {mesh,material,groups,visible} of meshes){mesh.material=material;mesh.geometry.groups=groups;mesh.visible=visible;}restoreGroups();scene.background=old.background;renderer.autoClear=old.autoClear;renderer.setRenderTarget(old.target);renderer.setViewport(old.viewport);renderer.setScissor(old.scissor);renderer.setScissorTest(old.scissorTest);renderer.setClearColor(old.color,old.alpha);Object.assign(renderer.info.render,old.info);
  }finally{try{probe?.dispose();}finally{oracleLease?.release();lease?.release();}}
 }
}
