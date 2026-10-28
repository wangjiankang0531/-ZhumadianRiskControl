import test from 'node:test';import assert from 'node:assert/strict';
import {SourcePlanCache,SOURCE_PLAN_SCHEMA,readSourcePlan,verifyPlannedSource,SourcePlanChanged} from '../src/source_descriptor_plan.js';
import {SourceLoadCancelled} from '../src/lod_transaction.js';
const marker=id=>({schema:'hongtu.osgb_native_chunk_bundle.v1',tile_id:id,depth:3,texture_policy:'original_pixels_v1',complete_frontier:true,parts:[{directory:'part_000',files:[{name:'geometry.bin',sha256:'a'.repeat(64)}]}],source_nodes:[]});
const wrapper=id=>({schema:SOURCE_PLAN_SCHEMA,verification:'metadata_only',availabilityVerified:false,markerSHA256:'b'.repeat(64),marker:marker(id)});
test('hundreds of camera/cut rescoring rounds reuse exact immutable metadata, never a lease',async()=>{
 let reads=0;const cache=new SourcePlanCache(),fetcher=async()=>{reads++;return Response.json(wrapper(141));};let first;
 for(let cut=0;cut<300;cut++){const plan=await cache.read({request:{id:141,depth:3},fetcher});first??=plan;assert.equal(plan,first);assert.equal(Object.hasOwn(plan.marker,'cache_lease'),false);}
 assert.equal(reads,1);assert.equal(cache.snapshot().hits,299);assert.ok(cache.bytes<=cache.maxBytes);
 const reply=new Response(null,{headers:{'X-XNBY-Source-Marker-SHA256':'b'.repeat(64)}}),actual={...marker(141),cache_lease:'c'.repeat(32)};
 assert.equal(verifyPlannedSource(first,reply,actual),true);assert.throws(()=>verifyPlannedSource(first,reply,{...actual,depth:4}),SourcePlanChanged);assert.throws(()=>verifyPlannedSource(first,reply,{...actual,cache_lease:undefined}),SourcePlanChanged);
 cache.invalidate(first);assert.equal(cache.bytes,0);assert.equal(cache.snapshot().invalidations,1);await cache.read({request:{id:141,depth:3},fetcher});assert.equal(reads,2);
});
test('entry and byte bounds evict only metadata, and oversized descriptors are not retained',async()=>{
 let reads=0;const load=options=>readSourcePlan({...options,fetcher:async()=>{reads++;return Response.json(wrapper(options.request.id));}}),cache=new SourcePlanCache({maxEntries:2,load});
 for(const id of [1,2,1,3,2])await cache.read({request:{id,depth:3}});assert.equal(reads,4);assert.equal(cache.entries.size,2);assert.equal(cache.evictions,2);
 const tiny=new SourcePlanCache({maxBytes:1,load});await tiny.read({request:{id:1,depth:3}});assert.equal(tiny.entries.size,0);assert.equal(tiny.bytes,0);
});
test('cancelled or unverified plans never enter the cache, including existing cache hits',async()=>{
 const cache=new SourcePlanCache();let wanted=true;await assert.rejects(cache.read({request:{id:1,depth:3},stillWanted:()=>wanted,fetcher:async()=>{wanted=false;return Response.json(wrapper(1));}}),SourceLoadCancelled);assert.equal(cache.entries.size,0);
 await cache.read({request:{id:1,depth:3},fetcher:async()=>Response.json(wrapper(1))});await assert.rejects(cache.read({request:{id:1,depth:3},stillWanted:()=>false}),SourceLoadCancelled);
 await assert.rejects(new SourcePlanCache({load:async()=>({marker:marker(1)})}).read({request:{id:1,depth:3}}),/Unverified/);
});
test('clear during an in-flight read cannot repopulate a retired cache generation',async()=>{
 let release;const gate=new Promise(resolve=>release=resolve),cache=new SourcePlanCache({load:async options=>{await gate;return readSourcePlan({...options,fetcher:async()=>Response.json(wrapper(1))});}});
 const pending=cache.read({request:{id:1,depth:3}});cache.clear();release();await pending;assert.equal(cache.entries.size,0);assert.equal(cache.bytes,0);
});

test('cache-only reads prove absence of descriptor IO while retaining exact pinned plans',async()=>{
 let reads=0;const cache=new SourcePlanCache({load:async options=>{reads++;return readSourcePlan({...options,fetcher:async()=>Response.json(wrapper(options.request.id))});}}),options={request:{id:141,depth:3}};
 assert.equal(cache.readCached(options),null);assert.equal(reads,0);assert.equal(cache.snapshot().misses,0);
 const original=await cache.read(options);assert.equal(reads,1);assert.equal(cache.readCached(options),original);assert.equal(reads,1);assert.equal(cache.snapshot().hits,1);
 assert.throws(()=>cache.readCached({...options,stillWanted:()=>false}),SourceLoadCancelled);assert.equal(cache.snapshot().hits,1);
 cache.invalidate(original);assert.equal(cache.readCached(options),null);assert.equal(reads,1);
});
test('cache-only lookup refuses injected unpinned metadata and validates bounded routes',()=>{
 const cache=new SourcePlanCache();cache.entries.set('api/lod-plan/1/3',{plan:{marker:marker(1)},bytes:1});assert.throws(()=>cache.readCached({request:{id:1,depth:3}}),/Unverified/);assert.throws(()=>cache.readCached({request:{id:0,depth:3}}));
});
