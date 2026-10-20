import test from 'node:test';
import assert from 'node:assert/strict';
import {fetchSourcePlanResponse} from '../src/source_plan_transport.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
const route='api/lod-plan/141/3';
test('acknowledged bounded waits avoid an additional client polling delay',async()=>{
 const calls=[],delays=[];let n=0;const response=await fetchSourcePlanResponse({url:route,fetcher:async url=>{calls.push(url);return ++n===1?new Response('preparing',{status:202,headers:{'X-XNBY-Source-Plan-Wait-Ms':'200'}}):Response.json({ready:true});},sleep:async ms=>delays.push(ms)});
 assert.equal(response.status,200);assert.deepEqual(calls,[route+'?wait_ms=200',route+'?wait_ms=200']);assert.deepEqual(delays,[]);
});
test('only the exact wait acknowledgment suppresses the old delay',async()=>{
 for(const ack of [null,'199','0200','201','200, 200']){const delays=[];let n=0;await fetchSourcePlanResponse({url:route,fetcher:async()=>++n===1?new Response('',{status:202,headers:ack===null?{}:{'X-XNBY-Source-Plan-Wait-Ms':ack}}):new Response('ok'),sleep:async ms=>delays.push(ms)});assert.deepEqual(delays,[300]);}
});
test('old 400 and 422 services retry the same original route once without the optional query',async()=>{
 for(const rejection of [400,422]){const calls=[],delays=[];let n=0;await fetchSourcePlanResponse({url:route,fetcher:async url=>{calls.push(url);return ++n===1?new Response('',{status:rejection}):n===2?new Response('',{status:202}):new Response('ok');},sleep:async ms=>delays.push(ms)});assert.deepEqual(calls,[route+'?wait_ms=200',route,route]);assert.deepEqual(delays,[300]);}
});
test('authentication, unavailable and malformed original requests are not retried as optional capability errors',async()=>{
 for(const status of [401,403,404,409,500,503]){let calls=0;const r=await fetchSourcePlanResponse({url:route,fetcher:async()=>{calls++;return new Response('',{status});}});assert.equal(r.status,status);assert.equal(calls,1);}
 let calls=0;const r=await fetchSourcePlanResponse({url:route,fetcher:async()=>{calls++;return new Response('',{status:400});}});assert.equal(r.status,400);assert.equal(calls,2);
});
test('camera cancellation closes a returned body and starts no further requests',async()=>{
 let wanted=true,cancelled=false,calls=0;const body=new ReadableStream({cancel(){cancelled=true;}});
 await assert.rejects(fetchSourcePlanResponse({url:route,stillWanted:()=>wanted,fetcher:async()=>{calls++;wanted=false;return new Response(body,{status:202});}}),SourceLoadCancelled);assert.equal(calls,1);assert.equal(cancelled,true);
});
test('cancellation after a compatibility response or delay prevents another fetch',async()=>{
 let wanted=true,calls=0;await assert.rejects(fetchSourcePlanResponse({url:route,stillWanted:()=>wanted,fetcher:async()=>{calls++;return new Response('',{status:202});},sleep:async()=>{wanted=false;}}),SourceLoadCancelled);assert.equal(calls,1);
});
test('lease, arbitrary URL and indexed-view paths cannot enter this metadata transport',async()=>{
 for(const url of ['https://example.com/api/lod-plan/1/3','api/lod/1/3','api/lod-index-family-plan/1/anything','api/lod-plan/1/3?x=1','api/lod-plan/../private'])await assert.rejects(fetchSourcePlanResponse({url,fetcher:()=>{throw Error('must not fetch');}}),/metadata route/);
});
