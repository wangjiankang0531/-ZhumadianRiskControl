// A distinct client-resource capability; public credentials never go to loopback.
import{readJSON}from'./http_json.js';
export const DEFAULT_RESOURCE_ENDPOINT='http://127.0.0.1:18768/xnby-client-resources/v1/';
const official='https://www.joinlinksmart.com',fail=code=>Object.assign(Error(code),{code}),hex=(v,n)=>typeof v==='string'&&new RegExp('^[a-f0-9]{'+n+'}$').test(v);
const exact=(v,keys)=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
export function resourceDeadline(headers,started,received){const text=headers.get('X-XNBY-Local-GIS-Remaining-Ms');if(!/^[1-9][0-9]{0,4}$/.test(text??'')||Number(text)>30000||![started,received].every(Number.isFinite)||received<started||started+Number(text)<=received)throw fail('RESOURCE_LEASE_INVALID');return started+Number(text);}
export function createClientResourceTransport({origin,authorizationProvider,assertProjectActive,endpoint=DEFAULT_RESOURCE_ENDPOINT,development=false,fetcher=fetch,now=()=>performance.now(),timeoutMs=90000,onState=()=>{}}={}){
 let site,local;try{site=new URL(origin);local=new URL(endpoint);}catch{throw fail('RESOURCE_CONFIGURATION_INVALID');}
 const dev=development===true&&site.protocol==='http:'&&site.hostname==='127.0.0.1';
 if(site.origin!==origin||!(origin===official||dev)||local.protocol!=='http:'||local.hostname!=='127.0.0.1'||!local.port||Number(local.port)<1024||local.pathname!=='/xnby-client-resources/v1/'||local.search||local.hash||local.username||local.password||(!dev&&endpoint!==DEFAULT_RESOURCE_ENDPOINT)||typeof authorizationProvider!=='function'||typeof assertProjectActive!=='function'||typeof fetcher!=='function'||typeof now!=='function'||typeof onState!=='function'||!Number.isFinite(timeoutMs)||timeoutMs<10||timeoutMs>120000)throw fail('RESOURCE_CONFIGURATION_INVALID');
 let closed=false,reason=null,bound=null,session=null,descriptor=null,connecting=null,closing=null,timer=null,generation=0,cleanupConfirmed=null;const active=new Set();
 const state=()=>Object.freeze({state:closed?'closed':session?'connected':connecting?'connecting':'waiting',code:reason,cleanupConfirmed,activeRequests:active.size});
 const emit=()=>onState(state());
 async function identity(){try{if(closed)throw fail(reason??'RESOURCE_CONNECTION_CLOSED');if(await assertProjectActive()!==true)throw fail('CLOUD_LOGIN_REQUIRED');let value;try{value=await authorizationProvider();}catch(error){throw fail(error?.code??'CLOUD_LOGIN_REQUIRED');}if(closed||typeof value!=='string'||!value||value.length>16384||value.trim()!==value||!/^[\x20-\x7e]+$/.test(value))throw fail('CLOUD_LOGIN_REQUIRED');if(bound!==null&&value!==bound)throw fail('CLOUD_ACCOUNT_CHANGED');bound=value;return value;}catch(error){if(!closed)await close(error?.code??'CLOUD_LOGIN_REQUIRED');throw error;}}
 function control(signal,limit=timeoutMs){const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),limit);active.add(controller);return{signal:signal?AbortSignal.any([signal,controller.signal]):controller.signal,done(){clearTimeout(timeout);active.delete(controller);}};}
 const localOptions=(options,signal)=>({...options,credentials:'omit',redirect:'error',cache:'no-store',referrerPolicy:'no-referrer',targetAddressSpace:'loopback',signal});
 async function json(response,maximum=262144){const result=await readJSON(response,maximum);await identity();return result.document;}
 function discovery(value){if(!exact(value,['schema','protocolVersion','instanceId','challenge','installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity','ready'])||value.schema!=='xnby.client-resources.discovery.v1'||value.protocolVersion!==1||value.ready!==true||!hex(value.instanceId,32)||!['challenge','installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity'].every(k=>hex(value[k],64)))throw fail('RESOURCE_VERSION_MISMATCH');return{origin:official,instanceId:value.instanceId,challenge:value.challenge,installationIdentity:value.installationIdentity,sourceRuntimeIdentity:value.sourceRuntimeIdentity,sourceIndexIdentity:value.sourceIndexIdentity};}
 function schedule(){clearTimeout(timer);timer=null;if(closed||!session)return;timer=setTimeout(()=>{timer=null;connect(true).catch(error=>close(error?.code??'RESOURCE_RENEWAL_FAILED'));},Math.max(10,(session.deadline-now()-1000)/2));}
 async function connect(renew=false){
  await identity();if(!renew&&session&&session.deadline>now()+1000)return true;if(connecting)return connecting;
  const work=control(undefined,Math.min(timeoutMs,20000)),own=generation;
  const promise=(async()=>{
   const response=await fetcher(local.href+'discovery',localOptions({method:'GET'},work.signal));if(!response.ok)throw fail('RESOURCE_UNAVAILABLE');const expected=discovery(await json(response,8192));
   if(descriptor&&JSON.stringify(expected)!==JSON.stringify(descriptor))throw fail('RESOURCE_SOURCE_CHANGED');
   const token=await identity(),issue=await fetcher(origin+'/zhumadian/api/spatial-sync/v2/client-resources/grants',{method:'POST',headers:{Authorization:token,'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({expected}),credentials:'omit',redirect:'error',cache:'no-store',referrerPolicy:'no-referrer',signal:work.signal});
   if(!issue.ok){try{await issue.body?.cancel();}catch{}throw fail(issue.status===401?'CLOUD_LOGIN_REQUIRED':issue.status===403?'CLOUD_ACCESS_DENIED':'RESOURCE_AUTHORITY_UNAVAILABLE');}
   const grant=await json(issue,8192);if(!exact(grant,['schema','grant','expiresAt'])||grant.schema!=='xnby.client-resources.grant.v1'||!hex(grant.grant,64)||typeof grant.expiresAt!=='number'||!Number.isFinite(grant.expiresAt))throw fail('RESOURCE_GRANT_INVALID');
   const previous=session,started=now(),result=await fetcher(local.href+(previous?'sessions/current':'sessions'),localOptions({method:'POST',headers:{'Content-Type':'application/json',...(previous?{'X-XNBY-Client-Resources-Session':previous.token}:{})},body:JSON.stringify({grant:grant.grant})},work.signal));
   if(result.status!==201){try{await result.body?.cancel();}catch{}throw fail('RESOURCE_SESSION_REJECTED');}
   const value=await json(result,8192),deadline=resourceDeadline(result.headers,started,now());if(!exact(value,['schema','session','instanceId','expiresAt'])||value.schema!=='xnby.client-resources.session.v1'||!hex(value.session,64)||value.instanceId!==expected.instanceId||typeof value.expiresAt!=='number'||!Number.isFinite(value.expiresAt)||closed||own!==generation)throw fail('RESOURCE_SESSION_INVALID');
   session={token:value.session,deadline};descriptor=expected;schedule();emit();return true;
  })().catch(async error=>{await close(error?.code??'RESOURCE_UNAVAILABLE');throw fail(error?.code??'RESOURCE_UNAVAILABLE');}).finally(()=>{work.done();if(connecting===promise)connecting=null;});connecting=promise;emit();return promise;
 }
 async function request(route,options={}){
  const method=options.method??'GET',part=typeof route==='string'&&route.startsWith('api/client-resources/v1/')?route.slice(24):null;
  const read=method==='GET'&&/^(configuration|reports|audits\/[a-f0-9]{32}|reports\/[a-f0-9]{32}|gis\/status|gis\/operations\/[a-f0-9]{32})$/.test(part??''),write=method==='POST'&&/^(configuration|audits|audits\/[a-f0-9]{32}\/cancel|gis\/(start|stop))$/.test(part??'');
  if(!(read||write)||read&&options.body!==undefined||write&&(typeof options.body!=='string'||new TextEncoder().encode(options.body).length>8192))throw fail('RESOURCE_ROUTE_INVALID');
  await connect();await identity();const own=generation,current=session,work=control(options.signal);let response;
  try{response=await fetcher(local.href+part,localOptions({method,headers:{'X-XNBY-Client-Resources-Session':current.token,...(write?{'Content-Type':'application/json'}:{})},...(write?{body:options.body}:{})},work.signal));if(response.status===401){try{await response.body?.cancel();}catch{}await close('RESOURCE_AUTHORIZATION_REQUIRED');throw fail('RESOURCE_AUTHORIZATION_REQUIRED');}const value=await json(response);if(closed||own!==generation)throw fail('RESOURCE_CONNECTION_CLOSED');return new Response(JSON.stringify(value),{status:response.status,headers:{'Content-Type':'application/json'}});}
  catch(error){try{await response?.body?.cancel();}catch{}if(!closed)await close(error?.code??'RESOURCE_REQUEST_FAILED');throw fail(error?.code??'RESOURCE_REQUEST_FAILED');}
  finally{work.done();}
 }
 function close(code='RESOURCE_CONNECTION_CLOSED'){
  if(closing)return closing;closed=true;reason=code;generation++;bound=null;clearTimeout(timer);timer=null;for(const controller of active)controller.abort();active.clear();const old=session;session=null;
  closing=Promise.resolve().then(async()=>{if(!old){cleanupConfirmed=true;emit();return;}const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),timeoutMs);
   try{const response=await fetcher(local.href+'sessions/current',localOptions({method:'DELETE',headers:{'X-XNBY-Client-Resources-Session':old.token}},controller.signal));try{await response.body?.cancel();}catch{}cleanupConfirmed=response.status===204;}
   catch{cleanupConfirmed=false;}finally{clearTimeout(timeout);emit();}
  });return closing;
 }
 return Object.freeze({connect,request,close,get state(){return state();}});
}
