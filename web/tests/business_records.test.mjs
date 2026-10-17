import test from 'node:test';
import assert from 'node:assert/strict';
import {parseBusinessRecords,businessRecordKey,resolveBusinessRecord,businessRecordRows,businessRecordSearchText,businessCoverage} from '../src/business_records.js';
const now=Date.parse('2026-10-13T08:00:00Z');
const binding={sourceSystem:'test-access',objectType:'access',businessId:'TEST-GATE-001',enterpriseId:'TEST-ENTERPRISE-001'};
const record={...binding,name:'测试台账卡口',updatedAt:'2026-10-13T07:00:00Z',attributes:[{label:'运行状态',value:'测试数据'},{label:'容量',value:0},{label:'启用',value:false},{label:'备注',value:null}]};
const document=()=>({schema:'xnby.business.records.v1',scene:'zhumadian',exportedAt:'2026-10-13T07:30:00Z',ttlHours:24,records:[structuredClone(record)]});
test('valid snapshot retains exact IDs and is isolated from caller mutation',()=>{
 const source=document(),catalog=parseBusinessRecords(source,'test.json');source.records[0].name='mutated';
 assert.equal(catalog.byKey.get(businessRecordKey(binding)).name,record.name);
 assert.equal(resolveBusinessRecord(binding,catalog,now).state,'ready');
});
test('full source/type/id key avoids punctuation collisions and cross-system matches',()=>{
 assert.notEqual(businessRecordKey({sourceSystem:'a/b',objectType:'access',businessId:'c'}),businessRecordKey({sourceSystem:'a',objectType:'access',businessId:'b/c'}));
 const catalog=parseBusinessRecords(document());assert.equal(resolveBusinessRecord({...binding,sourceSystem:'other'},catalog,now).state,'missing');
 assert.equal(resolveBusinessRecord({...binding,objectType:'video'},catalog,now).state,'missing');
});
test('unbound, unloaded, missing, conflict, future and stale are explicit states',()=>{
 const catalog=parseBusinessRecords(document());
 assert.equal(resolveBusinessRecord(null,catalog,now).state,'unbound');assert.equal(resolveBusinessRecord(binding,null,now).state,'unloaded');
 assert.equal(resolveBusinessRecord({...binding,businessId:'missing'},catalog,now).state,'missing');
 const conflict=resolveBusinessRecord({...binding,enterpriseId:'other'},catalog,now);assert.equal(conflict.state,'enterprise-mismatch');assert.equal(conflict.record,undefined);
 assert.equal(resolveBusinessRecord(binding,catalog,now+25*3600000).state,'stale');
 assert.equal(resolveBusinessRecord(binding,catalog,now-2*3600000).state,'future');
});
test('record age also controls expiration when export is recent',()=>{
 const doc=document();doc.records[0].updatedAt='2026-10-10T07:00:00Z';assert.equal(resolveBusinessRecord(binding,parseBusinessRecords(doc),now).state,'stale');
});
test('expiry boundary and allowed clock skew remain deterministic',()=>{
 const catalog=parseBusinessRecords(document());assert.equal(resolveBusinessRecord(binding,catalog,Date.parse(record.updatedAt)+24*3600000).state,'ready');
 assert.equal(resolveBusinessRecord(binding,catalog,Date.parse(record.updatedAt)+24*3600000+1).state,'stale');
});
test('empty snapshots are valid and missing is not interpreted as an empty business record',()=>{
 const doc=document();doc.records=[];const catalog=parseBusinessRecords(doc);assert.equal(resolveBusinessRecord(binding,catalog,now).state,'missing');
});
test('details retain zero and false, mark null missing, and do not interpret HTML',()=>{
 const doc=document();doc.records[0].attributes.push({label:'文本',value:'<img src=x onerror=alert(1)>'});
 const rows=businessRecordRows(binding,parseBusinessRecords(doc,'test.json'),now);
 assert.ok(rows.some(([k,v])=>k==='容量'&&v==='0'));assert.ok(rows.some(([k,v])=>k==='启用'&&v==='否'));
 assert.ok(rows.some(([k,v])=>k==='备注'&&v==='未提供'));assert.ok(rows.some(([k,v])=>k==='文本'&&v.startsWith('<img')));
 assert.equal(businessRecordRows(binding,null,now).length,1);
});
test('coverage reports matched, missing and conflicting spatial references independently',()=>{
 const catalog=parseBusinessRecords(document());
 const coverage=businessCoverage([{features:[{business:binding},{business:{...binding,businessId:'missing'}},{business:{...binding,enterpriseId:'other'}},{id:'unbound'}]}],catalog,now);
 assert.deepEqual(coverage,{bound:3,matched:1,missing:1,conflicts:1});
});
const invalids={schema:d=>d.schema='other',scene:d=>d.scene='other',rootField:d=>d.extra=true,invalidDate:d=>d.exportedAt='2026-02-30T07:00:00Z',localDate:d=>d.exportedAt='2026-10-13',ttl:d=>d.ttlHours=0,fractionalTtl:d=>d.ttlHours=1.5,tooMany:d=>d.records=Array(10001).fill(record),duplicate:d=>d.records.push(structuredClone(record)),badId:d=>d.records[0].businessId='bad id',badName:d=>d.records[0].name='',badUpdate:d=>d.records[0].updatedAt='not-a-date',missingAttributes:d=>delete d.records[0].attributes,attributeObject:d=>d.records[0].attributes={},tooManyAttributes:d=>d.records[0].attributes=Array(33).fill({label:'a',value:1}),duplicateLabel:d=>d.records[0].attributes.push({label:'容量',value:1}),nestedValue:d=>d.records[0].attributes[0].value={x:1},nonFinite:d=>d.records[0].attributes[0].value=Infinity,longValue:d=>d.records[0].attributes[0].value='x'.repeat(4097),controlValue:d=>d.records[0].attributes[0].value='bad\u0000',unknownRecordField:d=>d.records[0].url='javascript:alert(1)',unknownAttributeField:d=>d.records[0].attributes[0].extra=true};
for(const [name,change] of Object.entries(invalids))test(`malformed snapshot rejected: ${name}`,()=>{const doc=document();change(doc);assert.throws(()=>parseBusinessRecords(doc));});
