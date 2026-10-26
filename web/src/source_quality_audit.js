// Diagnostic decomposition only. Edge length is a proxy, never geometry error;
// texel scale is a source metric, never a final rendered-image quality claim.
export class ProjectedQualityAudit {
 constructor({height,fov,maxSamples=65536}) {
  if(!Number.isInteger(height)||height<1||height>16384||!Number.isFinite(fov)||fov<=0||fov>=180||!Number.isInteger(maxSamples)||maxSamples<1||maxSamples>65536)throw Error('Invalid projected quality audit');
  this.focal=height/(2*Math.tan(fov*Math.PI/360));this.maxSamples=maxSamples;this.count=0;
  this.cells=Array.from({length:9},()=>({edge:[],texel:[],unknownSamples:0,edgeOnlySamples:0,texelOnlySamples:0,bothSamples:0,neitherSamples:0}));
 }
 record(cell,metric,bin) {
  if(!Number.isInteger(cell)||cell<0||cell>8||!Number.isInteger(bin)||bin<0||bin>255||this.count>=this.maxSamples)throw Error('Invalid projected quality sample');
  this.count++;const c=this.cells[cell],depth=.5*120000**(bin/255),edge=metric?.longest_edge_p90_m,texel=metric?.texel_world_p90_m??0;
  const e=edge*this.focal/depth,t=texel*this.focal/depth;
  if(!Number.isFinite(edge)||edge<0||!Number.isFinite(texel)||texel<0||!Number.isFinite(e)||!Number.isFinite(t)){c.unknownSamples++;return;}
  c.edge.push(e);c.texel.push(t);const a=e>6,b=t>1.5;
  c[a?(b?'bothSamples':'edgeOnlySamples'):(b?'texelOnlySamples':'neitherSamples')]++;
 }
 snapshot() {
  const quantiles=values=>{if(!values.length)return {p50:null,p90:null,max:null};const sorted=[...values].sort((a,b)=>a-b);return {p50:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.5))],p90:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.9))],max:sorted.at(-1)};};
  return {scope:'depth_binned_source_edge_and_texel_proxies_not_geometric_error_or_final_pixel_quality',thresholds:{edgePixels:6,texelPixels:1.5},samples:this.count,cells:this.cells.map((c,i)=>({row:Math.floor(i/3),column:i%3,knownSamples:c.edge.length,unknownSamples:c.unknownSamples,edgeOnlySamples:c.edgeOnlySamples,texelOnlySamples:c.texelOnlySamples,bothSamples:c.bothSamples,neitherSamples:c.neitherSamples,edgePixels:quantiles(c.edge),texelPixels:quantiles(c.texel)}))};
 }
}

export function captureSourceLoadState({failed,familyFailed,coverageRejected,restoreFailed,lastGain=null,allocationChoice=null,indexedQualityLimits=0,budgetFallbacks=0}) {
 const list=set=>{const keys=[];for(const key of set){keys.push(String(key).slice(0,512));if(keys.length===32)break;}return {count:set.size,keys,truncated:set.size>keys.length};};
 const fields=(value,names)=>value?Object.fromEntries(names.filter(k=>Object.hasOwn(value,k)).map(k=>[k,typeof value[k]==='string'?value[k].slice(0,512):value[k]])):null;
 return {scope:'bounded_current_failure_sets_not_all_HTTP_history',roots:list(failed),families:list(familyFailed),coverageRejected:list(coverageRejected),restoreFailed:list(restoreFailed),indexedQualityLimits,budgetFallbacks,lastGain:fields(lastGain,['root','samples','hits','missing','parentDeficit','childResidual','gain','combinedGain','texelGain','signedTexelGain','parentTexelDeficit','childTexelResidual','gainPolicy','model','memoHit','milliseconds']),allocationChoice:fields(allocationChoice,['key','gain','bytes'])};
}
