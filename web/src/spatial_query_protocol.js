import {categories} from './spatial_catalog.js';
const fail=code=>Object.assign(Error(code),{code});
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const point=p=>Array.isArray(p)&&p.length===2&&p.every(n=>typeof n==='number'&&Number.isFinite(n)&&Math.abs(n)<=1e9);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function normalizeQueryArea(value){
 if(!value||typeof value!=='object'||Array.isArray(value))throw fail('INVALID_QUERY');
 const keys=Object.keys(value).sort().join(','),kind=value.type;
 if(kind==='circle'&&keys==='center,radiusMeters,type'&&point(value.center)&&typeof value.radiusMeters==='number'&&Number.isFinite(value.radiusMeters)&&value.radiusMeters>0&&value.radiusMeters<=10000)return {type:kind,center:[...value.center],radiusMeters:value.radiusMeters};
 if(kind==='rectangle'&&keys==='max,min,type'&&point(value.min)&&point(value.max)&&value.min.every((n,i)=>n<value.max[i]))return {type:kind,min:[...value.min],max:[...value.max]};
 if(kind==='polygon'&&keys==='type,vertices'&&Array.isArray(value.vertices)&&value.vertices.length>=3&&value.vertices.length<=33&&value.vertices.every(point)){
  const vertices=value.vertices.map(p=>[...p]);if(same(vertices[0],vertices.at(-1)))vertices.pop();
  if(vertices.length>=3&&vertices.length<=32&&new Set(vertices.map(p=>JSON.stringify(p))).size===vertices.length)return {type:kind,vertices};
 }
 throw fail('INVALID_QUERY');
}
export function areaFromSelection(feature,{shape='circle',radius=200,width=400,height=400}={}){
 if(!feature||!Array.isArray(feature.positions)||!feature.positions.length)throw fail('SELECT_QUERY_OBJECT');
 if(shape==='polygon'){
  if(feature.type!=='region')throw fail('SELECT_QUERY_REGION');
  return normalizeQueryArea({type:'polygon',vertices:feature.positions.map(p=>p.slice(0,2))});
 }
 if(feature.type!=='point')throw fail('SELECT_QUERY_POINT');
 const center=feature.positions[0].slice(0,2);
 if(shape==='circle')return normalizeQueryArea({type:'circle',center,radiusMeters:radius});
 if(shape==='rectangle'&&[width,height].every(n=>typeof n==='number'&&Number.isFinite(n)&&n>0))return normalizeQueryArea({type:'rectangle',min:[center[0]-width/2,center[1]-height/2],max:[center[0]+width/2,center[1]+height/2]});
 throw fail('INVALID_QUERY');
}
export function validateQueryPage(data,{area,offset,limit,datasetVersion,queryVersion=null,category=null,document}){
 const normalized=normalizeQueryArea(area),known=key=>key==='unregistered'||Object.hasOwn(categories,key);
 if(!data||data.schema!=='xnby.spatial.query.v1'||data.source!=='file_snapshot'||data.matchRule!=='horizontal-intersection-including-boundary'||data.circleBoundaryToleranceMeters!==(normalized.type==='circle'?1e-7:0)||!same(normalizeQueryArea(data.area),normalized)||!hash(data.datasetVersion)||data.datasetVersion!==datasetVersion||!hash(data.queryVersion)||queryVersion&&data.queryVersion!==queryVersion||!same(data.coordinates,document?.coordinates)||!hash(data.layerFingerprint))throw fail('DATA_CHANGED');
 if(!Number.isInteger(data.total)||data.total<0||data.total>10000||data.offset!==offset||data.limit!==limit||!Array.isArray(data.items)||data.items.length!==Math.max(0,Math.min(limit,data.total-offset))||!data.counts||typeof data.counts!=='object'||Array.isArray(data.counts))throw fail('DATA_INVALID');
 let total=0;for(const [key,value] of Object.entries(data.counts)){if(!known(key)||!Number.isInteger(value)||value<=0||value>10000)throw fail('DATA_INVALID');total+=value;}
 if(total>10000||category===null&&total!==data.total||category!==null&&(data.counts[category]??0)!==data.total)throw fail('DATA_INVALID');
 const byId=new Map();for(const layer of document.layers)for(const feature of layer.features){if(byId.has(feature.id))throw fail('DATA_INVALID');byId.set(feature.id,{feature,layer});}
 const ids=new Set(),items=[];
 for(const item of data.items){
  const original=byId.get(item?.id);
  if(!original||ids.has(item.id)||!known(item.category)||category!==null&&item.category!==category||item.name!==original.feature.name||item.type!==original.feature.type||!same(item.positions,original.feature.positions)||item.layer?.id!==original.layer.id)throw fail('DATA_CHANGED');
  ids.add(item.id);items.push({id:item.id,name:item.name,type:item.type,category:item.category,layerId:item.layer.id});
 }
 return {area:normalized,items,total:data.total,offset,limit,counts:{...data.counts},datasetVersion:data.datasetVersion,queryVersion:data.queryVersion,source:data.source};
}
