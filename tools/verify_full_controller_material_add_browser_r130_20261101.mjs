import path from 'node:path';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
const R='D:/Project/Zhumadian',root=process.argv[2];
if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r130\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_MATERIAL_ROOT');
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>16384)throw Error('BOUNDED_OWN_INPUT');}
const wire=JSON.parse(raw);raw='';const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));
if(!wire.syntheticNormalUser||wire.account!=='own_operator_a'||wire.base!=='http://127.0.0.1:'+started.gatewayPort)throw Error('OWN_MATERIAL_SCOPE');
const O=root+'/material-browser',sleep=ms=>new Promise(r=>setTimeout(r,ms));await fs.mkdir(O);await fs.mkdir(O+'/downloads');
let chrome,ws,session,seq=0,token='',stage='start',failed=null,holdNextSuccessfulImport=false,heldImport=null;let mapRequests=0;const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],cases=[],blocked=[],exceptions=[],downloadEvents=[],consoleMarkers=[];
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
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/materials/importExcel','/materials/updateById','/materials/save'].some(p=>u.pathname.endsWith(p));
  if(u?.pathname.startsWith('/zhumadian/map/'))mapRequests++;
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
   if(row.path.endsWith('/materials/updateById')||row.path.endsWith('/materials/save'))row.saved=b.data;
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
 const fill=async(label,value)=>{if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_MANUAL_FIELD_'+label)};
 const selectField=async label=>{if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('.el-select__wrapper,input');if(!e)return false;e.click();return true})()`))throw Error('OWN_SELECT_FIELD_'+label)};
 const normalizedClick=async(container,text)=>evaluate(`(()=>{const e=Array.from(document.querySelectorAll(${JSON.stringify(container)})).find(e=>e.textContent.split("").filter(ch=>ch.trim()).join("")===${JSON.stringify(text)}&&!e.disabled);if(!e)return false;e.click();return true})()`);
 await until(()=>http.some(x=>x.path.endsWith('/materials/getPage')&&Number(x.total)>100));
 stage='native-add-empty-required';if(!await click('.table-box button','新增'))throw Error('OWN_ADD_BUTTON');await until(()=>evaluate('location.pathname.endsWith("/materials/add")&&!!document.querySelector(".info-title")'));
 let saves=http.filter(x=>x.path.endsWith('/materials/save')).length;if(!await click('button','提交'))throw Error('OWN_ADD_SUBMIT');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>0'));if(http.filter(x=>x.path.endsWith('/materials/save')).length!==saves)throw Error('INVALID_ADD_CALLED_SERVER');cases.push({case:'native-empty-required-form-sends-no-save',passed:true});
 const name='OWN_F_MANUAL_R130_'+root.split('/').at(-1);stage='native-synthetic-dictionary-choice';await fill('物资名称',name);await fill('物资数量','7');await fill('物资型号','OWN_MANUAL_MODEL');await fill('物资单位','个');
 await selectField('物资类型');await until(()=>evaluate('Array.from(document.querySelectorAll(".el-select-dropdown__item")).some(e=>e.getClientRects().length&&e.textContent.trim()==="自建物资类型")'));
 if(!await click('.el-select-dropdown__item','自建物资类型'))throw Error('OWN_MATERIAL_TYPE_CHOICE');cases.push({case:'original-dictionary-API-populates-real-material-select',passed:true});
 stage='native-department-tree-choice';await selectField('所属部门');let department;
 await until(async()=>{department=await evaluate(`(()=>{const e=Array.from(document.querySelectorAll('.el-tree-node__content')).find(e=>e.getClientRects().length&&e.textContent.trim());return e?.textContent.trim()||''})()`);return !!department});
 if(!await click('.el-tree-node__content',department))throw Error('OWN_DEPARTMENT_TREE_SELECT');cases.push({case:'native-department-tree-selected-with-original-fullName-value',passed:true});
 stage='native-coordinate-map-click';if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='坐标信息');const e=a?.querySelector('input');if(!e)return false;e.click();return true})()`))throw Error('OWN_MAP_FIELD');
 await until(()=>evaluate('!!document.querySelector(".el-dialog .ol-viewport")'));const rect=await evaluate('(()=>{const e=document.querySelector(".el-dialog .ol-viewport");e.scrollIntoView({block:"center",behavior:"instant"});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:Math.min(innerHeight-20,r.y+r.height/2)}})()');
 await send('Target.activateTarget',{targetId:target.targetId});
 await evaluate(`(()=>{window.__ownMapEvents=[];const v=document.querySelector('.el-dialog .ol-viewport');for(const type of ['pointerdown','pointerup','mousedown','mouseup','click'])v.addEventListener(type,e=>window.__ownMapEvents.push({type,button:e.button,buttons:e.buttons}));})()`);
 await sleep(250);
 for(const type of ['mouseMoved','mousePressed','mouseReleased']){await send('Input.dispatchMouseEvent',{type,x:rect.x,y:rect.y,button:type==='mouseMoved'?'none':'left',buttons:type==='mousePressed'?1:0,clickCount:1},session);await sleep(60);}
 await until(()=>evaluate('Array.from(document.querySelectorAll(".el-dialog button")).some(e=>e.textContent.split("").filter(ch=>ch.trim()).join("")==="确定"&&!e.disabled)'));
 if(!await normalizedClick('.el-dialog button','确定'))throw Error('OWN_MAP_CONFIRM');await until(()=>evaluate('!document.querySelector(".el-dialog .ol-viewport")'));
 const coordinate=await formValue('坐标信息'),numbers=String(coordinate).split(',').map(Number);if(numbers.length!==2||!numbers.every(Number.isFinite)||Math.abs(numbers[0])>180||Math.abs(numbers[1])>90)throw Error('OWN_REAL_MAP_COORDINATE_MISSING');
 if(mapRequests<1)throw Error('RESTORED_SAME_ORIGIN_TILE_PATH_NOT_REQUESTED');cases.push({case:'actual-OpenLayers-mouse-click-populates-readonly-coordinate-field',passed:true,sameOriginMapRequests:mapRequests,baseMapImageryAccepted:false});
 stage='native-manual-add-save';if(!await click('button','提交'))throw Error('OWN_ADD_FINAL_SUBMIT');await until(()=>http.filter(x=>x.path.endsWith('/materials/save')).length>saves);const response=http.filter(x=>x.path.endsWith('/materials/save')).at(-1);if(response.businessCode!==0||response.saved!==true)throw Error('NATIVE_MANUAL_SAVE_NOT_CONFIRMED');
 await until(()=>evaluate('location.pathname.endsWith("/emergencyResources/materials")&&!!document.querySelector(".table-search")'));
 const records=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(name));if(Number(records.total)!==1)throw Error('NATIVE_MANUAL_ADD_NOT_VISIBLE_TO_NORMAL_ROLE');const detail=await ownAPI('/getById?id='+encodeURIComponent(records.records[0].id));
 if(detail.materialName!==name||String(detail.materialQuantity)!=='7'||detail.materialType!=='OWN_TYPE'||detail.department!==department||detail.coordinate!==coordinate)throw Error('NATIVE_MANUAL_ADD_VALUES_NOT_PERSISTED');cases.push({case:'native-add-and-normal-role-list-detail-confirm-original-payload',passed:true});
 stage='native-new-detail';await click('.table-search button','更多');await fill('物资名称',name);let n=http.filter(x=>x.path.endsWith('/materials/getPage')).length;await click('.table-search button','搜索');await until(()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length>n);
 await until(()=>evaluate('document.querySelectorAll(".el-table__body-wrapper tbody tr").length===1'));if(!await click('.el-table__body-wrapper button','详情'))throw Error('OWN_NEW_DETAIL_BUTTON');await until(()=>evaluate('location.pathname.endsWith("/materials/detail")'));await until(async()=>await formValue('物资名称')===name);
 if(await formValue('物资数量')!=='7'||await formValue('物资类型')!=='自建物资类型')throw Error('NATIVE_DETAIL_OR_DICTIONARY_LABEL_WRONG');cases.push({case:'native-new-detail-shows-persisted-values-and-original-dictionary-label',passed:true});
 stage='native-coordinate-readonly-view';if(!await click('.el-link','查看坐标'))throw Error('OWN_VIEW_COORDINATE_LINK');await until(()=>evaluate('!!document.querySelector(".el-dialog .ol-viewport")'));
 if(await evaluate('Array.from(document.querySelectorAll(".el-dialog button")).some(e=>["确定","清空"].includes(e.textContent.split("").filter(ch=>ch.trim()).join("")))'))throw Error('READONLY_COORDINATE_VIEW_HAS_WRITE_ACTION');
 if(!await normalizedClick('.el-dialog button','取消'))throw Error('OWN_MAP_VIEW_CLOSE');cases.push({case:'native-existing-coordinate-view-has-no-write-actions',passed:true});
 await fs.writeFile(O+'/native-manual-add-proof.json',JSON.stringify({normalOriginalRole:true,actualRequiredValidationSelectTreeMapSaveAndDetail:true,onlyOwnSyntheticMaterialCreated:true,actualSameOriginTileRequests:mapRequests,actualBaseMapImageryOrRealZhumadianGISAccepted:false,sourceOriginalMapCenterNotChanged:true},null,2));
 await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baselineDefectReproduced:false,productFixed:true,candidateAcceptanceLimitedToThisMaterialImportPath:true,normalOriginalLoginAndRole:true,realNangangRoleAccepted:false,blocked,exceptions,http,servicesManagedByOuterHost:true},null,2));
}catch(e){failed=String(e.message);let diagnostic={stage,message:failed,exceptions,blocked,http,cases,downloadEvents,consoleMarkers,mapRequests};
 try{if(stage==='native-coordinate-map-click')diagnostic.map=await evaluate(`(()=>{const e=document.querySelector('.el-dialog .ol-viewport'),r=e?.getBoundingClientRect();return{window:{width:innerWidth,height:innerHeight},rect:r?{x:r.x,y:r.y,width:r.width,height:r.height}:null,centerElement:r?document.elementFromPoint(r.x+r.width/2,Math.min(innerHeight-20,r.y+r.height/2))?.className:null,events:window.__ownMapEvents||[],canvasCount:e?.querySelectorAll('canvas').length,buttons:Array.from(document.querySelectorAll('.el-dialog button')).map(e=>({text:e.textContent.trim(),disabled:e.disabled}))}})()`)}catch{}try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,title:document.title,text:document.body.innerText.slice(-1200)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{
 wire.password='';token='';if(heldImport&&ws?.readyState===WebSocket.OPEN){try{await send('Fetch.continueResponse',{requestId:heldImport},session)}catch{}heldImport=null;}if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}
 if(chrome)await new Promise(r=>{if(chrome.exitCode!==null)r();else chrome.once('exit',r)});
 await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));
}
if(failed)throw Error(failed);
