import {ensureSourceWanted} from './lod_transaction.js';

// This helper waits for metadata only. Bundle transport separately controls
// optional waiting and lease acquisition; real upload admission is unchanged.
export async function fetchSourcePlanResponse({url,fetcher=fetch,stillWanted=()=>true,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))}){
 const direct=typeof url==='string'&&/^api\/lod-(?:family-)?plan\/[1-9][0-9]*\/[A-Za-z0-9_.%-]+$/.test(url),indexed=typeof url==='string'&&/^api\/lod-index-family-plan\/[1-9][0-9]*\/Tile_[0-9]+_L[0-9]+_0[0-9u]+\.osgb\?view=[0-9a-fA-F+%.,-]{1,1536}$/.test(url);if(!direct&&!indexed)throw Error('Invalid source metadata route');
 const waitingURL=url+(indexed?'&':'?')+'wait_ms=200';let optional=true;
 const request=async()=>{ensureSourceWanted(stillWanted);const response=await fetcher(optional?waitingURL:url,{cache:'no-store'});try{ensureSourceWanted(stillWanted);}catch(error){await response.body?.cancel().catch(()=>{});throw error;}return response;};
 let response=await request();
 if(response.status===400||response.status===422){await response.body?.cancel().catch(()=>{});optional=false;response=await request();}
 while(response.status===202){
  const waited=optional&&response.headers.get('X-XNBY-Source-Plan-Wait-Ms')==='200';
  await response.body?.cancel().catch(()=>{});ensureSourceWanted(stillWanted);
  if(!waited){await sleep(300);ensureSourceWanted(stillWanted);}
  response=await request();
 }
 return response;
}
