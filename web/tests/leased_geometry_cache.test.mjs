import test from 'node:test';import assert from 'node:assert/strict';import {LeasedDownloads} from '../src/lod_downloads.js';
const token='a'.repeat(32),base='http://127.0.0.1:8768/',route=i=>`native/tile_${i}_depth_3/part_000/geometry.bin`;
test('gain-worker transfers and caller mutations cannot detach or change the retained leased geometry',async()=>{
 let reads=0;const d=new LeasedDownloads(token,base,async(url,o)=>{if(o?.method==='POST')return {ok:true};reads++;return {ok:true,arrayBuffer:async()=>new Uint8Array([1,2,3,4]).buffer};},{geometryCacheBytes:8});
 const first=await d.read(route(1));structuredClone(first,{transfer:[first]});assert.equal(first.byteLength,0);const next=await d.read(route(1));new Uint8Array(next)[0]=99;assert.deepEqual([...new Uint8Array(await d.read(route(1)))],[1,2,3,4]);assert.equal(reads,1);assert.equal(d.geometrySnapshot().hits,2);await d.release();assert.equal(d.geometrySnapshot().bytes,0);
});
test('LRU is byte bounded and source PNG, base assets and external resources are never cached',async()=>{
 let reads=0;const d=new LeasedDownloads(token,base,async(url,o)=>{if(o?.method==='POST')return {ok:true};reads++;return {ok:true,arrayBuffer:async()=>new ArrayBuffer(4)};},{geometryCacheBytes:8});
 await d.read(route(1));await d.read(route(2));await d.read(route(1));await d.read(route(3));await d.read(route(2));assert.equal(reads,4);assert.equal(d.geometrySnapshot().bytes,8);assert.equal(d.geometrySnapshot().evictions,2);
 for(const path of ['native/tile_1_depth_3/part_000/texture.png','assets/a.bin','https://example.test/native/tile_1_depth_3/part_000/geometry.bin']){await d.read(path);await d.read(path);}assert.equal(reads,10);assert.equal(d.geometrySnapshot().bytes,8);assert.equal(d.geometrySnapshot().peakBytes,8);await d.release();
});
test('a late fetch after owner release cannot repopulate cache and still sends release only once',async()=>{
 let releaseRead,posts=0;const d=new LeasedDownloads(token,base,async(url,o)=>{if(o?.method==='POST'){posts++;return {ok:true};}return {ok:true,arrayBuffer:()=>new Promise(r=>{releaseRead=r;})};},{geometryCacheBytes:8});
 const late=d.read(route(1));await new Promise(r=>setImmediate(r));await d.release();releaseRead(new ArrayBuffer(4));await assert.rejects(late,/已释放/);await d.release();assert.equal(posts,1);assert.equal(d.geometrySnapshot().entries,0);assert.equal(d.geometrySnapshot().bytes,0);
});
test('overlapping requests for one URL account replacement once and failing observers cannot leak the lease',async()=>{
 const pending=[];let posts=0;const d=new LeasedDownloads(token,base,async(url,o)=>{if(o?.method==='POST'){posts++;return {ok:true};}return {ok:true,arrayBuffer:()=>new Promise(r=>pending.push(r))};},{geometryCacheBytes:8,onGeometryStats:()=>{throw Error('observer');}});
 const a=d.read(route(1)),b=d.read(route(1));await new Promise(r=>setImmediate(r));pending[1](new ArrayBuffer(4));await b;pending[0](new ArrayBuffer(4));await a;assert.equal(d.geometrySnapshot().bytes,4);assert.equal(d.geometrySnapshot().entries,1);await d.release();assert.equal(posts,1);assert.equal(d.geometrySnapshot().bytes,0);assert.equal(d.geometrySnapshot().observerErrors,3);
});
test('default cache stays disabled, huge individual buffers are not retained and bounds reject invalid options',async()=>{
 let reads=0;const fetcher=async(url,o)=>o?.method==='POST'?{ok:true}:{ok:true,arrayBuffer:async()=>{reads++;return new ArrayBuffer(9);}};const legacy=new LeasedDownloads(token,base,fetcher);await legacy.read(route(1));await legacy.read(route(1));assert.equal(reads,2);assert.equal(legacy.geometrySnapshot().bytes,0);await legacy.release();
 const d=new LeasedDownloads(token,base,fetcher,{geometryCacheBytes:8});await d.read(route(1));assert.equal(d.geometrySnapshot().bytes,0);await d.release();for(const geometryCacheBytes of [-1,NaN,32*1048576+1])assert.throws(()=>new LeasedDownloads(token,base,fetcher,{geometryCacheBytes}),/bound/);
});
