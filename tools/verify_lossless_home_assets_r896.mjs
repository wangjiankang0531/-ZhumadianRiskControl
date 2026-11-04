/** Exercise only original navigation CSS/assets in a real browser and gateway.
 * The static DOM is an explicit rendering fixture, not original SDK acceptance.
 */
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
let raw='';for await(const part of process.stdin){raw+=part;if(raw.length>16384)throw Error('BOUNDED_WIRE_REQUIRED');}
const w=JSON.parse(raw);raw='';
if(!/^http:\/\/127\.0\.0\.1:\d{4,5}$/.test(w.base)||!w.output.endsWith('/browser-r896')||[18891,18892,8767].includes(+new URL(w.base).port))throw Error('OWN_RENDER_SCOPE_REQUIRED');
await fs.mkdir(w.output);const profile=w.output+'/chrome-profile';let browser,ws,session,seq=0,exited=false,failure=null;
const pending=new Map(),rows=[],requests=[],cachedIds=new Set();let phase='start';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(f,ms=30000){const end=Date.now()+ms;while(!await f()){if(exited||Date.now()>end)throw Error('OWN_RENDER_TIMEOUT');await sleep(50);}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const id=++seq,t=setTimeout(()=>{pending.delete(id);reject(Error('CDP_TIMEOUT'))},15000);pending.set(id,{resolve:v=>{clearTimeout(t);resolve(v)},reject:e=>{clearTimeout(t);reject(e)}});ws.send(JSON.stringify({id,method,params,...sid?{sessionId:sid}:{}}));});}
async function ev(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error('RENDER_EVALUATION_FAILED');return r.result.value;}
async function connect(){const p=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split(/\r?\n/);if(!/^\d+$/.test(p[0])||!p[1].startsWith('/devtools/browser/'))throw Error('OWN_DEBUG_PORT_REQUIRED');ws=new WebSocket('ws://127.0.0.1:'+p[0]+p[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);if(p){pending.delete(v.id);v.error?p.reject(Error('CDP_ERROR')):p.resolve(v.result);}return;}if(v.method==='Fetch.requestPaused'){const u=new URL(v.params.request.url),allowed=(u.origin===w.base&&['GET','HEAD'].includes(v.params.request.method))||['data:','about:'].includes(u.protocol);send(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:v.params.requestId,...allowed?{}:{errorReason:'BlockedByClient'}},v.sessionId).catch(()=>{});}if(v.sessionId===session&&v.method==='Network.requestServedFromCache')cachedIds.add(v.params.requestId);if(v.sessionId===session&&v.method==='Network.responseReceived'){const r=v.params.response,u=new URL(r.url);if(u.origin===w.base){const get=n=>Object.entries(r.headers).find(([k])=>k.toLowerCase()===n)?.[1]??null;requests.push({phase,path:u.pathname,status:r.status,cached:!!r.fromDiskCache||cachedIds.has(v.params.requestId),mime:r.mimeType,cacheControl:get('cache-control'),encodedDataLength:r.encodedDataLength});}}});}
try{
 browser=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 browser.stderr.on('data',x=>fs.appendFile(w.output+'/chrome.private.log',x));browser.once('exit',()=>{exited=true;});
 await until(async()=>{try{await fs.access(profile+'/DevToolsActivePort');return true;}catch{return false;}});await connect();
 const t=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 for(const method of ['Page.enable','Runtime.enable','Network.enable'])await send(method,{},session);
 // CSP and a loopback-only fixture bound network access without interception,
 // which changes Chrome cache behavior and would invalidate this measurement.
 await send('Network.setCacheDisabled',{cacheDisabled:false},session);
 for(const variant of ['baseline','candidate']){
  await send('Network.clearBrowserCache',{},session);
  for(const [width,height]of [[1366,768],[1920,1080],[3840,2160]]){
   phase=variant+'-'+width;await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false},session);
   const navigation=await send('Page.navigate',{url:w.base+'/zhumadian/'+variant+'.html'},session);
   if(navigation.errorText)throw Error('LOOPBACK_NAVIGATION_'+navigation.errorText);
   await until(()=>ev('document.readyState==="complete"&&document.querySelector(".title")!==null'));
   // FontFaceSet.load enumerates overlapping @font-face declarations and can
   // fetch an unused original face. Wait only for faces actually used by layout.
   await ev('document.fonts.ready.then(()=>true)');
   await until(()=>ev('[...document.fonts].some(f=>f.family==="YouSheBiaoTiHei"&&f.status==="loaded")'));
   await sleep(100);
   const state=await ev('(()=>{const el=document.querySelector(".title"),b=document.querySelector(".background-pattern");return{font:getComputedStyle(el).fontFamily,background:getComputedStyle(b).backgroundImage,width:innerWidth,height:innerHeight,titleWidth:el.getBoundingClientRect().width,titleHeight:el.getBoundingClientRect().height,overflow:document.documentElement.scrollWidth>innerWidth}})()');
   if(!state.font.includes('YouSheBiaoTiHei')||state.width!==width||state.overflow)throw Error('ORIGINAL_RENDER_GEOMETRY_REQUIRED');
   const image=await send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false},session);const bytes=Buffer.from(image.data,'base64');await fs.writeFile(w.output+'/'+phase+'.png',bytes);
   rows.push({variant,width,height,...state,screenshotSHA256:createHash('sha256').update(bytes).digest('hex')});
  }
 }
 const current=requests.filter(r=>r.phase.startsWith('candidate-'));
 if(current.some(r=>r.path.endsWith('.ttf')||r.path.includes('background-BHYqFd8n.png')))throw Error('OLD_LARGE_ASSET_STILL_REQUESTED');
 for(const suffix of ['.woff2','.webp']){
  const r=current.filter(r=>r.path.endsWith(suffix));if(r.length!==3||r[0].cached||!r.slice(1).every(x=>x.cached))throw Error('COLD_AND_WARM_ASSET_CACHE_REQUIRED');
  if(r.some(x=>x.status!==200||x.cacheControl!=='public, max-age=31536000, immutable'))throw Error('ACTUAL_NGINX_CACHE_REQUIRED');
 }
}catch(e){failure={stage:phase,type:e.name,message:e.message};try{failure.fontFaces=await ev('[...document.fonts].filter(f=>f.family==="YouSheBiaoTiHei").map(f=>({family:f.family,status:f.status}))');}catch{}}
finally{
 let closeRequested=false;if(browser&&!exited&&ws?.readyState===WebSocket.OPEN){try{await send('Browser.close');closeRequested=true;}catch{}}
 if(browser&&!exited)await new Promise(r=>browser.once('exit',r));if(ws?.readyState===WebSocket.OPEN)ws.close();
 await fs.writeFile(w.output+'/result.json',JSON.stringify({passed:!failure,failure,rows,requests,fixtureDOM:true,actualOriginalCompiledCSS:true,originalSDKAccepted:false,publicOrDesktopTouched:false},null,2)+'\n');
 await fs.writeFile(w.output+'/browser-terminal.json',JSON.stringify({normalCloseRequested:closeRequested,exitCode:browser?.exitCode,forceTerminationUsed:false})+'\n');
}
if(failure){console.log(JSON.stringify({passed:false,failure}));process.exitCode=1;}else console.log(JSON.stringify({passed:true,renderCases:rows.length}));
