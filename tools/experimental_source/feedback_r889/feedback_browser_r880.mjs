/** Full compiled application, real original login/detail/approval. No API doubles. */
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
let raw='';for await(const part of process.stdin){raw+=part;if(raw.length>32768)throw Error('BOUNDED_PRIVATE_WIRE_REQUIRED')}
const w=JSON.parse(raw);raw='';
const root='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/feedback-r880';
if(!['feedback-submit','feedback-readonly'].includes(w.mode)||w.syntheticNormalUser!==true||w.ownCaptchaPolicyDisabled!==true||
    !/^http:\/\/127\.0\.0\.1:\d{4,5}$/.test(w.base)||[18891,18892,8767].includes(+new URL(w.base).port)||
    !['own_operator_a','own_reviewer_b'].includes(w.account)||!/^a531[0-9a-f]{28}$/.test(w.expectedUserId)||
    typeof w.password!=='string'||!/^OWN_MANAGER_APPROVAL_[0-9a-f]{32}$/.test(w.opinion))throw Error('EXACT_OWN_NORMAL_UI_WIRE_REQUIRED');
for(const key of ['taskId','instanceId','operatorId','engineTaskId','versionId'])if(!/^[A-Za-z0-9_-]{1,128}$/.test(w[key]))throw Error('KNOWN_OWN_WORKFLOW_LINK_REQUIRED');
if(w.account!=='own_operator_a'||!/^OWN_MANAGER_[0-9a-f]{32}$/.test(w.taskName)||!/^OWN_FEEDBACK_[0-9a-f]{32}$/.test(w.feedback)||!/^OWN_EVALUATION_[0-9a-f]{32}$/.test(w.evaluation))throw Error('EXACT_NORMAL_FEEDBACK_ACTOR_REQUIRED');
if(await fs.readFile(root+'/own-normal-manager-test.marker','utf8')!=='own-original-manager-full-lifecycle-r609\n')throw Error('EXACT_OWN_UI_MARKER_REQUIRED');
if(w.eventId!=='a5320000000000000000000000000006')throw Error('OWN_CONFIRMED_EVENT_REQUIRED');
const O=root+'/ui-'+w.mode+'-r889';await fs.mkdir(O);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let chrome,ws,session,active,seq=0,token='',current=null,problem=null,stage='start';
const pending=new Map(),tracked=new Map(),reads=new Set(),requests=[],cases=[],exceptions=[];
let detail=null,nativeList=null,baseline=null,audits=0,proof;
const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];let taskList=null,taskDetail=null,feedbackIssued=0,feedbackConfirmed=false;
function save(name,value){return fs.writeFile(O+'/'+name,JSON.stringify(value,null,2)+'\n')}

const digest=value=>createHash('sha256').update(value).digest('hex');
function fieldIdentity(data){
 if(!data||typeof data!=='object'||Array.isArray(data))throw Error('ORIGINAL_NATIVE_FORM_OBJECT_REQUIRED');
 const present=Object.hasOwn(data,'inputField101'),value=data.inputField101;
 if(present&&value!==null&&typeof value!=='string')throw Error('ORIGINAL_TEXT_FIELD_TYPE_REQUIRED');
 return{nativeFieldPresent:String(present),nativeFieldType:!present?'absent':value===null?'null':'string',
  databaseFieldCanonicalSHA256:digest(value==null?'null':'string:'+value),
  payloadFieldSHA256:digest(JSON.stringify([present,value??null])),displaySHA256:digest(value??'')};
}
const sameField=data=>{try{return baseline!==null&&fieldIdentity(data).payloadFieldSHA256===baseline.payloadFieldSHA256}catch{return false}};
async function captureOrMatchNativeField(data){
 const actual=fieldIdentity(data),file=root+'/original-field-baseline-r806.private.properties';
 if(baseline===null){
  if(w.mode==='pending-approve'){
   baseline=actual;const lines=['schema=xnby.original-manager-field-baseline.r806.v1',...Object.entries(baseline).map(([k,v])=>k+'='+v)];
   await fs.writeFile(file,lines.join('\n')+'\n',{flag:'wx'});
  }else{
   baseline=Object.fromEntries((await fs.readFile(file,'ascii')).trim().split('\n').map(line=>line.split('=')));
   if(baseline.schema!=='xnby.original-manager-field-baseline.r806.v1')throw Error('EXACT_NATIVE_BASELINE_REQUIRED');
  }
 }
 if(w.mode==='pending-approve'){
  if(Object.entries(actual).some(([key,value])=>baseline[key]!==value))throw Error('ORIGINAL_NATIVE_READONLY_VALUE_CHANGED');
 }else{
  if(actual.databaseFieldCanonicalSHA256!==baseline.databaseFieldCanonicalSHA256||actual.displaySHA256!==baseline.displaySHA256)throw Error('ORIGINAL_REOPENED_FIELD_VALUE_CHANGED');
  if(actual.payloadFieldSHA256!==baseline.payloadFieldSHA256){
   if(!['absent','null'].includes(actual.nativeFieldType)||!['absent','null'].includes(baseline.nativeFieldType))throw Error('ONLY_PROVEN_NULL_ABSENT_NORMALIZATION_ALLOWED');
   if(!cases.some(c=>c.case==='original-null-absent-normalization-keeps-same-database-and-display-value'))cases.push({case:'original-null-absent-normalization-keeps-same-database-and-display-value',passed:true,originalFieldType:baseline.nativeFieldType,reopenedFieldType:actual.nativeFieldType});
  }
 }
}
async function until(fn,ms=45000){const end=Date.now()+ms;for(;;){if(await fn())return;if(problem)throw Error(problem);if(Date.now()>end)throw Error('OWN_NORMAL_UI_OBSERVATION_TIMEOUT');await sleep(50)}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT'))},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...sid?{sessionId:sid}:{}}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw Error('OWN_NORMAL_UI_DOM_FAILED');return r.result.value}
function observe(v){
 if(v.method==='Network.requestWillBeSent'){
  const u=new URL(v.params.request.url);if(u.origin===w.base&&u.pathname.endsWith('.js'))assets.push(u.pathname);
  if(u.origin===w.base&&u.pathname==='/zhumadian/emergency/branding-20261025/login')problem='BUSINESS_LOGOUT_USED_STATIC_BASE';
 }

 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request,u=new URL(request.url);let allowed=u.origin===w.base||['about:','data:','blob:'].includes(u.protocol);

  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventTask/updateById'){
   let body;try{body=JSON.parse(request.postData||'')}catch{}
   const exact=body&&Object.keys(body).sort().join(',')==='disposeTime,evaluationSum,feedbackInfo,id,taskStatus'&&body.id===w.taskId&&body.taskStatus==='1'&&body.feedbackInfo===w.feedback&&body.evaluationSum===w.evaluation&&body.disposeTime==='2026-11-04 17:30:00';
   if(w.mode==='feedback-submit'&&request.method==='POST'&&feedbackIssued===0&&exact){
    feedbackIssued++;
    save('feedback-issued.json',{issuedOnce:true,exactOwnedTask:true,originalSparseFiveFieldsOnly:true,requestSHA256:digest(request.postData),mutationsRetried:false}).then(()=>send('Fetch.continueRequest',{requestId:v.params.requestId},session)).catch(()=>{problem='OWN_FEEDBACK_INTENT_OR_CONTINUE_FAILED'});return;
   }
   problem='UNEXPECTED_OR_DUPLICATE_OWN_FEEDBACK_REFUSED';send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},session).catch(()=>{});return;
  }
  if(u.origin===w.base&&u.pathname.startsWith('/zhumadian/api/')&&/\/(removeById|callback|delete)(\/|$)/i.test(u.pathname)){
   problem='UNEXPECTED_MUTATING_GET_REFUSED';send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},session).catch(()=>{});return;
  }
  if(u.origin===w.base&&!['GET','HEAD'].includes(request.method)&&u.pathname!=='/zhumadian/api/jnpf/oauth/Login'){
   let query;try{query=JSON.parse(request.postData||'')}catch{}
   const selectorQuery=request.method==='POST'&&u.pathname==='/zhumadian/api/jnpf/permission/Users/ImUser/Selector/0'&&
    query&&Object.keys(query).sort().join(',')==='currentPage,keyword,organizeId,pageSize'&&
    query.currentPage===1&&query.pageSize===20&&query.keyword===''&&query.organizeId===0;
   if(!selectorQuery){allowed=false;problem='READONLY_BROWSER_UNEXPECTED_MUTATION_REFUSED';
    save('blocked-request.json',{method:request.method,path:u.pathname,selectorQueryMatched:false}).catch(()=>{});}
  }
  if(u.origin===w.base&&u.pathname.includes('/FlowBefore/Audit/')){
   allowed=allowed&&w.mode==='pending-approve'&&request.method==='POST'&&audits===0;
   let data;try{data=JSON.parse(request.postData||'')}catch{allowed=false}
   const readonlyMatched=sameField(data?.formData),opinionMatched=data?.handleOpinion===w.opinion;
   allowed=allowed&&readonlyMatched&&opinionMatched;
   if(allowed){audits++;fs.writeFile(O+'/approval-issued.json',JSON.stringify({issuedOnce:true,readonlyValueMatched:true,opinionMatched:true,
      requestSHA256:createHash('sha256').update(request.postData).digest('hex'),mutationsRetried:false})+'\n').then(()=>send('Fetch.continueRequest',{requestId:v.params.requestId},session)).catch(()=>{problem='OWN_APPROVAL_JOURNAL_OR_CONTINUE_FAILED'});return}
   problem='UNEXPECTED_OR_DUPLICATE_UI_APPROVAL_REFUSED';
  }
  send(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:v.params.requestId,...allowed?{}:{errorReason:'BlockedByClient'}},session).catch(()=>{});
 }else if(v.method==='Network.requestWillBeSent'){
  const request=v.params.request,u=new URL(request.url);if(u.origin!==w.base||!u.pathname.startsWith('/zhumadian/api/'))return;
  if(tracked.size>256){problem='BOUNDED_ORIGINAL_UI_HTTP_REQUIRED';return}
  tracked.set(v.params.requestId,{endpoint:u.pathname.replace(/(\/FlowBefore\/)(?!List|Audit)[^/]+$/,'$1[owned-id]').replace(/(\/Audit\/)[^/]+$/,'$1[owned-node]'),path:u.pathname,method:request.method});
 }else if(v.method==='Network.responseReceived'&&tracked.has(v.params.requestId))tracked.get(v.params.requestId).httpStatus=v.params.response.status;
 else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);tracked.delete(v.params.requestId);
  const read=send('Network.getResponseBody',{requestId:v.params.requestId},session).then(r=>{
   let body;try{body=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body)}catch{row.nonJSON=true;return}
   row.businessCode=body.code;
   if(row.path.endsWith('/oauth/Login')){if(body.code!==200)problem='ORIGINAL_NORMAL_LOGIN_REFUSED';token=body.data?.token||''}
   if(row.path.endsWith('/eventTask/getPage')&&body.code===0)taskList=body.data;
   if(row.path.startsWith('/zhumadian/api/serv/eventTask/getById')&&body.code===0)taskDetail=body.data;
   if(row.path.endsWith('/eventTask/updateById')){feedbackConfirmed=body.code===0&&body.data===true;if(!feedbackConfirmed)problem='ORIGINAL_FEEDBACK_UPDATE_NOT_SAVED';}
   if(row.path.endsWith('/oauth/CurrentUser')){current=body.data;if(body.code!==200||current?.userInfo?.userId!==w.expectedUserId||current?.userInfo?.isAdministrator!==false)problem='EXACT_NORMAL_NONADMIN_REQUIRED'}
   if((row.path.endsWith('/FlowBefore/List/1')||row.path.endsWith('/Engine/FlowLaunch'))&&body.code===200)nativeList=body.data;
   if(/^\/zhumadian\/api\/jnpf\/workflow\/Engine\/FlowBefore\/[^/]+$/.test(row.path)&&body.code===200){detail=body.data;row.knownInstanceMatched=detail?.flowTaskInfo?.id===w.instanceId;row.originalReadonlyFieldType=detail?.formData&&Object.hasOwn(detail.formData,"inputField101")?(detail.formData.inputField101===null?"null":typeof detail.formData.inputField101):"absent"}
   if(row.path.includes('/FlowBefore/Audit/'))row.originalApprovalSuccess=row.httpStatus===200&&body.code===200;
  }).catch(()=>{row.responseBodyObserved=false;row.observationFailure='CDP_RESPONSE_BODY_UNAVAILABLE';const essential=row.path.endsWith('/oauth/Login')||row.path.endsWith('/oauth/CurrentUser')||row.path.includes('/workflow/Engine/FlowBefore/');if(essential)problem='ORIGINAL_ESSENTIAL_UI_RESPONSE_OBSERVATION_FAILED';else row.auxiliaryObservationUnavailable=true;}).finally(()=>{delete row.path;requests.push(row);reads.delete(read)});reads.add(read);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION'});
}
async function closeBrowser(){
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close()}
 let next=0;while(chrome?.pid&&chrome.exitCode===null&&chrome.signalCode===null){
  if(active&&Date.now()>next){next=Date.now()+3000;try{const s=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);s.addEventListener('error',()=>{});s.addEventListener('open',()=>s.send(JSON.stringify({id:1,method:'Browser.close'})),{once:true});setTimeout(()=>s.close(),2000)}catch{}}
  await sleep(100);
 }
}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',x=>fs.appendFile(O+'/chrome.private.log',x));chrome.on('exit',()=>{for(const p of pending.values())p.reject(Error('OWN_CHROME_EXITED'));pending.clear()});
 await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});
 ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',event=>{const v=JSON.parse(event.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p)v.error?p.reject(Error('OWN_CDP_ERROR')):p.resolve(v.result)}else observe(v)});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const name of ['Page','Runtime','Network'])await send(name+'.enable',{},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);
 stage='normal-compiled-login';loginStarted=Date.now();await send('Page.navigate',{url:w.base+'/zhumadian/emergency/home/index'},session);
 await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 loginVisibleMs=Date.now()-loginStarted;anonymousAssets=[...new Set(assets)];
 if(anonymousAssets.some(p=>p.includes('wf-authenticated-components-')))throw Error('FULL_COMPONENTS_FETCHED_BEFORE_LOGIN');
 if(await evaluate('!!document.querySelector("#app").__vue_app__._context.components.ElTransfer'))throw Error('FULL_COMPONENTS_REGISTERED_BEFORE_LOGIN');
 cases.push({case:'anonymous-login-renders-without-full-component-installer',passed:true});

 await evaluate(`(()=>{const values=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});const b=Array.from(document.querySelectorAll('.login-body button')).find(e=>e.textContent.trim()==='登录');if(!b)throw Error('NORMAL_LOGIN_BUTTON_REQUIRED');b.click()})()`);
 await until(()=>token&&current);cases.push({case:'normal-original-compiled-nonadmin-login',passed:true});
 await until(()=>evaluate('document.querySelectorAll("[data-workflow-route]").length===3'));
 if(!assets.some(p=>p.includes('wf-authenticated-components-')))throw Error('ORIGINAL_FULL_INSTALLER_NOT_LOADED_AFTER_LOGIN');
 if(!await evaluate('(()=>{const c=document.querySelector("#app").__vue_app__._context.components;return ["ElInput","ElForm","ElSelect","ElTreeSelect","ElDatePicker","ElTransfer","ElUpload","EleProTable"].every(n=>!!c[n])})()'))throw Error('ORIGINAL_GLOBAL_COMPONENTS_MISSING_AFTER_LOGIN');
 cases.push({case:'all-original-global-components-registered-before-authenticated-home',passed:true});
 if(assets.some(p=>p.startsWith('/zhumadian/emergency/assets/')))throw Error('UNVERSIONED_PRELOAD_ALIAS_STILL_REQUESTED');
 cases.push({case:'canonical-static-urls-avoid-unversioned-preload-alias',passed:true});


 stage='original-owned-task-list';taskList=null;
 await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/taskSend'},session);
 await until(()=>Array.isArray(taskList?.records)&&evaluate('!!document.querySelector(".table-search")'));
 async function fill(label,value){
  const ok=await evaluate(`(()=>{const controls=[...new Set(Array.from(document.querySelectorAll('.el-form-item')).filter(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\s:：]/g,'')===${JSON.stringify(label)}).flatMap(e=>Array.from(e.querySelectorAll('input,textarea'))))].filter(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly);if(controls.length!==1)return false;const input=controls[0];input.value=${JSON.stringify(value)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));input.dispatchEvent(new Event('blur',{bubbles:true}));return true})()`);
  if(!ok)throw Error('ORIGINAL_NORMAL_FEEDBACK_FIELD_REQUIRED');
 }
 async function search(){
  await until(()=>evaluate('!!document.querySelector(".table-search")'));await fill('任务名称',w.taskName);taskList=null;
  await evaluate('Array.from(document.querySelectorAll(".table-search button")).find(e=>e.textContent.trim()==="搜索").click()');
  await until(()=>Array.isArray(taskList?.records));
  const rows=taskList.records.filter(r=>r.id===w.taskId&&r.taskName===w.taskName&&r.flowId===w.instanceId&&r.infoId===w.eventId);
  if(rows.length!==1)throw Error('EXACT_EXISTING_OWN_FEEDBACK_TASK_REQUIRED');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).filter(e=>e.textContent.includes('+JSON.stringify(w.taskName)+')).length===1'));
  return rows[0];
 }
 async function action(label){
  const ok=await evaluate(`(()=>{const rows=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(w.taskName)}));if(rows.length!==1)return false;const b=Array.from(rows[0].querySelectorAll('button')).find(e=>e.getClientRects().length&&e.textContent.trim()===${JSON.stringify(label)});if(!b||b.disabled)return false;b.click();return true})()`);
  if(!ok)throw Error('ORIGINAL_FEEDBACK_ROW_ACTION_REQUIRED');
 }
 const owned=await search();
 if(w.mode==='feedback-submit'){
  if(owned.taskStatus!=='2')throw Error('REAL_PENDING_TASK_REQUIRED_BEFORE_FEEDBACK');
  taskDetail=null;stage='original-disposal-form';await action('处置');
  await until(()=>taskDetail?.id===w.taskId&&evaluate('new URL(location.href).searchParams.get("judge")==="1"&&document.querySelectorAll("textarea:not(:disabled)").length===2'));
  if(taskDetail.flowId!==w.instanceId||taskDetail.infoId!==w.eventId||['feedbackInfo','evaluationSum','disposeTime'].some(k=>taskDetail[k]!=null&&taskDetail[k]!==''))throw Error('ONLY_NEW_OWN_EMPTY_FEEDBACK_TASK_REQUIRED');
  cases.push({case:'real-pending-task-row-opens-original-disposal-form',passed:true});
  await fill('处置时间','2026-11-04 17:30:00');
  await evaluate('(()=>{const controls=[...new Set(Array.from(document.querySelectorAll(".el-form-item")).filter(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="处置时间").flatMap(e=>Array.from(e.querySelectorAll("input"))))].filter(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly);if(controls.length!==1)throw Error("ONE_EDITABLE_DISPOSAL_TIME_REQUIRED");const e=controls[0];e.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",code:"Enter",bubbles:true}));e.blur()})()');
  await fill('反馈信息',w.feedback);await fill('评估总结',w.evaluation);
  stage='one-original-feedback-submit';
  await evaluate('(()=>{const b=Array.from(document.querySelectorAll("button")).find(e=>e.getClientRects().length&&e.textContent.trim()==="提交");if(!b||b.disabled)throw Error("ORIGINAL_FEEDBACK_SUBMIT_REQUIRED");b.click();b.click()})()');
  await until(()=>feedbackConfirmed&&evaluate('location.pathname.endsWith("/emergencyResponse/taskSend")'));
  if(feedbackIssued!==1)throw Error('ONE_FEEDBACK_UPDATE_REQUIRED');
  cases.push({case:'one-real-original-sparse-feedback-update-after-double-click',passed:true});
 }else if(owned.taskStatus!=='1')throw Error('APPROVED_TASK_MUST_REMAIN_COMPLETED');
 stage='original-persisted-feedback-detail';await search();taskDetail=null;await action('详情');
 await until(()=>taskDetail?.id===w.taskId&&evaluate('location.pathname.endsWith("/taskSend/detail")'));
 if(taskDetail.flowId!==w.instanceId||taskDetail.infoId!==w.eventId||taskDetail.taskStatus!=='1'||taskDetail.feedbackInfo!==w.feedback||taskDetail.evaluationSum!==w.evaluation||taskDetail.disposeTime!=='2026-11-04 17:30:00')throw Error('ORIGINAL_FEEDBACK_FIELDS_OR_LINKS_NOT_PERSISTED');
 const visible=await evaluate(`({values:[${JSON.stringify(w.feedback)},${JSON.stringify(w.evaluation)},'2026-11-04 17:30:00'].every(v=>document.body.innerText.includes(v)||Array.from(document.querySelectorAll('input,textarea')).some(e=>e.getClientRects().length&&e.value===v)),submit:Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length&&e.textContent.trim()==='提交'),editable:Array.from(document.querySelectorAll('textarea')).some(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly),judge:new URL(location.href).searchParams.has('judge')})`);
 if(!visible.values||visible.submit||visible.editable||visible.judge)throw Error('ORIGINAL_READONLY_FEEDBACK_RENDER_REQUIRED');
 cases.push({case:w.mode==='feedback-submit'?'real-detail-renders-saved-feedback-evaluation-and-time':'normal-restart-detail-retains-original-feedback-evaluation-and-time',passed:true,sameOriginalInstance:true});
 await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_FEEDBACK_UI_EXCEPTION');
 stage='normal-header-logout-business-root';
 const avatar=await evaluate('(()=>{const e=document.querySelector(".header-avatar");if(!e)return null;const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()');
 if(!avatar)throw Error('ORIGINAL_HEADER_USER_CONTROL_REQUIRED');
 await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:avatar.x,y:avatar.y},session);
 await until(()=>evaluate('Array.from(document.querySelectorAll(".el-dropdown-menu__item")).some(e=>e.getClientRects().length&&e.textContent.includes("退出"))'));
 await evaluate('Array.from(document.querySelectorAll(".el-dropdown-menu__item")).find(e=>e.getClientRects().length&&e.textContent.includes("退出")).click()');
 await until(()=>evaluate('!!document.querySelector(".el-message-box__btns .el-button--primary")'));
 await evaluate('document.querySelector(".el-message-box__btns .el-button--primary").click()');
 await until(()=>evaluate('location.pathname==="/zhumadian/emergency/login"&&document.querySelectorAll(".login-body input").length===3'));
 cases.push({case:'normal-header-logout-returns-to-business-login-not-static-base',passed:true});
 proof={passed:true,mode:w.mode,cases,requests,actualCompiledApplicationAndOriginalSDK:true,APIsMocked:false,
  taskCreationUIAccepted:false,approvalUIAccepted:false,approvalRequests:audits,feedbackUpdateRequests:feedbackIssued,feedbackSaveConfirmed:feedbackConfirmed,actualOriginalTaskFeedbackUI:true,
  credentialOrTokenPersistedInProof:false,loginVisibleMs,anonymousJavaScriptRequests:anonymousAssets,fullInstallerRequestedOnlyAfterLogin:true,allJavaScriptRequests:[...new Set(assets)],originalFieldBaselineSHA256:baseline?.databaseFieldCanonicalSHA256,baselineIsNativeDetailValue:true,publicOrDesktopTouched:false,fullCloneReady:false};
}catch(error){proof={passed:false,stage,failure:error.message,cases,requests,approvalRequests:audits,feedbackUpdateRequests:feedbackIssued,feedbackSaveConfirmed:feedbackConfirmed,APIsMocked:false,fullCloneReady:false};
 try{await save('diagnostic.private.json',await evaluate('({path:location.pathname,onlineFieldPresent:!!document.querySelector("[data-online-field]"),auditPresent:!!document.querySelector(".audit-form"),alerts:Array.from(document.querySelectorAll(".el-alert,.el-message")).map(e=>e.textContent.slice(0,120)),visibleHeadings:Array.from(document.querySelectorAll("h1,h2,h3")).map(e=>e.textContent)})()'))}catch{}
}finally{
 token='';current=null;detail=null;w.password='';
 await closeBrowser();await save('browser-terminal.json',{normalBrowserClosed:chrome?.exitCode===0,exitCode:chrome?.exitCode,forceTerminationUsed:false});
 await save('result.json',proof);
}
process.stdout.write(JSON.stringify({passed:proof.passed,mode:w.mode,cases:proof.cases.length,approvalRequests:audits,normalBrowserClosed:chrome?.exitCode===0}));
if(!proof.passed||chrome?.exitCode!==0)process.exitCode=1;
