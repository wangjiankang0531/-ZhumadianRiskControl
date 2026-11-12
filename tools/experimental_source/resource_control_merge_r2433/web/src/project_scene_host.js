import{createResourceProjectHost}from'./resource_project_host.js';
import{readJSON}from'./http_json.js';
// The normal project getToken() is supplied by the original host, in memory only.
const failure=code=>Object.assign(Error(code),{code});
const credential=v=>typeof v==='string'&&/^[\x21-\x7e][\x20-\x7e]{0,16383}$/.test(v)&&v.trim()===v;
const safeCode=e=>typeof e?.code==='string'&&/^[A-Z_]{1,80}$/.test(e.code)?e.code:'CLOUD_HOST_FAILED';
export function createProjectSceneHost({frame,authorizationProvider,origin=location.origin,development=false,onState=()=>{},pollMs=250,readyTimeoutMs=60000,events=globalThis.document,mode='edit',topic=mode==='edit'?'layer-edit':'all',resourceRequest=null,onTopicRequest=null,resourceEndpoint=undefined}){
 if(resourceRequest!==null&&typeof resourceRequest!=='function')throw failure('CLOUD_CONFIGURATION_INVALID');
 if(onTopicRequest!==null&&typeof onTopicRequest!=='function')throw failure('CLOUD_CONFIGURATION_INVALID');
 if(topic==='resource-management')return createResourceProjectHost({frame,authorizationProvider,origin,development,onState,pollMs,readyTimeoutMs,events,mode,onTopicRequest,endpoint:resourceEndpoint});
 if(!['edit','view'].includes(mode)||!frame||typeof frame.addEventListener!=='function'||typeof frame.removeEventListener!=='function'||typeof authorizationProvider!=='function'||typeof onState!=='function'||!Number.isFinite(pollMs)||pollMs<10||pollMs>1000||!Number.isFinite(readyTimeoutMs)||readyTimeoutMs<100||readyTimeoutMs>120000)throw failure('CLOUD_CONFIGURATION_INVALID');
 let approved;try{approved=new URL(origin);}catch{throw failure('CLOUD_CONFIGURATION_INVALID');}
 if(approved.origin!==origin||!(origin==='https://www.joinlinksmart.com'||development===true&&approved.protocol==='http:'&&approved.hostname==='127.0.0.1'))throw failure('CLOUD_CONFIGURATION_INVALID');
 const connectName=mode==='edit'?'connectCloudEditor':'connectCloudLayers',disconnectName=mode==='edit'?'disconnectCloudEditor':'disconnectCloudLayers',stateName=mode==='edit'?'cloudEditorState':'cloudLayerState';
 const allowedTopics=new Set(['all','portrait','monitoring','closed','emergency','energy','layer-edit','scene-edit','resource-management']);
 if(typeof topic!=='string'||!allowedTopics.has(topic))throw failure('CLOUD_CONFIGURATION_INVALID');
 const target=new URL('/zhumadian/scene/',origin);target.search=new URLSearchParams({topic,...(mode==='edit'?{edit:'1'}:{}),quality:'high',projectHost:'1'}).toString();
 function approvedSceneHref(href){
  let peer;try{peer=new URL(href);}catch{return false;}
  const topic=peer.searchParams.get('topic');if(!allowedTopics.has(topic)||peer.searchParams.getAll('topic').length!==1)return false;
  const expected=new URL(target.href);expected.searchParams.set('topic',topic);
  if(peer.searchParams.has('scene')){if(peer.searchParams.getAll('scene').length!==1||peer.searchParams.get('scene')!=='tianjin-reference')return false;expected.searchParams.set('scene','tianjin-reference');}
  return peer.href===expected.href;
 }
 let epoch=0,running=false,disposed=false,established=false,modelsConnected=false,bound=null,viewer=null,sourceAccess=null,pending=null,timer=null,last={state:'idle',mode};
 let retiring=Promise.resolve(),retirementActive=false,retireGeneration=0;const resourceRequests=new Set();
 const emit=value=>{last={...value,mode};if(!disposed)onState({...last});};
 function wipe(code){
  const oldSource=sourceAccess;sourceAccess=null;try{oldSource?.close(code);}catch{}
  const old=viewer;viewer=null;bound=null;established=false;clearTimeout(timer);timer=null;modelsConnected=false;
  for(const control of resourceRequests)control.abort();resourceRequests.clear();
  const closing=[];let resourceClosing=null;
  try{resourceClosing=old?.disconnectClientResources?.();if(resourceClosing?.then)closing.push(resourceClosing);}catch{}
  try{const value=old?.disconnectCloudModels?.();if(value?.then)closing.push(value);}catch{}
  try{const value=old?.[disconnectName]();if(value?.then)closing.push(value);}catch{}
  const clear=()=>{if(viewer===null)try{frame.src='about:blank';}catch{}};
  if(!resourceClosing?.then)clear();
  const release=++retireGeneration;retirementActive=true;retiring=Promise.allSettled([retiring,...closing]).then(()=>{clear();if(release===retireGeneration)retirementActive=false;});return retiring;
 }
 function stop(code='CLOUD_HOST_CLOSED'){epoch++;running=false;const closed=wipe(code);emit({state:'signed-out',code});return closed;}
 function checkLocation({initial=false}={}){try{const peer=frame.contentWindow;if(!peer)throw failure('CLOUD_HOST_PEER_INVALID');const href=peer.location.href;if(initial&&href==='about:blank')return null;if(!approvedSceneHref(href))throw failure('CLOUD_HOST_PEER_INVALID');return peer;}catch(e){throw failure(safeCode(e)==='CLOUD_HOST_FAILED'?'CLOUD_HOST_PEER_INVALID':safeCode(e));}}
 function readCredential(){let value;try{value=authorizationProvider();}catch{throw failure('CLOUD_LOGIN_REQUIRED');}if(!credential(value))throw failure('CLOUD_LOGIN_REQUIRED');return value;}
 function checkSession(){const state=viewer?.[stateName];if(!state||state.running!==true){const code=state?.code??(state?.state==='revoked'?'CLOUD_HOST_SESSION_REVOKED':'CLOUD_HOST_SESSION_CLOSED');throw failure(safeCode({code}));}if(modelsConnected){const model=viewer?.cloudModelState;if(!model?.running)throw failure(safeCode({code:model?.code??'CLOUD_MODEL_SESSION_CLOSED'}));}return state;}
 function guard(own){if(!running||own!==epoch||disposed)throw failure('CLOUD_LOGIN_REQUIRED');try{const current=readCredential();if(current!==bound)throw failure('CLOUD_ACCOUNT_CHANGED');const peer=checkLocation();if(peer.hongtuViewer!==viewer)throw failure('CLOUD_HOST_PEER_INVALID');if(sourceAccess&&(peer.hongtuSourceAccess!==sourceAccess||sourceAccess.state?.state!=='connected'))throw failure(sourceAccess.state?.code??'CLOUD_SOURCE_SESSION_CLOSED');if(established)checkSession();return current;}catch(e){stop(safeCode(e));throw failure(safeCode(e));}}
 function guardSource(own,peer,bridge){if(!running||own!==epoch||disposed)throw failure('CLOUD_LOGIN_REQUIRED');try{const current=readCredential();if(current!==bound)throw failure('CLOUD_ACCOUNT_CHANGED');if(checkLocation()!==peer||peer.hongtuSourceAccess!==bridge||bridge!==sourceAccess)throw failure('CLOUD_HOST_PEER_INVALID');if(viewer&&peer.hongtuViewer!==viewer)throw failure('CLOUD_HOST_PEER_INVALID');if(bridge.state?.state!=='connected')throw failure(bridge.state?.code??'CLOUD_SOURCE_SESSION_CLOSED');if(established)checkSession();return current;}catch(e){stop(safeCode(e));throw failure(safeCode(e));}}
 function schedule(own){clearTimeout(timer);if(!running||own!==epoch)return;timer=setTimeout(()=>{try{guard(own);const state=checkSession(),access=mode==='view'||state.writeBlocked||viewer?.cloudModelState?.writeBlocked?'read-only':'edit';if(last.access!==access)emit({state:'ready',access});schedule(own);}catch{}},pollMs);}
 const onTopicNavigation=event=>{const value=event.detail;if(event.target!==frame||!value||Object.keys(value).length!==1||!allowedTopics.has(value.topic))return;try{guard(epoch);onTopicRequest?.(value.topic);}catch{}};frame.addEventListener('xnby-topic-request',onTopicNavigation);
 const onVisible=()=>{if(running&&viewer)try{guard(epoch);}catch{}};const onLoad=()=>{if(running&&viewer)try{guard(epoch);}catch{}};frame.addEventListener('load',onLoad);events?.addEventListener('visibilitychange',onVisible);
 async function start(){
  if(disposed)throw failure('CLOUD_HOST_CLOSED');if(retirementActive){const requested=epoch;await retiring;if(disposed)return false;if(pending&&running)return pending;if(requested!==epoch)return false;}if(pending)return pending;if(running&&viewer){guard(epoch);return true;}
  let token;try{token=readCredential();}catch(e){emit({state:'signed-out',code:safeCode(e)});throw e;}
  const own=++epoch;running=true;bound=token;established=false;emit({state:'loading'});frame.src=target.href;
  const work=(async()=>{const deadline=Date.now()+readyTimeoutMs;while(true){if(disposed||!running||own!==epoch)return false;const current=readCredential();if(current!==bound)throw failure('CLOUD_ACCOUNT_CHANGED');const peer=checkLocation({initial:true});if(peer?.hongtuSourceAccess){const bridge=peer.hongtuSourceAccess;if(sourceAccess&&sourceAccess!==bridge)throw failure('CLOUD_HOST_PEER_INVALID');if(!sourceAccess){if(typeof bridge.connect!=='function'||typeof bridge.close!=='function')throw failure('CLOUD_HOST_PEER_INVALID');sourceAccess=bridge;bridge.connect({origin,development,authorizationProvider:()=>guardSource(own,peer,bridge)});}if(bridge.state?.state!=='connected')throw failure(bridge.state?.code??'CLOUD_SOURCE_SESSION_CLOSED');}if(peer?.document?.readyState==='complete'&&peer.hongtuViewer?.document&&typeof peer.hongtuViewer[connectName]==='function'&&typeof peer.hongtuViewer[disconnectName]==='function'){viewer=peer.hongtuViewer;break;}if(Date.now()>=deadline)throw failure('CLOUD_HOST_NOT_READY');await new Promise(r=>setTimeout(r,50));}
   const active=viewer;await active[connectName]({origin,development,authorizationProvider:()=>guard(own)});
   while(true){if(disposed||!running||own!==epoch)return false;guard(own);const state=checkSession();if(mode==='edit'||Number.isInteger(state.revision)&&state.revision>=0)break;if(Date.now()>=deadline)throw failure('CLOUD_HOST_NOT_READY');await new Promise(r=>setTimeout(r,50));}
   if(typeof active.connectCloudModels!=='function'||typeof active.disconnectCloudModels!=='function')throw failure('CLOUD_MODEL_SYNC_NOT_INSTALLED');
   await active.connectCloudModels({origin,development,authorizationProvider:()=>guard(own),readOnly:mode==='view'});
   if(disposed||!running||own!==epoch)return false;modelsConnected=true;guard(own);
   if(resourceRequest){
    if(typeof active.connectClientResources!=='function'||typeof active.disconnectClientResources!=='function')throw failure('CLOUD_RESOURCE_SYNC_NOT_INSTALLED');
    const request=async(route,options={})=>{
     guard(own);
     const method=options.method??'GET',relative=typeof route==='string'?route.slice('api/client-resources/v1/'.length):'';
     const read=method==='GET'&&/^(configuration|reports|audits\/[a-f0-9]{32}|reports\/[a-f0-9]{32})$/.test(relative);
     const write=method==='POST'&&/^(configuration|audits|audits\/[a-f0-9]{32}\/cancel)$/.test(relative);
     if(typeof route!=='string'||!route.startsWith('api/client-resources/v1/')||!(read||write)||read&&options.body!==undefined||write&&(typeof options.body!=='string'||new TextEncoder().encode(options.body).length>8192))throw failure('RESOURCE_ROUTE_INVALID');
     const control=new AbortController();resourceRequests.add(control);const abort=()=>control.abort();options.signal?.addEventListener('abort',abort,{once:true});if(options.signal?.aborted)control.abort();
     let response;
     try{response=await resourceRequest(route,{method,signal:control.signal,...(options.body===undefined?{}:{body:options.body,headers:{'Content-Type':'application/json'}})});guard(own);
      if(response.status===401||response.status===403){try{await response.body?.cancel();}catch{}guard(own);return new Response('{}',{status:response.status,headers:{'Content-Type':'application/json'}});}
      const{document}=await readJSON(response,262144);guard(own);return new Response(JSON.stringify(document),{status:response.status,headers:{'Content-Type':'application/json'}});
     }
     catch(error){try{await response?.body?.cancel();}catch{}throw failure(safeCode(error));}
     finally{resourceRequests.delete(control);options.signal?.removeEventListener('abort',abort);}
    };
    await active.connectClientResources({request});if(disposed||!running||own!==epoch)return false;guard(own);
   }
   established=true;guard(own);const state=checkSession();emit({state:'ready',access:mode==='view'||state.writeBlocked||viewer?.cloudModelState?.writeBlocked?'read-only':'edit'});schedule(own);return true;
  })().catch(e=>{if(own===epoch){running=false;epoch++;wipe(safeCode(e));emit({state:'error',code:safeCode(e)});}throw failure(safeCode(e));}).finally(()=>{if(pending===work)pending=null;});pending=work;return work;
 }
 return Object.freeze({start,stop,get state(){return {...last};},dispose(){if(disposed)return retiring;const closed=stop();disposed=true;frame.removeEventListener('load',onLoad);frame.removeEventListener('xnby-topic-request',onTopicNavigation);events?.removeEventListener('visibilitychange',onVisible);return closed;}});
}
