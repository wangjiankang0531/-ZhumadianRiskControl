import path from 'node:path';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
const R='D:/Project/Zhumadian',root=process.argv[2];
if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r130\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_MATERIAL_ROOT');
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>16384)throw Error('BOUNDED_OWN_INPUT');}
const wire=JSON.parse(raw);raw='';const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));
if(!wire.syntheticNormalUser||wire.account!=='own_operator_a'||wire.base!=='http://127.0.0.1:'+started.gatewayPort)throw Error('OWN_MATERIAL_SCOPE');
const O=root+'/material-browser',sleep=ms=>new Promise(r=>setTimeout(r,ms));await fs.mkdir(O);await fs.mkdir(O+'/downloads');
let chrome,ws,session,seq=0,token='',stage='start',failed=null,holdNextSuccessfulImport=false,heldImport=null,holdMaterialResponses=0;const heldMaterial=[];const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],cases=[],blocked=[],exceptions=[],downloadEvents=[],consoleMarkers=[];
async function until(fn,ms=40000){let end=Date.now()+ms;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_MATERIAL_UI_TIMEOUT_'+stage);await sleep(50);}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN)return reject(Error('OWN_CDP_CLOSED'));const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method));},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}
async function evaluate(expression){const v=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(v.exceptionDetails)throw Error('OWN_MATERIAL_EVALUATE');return v.result.value;}
async function click(selector,text){return evaluate(`(()=>{const e=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(e=>e.textContent.trim()===${JSON.stringify(text)});if(!e)return false;e.click();return true})()`);}
async function ownAPI(path){if(!/^\/(?:getPage|getById)\?/.test(path))throw Error('OWN_MATERIAL_READ_ONLY');const ua=await evaluate('navigator.userAgent');const r=await fetch(wire.base+'/zhumadian/api/serv/materials'+path,{headers:{Authorization:token,'User-Agent':ua}});const v=await r.json();if(r.status!==200||v.code!==0)throw Error('OWN_MATERIAL_READBACK_FAILED');return v.data;}
async function nodeRun(command,args){const child=spawn(command,args,{windowsHide:true,stdio:['ignore','pipe','pipe']});let out='',err='';for await(const b of child.stdout)out+=b;for await(const b of child.stderr)err+=b;const exit=await new Promise(r=>child.exitCode!==null?r(child.exitCode):child.once('exit',r));if(exit!==0)throw Error('OWN_WORKBOOK_GENERATOR_FAILED');return JSON.parse(out);}
async function upload(file){
 if(!await click('.table-box button','Excel导入'))throw Error('OWN_IMPORT_BUTTON');
 await until(()=>evaluate('!!document.querySelector(".el-dialog input[type=file]")'));
 const before=http.filter(x=>x.path.endsWith('/materials/importExcel')).length;
 const doc=await send('DOM.getDocument',{},session);const q=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'.el-dialog input[type=file]'},session);
 await send('DOM.setFileInputFiles',{nodeId:q.nodeId,files:[path.win32.resolve(file)]},session);
 await until(()=>http.filter(x=>x.path.endsWith('/materials/importExcel')).length>before,90000);
 await Promise.allSettled([...reads]);return http.filter(x=>x.path.endsWith('/materials/importExcel')).at(-1);
}
async function event(v){
 if(v.method==='Browser.downloadWillBegin'){downloadEvents.push({event:'begin',name:v.params.suggestedFilename,blob:v.params.url?.startsWith('blob:')});return;}
 if(v.method==='Browser.downloadProgress'){downloadEvents.push({event:'progress',state:v.params.state,totalBytes:v.params.totalBytes,receivedBytes:v.params.receivedBytes});return;}
 if(v.method==='Runtime.consoleAPICalled'){for(const a of v.params.args||[]){const markers=String(a.description||a.value||'').match(/MATERIAL_[A-Z_]+|DOWNLOAD_[A-Z_]+/g);if(markers)consoleMarkers.push(...markers);}return;}
 if(v.id){const p=pending.get(v.id);if(!p)return;pending.delete(v.id);v.error?p.reject(Error('OWN_CDP_'+v.error.code)):p.resolve(v.result);return;}
 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request;let u;try{u=new URL(request.url)}catch{}
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/materials/importExcel','/materials/updateById'].some(p=>u.pathname.endsWith(p));
  const responseStage=v.params.responseStatusCode!==undefined;
  if(responseStage&&holdMaterialResponses>0&&u?.pathname.endsWith('/materials/getPage')&&v.params.responseStatusCode===200){holdMaterialResponses--;heldMaterial.push(v.params.requestId);return;}
  if(responseStage&&holdNextSuccessfulImport&&u?.pathname.endsWith('/materials/importExcel')&&v.params.responseStatusCode===200){holdNextSuccessfulImport=false;heldImport=v.params.requestId;return;}
  if(disallowed){blocked.push({origin:u?.origin||'invalid',path:u?.pathname||'',method:request.method});await send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},session);}
  else await send(responseStage?'Fetch.continueResponse':'Fetch.continueRequest',{requestId:v.params.requestId},session);
 }else if(v.method==='Network.responseReceived'){
  const r=v.params.response;let u;try{u=new URL(r.url)}catch{};if(u?.origin===wire.base&&u.pathname.includes('/api/'))tracked.set(v.params.requestId,{path:u.pathname,httpStatus:r.status,mime:r.mimeType});
 }else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);const p=send('Network.getResponseBody',{requestId:v.params.requestId},session).then(r=>{
   const bytes=r.base64Encoded?Buffer.from(r.body,'base64'):Buffer.from(r.body);if(row.path.endsWith('/materials/getModel'))return fs.writeFile(O+'/original-http-template-response.bin',bytes).then(()=>{row.bodyBytes=bytes.length;row.nonJSON=true;http.push(row)});
   const raw=bytes.toString('utf8');let b;try{b=JSON.parse(raw)}catch{row.nonJSON=true;row.bodyBytes=Buffer.byteLength(raw);http.push(row);return;}
   row.businessCode=b.code;
   if(row.path.endsWith('/oauth/Login')){token=b.data?.token||'';row.normalTokenReturned=!!token;}
   if(row.path.endsWith('/oauth/CurrentUser')){row.ownUserMatched=b.data?.userInfo?.userId===wire.expectedUserId;row.materialMenuReturned=JSON.stringify(b.data?.menuList||[]).includes('/emergencyResources/materials');}
   if(row.path.endsWith('/materials/getPage')){row.rows=Array.isArray(b.data?.records)?b.data.records.length:null;row.total=b.data?.total;}
   if(row.path.endsWith('/materials/updateById'))row.saved=b.data;
   http.push(row);
  }).catch(()=>{row.observationFailed=true;http.push(row)}).finally(()=>reads.delete(p));reads.add(p);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION'});
}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--no-first-run','--disable-default-apps','--disable-sync','--disable-background-networking','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:'ignore'});
 await until(async()=>{try{await fs.access(O+'/chrome-profile/DevToolsActivePort');return true}catch{return false}});
 const lines=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split(/\r?\n/);ws=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});
 ws.addEventListener('message',e=>{event(JSON.parse(e.data)).catch(()=>{})});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 await send('Page.enable',{},session);await send('Runtime.enable',{},session);await send('Network.enable',{},session);await send('DOM.enable',{},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.win32.resolve(O+'/downloads'),eventsEnabled:true});
 stage='normal-login';await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyResources/materials'},session);
 await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([wire.account,wire.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})})()`);
 if(!await click('.login-body button','登录'))throw Error('OWN_LOGIN_BUTTON');
 await until(()=>http.some(x=>x.path.endsWith('/oauth/CurrentUser')&&x.ownUserMatched&&x.materialMenuReturned));
 await until(()=>evaluate('!document.querySelector(".login-body")&&Array.from(document.querySelectorAll(".el-menu-item")).some(e=>e.textContent.trim()==="应急物资")'));
 if(!await click('.el-menu-item','应急物资'))throw Error('OWN_MATERIAL_MENU');
 await until(()=>evaluate('location.pathname.endsWith("/emergencyResources/materials")&&Array.from(document.querySelectorAll(".table-box button")).some(e=>e.textContent.trim()==="下载模板")'));
 cases.push({case:'original-native-normal-login-and-material-menu',passed:true});wire.password='';


 const expected=await ownAPI('/getPage?current=1&size=1&materialName=OWN_F_MAT_r7_valid_');if(Number(expected.total)<1||Number(expected.total)>10)throw Error('OWN_FILTER_SAMPLE_SCOPE');
 await until(()=>http.some(x=>x.path.endsWith('/materials/getPage')&&Number(x.total)>100));
 await until(()=>evaluate('document.querySelectorAll(".el-table__body-wrapper tbody tr").length===10'));
 const listCount=()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length;
 const visible=()=>evaluate(`({rows:Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).map(e=>e.textContent),loading:Array.from(document.querySelectorAll('.el-loading-mask')).some(e=>e.getClientRects().length&&getComputedStyle(e).display!=='none')})`);
 const startSearch=async name=>{
  await click('.table-search button','更多');
  if(!await evaluate(`(()=>{const e=Array.from(document.querySelectorAll('.table-search .el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='物资名称')?.querySelector('input');if(!e||!e.getClientRects().length)return false;e.value=${JSON.stringify(name)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_VISIBLE_SEARCH_FIELD');
  if(!await click('.table-search button','搜索'))throw Error('OWN_SEARCH_BUTTON');
 };
 const assertNarrow=async()=>{const v=await visible();if(v.rows.length!==Number(expected.total)||!v.rows.every(x=>x.includes('OWN_F_MAT_r7_valid_')))throw Error('LATEST_NATIVE_FILTER_NOT_DISPLAYED');return v};
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'},{urlPattern:'*/materials/getPage*',requestStage:'Response'}]},session);
 stage='older-success-after-newer-success';let n=listCount();holdMaterialResponses=1;await startSearch('OWN_F_MAT_');await until(()=>heldMaterial.length===1);
 await startSearch('OWN_F_MAT_r7_valid_');await until(()=>listCount()===n+1);await until(async()=>{const v=await visible();return !v.loading&&v.rows.length===Number(expected.total)});await assertNarrow();
 let held=heldMaterial.shift();await send('Fetch.continueResponse',{requestId:held},session);await until(()=>listCount()===n+2);await sleep(250);
 let v=await visible();const overwritten=v.rows.length!==Number(expected.total)||!v.rows.every(x=>x.includes('OWN_F_MAT_r7_valid_'));
 if(wire.variant==='guarded'){if(!overwritten)throw Error('ORIGINAL_REVERSED_RESPONSE_DEFECT_NOT_REPRODUCED');cases.push({case:'original-native-old-response-overwrites-new-filter-reproduced',passed:true,oldRows:v.rows.length,newExpectedRows:Number(expected.total)});}
 else{
  if(overwritten)throw Error('OLD_SUCCESS_OVERWROTE_LATEST_FILTER');cases.push({case:'actual-old-success-after-new-success-keeps-latest-native-filter',passed:true,rows:Number(expected.total)});
  stage='older-completion-while-newest-pending';n=listCount();holdMaterialResponses=2;await startSearch('OWN_F_MAT_');await until(()=>heldMaterial.length===1);await startSearch('OWN_F_MAT_r7_valid_');await until(()=>heldMaterial.length===2);
  held=heldMaterial.shift();await send('Fetch.continueResponse',{requestId:held},session);await until(()=>listCount()===n+1);await sleep(150);v=await assertNarrow();if(!v.loading)throw Error('OLD_COMPLETION_CLEARED_NEWEST_LOADING');
  held=heldMaterial.shift();await send('Fetch.continueResponse',{requestId:held},session);await until(()=>listCount()===n+2);await until(async()=>!(await visible()).loading);await assertNarrow();
  cases.push({case:'old-completion-cannot-clear-newest-pending-loading-or-rows',passed:true});
 }
 await fs.writeFile(O+'/actual-response-order-proof.json',JSON.stringify({originalDefectReproduced:wire.variant==='guarded',candidateProtected:wire.variant==='candidate',actualServerResponsesHeldAndReleasedOnly:true,syntheticFulfillmentUsed:false,businessWrites:0,expectedFilteredRows:Number(expected.total)},null,2));
 await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baselineDefectReproduced:wire.variant==='guarded',productFixed:wire.variant==='candidate',candidateAcceptanceLimitedToThisMaterialImportPath:true,normalOriginalLoginAndRole:true,realNangangRoleAccepted:false,blocked,exceptions,http,servicesManagedByOuterHost:true},null,2));
}catch(e){failed=String(e.message);let diagnostic={stage,message:failed,exceptions,blocked,http,cases,downloadEvents,consoleMarkers};try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,title:document.title,text:document.body.innerText.slice(-1200)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{
 wire.password='';token='';for(const requestId of heldMaterial.splice(0)){try{await send('Fetch.continueResponse',{requestId},session)}catch{}}if(heldImport&&ws?.readyState===WebSocket.OPEN){try{await send('Fetch.continueResponse',{requestId:heldImport},session)}catch{}heldImport=null;}if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}
 if(chrome)await new Promise(r=>{if(chrome.exitCode!==null)r();else chrome.once('exit',r)});
 await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));
}
if(failed)throw Error(failed);
