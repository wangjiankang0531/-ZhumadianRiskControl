import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
const output=process.argv[2],mode=process.argv[3],base='http://127.0.0.1:18892';
if(!output?.endsWith('/static-transport-r231/'+mode)||!['baseline','candidate'].includes(mode))throw Error('OWN_STATIC_BROWSER_SCOPE');
let chrome,ws,session,id=0;const pending=new Map(),events=[],failures=[],blocked=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms=45000){const end=Date.now()+ms;while(!await fn()){if(Date.now()>end)throw Error('BROWSER_WAIT_TIMEOUT');await sleep(30)}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const n=++id;const timer=setTimeout(()=>{pending.delete(n);reject(Error(method+'_TIMEOUT'))},12000);pending.set(n,{resolve:r=>{clearTimeout(timer);resolve(r)},reject});ws.send(JSON.stringify({id:n,method,params,...(sid?{sessionId:sid}:{})}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true},session);if(r.exceptionDetails)throw Error('EVALUATE_FAILED');return r.result.value}
async function event(v){
 if(v.id){const p=pending.get(v.id);if(p){pending.delete(v.id);v.error?p.reject(Error(JSON.stringify(v.error))):p.resolve(v.result)}return}
 if(v.method==='Fetch.requestPaused'){
  const r=v.params.request,u=new URL(r.url);if(u.origin===base&&r.method==='GET')await send('Fetch.continueRequest',{requestId:v.params.requestId},v.sessionId);else{blocked.push({origin:u.origin,method:r.method});await send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},v.sessionId)}
 }else if(v.method.startsWith('Network.'))events.push(v);
 else if(v.method==='Runtime.exceptionThrown')failures.push({kind:'runtime',description:v.params.exceptionDetails?.text||'exception'});
}
const rows=[];
try{
 const profile=output+'/browser-profile';chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--window-size=1360,900','--no-first-run','--disable-default-apps','--disable-sync','--disable-background-networking','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
 await until(async()=>{try{await fs.access(profile+'/DevToolsActivePort');return true}catch{return false}});
 const lines=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split(/\r?\n/);ws=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',e=>event(JSON.parse(e.data)).catch(e=>failures.push({kind:'driver',description:e.message})));
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const m of ['Page.enable','Runtime.enable','Network.enable'])await send(m,{},session);
 await send('Network.setCacheDisabled',{cacheDisabled:false},session);
 // Controlled transfer comparison, not a claim about public bandwidth or server latency.
 await send('Network.emulateNetworkConditions',{offline:false,latency:60,downloadThroughput:1250000,uploadThroughput:1250000,connectionType:'ethernet'},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 for(const [portal,path] of [['security','/zhumadian/login'],['emergency','/zhumadian/emergency/login']]){
  await send('Network.clearBrowserCache',{},session);
  for(const cache of ['cold','warm']){
   events.length=0;const started=Date.now();await send('Page.navigate',{url:base+path},session);
   await until(()=>evaluate(`location.pathname===${JSON.stringify(path)}&&document.querySelectorAll('input').length>=2&&Array.from(document.querySelectorAll('button')).some(x=>x.textContent.includes('登录'))`));
   const loginVisibleMs=Date.now()-started;await sleep(350);
   const requests=new Map();
   for(const e of events){const p=e.params;if(e.method==='Network.requestWillBeSent')requests.set(p.requestId,{url:p.request.url,wireBytes:0,cached:false});if(e.method==='Network.requestServedFromCache'&&requests.has(p.requestId))requests.get(p.requestId).cached=true;if(e.method==='Network.responseReceived'&&requests.has(p.requestId))Object.assign(requests.get(p.requestId),{status:p.response.status,cached:!!p.response.fromDiskCache||requests.get(p.requestId).cached,encoding:p.response.headers['Content-Encoding']||p.response.headers['content-encoding']||null});if(e.method==='Network.loadingFinished'&&requests.has(p.requestId))requests.get(p.requestId).wireBytes=p.encodedDataLength;}
   const assets=[...requests.values()].filter(x=>new URL(x.url).pathname.includes('/assets/'));const timing=await evaluate(`(()=>{const n=performance.getEntriesByType('navigation')[0];return{domContentLoadedMs:n.domContentLoadedEventEnd,loadMs:n.loadEventEnd}})()`);
   rows.push({portal,cache,loginVisibleMs,...timing,staticWireBytes:assets.reduce((s,x)=>s+x.wireBytes,0),cachedStaticResources:assets.filter(x=>x.cached).length,staticRequests:assets.length,failedStaticResources:assets.filter(x=>x.status>=400).length});
  }
 }
 if(rows.length!==4||rows.some(x=>x.failedStaticResources))throw Error('LOGIN_STATIC_REQUESTS_FAILED');
 if(mode==='candidate'&&rows.filter(x=>x.cache==='warm').some(x=>x.cachedStaticResources===0))throw Error('WARM_STATIC_CACHE_NOT_USED');
 await fs.writeFile(output+'/browser-results.json',JSON.stringify({mode,rows,controlledDownloadBytesPerSecond:1250000,controlledRTTMs:60,anonymousLoginOnly:true,publicAuthenticatedHomepageOrModuleTiming:false,failures,blocked},null,2));
 console.log(JSON.stringify({mode,rows,failures:failures.length,blocked:blocked.length}));
}finally{
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close()}
 if(chrome)await new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));
 await fs.writeFile(output+'/browser-terminal.json',JSON.stringify({normalBrowserClose:true,exitCode:chrome?.exitCode,forceKill:false}));
}
