import test from 'node:test';import assert from 'node:assert/strict';import {WitnessArchive,witnessArchiveEnabled} from '../src/witness_archive.js';
const href='http://127.0.0.1:54321/?qa=1&witness=1&witnessArchive=1',record=()=>({targetMs:20000,actualElapsedMs:20012}),blob=()=>new Blob(['PNG transport fixture'],{type:'image/png'}),cap={schema:'xnby.witness_archive.v1',nonce:'a'.repeat(32),targets:[5000,20000,40000]};
test('archive needs explicit QA flags on a credential-free loopback HTTP origin',async()=>{
 assert.equal(witnessArchiveEnabled(href),true);for(const url of ['https://example.test/?qa=1&witness=1&witnessArchive=1','http://user:pass@127.0.0.1/?qa=1&witness=1&witnessArchive=1','http://127.0.0.1/?qa=1&witness=1','file:///a?qa=1&witness=1&witnessArchive=1'])assert.equal(witnessArchiveEnabled(url),false);
 const a=new WitnessArchive({href:'http://127.0.0.1/',fetcher:()=>{throw Error('no IO');}});assert.equal(await a.archive(record(),blob()),false);assert.equal(a.snapshot().attempted,0);a.dispose();
});
test('same-origin fixed target receives PNG once and receipt must identify the exact bytes',async()=>{
 const b=blob(),sha=Buffer.from(await crypto.subtle.digest('SHA-256',await b.arrayBuffer())).toString('hex'),calls=[];const a=new WitnessArchive({href,fetcher:async(url,o)=>{calls.push([url,o]);assert.equal(new URL(url).origin,'http://127.0.0.1:54321');assert.equal(o.redirect,'error');assert.equal(o.credentials,'omit');return o.method==='POST'?Response.json({targetMs:20000,filename:'20000_scene.png',bytes:b.size,sha256:sha},{status:201}):Response.json(cap);}});
 const r=record();assert.equal(await a.archive(r,b),true);assert.equal(r.archiveStatus,'archived');assert.equal(r.archiveSHA256,sha);assert.equal(calls[1][0],'http://127.0.0.1:54321/qa/witness/20000');assert.equal(calls[1][1].headers['X-Witness-Archive'],cap.nonce);assert.equal(await a.archive(record(),b),false);assert.equal(calls.length,2);assert.equal(a.snapshot().pending,0);a.dispose();
});
test('malformed capability cannot redirect PNG elsewhere and a mismatched receipt stays failed',async()=>{
 for(const bad of [{...cap,nonce:'bad'},{...cap,targets:[20000]}]){let calls=0;const a=new WitnessArchive({href,fetcher:async()=>{calls++;return Response.json(bad);}}),r=record();assert.equal(await a.archive(r,blob()),false);assert.equal(calls,1);assert.equal(r.archiveStatus,'failed');a.dispose();}
 const a=new WitnessArchive({href,fetcher:async(url,o)=>o.method==='POST'?Response.json({targetMs:20000,filename:'escape.png',bytes:1,sha256:'b'.repeat(64)},{status:201}):Response.json(cap)}),r=record();assert.equal(await a.archive(r,blob()),false);assert.match(r.archiveError,/receipt differs/);a.dispose();
});
test('invalid deadlines, media and backdated capture never request capability or upload',async()=>{
 for(const [r,b] of [[{targetMs:100,actualElapsedMs:100},blob()],[{targetMs:20000,actualElapsedMs:19999},blob()],[record(),new Blob(['no'],{type:'text/plain'})],[record(),new Blob([new ArrayBuffer(8*1048576+1)],{type:'image/png'})]]){const a=new WitnessArchive({href,fetcher:()=>{throw Error('no request');}});assert.equal(await a.archive(r,b),false);assert.equal(a.snapshot().failed,1);a.dispose();}
});
test('dispose while capability is pending prevents PNG submission and records failure without retry',async()=>{
 let finish,calls=0;const a=new WitnessArchive({href,fetcher:()=>{calls++;return new Promise(r=>finish=r);}}),r=record(),pending=a.archive(r,blob());a.dispose();finish(Response.json(cap));assert.equal(await pending,false);assert.equal(calls,1);assert.equal(r.archiveStatus,'failed');assert.equal(await a.archive(r,blob()),false);assert.equal(a.snapshot().pending,0);
});
