import fs from'node:fs/promises';import{spawn}from'node:child_process';
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>12000)throw Error('BOUNDED_OWN_WIRE')}
const w=JSON.parse(raw);raw='';
if(!w.syntheticNormalUser||!w.ownCaptchaPolicyDisabled||w.phase!=='normal-restart'||!/^http:\/\/127\.0\.0\.1:[0-9]+$/.test(w.base)||!/^[a-f0-9]{32}$/.test(w.nonce))throw Error('OWN_EVENT_TEST_SCOPE');
const root='D:/Project/Zhumadian/work/ev990',O=root+'/browser/'+w.phase,contextFile='D:/Project/Zhumadian/work/ev985/event-context.private.json';
await fs.mkdir(O,{recursive:true});const save=(n,v)=>fs.writeFile(O+'/'+n,JSON.stringify(v,null,2)+'\n');
const name='OWN_EVENT_CRUD_R985_'+w.nonce,content='OWN_EVENT_CRUD_CONTENT_'+w.nonce,edited=content+'_EDITED',unsaved=content+'_UNSAVED';
const wait=ms=>new Promise(r=>setTimeout(r,ms));let chrome,ws,session,firstSession,seq=0,token='',stage='start',proof,problem=null;const pending=new Map(),tracked=new Map(),reads=new Set(),requests=[],exceptions=[],cases=[];
function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN)return reject(Error('OWN_CDP_CLOSED'));const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method))},12000);pending.set(id,{resolve:r=>{clearTimeout(timer);resolve(r)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}))})}
async function evaluate(code){const r=await send('Runtime.evaluate',{expression:code,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error('OWN_UI_EVALUATION');return r.result.value}
async function until(fn,ms=30000){const end=Date.now()+ms;for(;;){if(problem)throw Error(problem);if(await fn())return;if(Date.now()>end)throw Error('OWN_EVENT_UI_TIMEOUT');await wait(40)}}
function check(value,label){if(!value)throw Error(label);cases.push({case:label,passed:true})}
function observe(v){
 if(v.method==='Fetch.requestPaused'){
  const u=new URL(v.params.request.url),sid=v.sessionId;
  if(u.origin===w.base||['about:','data:'].includes(u.protocol))send('Fetch.continueRequest',{requestId:v.params.requestId},sid).catch(()=>{});
  else send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},sid).catch(()=>{});
 }else if(v.method==='Network.requestWillBeSent'){
  const u=new URL(v.params.request.url);if(u.origin!==w.base||!u.pathname.startsWith('/zhumadian/api/'))return;
  if(tracked.size>160){problem='BOUNDED_EVENT_REQUESTS';return}
  const key=v.sessionId+':'+v.params.requestId;
  tracked.set(key,{path:u.pathname,method:v.params.request.method,secondaryContext:v.sessionId!==firstSession});
 }else if(v.method==='Network.responseReceived'){
  const r=tracked.get(v.sessionId+':'+v.params.requestId);if(r)r.status=v.params.response.status;
 }else if(v.method==='Network.loadingFinished'){
  const row=tracked.get(v.sessionId+':'+v.params.requestId);if(!row)return;
  const p=send('Network.getResponseBody',{requestId:v.params.requestId},v.sessionId).then(r=>{
   let b;try{b=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body)}catch{row.nonJSON=true;requests.push(row);return}
   row.code=b.code;row.booleanResult=typeof b.data==='boolean'?b.data:null;
   if(row.path.endsWith('/oauth/Login'))token=b.data?.token||'';
   if(row.path.endsWith('/oauth/CurrentUser'))row.normalOwnUserMatched=b.data?.userInfo?.userId===w.expectedUserId;
   requests.push(row);
  }).catch(()=>{problem='EVENT_RESPONSE_OBSERVATION_FAILED'}).finally(()=>reads.delete(p));reads.add(p);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({stage,text:v.params.exceptionDetails?.text||'uncaught'});
}
const click=(selector,label)=>evaluate(`(()=>{const b=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(e=>e.getClientRects().length&&!e.disabled&&e.textContent.trim()===${JSON.stringify(label)});if(!b)return false;b.click();return true})()`);
const value=label=>evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
async function fill(label,text){if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=Array.from(a?.querySelectorAll('input,textarea')||[]).find(e=>!e.disabled&&!e.readOnly);if(!e)return false;e.value=${JSON.stringify(text)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_EDITABLE_FIELD_'+label)}
const immediateNativeFill=fill;
fill=async(label,text)=>{
 await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-form-item')).some(a=>a.getClientRects().length&&a.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)}&&Array.from(a.querySelectorAll('input,textarea')).some(e=>!e.disabled&&!e.readOnly&&e.getClientRects().length))`));
 return immediateNativeFill(label,text);
};
async function select(label,expected){const id=await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const n=a?.querySelector('[aria-controls]');a?.querySelector('.el-select__wrapper,.el-input__wrapper')?.click();return n?.getAttribute('aria-controls')})()`);if(!id)throw Error('OWN_SELECT_ID');
 await until(()=>evaluate(`Array.from(document.getElementById(${JSON.stringify(id)})?.querySelectorAll('.el-select-dropdown__item')||[]).some(e=>e.getClientRects().length&&!e.classList.contains('is-disabled')&&e.textContent.trim()===${JSON.stringify(expected)})`));
 if(!await evaluate(`(()=>{const e=Array.from(document.getElementById(${JSON.stringify(id)})?.querySelectorAll('.el-select-dropdown__item')||[]).find(e=>e.getClientRects().length&&!e.classList.contains('is-disabled')&&e.textContent.trim()===${JSON.stringify(expected)});if(!e)return false;e.click();return true})()`))throw Error('OWN_SELECT_OPTION')}
async function attach(){const t=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;for(const n of['Runtime','Page','Network'])await send(n+'.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);return session}
async function api(path){if(!/^\/eventInfo\/(getPage\?|getById\?)/.test(path))throw Error('READ_ONLY_OWN_EVENT_API');const ua=await evaluate('navigator.userAgent');const r=await fetch(w.base+'/zhumadian/api/serv'+path,{headers:{Authorization:token,'User-Agent':ua}});const b=await r.json();if(r.status!==200||b.code!==0)throw Error('OWN_EVENT_READ');return b.data}
async function exactRecord(){const data=await api('/eventInfo/getPage?current=1&size=5&eventName='+encodeURIComponent(name));if(!Array.isArray(data.records)||data.records.length>5)throw Error('OWN_EVENT_BOUNDED_PAGE');const rows=data.records.filter(r=>r.eventName===name);return rows}
const rowExpr=`Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.textContent.includes(${JSON.stringify(name)}))`;
async function search(expect=true){await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/response'},session);await until(()=>evaluate('!!document.querySelector(".table-search")'));await fill('事件名称',name);if(!await click('.table-search button','搜索'))throw Error('OWN_SEARCH_BUTTON');if(expect)await until(()=>evaluate(`!!(${rowExpr})`));}
async function action(label){if(!await evaluate(`(()=>{const r=${rowExpr};const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()===${JSON.stringify(label)}&&!e.disabled);if(!b)return false;b.click();return true})()`))throw Error('OWN_EVENT_ROW_ACTION_'+label)}
async function edit(){await action('编辑');await until(async()=>await value('事件内容')===edited)}
function count(suffix){return requests.filter(r=>r.path.endsWith(suffix)).length}
async function openNormalSibling(){
 const before=new Set((await send('Target.getTargets')).targetInfos.map(t=>t.targetId));
 await send('Runtime.evaluate',{expression:'window.open("about:blank","_blank")',userGesture:true,returnByValue:false},firstSession);
 let t;await until(async()=>{t=(await send('Target.getTargets')).targetInfos.find(t=>!before.has(t.targetId)&&t.type==='page'&&t.openerId);return !!t});
 session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 for(const n of['Runtime','Page','Network'])await send(n+'.enable',{},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);
 check(await evaluate('sessionStorage.length>0'),'normal-browser-opener-inherits-storage-without-token-copy');
}
async function close(){if(ws?.readyState===WebSocket.OPEN)await send('Browser.close').catch(()=>{});if(chrome)while(chrome.exitCode===null)await new Promise(r=>{const t=setTimeout(r,1000);chrome.once('exit',()=>{clearTimeout(t);r()})});ws?.close()}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',v=>fs.appendFile(O+'/chrome.private.log',v));
 let active;await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p){if(v.error)p.reject(Error('CDP_PROTOCOL'));else p.resolve(v.result)}}else observe(v)});
 firstSession=await attach();stage='normal-original-login';await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/response'},session);await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const a=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=a[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});})()`);if(!await click('.login-body button','登录'))throw Error('OWN_LOGIN_BUTTON');await until(()=>requests.some(r=>r.path.endsWith('/oauth/CurrentUser')&&r.normalOwnUserMatched));w.password='';check(!!token,'normal-nonadmin-original-login');
 let context;
 {
  context=JSON.parse(await fs.readFile(contextFile,'utf8'));if(context.phase!=='edited-verified'||context.nonce!==w.nonce||context.name!==name)throw Error('OWN_EXISTING_CONTEXT_NO_RECREATE');
  stage='normal-restart-edit-readback';const rows=await exactRecord();check(rows.length===1&&rows[0].id===context.id&&rows[0].eventContent===edited&&rows[0].coordinate===context.coordinate,'normal-six-component-restart-retains-same-event-edit');
  await search();await edit();await fill('事件内容',unsaved);check(await value('事件内容')===unsaved,'first-tab-unsaved-input-entered');
  stage='second-tab-original-delete-cancel';await openNormalSibling();await search();await until(()=>requests.some(r=>r.secondaryContext&&r.path.endsWith('/oauth/CurrentUser')&&r.normalOwnUserMatched));let before=count('/eventInfo/removeById');await action('删除');await until(()=>evaluate('!!document.querySelector(".el-message-box")'));if(!await click('.el-message-box button','取消'))throw Error('OWN_DELETE_CANCEL');await until(()=>evaluate('!document.querySelector(".el-message-box")||!document.querySelector(".el-message-box").getClientRects().length'));check(count('/eventInfo/removeById')===before&&(await exactRecord()).length===1,'native-delete-cancel-sends-no-remove-and-retains-record');
  stage='second-tab-original-delete-confirm';await action('删除');await until(()=>evaluate('!!document.querySelector(".el-message-box")&&document.querySelector(".el-message-box").getClientRects().length'));await fs.writeFile(contextFile,JSON.stringify({...context,phase:'delete-issued-do-not-retry'},null,2)+'\n');if(!await click('.el-message-box button','确定'))throw Error('OWN_DELETE_CONFIRM');await until(()=>count('/eventInfo/removeById')===before+1);check(requests.filter(r=>r.path.endsWith('/eventInfo/removeById')).at(-1)?.booleanResult===true,'native-delete-confirm-once-returns-true');await until(async()=> (await exactRecord()).length===0);check(true,'original-list-excludes-logically-deleted-own-event');
  session=firstSession;stage='original-editor-false-save';check(await value('事件内容')===unsaved,'first-tab-input-retained-after-other-tab-delete');before=count('/eventInfo/updateById');if(!await click('.footer button','提交'))throw Error('OWN_FALSE_EDIT_SUBMIT');await until(()=>count('/eventInfo/updateById')===before+1);check(requests.filter(r=>r.path.endsWith('/eventInfo/updateById')).at(-1)?.booleanResult===false,'actual-original-update-false-for-deleted-own-record');await until(()=>evaluate('document.body.textContent.includes("保存未完成，请保留当前内容")'));check(await value('事件内容')===unsaved&&await evaluate("location.pathname.includes('/response/edit')"),'failed-save-keeps-editor-and-input-and-shows-failure');check((await exactRecord()).length===0,'failed-save-does-not-resurrect-deleted-record');context.phase='delete-and-false-save-verified';await fs.writeFile(contextFile,JSON.stringify(context,null,2)+'\n');
 }
 await Promise.all([...reads]);check(exceptions.length===0,'no-original-compiled-UI-uncaught-exceptions');proof={passed:true,phase:w.phase,cases,requests,exceptions,eventCreatesObserved:count('/eventInfo/save'),APIsMocked:false,mutationsOnlyThroughOriginalUI:true,normalNonadminLogin:true,actualIISTLSOrPublicAccepted:false,fullCloneReady:false};
}catch(e){proof={passed:false,phase:w.phase,stage,type:e.message,cases,requests,exceptions,eventCreatesObserved:count('/eventInfo/save'),APIsMocked:false,fullCloneReady:false};try{await save('diagnostic.private.json',await evaluate('({path:location.pathname,labels:Array.from(document.querySelectorAll(".el-form-item__label")).map(e=>e.textContent),alerts:Array.from(document.querySelectorAll(".el-message")).map(e=>e.textContent.slice(0,100))})'));const shot=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(O+'/failure.png',Buffer.from(shot.data,'base64'))}catch{}}
finally{token='';w.password='';await close();await save('browser-terminal.json',{exitCode:chrome?.exitCode,normalBrowserClosed:chrome?.exitCode===0,forceTerminationUsed:false});await save('result.json',proof)}
process.stdout.write(JSON.stringify({passed:proof.passed,phase:w.phase,cases:cases.length,stage,normalBrowserClosed:chrome?.exitCode===0}));if(!proof.passed||chrome?.exitCode!==0)process.exitCode=1;
