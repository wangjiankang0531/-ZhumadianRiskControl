import {fetchSourcePlanResponse} from './source_plan_transport.js';
import {isMemorySourcePart,isMemoryFamily,isIndexedMemoryFamily,MEMORY_ROOT_SCHEMA,isMemoryFormat} from './source_page_format.js';
import {ensureSourceWanted} from './lod_transaction.js';
import {sourceBundleIdentity} from './source_residency.js';
import {validateIndexedSourceReplacement} from './source_level_index.js';
export const SOURCE_PLAN_SCHEMA='xnby.source_bundle_plan.v1';
const plans=new WeakMap(),sha=/^[0-9a-f]{64}$/;
export function supportsSourcePlans(health){return health?.application==='xnby.landscape.web.v1'&&health.lodAccess==='read_only'&&health.conversionEnabled===false&&health.descriptorPlanSchema===SOURCE_PLAN_SCHEMA;}
export function sourcePlanURL(request){
 if(!Number.isSafeInteger(request?.id)||request.id<1||request.id>2346)throw Error('Invalid plan root');
 if(request.parent!==undefined){if(request.depth!==undefined||typeof request.parent!=='string'||request.parent.length>256||!new RegExp('^Tile_'+request.id+'_L\\d+_0[0-9u]+\\.osgb$').test(request.parent))throw Error('Invalid plan parent');if(request.view!==undefined){validateIndexedView(request.view);return `api/lod-index-family-plan/${request.id}/${encodeURIComponent(request.parent)}?view=${encodeURIComponent(request.view.join(','))}`;}return `api/lod-family-plan/${request.id}/${encodeURIComponent(request.parent)}`;}
 if(request.view!==undefined||!Number.isSafeInteger(request.depth)||request.depth<1||request.depth>12)throw Error('Invalid plan depth');return `api/lod-plan/${request.id}/${request.depth}`;
}
export class SourcePlanResponseError extends Error{constructor(response){super('地景计划读取失败');this.response=response;}}
export class IndexedSourceQualityLimit extends Error{constructor(marker){super('当前原始纹理或页限额要求保留完整父层');this.marker=marker;}}
export function validateIndexedView(view){if(!Array.isArray(view)||view.length!==10||!view.every(Number.isFinite)||view.slice(0,6).some(v=>Math.abs(v)>1e7)||Math.hypot(...view.slice(0,3).map((v,a)=>v-view[a+3]))<=1e-12||view[6]<=0||view[6]>=179||view[7]<=0||!Number.isInteger(view[8])||view[8]<1||view[8]>16384||view[9]<.25||view[9]>512||view.join(',').length>512)throw Error('Invalid indexed source camera');return true;}
export class SourcePlanChanged extends Error{constructor(){super('地景计划与实际资源版本不一致，保留当前地景');}}
function freeze(value){if(value&&typeof value==='object'){for(const v of Object.values(value))freeze(v);Object.freeze(value);}return value;}
export async function readSourcePlan(options){try{return await requestSourcePlan(options);}catch(error){ensureSourceWanted(options.stillWanted??(()=>true));throw error;}}
async function requestSourcePlan({request,fetcher=fetch,stillWanted=()=>true,topology=null,metrics=null}){
 const fetchPlan=()=>fetchSourcePlanResponse({url:sourcePlanURL(request),fetcher,stillWanted});
 const response=await (metrics?metrics.measureAsync('source_plan_http_wait',fetchPlan):fetchPlan());ensureSourceWanted(stillWanted);if(!response.ok)throw new SourcePlanResponseError(response);
 const readBody=()=>readSourcePlanBody(response,stillWanted),raw=await (metrics?metrics.measureAsync('source_plan_body_wait',readBody):readBody());
 const validate=()=>validateSourcePlanBody(raw,request,topology,stillWanted);return metrics?metrics.measure('source_plan_validation',validate):validate();
}
async function readSourcePlanBody(response,stillWanted){
 const limit=16*1048576+2048,declared=Number(response.headers.get('Content-Length'));if(declared>limit)throw Error('Source plan exceeds bound');let raw;
 if(response.body?.getReader){const reader=response.body.getReader(),chunks=[];let total=0;try{for(;;){ensureSourceWanted(stillWanted);const {done,value}=await reader.read();ensureSourceWanted(stillWanted);if(done)break;total+=value.byteLength;if(total>limit)throw Error('Source plan exceeds bound');chunks.push(value);}raw=new Uint8Array(total);let at=0;for(const chunk of chunks){raw.set(chunk,at);at+=chunk.byteLength;}}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}}
 else{raw=new Uint8Array(await response.arrayBuffer());if(raw.byteLength>limit)throw Error('Source plan exceeds bound');}
 return raw;
}
function validateSourcePlanBody(raw,request,topology,stillWanted){
 ensureSourceWanted(stillWanted);const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)),marker=value.marker;
 const indexed=request.view!==undefined;if(indexed){if(!/^[0-9a-f]{32}$/.test(value.indexedRequest)||value.requestedPixels!==request.view[9]||!Number.isFinite(value.selectedPixels)||value.selectedPixels<value.requestedPixels||value.selectedPixels>65536)throw Error('Invalid indexed plan request identity');if(marker?.schema==='zhumadian.indexed_quality_limit.v1'&&marker.tile_id===request.id&&marker.replacement_parent===request.parent&&marker.complete_parent_retained===true&&!Object.hasOwn(marker,'cache_lease')&&!Object.hasOwn(marker,'parts'))throw new IndexedSourceQualityLimit(marker);validateIndexedSourceReplacement(topology,marker,request.parent);}
 const expected=indexed?'availabilityVerified,indexedRequest,marker,markerSHA256,queryStats,requestedPixels,schema,selectedMaxDepth,selectedPixels,selectionLimitedByBudget,verification':'availabilityVerified,marker,markerSHA256,schema,verification';
 if(Object.keys(value).sort().join(',')!==expected||value.schema!==SOURCE_PLAN_SCHEMA||value.verification!=='metadata_only'||value.availabilityVerified!==false||!sha.test(value.markerSHA256)||!marker||Object.hasOwn(marker,'cache_lease')||marker.tile_id!==request.id||marker.texture_policy!=='original_pixels_v1'||!Array.isArray(marker.parts)||!marker.parts.length||marker.parts.length>64)throw Error('Invalid source plan identity');
 if(marker.source_format!==undefined&&!isMemoryFormat(marker.source_format)||marker.parts.some(p=>isMemorySourcePart(p)!==isMemoryFormat(marker.source_format)||isMemoryFormat(marker.source_format)&&p.source_format!==marker.source_format))throw Error('Invalid source plan page format');
 if(isMemoryFormat(marker.source_format)&&(request.parent!==undefined?!isMemoryFamily(marker):marker.schema!==MEMORY_ROOT_SCHEMA))throw Error('Mixed source marker schema');
 if(request.parent!==undefined?!(marker.schema==='xnby.osgb_native_family.v1'||isMemoryFamily(marker))||marker.replacement_parent!==request.parent||(!indexed&&marker.complete_sibling_family!==true):!(marker.schema==='hongtu.osgb_native_chunk_bundle.v1'||marker.schema===MEMORY_ROOT_SCHEMA&&isMemoryFormat(marker.source_format))||marker.depth!==request.depth||marker.complete_frontier!==true)throw Error('Plan source differs from request');
 const result=freeze({marker,markerSHA256:value.markerSHA256,...(indexed?{indexedRequest:value.indexedRequest,bundleURL:`api/lod-index-family/${request.id}/${value.indexedRequest}`,sourceRequest:structuredClone(request)}:{})});plans.set(result,{identity:sourceBundleIdentity(marker),markerSHA256:value.markerSHA256});return result;
}

export function verifyPlannedSource(plan,response,marker){const pinned=plans.get(plan);if(!pinned||response.headers.get('X-XNBY-Source-Marker-SHA256')!==pinned.markerSHA256||!sha.test(pinned.markerSHA256)||!/^[0-9a-f]{32}$/.test(marker?.cache_lease??'')||sourceBundleIdentity(marker)!==pinned.identity)throw new SourcePlanChanged();return true;}


// Immutable metadata can survive a camera/cut change. Availability and leases
// cannot: every admitted load still calls verifyPlannedSource on the real reply.
export class SourcePlanCache{
 constructor({maxBytes=4*1048576,maxEntries=256,load=readSourcePlan}={}){
  if(!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>16*1048576||!Number.isSafeInteger(maxEntries)||maxEntries<1||maxEntries>256||typeof load!=='function')throw Error('Invalid source plan cache bound');
  this.maxBytes=maxBytes;this.maxEntries=maxEntries;this.load=load;this.entries=new Map();this.bytes=0;this.hits=0;this.misses=0;this.evictions=0;this.invalidations=0;this.generation=0;
 }
 // A cache-only read proves this call did not start or await a descriptor fetch.
 // It returns the original privately pinned plan, never a copied availability claim.
 readCached(options){
  const wanted=options.stillWanted??(()=>true),key=sourcePlanURL(options.request);ensureSourceWanted(wanted);
  const prior=this.entries.get(key);if(!prior)return null;
  if(!plans.has(prior.plan))throw Error('Unverified source plan cannot be cached');
  this.hits++;this.entries.delete(key);this.entries.set(key,prior);return prior.plan;
 }
 async read(options){
  const wanted=options.stillWanted??(()=>true),key=sourcePlanURL(options.request);ensureSourceWanted(wanted);
  const cached=this.readCached(options);if(cached)return cached;
  this.misses++;const generation=this.generation,plan=await this.load(options);ensureSourceWanted(wanted);if(!plans.has(plan))throw Error('Unverified source plan cannot be cached');
  const bytes=new TextEncoder().encode(JSON.stringify(plan)).byteLength+new TextEncoder().encode(key).byteLength;
  if(bytes>this.maxBytes||generation!==this.generation)return plan;
  const previous=this.entries.get(key);if(previous){this.entries.delete(key);this.bytes-=previous.bytes;}
  while(this.entries.size&&(this.entries.size>=this.maxEntries||this.bytes+bytes>this.maxBytes)){const [old,value]=this.entries.entries().next().value;this.entries.delete(old);this.bytes-=value.bytes;this.evictions++;}
  this.entries.set(key,{plan,bytes});this.bytes+=bytes;return plan;
 }
 invalidate(plan){for(const [key,value] of this.entries)if(value.plan===plan){this.entries.delete(key);this.bytes-=value.bytes;this.invalidations++;}}
 clear(){this.entries.clear();this.bytes=0;this.generation++;}
 snapshot(){return {bytes:this.bytes,entries:this.entries.size,hits:this.hits,misses:this.misses,evictions:this.evictions,invalidations:this.invalidations,maxBytes:this.maxBytes,maxEntries:this.maxEntries};}
}
