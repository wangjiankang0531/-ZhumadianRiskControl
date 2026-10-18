// One ledger for live, staged, restoring pages and the offscreen upload target.
export class SourcePageBudget{
 constructor(limit){if(!Number.isSafeInteger(limit)||limit<=0)throw Error('Invalid source page budget');this.limit=limit;this.held=0;this.peak=0;this.admissions=0;this.releases=0;this.formats=new Map();}
 reserve({format,bytes}){
  if(typeof format!=='string'||!Number.isSafeInteger(bytes)||bytes<=0||this.held+bytes>this.limit)throw Error('Concurrent source page budget exceeded');
  this.held+=bytes;this.peak=Math.max(this.peak,this.held);this.admissions++;this.formats.set(format,(this.formats.get(format)||0)+bytes);let live=true;
  return {release:()=>{if(!live)return;live=false;this.held-=bytes;this.releases++;this.formats.set(format,this.formats.get(format)-bytes);}};
 }
 snapshot(){return {limit:this.limit,held:this.held,peak:this.peak,admissions:this.admissions,releases:this.releases,formats:Object.fromEntries(this.formats)};}
}

// Parent recovery precedes the atomic cut switch. Every current page is still
// alive during that upload, including roots scheduled for removal at commit.
export function sourceRestorationFootprint(residents,actions){
 let bytes=[...residents.values()].reduce((sum,ready)=>sum+ready.frontier.bytes,0);const missing=new Map();
 for(const action of actions)if(action.parent!==null){
  const ready=residents.get(action.root),plan=ready?.frontier.rollbackPlan(action.parent);if(!plan)throw Error('Unknown source restoration action');
  for(const {bundle,part} of plan.missingPages){if(!missing.has(bundle))missing.set(bundle,new Map());missing.get(bundle).set(part.directory,part.gpu_payload_bytes);}
 }
 for(const parts of missing.values())for(const value of parts.values())bytes+=value;
 return bytes;
}
