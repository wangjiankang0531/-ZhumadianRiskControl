import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
const root=process.argv[2];if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r163\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_RESOURCE_ROOT');
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>16384)throw Error('BOUNDED_OWN_INPUT');}const wire=JSON.parse(raw);raw='';
const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));if(!wire.syntheticNormalUser||wire.account!=='own_operator_a'||wire.base!=='http://127.0.0.1:'+started.gatewayPort)throw Error('OWN_RESOURCE_SCOPE');
const O=root+'/plan-browser',sleep=ms=>new Promise(r=>setTimeout(r,ms));await fs.mkdir(O);await fs.mkdir(O+'/downloads');
let chrome,ws,session,seq=0,token='',stage='start',failed=null;const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],cases=[],blocked=[],exceptions=[],downloads=[];
async function until(fn,ms=40000){const end=Date.now()+ms;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_EXPERT_UI_TIMEOUT_'+stage);await sleep(50);}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN)return reject(Error('OWN_CDP_CLOSED'));const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method));},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}
async function evaluate(expression){const v=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(v.exceptionDetails)throw Error('OWN_EXPERT_EVALUATE');return v.result.value;}
async function click(selector,text){return evaluate(`(()=>{const e=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(e=>e.getClientRects().length&&e.textContent.split('').filter(c=>c.trim()).join('')===${JSON.stringify(String(text).split('').filter(c=>c.trim()).join(''))}&&!e.disabled);if(!e)return false;e.click();return true})()`);}
const value=label=>evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
async function fill(label,text){if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(text)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_EXPERT_FIELD_'+label);}
async function ownAPI(entity,query){if(!['emergencyPlan','emergencyExercise'].includes(entity)||!/^get(?:Page|ById)\?/.test(query))throw Error('OWN_PLAN_READONLY_API');const ua=await evaluate('navigator.userAgent'),r=await fetch(wire.base+'/zhumadian/api/serv/'+entity+'/'+query,{headers:{Authorization:token,'User-Agent':ua}}),v=await r.json();if(r.status!==200||v.code!==0)throw Error('OWN_PLAN_API_READBACK');return v.data;}
let holdUpload=false,heldUpload=null,holdExercise=false,heldExercise=null,exercisePaused=0,injectExerciseFalse=false;
const count=suffix=>http.filter(x=>x.path.endsWith('/emergencyPlan/'+suffix)).length;
async function event(v){
 if(v.id){const p=pending.get(v.id);if(!p)return;pending.delete(v.id);v.error?p.reject(Error('OWN_CDP_'+v.error.code)):p.resolve(v.result);return;}
 if(v.method==='Browser.downloadWillBegin'){downloads.push({state:'begin',name:v.params.suggestedFilename});return;}
 if(v.method==='Browser.downloadProgress'){downloads.push({state:v.params.state,bytes:v.params.receivedBytes});return;}
 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request;let u;try{u=new URL(request.url)}catch{}
  if(u?.origin===wire.base&&u.pathname.endsWith('/sys-file/upload')&&holdUpload){if(heldUpload)throw Error('ONE_HELD_UPLOAD_ONLY');heldUpload={id:v.params.requestId,session:v.sessionId};return;}
  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyExercise/save')&&request.method==='POST'){
   exercisePaused++;
   if(injectExerciseFalse){injectExerciseFalse=false;await send('Fetch.fulfillRequest',{requestId:v.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_FALSE_INJECTION'})).toString('base64')},v.sessionId);return;}
   if(holdExercise){if(heldExercise)throw Error('DUPLICATE_HELD_EXERCISE');heldExercise={id:v.params.requestId,session:v.sessionId};return;}
  }
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/emergencyPlan/save','/emergencyPlan/updateById','/emergencyExercise/save','/sys-file/upload'].some(p=>u.pathname.endsWith(p));
  if(disallowed){blocked.push({origin:u?.origin||'invalid',path:u?.pathname||'',method:request.method});await send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},v.sessionId);}else await send('Fetch.continueRequest',{requestId:v.params.requestId},v.sessionId);
 }else if(v.method==='Network.responseReceived'){
  let u;try{u=new URL(v.params.response.url)}catch{};if(u?.origin===wire.base&&u.pathname.includes('/api/'))tracked.set(v.params.requestId,{path:u.pathname,httpStatus:v.params.response.status,session:v.sessionId});
 }else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);const p=send('Network.getResponseBody',{requestId:v.params.requestId},row.session).then(r=>{
   const bytes=r.base64Encoded?Buffer.from(r.body,'base64'):Buffer.from(r.body);let b;try{b=JSON.parse(bytes.toString('utf8'))}catch{row.nonJSON=true;row.bytes=bytes.length;delete row.session;http.push(row);return;}
   row.businessCode=b.code;if(row.path.endsWith('/emergencyExercise/save'))row.saved=b.data;if(row.path.endsWith('/oauth/Login')){token=b.data?.token||'';row.normalTokenReturned=!!token;}
   if(row.path.endsWith('/oauth/CurrentUser')){row.ownUserMatched=b.data?.userInfo?.userId===wire.expectedUserId;row.planMenuReturned=JSON.stringify(b.data?.menuList||[]).includes('/emergencyPlans/structured');}
   if(row.path.endsWith('/emergencyPlan/getPage')){row.total=b.data?.total;row.records=Array.isArray(b.data?.records)?b.data.records.length:null;}
   if(['/save','/updateById','/removeById'].some(p=>row.path.endsWith('/emergencyPlan'+p)))row.saved=b.data;
   delete row.session;http.push(row);
  }).catch(()=>{row.observationFailed=true;delete row.session;http.push(row)}).finally(()=>reads.delete(p));reads.add(p);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION',description:String(v.params.exceptionDetails?.exception?.description||'').slice(0,500)});
}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--window-size=1360,1000','--no-first-run','--disable-default-apps','--disable-sync','--disable-background-networking','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:'ignore'});
 await until(async()=>{try{await fs.access(O+'/chrome-profile/DevToolsActivePort');return true}catch{return false}});
 const lines=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split(/\r?\n/);ws=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',e=>{event(JSON.parse(e.data)).catch(()=>{})});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const method of ['Page.enable','Runtime.enable','Network.enable','DOM.enable'])await send(method,{},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.win32.resolve(O+'/downloads'),eventsEnabled:true});
 stage='normal-login';await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyPlans/structured'},session);
 await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([wire.account,wire.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})})()`);
 if(!await click('.login-body button','登录'))throw Error('OWN_LOGIN_BUTTON');
 await until(()=>http.some(x=>x.path.endsWith('/oauth/CurrentUser')&&x.ownUserMatched&&x.planMenuReturned));wire.password='';
 await until(()=>evaluate('!document.querySelector(".login-body")&&Array.from(document.querySelectorAll(".el-menu-item")).some(e=>e.textContent.trim()==="应急预案")'));
 if(!await click('.el-menu-item','应急预案'))throw Error('OWN_PLAN_MENU');await until(()=>count('getPage')>0);
 cases.push({case:'normal-nonadministrator-login-original-plan-menu-and-page',passed:true});
 const name='OWN_G_PLAN_R222_'+root.split('/').at(-1),exerciseName='OWN_G_EXERCISE_R222_'+root.split('/').at(-1);
 let writes=count('save');stage='required-plan-validation';if(!await click('.table-box button','新增'))throw Error('OWN_PLAN_ADD');
 await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
 await click('button','提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>=1'));
 if(count('save')!==writes)throw Error('EMPTY_PLAN_WRITTEN');cases.push({case:'plan-required-fields-block-write',passed:true});
 await fill('应急预案名称',name);await fill('指挥长','OWN_COMMANDER_R222');await fill('指挥长电话','invalid');
 if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('ORIGINAL_PLAN_FILINGS_RADIO');
 await click('button','提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>0'));
 if(count('save')!==writes)throw Error('INVALID_PLAN_PHONE_WRITTEN');cases.push({case:'plan-invalid-phone-keeps-editor-no-save',passed:true});
 await fill('指挥长电话','13800000000');await fill('处置措施','OWN_PLAN_MEASURES_R222');stage='actual-plan-create';
 await click('button','提交');await until(()=>count('save')>writes);let saved=http.filter(x=>x.path.endsWith('/emergencyPlan/save')).at(-1);
 if(saved.businessCode!==0||saved.saved!==true)throw Error('PLAN_SAVE_NOT_CONFIRMED');
 await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
 let page=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(name));
 if(Number(page.total)!==1)throw Error('OWN_PLAN_NOT_PERSISTED');const id=page.records[0].id;
 let detail=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));
 if(detail.emergencyPlanName!==name||detail.commanderPhone!=='13800000000'||String(detail.isFilings)!=='0'||detail.disposalMeasures!=='OWN_PLAN_MEASURES_R222')throw Error('PLAN_VALUES_LOST');
 await fs.writeFile(root+'/plan-context.private.json',JSON.stringify({id,name,ownedSyntheticOnly:true}));
 cases.push({case:'plan-native-create-original-controller-and-normal-role-detail-values',passed:true});
 async function filterOwn(){
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  if(await value('应急预案名称')===null)await click('.table-search button','更多');await fill('应急预案名称',name);
  const n=count('getPage');await click('.table-search button','搜索');await until(()=>count('getPage')>n);
  await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(e=>e.textContent.includes(${JSON.stringify(name)}))`));
 }
 await filterOwn();stage='plan-edit-and-readback';await click('.el-table__body-wrapper button','编辑');
 await until(async()=>await value('应急预案名称')===name);await fill('处置措施','OWN_PLAN_REVISED_R222');
 let edits=count('updateById');await click('button','提交');await until(()=>count('updateById')>edits);
 if(http.filter(x=>x.path.endsWith('/emergencyPlan/updateById')).at(-1).saved!==true)throw Error('PLAN_EDIT_NOT_CONFIRMED');
 await filterOwn();detail=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));if(detail.disposalMeasures!=='OWN_PLAN_REVISED_R222')throw Error('PLAN_EDIT_NOT_PERSISTED');
 await click('.el-table__body-wrapper button','详情');await until(async()=>await value('应急预案名称')===name);
 if(await value('处置措施')!=='OWN_PLAN_REVISED_R222'||!await evaluate('Array.from(document.querySelectorAll(".ele-page input,.ele-page textarea")).filter(e=>e.getClientRects().length).every(e=>e.disabled||e.readOnly)'))throw Error('PLAN_DETAIL_NOT_READONLY_OR_REVISED');
 cases.push({case:'plan-edit-reopen-detail-readonly-and-original-identity-kept',passed:true});await click('button','返回');await filterOwn();
 await click('.el-table__body-wrapper button','演练记录');
 const dialogTitle=t=>`Array.from(document.querySelectorAll('.el-dialog')).find(d=>d.getClientRects().length&&d.querySelector('.el-dialog__title')?.textContent.trim()===${JSON.stringify(t)})`;
 async function modalClick(title,selector,text){return evaluate(`(()=>{const d=${dialogTitle(title)},e=Array.from(d?.querySelectorAll(${JSON.stringify(selector)})||[]).find(e=>e.getClientRects().length&&e.textContent.trim()===${JSON.stringify(text)});e?.click();return!!e})()`);}
 await until(()=>evaluate(`!!(${dialogTitle('演练记录')})`));
 if(!await modalClick('演练记录','button','新增'))throw Error('OWN_EXERCISE_ADD');
 await until(()=>evaluate(`!!(${dialogTitle('新增演练记录')})`));stage='optional-participants-baseline-reproduction';
 await fill('演练地点',exerciseName+'_EMPTY');await fill('演练内容及过程描述','OWN_EMPTY_PARTICIPANTS_ALLOWED');
 const exerciseCount=()=>http.filter(x=>x.path.endsWith('/emergencyExercise/save')).length;
 const beforeEmpty=exerciseCount();await modalClick('新增演练记录','.el-dialog__footer button','确定');
 if(wire.baseline){
  await until(()=>exceptions.some(x=>/join|undefined/.test(x.description||'')));
  if(exerciseCount()!==beforeEmpty||await value('演练地点')!==exerciseName+'_EMPTY')throw Error('EXPECTED_BASELINE_EMPTY_PARTICIPANTS_REPRO_NOT_OBSERVED');
  await fs.writeFile(O+'/baseline-reproduction.json',JSON.stringify({reproduced:true,normalUserActualCompiledPage:true,optionalPersonSelectionLeftEmpty:true,uncaughtUndefinedJoinException:true,noExerciseSaveRequestSent:true,productChanged:false},null,2));
  cases.push({case:'baseline-real-normal-page-optional-persons-trigger-undefined-join-before-save',passed:true});
 }else{
  await until(()=>exerciseCount()>beforeEmpty);
  if(http.filter(x=>x.path.endsWith('/emergencyExercise/save')).at(-1).saved!==true)throw Error('EMPTY_PARTICIPANTS_SAVE_NOT_CONFIRMED');
  await until(()=>evaluate(`!(${dialogTitle('新增演练记录')})`));
  let exercises=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  let empty=exercises.records.find(x=>x.exerciseLocation===exerciseName+'_EMPTY');
  if(!empty||empty.emergencyPlanId!==id||empty.participants)throw Error('EMPTY_PERSON_RECORD_LINK_OR_CSV_WRONG');
  cases.push({case:'native-optional-participants-empty-save-and-parent-scoped-list-roundtrip',passed:true});
  await modalClick('演练记录','button','新增');await until(()=>evaluate(`!!(${dialogTitle('新增演练记录')})`));
  await fill('演练地点',exerciseName+'_FILE');await fill('总指挥','OWN_EXERCISE_COMMANDER');await fill('演练内容及过程描述','OWN_EXERCISE_PROCESS');
  stage='original-organization-and-person-selector';
  if(!await evaluate(`(()=>{const d=${dialogTitle('新增演练记录')},f=Array.from(d.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='组织部门');const e=f?.querySelector('.el-select__wrapper,.el-input__wrapper');e?.click();return!!e})()`))throw Error('EXERCISE_ORG_FIELD');
  let department;await until(async()=>{department=await evaluate('Array.from(document.querySelectorAll(".el-tree-node__content")).find(e=>e.getClientRects().length&&e.textContent.trim())?.textContent.trim()||""');return!!department});
  if(!await click('.el-tree-node__content',department))throw Error('EXERCISE_ORG_CHOICE');
  if(!await modalClick('新增演练记录','.person-list button','添加'))throw Error('ORIGINAL_PERSON_ADD');
  await until(()=>evaluate(`(${dialogTitle('选择人员')})?.querySelectorAll('.el-tree-node input[type=checkbox]').length>=2`));await sleep(650);
  await evaluate(`(()=>{const d=${dialogTitle('选择人员')};Array.from(d.querySelectorAll('.el-tree-node input[type=checkbox]')).slice(0,2).forEach(e=>e.click())})()`);
  await until(()=>evaluate(`(${dialogTitle('选择人员')})?.querySelector('.nums')?.textContent.includes('2')===true`));
  await modalClick('选择人员','.el-dialog__footer button','确认');await until(()=>evaluate(`(${dialogTitle('新增演练记录')})?.querySelectorAll('.person-list .check-user').length===2`));
  cases.push({case:'actual-org-tree-and-original-person-checkbox-dialog-select-two-people',passed:true});
  stage='pending-upload-submit-guard';
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j2ioAAAAASUVORK5CYII=','base64');
  const file=O+'/own-plan-exercise-r222.png';await fs.writeFile(file,png);holdUpload=true;
  const dom=await send('DOM.getDocument',{depth:-1},session),input=await send('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'input[type=file]'},session);
  if(!input.nodeId)throw Error('ORIGINAL_EXERCISE_FILE_INPUT');await send('DOM.setFileInputFiles',{nodeId:input.nodeId,files:[path.win32.resolve(file)]},session);
  await until(()=>heldUpload!==null);const beforeUploadSave=exerciseCount();await modalClick('新增演练记录','.el-dialog__footer button','确定');await sleep(200);
  if(exerciseCount()!==beforeUploadSave)throw Error('PENDING_UPLOAD_SUBMITTED_EXERCISE');
  holdUpload=false;const uploadRequest=heldUpload;heldUpload=null;await send('Fetch.continueRequest',{requestId:uploadRequest.id},uploadRequest.session);
  await until(()=>http.some(x=>x.path.endsWith('/sys-file/upload')&&x.httpStatus===200&&x.businessCode===0));
  await until(()=>evaluate(`(${dialogTitle('新增演练记录')})?.querySelector('.el-upload-list__item')?.textContent.includes('own-plan-exercise-r222.png')===true`));
  cases.push({case:'real-upload-held-before-network-blocks-submit-then-real-object-store-completes',passed:true});
  stage='explicit-false-response-keeps-editor';injectExerciseFalse=true;const beforeFalse=exerciseCount();await modalClick('新增演练记录','.el-dialog__footer button','确定');
  await until(()=>exerciseCount()>beforeFalse);
  if(http.filter(x=>x.path.endsWith('/emergencyExercise/save')).at(-1).saved!==false||await value('演练地点')!==exerciseName+'_FILE')throw Error('FALSE_RESULT_DID_NOT_KEEP_FORM');
  exercises=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  if(exercises.records.some(x=>x.exerciseLocation===exerciseName+'_FILE'))throw Error('FAULT_INJECTION_MUST_NOT_WRITE_BUSINESS_RECORD');
  cases.push({case:'browser-only-false-business-response-retains-dialog-fields-people-and-file-no-server-write',passed:true,realSQLFailureClaimed:false});
  stage='one-real-save-with-duplicate-protection';holdExercise=true;await modalClick('新增演练记录','.el-dialog__footer button','确定');await until(()=>heldExercise!==null);
  const initialPaused=exercisePaused;await modalClick('新增演练记录','.el-dialog__footer button','确定');await sleep(200);
  if(exercisePaused!==initialPaused)throw Error('DUPLICATE_EXERCISE_SAVE_SENT');
  holdExercise=false;const request=heldExercise;heldExercise=null;await send('Fetch.continueRequest',{requestId:request.id},request.session);
  await until(()=>evaluate(`!(${dialogTitle('新增演练记录')})`));
  exercises=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  const matches=exercises.records.filter(x=>x.exerciseLocation===exerciseName+'_FILE');if(matches.length!==1)throw Error('EXERCISE_RETRY_MUST_WRITE_ONCE');const exercise=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(matches[0].id));
  if(exercise.emergencyPlanId!==id||exercise.participants?.split(',').length!==2||exercise.exerciseDescribe!=='OWN_EXERCISE_PROCESS'||exercise.fileList?.length!==1)throw Error('EXERCISE_FIELDS_PEOPLE_FILES_NOT_PERSISTED');
  cases.push({case:'real-single-save-retry-preserves-two-people-parent-process-description-and-one-file',passed:true});
  const row=await evaluate(`(()=>{const d=${dialogTitle('演练记录')},r=Array.from(d.querySelectorAll('tbody tr')).find(e=>e.textContent.includes(${JSON.stringify(exerciseName+'_FILE')}));const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='查看');b?.click();return!!b})()`);
  if(!row)throw Error('EXERCISE_LIST_VIEW_BUTTON');await until(()=>evaluate(`!!(${dialogTitle('演练记录详情')})`));
  await until(async()=>await value('演练地点')===exerciseName+'_FILE');
  const currentLink=await evaluate(`(()=>{const d=${dialogTitle('演练记录详情')},a=d?.querySelector('a[href]');if(!a)return null;a.scrollIntoView({block:'center'});const r=a.getBoundingClientRect();return{href:a.href,x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  if(!currentLink||new URL(currentLink.href).origin!==wire.base)throw Error('ORIGINAL_OWN_FILE_DETAIL_LINK');
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:currentLink.x,y:currentLink.y,button:'left',clickCount:1},session);await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:currentLink.x,y:currentLink.y,button:'left',clickCount:1},session);
  await until(()=>downloads.some(x=>x.state==='completed'));const downloaded=await fs.readdir(O+'/downloads');if(downloaded.length!==1||!(await fs.readFile(O+'/downloads/'+downloaded[0])).equals(png))throw Error('EXERCISE_NATIVE_ATTACHMENT_DISK_BYTES');
  cases.push({case:'native-exercise-list-view-readonly-details-and-actual-anchor-disk-download-identical',passed:true});
  if(exceptions.length)throw Error('CANDIDATE_ORIGINAL_UI_EXCEPTION');
 }
 await Promise.allSettled([...reads]);
 await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baseline:!!wire.baseline,originalNormalLoginAndNativeRoutes:true,onlyOwnedSyntheticPlanExerciseRows:true,fullNangangOrWholeModuleAccepted:false,publicOrFormalOrDesktopChanged:false,http,blocked,exceptions:exceptions.map(x=>({text:x.text,optionalJoinObserved:/join|undefined/.test(x.description||'')}))},null,2));

}catch(e){failed=String(e.message);const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads};try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,text:document.body.innerText.slice(-1800)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{wire.password='';token='';if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}if(chrome)await new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));}
if(failed)throw Error(failed);
