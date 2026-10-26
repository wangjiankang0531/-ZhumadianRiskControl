import {validatePNGIconData} from './png_icon.js';
import {labelOptions} from './label_options.js';
import {validateBusiness} from './business_binding.js';

// Validate without normalizing: saved DLG identity, geometry and styles must survive unchanged.
const record=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);

export function validateLandscapeDocument(doc){
  if(!record(doc))throw Error('图层文档须为对象');
  if(doc.schema!=='hongtu.landscape.layers.v1'||doc.scene!=='zhumadian'||JSON.stringify(doc.coordinates?.origin)!==JSON.stringify([225319.5,3648440.1,30.9])||doc.coordinates?.srs!=='EPSG:32650'||doc.coordinates?.axes!=='east,north,up'||doc.coordinates?.unit!=='metre')throw Error('图层格式或驻马店坐标系不匹配');
  if(!Array.isArray(doc.layers)||doc.layers.length>1000)throw Error('图层数量无效');
  const ids=new Set();let total=0;
  for(const l of doc.layers){if(!record(l)||typeof l.id!=='string'||!l.id||ids.has('l:'+l.id)||typeof l.name!=='string'||typeof l.visible!=='boolean'||typeof l.locked!=='boolean'||!Array.isArray(l.features))throw Error('图层内容无效');ids.add('l:'+l.id);
    for(const f of l.features){if(!record(f)||++total>10000||typeof f.id!=='string'||!f.id||ids.has('f:'+f.id)||typeof f.name!=='string'||!['point','line','region'].includes(f.type)||!Array.isArray(f.positions)||f.positions.length>1000||f.positions.length<(f.type==='point'?1:f.type==='line'?2:3)||(f.type==='point'&&f.positions.length!==1))throw Error('标注内容无效');ids.add('f:'+f.id);
      if(f.positions.some(p=>!Array.isArray(p)||p.length!==3||p.some(v=>!Number.isFinite(v)||Math.abs(v)>100000)))throw Error('标注坐标无效');
      const s=f.style;if(!record(s)||typeof s.color!=='string'||typeof s.fillColor!=='string'||!/^#[\da-f]{6}$/i.test(s.color)||!/^#[\da-f]{6}$/i.test(s.fillColor)||!['solid','dash','dot'].includes(s.pattern)||!['pin','circle','square','star','warning','custom'].includes(s.icon))throw Error('标注样式无效');
      for(const [k,lo,hi] of [['opacity',0,1],['fillOpacity',0,1],['widthPx',.5,32],['sizePx',8,128]])if(!Number.isFinite(s[k])||s[k]<lo||s[k]>hi)throw Error('标注样式数值超出范围');
      if(s.icon==='custom')validatePNGIconData(s.iconData);
      if(f.type==='region')validateRing(f.positions);
      if(Object.hasOwn(f,'business'))validateBusiness(f.business);
      if(Object.hasOwn(f,'label')){const l=f.label;if(!record(l)||typeof l.visible!=='boolean'||typeof l.text!=='string'||new TextEncoder().encode(l.text).length>768||typeof l.color!=='string'||!/^#[\da-f]{6}$/i.test(l.color)||!Number.isFinite(l.fontPx)||l.fontPx<8||l.fontPx>48||!Number.isFinite(l.opacity)||l.opacity<0||l.opacity>1||!Array.isArray(l.offset)||l.offset.length!==2||l.offset.some(v=>!Number.isFinite(v)||Math.abs(v)>1000))throw Error('文字标牌参数无效');labelOptions(l);}
    }}return doc;
}
function validateRing(p){const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);const on=(a,b,c)=>Math.abs(cross(a,b,c))<.0001&&c[0]>=Math.min(a[0],b[0])-.0001&&c[0]<=Math.max(a[0],b[0])+.0001&&c[1]>=Math.min(a[1],b[1])-.0001&&c[1]<=Math.max(a[1],b[1])+.0001;
  let area=0;for(let i=0;i<p.length;i++){const a=p[i],b=p[(i+1)%p.length];if(Math.hypot(a[0]-b[0],a[1]-b[1])<.001)throw Error('区域存在重复顶点');area+=a[0]*b[1]-b[0]*a[1];for(let j=i+1;j<p.length;j++){if(j===i+1||(i===0&&j===p.length-1))continue;const c=p[j],d=p[(j+1)%p.length];if((cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0)||on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b))throw Error('区域边界自相交');}}if(Math.abs(area)<.001)throw Error('区域面积为零');}

// Prepare fully before the viewer releases the current document or browsing state.
export function prepareLandscapeDocument(doc){
  validateLandscapeDocument(doc);
  return structuredClone(doc);
}
