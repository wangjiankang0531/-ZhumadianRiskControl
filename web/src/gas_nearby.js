import {categories} from './spatial_catalog.js';
export const nearbyCategories=Object.freeze({'':'全部类别',...categories,unregistered:'未分类标注'});
export const nearbyCategoryName=name=>categories[name]??'未分类标注';
const fail=()=>Object.assign(Error('DATA_CHANGED'),{code:'DATA_CHANGED'});
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
export function validateNearby(data,query){
 if(!data||data.eventId!==query.id||data.eventRevision!==query.revision||!hash(data.datasetVersion)||query.datasetVersion&&query.datasetVersion!==data.datasetVersion||data.radiusMeters!==query.radius||data.category!==(query.category||null)||data.offset!==query.offset||data.limit!==query.limit||!Number.isInteger(data.total)||data.total<0||data.total>10000||data.distanceMetric!=='horizontal-minimum-metres'||typeof data.businessDetailsAuthorized!=='boolean'||!Array.isArray(data.items)||data.items.length>data.limit||data.offset+data.items.length>data.total&&data.items.length||data.offset<data.total&&data.items.length!==Math.min(data.limit,data.total-data.offset)||!data.counts||typeof data.counts!=='object'||Array.isArray(data.counts))throw fail();
 let count=0;for(const [name,n] of Object.entries(data.counts)){if(name!=='unregistered'&&!Object.hasOwn(categories,name)||!Number.isInteger(n)||n<0||n>10000)throw fail();count+=n;}
 if(count>10000||(!query.category?count!==data.total:(data.counts[query.category]||0)!==data.total))throw fail();
 const ids=new Set();let last=-1;
 for(const item of data.items){
  if(!item||typeof item.id!=='string'||!item.id||ids.has(item.id)||typeof item.name!=='string'||!item.name||!['point','line','region'].includes(item.type)||item.category!=='unregistered'&&!Object.hasOwn(categories,item.category)||query.category&&item.category!==query.category||!['public_basic','enterprise'].includes(item.access)||!Number.isFinite(item.distanceMeters)||item.distanceMeters<0||item.distanceMeters>data.radiusMeters||item.distanceMeters<last||item.access==='public_basic'&&(item.enterpriseId!==undefined||item.businessRecord!==undefined))throw fail();
  ids.add(item.id);last=item.distanceMeters;
  if(item.businessRecord){const r=item.businessRecord;if(!data.businessDetailsAuthorized||item.access!=='enterprise'||r.enterpriseId!==item.enterpriseId||typeof r.name!=='string'||!['ready','stale','future'].includes(r.state)||!Array.isArray(r.attributes)||r.attributes.some(a=>typeof a.label!=='string'||typeof a.value!=='string'))throw fail();}
 }
 return data;
}
