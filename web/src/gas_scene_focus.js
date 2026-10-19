// Only opaque event identity/version crosses the page boundary. No token or guessed coordinates.
const fail=code=>Object.assign(Error(code),{code});
const key='xnby.gas.scene-focus.v1';
const spatialId=id=>typeof id==='string'&&id.length<=128&&!!id.trim()&&!/[\x00-\x1f\x7f]/u.test(id);
const valid=r=>r&&typeof r.id==='string'&&/^[a-f0-9]{32}$/.test(r.id)&&Number.isInteger(r.revision)&&r.revision>=1&&r.revision<=10000&&(r.objectId===undefined&&r.radius===undefined||spatialId(r.objectId)&&Number.isInteger(r.radius)&&r.radius>=1&&r.radius<=5000);
export function gasSceneLink(event,target=null){const r={id:event?.id,revision:event?.revision,...(target?{objectId:target.id,radius:target.radius}:{})};if(!valid(r))throw fail('DATA_INVALID');return '/?'+new URLSearchParams({gasEvent:r.id,gasRevision:String(r.revision),...(target?{gasObject:r.objectId,gasRadius:String(r.radius)}:{})});}
export function gasSceneRequest(url){
 const p=url.searchParams;if(!['gasEvent','gasRevision','gasObject','gasRadius'].some(k=>p.has(k)))return null;
 if(p.getAll('gasEvent').length!==1||p.getAll('gasRevision').length!==1||!/^[1-9][0-9]{0,4}$/.test(p.get('gasRevision'))||['code','state','error'].some(k=>p.has(k)))throw fail('DATA_INVALID');
 let target={};if(p.has('gasObject')||p.has('gasRadius')){if(p.getAll('gasObject').length!==1||p.getAll('gasRadius').length!==1||!/^[1-9][0-9]{0,3}$/.test(p.get('gasRadius')))throw fail('DATA_INVALID');target={objectId:p.get('gasObject'),radius:Number(p.get('gasRadius'))};}
 const r={id:p.get('gasEvent'),revision:Number(p.get('gasRevision')),...target};if(!valid(r))throw fail('DATA_INVALID');return r;
}
export function rememberGasScene(storage,request,authorizationUrl,redirectUri,now=Date.now()){
 storage.removeItem(key);if(!request)return;if(!valid(request))throw fail('DATA_INVALID');
 const state=new URL(authorizationUrl).searchParams.get('state');if(!state||state.length>128)throw fail('LOGIN_INVALID');
 storage.setItem(key,JSON.stringify({request,state,redirectUri,at:now}));
}
export function resumeGasScene(storage,callback,now=Date.now()){
 const raw=storage.getItem(key);storage.removeItem(key);if(raw===null)return null;
 let t;try{t=JSON.parse(raw);}catch{throw fail('LOGIN_INVALID');}
 if(!t||!valid(t.request)||!Number.isFinite(t.at)||now<t.at||now-t.at>300000||callback.origin+callback.pathname!==t.redirectUri||callback.searchParams.getAll('state').length!==1||callback.searchParams.get('state')!==t.state)throw fail('LOGIN_INVALID');
 return t.request;
}
export function gasSceneTarget(payload,request,document,datasetVersion){
 if(!valid(request)||payload?.eventId!==request.id||payload.eventRevision!==request.revision||typeof datasetVersion!=='string'||!/^[a-f0-9]{64}$/.test(datasetVersion)||payload.datasetVersion!==datasetVersion||JSON.stringify(payload.coordinates)!==JSON.stringify(document.coordinates))throw fail('DATA_CHANGED');
 const point=request.objectId?payload.target:payload.point;if(request.objectId&&(point?.id!==request.objectId||payload.radiusMeters!==request.radius))throw fail('DATA_CHANGED');
 if(!point||!['point','line','region'].includes(point.type)||typeof point.id!=='string'||!Array.isArray(point.positions)||point.positions.length<({point:1,line:2,region:3}[point.type])||point.positions.length>1000||point.type==='point'&&point.positions.length!==1||point.positions.some(p=>!Array.isArray(p)||p.length!==3||p.some(n=>!Number.isFinite(n))))throw fail('DATA_INVALID');
 const matches=document.layers.flatMap(layer=>layer.features.filter(f=>f.id===point.id).map(feature=>({feature,layer})));
 if(matches.length!==1||matches[0].feature.type!==point.type||matches[0].feature.name!==point.name||JSON.stringify(matches[0].feature.positions)!==JSON.stringify(point.positions))throw fail('DATA_CHANGED');
 if(!matches[0].layer.visible)throw fail('POINT_HIDDEN');return matches[0];
}
