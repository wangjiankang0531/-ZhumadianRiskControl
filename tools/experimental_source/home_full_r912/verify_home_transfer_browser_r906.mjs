/** Full compiled application, real original login/detail/approval. No API doubles. */
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
let raw='';for await(const part of process.stdin){raw+=part;if(raw.length>32768)throw Error('BOUNDED_PRIVATE_WIRE_REQUIRED')}
const w=JSON.parse(raw);raw='';
const root='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/task-ui-r806';
if(!['pending-approve','completed-readonly'].includes(w.mode)||w.syntheticNormalUser!==true||w.ownCaptchaPolicyDisabled!==true||
    !/^http:\/\/127\.0\.0\.1:\d{4,5}$/.test(w.base)||[18891,18892,8767].includes(+new URL(w.base).port)||
    !['own_operator_a','own_reviewer_b'].includes(w.account)||!/^a531[0-9a-f]{28}$/.test(w.expectedUserId)||
    typeof w.password!=='string'||!/^OWN_MANAGER_APPROVAL_[0-9a-f]{32}$/.test(w.opinion))throw Error('EXACT_OWN_NORMAL_UI_WIRE_REQUIRED');
for(const key of ['taskId','instanceId','operatorId','engineTaskId','versionId'])if(!/^[A-Za-z0-9_-]{1,128}$/.test(w[key]))throw Error('KNOWN_OWN_WORKFLOW_LINK_REQUIRED');
if(w.mode==='pending-approve'&&w.account!=='own_reviewer_b'||w.mode==='completed-readonly'&&w.account!=='own_operator_a')throw Error('EXACT_NORMAL_UI_ACTOR_REQUIRED');
if(await fs.readFile(root+'/own-normal-manager-test.marker','utf8')!=='own-original-manager-full-lifecycle-r609\n')throw Error('EXACT_OWN_UI_MARKER_REQUIRED');
if(w.mode!=='completed-readonly')throw Error('READ_ONLY_EXISTING_TASK_ONLY');
const O='D:/Project/Zhumadian/work/home-browser-r912';await fs.mkdir(O);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let chrome,ws,session,active,seq=0,token='',current=null,problem=null,stage='start';
const pending=new Map(),tracked=new Map(),reads=new Set(),requests=[],cases=[],exceptions=[];
let detail=null,nativeList=null,baseline=null,audits=0,proof;
const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];
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
const homeResourceRequests=[];let homeAssetObservation=false;
function observe(v){
 if(homeAssetObservation&&v.method==='Network.requestWillBeSent'){const u=new URL(v.params.request.url);if(u.origin===w.base&&u.pathname.includes('/assets/'))homeResourceRequests.push(u.pathname);}

 if(v.method==='Network.requestWillBeSent'){
  const u=new URL(v.params.request.url);if(u.origin===w.base&&u.pathname.endsWith('.js'))assets.push(u.pathname);
  if(u.origin===w.base&&u.pathname==='/zhumadian/emergency/branding-20261025/login')problem='BUSINESS_LOGOUT_USED_STATIC_BASE';
 }

 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request,u=new URL(request.url);let allowed=u.origin===w.base||['about:','data:','blob:'].includes(u.protocol);
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
   row.businessCode=body.code;if(row.path.endsWith('/oauth/CurrentUser')){row.userInfoPresent=!!body.data?.userInfo;row.menuListIsArray=Array.isArray(body.data?.menuList);}
   if(row.path.endsWith('/oauth/Login')){if(body.code!==200)problem='ORIGINAL_NORMAL_LOGIN_REFUSED';token=body.data?.token||''}
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

 for(const [route,endpoint] of [['/emergencyResponse/response','/eventInfo/getPage'],['/emergencyResponse/taskSend','/eventTask/getPage']]){
  const start=Date.now(),seen=requests.length;
  await send('Page.navigate',{url:w.base+'/zhumadian/emergency'+route},session);
  await until(()=>requests.slice(seen).some(r=>r.endpoint.endsWith(endpoint)&&r.httpStatus===200&&r.businessCode===0));
  await until(()=>evaluate('!!document.querySelector(".el-table__body-wrapper")'));
  cases.push({case:'original-business-list-and-registered-form-components',route,passed:true,navigationMs:Date.now()-start});
 }

 let url;
 if(w.mode==='pending-approve'){
  stage='actual-native-pending-list';await send('Page.navigate',{url:w.base+'/zhumadian/emergency/workflow/flowTodo'},session);
  await until(()=>Array.isArray(nativeList?.list));
  const matches=nativeList.list.map((row,index)=>({row,index})).filter(x=>x.row.processInstanceId===w.instanceId);
  if(matches.length!==1)throw Error('EXACT_OWN_TASK_MUST_BE_IN_REAL_NATIVE_PENDING_LIST');
  const {row,index}=matches[0];
  if(row.id!==w.engineTaskId)throw Error('ORIGINAL_NATIVE_LIST_ENGINE_TASK_ID_REQUIRED');
  await until(()=>evaluate('document.querySelectorAll(".work-item").length==='+nativeList.list.length));
  detail=null;await evaluate('document.querySelectorAll(".work-item")['+index+'].click()');
  await until(()=>detail?.flowTaskInfo?.id===w.instanceId);
  url=await evaluate('location.href');const actual=new URL(url);
  if(actual.origin!==w.base||actual.pathname!=='/zhumadian/emergency/workflow/flowTodo/detail'||actual.searchParams.get('id')!==w.engineTaskId)throw Error('ACTUAL_NATIVE_CARD_ROUTE_REQUIRED');
  cases.push({case:'real-native-list-card-opens-engine-task-detail',passed:true,routeOperatorIdSubstituted:false});
 }else{
  stage='actual-native-initiator-list';await send('Page.navigate',{url:w.base+'/zhumadian/emergency/workflow/startWithMeTwo'},session);
  await until(()=>Array.isArray(nativeList?.list));
  const matches=nativeList.list.map((row,index)=>({row,index})).filter(x=>x.row.id===w.instanceId||x.row.processInstanceId===w.instanceId);
  if(matches.length!==1)throw Error('EXACT_COMPLETED_OWN_TASK_MUST_BE_IN_REAL_INITIATOR_LIST');
  await until(()=>evaluate('document.querySelectorAll(".work-item").length==='+nativeList.list.length));
  detail=null;await evaluate('document.querySelectorAll(".work-item")['+matches[0].index+'].click()');
  await until(()=>detail?.flowTaskInfo?.id===w.instanceId);
  url=await evaluate('location.href');const actual=new URL(url);
  if(actual.origin!==w.base||actual.pathname!=='/zhumadian/emergency/workflow/startWithMe/examine')throw Error('ACTUAL_NATIVE_INITIATOR_CARD_ROUTE_REQUIRED');
  cases.push({case:'real-native-initiator-card-opens-same-completed-instance',passed:true});
 }
 async function loadDetail(){
  detail=null;await send('Page.navigate',{url},session);
  await until(()=>detail?.flowTaskInfo?.id===w.instanceId);
  if(detail?.flowFormInfo?.enCode!=='tj_eventTask'||Number(detail.flowFormInfo.formType)!==2)throw Error('EXACT_ORIGINAL_TASK_ONLINE_FORM_REQUIRED');
  await captureOrMatchNativeField(detail.formData);
  await until(()=>evaluate('!!document.querySelector("input[data-online-field=inputField101]")'));
  const originalValue=await evaluate('(()=>{const e=document.querySelector("input[data-online-field=inputField101]");return {value:e.value,disabled:e.disabled,readonly:e.readOnly}})()');
  if(digest(originalValue.value)!==baseline.displaySHA256||!originalValue.disabled||!originalValue.readonly)throw Error('ORIGINAL_MANAGER_FIELD_MUST_RENDER_READONLY');
  cases.push({case:'real-sdk-detail-instance-and-readonly-form-rendered',passed:true});
 }
 stage='actual-original-pending-detail';await loadDetail();
 stage='actual-detail-refresh';await loadDetail();cases.push({case:'full-page-refresh-retains-native-original-readonly-value',passed:true});
 if(w.mode==='pending-approve'){
  stage='original-page-one-approval';await until(()=>evaluate('!!document.querySelector(".audit-form textarea")'));
  const selected=await evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).map(e=>e.textContent.trim())');
  if(selected.length!==1||!['通过','提交审核',w.approveLabel].includes(selected[0]))throw Error('ORIGINAL_APPROVE_ACTION_REQUIRED');
  await evaluate(`(()=>{const e=document.querySelector('.audit-form textarea');e.value=${JSON.stringify(w.opinion)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  await evaluate(`(()=>{const b=Array.from(document.querySelectorAll('.audit-form button')).find(e=>e.textContent.trim()==='提交');if(!b||b.disabled)throw Error('NORMAL_SUBMIT_REQUIRED');b.click()})()`);
  await until(()=>requests.some(r=>r.originalApprovalSuccess));
  if(audits!==1)throw Error('ONE_ORIGINAL_UI_APPROVAL_REQUIRED');
  cases.push({case:'real-page-submitted-once-original-sdk-approved',passed:true,readonlyValuePreserved:true});
 }else{
  if(await evaluate('!!document.querySelector(".audit-form")'))throw Error('COMPLETED_TASK_MUST_NOT_OFFER_APPROVAL');
  if(!await evaluate('document.body.textContent.includes('+JSON.stringify(w.opinion)+')'))throw Error('ORIGINAL_MANAGER_OPINION_MUST_RENDER_AFTER_RESTART');
  cases.push({case:'normal-relogin-completed-detail-opinion-and-no-approval',passed:true});
 }
 if(assets.some(p=>p.startsWith('/zhumadian/emergency/assets/')))throw Error('UNVERSIONED_PRELOAD_ALIAS_AFTER_MODULE_NAVIGATION');
 await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_COMPILED_UI_EXCEPTION');
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

 // The original emergency login, lists, native detail/refresh and logout above
 // remain unchanged. This second login uses the original security application.
 stage='normal-security-original-login';token='';current=null;homeAssetObservation=true;
 await send('Page.navigate',{url:w.base+'/zhumadian/home'},session);
 await until(()=>evaluate('location.pathname==="/zhumadian/login"&&document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});const b=Array.from(document.querySelectorAll('.login-body button')).find(e=>e.textContent.trim()==='登录');if(!b)throw Error('NORMAL_SECURITY_LOGIN_BUTTON_REQUIRED');b.click()})()`);
 await until(()=>token&&current);cases.push({case:'original-security-normal-nonadmin-login',passed:true});
 async function homeCheck(){
  await until(()=>evaluate('location.pathname==="/zhumadian/home"&&document.querySelectorAll(".card-container .card-item").length===3'));
  await evaluate('document.fonts.ready.then(()=>true)');
  await until(()=>evaluate('[...document.fonts].some(f=>f.family==="YouSheBiaoTiHei"&&f.status==="loaded")'));
  const state=await evaluate('(()=>{const b=document.querySelector(".background-pattern"),t=document.querySelector("header .title");return{title:t?.textContent?.trim(),font:t?getComputedStyle(t).fontFamily:null,background:b?getComputedStyle(b).backgroundImage:null,overlay:!!document.querySelector("link[data-xnby-home-transfer]"),cards:document.querySelectorAll(".card-container .card-item").length}})()');
  if(state.title!=='驻马店重大风险防控'||!state.font?.includes('YouSheBiaoTiHei')||!state.background?.includes('home-background-415f7103fab4437c.webp')||!state.overlay||state.cards!==3)throw Error('ORIGINAL_HOME_WITH_NEW_LOSSLESS_ASSETS_REQUIRED');
 }
 stage='original-security-home-render';await homeCheck();
 await until(()=>evaluate('document.querySelectorAll(".menu-item").length===8'));
 cases.push({case:'original-home-async-menu-response-renders-eight-owned-entries',passed:true});
 cases.push({case:'original-security-home-cards-title-and-new-background-render',passed:true});
 stage='original-security-home-refresh';await send('Page.navigate',{url:w.base+'/zhumadian/home'},session);await homeCheck();
 await until(()=>homeResourceRequests.some(p=>p.endsWith('YouSheBiaoTiHei-7af84bf1c97ae44e.woff2')));
 if(homeResourceRequests.some(p=>p.endsWith('/YouSheBiaoTiHei-fahbdFno.ttf')||p.endsWith('/background-BHYqFd8n.png')))throw Error('UNUSED_OLD_LARGE_HOME_RESOURCE_REQUESTED');
 cases.push({case:'original-security-home-refresh-uses-woff2-webp-without-old-large-assets',passed:true});
 await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_SECURITY_COMPILED_UI_EXCEPTION');
 stage='original-security-header-logout';
 if(!await evaluate('!!document.querySelector("header .user img")'))throw Error('ORIGINAL_SECURITY_LOGOUT_CONTROL_REQUIRED');
 await evaluate('document.querySelector("header .user img").click()');
 await until(()=>evaluate('!!document.querySelector(".el-message-box__btns .el-button--primary")'));
 await evaluate('document.querySelector(".el-message-box__btns .el-button--primary").click()');
 await until(()=>evaluate('location.pathname==="/zhumadian/login"&&document.querySelectorAll(".login-body input").length===3'));
 cases.push({case:'original-security-header-logout-preserves-original-business-login',passed:true});
 await Promise.all([...reads]);if(problem)throw Error(problem);

 proof={passed:true,mode:w.mode,cases,requests,actualCompiledApplicationAndOriginalSDK:true,APIsMocked:false,
  taskCreationUIAccepted:false,approvalUIAccepted:w.mode==='pending-approve',approvalRequests:audits,
  credentialOrTokenPersistedInProof:false,homeResourceRequests:[...new Set(homeResourceRequests)],normalSecurityHomeOriginalSDKAccepted:true,cacheAndTimingAcceptedByThisInterceptedProbe:false,loginVisibleMs,anonymousJavaScriptRequests:anonymousAssets,fullInstallerRequestedOnlyAfterLogin:true,allJavaScriptRequests:[...new Set(assets)],originalFieldBaselineSHA256:baseline?.databaseFieldCanonicalSHA256,baselineIsNativeDetailValue:true,publicOrDesktopTouched:false,fullCloneReady:false};
}catch(error){proof={passed:false,stage,failure:error.message,cases,requests,approvalRequests:audits,APIsMocked:false,fullCloneReady:false};
 try{await save('diagnostic.private.json',await evaluate('({path:location.pathname,onlineFieldPresent:!!document.querySelector("[data-online-field]"),auditPresent:!!document.querySelector(".audit-form"),alerts:Array.from(document.querySelectorAll(".el-alert,.el-message")).map(e=>e.textContent.slice(0,120)),visibleHeadings:Array.from(document.querySelectorAll("h1,h2,h3")).map(e=>e.textContent)})()'))}catch{}
}finally{
 token='';current=null;detail=null;w.password='';
 await closeBrowser();await save('browser-terminal.json',{normalBrowserClosed:chrome?.exitCode===0,exitCode:chrome?.exitCode,forceTerminationUsed:false});
 await save('result.json',proof);
}
process.stdout.write(JSON.stringify({passed:proof.passed,mode:w.mode,cases:proof.cases.length,approvalRequests:audits,normalBrowserClosed:chrome?.exitCode===0}));
if(!proof.passed||chrome?.exitCode!==0)process.exitCode=1;
