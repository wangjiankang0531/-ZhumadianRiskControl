// Bound the spare capacity by complete retained bundle metadata, including
// hidden parent pages. This is not upload permission or a higher budget.
export function observedSourceRecoveryHeadroom({residents,incomingCost=0}){
 if(!(residents instanceof Map)||residents.size>2346||!Number.isSafeInteger(incomingCost)||incomingCost<0)throw Error('Invalid observed recovery inputs');
 let largest=incomingCost,bundles=0,parts=0;
 for(const ready of residents.values()){
  const retained=ready?.frontier?.bundles;
  if(!(retained instanceof Map)||retained.size===0)throw Error('Missing complete recovery metadata');
  for(const bundle of retained.values()){
   if(++bundles>16384||!Array.isArray(bundle?.marker?.parts)||bundle.marker.parts.length===0||bundle.marker.parts.length>64)throw Error('Invalid complete recovery bundle');
   let cost=0;const names=new Set();
   for(const part of bundle.marker.parts){
    if(++parts>65536||typeof part.directory!=='string'||!/^part_[0-9]{3}$/.test(part.directory)||names.has(part.directory)||!Number.isSafeInteger(part.gpu_payload_bytes)||part.gpu_payload_bytes<=0||part.gpu_payload_bytes>32*1048576)throw Error('Invalid complete recovery page');
    names.add(part.directory);cost+=part.gpu_payload_bytes;
   }
   if(!Number.isSafeInteger(cost)||bundle.marker.gpu_payload_bytes!==cost)throw Error('Incomplete recovery byte identity');
   largest=Math.max(largest,cost);
  }
 }
 return largest;
}
