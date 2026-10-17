import test from 'node:test';
import assert from 'node:assert/strict';
import {leasedAssetURL,LeasedDownloads} from '../src/lod_downloads.js';
const token='a'.repeat(32),base='http://127.0.0.1:8767/';
test('all native GLTF dependencies carry the same batch lease, external/base assets do not',()=>{
 for(const file of ['geometry.gltf','geometry.bin','atlas.jpg'])assert.equal(new URL(leasedAssetURL(`native/tile_141_depth_5/part_000/${file}`,token,base)).searchParams.get('lease'),token);
 assert.equal(leasedAssetURL('assets/context.gltf',token,base),base+'assets/context.gltf');
 assert.equal(leasedAssetURL('https://example.test/native/a.bin',token,base),'https://example.test/native/a.bin');
 assert.equal(leasedAssetURL('data:application/octet-stream;base64,AA==',token,base),'data:application/octet-stream;base64,AA==');
});
test('lease release is idempotent and cancellation can release without loading',async()=>{
 const calls=[],downloads=new LeasedDownloads(token,base,async(...args)=>{calls.push(args);return{ok:true};});
 await downloads.release();await downloads.release();assert.equal(calls.length,1);assert.equal(calls[0][1].method,'POST');assert.equal(calls[0][1].keepalive,true);
 assert.throws(()=>new LeasedDownloads('bad',base),/租约/);
});

test('browser fetch is called without a foreign receiver and release errors never break cleanup',async()=>{
 let called=false;const fetcher=function(){assert.equal(this,undefined);called=true;return Promise.resolve({ok:true});};
 const downloads=new LeasedDownloads(token,base,fetcher);await downloads.release();assert.ok(called);
 const failure=new LeasedDownloads(token,base,()=>{throw Error('network unavailable');});await assert.doesNotReject(()=>failure.release());
});
