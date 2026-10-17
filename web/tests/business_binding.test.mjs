import test from 'node:test';
import assert from 'node:assert/strict';
import {validateBusiness,objectTypeNames,businessDetailRows} from '../src/business_binding.js';
import {matchesFeature} from '../src/annotation_interaction.js';
const valid={objectType:'access',businessId:'TEST-GATE-001',enterpriseId:'TEST-ENTERPRISE-001',sourceSystem:'test-access'};
test('all documented spatial categories accept source-qualified references',()=>{
  assert.equal(Object.keys(objectTypeNames).length,13);
  for(const objectType of Object.keys(objectTypeNames))assert.doesNotThrow(()=>validateBusiness({...valid,objectType}));
});
test('enterprise id is optional; valid Unicode ids retain exact content without mutation',()=>{
  const b={objectType:'enterprise',businessId:'企业-编号',sourceSystem:'企业台账'};
  const before=JSON.stringify(b);assert.equal(validateBusiness(b),b);assert.equal(JSON.stringify(b),before);
  assert.doesNotThrow(()=>validateBusiness({...b,enterpriseId:''}));
});
for(const [name,value] of Object.entries({null:null,array:[],unknown:{...valid,objectType:'unknown'},
  missingId:{objectType:'access',sourceSystem:'test'},emptyId:{...valid,businessId:''},
  numericId:{...valid,businessId:1},emptySource:{...valid,sourceSystem:''},nullEnterprise:{...valid,enterpriseId:null},
  whitespace:{...valid,businessId:'invalid id'},control:{...valid,sourceSystem:'test\n'},
  longId:{...valid,businessId:'x'.repeat(257)},longSource:{...valid,sourceSystem:'x'.repeat(129)},
  utf8Limit:{...valid,businessId:'企'.repeat(86)},unsupported:{...valid,risk:0}})){
  test(`invalid reference rejected: ${name}`,()=>assert.throws(()=>validateBusiness(value)));
}
test('search finds business, enterprise, system and object category while retaining geometry filters',()=>{
  const feature={id:'spatial-1',name:'门禁标注',type:'point',business:valid};const layer={name:'封闭管理'};
  for(const text of ['TEST-GATE-001','TEST-ENTERPRISE-001','test-access','卡口门禁','ｔｅｓｔ－ｇａｔｅ－００１'])assert.equal(matchesFeature(feature,layer,text),true);
  assert.equal(matchesFeature(feature,layer,'TEST-GATE-001','region'),false);
});
test('details distinguish unbound and registered references from live business data',()=>{
  const feature={id:'spatial-1',business:valid};const rows=businessDetailRows(feature);
  assert.ok(rows.some(([k,v])=>k==='空间对象编号'&&v==='spatial-1'));
  assert.ok(rows.some(([k,v])=>k==='业务数据状态'&&v==='仅登记关联，业务数据未接入'));
  assert.deepEqual(businessDetailRows({id:'old-1'}),[['空间对象编号','old-1'],['业务关联','未挂接']]);
});
