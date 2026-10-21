export class SourceLoadCancelled extends Error {
  constructor(){super('航拍加载需求已变化');this.name='SourceLoadCancelled';}
}
export function ensureSourceWanted(stillWanted){if(!stillWanted())throw new SourceLoadCancelled();}

// The caller owns the staging group and lease until commit/finally cleanup.
// A late part remains ours until attached; cancellation never changes the live cut.
export async function stageSourceParts({marker,downloads,urlForPart,group,prepare,upload,stillWanted,dispose,onReady,yieldFrame,loadConcurrency=1}){
  const parts=marker.parts;
  if(!Array.isArray(parts)||!parts.length||parts.length>64||new Set(parts.map(p=>p.directory)).size!==parts.length||parts.some(p=>!/^part_\d{3}$/.test(p.directory)||!Number.isSafeInteger(p.gpu_payload_bytes)||p.gpu_payload_bytes<=0||p.gpu_payload_bytes>32*1048576)||parts.reduce((sum,p)=>sum+p.gpu_payload_bytes,0)!==marker.gpu_payload_bytes)throw Error('航拍分批资源账目无效');
  if(loadConcurrency!==1&&loadConcurrency!==2)throw Error('Source preparation concurrency must be 1 or 2');
  if(loadConcurrency===2)return stageSourceWindow({parts,downloads,urlForPart,group,prepare,upload,stillWanted,dispose,onReady,yieldFrame});
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

// Two CPU preparation slots; GPU upload and group attachment retain source order.
// Every speculative load settles before return, so callers may safely release
// the shared bundle lease after failure. A ready model is either group-owned or
// disposed here, including models that arrive after cancellation.
async function stageSourceWindow({parts,downloads,urlForPart,group,prepare,upload,stillWanted,dispose,onReady,yieldFrame}){
 const entries=[],queue=[];let next=0,closed=false,failure=null;
 const wanted=()=>!closed&&!failure&&stillWanted();
 const check=()=>{if(failure)throw failure;ensureSourceWanted(wanted);};
 const fill=()=>{while(queue.length<2&&next<parts.length){check();const index=next++,entry={index,model:null,transferred:false};entries.push(entry);queue.push(entry);
  // Attach a rejection handler immediately, even if a later page fails first.
  entry.done=Promise.resolve().then(()=>{check();return downloads.load(urlForPart(parts[index]),wanted);}).then(model=>{entry.model=model;},error=>{failure??=error;});
 }};
 let error=null;
 try{
  fill();
  while(queue.length){const entry=queue[0];await entry.done;check();const model=entry.model;
   prepare(model);check();await upload?.(model,entry.index);check();
   group.add(model.scene);entry.transferred=true;onReady?.(entry.index);
   queue.shift();fill();await yieldFrame();
  }
  check();
 }catch(cause){error=cause;}
 closed=true;
 await Promise.all(entries.map(entry=>entry.done));
 for(const entry of entries)if(entry.model&&!entry.transferred){try{dispose(entry.model.scene);}catch(cause){error??=cause;}}
 if(error)throw error;
}
