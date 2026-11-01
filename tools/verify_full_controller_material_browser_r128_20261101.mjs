import path from 'node:path';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
const R='D:/Project/Zhumadian',root=process.argv[2];
if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r128\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_MATERIAL_ROOT');
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>16384)throw Error('BOUNDED_OWN_INPUT');}
const wire=JSON.parse(raw);raw='';const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));
if(!wire.syntheticNormalUser||wire.account!=='own_operator_a'||wire.base!=='http://127.0.0.1:'+started.gatewayPort)throw Error('OWN_MATERIAL_SCOPE');
const O=root+'/material-browser',sleep=ms=>new Promise(r=>setTimeout(r,ms));await fs.mkdir(O);await fs.mkdir(O+'/downloads');
let chrome,ws,session,seq=0,token='',stage='start',failed=null,holdNextSuccessfulImport=false,heldImport=null;const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],cases=[],blocked=[],exceptions=[],downloadEvents=[],consoleMarkers=[];
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
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!u.pathname.endsWith('/materials/importExcel');
  const responseStage=v.params.responseStatusCode!==undefined;
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
 stage='download-template';if(!await click('.table-box button','下载模板'))throw Error('OWN_TEMPLATE_BUTTON');
 await until(()=>evaluate('!!document.querySelector(".el-message-box")'));if(!await click('.el-message-box button','确定'))throw Error('OWN_TEMPLATE_CONFIRM');
 let template;await until(async()=>{const names=await fs.readdir(O+'/downloads');const name=names.find(x=>x.endsWith('.xlsx'));if(!name)return false;template=O+'/downloads/'+name;return true});
 const books=await nodeRun(R+'/_f/Application/runtime/python/python.exe',['-I','-B','-X','utf8',R+'/Application/tools/prepare_owned_material_workbooks_r128_20261101.py',O,template]);
 cases.push({case:'actual-chrome-template-has-all12-original-headers-no-data',passed:true});
 stage='valid-import';const before=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(books.prefix+'valid_'));if(Number(before.total)!==0)throw Error('OWN_SAMPLE_ALREADY_PRESENT');
 const good=await upload(books.valid);await until(()=>evaluate('!document.querySelector(".el-dialog__body input[type=file]")'));
 const after=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(books.prefix+'valid_'));if(Number(after.total)!==3||after.records.length!==3)throw Error('OWN_VALID_IMPORT_READBACK');
 const detail=await ownAPI('/getById?id='+encodeURIComponent(after.records[0].id));if(detail.materialName!==after.records[0].materialName||String(detail.materialQuantity)!=='12')throw Error('OWN_IMPORT_DETAIL_READBACK');
 cases.push({case:'actual-upload-three-rows-list-detail-readback',passed:true,rows:3,httpStatus:good.httpStatus});
 if(wire.variant==='candidate'&&root.endsWith('/r7')){
  const prior=await ownAPI('/getPage?current=1&size=5&materialName=OWN_F_MAT_r6_valid_');if(Number(prior.total)!==3)throw Error('OWN_RESTART_LOST_ACCEPTED_SAMPLE');
  cases.push({case:'previous-accepted-three-rows-survive-full-six-component-restart',passed:true,rows:3});
 }

 stage='partial-import-baseline';const bad=await upload(books.partial);
 const partial=await ownAPI('/getPage?current=1&size=1&materialName='+encodeURIComponent(books.prefix+'partial_'));
 const dialogOpen=await evaluate('!!document.querySelector(".el-dialog__body input[type=file]")');
 const baseline={case:(wire.variant==='candidate'?'candidate':'original')+'-import-row3001-too-long',httpStatus:bad.httpStatus,businessCode:bad.businessCode??null,previousBatchPersisted:Number(partial.total),dialogStillOpen:dialogOpen};
 const expectedPartial=wire.variant==='candidate'?0:3000;if(Number(partial.total)!==expectedPartial)throw Error('OWN_MATERIAL_IMPORT_TRANSACTION_RESULT_MISMATCH');
 if(wire.variant==='candidate'&&!dialogOpen)throw Error('OWN_FAILED_IMPORT_DIALOG_CLOSED');
 const old=await ownAPI('/getPage?current=1&size=1&materialName=OWN_F_MAT_r5_partial_');if(Number(old.total)!==3000)throw Error('OWN_ORIGINAL_BASELINE_ROWS_CHANGED');
 cases.push({case:wire.variant==='candidate'?'actual-file-transaction-rolls-back-first3000-and-keeps-original3000':'actual-normal-role-original-import-partial-commit-reproduced',passed:true,failedFilePersistedRows:Number(partial.total),oldBaselineRowsPreserved:Number(old.total)});
 await fs.writeFile(O+'/baseline-defect.json',JSON.stringify(baseline,null,2));
 if(wire.variant==='candidate'&&root.endsWith('/r7')){
  const close=async()=>{if(!await evaluate('(()=>{const b=document.querySelector(".el-dialog__headerbtn");if(!b)return false;b.click();return true})()'))throw Error('OWN_IMPORT_CLOSE');await until(()=>evaluate('!document.querySelector(".el-dialog input[type=file]")'));};
  await close();stage='invalid-file-rejected';const fake=O+'/own-fake.xlsx';await fs.writeFile(fake,'OWN_SYNTHETIC_NOT_EXCEL');
  const invalid=await upload(fake);if(invalid.httpStatus<400||!await evaluate('!!document.querySelector(".el-dialog input[type=file]")'))throw Error('OWN_FAKE_FILE_NOT_REJECTED_WITH_DIALOG');
  const unchanged=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(books.prefix+'valid_'));if(Number(unchanged.total)!==3)throw Error('OWN_FAKE_FILE_CHANGED_PRIOR_ROWS');
  cases.push({case:'fake-xlsx-rejected-and-original-three-rows-preserved',passed:true});await close();
  stage='header-only-template-no-op';const empty=await upload(template);await until(()=>evaluate('!document.querySelector(".el-dialog input[type=file]")'));
  const noOp=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(books.prefix+'valid_'));if(empty.httpStatus!==200||Number(noOp.total)!==3)throw Error('OWN_HEADER_ONLY_IMPORT_NOT_NOOP');
  cases.push({case:'original-header-only-template-remains-successful-no-op',passed:true});
  stage='actual-success-response-delayed-close-reopen';await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'},{urlPattern:'*/materials/importExcel',requestStage:'Response'}]},session);
  holdNextSuccessfulImport=true;if(!await click('.table-box button','Excel导入'))throw Error('OWN_IMPORT_BUTTON');await until(()=>evaluate('!!document.querySelector(".el-dialog input[type=file]")'));
  const beforeLate=http.filter(x=>x.path.endsWith('/materials/importExcel')).length;
  const doc=await send('DOM.getDocument',{},session),node=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'.el-dialog input[type=file]'},session);
  await send('DOM.setFileInputFiles',{nodeId:node.nodeId,files:[path.win32.resolve(books.valid)]},session);await until(()=>!!heldImport,60000);
  await close();if(!await click('.table-box button','Excel导入'))throw Error('OWN_REOPEN_IMPORT');await until(()=>evaluate('!!document.querySelector(".el-dialog input[type=file]")'));
  const requestId=heldImport;heldImport=null;await send('Fetch.continueResponse',{requestId},session);await until(()=>http.filter(x=>x.path.endsWith('/materials/importExcel')).length>beforeLate);await sleep(500);
  if(!await evaluate('!!document.querySelector(".el-dialog input[type=file]")'))throw Error('OLD_SUCCESS_CLOSED_NEW_IMPORT_DIALOG');
  const repeat=await ownAPI('/getPage?current=1&size=10&materialName='+encodeURIComponent(books.prefix+'valid_'));if(Number(repeat.total)!==6||new Set(repeat.records.map(x=>x.id)).size!==6)throw Error('ORIGINAL_APPEND_SEMANTICS_NOT_RETAINED');
  cases.push({case:'actual-committed-success-late-response-keeps-new-dialog-open',passed:true,newRows:3});
  cases.push({case:'same-file-second-import-retains-original-append-six-distinct-ids',passed:true,rows:6});await close();
 }

 await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baselineDefectReproduced:wire.variant!=='candidate',productFixed:wire.variant==='candidate',candidateAcceptanceLimitedToThisMaterialImportPath:true,normalOriginalLoginAndRole:true,realNangangRoleAccepted:false,blocked,exceptions,http,servicesManagedByOuterHost:true},null,2));
}catch(e){failed=String(e.message);let diagnostic={stage,message:failed,exceptions,blocked,http,cases,downloadEvents,consoleMarkers};try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,title:document.title,text:document.body.innerText.slice(-1200)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{
 wire.password='';token='';if(heldImport&&ws?.readyState===WebSocket.OPEN){try{await send('Fetch.continueResponse',{requestId:heldImport},session)}catch{}heldImport=null;}if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}
 if(chrome)await new Promise(r=>{if(chrome.exitCode!==null)r();else chrome.once('exit',r)});
 await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));
}
if(failed)throw Error(failed);
