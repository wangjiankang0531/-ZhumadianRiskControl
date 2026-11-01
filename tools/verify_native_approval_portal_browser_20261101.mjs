import fs from 'node:fs/promises';import{spawn}from'node:child_process';
const root=process.argv[2];if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r123\/r[1-9][0-9]*$/.test(root))throw Error('OWN_WORKFLOW_ROOT');
let raw='';for await(const p of process.stdin){raw+=p;if(raw.length>16384)throw Error('BOUNDED_OWN_LOGIN');}const wire=JSON.parse(raw);raw='';
const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));if(wire.base!=='http://127.0.0.1:'+started.gatewayPort||!wire.syntheticNormalUser||!['operator','reviewer'].includes(wire.actor))throw Error('OWN_WORKFLOW_SCOPE');
const O=root+'/workflow-browser-'+(wire.readbackOnly?'operator-readback':wire.actor);await fs.mkdir(O);const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,chrome,session,seq=0,token='',stage='start',expectedContext=null,faultInjected=false,lostResponse=null,reconcileReadFault=false;const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],exceptions=[],cases=[],blocked=[],lists=new Map(),taskLists=new Map();
async function until(fn,ms=30000){const end=Date.now()+ms;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_WORKFLOW_UI_TIMEOUT');await sleep(40);}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN)return reject(Error('OWN_BROWSER_CLOSED'));const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method));},12000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}
async function evaluate(code){const v=await send('Runtime.evaluate',{expression:code,awaitPromise:true,returnByValue:true},session);if(v.exceptionDetails)throw Error('OWN_UI_EVALUATION_FAILED');return v.result.value;}
const click=(selector,text)=>evaluate(`(()=>{const b=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(x=>x.textContent.trim()===${JSON.stringify(text)});if(!b)return false;const target=${JSON.stringify(selector)}==='.el-menu-item'?(b.querySelector('a')||b):b;target.click();return true;})()`);
function observe(v){
 if(v.method==='Fetch.requestPaused'){
  const u=new URL(v.params.request.url),id=v.params.requestId;
  if(u.origin===wire.base||['about:','data:'].includes(u.protocol)){
   const audit=v.params.request.method==='POST'&&u.pathname.includes('/FlowBefore/Audit/');
   if(wire.reconcileReadFailure&&lostResponse&&!reconcileReadFault&&v.params.responseStatusCode===undefined&&v.params.request.method==='GET'&&/\/Engine\/FlowBefore\/[0-9]+$/.test(u.pathname)){reconcileReadFault=true;send('Fetch.failRequest',{requestId:id,errorReason:'ConnectionFailed'},session).catch(()=>{});}
   else if(audit&&wire.responseLost&&v.params.responseStatusCode!==undefined&&!lostResponse){
    (async()=>{const payload=await send('Fetch.getResponseBody',{requestId:id},session);const body=JSON.parse(payload.base64Encoded?Buffer.from(payload.body,'base64').toString('utf8'):payload.body);lostResponse={originalHTTPStatus:v.params.responseStatusCode,originalBusinessCode:body.code,realResponseObservedBeforeLoss:true};await send('Fetch.failRequest',{requestId:id,errorReason:'ConnectionClosed'},session);})().catch(()=>{exceptions.push({text:'OWN_RESPONSE_LOSS_INJECTION_FAILED'});send('Fetch.continueRequest',{requestId:id},session).catch(()=>{});});
   }else if(audit&&wire.approvalResilience&&!faultInjected){faultInjected=true;send('Fetch.failRequest',{requestId:id,errorReason:'ConnectionFailed'},session).catch(()=>{});}
   else if(audit&&wire.doubleClick)sleep(400).then(()=>send('Fetch.continueRequest',{requestId:id},session)).catch(()=>{});
   else send('Fetch.continueRequest',{requestId:id},session).catch(()=>{});
  }else{blocked.push({protocol:u.protocol});send('Fetch.failRequest',{requestId:id,errorReason:'BlockedByClient'},session).catch(()=>{});}
 }
 else if(v.method==='Network.requestWillBeSent'){const r=v.params.request,u=new URL(r.url);if(u.origin!==wire.base||!u.pathname.startsWith('/zhumadian/api/'))return;if(tracked.size>160)throw Error('BOUNDED_NATIVE_HTTP');const row={path:u.pathname,method:r.method};if(u.pathname.endsWith('/eventTask/getPage')){row.taskStatusQuery=u.searchParams.get('taskStatus');row.ownTaskNameQueryMatched=u.searchParams.get('taskName')===expectedContext?.taskName;}if(u.pathname.endsWith('/oauth/Login')){row.queryParameters=u.searchParams.has('grant_type');row.cipherMatched=u.searchParams.get('password')===wire.expectedWirePassword;}tracked.set(v.params.requestId,row);}
 else if(v.method==='Network.responseReceived'){const r=tracked.get(v.params.requestId);if(r)r.httpStatus=v.params.response.status;}
 else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){const row=tracked.get(v.params.requestId);const p=send('Network.getResponseBody',{requestId:v.params.requestId},session).then(r=>{let body;try{body=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body);}catch{row.nonJSON=true;http.push(row);return;}row.businessCode=body.code;if(row.path.endsWith('/oauth/Login')){token=body.data?.token||'';row.normalTokenReturned=!!token;}if(row.path.endsWith('/oauth/CurrentUser')){row.normalOwnUserMatched=body.data?.userInfo?.userId===wire.expectedUserId;const text=JSON.stringify(body.data?.menuList||[]);row.workflowMenusReturned=text.includes('/workflow/flowTodo')&&text.includes('/workflow/startWithMeTwo');}if(row.path.endsWith('/Engine/FlowLaunch')||row.path.endsWith('/FlowBefore/List/1')){const data=body.data||{};row.listIsArray=Array.isArray(data.list);row.listCount=Array.isArray(data.list)?data.list.length:null;row.paginationPresent=!!data.pagination;lists.set(row.path,data);}if(/\/Engine\/FlowBefore\/[^/]+$/.test(row.path)){row.recordsPresent=Array.isArray(body.data?.flowTaskOperatorRecordList);row.nodesPresent=Array.isArray(body.data?.flowTaskNodeList);row.templatePresent=!!body.data?.flowTemplateInfo;row.nativeFlowState=body.data?.flowTaskInfo?.status;row.noOperateAuth=body.data?.noOperateAuth;row.operators=(body.data?.flowTaskOperatorList||[]).map(o=>({keys:Object.keys(o),state:o.state,status:o.status,handleStatus:o.handleStatus,ownUser:o.handleId===wire.expectedUserId||o.userId===wire.expectedUserId}));}if(row.path.endsWith('/eventTask/getPage')){const rows=body.data?.records;row.taskRowsArray=Array.isArray(rows);row.taskRowCount=rows?.length;row.ownTaskReturned=rows?.some(r=>r.id===expectedContext?.taskId);row.allReturnedTasksState2=rows?.length>0&&rows.every(r=>String(r.taskStatus)==='2');taskLists.set(row.path,body.data);}if(row.path.endsWith('/eventTask/getById')){row.taskStatus=body.data?.taskStatus;row.correctTaskFlowRead=body.code===0&&body.data?.id===expectedContext?.taskId&&body.data?.taskName===expectedContext?.taskName;}http.push(row);}).catch(()=>{row.observationFailed=true;http.push(row);}).finally(()=>reads.delete(p));reads.add(p);}
 else if(v.method==='Network.loadingFailed'&&tracked.has(v.params.requestId)){const row=tracked.get(v.params.requestId);row.transportFailed=true;row.errorText=String(v.params.errorText||'').slice(0,120);http.push(row);}
 else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION'});
}
async function menu(label,endpoint){stage='menu-'+label;const before=http.filter(x=>x.path.endsWith(endpoint)).length;const route=label==='我发起的'?'/zhumadian/emergency/workflow/startWithMeTwo':'/zhumadian/emergency/workflow/flowTodo';const alreadyOnRoute=await evaluate('location.pathname==='+JSON.stringify(route));await until(()=>evaluate('Array.from(document.querySelectorAll(".el-menu-item")).some(e=>e.textContent.trim()==='+JSON.stringify(label)+')'));if(!await click('.el-menu-item',label))throw Error('OWN_WORKFLOW_MENU_MISSING');await until(()=>http.filter(x=>x.path.endsWith(endpoint)).length>before||alreadyOnRoute&&before>0);await until(()=>evaluate('location.pathname==='+JSON.stringify(route)));const result=http.filter(x=>x.path.endsWith(endpoint)).at(-1);if(result.httpStatus!==200||result.businessCode!==200||!result.listIsArray||!result.paginationPresent)throw Error('NATIVE_WORKFLOW_LIST_CONTRACT');await until(()=>evaluate(`document.querySelectorAll('.work-item').length===${result.listCount}`));if(!await evaluate(`!!document.querySelector('.work-list')&&!document.body.textContent.includes('22222')&&!document.body.textContent.includes('11111')`))throw Error('WORKFLOW_VIEW_NOT_RENDERED');cases.push({case:label+'-native-list-and-render',rows:result.listCount});return lists.get(result.path).list;}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',v=>fs.appendFile(O+'/chrome.private.log',v));chrome.on('exit',()=>{for(const p of pending.values())p.reject(Error('OWN_CHROME_EXITED'));pending.clear();});let active;await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true;}catch{return false;}});ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p){if(v.error)p.reject(Error('OWN_CDP_ERROR'));else p.resolve(v.result);}}else observe(v);});const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;for(const name of['Runtime','Page','Network'])await send(name+'.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'},...(wire.responseLost?[{urlPattern:wire.base+'/zhumadian/api/jnpf/workflow/Engine/FlowBefore/Audit/*',requestStage:'Response'}]:[])]},session);await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);
 stage='normal-native-login';await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/workflow/flowTodo'},session);await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));await evaluate(`(()=>{const values=${JSON.stringify([wire.account,wire.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});})()`);if(!await click('.login-body button','登录'))throw Error('OWN_NORMAL_LOGIN_BUTTON');await until(()=>http.some(x=>x.path.endsWith('/oauth/CurrentUser')&&x.normalOwnUserMatched&&x.workflowMenusReturned));await until(()=>evaluate('!document.querySelector(".login-body")&&!!document.querySelector(".el-menu-item")'));cases.push({case:'real-original-login-and-standard-workflow-role-menus',passed:true});
 let context;
 if(wire.actor==='operator'&&!wire.readbackOnly){
  stage='prepare-owned-real-pending-task';const ua=await evaluate('navigator.userAgent');async function api(method,path,body){const response=await fetch(wire.base+'/zhumadian/api/serv'+path,{method,headers:{Authorization:token,'Content-Type':'application/json','User-Agent':ua},...(body?{body:JSON.stringify(body)}:{})});const value=await response.json();cases.push({case:'owned-native-fixture-api',endpoint:path.split('?')[0],httpStatus:response.status,businessCode:value.code});if(response.status!==200||value.code!==0)throw Error('OWN_REAL_TASK_PREPARATION_FAILED');return value.data;}
  if(wire.configureTaskForm){
   stage='configure-only-owned-task-code-form';
   const formId='a5320000000000000000000000000001';const targetUrl='/emergencyResponse/taskSend/info/detail.vue';
   async function native(method,path,body){const response=await fetch(wire.base+'/zhumadian/api/jnpf'+path,{method,headers:{Authorization:token,'Content-Type':'application/json','User-Agent':ua},...(body?{body:JSON.stringify(body)}:{})});const value=await response.json();cases.push({case:'owned-standard-native-form-api',method,endpoint:path.split('?')[0],httpStatus:response.status,businessCode:value.code});if(response.status!==200||value.code!==200)throw Error('OWN_NATIVE_TASK_FORM_CONFIGURATION_FAILED');return value.data;}
   const current=await native('GET','/flowForm/Form/'+formId);
   if(current.id!==formId||current.enCode!=='OWN_FORM_CODE'||![1,2].includes(current.formType))throw Error('EXACT_OWN_FORM_REQUIRED');
   const definition=JSON.parse(await fs.readFile('D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-business-main-r114/own-workflow-definition.json','utf8'));
   if(!definition.syntheticInputOnly||definition.formId!==formId||definition.formBody.enCode!=='OWN_FORM_CODE')throw Error('EXACT_PRIOR_OWN_FORM_DEFINITION_REQUIRED');
   const property=JSON.parse(definition.formBody.propertyJson);if(typeof property.fields==='string')property.fields=JSON.parse(property.fields);
   if(!Array.isArray(property.fields)||property.fields.length!==1)throw Error('OWN_SAMPLE_FIELD_SHAPE_REQUIRED');
   const body={...definition.formBody,formType:2,urlAddress:targetUrl,tableJson:definition.formBody.tableJson,enabledMark:1,propertyJson:JSON.stringify(property),draftJson:JSON.stringify(property)};
   await native('PUT','/flowForm/Form',body);await native('POST','/flowForm/Form/Release/'+formId+'?isRelease=1');
   const after=await native('GET','/flowForm/Form/'+formId);
   if(after.formType!==2||after.urlAddress!==targetUrl||!Array.isArray(JSON.parse(after.propertyJson).fields))throw Error('OWN_PUBLISHED_TASK_CODE_FORM_REQUIRED');
   cases.push({case:'owned-task-form-published-with-native-fields-array-and-real-task-component',passed:true,productionFormOrRoleChanged:false});
   stage='prepare-owned-real-pending-task';
  }
  const name='Own workflow approval R123 '+root.split('/').pop();if(await api('POST','/eventInfo/save',{eventName:name,eventContent:'Own workflow UI input',eventType:'OWN',eventLevel:'1',eventLocation:'Own isolated site',reportTime:'2026-11-01 09:00:00'})!==true)throw Error('OWN_EVENT_NOT_SAVED');const event=(await api('GET','/eventInfo/getPage?current=1&size=5&eventName='+encodeURIComponent(name))).records.find(x=>x.eventName===name);if(!event)throw Error('OWN_EVENT_NOT_FOUND');if(await api('POST','/eventInfo/updateById',{id:event.id,researchStatus:'1',eventLevel:'1',researchResult:'Own workflow precondition'})!==true)throw Error('OWN_EVENT_NOT_CONFIRMED');if(wire.expectEmptyFlowRejection){
   const response=await fetch(wire.base+'/zhumadian/api/serv/eventTask/save',{method:'POST',headers:{Authorization:token,'Content-Type':'application/json','User-Agent':ua},body:JSON.stringify({infoId:event.id,eventNumber:event.eventNumber,eventName:name,taskName:name,taskContent:'Own rejected native workflow UI task'})});
   const body=await response.json();const guardMessageMatched=String(body.msg||body.message||'').includes('审批流程创建失败，任务未保存，请稍后重试');
   cases.push({case:'empty-native-flow-refused-with-explicit-guard-error',httpStatus:response.status,businessCode:body.code,guardMessageMatched});
   if(body.code===0||body.data===true||!guardMessageMatched)throw Error('EMPTY_NATIVE_FLOW_MUST_BE_REFUSED_BY_GUARD');
   const rows=(await api('GET','/eventTask/getPage?current=1&size=5&taskName='+encodeURIComponent(name))).records.filter(x=>x.taskName===name);
   if(rows.length!==0)throw Error('FAILED_NATIVE_FLOW_SAVED_BUSINESS_TASK');
   cases.push({case:'failed-native-flow-has-no-saved-task-row',matchingRows:0,passed:true});
  }else{if(await api('POST','/eventTask/save',{infoId:event.id,eventNumber:event.eventNumber,eventName:name,taskName:name,taskContent:'Own pending native workflow UI task'})!==true)throw Error('OWN_TASK_NOT_SAVED');const task=(await api('GET','/eventTask/getPage?current=1&size=5&taskName='+encodeURIComponent(name))).records.find(x=>x.taskName===name);if(!task?.flowId||task.taskStatus!=='2')throw Error('OWN_REAL_PENDING_INSTANCE_REQUIRED');context={taskId:task.id,eventId:event.id,flowId:task.flowId,taskName:name,syntheticDataOnly:true};await fs.writeFile(root+'/workflow-context.private.json',JSON.stringify(context));cases.push({case:'real-business-api-created-pending-original-instance',passed:true,taskCreateUIAccepted:false});}
 }else{context=JSON.parse(await fs.readFile(root+'/workflow-context.private.json','utf8'));if(!context.syntheticDataOnly)throw Error('OWN_CONTEXT_REQUIRED');}

 expectedContext=context;
 if(wire.taskStatusFilter){
  stage='actual-task-table-state-filter-and-reset';
  const path='/zhumadian/api/serv/eventTask/getPage',before=http.filter(x=>x.path===path).length;
  if(!await evaluate('(()=>{const a=Array.from(document.querySelectorAll(".el-menu-item a")).find(e=>e.getAttribute("href")?.endsWith("/emergencyResponse/taskSend"));if(!a)return false;if(!a.getClientRects().length)a.closest(".el-sub-menu")?.querySelector(".el-sub-menu__title")?.click();return true;})()'))throw Error('OWN_ORIGINAL_TASK_MENU_REQUIRED');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-menu-item a")).some(e=>e.getAttribute("href")?.endsWith("/emergencyResponse/taskSend")&&e.getClientRects().length)'));
  await evaluate('Array.from(document.querySelectorAll(".el-menu-item a")).find(e=>e.getAttribute("href")?.endsWith("/emergencyResponse/taskSend")).click()');
  await until(()=>http.filter(x=>x.path===path).length>before);
  if(!await evaluate('(()=>{const item=Array.from(document.querySelectorAll(".table-search .el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务名称");const input=item?.querySelector("input");if(!input)return false;input.value='+JSON.stringify(context.taskName)+';input.dispatchEvent(new Event("input",{bubbles:true}));input.dispatchEvent(new Event("change",{bubbles:true}));return true;})()'))throw Error('OWN_TASK_NAME_SEARCH_REQUIRED');
  if(!await evaluate('(()=>{const item=Array.from(document.querySelectorAll(".table-search .el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务状态");const select=item?.querySelector(".el-select__wrapper");if(!select)return false;select.click();return true;})()'))throw Error('ACTUAL_TASK_STATE_SELECT_REQUIRED');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-select-dropdown__item")).some(e=>e.textContent.trim()==="处置中"&&e.getClientRects().length)'));
  await evaluate('Array.from(document.querySelectorAll(".el-select-dropdown__item")).find(e=>e.textContent.trim()==="处置中"&&e.getClientRects().length).click()');
  const searchBefore=http.filter(x=>x.path===path).length;if(!await click('.table-search button','搜索'))throw Error('ACTUAL_TASK_SEARCH_BUTTON_REQUIRED');
  await until(()=>http.filter(x=>x.path===path).length>searchBefore);const filtered=http.filter(x=>x.path===path).at(-1);
  if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.taskStatusQuery!=='2'||!filtered.ownTaskNameQueryMatched||!filtered.ownTaskReturned||!filtered.allReturnedTasksState2)throw Error('ACTUAL_TASK_STATUS_FILTER_MUST_USE_ORIGINAL_QUERY');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-table__body tr")).some(e=>e.textContent.includes('+JSON.stringify(context.taskName)+')&&e.textContent.includes("处置中"))'));
  cases.push({case:'actual-task-list-existing-state2-search-and-render',passed:true,actualOriginalQueryState:'2',matchingOwnTaskReturned:true});
  await fs.writeFile(O+'/task-state-filter-owned.png',Buffer.from((await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session)).data,'base64'));
  const resetBefore=http.filter(x=>x.path===path).length;if(!await click('.table-search button','重置'))throw Error('ACTUAL_TASK_RESET_REQUIRED');await until(()=>http.filter(x=>x.path===path).length>resetBefore);
  const reset=http.filter(x=>x.path===path).at(-1);if(reset.httpStatus!==200||reset.businessCode!==0||reset.taskStatusQuery||reset.ownTaskNameQueryMatched)throw Error('ACTUAL_TASK_RESET_MUST_CLEAR_QUERY');
  cases.push({case:'actual-task-list-search-reset-clears-state-and-name',passed:true});
 }

 if(!wire.expectEmptyFlowRejection){ const endpoint=wire.actor==='operator'?'/Engine/FlowLaunch':'/FlowBefore/List/1',label=wire.actor==='operator'?'我发起的':'待办事宜';const rows=await menu(label,endpoint);const index=rows.findIndex(x=>x.processInstanceId===context.flowId||x.id===context.flowId);if(index<0)throw Error('OWN_PENDING_INSTANCE_NOT_IN_NATIVE_LIST');
 if(!wire.listsOnly){stage='actual-native-detail';await evaluate(`document.querySelectorAll('.work-item')[${index}].click()`);await until(()=>http.some(x=>/\/Engine\/FlowBefore\/[^/]+$/.test(x.path)&&x.businessCode===200));await until(()=>evaluate(`document.body.textContent.includes('审批记录')&&document.body.textContent.includes('流程状态')&&document.body.textContent.includes('流程图')`));cases.push({case:label+'-real-detail-record-state-and-diagram-tabs',passed:true});
  await until(()=>http.some(x=>x.path.endsWith('/eventTask/getById')&&x.correctTaskFlowRead));
  await until(()=>evaluate('Array.from(document.querySelectorAll(".left-content .el-form-item")).some(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务名称"&&e.querySelector("input,textarea")?.value==='+JSON.stringify(context.taskName)+')'));
  if(!await evaluate('document.querySelectorAll(".left-content .el-form").length===1&&!document.querySelector(".left-content input:not(:disabled),.left-content textarea:not(:disabled),.left-content select:not(:disabled),.left-content [contenteditable=true]")'))throw Error('EMBEDDED_TASK_FORM_MUST_BE_READ_ONLY');
  cases.push({case:'actual-workflow-task-component-read-by-native-instance-and-rendered-read-only',passed:true});
  if(wire.expectStateLabel){
   const state=String(http.filter(x=>x.path.endsWith('/eventTask/getById')&&x.correctTaskFlowRead).at(-1)?.taskStatus);
   const label=({'0':'待处置','1':'已处置','2':'处置中'})[state];if(!label)throw Error('KNOWN_PROVIDED_TASK_STATE_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".left-content .el-form-item")).some(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务状态"&&(e.querySelector("input,textarea")?.value==='+JSON.stringify(label)+'||e.textContent.includes('+JSON.stringify(label)+')))'));
   cases.push({case:'actual-existing-task-state-rendered-from-provided-entity-definition',passed:true,state,label,persistentStateOrSchemaChanged:false});
  }
  for(const tab of ['流程状态','流程图','基本信息','审批记录']){if(!await click('.el-tabs__item',tab))throw Error('ACTUAL_WORKFLOW_TAB_MISSING');await sleep(80);if(tab==='基本信息'){if(!await evaluate('document.querySelector("#pane-fourth")?.textContent.replace(/\s+/g,"").includes("发起人身份own_operator_a")'))throw Error('ACTUAL_INITIATOR_MUST_NOT_BE_CURRENT_APPROVER');cases.push({case:'actual-initial-submitter-identity-not-current-approver',passed:true});}}
  await fs.writeFile(O+'/details-owned.png',Buffer.from((await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session)).data,'base64'));
  if(wire.readbackOnly){
   if(!http.some(x=>x.path.endsWith('/eventTask/getById')&&x.correctTaskFlowRead&&x.taskStatus==='1'))throw Error('NATIVE_CALLBACK_TASK_STATE_NOT_PRESERVED_ON_REOPEN');
   if(await evaluate('!!document.querySelector(".audit-content .audit-form")'))throw Error('COMPLETED_INITIATOR_VIEW_MUST_NOT_OFFER_ACTIVE_AUDIT');
   cases.push({case:'normal-initiator-relogin-completed-native-flow-and-read-only-task-state',passed:true,manualDisposalFeedbackAccepted:false});
  }
  if(wire.approveOnce){
   if(wire.actor!=='reviewer')throw Error('ONLY_OWN_ASSIGNED_REVIEWER_UI_APPROVES');stage='real-ui-one-approval-and-native-callback';
   if(!await evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==="通过")'))throw Error('REAL_NATIVE_APPROVE_ACTION_REQUIRED');
   if(!await evaluate('(()=>{const e=document.querySelector(".audit-form textarea");if(!e)return false;e.value="Own UI approval resilience R124";e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));return true;})()'))throw Error('ACTUAL_AUDIT_OPINION_FIELD_REQUIRED');
   if(wire.responseLost){
    stage='real-server-approval-success-response-lost';
    const search=await evaluate('location.search');const query=Object.fromEntries(new URLSearchParams(search));
    if(!query.id||!query.flowId)throw Error('OWN_NATIVE_ROUTE_IDENTIFIERS_REQUIRED');
    if(!await click('.audit-form button','提交'))throw Error('ACTUAL_NATIVE_APPROVE_BUTTON_REQUIRED');
    await until(()=>lostResponse&&http.some(x=>x.path.includes('/FlowBefore/Audit/')&&x.transportFailed));
    if(lostResponse.originalHTTPStatus!==200||lostResponse.originalBusinessCode!==200)throw Error('REAL_SERVER_APPROVAL_BEFORE_LOSS_REQUIRED');
    const ua=await evaluate('navigator.userAgent');const headers={Authorization:token,'User-Agent':ua};let callback=false;
    for(let i=0;i<100;i++){const response=await fetch(wire.base+'/zhumadian/api/serv/eventTask/getById?flowId='+encodeURIComponent(context.flowId),{headers});const body=await response.json();if(response.status===200&&body.code===0&&body.data?.id===context.taskId&&body.data.taskStatus==='1'){callback=true;break;}await sleep(200);}
    if(!callback)throw Error('ORIGINAL_CALLBACK_AFTER_LOST_RESPONSE_REQUIRED');
    const params=new URLSearchParams({taskNodeId:query.id,taskOperatorId:query.id,flowId:query.flowId});
    const response=await fetch(wire.base+'/zhumadian/api/jnpf/workflow/Engine/FlowBefore/'+encodeURIComponent(query.id)+'?'+params,{headers});const body=await response.json();
    const dto=body.data||{};const shape={httpStatus:response.status,businessCode:body.code,keys:Object.keys(dto),flowState:dto.flowTaskInfo?.status,noOperateAuth:dto.noOperateAuth,operators:(dto.flowTaskOperatorList||[]).map(o=>({keys:Object.keys(o),state:o.state,status:o.status,handleStatus:o.handleStatus,ownUser:o.handleId===wire.expectedUserId||o.userId===wire.expectedUserId})),approversProperties:dto.approversProperties,records:(dto.flowTaskOperatorRecordList||[]).map(r=>({handleStatus:r.handleStatus,ownReviewer:r.userName?.split('/')[0]==='own_reviewer_b',keys:Object.keys(r)}))};
    await fs.writeFile(O+'/owned-completed-native-shape.json',JSON.stringify(shape,null,2));
    if(response.status!==200||body.code!==200||String(dto.flowTaskInfo?.status)!=='2')throw Error('AUTHORITATIVE_COMPLETED_FLOW_AFTER_LOSS_REQUIRED');
    if(wire.reconcileReadFailure){
     await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form button")).some(b=>b.textContent.trim()==="核对提交结果"&&!b.disabled)'));
     if(!reconcileReadFault||!await evaluate('document.querySelector(".audit-form textarea")?.value==="Own UI approval resilience R124"'))throw Error('UNKNOWN_OUTCOME_MUST_KEEP_DRAFT_AND_QUERY_ONLY');
     const count=Array.from(tracked.values()).filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
     if(!await evaluate('(()=>{const b=Array.from(document.querySelectorAll(".audit-form button")).find(x=>x.textContent.trim()==="核对提交结果");if(!b)return false;b.click();b.click();return true;})()'))throw Error('REAL_OUTCOME_RECHECK_BUTTON_REQUIRED');
     await until(()=>evaluate('!document.querySelector(".audit-form")'));
     if(Array.from(tracked.values()).filter(x=>x.path.includes('/FlowBefore/Audit/')).length!==count)throw Error('UNKNOWN_OUTCOME_RECHECK_MUST_NOT_POST_APPROVAL');
     cases.push({case:'failed-authoritative-read-keeps-opinion-and-double-recheck-sends-no-extra-audit',passed:true});
    }
    await until(()=>evaluate('!document.querySelector(".audit-form")'));
    await until(()=>http.some(x=>x.path.endsWith('/eventTask/getById')&&x.correctTaskFlowRead&&x.taskStatus==='1'));
    await until(()=>evaluate('Array.from(document.querySelectorAll(".left-content .el-form-item")).some(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务状态"&&e.querySelector("input,textarea")?.value==="已处置")'));
    const offersRetry=await evaluate('!!document.querySelector(".audit-form")');
    cases.push({case:'real-success-response-lost-authoritative-completed-flow',...lostResponse,originalCallbackTaskState:'1',flowState:String(dto.flowTaskInfo.status),activeApprovalFormStillShown:offersRetry,passed:!offersRetry});
    if(offersRetry)throw Error('APPROVAL_RESPONSE_LOST_MUST_REFRESH_AUTHORITATIVE_STATE');
   }else{
   let before=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
   if(wire.approvalResilience){
    stage='actual-invalid-reviewer-action-keeps-form-usable';
    const opinion='Own UI approval resilience R124';
    const writes=()=>Array.from(tracked.values()).filter(x=>x.method==='POST'&&/\/FlowBefore\/(Audit|Transfer)\//.test(x.path)).length;
    const writesBefore=writes();
    if(!await click('.audit-form .el-radio','转审'))throw Error('OWN_NATIVE_TRANSFER_ACTION_REQUIRED');
    await until(()=>evaluate('!!document.querySelector(".audit-form input[placeholder*=转审]")'));
    if(!await click('.audit-form button','提交'))throw Error('ACTUAL_NATIVE_APPROVE_BUTTON_REQUIRED');
    await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-form-item__error")).some(e=>e.textContent.includes("请选择人员"))'));
    await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form button")).some(b=>b.textContent.trim()==="提交"&&!b.disabled&&!b.classList.contains("is-loading"))'));
    if(writes()!==writesBefore||!await evaluate('document.querySelector(".audit-form textarea")?.value==='+JSON.stringify(opinion)))throw Error('INVALID_AUDIT_MUST_KEEP_INPUT_AND_NOT_POST');
    cases.push({case:'actual-invalid-required-transfer-no-mutation-and-unlocked-opinion-retained',passed:true});
    if(!await click('.audit-form .el-radio','通过'))throw Error('OWN_NATIVE_APPROVE_RESELECT_REQUIRED');
    await until(()=>evaluate('!document.querySelector(".audit-form input[placeholder*=转审]")'));
    stage='actual-audit-transport-failure-retains-opinion';
    const failedBefore=http.filter(x=>x.path.includes('/FlowBefore/Audit/')&&x.transportFailed).length;
    if(!await click('.audit-form button','提交'))throw Error('ACTUAL_NATIVE_APPROVE_BUTTON_REQUIRED');
    await until(()=>http.filter(x=>x.path.includes('/FlowBefore/Audit/')&&x.transportFailed).length===failedBefore+1);
    await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form button")).some(b=>b.textContent.trim()==="提交"&&!b.disabled&&!b.classList.contains("is-loading"))'));
    if(!faultInjected||!await evaluate('document.querySelector(".audit-form textarea")?.value==='+JSON.stringify(opinion))||!await evaluate('Array.from(document.querySelectorAll(".el-message")).some(e=>e.textContent.includes("提交失败，请重试"))'))throw Error('FAILED_AUDIT_MUST_SHOW_RETRY_AND_PRESERVE_OPINION');
    const ua=await evaluate('navigator.userAgent');const response=await fetch(wire.base+'/zhumadian/api/serv/eventTask/getById?flowId='+encodeURIComponent(context.flowId),{headers:{Authorization:token,'User-Agent':ua}});const body=await response.json();
    if(response.status!==200||body.code!==0||body.data?.id!==context.taskId||body.data?.taskStatus!=='2')throw Error('TRANSPORT_FAILURE_MUST_NOT_COMPLETE_TASK');
    cases.push({case:'actual-audit-transport-failure-visible-error-opinion-retained-unlocked-original-task-pending',passed:true,onlyOwnedRequestFailedBeforeServer:true,fakeSuccessResponse:false});
    before=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
    stage='actual-retry-double-click-one-native-audit';
   }
   if(wire.doubleClick){
    const requestsBefore=Array.from(tracked.values()).filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
    if(!await evaluate('(()=>{const b=Array.from(document.querySelectorAll(".audit-form button")).find(x=>x.textContent.trim()==="提交");if(!b)return false;b.click();b.click();return true;})()'))throw Error('ACTUAL_NATIVE_APPROVE_BUTTON_REQUIRED');
    await until(()=>Array.from(tracked.values()).filter(x=>x.path.includes('/FlowBefore/Audit/')).length>requestsBefore);
    const busy=await evaluate('Array.from(document.querySelectorAll(".audit-form button")).some(b=>b.textContent.trim()==="提交"&&b.disabled&&b.classList.contains("is-loading"))');
    if(!busy)throw Error('ACTUAL_AUDIT_BUTTON_MUST_BE_BUSY_WHILE_PENDING');
    cases.push({case:'actual-audit-submit-disabled-and-loading-during-real-pending-request',passed:true});await sleep(650);
    const requests=Array.from(tracked.values()).filter(x=>x.path.includes('/FlowBefore/Audit/')).length-requestsBefore;
    cases.push({case:'actual-native-audit-double-click-attempt-count',requests,shortTransportDelayOnly:true,retryAfterFailedTransport:!!wire.approvalResilience});
    if(requests!==1){await sleep(1000);throw Error('NATIVE_APPROVAL_DOUBLE_CLICK_MUST_SEND_ONCE');}
   }else if(!await click('.audit-form button','提交'))throw Error('ACTUAL_NATIVE_APPROVE_BUTTON_REQUIRED');
   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length>before);
   const audits=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).slice(before);
   if(audits.length!==1||audits[0].method!=='POST'||audits[0].httpStatus!==200||audits[0].businessCode!==200)throw Error('REAL_NATIVE_UI_APPROVAL_MUST_SUCCEED_ONCE');
   const agent=await evaluate('navigator.userAgent');let callback=false;
   for(let i=0;i<100;i++){
    const response=await fetch(wire.base+'/zhumadian/api/serv/eventTask/getById?flowId='+encodeURIComponent(context.flowId),{headers:{Authorization:token,'User-Agent':agent}});const body=await response.json();
    if(response.status===200&&body.code===0&&body.data?.id===context.taskId&&body.data.taskStatus==='1'){callback=true;break;}await sleep(200);
   }
   if(!callback)throw Error('REAL_UI_APPROVAL_NATIVE_CALLBACK_REQUIRED');
   cases.push({case:'assigned-reviewer-real-ui-one-native-audit-and-original-callback-task-2-to-1',passed:true,nativeAuditRequests:1,manualBusinessTaskUpdateSent:false,manualDisposalFeedbackAccepted:false});
   }
  }

 }
 }
 if(exceptions.length)throw Error('ORIGINAL_WORKFLOW_UI_EXCEPTION');await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,actor:wire.actor,cases,http,exceptions,blocked,realNativeRoleSessionAndAPIs:true,syntheticRowsOnly:true,approvalSubmitted:!!wire.approveOnce,afterApprovalReadback:!!wire.readbackOnly,emptyFlowRejectionChecked:!!wire.expectEmptyFlowRejection,listsOnly:!!wire.listsOnly,completeNangangAcceptance:false},null,2));console.log(JSON.stringify({passed:true,actor:wire.actor,cases}));
}catch(error){await Promise.allSettled([...reads]);await fs.writeFile(O+'/failure.json',JSON.stringify({message:error.message,stage,cases,http,exceptions,blocked},null,2));try{await fs.writeFile(O+'/owned-page-diagnostic.private.json',JSON.stringify(await evaluate('({path:location.pathname,text:document.body.textContent.slice(0,15000)})'),null,2));}catch{}throw error;}
finally{if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close');}catch{}ws.close();}if(chrome)while(chrome.exitCode===null&&chrome.signalCode===null)await sleep(100);token='';wire.password='';wire.expectedWirePassword='';await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({normalBrowserClosed:!!chrome&&chrome.exitCode===0,forceTerminationUsed:false}));}
