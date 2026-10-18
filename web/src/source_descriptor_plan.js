import {ensureSourceWanted} from './lod_transaction.js';
import {sourceBundleIdentity} from './source_residency.js';
export const SOURCE_PLAN_SCHEMA='xnby.source_bundle_plan.v1';
const plans=new WeakMap(),sha=/^[0-9a-f]{64}$/;
export function supportsSourcePlans(health){return health?.application==='xnby.landscape.web.v1'&&health.lodAccess==='read_only'&&health.conversionEnabled===false&&health.descriptorPlanSchema===SOURCE_PLAN_SCHEMA;}
export function sourcePlanURL(request){
 if(!Number.isSafeInteger(request?.id)||request.id<1||request.id>2346)throw Error('Invalid plan root');
 if(request.parent!==undefined){if(request.depth!==undefined||typeof request.parent!=='string'||request.parent.length>256||!new RegExp('^Tile_'+request.id+'_L\\d+_0[0-9u]+\\.osgb$').test(request.parent))throw Error('Invalid plan parent');return `api/lod-family-plan/${request.id}/${encodeURIComponent(request.parent)}`;}
 if(!Number.isSafeInteger(request.depth)||request.depth<1||request.depth>12)throw Error('Invalid plan depth');return `api/lod-plan/${request.id}/${request.depth}`;
}
export class SourcePlanResponseError extends Error{constructor(response){super('地景计划读取失败');this.response=response;}}
export class SourcePlanChanged extends Error{constructor(){super('地景计划与实际资源版本不一致，保留当前地景');}}
function freeze(value){if(value&&typeof value==='object'){for(const v of Object.values(value))freeze(v);Object.freeze(value);}return value;}
export async function readSourcePlan(options){try{return await requestSourcePlan(options);}catch(error){ensureSourceWanted(options.stillWanted??(()=>true));throw error;}}
async function requestSourcePlan({request,fetcher=fetch,stillWanted=()=>true}){
 const url=sourcePlanURL(request);ensureSourceWanted(stillWanted);const response=await fetcher(url,{cache:'no-store'});ensureSourceWanted(stillWanted);if(!response.ok)throw new SourcePlanResponseError(response);
 const limit=16*1048576+2048,declared=Number(response.headers.get('Content-Length'));if(declared>limit)throw Error('Source plan exceeds bound');let raw;
 if(response.body?.getReader){const reader=response.body.getReader(),chunks=[];let total=0;try{for(;;){ensureSourceWanted(stillWanted);const {done,value}=await reader.read();ensureSourceWanted(stillWanted);if(done)break;total+=value.byteLength;if(total>limit)throw Error('Source plan exceeds bound');chunks.push(value);}raw=new Uint8Array(total);let at=0;for(const chunk of chunks){raw.set(chunk,at);at+=chunk.byteLength;}}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}}
 else{raw=new Uint8Array(await response.arrayBuffer());if(raw.byteLength>limit)throw Error('Source plan exceeds bound');}
 ensureSourceWanted(stillWanted);const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)),marker=value.marker;
 if(Object.keys(value).sort().join(',')!=='availabilityVerified,marker,markerSHA256,schema,verification'||value.schema!==SOURCE_PLAN_SCHEMA||value.verification!=='metadata_only'||value.availabilityVerified!==false||!sha.test(value.markerSHA256)||!marker||Object.hasOwn(marker,'cache_lease')||marker.tile_id!==request.id||marker.texture_policy!=='original_pixels_v1'||!Array.isArray(marker.parts)||!marker.parts.length||marker.parts.length>64)throw Error('Invalid source plan identity');
 if(request.parent!==undefined?marker.schema!=='xnby.osgb_native_family.v1'||marker.replacement_parent!==request.parent||marker.complete_sibling_family!==true:marker.schema!=='hongtu.osgb_native_chunk_bundle.v1'||marker.depth!==request.depth||marker.complete_frontier!==true)throw Error('Plan source differs from request');
 const result=freeze({marker,markerSHA256:value.markerSHA256});plans.set(result,{identity:sourceBundleIdentity(marker),markerSHA256:value.markerSHA256});return result;
}
export function verifyPlannedSource(plan,response,marker){const pinned=plans.get(plan);if(!pinned||response.headers.get('X-XNBY-Source-Marker-SHA256')!==pinned.markerSHA256||!sha.test(pinned.markerSHA256)||!/^[0-9a-f]{32}$/.test(marker?.cache_lease??'')||sourceBundleIdentity(marker)!==pinned.identity)throw new SourcePlanChanged();return true;}
