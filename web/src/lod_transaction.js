export class SourceLoadCancelled extends Error {
  constructor(){super('航拍加载需求已变化');this.name='SourceLoadCancelled';}
}
export function ensureSourceWanted(stillWanted){if(!stillWanted())throw new SourceLoadCancelled();}

// The caller owns the staging group and lease until commit/finally cleanup.
// A late part remains ours until attached; cancellation never changes the live cut.
export async function stageSourceParts({marker,downloads,urlForPart,group,prepare,upload,stillWanted,dispose,onReady,yieldFrame}){
  const parts=marker.parts;
  if(!Array.isArray(parts)||!parts.length||parts.length>64||new Set(parts.map(p=>p.directory)).size!==parts.length||parts.some(p=>!/^part_\d{3}$/.test(p.directory)||!Number.isSafeInteger(p.gpu_payload_bytes)||p.gpu_payload_bytes<=0||p.gpu_payload_bytes>32*1048576)||parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)!==marker.gpu_payload_bytes)throw Error('航拍分批资源账目无效');
  for(let i=0;i<parts.length;i++){
    ensureSourceWanted(stillWanted);
    const model=await downloads.load(urlForPart(parts[i]));let owned=true;
    try{
      ensureSourceWanted(stillWanted);prepare(model);
      ensureSourceWanted(stillWanted);await upload?.(model,i);
      ensureSourceWanted(stillWanted);group.add(model.scene);owned=false;onReady?.(i);
      await yieldFrame();
    }finally{if(owned)dispose(model.scene);}
  }
  ensureSourceWanted(stillWanted);
}
