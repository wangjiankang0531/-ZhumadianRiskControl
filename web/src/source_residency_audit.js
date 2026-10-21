import {webSourceGeometryBytes} from './source_geometry_layout.js';
// Metadata-only QA. No render, download, release, planner or frontier mutation.
// A zero low-resolution sample count is not proof that a page is invisible.
export function captureSourceResidency({residents,samples,width,height,obscured=[],ledger=null}) {
 if(!(residents instanceof Map)||!(samples instanceof Map)||!Number.isInteger(width)||width<1||!Number.isInteger(height)||height<1)throw Error('Invalid source residency audit');
 const counts=new Map();for(const [key,values] of samples){if(values.length%4)throw Error('Invalid residency samples');let exposed=0;for(let i=0;i<values.length;i+=4){const x=(values[i]+1)*width/2,y=(1-values[i+1])*height/2;if(!obscured.some(r=>x>=r.left&&x<r.right&&y>=r.top&&y<r.bottom))exposed++;}counts.set(key,{all:values.length/4,exposed});}
 const pages=[],duplicates=new Map(),totals={pages:0,geometryBytes:0,textureBytes:0,gpuBytes:0,indices:0,drawnCutIndices:0,noSamplePages:0,noSampleBytes:0,noExposedSamplePages:0,noExposedSampleBytes:0,cutLeaves:0,terminalLeaves:0,refinableLeaves:0};
 for(const [root,ready] of residents){const f=ready.frontier;if(!f)throw Error('Missing source frontier in residency audit');
  for(const bundle of f.bundles.values()){
   const byPart=new Map();for(const node of bundle.marker.source_nodes)if(f.visible.has(node.name)){
    totals.cutLeaves++;if(node.children.length)totals.refinableLeaves++;else totals.terminalLeaves++;
    const count=counts.get('node/'+root+'/'+node.name)??{all:0,exposed:0};for(const span of node.spans){if(!byPart.has(span.part))byPart.set(span.part,{indices:0,nodes:new Map()});const entry=byPart.get(span.part);entry.indices+=span.count;entry.nodes.set(node.name,{...count,depth:node.depth,refinable:!!node.children.length});}
   }
   for(const part of bundle.marker.parts){const mesh=bundle.meshes.get(part.directory);if(!mesh||mesh.userData?.sourceGpuResident===false)continue;
    if(pages.length>=8192)throw Error('Residency audit exceeds bounded page count');
    const geometryBytes=webSourceGeometryBytes(part),textureBytes=part.gpu_payload_bytes-geometryBytes;if(!Number.isSafeInteger(textureBytes)||textureBytes<0)throw Error('Invalid residency page accounting');
    const active=byPart.get(part.directory),nodes=[...(active?.nodes??new Map()).entries()],all=nodes.reduce((s,[,n])=>s+n.all,0),exposed=nodes.reduce((s,[,n])=>s+n.exposed,0),image=part.source_image;
    const file=part.files?.find(f=>f.name===(image?'texture.png':'atlas.jpg')),identity=file?.sha256?JSON.stringify([file.sha256,part.runtime_texture??null,image??part.atlas_extent??part.atlas_size]):null;
    const row={root,bundleParent:bundle.marker.replacement_parent??null,part:part.directory,gpuBytes:part.gpu_payload_bytes,geometryBytes,textureBytes,indices:part.indices,drawnCutIndices:active?.indices??0,cutNodes:nodes.map(([name,n])=>({name,...n})),sampleCount:all,exposedSampleCount:exposed,width:image?.width??part.atlas_extent?.[0]??part.atlas_size??null,height:image?.height??part.atlas_extent?.[1]??part.atlas_size??null,textureSHA256:file?.sha256??null,format:part.runtime_texture?.format??'unreported'};
    if(row.drawnCutIndices>row.indices)throw Error('Residency mask exceeds source page');pages.push(row);totals.pages++;totals.geometryBytes+=geometryBytes;totals.textureBytes+=textureBytes;totals.gpuBytes+=part.gpu_payload_bytes;totals.indices+=part.indices;totals.drawnCutIndices+=row.drawnCutIndices;
    if(!all){totals.noSamplePages++;totals.noSampleBytes+=row.gpuBytes;}if(!exposed){totals.noExposedSamplePages++;totals.noExposedSampleBytes+=row.gpuBytes;}
    if(identity){if(!duplicates.has(identity))duplicates.set(identity,[]);duplicates.get(identity).push(pages.length-1);}
   }
  }
 }
 const duplicateGroups=[...duplicates.values()].filter(v=>v.length>1);return {scope:'live_GPU_page_metadata_and_low_resolution_ID_samples_not_full_pixel_visibility; excludes_static_scene_and_staging',totals,pages,duplicateGroups,duplicateTextureUpperBoundBytes:duplicateGroups.reduce((s,g)=>s+g.slice(1).reduce((n,i)=>n+pages[i].textureBytes,0),0),ledgerHeldBytes:ledger?.held??null,unattributedLedgerBytes:ledger?ledger.held-totals.gpuBytes:null};
}
