import{win32}from'node:path';
import{clickStableOriginalDownload}from'./stable_original_download_click_r954.mjs';
import fs from 'node:fs/promises';
import {spawn}from'node:child_process';
import{createHash}from'node:crypto';
let input='';for await(const c of process.stdin){input+=c;if(input.length>16384)throw Error('BOUNDED_OWN_LEDGER_WIRE')}
const w=JSON.parse(input);input='';
if(!['create','readback'].includes(w.mode)||w.syntheticNormalUser!==true||w.ownCaptchaPolicyDisabled!==true||w.account!=='own_operator_a'||!/^a531[0-9a-f]{28}$/.test(w.expectedUserId)||!/^http:\/\/127\.0\.0\.1:\d{4,5}$/.test(w.base)||[8767,18891,18892].includes(+new URL(w.base).port)||!/^[0-9a-f]{32}$/.test(w.nonce)||typeof w.password!=='string')throw Error('EXACT_OWN_LEDGER_SCOPE');
const parent='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/ledger-ui-r941';
if(await fs.readFile(parent+'/own-ledger-ui.marker','utf8')!=='own-ledger-ui-r941\n')throw Error('OWN_LEDGER_MARKER');
if(w.mode!=='readback'||!['first-start','normal-restart'].includes(w.phase))throw Error('EXISTING_GENERATED_LEDGER_READBACK_ONLY');
const label=w.phase,O='D:/Project/Zhumadian/work/ledger-browser-r960/'+label;
await fs.mkdir(O,{recursive:true});await fs.mkdir(O+'/downloads');
const ownId='own-sui-'+w.nonce.slice(0,20)+'-a',description='OWN_LEDGER_UI_'+w.nonce,contextFile=parent+'/ledger-context.private.json';
const digest=b=>createHash('sha256').update(b).digest('hex'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
let chrome,ws,active,session,seq=0,token='',current=null,problem=null,stage='initializing',proof,epoch=0,currentEpoch=-1,generationAuthorized=false,generations=0,ledgerRows=null,ledgerEpoch=0;
const pending=new Map(),tracked=new Map(),reads=new Set(),cases=[],requests=[],exceptions=[],pdfResponses=[],downloads=new Map();
const save=(n,v)=>fs.writeFile(O+'/'+n,JSON.stringify(v,null,2)+'\n');
async function until(fn,ms=45000){const end=Date.now()+ms;for(;;){if(await fn())return;if(problem)throw Error(problem);if(Date.now()>end)throw Error('OWN_LEDGER_OBSERVATION_TIMEOUT');await sleep(50)}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT'))},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...sid?{sessionId:sid}:{}}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw Error('OWN_LEDGER_UI_EVALUATION');return r.result.value}
function observe(v){
 if(v.method==='Fetch.requestPaused'){
  const request=v.params.request,u=new URL(request.url);let allowed=u.origin===w.base||['about:','data:','blob:'].includes(u.protocol);
  if(u.origin===w.base&&u.pathname.startsWith('/zhumadian/api/')&&!['GET','HEAD'].includes(request.method)&&u.pathname!=='/zhumadian/api/jnpf/oauth/Login')allowed=false;
  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/checkHiddenDanger/sendMessage')allowed=false;
  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/checkHiddenDanger/addPdf'){
   allowed=allowed&&w.mode==='create'&&generationAuthorized&&generations===0&&request.method==='GET'&&u.searchParams.get('id')===ownId&&[...u.searchParams.keys()].join(',')==='id';
   if(allowed){generations++;fs.writeFile(O+'/generation-request-issued.json',JSON.stringify({issuedOnce:true,ownIdSHA256:digest(ownId),requestMethod:'GET',mode:w.mode})+'\n',{flag:'wx'}).then(()=>send('Fetch.continueRequest',{requestId:v.params.requestId},session)).catch(()=>{problem='OWN_GENERATION_JOURNAL_OR_RESUME_FAILED'});return;}
  }
  if(!allowed&&u.origin===w.base)problem='UNEXPECTED_LEDGER_MUTATION_OR_GENERATION_REFUSED';
  send(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:v.params.requestId,...allowed?{}:{errorReason:'BlockedByClient'}},session).catch(()=>{});
 }else if(v.method==='Network.requestWillBeSent'){
  const u=new URL(v.params.request.url);if(u.origin!==w.base||!u.pathname.startsWith('/zhumadian/api/'))return;
  tracked.set(v.params.requestId,{path:u.pathname,method:v.params.request.method,epoch});
 }else if(v.method==='Network.responseReceived'){
  const u=new URL(v.params.response.url);if(u.origin===w.base&&u.pathname.includes('/sys-file/'))pdfResponses.push({status:v.params.response.status,mime:v.params.response.mimeType});
  if(tracked.has(v.params.requestId))tracked.get(v.params.requestId).status=v.params.response.status;
 }else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);tracked.delete(v.params.requestId);
  const p=send('Network.getResponseBody',{requestId:v.params.requestId},session).then(r=>{
   let body;try{body=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body)}catch{row.nonJSON=true;return}
   row.businessCode=body.code;
   if(row.path.endsWith('/oauth/Login')){if(row.status!==200||body.code!==200)problem='ORIGINAL_NORMAL_LOGIN_REFUSED';token=body.data?.token||'';}
   if(row.path.endsWith('/oauth/CurrentUser')){current=body.data;currentEpoch=row.epoch;if(row.status!==200||body.code!==200||current?.userInfo?.userId!==w.expectedUserId||current?.userInfo?.isAdministrator!==false)problem='EXACT_ORIGINAL_NORMAL_ACTOR_REQUIRED';}
   if(row.path==='/zhumadian/api/serv/checkHiddenDanger/page'){
    if(row.status!==200||body.code!==0)problem='ORIGINAL_LEDGER_PAGE_REFUSED';ledgerRows=Array.isArray(body.data)?body.data:body.data?.records??body.data?.list;ledgerEpoch++;
   }
   if(row.path==='/zhumadian/api/serv/checkHiddenDanger/addPdf')row.generationSuccess=row.status===200&&body.code===0;
  }).catch(()=>{if(row.path?.endsWith('/oauth/Login')||row.path?.endsWith('/oauth/CurrentUser')||row.path==='/zhumadian/api/serv/checkHiddenDanger/page')problem='ESSENTIAL_LEDGER_RESPONSE_OBSERVATION_FAILED';else row.bodyObservationUnavailable=true;}).finally(()=>{row.endpoint=row.path.replace(/own-sui-[0-9a-f]{20}-a/g,':owned-id');delete row.path;requests.push(row);reads.delete(p)});reads.add(p);
 }else if(v.method==='Runtime.exceptionThrown')exceptions.push({stage,type:'ORIGINAL_COMPILED_UI_EXCEPTION'});
 else if(['Browser.downloadWillBegin','Page.downloadWillBegin'].includes(v.method))downloads.set(v.params.guid,{filename:v.params.suggestedFilename,state:'started'});
 else if(['Browser.downloadProgress','Page.downloadProgress'].includes(v.method)&&downloads.has(v.params.guid))downloads.get(v.params.guid).state=v.params.state;
}
async function boundedBytes(response){const reader=response.body.getReader(),chunks=[];let n=0;for(;;){const v=await reader.read();if(v.done)break;n+=v.value.length;if(n>4*1024*1024){await reader.cancel();throw Error('BOUNDED_OWN_LEDGER_RESPONSE')}chunks.push(Buffer.from(v.value));}return Buffer.concat(chunks)}
let ua='';
async function native(path,method='GET',data){
 const allowed=path==='/checkHiddenDanger/insert'&&method==='POST'&&w.mode==='create'&&data?.id===ownId||method==='GET'&&(path==='/checkHiddenDanger/getDetails/'+ownId||path==='/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+ownId||/^\/sys-file\/[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\.pdf$/.test(path));
 if(!allowed)throw Error('EXACT_OWN_LEDGER_NATIVE_SCOPE');
 const response=await fetch(w.base+'/zhumadian/api/serv'+path,{method,headers:{Authorization:token,'User-Agent':ua,...data?{'Content-Type':'application/json'}:{}},...data?{body:JSON.stringify(data)}:{},signal:AbortSignal.timeout(20000)});
 if(response.status!==200)throw Error('OWN_LEDGER_NATIVE_HTTP');const b=await boundedBytes(response);
 if(path.startsWith('/sys-file/'))return b;
 const result=JSON.parse(b.toString('utf8'));if(result.code!==0)throw Error('OWN_LEDGER_NATIVE_BUSINESS');return result.data;
}
async function ownRow(){return evaluate(`(()=>{const rows=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(description)}));if(rows.length!==1)return null;const buttons=Array.from(rows[0].querySelectorAll('button'));return{supervise:buttons.filter(b=>b.textContent.trim()==='督办').map(b=>({disabled:b.disabled})),detail:buttons.filter(b=>b.textContent.trim()==='详情').length}})()`)}
async function clickRow(text){return evaluate(`(()=>{const rows=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(description)}));if(rows.length!==1)throw Error('ONE_OWN_LEDGER_ROW');const b=Array.from(rows[0].querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(text)});if(!b||b.disabled)throw Error('ENABLED_OWN_ROW_ACTION');b.click();})()`)}
async function searchOwn(){
 const before=ledgerEpoch;
 await evaluate(`(()=>{const group=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.includes('隐患描述'));const input=group?.querySelector('input');if(!input)throw Error('ORIGINAL_LEDGER_SEARCH_INPUT');input.value=${JSON.stringify(description)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));const button=Array.from(document.querySelectorAll('button')).find(e=>e.getClientRects().length&&['搜索','查询'].includes(e.textContent.trim()));if(!button)throw Error('ORIGINAL_SEARCH_ACTION');button.click();})()`);
 await until(()=>ledgerEpoch>before&&Array.isArray(ledgerRows)&&ledgerRows.some(row=>row.id===ownId));await until(async()=>!!await ownRow());
}
async function confirmBox(yes){await until(()=>evaluate('!!document.querySelector(".el-message-box__btns")'));await evaluate(`(()=>{const buttons=Array.from(document.querySelectorAll('.el-message-box__btns button'));const b=buttons.find(e=>e.textContent.trim()===${JSON.stringify(yes?'确定':'取消')});if(!b)throw Error('EXPECTED_CONFIRMATION_ACTION');b.click();})()`);}
async function close(){if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close()}let next=0;while(chrome?.pid&&chrome.exitCode===null&&chrome.signalCode===null){if(active&&Date.now()>next){next=Date.now()+3000;try{const closer=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);closer.addEventListener('error',()=>{});closer.addEventListener('open',()=>closer.send(JSON.stringify({id:1,method:'Browser.close'})),{once:true});setTimeout(()=>closer.close(),2000)}catch{}}await sleep(100)}}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',x=>fs.appendFile(O+'/chrome.private.log',x));chrome.on('exit',()=>{for(const p of pending.values())p.reject(Error('OWN_CHROME_EXITED'));pending.clear()});
 await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});
 ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',event=>{const v=JSON.parse(event.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p)v.error?p.reject(Error('OWN_CDP_ERROR')):p.resolve(v.result)}else observe(v)});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 for(const name of ['Page','Runtime','Network'])await send(name+'.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:win32.normalize(O+'/downloads'),eventsEnabled:true});await send('Emulation.setDeviceMetricsOverride',{width:1600,height:1100,deviceScaleFactor:1,mobile:false},session);
 stage='normal-security-login-to-original-ledger';await send('Page.navigate',{url:w.base+'/zhumadian/hiddenInvestigate/perilLedger'},session);await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});const b=Array.from(document.querySelectorAll('.login-body button')).find(e=>e.textContent.trim()==='登录');if(!b)throw Error('NORMAL_LOGIN_BUTTON');b.click()})()`);
 await until(()=>token&&current);ua=await evaluate('navigator.userAgent');
 const menuFlat=[];function walkMenu(nodes){for(const n of nodes||[]){menuFlat.push({path:n.path,urlAddress:n.urlAddress,id:n.id,hasChildren:n.hasChildren});walkMenu(n.children)}}walkMenu(current.menuList);
 await save('normal-login-route-diagnostic.private.json',{menus:menuFlat,permissions:(current.permissionList||[]).map(n=>({modelId:n.modelId,button:(n.button||[]).map(b=>({path:b.path,urlAddress:b.urlAddress}))})),dom:await evaluate('({path:location.pathname,title:document.title,table:!!document.querySelector(".el-table__body-wrapper"),home:!!document.querySelector(".home-wrapper"),body:document.body.textContent.slice(0,500)})')});
 stage='fresh-original-ledger-navigation';await send('Page.navigate',{url:w.base+'/zhumadian/hiddenInvestigate/perilLedger'},session);
 await until(()=>Array.isArray(ledgerRows));await until(()=>evaluate('!!document.querySelector(".el-table__body-wrapper")'));
 cases.push({case:'original-security-normal-nonadmin-login-and-native-ledger-route',passed:true});
 let context;
 if(w.mode==='create'){
  stage='prepare-one-owned-business-record';try{await fs.access(contextFile);throw Error('PREVIOUS_LEDGER_CONTEXT_REFUSE_CREATION')}catch(e){if(e.code!=='ENOENT')throw e}
  if(await native('/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+ownId)!==null)throw Error('OWN_LEDGER_ID_ALREADY_USED');
  const entity={id:ownId,correctDepartmentName:'自有合成部门',hiddenDangerPlace:'自有台账测试位置',hiddenDangerExplain:description,checkDate:'2026-11-04',correctDeadline:'2026-11-10',hiddenDangerStatus:'待整改',logStatus:false,deleted:false};
  await fs.writeFile(contextFile,JSON.stringify({phase:'insert-intent',id:ownId,nonce:w.nonce,actor:w.expectedUserId})+'\n',{flag:'wx'});
  if(await native('/checkHiddenDanger/insert','POST',entity)!==true)throw Error('ONE_OWN_LEDGER_INSERT_REQUIRED');
  const before=await native('/checkHiddenDanger/getDetails/'+ownId);if(before.id!==ownId||before.logStatus===true)throw Error('OWN_UNSUPERVISED_RECORD_REQUIRED');
  await fs.writeFile(contextFile,JSON.stringify({phase:'inserted',id:ownId,nonce:w.nonce,actor:w.expectedUserId})+'\n');
  stage='original-ledger-search';await searchOwn();let state=await ownRow();if(state.supervise.length!==1||state.supervise[0].disabled||state.detail!==1)throw Error('ORIGINAL_LEDGER_ACTION_STATE');cases.push({case:'normal-native-record-found-by-original-search',passed:true});
  stage='cancel-supervision';await clickRow('督办');await confirmBox(false);await until(()=>evaluate('!document.querySelector(".el-message-box__btns")'));if(generations!==0||await native('/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+ownId)!==null)throw Error('CANCEL_MUST_NOT_GENERATE_OR_WRITE_LOG');cases.push({case:'cancel-original-supervision-dialog-causes-no-generation',passed:true});
  stage='confirm-one-original-supervision';await clickRow('督办');await until(()=>evaluate('document.querySelector(".el-message-box__message")?.textContent.includes("是否督办")'));
  await fs.writeFile(O+'/generation-confirm-intent.json',JSON.stringify({ownIdSHA256:digest(ownId),confirmedOnce:true})+'\n',{flag:'wx'});generationAuthorized=true;await confirmBox(true);
  await until(()=>requests.some(r=>r.generationSuccess));await until(async()=>{const s=await ownRow();return s?.supervise.length===1&&s.supervise[0].disabled});if(generations!==1)throw Error('ONE_GENERATION_ONLY');
  const record=await native('/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+ownId),row=await native('/checkHiddenDanger/getDetails/'+ownId);
  if(row.logStatus!==true||record.checkHiddenDangerId!==ownId||record.createId!==w.expectedUserId)throw Error('NATIVE_SUPERVISION_ACTOR_AND_STATUS');
  const pdf=await native(record.url);if(pdf.subarray(0,5).toString('ascii')!=='%PDF-')throw Error('NATIVE_PDF_BYTES_REQUIRED');
  context={phase:'generated-verified',id:ownId,nonce:w.nonce,actor:w.expectedUserId,logId:record.id,url:record.url,createDate:record.createDate,pdf:{bytes:pdf.length,sha256:digest(pdf)}};await fs.writeFile(contextFile,JSON.stringify(context,null,2)+'\n');
  cases.push({case:'original-ledger-button-confirms-once-and-becomes-disabled-after-success',passed:true});
 }else{
  context=JSON.parse(await fs.readFile(contextFile,'utf8'));if(context.phase!=='generated-verified'||context.id!==ownId||context.nonce!==w.nonce||context.actor!==w.expectedUserId)throw Error('EXACT_EXISTING_LEDGER_CONTEXT');
  stage='normal-restart-ledger-readback';await searchOwn();const state=await ownRow();if(state.supervise.length!==1||!state.supervise[0].disabled)throw Error('RESTART_RETAINS_SUPERVISED_BUTTON_STATE');
  const record=await native('/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+ownId),pdf=await native(context.url);
  if(record.id!==context.logId||record.url!==context.url||record.createDate!==context.createDate||pdf.length!==context.pdf.bytes||digest(pdf)!==context.pdf.sha256||generations!==0)throw Error('RESTART_LOG_AND_PDF_BYTES_RETAINED');
  cases.push({case:'normal-restart-new-login-retains-ledger-status-log-and-file-without-regeneration',passed:true});
 }
 stage='original-ledger-detail-and-pdf-preview';await clickRow('详情');await until(()=>evaluate('location.pathname==="/zhumadian/hiddenInvestigate/perilLedger/detail"&&document.body.textContent.includes("督办信息")'));
 const url=await evaluate('location.href');if(new URL(url).searchParams.get('id')!==ownId)throw Error('EXACT_NATIVE_DETAIL_LINK');
 await evaluate('(()=>{const a=Array.from(document.querySelectorAll(".el-link")).filter(e=>e.textContent.includes("隐患整改督办通知书"));if(a.length!==1)throw Error("ONE_GENERATED_PDF_LINK");a[0].click()})()');
 await until(()=>pdfResponses.some(r=>r.status===200));await until(()=>evaluate('Array.from(document.querySelectorAll(".el-drawer canvas")).some(e=>e.width>0&&e.height>0)'),60000);
 if(pdfResponses.some(r=>r.status>=400))throw Error('NATIVE_UNMODIFIED_PREVIEW_REQUEST_FAILED');cases.push({case:'original-detail-link-opens-drawer-and-renders-real-PDF-canvas-without-auth-injection',passed:true});
 stage='original-pdf-download-button';
 await clickStableOriginalDownload({evaluate,send,session,save,until});
 await until(()=>[...downloads.values()].some(d=>d.state==='completed'));const done=[...downloads.values()].filter(d=>d.state==='completed');if(done.length!==1||!done[0].filename.endsWith('.pdf')||/[\\/:]/.test(done[0].filename))throw Error('ONE_OWN_PDF_DOWNLOAD');
 let downloaded;await until(async()=>{try{downloaded=await fs.readFile(O+'/downloads/'+done[0].filename);return true}catch{return false}});
 if(downloaded.length!==context.pdf.bytes||digest(downloaded)!==context.pdf.sha256)throw Error('ACTUAL_ANCHOR_DOWNLOAD_BYTES_MUST_MATCH');cases.push({case:'original-drawer-download-button-produces-exact-generated-PDF-bytes',passed:true});
 stage='full-detail-refresh';epoch++;await send('Page.reload',{ignoreCache:true},session);await until(()=>currentEpoch===epoch&&current);await until(()=>evaluate('document.body.textContent.includes("督办信息")&&Array.from(document.querySelectorAll(".el-link")).some(e=>e.textContent.includes("隐患整改督办通知书"))'));
 cases.push({case:'full-refresh-retains-original-supervision-detail-link',passed:true});await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_LEDGER_COMPILED_UI_EXCEPTION');
 proof={passed:true,mode:w.mode,cases,requests,pdfResponses,generationRequests:generations,fixtureRecordsCreated:w.mode==='create'?1:0,actualOriginalLedgerAndDetailAndPreviewAndDownloadButtons:true,APIsMocked:false,tokenInjectedIntoPreviewOrDownload:false,normalNonadminOriginalLogin:true,desktopOrPublicUsed:false,fullCloneReady:false};
}catch(e){proof={passed:false,mode:w.mode,stage,type:e.message,cases,requests,pdfResponses,generationRequests:generations,exceptions,APIsMocked:false,fullCloneReady:false};try{await save('diagnostic.private.json',await evaluate('({path:location.pathname,tablePresent:!!document.querySelector(".el-table__body-wrapper"),drawerPresent:!!document.querySelector(".el-drawer"),canvasCount:document.querySelectorAll(".el-drawer canvas").length,formLabels:Array.from(document.querySelectorAll(".el-form-item__label")).map(e=>e.textContent),alerts:Array.from(document.querySelectorAll(".el-message")).map(e=>e.textContent.slice(0,80))})'))}catch(d){await save('diagnostic-observation-error.json',{type:d.message});try{const tree=await send('Page.getFrameTree',{},session);await save('failure-frame-tree.private.json',tree)}catch{}}}
finally{if(!proof?.passed){try{const shot=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(O+'/failure.png',Buffer.from(shot.data,'base64'))}catch{}}token='';current=null;w.password='';await close();await save('browser-terminal.json',{normalBrowserClosed:chrome?.exitCode===0,exitCode:chrome?.exitCode,forceTerminationUsed:false});await save('result.json',proof)}
process.stdout.write(JSON.stringify({passed:proof.passed,mode:w.mode,cases:proof.cases.length,generationRequests:generations,normalBrowserClosed:chrome?.exitCode===0}));if(!proof.passed||chrome?.exitCode!==0)process.exitCode=1;
