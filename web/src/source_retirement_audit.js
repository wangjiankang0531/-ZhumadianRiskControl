import {sourceRestorationFootprint} from './source_page_budget.js';
// Read-only, bounded evidence for why an existing complete parent cannot be
// restored. No result from this observer authorizes a retirement or an upload.
export function auditSourceRetirement({residents,limit,priority,maxGain=0}){
 if(!(residents instanceof Map)||!Number.isSafeInteger(limit)||limit<1||typeof priority!=='function'||!Number.isFinite(maxGain)||maxGain<0)throw Error('Invalid retirement audit');
 const used=[...residents.values()].reduce((s,r)=>s+r.frontier.bytes,0),rows=[],totals={scanned:0,saving:0,eligible:0,eligiblePeakFits:0,zeroLoss:0,zeroLossPeakFits:0};let truncated=false;
 outer:for(const [root,ready] of residents){const f=ready.frontier,nodes=f.nodes;for(const parent of f.bundles.keys())if(parent!=='$root'){
  if(totals.scanned===4096){truncated=true;break outer;}totals.scanned++;
  const plan=f.rollbackPlan(parent),freed=f.bytes-plan.bytes;if(freed<=0)continue;totals.saving++;
  const loss=priority(root,nodes.get(parent).node,plan.subtree),peak=used+sourceRestorationFootprint(new Map([[root,ready]]),[{root,parent}])-f.bytes,eligible=Number.isFinite(loss)&&loss>=0&&loss*2<maxGain;
  if(loss===0){totals.zeroLoss++;if(peak<=limit)totals.zeroLossPeakFits++;}if(eligible){totals.eligible++;if(peak<=limit)totals.eligiblePeakFits++;}
  rows.push({root,parent,freed,loss:Number.isFinite(loss)?loss:null,restoreBytes:peak-used,peak,peakFits:peak<=limit,eligible});
 }}
 rows.sort((a,b)=>(a.loss??Infinity)-(b.loss??Infinity)||a.restoreBytes-b.restoreBytes||b.freed-a.freed||a.root-b.root);
 return {scope:'bounded_current_cut_metadata_only_not_admission_permission',limit,used,headroom:limit-used,maxGain,...totals,truncated:truncated||rows.length>64,rows:rows.slice(0,64)};
}
