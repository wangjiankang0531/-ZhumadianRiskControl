// Only opaque event identity/version crosses the page boundary. No token or guessed coordinates.
const fail=code=>Object.assign(Error(code),{code});
const key='xnby.gas.scene-focus.v1';
const valid=r=>r&&typeof r.id==='string'&&/^[a-f0-9]{32}$/.test(r.id)&&Number.isInteger(r.revision)&&r.revision>=1&&r.revision<=10000;
export function gasSceneLink(event){const r={id:event?.id,revision:event?.revision};if(!valid(r))throw fail('DATA_INVALID');return '/?'+new URLSearchParams({gasEvent:r.id,gasRevision:String(r.revision)});}
export function gasSceneRequest(url){
 const p=url.searchParams;if(!p.has('gasEvent')&&!p.has('gasRevision'))return null;
 if(p.getAll('gasEvent').length!==1||p.getAll('gasRevision').length!==1||!/^[1-9][0-9]{0,4}$/.test(p.get('gasRevision'))||['code','state','error'].some(k=>p.has(k)))throw fail('DATA_INVALID');
 const r={id:p.get('gasEvent'),revision:Number(p.get('gasRevision'))};if(!valid(r))throw fail('DATA_INVALID');return r;
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
 const point=payload.point;if(!point||point.type!=='point'||typeof point.id!=='string'||!Array.isArray(point.positions)||point.positions.length!==1||!Array.isArray(point.positions[0])||point.positions[0].length!==3||point.positions[0].some(n=>!Number.isFinite(n)))throw fail('DATA_INVALID');
 const matches=document.layers.flatMap(layer=>layer.features.filter(f=>f.id===point.id).map(feature=>({feature,layer})));
 if(matches.length!==1||matches[0].feature.type!=='point'||matches[0].feature.name!==point.name||JSON.stringify(matches[0].feature.positions)!==JSON.stringify(point.positions))throw fail('DATA_CHANGED');
 if(!matches[0].layer.visible)throw fail('POINT_HIDDEN');return matches[0];
}
