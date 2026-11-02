import {isMemoryFormat} from './source_page_format.js';
import {ensureSourceWanted} from './lod_transaction.js';

// Successful replies transfer a live lease to the caller. The caller must read
// the marker and register its lease before checking late camera cancellation.
export async function fetchSourceBundleResponse({url,fetcher=fetch,stillWanted=()=>true,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))}){
 const root=/^api\/lod\/[1-9][0-9]{0,3}\/[1-9][0-9]?$/.test(url),family=/^api\/lod-family\/[1-9][0-9]{0,3}\/Tile_[0-9]+_L[0-9]+_0[0-9u]+\.osgb$/.test(url),indexed=/^api\/lod-index-family\/[1-9][0-9]{0,3}\/[0-9a-f]{32}$/.test(url);
 if(typeof url!=='string'||!root&&!family&&!indexed)throw Error('Invalid source bundle route');
 let optional=true;const waitingURL=url+'?wait_ms=200';
 const request=async()=>{ensureSourceWanted(stillWanted);const response=await fetcher(optional?waitingURL:url,{cache:'no-store'});if(response.status===200)return response;try{ensureSourceWanted(stillWanted);}catch(error){await response.body?.cancel().catch(()=>{});throw error;}return response;};
 let response=await request();
 // Only the old handler's unsupported-query response is compatible fallback.
 // Source validation failures (422), auth and unavailable errors are final.
 if(response.status===400){await response.body?.cancel().catch(()=>{});optional=false;response=await request();}
 while(response.status===202){const waited=optional&&response.headers.get('X-XNBY-Source-Bundle-Wait-Ms')==='200';await response.body?.cancel().catch(()=>{});ensureSourceWanted(stillWanted);if(!waited){await sleep(300);ensureSourceWanted(stillWanted);}response=await request();}
 return response;
}

export function sourceBundleWaitEligible({enabled,marker}){if(typeof enabled!=='boolean')throw Error('Invalid bundle wait policy');return enabled&&isMemoryFormat(marker?.source_format);}
