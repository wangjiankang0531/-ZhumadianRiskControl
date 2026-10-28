import {categories} from './spatial_catalog.js';
import {areaFromSelection} from './spatial_query_protocol.js';
const messages={SELECT_QUERY_OBJECT:'请先选择一个点标注，或选择已有区域作为多边形范围',SELECT_QUERY_POINT:'圆形和矩形查询需要先选择一个点标注作为中心',SELECT_QUERY_REGION:'多边形查询需要先选择一个已有区域标注',INVALID_QUERY:'查询范围无效。多边形须无自交，最多32个顶点；圆形半径不超过10公里',DATA_CHANGED:'空间数据已变化，请刷新业务数据后重新查询',QUERY_CHANGED:'查询范围或授权已变化，请重新查询',SPATIAL_QUERY_COMPLEXITY_LIMIT:'当前范围的几何计算量过大，请缩小范围或减少复杂对象',DATA_SOURCE_UNAVAILABLE:'空间数据源暂不可用，请稍后重试',FORBIDDEN:'当前账号无此查询权限',AUTH_EXPIRED:'登录已到期，请重新登录',NOT_SUPPORTED:'当前业务服务尚未提供空间范围查询'};
export function createSpatialQueryPanel({parent,context,query,onLocate,doc=document}){
 const el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const section=el('section');section.id='spatial-query';section.className='search-controls';section.hidden=true;
 section.append(el('h2','空间范围查询'));
 const form=el('form');form.style.cssText='display:grid;gap:8px';section.append(form);
 function field(name,node){const label=el('label',name);label.append(node);form.append(label);return label;}
 const shape=el('select');shape.setAttribute('aria-label','查询范围形状');for(const [value,label] of [['circle','圆形'],['rectangle','矩形'],['polygon','已有区域多边形']]){const o=el('option',label);o.value=value;shape.append(o);}field('查询形状',shape);
 const hint=el('p','圆形和矩形以当前选中的点为中心；多边形使用选中的已有区域。');form.append(hint);
 const radius=el('input');radius.type='number';radius.min='0.1';radius.max='10000';radius.step='0.1';radius.value='200';radius.setAttribute('aria-label','圆形半径 米');
 const radiusField=field('圆形半径 米',radius),presets=el('div');presets.style.cssText='display:flex;gap:6px';
 for(const [label,value] of [['200米',200],['10公里',10000]]){const b=el('button',label);b.type='button';b.onclick=()=>{radius.value=String(value);invalidate();};presets.append(b);}form.append(presets);
 const width=el('input'),height=el('input');for(const n of [width,height]){n.type='number';n.min='0.1';n.step='0.1';n.value='400';}
 width.setAttribute('aria-label','矩形宽度 米');height.setAttribute('aria-label','矩形高度 米');const widthField=field('矩形宽度 米',width),heightField=field('矩形高度 米',height);
 const category=el('select');category.setAttribute('aria-label','查询对象类别');for(const [value,label] of [['','全部类别'],...Object.entries(categories),['unregistered','未分类标注']]){const o=el('option',label);o.value=value;category.append(o);}field('对象类别',category);
 const submit=el('button','查询范围内对象');submit.type='submit';form.append(submit);
 const status=el('p','选择标注后设置查询范围');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('data-testid','spatial-query-status');section.append(status);
 const summary=el('p'),results=el('div'),pager=el('div');results.setAttribute('data-testid','spatial-query-results');pager.style.cssText='display:flex;gap:6px';section.append(summary,results,pager,el('p','按水平相交范围查询；不是路线距离或事故影响范围。结果来自授权文件快照。'));
 parent.append(section);let available=false,busy=false,serial=0,active=null;
 function clear(){serial++;active=null;results.replaceChildren();pager.replaceChildren();summary.textContent='';status.textContent='选择标注后设置查询范围';}
 function invalidate(){clear();radiusField.hidden=presets.hidden=shape.value!=='circle';widthField.hidden=heightField.hidden=shape.value!=='rectangle';}
 for(const n of [shape,radius,width,height,category])n.addEventListener('change',invalidate);invalidate();
 async function run(offset=0,paging=false){
  if(!available||busy)return;busy=true;submit.disabled=true;const generation=++serial;
  try{
   const current=context();if(!current?.document||!current.datasetVersion)throw Object.assign(Error(),{code:'DATA_CHANGED'});
   const saved=paging?active:null;
   if(paging&&!saved)throw Object.assign(Error(),{code:'QUERY_CHANGED'});
   const area=saved?.area??areaFromSelection(current.feature,{shape:shape.value,radius:Number(radius.value),width:Number(width.value),height:Number(height.value)});
   const kind=saved?.category??(category.value||null),name=saved?.name??current.feature.name;
   status.textContent='正在查询授权范围内的对象…';results.replaceChildren();pager.replaceChildren();summary.textContent='';
   const data=await query(area,{document:current.document,datasetVersion:current.datasetVersion,offset,limit:20,category:kind,...(saved?{queryVersion:saved.queryVersion}:{})});
   if(generation!==serial||!available||context()?.document!==current.document||context()?.datasetVersion!==current.datasetVersion)return;
   active={...data,category:kind,name};status.textContent=`共 ${data.total} 个匹配对象 · 第 ${offset+1>data.total?0:offset+1}–${Math.min(offset+20,data.total)} 个`;
   summary.textContent=`${name} · ${area.type==='circle'?`半径 ${area.radiusMeters} 米`:area.type==='rectangle'?'矩形范围':'已有区域范围'} · `+Object.entries(data.counts).map(([key,value])=>`${categories[key]??'未分类'} ${value}`).join('，');
   for(const item of data.items){const b=el('button',`${categories[item.category]??'未分类'} · ${item.name}`);b.type='button';b.className='feature';b.setAttribute('data-query-object',item.id);b.onclick=()=>{if(context()?.datasetVersion!==data.datasetVersion){clear();status.textContent=messages.DATA_CHANGED;return;}onLocate(item.id);};results.append(b);}
   for(const [label,next,enabled] of [['上一页',Math.max(0,offset-20),offset>0],['下一页',offset+20,offset+20<data.total]]){const b=el('button',label);b.type='button';b.disabled=!enabled;b.onclick=()=>run(next,true);pager.append(b);}
  }catch(error){if(generation===serial){active=null;results.replaceChildren();pager.replaceChildren();summary.textContent='';status.textContent=messages[error.code]??'查询未完成，请稍后重试';}}
  finally{busy=false;submit.disabled=!available;}
 }
 form.onsubmit=event=>{event.preventDefault();active=null;run();};
 return {element:section,clear,setAvailable(value){available=Boolean(value);section.hidden=!available;submit.disabled=!available;if(!available)clear();}};
}
