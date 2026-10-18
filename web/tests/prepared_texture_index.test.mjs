import test from 'node:test';
import assert from 'node:assert/strict';
import {PreparedTextureIndex} from '../src/prepared_texture_index.js';
import {SourcePageBudget,sourceRestorationFootprint} from '../src/source_page_budget.js';
const source='a'.repeat(64),payload='b'.repeat(64),part={files:[{name:'atlas.jpg',sha256:source}]};
const value=()=>({schema:'xnby.prepared_texture_index.v1',entries:[{sourceSHA256:source,payloadSHA256:payload}]});
test('prepared index derives only same-origin hash paths below the application',async()=>{
 const calls=[];const index=new PreparedTextureIndex(value(),'https://example.test/view/?inspect=1',async(url,options)=>{calls.push([url,options]);return {ok:true,json:async()=>({sourceSHA256:source,payloadSHA256:payload}),arrayBuffer:async()=>new ArrayBuffer(8)};});
 assert.equal(index.has(part),true);assert.equal(index.has({files:[]}),false);
 assert.deepEqual(await index.manifest(part),{sourceSHA256:source,payloadSHA256:payload});assert.equal((await index.payload(part)).byteLength,8);
 assert.equal(calls[0][0],`https://example.test/view/prepared-textures/${source}/${payload}/manifest.json`);assert.equal(calls[1][1].cache,'no-store');
 assert.throws(()=>index.url(part,'../../secret'));assert.throws(()=>index.url({files:[]},'texture.bc7'));
});
test('duplicate, malformed and changed descriptor identities fail closed',async()=>{
 for(const change of [v=>v.entries.push(v.entries[0]),v=>v.entries[0].sourceSHA256='../path',v=>v.entries[0].payloadSHA256='x',v=>v.schema='other']){const v=value();change(v);assert.throws(()=>new PreparedTextureIndex(v,'http://localhost/'));}
 const index=new PreparedTextureIndex(value(),'http://localhost/',async()=>({ok:true,json:async()=>({sourceSHA256:source,payloadSHA256:'c'.repeat(64)})}));await assert.rejects(index.manifest(part),/differs from index/);
});
test('browser fetch is invoked without a foreign index receiver',async()=>{
 let calls=0;const index=new PreparedTextureIndex(value(),'http://localhost/',function(){assert.equal(this,undefined);calls++;return Promise.resolve({ok:true,json:async()=>({sourceSHA256:source,payloadSHA256:payload}),arrayBuffer:async()=>new ArrayBuffer(1)});});
 await index.manifest(part);await index.payload(part);assert.equal(calls,2);
});
test('one source ledger counts concurrent old cut, full candidate, restore and target',()=>{
 const ledger=new SourcePageBudget(100),target=ledger.reserve({format:'upload_target',bytes:4}),old=ledger.reserve({format:'rgba8',bytes:52}),candidate=ledger.reserve({format:'bc7',bytes:24});
 assert.throws(()=>ledger.reserve({format:'geometry',bytes:21}),/budget exceeded/);assert.equal(ledger.held,80);
 const restore=ledger.reserve({format:'rgba8',bytes:20});assert.equal(ledger.peak,100);restore.release();restore.release();assert.equal(ledger.held,80);
 candidate.release();old.release();target.release();assert.equal(ledger.held,0);assert.equal(ledger.admissions,ledger.releases);
 assert.throws(()=>ledger.reserve({format:'rgba8',bytes:-1}));assert.equal(ledger.held,0);
});
test('restore footprint keeps all old roots until commit and deduplicates missing pages',()=>{
 const bundle={},part={directory:'part_000',gpu_payload_bytes:20},frontier={bytes:70,rollbackPlan:()=>({missingPages:[{bundle,part}]})},residents=new Map([[1,{frontier}],[2,{frontier:{bytes:15}}]]);
 assert.equal(sourceRestorationFootprint(residents,[{root:1,parent:'a'},{root:1,parent:'b'},{root:2,parent:null}]),105);
 assert.equal(sourceRestorationFootprint(residents,[{root:2,parent:null}]),85);
});

test('rejected compressed source remains on fallback for this index without changing files or other identities',()=>{
 const v=value(),other='c'.repeat(64);v.entries.push({sourceSHA256:other,payloadSHA256:'d'.repeat(64)});const index=new PreparedTextureIndex(v,'http://localhost/');assert.equal(index.reject(part),true);assert.equal(index.has(part),false);assert.equal(index.reject(part),false);assert.throws(()=>index.url(part,'texture.bc7'));assert.equal(index.has({files:[{name:'atlas.jpg',sha256:other}]}),true);assert.equal(v.entries.length,2);assert.equal(new PreparedTextureIndex(v,'http://localhost/').has(part),true);assert.throws(()=>index.reject({files:[]}));
});
