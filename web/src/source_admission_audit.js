const encoder=new TextEncoder();
const numeric=['root','upperBound','gain','combinedGain','texelGain','cost','metadataCost','beforeHeld','afterHeld','detailLimit','residentBytesBefore','residentBytesAfter','rootsBefore','rootsAfter','beforeContext','afterContext','durationMs'];
const booleans=['reprobeMeasured','reprobeUpperBound'];
// Observation only. Context IDs prove equality against the immediately retained
// complete feasibility context, including visibility/frontier object identity.
// IDs are not persistent hashes and cannot compare separate page executions.
export class SourceAdmissionAudit {
 constructor({enabled=false,capacity=128,maxContextBytes=1048576}={}){
  if(typeof enabled!=='boolean'||!Number.isInteger(capacity)||capacity<1||capacity>128||!Number.isSafeInteger(maxContextBytes)||maxContextBytes<128||maxContextBytes>1048576)throw Error('Invalid admission audit bound');
  Object.assign(this,{enabled,capacity,maxContextBytes});this.events=[];this.context=null;this.nextContext=0;this.identities=new WeakMap();this.nextIdentity=0;this.total=0;this.overwritten=0;this.oversizedContexts=0;this.counts={accepted:0,rejected:0,cancelled:0,error:0};this.stageCounts=Object.fromEntries(['metadata','memo','upload'].map(stage=>[stage,{accepted:0,rejected:0,cancelled:0,error:0}]));
 }
 identity(value){if(value==null)return 0;if(typeof value!=='object'&&typeof value!=='function')throw Error('Invalid admission context identity');if(!this.identities.has(value))this.identities.set(value,++this.nextIdentity);return this.identities.get(value);}
 contextId(next){
  if(!this.enabled)return null;
  if(!next){this.context=null;return null;}
  if(typeof next.state!=='string'||!Array.isArray(next.frontiers))throw Error('Invalid admission context');
  if(next.frontiers.length>2346||encoder.encode(next.state).length+next.frontiers.length*8+64>this.maxContextBytes){this.oversizedContexts++;this.context=null;return null;}
  const visibilityId=this.identity(next.visibility),frontierIds=next.frontiers.map(f=>this.identity(f));
  if(this.context&&this.context.state===next.state&&this.context.visibilityId===visibilityId&&this.context.frontierIds.length===frontierIds.length&&this.context.frontierIds.every((id,i)=>id===frontierIds[i]))return this.context.id;
  const id=++this.nextContext;this.context={id,state:next.state,visibilityId,frontierIds};return id;
 }
 record(value){
  if(!this.enabled)return;
  if(!Object.hasOwn(this.counts,value?.status)||typeof value.key!=='string'||!value.key||value.key.length>512||!['root','family'].includes(value.kind))throw Error('Invalid admission event');
  const stage=value.stage??'upload';if(!Object.hasOwn(this.stageCounts,stage))throw Error('Invalid admission stage');
  const row={status:value.status,key:value.key,kind:value.kind,stage};
  for(const key of numeric){const n=value[key]??null;if(n!==null&&(!Number.isFinite(n)||n<0))throw Error('Invalid admission number');row[key]=n;}
  for(const key of booleans){const b=value[key]??null;if(b!==null&&typeof b!=='boolean')throw Error('Invalid admission probe');row[key]=b;}
  if(value.markerSHA256!=null&&!/^[0-9a-f]{64}$/.test(value.markerSHA256))throw Error('Invalid admission marker digest');row.markerSHA256=value.markerSHA256??null;
  row.sameContext=row.beforeContext!==null&&row.beforeContext===row.afterContext;
  row.sameInputRejectionSeen=row.status==='rejected'&&row.beforeContext!==null&&this.events.some(e=>e.status==='rejected'&&e.stage===row.stage&&e.afterContext===row.beforeContext&&e.key===row.key&&e.markerSHA256===row.markerSHA256&&e.gain===row.gain&&e.cost===row.cost);
  row.sequence=++this.total;this.counts[row.status]++;this.stageCounts[stage][row.status]++;this.events.push(row);if(this.events.length>this.capacity){this.events.shift();this.overwritten++;}
 }
 snapshot(){return {enabled:this.enabled,capacity:this.capacity,total:this.total,overwritten:this.overwritten,oversizedContexts:this.oversizedContexts,counts:{...this.counts},stageCounts:Object.fromEntries(Object.entries(this.stageCounts).map(([stage,counts])=>[stage,{...counts}])),events:this.events.map(e=>({...e})),scope:'bounded_budget_admission_observation_only; context IDs are page-local; no payload retained; not a refusal blacklist'};}
}
