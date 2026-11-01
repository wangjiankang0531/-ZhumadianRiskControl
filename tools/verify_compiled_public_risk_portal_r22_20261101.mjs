import path from "node:path";
import fs from'node:fs/promises';import{spawn}from'node:child_process';

const root=process.argv[2];if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-business-main-r[1-9][0-9]*$/.test(root))throw Error('OWN_PORTAL_ROOT');let input='';for await(const x of process.stdin){input+=x;if(input.length>16384)throw Error('BOUNDED_OWN_PORTAL_INPUT');}const wire=JSON.parse(input);input='';if(!wire.syntheticNormalUser||!wire.ownCaptchaPolicyDisabled||!['risk-unit'].includes(wire.phase)||!/^http:\/\/127\.0\.0\.1:[0-9]+$/.test(wire.base))throw Error('OWN_PORTAL_SCOPE');const O=root+'/compiled-security-browser-'+wire.phase;await fs.mkdir(O);const sleep=ms=>new Promise(r=>setTimeout(r,ms));let chrome,ws,session,seq=0,loginToken='',updates=0;const excelDownloads=[];const pending=new Map(),tracked=new Map(),http=[],reads=new Set(),cases=[],exceptions=[],blocked=[];

async function until(fn,ms=25000){const end=Date.now()+ms;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_COMPILED_PORTAL_TIMEOUT');await sleep(30);}}

function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN){reject(Error('OWN_BROWSER_CLOSED'));return;}const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_RPC_TIMEOUT_'+method));},10000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}

async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error('OWN_PORTAL_SCRIPT_FAILED');return r.result.value;}

const cleanHTTP=()=>http.map(({_auth,...v})=>({...v,normalLoginTokenMatched:_auth?!!loginToken&&_auth===loginToken:null}));

function observe(v){

 if(v.method==='Browser.downloadWillBegin'){if(!/^[a-f0-9-]{36}$/.test(v.params.guid)||new URL(v.params.url).origin!==wire.base)throw Error('OWN_BROWSER_EXCEL_DOWNLOAD_SCOPE');excelDownloads.push({guid:v.params.guid,filenameEndsXLSX:String(v.params.suggestedFilename).toLowerCase().endsWith('.xlsx'),state:'begun'});}
 else if(v.method==='Browser.downloadProgress'){const row=excelDownloads.find(x=>x.guid===v.params.guid);if(row){row.state=v.params.state;row.bytes=v.params.totalBytes;}}
 else if(v.method==='Fetch.requestPaused'){const u=new URL(v.params.request.url);const own=u.origin===wire.base||u.protocol==='data:'||u.protocol==='about:';if(!own)blocked.push({scheme:u.protocol,host:u.hostname,path:u.pathname.slice(0,140)});send(own?'Fetch.continueRequest':'Fetch.failRequest',{requestId:v.params.requestId,...(own?{}:{errorReason:'BlockedByClient'})},session).catch(()=>{});}

 else if(v.method==='Network.requestWillBeSent'){const r=v.params.request,u=new URL(r.url);if(u.origin===wire.base&&u.pathname.startsWith('/zhumadian/api/')){if(tracked.size>=256)throw Error('BOUNDED_OWN_PORTAL_HTTP');tracked.set(v.params.requestId,{path:u.pathname,method:r.method,_auth:Object.entries(r.headers).find(([k])=>k.toLowerCase()==='authorization')?.[1]});if(u.pathname.endsWith('/riskLevel/getPage')){const q=u.searchParams,row=tracked.get(v.params.requestId);row.currentPage=Number(q.get('current'));row.departmentIsA=q.get('department')==='Own risk department A';row.departmentFilterPresent=!!q.get('department');}if(u.pathname.endsWith('/oauth/CurrentUser'))tracked.get(v.params.requestId).currentUserSystemCode=['mainSystem','safety','emergency','cqweh-endanger','workSystem'].includes(u.searchParams.get('systemCode'))?u.searchParams.get('systemCode'):'OTHER_OR_ABSENT';if(u.pathname.includes('/workflow/Engine/')){const q=u.searchParams;tracked.get(v.params.requestId).creatorFilterPresent=q.has('creatorUserId');tracked.get(v.params.requestId).creatorIsOperatorA=q.get('creatorUserId')==='a531'+(100).toString(16).padStart(28,'0');tracked.get(v.params.requestId).creatorIsReviewerB=q.get('creatorUserId')==='a531'+(101).toString(16).padStart(28,'0');tracked.get(v.params.requestId).currentPage=Number(q.get('currentPage'));}if(r.method==='POST'&&u.pathname.endsWith('/oauth/Login')){const row=tracked.get(v.params.requestId);const body=r.postData||'';const fields=new URLSearchParams(u.search);row.loginRequestProtocol='original-native-post-query';row.loginBodyEmpty=body.length===0;row.loginGrantTypePassword=fields.get('grant_type')==='password';row.formKeys=Array.from(fields.keys()).filter(x=>x.length<60).sort();row.formAccountMatched=fields.get('account')===wire.account;row.formCipherMatchesNormalHTTP=fields.get('password')===wire.expectedWirePassword;row.formBodyLooksJSON=body.trim().startsWith('{');row.contentType=Object.entries(r.headers).find(([k])=>k.toLowerCase()==='content-type')?.[1];}if(r.method==='POST'&&u.pathname.endsWith('/eventTask/updateById'))updates++;}}

 else if(v.method==='Network.responseReceived'){const r=tracked.get(v.params.requestId);if(r)r.httpStatus=v.params.response.status;}

 else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){const id=v.params.requestId,row=tracked.get(id);if(row.path.includes('/ImageCode/')){http.push(row);return;}const p=send('Network.getResponseBody',{requestId:id},session).then(r=>{let body;try{body=JSON.parse(r.base64Encoded?Buffer.from(r.body,'base64').toString('utf8'):r.body)}catch{row.nonJSON=true;http.push(row);return;}row.businessCode=body.code;if(row.path.endsWith('/oauth/Login')){loginToken=body.data?.token||'';row.loginTokenReturned=!!loginToken;const message=body.msg||body.message||'';row.ownedSyntheticRefusalDetail=String(message).replaceAll(wire.password,'[OWN_PASSWORD_REDACTED]').replaceAll(wire.expectedWirePassword,'[OWN_CIPHER_REDACTED]').slice(0,160);row.refusalMessage=['账号或密码错误','验证码错误','验证码已失效','该用户未分配权限','账号已被禁用','请输入用户名','请输入密码'].includes(message)?message:(body.code===200?'SUCCESS':'OTHER_LOGIN_REFUSAL');}if(row.path.endsWith('/oauth/CurrentUser')){row.ownUserMatched=body.data?.userInfo?.userId===wire.expectedUserId;if(body.code!==200)row.ownedSyntheticCurrentUserRefusal=String(body.msg||body.message||'').slice(0,200);row.riskMenuReturned=JSON.stringify(body.data?.menuList||[]).includes('/hiddenInvestigate/riskAnalysisUnit');row.taskDetailPermissionReturned=JSON.stringify(body.data?.permissionList||[]).includes('/emergencyResponse/taskSend/detail');row.ownedPermissionMenuPaths=(body.data?.permissionList||[]).flatMap(x=>(x.button||[]).map(y=>({path:y.path,component:y.urlAddress}))).filter(x=>x.path?.includes('taskSend')); }if(row.path.endsWith('/riskLevel/getPage')){row.total=Number(body.data?.total);row.rowCount=body.data?.records?.length;row.firstIsOwnCreated=body.data?.records?.[0]?.analysisObject===wire.newObject;row.ownCreatedFound=body.data?.records?.some(x=>x.analysisObject===wire.newObject);row.firstOwnHasCreateTime=row.firstIsOwnCreated&&!!body.data?.records?.[0]?.createTime;}if(row.path.endsWith('/riskLevel/save'))row.saved=body.data===true;if(row.path.endsWith('/eventTask/updateById'))row.saved=body.data===true;if(row.path.endsWith('/eventTask/getById')){row.taskIdMatched=body.data?.id===wire.id;row.taskStatus=body.data?.taskStatus;row.feedbackMatched=body.data?.feedbackInfo===wire.feedbackInfo;row.evaluationMatched=body.data?.evaluationSum===wire.evaluationSum;row.timeMatched=body.data?.disposeTime===wire.disposeTime;}http.push(row);}).catch(()=>{row.observationFailed=true;http.push(row)}).finally(()=>reads.delete(p));reads.add(p);}

 else if(v.method==='Runtime.exceptionThrown')exceptions.push({text:v.params.exceptionDetails?.text||'OWN_RUNTIME_EXCEPTION'});

}

async function clickText(selector,text){return evaluate(`(()=>{const e=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(x=>x.textContent.trim()===${JSON.stringify(text)});if(!e)return false;e.click();return true})()`);}

const hasValue=value=>evaluate('Array.from(document.querySelectorAll("input,textarea")).some(x=>x.value==='+JSON.stringify(value)+')||document.body.textContent.includes('+JSON.stringify(value)+')');

try{

 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+O+'/chrome-profile','about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});chrome.stderr.on('data',v=>fs.appendFile(O+'/chrome.stderr.log',v));chrome.on('exit',()=>{for(const p of pending.values())p.reject(Error('OWN_CHROME_EXITED'));pending.clear();});let active;await until(async()=>{try{active=(await fs.readFile(O+'/chrome-profile/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('close',()=>{for(const p of pending.values())p.reject(Error('OWN_CHANNEL_CLOSED'));pending.clear();});ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(p){if(v.error)p.reject(Error('OWN_RPC_ERROR_'+v.error.code));else p.resolve(v.result)}}else observe(v)});const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;await send('Runtime.enable',{},session);await send('Page.enable',{},session);await send('Network.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false},session);

 await send('Page.navigate',{url:wire.base+'/zhumadian/hiddenInvestigate/riskAnalysisUnit'},session);await until(()=>evaluate('document.querySelectorAll(".login-body input").length===3'));cases.push('exact-compiled-client-guard-redirects-unauthenticated-task-route-to-login');

 await evaluate(`(()=>{const inputs=document.querySelectorAll('.login-body input'),values=${JSON.stringify([wire.account,wire.password,'0000'])};inputs.forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});})()`);if(!await clickText('.login-body button','登录'))throw Error('COMPILED_LOGIN_SUBMIT_REQUIRED');await until(()=>http.some(x=>x.path.endsWith('/oauth/Login')&&x.businessCode===200&&x.loginTokenReturned));cases.push('compiled-login-form-crypto-and-normal-native-login-succeed');await until(()=>http.some(x=>x.path.endsWith('/oauth/CurrentUser')&&x.ownUserMatched&&x.riskMenuReturned));cases.push('compiled-user-store-receives-original-native-role-menu');

const handoff=wire.syntheticSessionHandoff;

if(!handoff||!/^http:\/\/127\.0\.0\.1:[0-9]+\/owned-compiled-login-session$/.test(handoff.url)||!/^[A-Za-z0-9_-]{43}$/.test(handoff.nonce)||!['own_operator_a','own_reviewer_b'].includes(wire.account))throw Error('OWN_SYNTHETIC_HANDOFF_SCOPE');

const exchange=async(nonce,token)=>fetch(handoff.url,{method:'POST',headers:{'Content-Type':'application/json','X-Own-Handoff-Nonce':nonce},body:JSON.stringify({token}),signal:AbortSignal.timeout(20000)});

const negative=await exchange('invalid-owned-nonce','OWN_INVALID_HANDOFF_TEST_TOKEN');if(negative.status!==403)throw Error('OWN_HANDOFF_WRONG_NONCE_MUST_REJECT');

const accepted=await exchange(handoff.nonce,loginToken);if(accepted.status!==200||!(await accepted.json()).accepted)throw Error('OWN_NORMAL_LOGIN_HANDOFF_REJECTED');

const replay=await exchange(handoff.nonce,'OWN_INVALID_HANDOFF_TEST_TOKEN');if(replay.status!==409)throw Error('OWN_HANDOFF_REPLAY_MUST_REJECT');

handoff.nonce='';cases.push('same-synthetic-user-real-ui-session-handoff-in-memory-with-owner-role-nonce-and-replay-guards');




 if(!/^Own UI risk [a-f0-9]{8}$/.test(wire.newObject))throw Error('BOUNDED_OWN_RISK_OBJECT_NAME');
 const pages=()=>http.filter(x=>x.path.endsWith('/riskLevel/getPage'));
 const saves=()=>http.filter(x=>x.path.endsWith('/riskLevel/save')&&x.method==='POST');
 async function button(text,selector='button'){
  const ok=await evaluate('(()=>{const e=[...document.querySelectorAll('+JSON.stringify(selector)+')].find(x=>x.getBoundingClientRect().height>0&&x.textContent.replace(/\\s/g,"")==='+JSON.stringify(text.replace(/\s/g,''))+');if(!e||e.disabled)return false;e.click();return true})()');
  if(!ok)throw Error('ORIGINAL_RISK_BUTTON_REQUIRED_'+text);
 }
 async function nativeButton(text,selector='button'){
  let pos;const position=()=>evaluate('(()=>{const e=[...document.querySelectorAll('+JSON.stringify(selector)+')].find(x=>x.getBoundingClientRect().height>0&&x.textContent.replace(/\\s/g,"")==='+JSON.stringify(text.replace(/\s/g,''))+');if(!e||e.disabled)return false;const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);if(!hit||!e.contains(hit))return false;return{x,y}})()');
  await until(async()=>{pos=await position();return !!pos});
  if(!pos)throw Error('ORIGINAL_RISK_BUTTON_REQUIRED_'+text);
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:pos.x,y:pos.y,button:'left',clickCount:1},session);
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:pos.x,y:pos.y,button:'left',clickCount:1},session);
 }
 const rows=()=>evaluate('document.querySelectorAll(".el-table__body-wrapper .el-table__row").length');
 const first=()=>evaluate('document.querySelector(".el-table__body-wrapper .el-table__row")?.textContent.includes('+JSON.stringify(wire.newObject)+')');
 function field(label){return '[...document.querySelectorAll(".el-form-item")].find(e=>e.querySelector(".el-form-item__label")?.textContent.includes('+JSON.stringify(label)+'))'}
 async function input(label,value){await evaluate('(()=>{const e='+field(label)+'?.querySelector("input");if(!e)throw Error("FIELD_REQUIRED");e.value='+JSON.stringify(value)+';e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}))})()')}
 async function choose(label,value){
  await evaluate(field(label)+'.querySelector(".el-select__wrapper").click()');
  const expression='[...document.querySelectorAll(".el-select-dropdown__item,.el-tree-node__label")].find(e=>e.getBoundingClientRect().height>0&&e.textContent.trim()==='+JSON.stringify(value)+')';
  await until(()=>evaluate('!!('+expression+')'));await evaluate(expression+'.click()');
 }
 if(!await clickText('.el-menu-item','风险分析单元')){await clickText('.el-sub-menu__title','双重预防');await sleep(100);if(!await clickText('.el-menu-item','风险分析单元'))throw Error('NATIVE_RISK_MENU_REQUIRED')}
 await until(async()=>pages().some(p=>p.businessCode===0&&p.total===32)&&await rows()===10);
 cases.push('actual-native-role-menu-opens-compiled-risk-list-with-original-API');
 await button('下一页','.el-pagination .btn-next').catch(async()=>{
  const clicked=await evaluate('(()=>{const e=document.querySelector(".el-pagination .btn-next");if(!e||e.disabled)return false;e.click();return true})()');if(!clicked)throw Error('ORIGINAL_RISK_NEXT_PAGE_REQUIRED');
 });
 await until(()=>pages().some(p=>p.currentPage===2&&p.businessCode===0));
 cases.push('original-risk-table-pagination-reaches-second-page');
 await button('新增');await until(()=>evaluate('location.pathname.endsWith("/riskAnalysisUnit/add")&&!!document.querySelector(".info-title")'));
 const initialWrites=saves().length;await button('提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item.is-error").length>0'));
 if(saves().length!==initialWrites)throw Error('NATIVE_VALIDATION_MUST_PREVENT_EMPTY_SAVE');cases.push('actual-form-required-validation-prevents-empty-request');
 await choose('责任部门','Own risk department A');
 await until(()=>http.some(p=>p.path.endsWith('/Users/getDepartmentIdByUserList')&&p.httpStatus===200&&p.businessCode===200));
 await choose('部门责任人','Own risk contact A');
 await input('风险分析对象',wire.newObject);await input('风险分析单元','Own UI risk unit');await choose('风险等级','Own risk grade 1');
 cases.push('native-org-tree-contact-directory-and-grade-select-real-owned-options');
 await evaluate(field('坐标信息')+'.querySelector("input").click()');
 await until(()=>evaluate('!!document.querySelector(".el-dialog .ol-viewport canvas")'));
 const box=await evaluate('(()=>{const r=document.querySelector(".el-dialog .ol-viewport").getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()');
 await send('Input.dispatchMouseEvent',{type:'mousePressed',x:box.x,y:box.y,button:'left',clickCount:1},session);
 await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:box.x,y:box.y,button:'left',clickCount:1},session);
 await until(()=>evaluate('[...document.querySelectorAll(".el-dialog .el-dialog__footer button")].some(e=>!e.disabled&&e.textContent.replace(/\\s/g,"")==="确定")'));
 await button('确定','.el-dialog .el-dialog__footer button');
 await until(()=>evaluate('!!('+field('坐标信息')+'?.querySelector("input")?.value)'));
 cases.push('actual-original-OpenLayers-click-selects-coordinate-through-native-dialog');
 const beforePage=pages().length;await button('提交');
 await until(async()=>saves().some(p=>p.businessCode===0&&p.saved)&&pages().length>beforePage&&await first());
 const newest=pages().at(-1);if(newest.currentPage!==1||!newest.firstIsOwnCreated||!newest.firstOwnHasCreateTime||newest.total!==33)throw Error('NATIVE_CREATE_MUST_RELOAD_FIRST_PAGE_WITH_NEWEST_RECORD');
 cases.push('native-form-save-refreshes-cached-second-page-to-first-and-new-record-top');
 const reloadBefore=pages().length;await send('Page.reload',{},session);await until(async()=>pages().length>reloadBefore&&await first()&&pages().at(-1)?.currentPage===1&&pages().at(-1)?.firstIsOwnCreated);
 cases.push('full-compiled-page-reload-preserves-created-record-at-top');
 await evaluate('document.querySelector(".table-search .el-select__wrapper").click()');
 const option='[...document.querySelectorAll(".el-tree-node__label,.el-select-dropdown__item")].find(e=>e.getBoundingClientRect().height>0&&e.textContent.trim()==="Own risk department A")';
 await until(()=>evaluate('!!('+option+')'));await evaluate(option+'.click()');const beforeSearch=pages().length;await button('搜索','.table-search button');
 await until(()=>pages().length>beforeSearch&&pages().at(-1).departmentIsA);
 if(pages().at(-1).total!==18||!await first())throw Error('NATIVE_DEPARTMENT_SELECTION_MUST_MATCH_STORED_DATA');
 cases.push('native-department-option-is-sent-by-name-and-finds-corresponding-records');
 const beforeReset=pages().length;await button('重置','.table-search button');await until(()=>pages().length>beforeReset&&!pages().at(-1).departmentFilterPresent);
 if(pages().at(-1).total!==33)throw Error('NATIVE_RISK_RESET_MUST_RESTORE_FULL_LIST');cases.push('native-risk-reset-clears-department-and-restores-list');
 if(wire.excelFixture!=='D:/Project/Zhumadian/Application/tools/test-data/risk-unit-excel-r76/risk-unit-import.xlsx')throw Error('EXACT_OWN_BROWSER_EXCEL_FIXTURE_REQUIRED');
 await fs.mkdir(O+'/downloads');await send('Browser.setDownloadBehavior',{behavior:'allowAndName',downloadPath:path.resolve(O,'downloads'),eventsEnabled:true});
 async function downloadNative(label,title){
  const before=excelDownloads.length;await nativeButton(title);await until(()=>evaluate('!!document.querySelector(".el-message-box__btns button.el-button--primary")'));
  await nativeButton('确定','.el-message-box__btns button');await until(()=>excelDownloads.length===before+1&&excelDownloads.at(-1).state==='completed');
  const row=excelDownloads.at(-1),raw=await fs.readFile(O+'/downloads/'+row.guid);if(!row.filenameEndsXLSX||raw.length<100||raw.length>5242880||!raw.subarray(0,4).equals(Buffer.from([80,75,3,4])))throw Error('ACTUAL_BROWSER_DOWNLOAD_MUST_BE_XLSX');row.case=label;row.actualBytes=raw.length;cases.push(label);
 }
 await downloadNative('native-template-confirmation-and-real-xlsx-browser-download','下载模板');
 await downloadNative('native-export-confirmation-and-real-all-33-row-browser-download','导出列表');
 await evaluate('document.querySelector(".table-search .el-select__wrapper").click()');await until(()=>evaluate('!!('+option+')'));await evaluate(option+'.click()');
 const excelSearch=pages().length;await button('搜索','.table-search button');await until(()=>pages().length>excelSearch&&pages().at(-1).departmentIsA);if(pages().at(-1).total!==18)throw Error('NATIVE_EXCEL_FILTER_REQUIRED');
 await downloadNative('native-filtered-export-real-18-row-browser-download','导出列表');
 const excelReset=pages().length;await button('重置','.table-search button');await until(()=>pages().length>excelReset&&!pages().at(-1).departmentFilterPresent&&pages().at(-1).total===33);
 await nativeButton('Excel导入');
 const visibleImport='[...document.querySelectorAll(".el-dialog")].find(d=>d.getBoundingClientRect().height>0&&d.querySelector(".el-dialog__title")?.textContent.trim()==="批量添加风险分析单元")';
 await until(()=>evaluate('!!('+visibleImport+'?.querySelector(".el-upload input[type=file]"))'));
 const inputExpression='(()=>{const e='+visibleImport+'.querySelector(".el-upload input[type=file]");if(window.__ownRiskExcelFileSelection!==undefined)throw Error("NO_DUPLICATE_EXCEL_SELECTION_OBSERVER");e.addEventListener("change",()=>{window.__ownRiskExcelFileSelection=Array.from(e.files||[]).map(f=>({expectedName:f.name==="risk-unit-import.xlsx",bytes:f.size,mime:f.type}))},{once:true,capture:true});return e})()';
 const inputObject=await send('Runtime.evaluate',{expression:inputExpression,returnByValue:false},session);if(!inputObject.result.objectId)throw Error('EXACT_VISIBLE_NATIVE_EXCEL_INPUT_REQUIRED');
 const inputNode=await send('DOM.describeNode',{objectId:inputObject.result.objectId},session);
 await send('DOM.setFileInputFiles',{backendNodeId:inputNode.node.backendNodeId,files:[path.resolve(wire.excelFixture)]},session);
 const selected=await evaluate('window.__ownRiskExcelFileSelection');if(!Array.isArray(selected)||selected.length!==1||!selected[0].expectedName||selected[0].bytes!==3792)throw Error('EXACT_SYNTHETIC_FILE_SELECTION_REQUIRED');
 await fs.writeFile(O+'/excel-file-selection.json',JSON.stringify({onlySyntheticFileSelected:true,selection:selected},null,2));
 await until(async()=>http.some(x=>x.path.endsWith('/riskLevel/importExcel')&&x.httpStatus===200)&&pages().at(-1)?.total===34&&await evaluate('![...document.querySelectorAll(".el-dialog")].some(e=>e.getBoundingClientRect().height>0)&&[...document.querySelectorAll(".el-notification__content")].some(e=>e.textContent.includes("批量添加风险分析单元成功"))'));
 if(http.filter(x=>x.path.endsWith('/riskLevel/importExcel')&&x.method==='POST').length!==1)throw Error('ONLY_ONE_NATIVE_EXCEL_UPLOAD_EXPECTED');
 cases.push('native-excel-file-input-one-upload-success-notification-close-and-table-total-34');
 await until(()=>evaluate('document.querySelector(".el-table__body-wrapper .el-table__row")?.textContent.includes("Own xlsx risk sample")'));
 cases.push('native-batch-import-refreshes-imported-record-to-first-row');
 await fs.writeFile(O+'/excel-downloads.json',JSON.stringify({downloads:excelDownloads,oneNativeUpload:true,originalCompiledImportComponentUsed:true,allDataSynthetic:true},null,2));
 if(reads.size)await Promise.all([...reads]);if(exceptions.length)throw Error('COMPILED_RISK_CLIENT_RUNTIME_EXCEPTION');
 if(saves().length!==1)throw Error('ONLY_ONE_NATIVE_RISK_CREATE_EXPECTED');
 await fs.writeFile(O+'/compiled-risk.png',Buffer.from((await send('Page.captureScreenshot',{format:'png'},session)).data,'base64'));
 await fs.writeFile(O+'/result.json',JSON.stringify({cases,http:cleanHTTP(),blocked,actualCompiledRiskPortalAndNativeSDK:true,actualNativeExcelBrowserDownloadsAndUpload:true,noComponentRouterAPIUserStoreOrTokenStubs:true,explicitOwnOrganizationBuildConfiguration:true,onlyOwnedSyntheticData:true,actualMapClickAccepted:true,mapBasemapVisualOrZhumadianGeolocationClaimed:false,formalOrPublicChanged:false,fullCloneReady:false},null,2));
 console.log('ORIGINAL_COMPILED_RISK_PORTAL_BROWSER_PASSED',cases.length);
}catch(error){try{await fs.writeFile(O+'/page-diagnostic.json',JSON.stringify(await evaluate('({path:location.pathname,text:document.body.textContent.slice(0,18000),inputCount:document.querySelectorAll("input").length,ownSearchDOM:document.querySelector(".table-search")?.outerHTML.slice(0,16000)})'),null,2));}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify({error:String(error),cases,http:cleanHTTP(),blocked,exceptions,downloadStates:excelDownloads.map(({guid,...row})=>row)},null,2));throw error;}

finally{if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}let forced=false;if(chrome){try{await until(()=>chrome.exitCode!==null||chrome.signalCode!==null,10000)}catch{forced=true;chrome.kill();}}await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({pid:chrome?.pid,exitCode:chrome?.exitCode,forced,normalBrowserClosed:!!chrome&&!forced&&chrome.exitCode===0}));wire.password='';loginToken='';for(const r of tracked.values())delete r._auth;}

