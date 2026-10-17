import spatialTypes from '../../shared/spatial_types.json' with {type:'json'};
export const topics=Object.freeze(spatialTypes.topics);
export const categories=Object.freeze(Object.fromEntries(Object.entries(spatialTypes.categories).map(([key,item])=>[key,item.name])));
const defaults=Object.fromEntries(Object.entries(spatialTypes.categories).map(([key,item])=>[key,item.defaultTopics]));
export const defaultTopics = category => [...(defaults[category]??[])];
// Grouping, names and style changes preserve the registration; geometry and business identity changes invalidate it.
export async function documentFingerprint(document) {
  const objects=document.layers.flatMap(l=>l.features).map(f=>({id:f.id,type:f.type,positions:f.positions,
    business:f.business?{objectType:f.business.objectType,businessId:f.business.businessId,sourceSystem:f.business.sourceSystem,enterpriseId:f.business.enterpriseId||null}:null}))
    .sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  const raw=new TextEncoder().encode(JSON.stringify({schema:'xnby.spatial.fingerprint.v1',scene:document.scene,coordinates:{srs:document.coordinates.srs,unit:document.coordinates.unit,axes:document.coordinates.axes,origin:document.coordinates.origin},objects}));
  if(!globalThis.crypto?.subtle)throw Error('浏览器无法校验图层，请使用HTTPS或本机地址访问');
  const hash=await crypto.subtle.digest('SHA-256',raw);
  return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
const plain = value => value && typeof value==='object' && !Array.isArray(value);
export function parseSpatialCatalog(document,filename='空间对象目录') {
  const keys=['schema','scene','layerFingerprint','exportedAt','objects'];
  if(!plain(document)||Object.keys(document).some(k=>!keys.includes(k))||document.schema!=='xnby.spatial.catalog.v1'||document.scene!=='zhumadian')throw Error('空间对象目录格式无效');
  if(typeof document.layerFingerprint!=='string'||!/^[0-9a-f]{64}$/.test(document.layerFingerprint))throw Error('图层校验码无效');
  if(typeof document.exportedAt!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(document.exportedAt)||!Number.isFinite(Date.parse(document.exportedAt))||new Date(document.exportedAt).toISOString()!==document.exportedAt.replace(/Z$/,document.exportedAt.includes('.')?'Z':'.000Z'))throw Error('目录导出时间须为有效UTC时间');
  if(!Array.isArray(document.objects)||document.objects.length>10000)throw Error('空间对象目录数量无效');
  const byId=new Map();
  for(const input of document.objects) {
    if(!plain(input)||Object.keys(input).some(k=>!['spatialId','category','themes'].includes(k))||typeof input.spatialId!=='string'||!input.spatialId||new TextEncoder().encode(input.spatialId).length>256||/[\x00-\x1f\x7f]/.test(input.spatialId)||byId.has(input.spatialId))throw Error('空间编号无效或重复');
    if(!Object.hasOwn(categories,input.category))throw Error('空间对象类别无效');
    const themes=input.themes??defaultTopics(input.category);
    if(!Array.isArray(themes)||themes.length<1||themes.length>5||new Set(themes).size!==themes.length||themes.some(t=>!Object.hasOwn(topics,t)))throw Error('专题归属无效或重复');
    byId.set(input.spatialId,{spatialId:input.spatialId,category:input.category,themes:[...themes]});
  }
  return {filename,layerFingerprint:document.layerFingerprint,exportedAt:document.exportedAt,byId};
}
export function spatialObject(feature,catalog=null) {
  const registered=catalog?.byId.get(feature.id);
  const category=registered?.category??feature.business?.objectType??'unregistered';
  return {id:feature.id,name:feature.name,category,themes:registered?.themes??defaultTopics(category),
    registration:registered?'目录登记':feature.business?'业务关联分类':'未分类',business:feature.business??null};
}
export function inTopic(feature,topic,catalog=null) {return topic==='all'||spatialObject(feature,catalog).themes.includes(topic);}
export function scopedObjects(layers,topic='all',category='all',catalog=null) {
  return (layers??[]).flatMap(layer=>layer.features.filter(feature=>inTopic(feature,topic,catalog)&&(category==='all'||spatialObject(feature,catalog).category===category)).map(feature=>({feature,layer})));
}
export function topicCounts(layers,catalog=null) {return Object.fromEntries(['all',...Object.keys(topics)].map(t=>[t,scopedObjects(layers,t,'all',catalog).length]));}
export function catalogOrphans(layers,catalog) {const ids=new Set((layers??[]).flatMap(l=>l.features.map(f=>f.id)));return [...(catalog?.byId.keys()??[])].filter(id=>!ids.has(id));}
