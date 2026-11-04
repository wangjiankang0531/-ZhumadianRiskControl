/** Normal compiled task creation and original event picker; no API doubles/fetch shortcuts. */
import fs from'node:fs/promises';import{spawn}from'node:child_process';import{createHash}from'node:crypto';
let raw='';for await(const part of process.stdin){raw+=part;if(raw.length>32768)throw Error('BOUNDED_PRIVATE_WIRE_REQUIRED')}
const w=JSON.parse(raw);raw='';const root='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/feedback-r880';
if(w.account!=='own_operator_a'||w.expectedUserId!=='a5310000000000000000000000000064'||w.eventId!=='a5320000000000000000000000000006'||
 w.eventNumber!=='OWN-NORMAL-WORKFLOW-EVENT'||w.eventName!=='Own workflow event'||!/^OWN_MANAGER_[0-9a-f]{32}$/.test(w.taskName)||
 typeof w.researchRequired!=='boolean'||typeof w.taskContent!=='string'||!w.taskContent.startsWith('Own task UI dispatch ')||w.syntheticNormalUser!==true||w.ownCaptchaPolicyDisabled!==true||
 !/^http:\/\/127\.0\.0\.1:\d{4,5}$/.test(w.base)||[8767,18891,18892].includes(+new URL(w.base).port)||typeof w.password!=='string')throw Error('EXACT_OWN_TASK_UI_SCOPE_REQUIRED');
if(await fs.readFile(root+'/own-normal-manager-test.marker','utf8')!=='own-original-manager-full-lifecycle-r609\n')throw Error('OWN_FULL_LIFECYCLE_MARKER_REQUIRED');
const O=root+'/ui-create-r887';await fs.mkdir(O);const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let chrome,ws,session,active,seq=0,logged=false,current=null,problem=null,stage='start',saveAttempts=0,saveConfirmed=false;
let eventRows=[],eventPageCount=0,taskRows=[],taskPageCount=0,eventDetail=null,researchAttempts=0,researchConfirmed=false,researchLevel=null,proof;
const researchText='Own UI research '+w.taskName.slice('OWN_MANAGER_'.length);
const pending=new Map(),tracked=new Map(),reads=new Set(),requests=[],cases=[],exceptions=[];
const persist=(name,value)=>fs.writeFile(O+'/'+name,JSON.stringify(value,null,2)+'\n');
async function until(fn,ms=45000){const end=Date.now()+ms;for(;;){if(problem)throw Error(problem);if(await fn())return;if(Date.now()>end)throw Error('OWN_TASK_UI_OBSERVATION_TIMEOUT');await sleep(50)}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT'))},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...sid?{sessionId:sid}:{}}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error('OWN_TASK_UI_DOM_FAILED');return r.result.value}
function observe(v){
 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request,u=new URL(request.url);let allowed=u.origin===w.base||['about:','data:','blob:'].includes(u.protocol);
  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventTask/save'){
   saveAttempts++;let body;try{body=JSON.parse(request.postData||'')}catch{allowed=false}
   const exact=body?.infoId===w.eventId&&body?.eventNumber===w.eventNumber&&body?.eventName===w.eventName&&body?.taskName===w.taskName&&body?.taskContent===w.taskContent;
   allowed=allowed&&request.method==='POST'&&saveAttempts===1&&exact;
   if(allowed){persist('task-save-issued.json',{issuedOnce:true,expectedConfirmedEventMatched:true,taskInputsMatched:true,
    requestSHA256:createHash('sha256').update(request.postData).digest('hex'),mutationsRetried:false}).then(()=>send('Fetch.continueRequest',{requestId:v.params.requestId},session)).catch(()=>{problem='OWN_TASK_INTENT_OR_CONTINUE_FAILED'});return}
   problem='UNEXPECTED_OR_DUPLICATE_TASK_CREATE_REFUSED';
  }
  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventInfo/updateById'){
   researchAttempts++;let body;try{body=JSON.parse(request.postData||'')}catch{allowed=false}
   const expected=body?.id===w.eventId&&String(body?.researchStatus)==='1'&&body?.researchResult===researchText&&typeof body?.eventLevel==='string'&&body.eventLevel.length>0&&body.eventLevel.length<65;
   allowed=allowed&&w.researchRequired&&request.method==='POST'&&researchAttempts===1&&expected;
   if(allowed){researchLevel=body.eventLevel;persist('research-issued.json',{issuedOnce:true,exactOwnedEventMatched:true,originalConfirmationStateMatched:true,researchValueSHA256:createHash('sha256').update(body.eventLevel).digest('hex'),requestSHA256:createHash('sha256').update(request.postData).digest('hex')}).then(()=>send('Fetch.continueRequest',{requestId:v.params.requestId},session)).catch(()=>{problem='OWN_RESEARCH_INTENT_OR_CONTINUE_FAILED'});return}
   problem='UNEXPECTED_OR_DUPLICATE_RESEARCH_CONFIRM_REFUSED';
  }else if(u.origin===w.base&&/\/serv\/event(?:Info|DisposalRecord)\/(?:save|update|remove|close)/i.test(u.pathname)){allowed=false;problem='NO_OTHER_EVENT_MUTATION_IN_TASK_UI_PROBE'}
  send(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:v.params.requestId,...allowed?{}:{errorReason:'BlockedByClient'}},session).catch(()=>{});
 }else if(v.method==='Network.requestWillBeSent'){
  const r=v.params.request,u=new URL(r.url);if(u.origin!==w.base)return;
  if(['/zhumadian/api/jnpf/oauth/Login','/zhumadian/api/jnpf/oauth/CurrentUser','/zhumadian/api/serv/eventInfo/getPage','/zhumadian/api/serv/eventInfo/getById','/zhumadian/api/serv/eventInfo/updateById','/zhumadian/api/serv/eventTask/getPage','/zhumadian/api/serv/eventTask/save'].includes(u.pathname))
   tracked.set(v.params.requestId,{endpoint:u.pathname,method:r.method,...u.pathname.endsWith('/eventInfo/getPage')?{confirmedFilterMatched:u.searchParams.get('researchStatus')==='1',expectedNameFilterMatched:u.searchParams.get('eventName')===w.eventName}:{}});
 }else if(v.method==='Network.responseReceived'&&tracked.has(v.params.requestId))tracked.get(v.params.requestId).httpStatus=v.params.response.status;
 else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);tracked.delete(v.params.requestId);
  const p=send('Network.getResponseBody',{requestId:v.params.requestId},session).then(r=>{
   const body=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body);row.businessCode=body.code;
   if(row.endpoint.endsWith('/oauth/Login')){logged=row.httpStatus===200&&body.code===200;if(!logged)problem='ORIGINAL_NORMAL_LOGIN_REFUSED'}
   if(row.endpoint.endsWith('/oauth/CurrentUser')){current=body.data;if(body.code!==200||current?.userInfo?.userId!==w.expectedUserId||current?.userInfo?.isAdministrator!==false)problem='KNOWN_NORMAL_NONADMIN_REQUIRED';row.taskMenuInCurrentUser=JSON.stringify(current?.menuList||[]).includes('/emergencyResponse/taskSend')}
   if(row.endpoint.endsWith('/eventInfo/getPage')){if(row.httpStatus!==200||body.code!==0||!Array.isArray(body.data?.records))problem='ORIGINAL_CONFIRMED_EVENT_PAGE_REQUIRED';eventRows=body.data?.records||[];eventPageCount++;row.exactOwnedEventPresent=eventRows.some(x=>x.id===w.eventId)}
   if(row.endpoint.endsWith('/eventInfo/getById')){eventDetail=body.data;row.knownEventMatched=eventDetail?.id===w.eventId&&eventDetail?.eventNumber===w.eventNumber;row.unresearchedEventMatched=String(eventDetail?.researchStatus)==='0';if(!row.knownEventMatched)problem='EXACT_OWN_RESEARCH_EVENT_REQUIRED'}
   if(row.endpoint.endsWith('/eventInfo/updateById')){researchConfirmed=row.httpStatus===200&&body.code===0&&body.data===true;row.confirmedTrue=researchConfirmed;if(!researchConfirmed)problem='ORIGINAL_RESEARCH_NOT_CONFIRMED_NO_RETRY'}
   if(row.endpoint.endsWith('/eventTask/getPage')){if(row.httpStatus!==200||body.code!==0||!Array.isArray(body.data?.records))problem='ORIGINAL_TASK_PAGE_REQUIRED';taskRows=body.data?.records||[];taskPageCount++;row.exactCreatedOwnTaskPresent=taskRows.some(x=>x.taskName===w.taskName)}
   if(row.endpoint.endsWith('/eventTask/save')){saveConfirmed=row.httpStatus===200&&body.code===0&&body.data===true;row.confirmedTrue=saveConfirmed;if(!saveConfirmed)problem='ORIGINAL_TASK_SAVE_NOT_CONFIRMED_NO_RETRY'}
  }).catch(()=>{row.responseBodyObserved=false;problem='ESSENTIAL_TASK_UI_RESPONSE_UNOBSERVED'}).finally(()=>{requests.push(row);reads.delete(p)});reads.add(p);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION'});
}
const fieldCode=(label,dialog=false)=>`(()=>{const scope=${dialog?'Array.from(document.querySelectorAll(".el-dialog")).find(e=>e.getClientRects().length)?.querySelector(".el-dialog__body")':'document.body'};if(!scope)return null;return Array.from(scope.querySelectorAll('.el-form-item')).find(e=>${dialog?'true':"!e.closest('.el-dialog')"}&&e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\\s:：]/g,'')===${JSON.stringify(label)})?.querySelector('input,textarea')})()`;
async function fill(label,value,dialog=false){const expression=fieldCode(label,dialog);if(!await evaluate(`(()=>{const e=${expression};if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.dispatchEvent(new Event('blur',{bubbles:true}));return true})()`))throw Error('NORMAL_EDITABLE_FIELD_REQUIRED')}
async function clickButton(text,dialog=false){if(!await evaluate(`(()=>{const all=Array.from(document.querySelectorAll(${JSON.stringify(dialog?'.el-dialog button':'button')})).filter(e=>e.getClientRects().length&&${dialog?'true':"!e.closest('.el-dialog')"}&&e.textContent.trim()===${JSON.stringify(text)});if(all.length!==1||all[0].disabled)return false;all[0].click();return true})()`))throw Error('ONE_NORMAL_VISIBLE_BUTTON_REQUIRED')}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',x=>fs.appendFile(O+'/chrome.private.log',x));chrome.on('exit',()=>{for(const p of pending.values())p.reject(Error('OWN_CHROME_EXITED'));pending.clear()});
 await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});
 ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p)v.error?p.reject(Error('OWN_CDP_ERROR')):p.resolve(v.result)}else observe(v)});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const name of ['Page','Runtime','Network'])await send(name+'.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);
 stage='normal-original-login';await send('Page.navigate',{url:w.base+'/zhumadian/emergency/home/index'},session);await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});Array.from(document.querySelectorAll('.login-body button')).find(e=>e.textContent.trim()==='登录').click()})()`);
 await until(()=>logged&&current);cases.push({case:'real-compiled-normal-nonadmin-login',passed:true});

 if(w.researchRequired){
  stage='native-event-list-for-research';eventRows=[];const eventBefore=eventPageCount;
  await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/response'},session);
  await until(()=>eventPageCount>eventBefore);await fill('事件名称',w.eventName);const filteredBefore=eventPageCount;await clickButton('搜索');
  await until(()=>eventPageCount>filteredBefore&&eventRows.some(row=>row.id===w.eventId&&String(row.researchStatus)==='0'));
  if(!await evaluate(`(()=>{const rows=Array.from(document.querySelectorAll('.el-table__body tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(w.eventNumber)})&&e.textContent.includes(${JSON.stringify(w.eventName)}));if(rows.length!==1)return false;const b=Array.from(rows[0].querySelectorAll('button')).find(e=>e.textContent.trim()==='研判');if(!b)return false;b.click();return true})()`))throw Error('ONE_NATIVE_OWN_EVENT_RESEARCH_ACTION_REQUIRED');
  await until(()=>eventDetail?.id===w.eventId&&String(eventDetail.researchStatus)==='0');
  stage='original-event-level-and-research-result';
  if(!await evaluate(`(()=>{const item=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='事件级别');const select=item?.querySelector('.el-select__wrapper')||item?.querySelector('.el-select input');if(!select)return false;select.click();return true})()`))throw Error('ORIGINAL_EVENT_LEVEL_SELECT_REQUIRED');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-select-dropdown__item")).some(e=>e.getClientRects().length&&!e.classList.contains("is-disabled"))'));
  await evaluate('Array.from(document.querySelectorAll(".el-select-dropdown__item")).find(e=>e.getClientRects().length&&!e.classList.contains("is-disabled")).click()');
  await fill('研判结果',researchText);await clickButton('提交');await until(()=>researchConfirmed);
  await until(()=>evaluate('location.pathname==="/zhumadian/emergency/emergencyResponse/response"'));
  await until(()=>evaluate('!!('+fieldCode('事件名称')+')'));await fill('事件名称',w.eventName);const afterResearch=eventPageCount;await clickButton('搜索');
  await until(()=>eventPageCount>afterResearch&&eventRows.some(row=>row.id===w.eventId&&String(row.researchStatus)==='1'&&row.eventLevel===researchLevel&&row.researchResult===researchText));
  cases.push({case:'real-event-list-research-level-confirmation-and-original-readback',passed:true,researchRequests:1});
 }
 stage='task-list-and-add-route';await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/taskSend'},session);await until(()=>taskPageCount>0);await clickButton('新增');
 await until(()=>evaluate('location.pathname==="/zhumadian/emergency/emergencyResponse/taskSend/add"&&!!('+fieldCode('任务名称')+')'));
 await fill('任务名称',w.taskName);await fill('任务内容',w.taskContent);
 cases.push({case:'real-task-list-opens-original-add-form',passed:true});
 stage='required-event-not-sent';await clickButton('提交');await until(()=>evaluate('!!document.querySelector(".el-form-item__error")'));
 if(saveAttempts!==0)throw Error('MISSING_EVENT_MUST_NOT_SEND_TASK_SAVE');cases.push({case:'missing-confirmed-event-blocks-task-post',passed:true});
 stage='original-confirmed-event-picker';if(!await evaluate(`(()=>{const e=${fieldCode('事件编号')};if(!e||!e.readOnly)return false;e.click();return true})()`))throw Error('ORIGINAL_READONLY_EVENT_PICKER_REQUIRED');
 await until(()=>evaluate('Array.from(document.querySelectorAll(".el-dialog")).some(e=>e.getClientRects().length&&e.textContent.includes("信息选择"))'));
 await clickButton('确定',true);await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message")).some(e=>e.textContent.includes("请先选择一条事件信息"))'));
 if(!await evaluate('Array.from(document.querySelectorAll(".el-dialog")).some(e=>e.getClientRects().length)'))throw Error('EMPTY_EVENT_CONFIRM_MUST_KEEP_DIALOG');
 cases.push({case:'empty-picker-confirm-keeps-dialog-and-task-input',passed:true});
 await until(()=>requests.some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.confirmedFilterMatched&&r.httpStatus===200&&r.businessCode===0));
 const beforeRequests=requests.length;await fill('事件名称',w.eventName,true);await clickButton('搜索',true);
 await until(()=>requests.slice(beforeRequests).some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.confirmedFilterMatched&&r.expectedNameFilterMatched&&r.exactOwnedEventPresent)&&eventRows.some(row=>row.id===w.eventId));
 await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-dialog .el-table__body tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(w.eventNumber)})&&e.textContent.includes(${JSON.stringify(w.eventName)})).length===1`));
 if(!requests.some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.confirmedFilterMatched&&r.exactOwnedEventPresent))throw Error('ORIGINAL_CONFIRMED_EVENT_FILTER_REQUIRED');
 if(!await evaluate(`(()=>{const rows=Array.from(document.querySelectorAll('.el-dialog .el-table__body tbody tr'));const selected=rows.filter(e=>e.textContent.includes(${JSON.stringify(w.eventNumber)})&&e.textContent.includes(${JSON.stringify(w.eventName)}));if(selected.length!==1)return false;const radio=selected[0].querySelector('.el-radio,input[type=radio]');if(!radio)return false;radio.click();return true})()`))throw Error('EXACT_REAL_PICKER_EVENT_RADIO_REQUIRED');
 await clickButton('确定',true);
 await until(()=>evaluate('!Array.from(document.querySelectorAll(".el-dialog")).some(e=>e.getClientRects().length)'));
 if(!await evaluate(`(${fieldCode('事件编号')})?.value===${JSON.stringify(w.eventNumber)}&&(${fieldCode('事件名称')})?.value===${JSON.stringify(w.eventName)}&&(${fieldCode('任务名称')})?.value===${JSON.stringify(w.taskName)}&&(${fieldCode('任务内容')})?.value===${JSON.stringify(w.taskContent)}`))throw Error('SELECTED_EVENT_AND_TASK_DRAFT_MUST_MATCH');
 cases.push({case:'real-confirmed-event-radio-fills-linked-event-and-retains-task-draft',passed:true});
 stage='one-real-task-submit';await clickButton('提交');await until(()=>saveConfirmed);await until(()=>evaluate('location.pathname==="/zhumadian/emergency/emergencyResponse/taskSend"'));
 await until(()=>evaluate('!!('+fieldCode('任务名称')+')'));const taskBefore=taskPageCount;await fill('任务名称',w.taskName);await clickButton('搜索');
 await until(()=>taskPageCount>taskBefore&&taskRows.some(row=>row.taskName===w.taskName&&row.infoId===w.eventId&&String(row.taskStatus)==='2'));
 if(saveAttempts!==1)throw Error('ONE_ORIGINAL_TASK_CREATE_REQUIRED');
 cases.push({case:'real-page-task-save-success-and-linked-pending-list-row',passed:true,taskRequests:1});
 await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_TASK_UI_RUNTIME_EXCEPTION');
 proof={passed:true,cases,requests,actualCompiledApplicationAndOriginalAPIs:true,taskCreationUIAccepted:true,
  taskSaveRequests:saveAttempts,taskSaveConfirmed:saveConfirmed,researchRequests:researchAttempts,researchUIAccepted:researchConfirmed,APIsMocked:false,APIShortcutUsed:false,credentialOrTokenPersistedInProof:false,publicOrDesktopTouched:false,fullCloneReady:false};
}catch(error){proof={passed:false,stage,failure:error.message,cases,requests,taskSaveRequests:saveAttempts,taskSaveConfirmed:saveConfirmed,researchRequests:researchAttempts,researchConfirmed,APIsMocked:false,fullCloneReady:false};
 try{
  await persist('diagnostic.private.json',await evaluate('({path:location.pathname,headings:Array.from(document.querySelectorAll("h1,h2,h3")).map(e=>e.textContent),visibleLabels:Array.from(document.querySelectorAll(".el-form-item__label")).filter(e=>e.getClientRects().length).map(e=>e.textContent),dropdowns:Array.from(document.querySelectorAll(".el-select-dropdown")).map(e=>({visible:e.getClientRects().length>0,text:e.textContent.slice(0,180)})),alerts:Array.from(document.querySelectorAll(".el-alert,.el-message")).map(e=>e.textContent.slice(0,120))})'));
  if(eventDetail?.id===w.eventId&&stage==='original-event-level-and-research-result'){
   const screenshot=await send('Page.captureScreenshot',{format:'png',clip:{x:0,y:150,width:1200,height:850,scale:1}},session);
   await fs.writeFile(O+'/research-diagnostic.private.png',Buffer.from(screenshot.data,'base64'));
  }
 }catch{await persist('diagnostic-unavailable.json',{failed:true})}

}finally{
 w.password='';current=null;
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close()}
 let next=0;while(chrome?.pid&&chrome.exitCode===null&&chrome.signalCode===null){if(active&&Date.now()>next){next=Date.now()+3000;try{const s=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);s.addEventListener('error',()=>{});s.addEventListener('open',()=>s.send(JSON.stringify({id:1,method:'Browser.close'})),{once:true});setTimeout(()=>s.close(),2000)}catch{}}await sleep(100)}
 await persist('browser-terminal.json',{normalBrowserClosed:chrome?.exitCode===0,exitCode:chrome?.exitCode,forceTerminationUsed:false});await persist('result.json',proof);
}
process.stdout.write(JSON.stringify({passed:proof.passed,cases:proof.cases.length,taskSaveRequests:saveAttempts,normalBrowserClosed:chrome?.exitCode===0}));
if(!proof.passed||chrome?.exitCode!==0)process.exitCode=1;
