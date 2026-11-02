import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveSourceBudget,loadSourceBudgetPolicy} from '../src/source_budget_policy.js';
import {SourcePageBudget} from '../src/source_page_budget.js';
import {portalConfiguration} from '../src/oauth_login.js';
test('2 GiB uses exact safe integer bytes without signed 32-bit overflow',()=>{
 const policy=resolveSourceBudget({configuredMiB:2048});assert.equal(policy.bytes,2147483648);const ledger=new SourcePageBudget(policy.bytes),a=ledger.reserve({format:'test',bytes:2147483647});assert.equal(ledger.held,2147483647);assert.throws(()=>ledger.reserve({format:'test',bytes:2}));const b=ledger.reserve({format:'test',bytes:1});assert.equal(ledger.held,2147483648);a.release();b.release();assert.equal(ledger.held,0);
});
test('only explicit QA may override the configured resource tier',()=>{
 assert.equal(resolveSourceBudget({configuredMiB:512,requestedMiB:'2048'}).mib,512);assert.equal(resolveSourceBudget({configuredMiB:512,qa:true,requestedMiB:'1024'}).mib,1024);
 for(const value of ['4096','0','-1','2048.0','2e3',' 1024',1024])assert.throws(()=>resolveSourceBudget({qa:true,requestedMiB:value}));for(const value of [0,768,4096,'2048',Infinity,NaN])assert.throws(()=>resolveSourceBudget({configuredMiB:value}));
});
test('legacy configuration preserves the existing budget and network failure stays conservative',async()=>{
 const old=await loadSourceBudgetPolicy({fetchConfig:async()=>({ok:true,json:async()=>({schema:'xnby.portal.config.v1',mode:'local'})})});assert.equal(old.mib,512);assert.equal(old.notice,null);
 const failed=await loadSourceBudgetPolicy({fetchConfig:async()=>{throw Error('offline');}});assert.equal(failed.mib,512);assert.equal(failed.notice,'offline');
});
test('same-origin configuration is read once and malformed profiles cannot enlarge the budget',async()=>{
 const calls=[],body={schema:'xnby.portal.config.v1',mode:'local'},fetchConfig=async(...args)=>{calls.push(args);return {ok:true,headers:{get:()=> '1024'},json:async()=>body};};
 const configured=await loadSourceBudgetPolicy({search:'?sourceBudgetMiB=2048',fetchConfig});assert.equal(configured.mib,1024);assert.equal(calls.length,1);assert.equal(calls[0][0],'application/config.json');assert.equal(calls[0][1].cache,'no-store');
 assert.deepEqual(portalConfiguration(body,'http://127.0.0.1:1234'),{mode:'local'});assert.equal(calls[0][1].credentials,'omit');assert.equal(calls[0][1].redirect,'error');
 const invalid=await loadSourceBudgetPolicy({fetchConfig:async()=>({ok:true,headers:{get:()=> '4096'},json:async()=>body})});assert.equal(invalid.mib,512);assert.ok(invalid.notice);
 const qa=await loadSourceBudgetPolicy({search:'?qa=1&sourceBudgetMiB=2048',fetchConfig});assert.equal(qa.mib,2048);assert.equal(qa.source,'qa_override');
});
