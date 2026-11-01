import path from 'node:path';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
const R='D:/Project/Zhumadian',root=process.argv[2];
if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r129\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_MATERIAL_ROOT');
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
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/materials/importExcel','/materials/updateById'].some(p=>u.pathname.endsWith(p));
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

 const formValue=label=>evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
 const fill=async(label,value)=>{if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly||!e.getClientRects().length)return false;e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_FORM_FIELD_NOT_EDITABLE_'+label)};
 const filter=async name=>{await click('.table-search button','更多');const n=http.filter(x=>x.path.endsWith('/materials/getPage')).length;await fill('物资名称',name);if(!await click('.table-search button','搜索'))throw Error('OWN_NATIVE_SEARCH_BUTTON');await until(()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length>n);await until(()=>evaluate('!document.querySelector(".el-loading-mask")'));await Promise.allSettled([...reads]);return http.filter(x=>x.path.endsWith('/materials/getPage')).at(-1)};
 const rowAction=async text=>{if(!await evaluate(`(()=>{const row=document.querySelector('.el-table__body-wrapper tbody tr');const b=Array.from(row?.querySelectorAll('button')||[]).find(x=>x.textContent.trim()===${JSON.stringify(text)});if(!b)return false;b.click();return true})()`))throw Error('OWN_NATIVE_ROW_ACTION_'+text)};
 const listReady=()=>until(()=>evaluate('location.pathname.endsWith("/emergencyResources/materials")&&!!document.querySelector(".table-search")'));
 await until(()=>http.some(x=>x.path.endsWith('/materials/getPage')&&Number(x.total)>100));await until(()=>evaluate('document.querySelectorAll(".el-table__body-wrapper tbody tr").length===10'));
 stage='actual-list-filter';const expected=await ownAPI('/getPage?current=1&size=1&materialName=OWN_F_MAT_r7_valid_');if(Number(expected.total)<1)throw Error('OWN_PRIOR_SAMPLE_EXHAUSTED');const filtered=await filter('OWN_F_MAT_r7_valid_');if(Number(filtered.total)!==Number(expected.total))throw Error('NATIVE_UI_FILTER_NOT_EXACT');
 if(!await evaluate('Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).every(e=>e.textContent.includes("OWN_F_MAT_r7_valid_"))'))throw Error('NATIVE_UI_FILTER_ROWS_WRONG');
 cases.push({case:'native-list-name-filter-matches-original-synthetic-API',passed:true,rows:Number(expected.total)});
 if(wire.variant==='guarded'){
  stage='actual-filtered-native-export';if(!await click('.table-box button','导出列表'))throw Error('OWN_EXPORT_BUTTON');await until(()=>evaluate('!!document.querySelector(".el-message-box")'));
  if(!await click('.el-message-box button','确定'))throw Error('OWN_EXPORT_CONFIRM');let exported;
  await until(async()=>{const n=(await fs.readdir(O+'/downloads')).find(n=>n.endsWith('.xlsx'));if(!n)return false;exported=O+'/downloads/'+n;return true});
  const exportProof=await nodeRun(R+'/_f/Application/runtime/python/python.exe',['-I','-B','-X','utf8',R+'/Application/tools/verify_owned_material_export_r129_20261101.py',exported,String(expected.total)]);
  await fs.writeFile(O+'/native-export-proof.json',JSON.stringify(exportProof,null,2));cases.push({case:'actual-chrome-filtered-export-valid-OOXML-and-exact-own-rows',passed:true,rows:exportProof.rows});
 }
 stage='actual-detail-click';await rowAction('详情');await until(()=>evaluate('location.pathname.endsWith("/materials/detail")'));await until(async()=>String(await formValue('物资名称')).startsWith('OWN_F_MAT_r7_valid_'));
 if(await formValue('物资数量')!=='12'||await formValue('物资型号')!=='OWN_MODEL')throw Error('NATIVE_DETAIL_FIELDS_WRONG');
 const originalName=await formValue('物资名称');cases.push({case:'native-row-detail-renders-original-imported-fields',passed:true});
 if(!await click('button','返回'))throw Error('OWN_DETAIL_BACK');await listReady();
 stage='actual-filter-reset';let n=http.filter(x=>x.path.endsWith('/materials/getPage')).length;if(!await click('.table-search button','重置'))throw Error('OWN_NATIVE_RESET');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length>n);await click('.table-search button','更多');if(await formValue('物资名称')!=='')throw Error('NATIVE_RESET_DID_NOT_CLEAR');cases.push({case:'native-list-reset-clears-name-filter',passed:true});
 stage='actual-edit-save';await filter(originalName);await rowAction('编辑');await until(()=>evaluate('location.pathname.endsWith("/materials/edit")'));await until(async()=>await formValue('物资名称')===originalName);
 const editedName='OWN_F_UI_R129_'+root.split('/').at(-1);await fill('物资名称',editedName);await fill('物资数量','23');
 n=http.filter(x=>x.path.endsWith('/materials/updateById')).length;if(!await click('button','提交'))throw Error('OWN_EDIT_SUBMIT');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/updateById')).length>n);await listReady();
 const response=http.filter(x=>x.path.endsWith('/materials/updateById')).at(-1);if(response.businessCode!==0||response.saved!==true)throw Error('NATIVE_EDIT_NOT_ACTUALLY_SAVED');
 const edited=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(editedName));if(Number(edited.total)!==1||String(edited.records[0].materialQuantity)!=='23')throw Error('NATIVE_EDIT_READBACK');
 cases.push({case:'native-edit-submit-and-original-API-confirmed-values',passed:true,actualRequests:1});
 stage='actual-edit-detail-reopen';await filter(editedName);await rowAction('详情');await until(()=>evaluate('location.pathname.endsWith("/materials/detail")'));await until(async()=>await formValue('物资名称')===editedName);
 if(await formValue('物资数量')!=='23')throw Error('NATIVE_REOPEN_DETAIL_STALE');cases.push({case:'native-reopened-detail-shows-saved-edit',passed:true});await click('button','返回');await listReady();
 // Load an editor, then delete that same synthetic record through another real UI tab.
 stage='stale-editor-open';await filter(editedName);await rowAction('编辑');await until(()=>evaluate('location.pathname.endsWith("/materials/edit")'));await until(async()=>await formValue('物资名称')===editedName);const editorSession=session;
 const targetIds=new Set((await send('Target.getTargets')).targetInfos.map(x=>x.targetId));
 await send('Runtime.evaluate',{expression:"window.open('about:blank','_blank')",userGesture:true},session);let second;
 await until(async()=>{second=(await send('Target.getTargets')).targetInfos.find(x=>x.type==='page'&&!targetIds.has(x.targetId));return !!second});session=(await send('Target.attachToTarget',{targetId:second.targetId,flatten:true})).sessionId;
 await send('Page.enable',{},session);await send('Runtime.enable',{},session);await send('Network.enable',{},session);await send('DOM.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyResources/materials'},session);await listReady();await filter(editedName);
 if(wire.variant==='guarded'){
  const beforeCancel=http.filter(x=>x.path.endsWith('/materials/removeById')).length;await rowAction('删除');await until(()=>evaluate('!!document.querySelector(".el-message-box")'));
  if(!await click('.el-message-box button','取消'))throw Error('OWN_DELETE_CANCEL');await until(()=>evaluate('!document.querySelector(".el-message-box")'));await sleep(200);
  if(http.filter(x=>x.path.endsWith('/materials/removeById')).length!==beforeCancel)throw Error('CANCELLED_DELETE_STILL_CALLED_SERVER');
  if(Number((await ownAPI('/getPage?current=1&size=1&materialName='+encodeURIComponent(editedName))).total)!==1)throw Error('CANCELLED_DELETE_CHANGED_ROW');
  cases.push({case:'native-cancel-delete-keeps-own-row-and-sends-zero-delete',passed:true});
 }
 await rowAction('删除');
 await until(()=>evaluate('!!document.querySelector(".el-message-box")'));n=http.filter(x=>x.path.endsWith('/materials/removeById')).length;if(!await click('.el-message-box button','确定'))throw Error('OWN_NATIVE_DELETE_CONFIRM');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/removeById')).length>n);const removed=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(editedName));if(Number(removed.total)!==0)throw Error('NATIVE_DELETE_NOT_APPLIED');
 cases.push({case:'native-delete-confirm-removes-only-selected-own-synthetic-row',passed:true});
 session=editorSession;stage='actual-code-zero-false-save';await fill('物资数量','24');n=http.filter(x=>x.path.endsWith('/materials/updateById')).length;await click('button','提交');await until(()=>http.filter(x=>x.path.endsWith('/materials/updateById')).length>n);await sleep(500);
 const stale=http.filter(x=>x.path.endsWith('/materials/updateById')).at(-1);if(stale.businessCode!==0||stale.saved!==false)throw Error('NATIVE_FALSE_RESULT_NOT_REPRODUCED');
 const onEditor=await evaluate('location.pathname.endsWith("/materials/edit")');
 await fs.writeFile(O+'/stale-save-baseline.json',JSON.stringify({originalActualCodeZeroFalse:true,editorRetained:onEditor,falseSaveNavigatedAsSuccess:!onEditor,syntheticRowRemainedAbsent:Number((await ownAPI('/getPage?current=1&size=1&materialName='+encodeURIComponent(editedName))).total)===0},null,2));
 if(wire.variant==='guarded'){
  if(!onEditor||await formValue('物资数量')!=='24')throw Error('FALSE_SAVE_DID_NOT_KEEP_ORIGINAL_EDITOR_AND_INPUT');
  if(!await evaluate('document.body.innerText.includes("保存未完成，请保留当前内容")'))throw Error('FALSE_SAVE_NOTICE_MISSING');
  cases.push({case:'actual-server-code-zero-false-keeps-editor-values-and-shows-failure',passed:true});
 }else cases.push({case:'actual-server-false-result-baseline-recorded',passed:true,originalDefectReproduced:!onEditor});
 await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baselineDefectReproduced:cases.some(x=>x.originalDefectReproduced),productFixed:wire.variant==='guarded',candidateAcceptanceLimitedToThisMaterialImportPath:true,normalOriginalLoginAndRole:true,realNangangRoleAccepted:false,blocked,exceptions,http,servicesManagedByOuterHost:true},null,2));
}catch(e){failed=String(e.message);let diagnostic={stage,message:failed,exceptions,blocked,http,cases,downloadEvents,consoleMarkers};try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,title:document.title,text:document.body.innerText.slice(-1200)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{
 wire.password='';token='';if(heldImport&&ws?.readyState===WebSocket.OPEN){try{await send('Fetch.continueResponse',{requestId:heldImport},session)}catch{}heldImport=null;}if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}
 if(chrome)await new Promise(r=>{if(chrome.exitCode!==null)r();else chrome.once('exit',r)});
 await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));
}
if(failed)throw Error(failed);
