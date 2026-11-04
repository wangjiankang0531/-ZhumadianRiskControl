import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
let gate='';for await(const chunk of process.stdin){gate+=chunk.toString();if(gate.length>128)throw Error('BOUNDED_PUBLIC_BROWSER_GATE');}if(gate!=='XNBY_PUBLIC_STATIC_BROWSER_R863\n')throw Error('OWN_BUDGET_GATE_REQUIRED');
const output=process.argv[2];
if(!output?.endsWith('/public-login-browser-r863'))throw Error('OWN_OUTPUT_REQUIRED');
const base='https://www.joinlinksmart.com',profile=output+'/browser-profile';
let chrome,ws,session,id=0,ended=false;const pending=new Map(),events=[],errors=[],rows=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms=60000){const deadline=Date.now()+ms;while(!await fn()){if(ended)throw Error('OWN_BROWSER_EXITED');if(Date.now()>deadline)throw Error('OBSERVATION_TIMEOUT');await sleep(100)}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const n=++id,timer=setTimeout(()=>{pending.delete(n);reject(Error(method+'_TIMEOUT'))},15000);pending.set(n,{resolve:r=>{clearTimeout(timer);resolve(r)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id:n,method,params,...(sid?{sessionId:sid}:{})}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true},session);if(r.exceptionDetails)throw Error('METRICS_EVALUATION_FAILED');return r.result.value}
let blocked=0,active=new Set(),lastActivity=0;
async function event(v){
 if(v.id){const p=pending.get(v.id);if(p){pending.delete(v.id);v.error?p.reject(Error('CDP_'+v.error.code)):p.resolve(v.result)}return}
 if(v.method==='Fetch.requestPaused'){
  const r=v.params.request,u=new URL(r.url);
  if(u.origin===base&&u.pathname.startsWith('/zhumadian/')&&['GET','HEAD'].includes(r.method))await send('Fetch.continueRequest',{requestId:v.params.requestId},v.sessionId);
  else{blocked++;await send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},v.sessionId)}
 }else if(v.sessionId===session&&v.method?.startsWith('Network.')){
  // Never retain request headers, Cookie, tokens, query strings or response bodies.
  const p=v.params;lastActivity=Date.now();
  if(v.method==='Network.requestWillBeSent'){active.add(p.requestId);const u=new URL(p.request.url);events.push({kind:'request',id:p.requestId,path:u.origin===base?u.pathname:'outside-project',type:p.type,time:p.timestamp})}
  else if(v.method==='Network.responseReceived'){
   const h=p.response.headers;const header=n=>Object.entries(h).find(([k])=>k.toLowerCase()===n)?.[1]??null;
   events.push({kind:'response',id:p.requestId,status:p.response.status,fromDiskCache:!!p.response.fromDiskCache,fromServiceWorker:!!p.response.fromServiceWorker,
    encoding:header('content-encoding'),cacheControl:header('cache-control'),vary:header('vary')});
  }else if(v.method==='Network.requestServedFromCache')events.push({kind:'cached',id:p.requestId});
  else if(v.method==='Network.loadingFinished'){active.delete(p.requestId);events.push({kind:'finished',id:p.requestId,encodedDataLength:p.encodedDataLength})}
  else if(v.method==='Network.loadingFailed'){active.delete(p.requestId);events.push({kind:'failed',id:p.requestId,blockedReason:p.blockedReason??null})}
 }else if(v.method==='Runtime.exceptionThrown')errors.push({kind:'page-exception'});
}
async function connect(){
 const lines=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split(/\r?\n/);
 if(!/^\d+$/.test(lines[0])||!lines[1]?.startsWith('/devtools/browser/'))throw Error('OWN_DEVTOOLS_BINDING_REQUIRED');
 ws=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});
 ws.addEventListener('message',e=>event(JSON.parse(e.data)).catch(()=>errors.push({kind:'driver-event-error'})));
}
let failure=null,normalClose=false;
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--window-size=1360,900','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--host-resolver-rules=MAP www.joinlinksmart.com 101.201.65.94','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 chrome.stderr.on('data',x=>fs.appendFile(output+'/chrome.private.log',x));
 chrome.once('exit',()=>{ended=true;for(const p of pending.values())p.reject(Error('OWN_BROWSER_EXITED'));pending.clear()});chrome.once('error',()=>{ended=true});
 await until(async()=>{try{await fs.access(profile+'/DevToolsActivePort');return true}catch{return false}},30000);await connect();
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const method of ['Page.enable','Runtime.enable','Network.enable'])await send(method,{},session);
 await send('Network.setCacheDisabled',{cacheDisabled:false},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:"globalThis.__xnbyLCP=0;new PerformanceObserver(l=>{for(const e of l.getEntries())globalThis.__xnbyLCP=e.startTime}).observe({type:'largest-contentful-paint',buffered:true});"},session);
 for(const [portal,route] of [['security','/zhumadian/login'],['emergency','/zhumadian/emergency/login']]){
  await send('Network.clearBrowserCache',{},session);
  for(const cache of ['cold','warm']){
   events.length=0;active=new Set();lastActivity=Date.now();const started=Date.now();
   console.log(JSON.stringify({phase:'anonymous-navigation-started',portal,cache}));
   await send('Page.navigate',{url:base+route},session);
   await until(()=>evaluate(`location.pathname===${JSON.stringify(route)}&&document.querySelectorAll('input').length>=2&&Array.from(document.querySelectorAll('button')).some(x=>x.textContent.includes('登录'))`));
   const loginVisibleMs=Date.now()-started;
   await until(()=>active.size===0&&Date.now()-lastActivity>=800,30000);
   const metrics=await evaluate("(()=>{const n=performance.getEntriesByType('navigation')[0];return{domContentLoadedMs:n.domContentLoadedEventEnd,loadEventMs:n.loadEventEnd,ttfbMs:n.responseStart-n.startTime,firstContentfulPaintMs:performance.getEntriesByName('first-contentful-paint')[0]?.startTime??null,lastObservedLargestContentfulPaintMs:globalThis.__xnbyLCP||null}})()");
   const map=new Map();for(const e of events){if(e.kind==='request')map.set(e.id,{path:e.path,type:e.type,encodedDataLength:0,cached:false});else if(map.has(e.id)){const r=map.get(e.id);if(e.kind==='response')Object.assign(r,{status:e.status,encoding:e.encoding,cacheControl:e.cacheControl,vary:e.vary,cached:r.cached||e.fromDiskCache,fromServiceWorker:e.fromServiceWorker});else if(e.kind==='cached')r.cached=true;else if(e.kind==='finished')r.encodedDataLength=e.encodedDataLength;else if(e.kind==='failed')r.failed=true}}
   const assets=[...map.values()].filter(r=>r.path.includes('/assets/'));
   rows.push({portal,cache,loginVisibleMs,...metrics,staticRequests:assets.length,cachedStaticResources:assets.filter(r=>r.cached).length,staticEncodedDataLength:assets.reduce((s,r)=>s+r.encodedDataLength,0),failedStaticResources:assets.filter(r=>r.failed||r.status>=400).length,assets});
   console.log(JSON.stringify({...rows.at(-1),assets:undefined}));
  }
 }
 if(rows.length!==4||rows.some(r=>r.failedStaticResources))throw Error('PUBLIC_LOGIN_STATIC_LOAD_FAILED');
}catch(e){failure={kind:e.name,message:e.message};console.log(JSON.stringify({failed:true,...failure}))}
finally{
 if(chrome&&!ended){if(ws?.readyState!==WebSocket.OPEN){try{await connect()}catch{}}
  if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close');normalClose=true}catch{}}}
 if(ws?.readyState===WebSocket.OPEN)ws.close();
 if(chrome&&!ended)await new Promise(r=>chrome.once('exit',r));
 const proof={completed:!failure,failure,rows,errors,blockedRequests:blocked,networkThrottlingUsed:false,cacheEnabled:true,anonymousLoginOnly:true,credentialsEntered:false,authenticatedHomepageOrModuleTiming:false,publicChanged:false,desktopOperated:false};
 await fs.writeFile(output+'/browser-results.json',JSON.stringify(proof,null,2)+'\n');
 await fs.writeFile(output+'/browser-terminal.json',JSON.stringify({normalBrowserCloseRequested:normalClose,exitCode:chrome?.exitCode,forceKill:false})+'\n');
}
if(failure)process.exitCode=1;
