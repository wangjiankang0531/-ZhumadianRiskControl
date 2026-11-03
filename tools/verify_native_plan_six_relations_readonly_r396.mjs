import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
const root=process.argv[2];if(!/^D:\/Project\/Zhumadian\/work\/event_delivery_consistency_20261030\/full-controller-r163\/r[1-9][0-9]*$/.test(root??''))throw Error('OWN_RESOURCE_ROOT');
let raw='';for await(const b of process.stdin){raw+=b;if(raw.length>16384)throw Error('BOUNDED_OWN_INPUT');}const wire=JSON.parse(raw);raw='';
const started=JSON.parse(await fs.readFile(root+'/controller-started.json','utf8'));if(!wire.syntheticNormalUser||wire.account!=='own_operator_a'||wire.base!=='http://127.0.0.1:'+started.gatewayPort)throw Error('OWN_RESOURCE_SCOPE');
const O=root+'/plan-browser',sleep=ms=>new Promise(r=>setTimeout(r,ms));await fs.mkdir(O);await fs.mkdir(O+'/downloads');
let chrome,ws,session,seq=0,token='',stage='start',failed=null;const pending=new Map(),tracked=new Map(),reads=new Set(),http=[],cases=[],blocked=[],exceptions=[],downloads=[];
 const resourceDeletionSteps=[];
 const boxVisible="Array.from(document.querySelectorAll('.el-message-box')).filter(e=>e.getClientRects().length)";

async function until(fn,ms=40000){const end=Date.now()+ms;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_EXPERT_UI_TIMEOUT_'+stage);await sleep(50);}}
function send(method,params={},sid){return new Promise((resolve,reject)=>{if(ws?.readyState!==WebSocket.OPEN)return reject(Error('OWN_CDP_CLOSED'));const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method));},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}
async function evaluate(expression){const v=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(v.exceptionDetails)throw Error('OWN_EXPERT_EVALUATE');return v.result.value;}
async function click(selector,text){return evaluate(`(()=>{const e=Array.from(document.querySelectorAll(${JSON.stringify(selector)})).find(e=>e.getClientRects().length&&e.textContent.split('').filter(c=>c.trim()).join('')===${JSON.stringify(String(text).split('').filter(c=>c.trim()).join(''))}&&!e.disabled);if(!e)return false;e.click();return true})()`);}
let activeFormTitle=null,optionalJoinConsoleErrors=0,optionalJoinDebuggerErrors=0;const debuggerObservations=[];
const fieldOwner=()=>activeFormTitle?`Array.from(document.querySelectorAll('.el-dialog')).find(d=>d.getClientRects().length&&d.querySelector('.el-dialog__title')?.textContent.trim()===${JSON.stringify(activeFormTitle)})`:'document';
const value=label=>evaluate(`(()=>{const root=${fieldOwner()};const a=Array.from(root?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
async function fill(label,text){if(!await evaluate(`(()=>{const root=${fieldOwner()};const a=Array.from(root?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(text)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return e.value===${JSON.stringify(text)}})()`))throw Error('EXACT_ACTIVE_FORM_FIELD_'+label);}
async function ownAPI(entity,query){if(!['emergencyPlan','emergencyExercise'].includes(entity)||!/^get(?:Page|ById)\?/.test(query))throw Error('OWN_PLAN_READONLY_API');const ua=await evaluate('navigator.userAgent'),r=await fetch(wire.base+'/zhumadian/api/serv/'+entity+'/'+query,{headers:{Authorization:token,'User-Agent':ua}}),v=await r.json();if(r.status!==200||v.code!==0){await fs.writeFile(O+'/readonly-api-diagnostic.json',JSON.stringify({entity,operation:query.split('?')[0],httpStatus:r.status,businessCode:v.code,responseShape:typeof v.data}));throw Error('OWN_PLAN_API_READBACK_'+entity+'_'+r.status+'_'+v.code);}return v.data;}
let holdUpload=false,heldUpload=null,holdExercise=false,heldExercise=null,exercisePaused=0,injectExerciseFalse=false;
let deleteTargetId="",injectPlanDeleteFalse=false,ownPlanDetailURL='';
const exerciseFilterRequests=[];
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
  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyPlan/removeById')){
   if(request.method!=='GET'||!deleteTargetId||u.searchParams.get('id')!==deleteTargetId)throw Error('ONLY_THIS_OWN_DELETE_TARGET_ALLOWED');
   if(injectPlanDeleteFalse){injectPlanDeleteFalse=false;await send('Fetch.fulfillRequest',{requestId:v.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Cache-Control',value:'no-store'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_DELETE_FALSE_INJECTION'})).toString('base64')},v.sessionId);return;}
  }
  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyExercise/getPage'))exerciseFilterRequests.push({legacyDepartmentNonempty:!!u.searchParams.get('department'),canonicalOrganizeDepartmentNonempty:!!u.searchParams.get('organizeDepartment')});
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/emergencyPlan/save','/emergencyPlan/updateById','/emergencyExercise/save','/sys-file/upload'].some(p=>u.pathname.endsWith(p));
  if(disallowed){blocked.push({origin:u?.origin||'invalid',path:u?.pathname||'',method:request.method});await send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},v.sessionId);}else await send('Fetch.continueRequest',{requestId:v.params.requestId},v.sessionId);
 }else if(v.method==='Network.responseReceived'){
  let u;try{u=new URL(v.params.response.url)}catch{};if(u?.origin===wire.base&&u.pathname.includes('/api/'))tracked.set(v.params.requestId,{path:u.pathname,httpStatus:v.params.response.status,session:v.sessionId});
 }else if(v.method==='Network.loadingFinished'&&tracked.has(v.params.requestId)){
  const row=tracked.get(v.params.requestId);const p=send('Network.getResponseBody',{requestId:v.params.requestId},row.session).then(r=>{
   const bytes=r.base64Encoded?Buffer.from(r.body,'base64'):Buffer.from(r.body);let b;try{b=JSON.parse(bytes.toString('utf8'))}catch{row.nonJSON=true;row.bytes=bytes.length;delete row.session;http.push(row);return;}
   if(row.path.endsWith('/emergencyExercise/getPage'))row.exerciseTotal=Number(b.data?.total);
   row.businessCode=b.code;if(row.path.endsWith('/emergencyExercise/save'))row.saved=b.data;if(row.path.endsWith('/oauth/Login')){token=b.data?.token||'';row.normalTokenReturned=!!token;}
   if(row.path.endsWith('/oauth/CurrentUser')){row.ownUserMatched=b.data?.userInfo?.userId===wire.expectedUserId;row.planMenuReturned=JSON.stringify(b.data?.menuList||[]).includes('/emergencyPlans/structured');}
   if(row.path.endsWith('/emergencyPlan/getPage')){row.total=b.data?.total;row.records=Array.isArray(b.data?.records)?b.data.records.length:null;}
   if(['/save','/updateById','/removeById'].some(p=>row.path.endsWith('/emergencyPlan'+p)))row.saved=b.data;
   delete row.session;http.push(row);
  }).catch(()=>{row.observationFailed=true;delete row.session;http.push(row)}).finally(()=>reads.delete(p));reads.add(p);
 }else if(v.method==='Debugger.paused'){
  const description=String(v.params.data?.description||v.params.data?.value||'');const optionalJoin=/join/.test(description)&&/undefined|TypeError/.test(description);
  if(optionalJoin)optionalJoinDebuggerErrors++;
  if(debuggerObservations.length<16)debuggerObservations.push({reason:v.params.reason,optionalJoinObserved:optionalJoin,topFunction:v.params.callFrames?.[0]?.functionName||''});
  await send('Debugger.resume',{},v.sessionId);
 }else if(v.method==='Runtime.consoleAPICalled'){const text=(v.params.args||[]).map(a=>String(a.description||a.value||'')).join(' ');if(/TypeError/.test(text)&&/join|undefined/.test(text))optionalJoinConsoleErrors++;
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
 const relationPrefix='OWN_REL_'+root.split('/').at(-1).toUpperCase();
 const relationKinds=[
  {entity:'materials',label:'应急物资',button:'新增应急物资',filter:'物资名称',nameKey:'materialName',tag:'MAT',ids:'emergencyGoodsManageIdList',list:'emergencyGoodsManageList',payload:{materialType:'1',materialModel:'OWN_REL_MODEL',materialQuantity:'4',unit:'件',storageLocation:'OWN_REL_STORE',person:'OWN_REL_PERSON',phone:'13800000000'}},
  {entity:'firstAidTeams',label:'应急队伍',button:'新增应急队伍',filter:'队伍名称',nameKey:'teamName',tag:'TEAM',ids:'emergencyTeamIdList',list:'emergencyTeamList',payload:{teamType:'OWN_REL_TEAM_TYPE',teamLocation:'OWN_REL_SITE',leaderName:'OWN_REL_LEADER',leaderPhone:'13800000000'}},
  {entity:'emergencyExperts',label:'应急专家',button:'新增应急专家',filter:'专家姓名',nameKey:'expertName',tag:'EXPERT',ids:'emergencyExpertIdList',list:'emergencyExpertList',payload:{expertPhone:'13800000000',expertField:'1',expertEducation:'OWN_DEGREE',expertMajor:'OWN_MAJOR',workingYears:'3'}}
 ];
 const memberKinds=[{title:'副指挥长',list:'emergencyPlanDeputyHeadList',nameKey:'deputyHeadName',fields:['副指挥长','副指挥长电话']},
  {title:'其他成员',list:'emergencyPlanOthermemberList',nameKey:'otherMemberName',fields:['其他成员','其他成员电话']},
  {title:'参与单位',list:'emergencyPlanCompanyList',nameKey:'planCompanyName',fields:['参与单位','单位负责人','单位负责人电话']}];
 async function resourceRequest(kind,operation,payload){
  if(!relationKinds.includes(kind)||!['save','getPage'].includes(operation))throw Error('ONLY_THIS_OWN_RESOURCE_KIND');
  const ua=await evaluate('navigator.userAgent');let url=wire.base+'/zhumadian/api/serv/'+kind.entity+'/'+operation;
  const options={headers:{Authorization:token,'User-Agent':ua},signal:AbortSignal.timeout(15000)};
  if(operation==='save'){
   if(![kind.ownA,kind.ownB].includes(payload[kind.nameKey])||Object.keys(payload).some(k=>!Object.keys({...kind.payload,[kind.nameKey]:''}).includes(k)))throw Error('ONLY_THIS_OWN_RESOURCE_BODY');
   options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(kind.entity==='firstAidTeams'?{teams:payload,members:[]}:payload);
  }else url+='?current=1&size=5&'+kind.nameKey+'='+encodeURIComponent(payload);
  const response=await fetch(url,options),reply=await response.json();if(response.status!==200||reply.code!==0)throw Error('OWN_ORIGINAL_RESOURCE_API_'+kind.entity+'_'+response.status+'_'+reply.code);
  return reply.data;
 }
 stage='create-original-typed-owned-resource-fixtures';
 for(const kind of relationKinds){
  kind.ownA=relationPrefix+'_'+kind.tag+'_A';kind.ownB=relationPrefix+'_'+kind.tag+'_B';kind.rows=[];
  for(const ownName of [kind.ownA,kind.ownB]){
   if(await resourceRequest(kind,'save',{...kind.payload,[kind.nameKey]:ownName})!==true)throw Error('OWN_RESOURCE_SAVE_NOT_TRUE');
   const page=await resourceRequest(kind,'getPage',ownName);
   if(Number(page.total)!==1||page.records[0][kind.nameKey]!==ownName||typeof page.records[0].id!=='string')throw Error('OWN_UNIQUE_RESOURCE_READBACK');
   kind.rows.push(page.records[0]);
  }
 }
 cases.push({case:'three-original-resource-save-APIs-create-six-owned-normal-role-fixtures',passed:true});
 const ownMemberValue=(kind,index,field,edited=false)=>field.includes('电话')?'13800000000':relationPrefix+'_'+kind.nameKey+'_'+index+(edited?'_EDIT':'');
 function memberRoot(title){return `Array.from(document.querySelectorAll('.form-list-item')).find(e=>e.getClientRects().length&&e.querySelector('.item-title')?.textContent.trim()===${JSON.stringify(title)})`;}
 async function memberFill(kind,index,edited=false){
  for(const field of kind.fields){const val=ownMemberValue(kind,index,field,edited);
   if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},row=g?.querySelectorAll('.item-form')[${index}],f=Array.from(row?.querySelectorAll('.el-form-item')||[]).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(field)}),input=f?.querySelector('input');if(!input||input.disabled||input.readOnly)return false;input.value=${JSON.stringify(val)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return input.value===${JSON.stringify(val)}})()`))throw Error('OWN_MEMBER_FIELD_'+kind.title+'_'+index+'_'+field);
  }
 }
 async function memberButton(kind,text){if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},b=Array.from(g?.querySelectorAll('.item-header button')||[]).find(e=>e.textContent.trim()===${JSON.stringify(text)});b?.click();return!!b})()`))throw Error('OWN_MEMBER_BUTTON_'+kind.title);}
 const pane=()=>`Array.from(document.querySelectorAll('.el-tab-pane')).find(e=>e.getClientRects().length&&e.querySelector('.el-table'))`;
 const picker=()=>`Array.from(document.querySelectorAll('.el-dialog')).find(e=>e.getClientRects().length&&e.querySelector('.el-dialog__title')?.textContent.trim()==='新增')`;
 async function resourceTab(kind){if(!await click('.el-tabs__item',kind.label))throw Error('OWN_RESOURCE_TAB_'+kind.entity);await until(()=>evaluate(`!!(${pane()})`));}
 async function selectedResourceCount(){return evaluate(`(${pane()})?.querySelectorAll('.el-table__body-wrapper tbody tr').length??-1`);}
 async function chooseResource(kind,which,expectedCount){
  await resourceTab(kind);if(!await click('button',kind.button))throw Error('OWN_RESOURCE_OPEN_'+kind.entity);
  await until(()=>evaluate(`!!(${picker()})?.querySelector('.table-search')`));
  await until(()=>evaluate(`!!(${picker()})?.querySelector('.el-dialog__footer button:last-child')?.disabled`));
  const ownName=which==='A'?kind.ownA:kind.ownB;
  if(!await evaluate(`(()=>{const d=${picker()},f=Array.from(d?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(kind.filter)}),e=f?.querySelector('input');if(!e)return false;e.value=${JSON.stringify(ownName)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));const b=Array.from(d.querySelectorAll('.table-search button')).find(e=>e.textContent.trim()==='搜索');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_FILTER_'+kind.entity);
  await until(()=>evaluate(`Array.from((${picker()})?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(e=>e.getClientRects().length).length===1&&Array.from((${picker()})?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).some(e=>e.textContent.includes(${JSON.stringify(ownName)}))`));
  if(!await evaluate(`(()=>{const d=${picker()},r=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).find(e=>e.textContent.includes(${JSON.stringify(ownName)})),b=r?.querySelector('.el-radio');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_RADIO_'+kind.entity);
  await until(()=>evaluate(`!(${picker()})?.querySelector('.el-dialog__footer button:last-child')?.disabled`));
  if(!await evaluate(`(()=>{const d=${picker()},b=Array.from(d?.querySelectorAll('.el-dialog__footer button')||[]).find(e=>e.textContent.trim()==='确定');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_CONFIRM_'+kind.entity);
  await until(()=>evaluate(`!(${picker()})`));await until(async()=>await selectedResourceCount()===expectedCount);
 }

 async function removeResourceA(kind){
  stage='resource-'+kind.entity+'-enter-tab';await resourceTab(kind);
  await until(()=>evaluate(`(${boxVisible}).length===0`));
  async function remove(action){
   stage='resource-'+kind.entity+'-open-'+action;
   if(!await evaluate(`(()=>{const p=${pane()},r=Array.from(p?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).find(e=>e.textContent.includes(${JSON.stringify(kind.ownA)})),b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_REMOVE_BUTTON');
   await until(()=>evaluate(`(${boxVisible}).length===1&&(${boxVisible})[0].textContent.includes('确认删除')`));
   resourceDeletionSteps.push({kind:kind.entity,phase:action+'-opened'});
  }
  async function action(text){
   if(!await evaluate(`(()=>{const boxes=${boxVisible};if(boxes.length!==1)return false;const b=Array.from(boxes[0].querySelectorAll('.el-message-box__btns button')).find(e=>e.textContent.trim()===${JSON.stringify(text)}&&!e.disabled);b?.click();return!!b})()`))throw Error('OWN_EXACT_ONE_RESOURCE_CONFIRMATION_BUTTON');
   await until(()=>evaluate(`(${boxVisible}).length===0`));
  }
  await remove('cancel');stage='resource-'+kind.entity+'-cancel-and-close';await action('取消');
  await until(async()=>await selectedResourceCount()===2);resourceDeletionSteps.push({kind:kind.entity,phase:'cancel-kept-two-and-dialog-closed'});
  await remove('confirm');stage='resource-'+kind.entity+'-confirm-and-close';await action('确定');
  await until(async()=>await selectedResourceCount()===1);
  if(!await evaluate(`(${pane()})?.textContent.includes(${JSON.stringify(kind.ownB)})===true`))throw Error('OWN_RESOURCE_REMOVE_RETAIN_B');
  resourceDeletionSteps.push({kind:kind.entity,phase:'confirm-kept-B-and-dialog-closed'});
 }
 function checkRelations(record,edited){
  for(const kind of relationKinds){const expected=(edited?[kind.rows[1]]:kind.rows).map(r=>String(r.id)).sort();
   if(JSON.stringify((record[kind.ids]||[]).map(String).sort())!==JSON.stringify(expected)||JSON.stringify((record[kind.list]||[]).map(r=>String(r.id)).sort())!==JSON.stringify(expected))throw Error('OWN_RESOURCE_CANONICAL_IDS_AND_DETAILS_'+kind.entity);
   for(const row of record[kind.list])if(!kind.rows.some(r=>r.id===row.id&&r[kind.nameKey]===row[kind.nameKey]))throw Error('OWN_RESOURCE_DETAIL_METADATA_'+kind.entity);
  }
  for(const kind of memberKinds){const rows=record[kind.list];if(!Array.isArray(rows)||rows.length!==(edited?1:2))throw Error('OWN_MEMBER_COUNT_'+kind.title);
   const expected=Array.from({length:edited?1:2},(_,i)=>ownMemberValue(kind,i,kind.fields[0],edited)).sort();if(JSON.stringify(rows.map(r=>r[kind.nameKey]).sort())!==JSON.stringify(expected))throw Error('OWN_MEMBER_VALUES_'+kind.title);
  }
 }

 let writes=count('save');stage='required-plan-validation';if(!await click('.table-box button','新增'))throw Error('OWN_PLAN_ADD');
 await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
 await click('button','提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>=1'));
 if(count('save')!==writes)throw Error('EMPTY_PLAN_WRITTEN');cases.push({case:'plan-required-fields-block-write',passed:true});
 await fill('应急预案名称',name);await fill('指挥长','OWN_COMMANDER_R222');await fill('指挥长电话','invalid');
 if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('ORIGINAL_PLAN_FILINGS_RADIO');
 await click('button','提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>0'));
 if(count('save')!==writes)throw Error('INVALID_PLAN_PHONE_WRITTEN');cases.push({case:'plan-invalid-phone-keeps-editor-no-save',passed:true});

 await fill('指挥长电话','13800000000');await fill('处置措施','OWN_PLAN_MEASURES_R222');
 stage='fill-original-six-plan-relation-groups';
 for(const kind of memberKinds){await memberFill(kind,0);await memberButton(kind,'新增'+kind.title);await until(()=>evaluate(`(${memberRoot(kind.title)})?.querySelectorAll('.item-form').length===2`));await memberFill(kind,1);}
 cases.push({case:'original-three-member-groups-two-real-form-rows-each-filled',passed:true});
 for(const kind of relationKinds){await chooseResource(kind,'A',1);await chooseResource(kind,'B',2);await chooseResource(kind,'A',2);cases.push({case:'original-'+kind.entity+'-picker-empty-guard-select-two-and-deduplicate',passed:true});}
 stage='actual-plan-create';

 await click('button','提交');await until(()=>count('save')>writes);let saved=http.filter(x=>x.path.endsWith('/emergencyPlan/save')).at(-1);
 if(saved.businessCode!==0||saved.saved!==true)throw Error('PLAN_SAVE_NOT_CONFIRMED');
 await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
 let page=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(name));
 if(Number(page.total)!==1)throw Error('OWN_PLAN_NOT_PERSISTED');const id=page.records[0].id;
 let detail=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));
 if(detail.emergencyPlanName!==name||detail.commanderPhone!=='13800000000'||String(detail.isFilings)!=='0'||detail.disposalMeasures!=='OWN_PLAN_MEASURES_R222')throw Error('PLAN_VALUES_LOST');
 await fs.writeFile(root+'/plan-context.private.json',JSON.stringify({id,name,ownedSyntheticOnly:true}));
 cases.push({case:'plan-native-create-original-controller-and-normal-role-detail-values',passed:true});
 checkRelations(detail,false);cases.push({case:'all-six-plan-relation-groups-normal-save-and-original-detail-readback',passed:true});
 async function filterOwn(){
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  if(await value('应急预案名称')===null)await click('.table-search button','更多');await fill('应急预案名称',name);
  const n=count('getPage');await click('.table-search button','搜索');await until(()=>count('getPage')>n);
  await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(e=>e.textContent.includes(${JSON.stringify(name)}))`));
 }
 await filterOwn();stage='plan-edit-and-readback';await click('.el-table__body-wrapper button','编辑');
 await until(async()=>await value('应急预案名称')===name);await fill('处置措施','OWN_PLAN_REVISED_R222');
 stage='edit-all-six-plan-relation-groups';
 for(const kind of memberKinds){await memberButton(kind,'删除');await until(()=>evaluate(`(${memberRoot(kind.title)})?.querySelectorAll('.item-form').length===1`));await memberFill(kind,0,true);}
 for(const kind of relationKinds)await removeResourceA(kind);

 let edits=count('updateById');await click('button','提交');await until(()=>count('updateById')>edits);
 if(http.filter(x=>x.path.endsWith('/emergencyPlan/updateById')).at(-1).saved!==true)throw Error('PLAN_EDIT_NOT_CONFIRMED');
 await filterOwn();detail=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));if(detail.disposalMeasures!=='OWN_PLAN_REVISED_R222')throw Error('PLAN_EDIT_NOT_PERSISTED');
 checkRelations(detail,true);cases.push({case:'all-six-plan-relation-groups-edit-replace-and-canonical-ID-readback',passed:true});
 await click('.el-table__body-wrapper button','详情');await until(async()=>await value('应急预案名称')===name);
 ownPlanDetailURL=await evaluate('location.href');if(!ownPlanDetailURL.startsWith(wire.base+'/zhumadian/emergency/'))throw Error('OWN_REAL_DETAIL_URL_REQUIRED');
 if(await value('处置措施')!=='OWN_PLAN_REVISED_R222'||!await evaluate('Array.from(document.querySelectorAll(".ele-page input,.ele-page textarea")).filter(e=>e.getClientRects().length).every(e=>e.disabled||e.readOnly)'))throw Error('PLAN_DETAIL_NOT_READONLY_OR_REVISED');


 stage='readonly-all-six-relation-values';
 for(const kind of memberKinds){
  for(const field of kind.fields){const expected=ownMemberValue(kind,0,field,true);
   if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},rows=g?.querySelectorAll('.item-form');if(rows?.length!==1)return false;const f=Array.from(rows[0].querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(field)}),input=f?.querySelector('input,textarea');return!!input&&input.disabled&&input.value===${JSON.stringify(expected)}})()`))throw Error('OWN_READONLY_DISABLED_INPUT_VALUE_'+kind.title+'_'+field);
  }
 }

 for(const kind of relationKinds){await resourceTab(kind);if(await selectedResourceCount()!==1||!await evaluate(`(${pane()})?.textContent.includes(${JSON.stringify(kind.ownB)})===true&&!Array.from((${pane()})?.querySelectorAll('button')||[]).some(e=>e.getClientRects().length&&/新增|删除/.test(e.textContent))`))throw Error('OWN_READONLY_RESOURCE_'+kind.entity);}
 cases.push({case:'all-six-plan-relation-groups-actual-readonly-detail-renders-current-values',passed:true});
 cases.push({case:'plan-edit-reopen-detail-readonly-and-original-identity-kept',passed:true});await click('button','返回');await filterOwn();

 await click('.el-table__body-wrapper button','演练记录');
 const dialogTitle=t=>`Array.from(document.querySelectorAll('.el-dialog')).find(d=>d.getClientRects().length&&d.querySelector('.el-dialog__title')?.textContent.trim()===${JSON.stringify(t)})`;
 async function modalClick(title,selector,text){return evaluate(`(()=>{const d=${dialogTitle(title)},e=Array.from(d?.querySelectorAll(${JSON.stringify(selector)})||[]).find(e=>e.getClientRects().length&&e.textContent.replace(/\\s/g,'')===${JSON.stringify(String(text).replace(/\s/g,''))}&&!e.disabled);e?.click();return!!e})()`);}
 await until(()=>evaluate(`!!(${dialogTitle('演练记录')})`));
 if(!await modalClick('演练记录','button','新增'))throw Error('OWN_EXERCISE_ADD');
 await until(()=>evaluate(`!!(${dialogTitle('新增演练记录')})`));activeFormTitle='新增演练记录';stage='optional-participants-baseline-reproduction';
 await fill('演练地点',exerciseName+'_EMPTY');await fill('演练内容及过程描述','OWN_EMPTY_PARTICIPANTS_ALLOWED');
 const exerciseCount=()=>http.filter(x=>x.path.endsWith('/emergencyExercise/save')).length;
 if(await value('演练地点')!==exerciseName+'_EMPTY')throw Error('ACTIVE_EXERCISE_LOCATION_REQUIRED_BEFORE_SUBMIT');
 if(wire.baseline){await send('Debugger.enable',{},session);await send('Debugger.setPauseOnExceptions',{state:'all'},session);}
 const beforeEmpty=exerciseCount();
 const submitObservation=await evaluate(`(()=>{const d=${dialogTitle('新增演练记录')};return{dialogFound:!!d,footers:Array.from(d?.querySelectorAll('.el-dialog__footer button')||[]).map(e=>({text:e.textContent.trim(),disabled:e.disabled,visible:!!e.getClientRects().length})),errors:Array.from(d?.querySelectorAll('.el-form-item__error')||[]).map(e=>e.textContent.trim())}})()`);
 await fs.writeFile(O+'/before-exercise-submit.json',JSON.stringify(submitObservation,null,2));
 if(!await modalClick('新增演练记录','.el-dialog__footer button','确定'))throw Error('EXACT_VISIBLE_EXERCISE_SUBMIT_BUTTON_NOT_CLICKED');
 if(wire.baseline){
  await until(()=>optionalJoinConsoleErrors>0||optionalJoinDebuggerErrors>0||exceptions.some(x=>/join|undefined/.test(x.description||'')));
  if(exerciseCount()!==beforeEmpty||await value('演练地点')!==exerciseName+'_EMPTY')throw Error('EXPECTED_BASELINE_EMPTY_PARTICIPANTS_REPRO_NOT_OBSERVED');
  await fs.writeFile(O+'/baseline-reproduction.json',JSON.stringify({reproduced:true,normalUserActualCompiledPage:true,optionalPersonSelectionLeftEmpty:true,actualUndefinedJoinErrorObservedViaRuntimeOrConsole:optionalJoinConsoleErrors>0||exceptions.some(x=>/join|undefined/.test(x.description||'')),actualUndefinedJoinErrorObservedViaDebugger:optionalJoinDebuggerErrors>0,activeChildDialogLocationFilled:true,noExerciseSaveRequestSent:true,productChanged:false},null,2));
  cases.push({case:'baseline-real-normal-page-optional-persons-trigger-undefined-join-before-save',passed:true});
  await send('Debugger.setPauseOnExceptions',{state:'none'},session);await fs.writeFile(O+'/debugger-observations.json',JSON.stringify(debuggerObservations,null,2));
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
  await send('DOM.getDocument',{depth:-1},session);const inputObject=await send('Runtime.evaluate',{expression:`(${dialogTitle('新增演练记录')})?.querySelector('input[type=file]')`,returnByValue:false},session);if(inputObject.exceptionDetails||!inputObject.result.objectId)throw Error('EXACT_EXERCISE_MODAL_FILE_INPUT_REQUIRED');const input=await send('DOM.requestNode',{objectId:inputObject.result.objectId},session);
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
  if(!row)throw Error('EXERCISE_LIST_VIEW_BUTTON');activeFormTitle='演练记录详情';await until(()=>evaluate(`!!(${dialogTitle('演练记录详情')})`));
  await until(async()=>await value('演练地点')===exerciseName+'_FILE');
  const currentLink=await evaluate(`(()=>{const d=${dialogTitle('演练记录详情')},a=d?.querySelector('a[href]');if(!a)return null;a.scrollIntoView({block:'center'});const r=a.getBoundingClientRect();return{href:a.href,x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  if(!currentLink||new URL(currentLink.href).origin!==wire.base)throw Error('ORIGINAL_OWN_FILE_DETAIL_LINK');
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:currentLink.x,y:currentLink.y,button:'left',clickCount:1},session);await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:currentLink.x,y:currentLink.y,button:'left',clickCount:1},session);
  await until(()=>downloads.some(x=>x.state==='completed'));const downloaded=await fs.readdir(O+'/downloads');if(downloaded.length!==1||!(await fs.readFile(O+'/downloads/'+downloaded[0])).equals(png))throw Error('EXERCISE_NATIVE_ATTACHMENT_DISK_BYTES');
  cases.push({case:'native-exercise-list-view-readonly-details-and-actual-anchor-disk-download-identical',passed:true});


  stage='exercise-organize-department-filter-baseline-or-fixed';
  if(!await evaluate(`(()=>{const d=${dialogTitle('演练记录详情')},b=d?.querySelector('.el-dialog__headerbtn');b?.click();return!!b})()`))throw Error('EXERCISE_DETAIL_CLOSE_FOR_SEARCH');
  await until(()=>evaluate(`!(${dialogTitle('演练记录详情')})`));
  activeFormTitle='演练记录';
  const unfiltered=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  if(Number(unfiltered.total)!==2||!unfiltered.records.some(r=>r.id===exercise.id&&r.organizeDepartment)||!unfiltered.records.some(r=>r.id!==exercise.id&&!r.organizeDepartment))throw Error('TWO_OWN_DEPARTMENT_DISTINCT_EXERCISES_REQUIRED');
  const searchDepartmentVisible=()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')};return Array.from(d?.querySelectorAll('.table-search .el-form-item')||[]).some(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()==='组织部门')})()`);
  if(!await searchDepartmentVisible()){
   if(!await modalClick('演练记录','.table-search button','更多'))throw Error('EXERCISE_SEARCH_MORE');
   await until(searchDepartmentVisible);
  }
  if(!await evaluate(`(()=>{const d=${dialogTitle('演练记录')},f=Array.from(d.querySelectorAll('.table-search .el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()==='组织部门');const e=f?.querySelector('.el-select__wrapper,.el-input__wrapper');e?.click();return!!e})()`))throw Error('EXERCISE_SEARCH_DEPARTMENT_FIELD');
  await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-tree-node__content')).some(e=>e.getClientRects().length&&e.textContent.trim()===${JSON.stringify(department)})`));
  if(!await click('.el-tree-node__content',department))throw Error('EXERCISE_SEARCH_DEPARTMENT_CHOICE');
  const beforeFilter=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length;
  if(!await modalClick('演练记录','.table-search button','搜索'))throw Error('EXERCISE_SEARCH_BUTTON');
  await until(()=>http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length>beforeFilter);
  const filtered=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).at(-1),query=exerciseFilterRequests.at(-1);
  await fs.writeFile(O+'/department-filter-observed-before-assert.json',JSON.stringify({httpStatus:filtered.httpStatus,businessCode:filtered.businessCode,filteredRows:filtered.exerciseTotal,requestShape:query},null,2));
  if(wire.exerciseDepartmentBaseline){
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==2||!query.legacyDepartmentNonempty||query.canonicalOrganizeDepartmentNonempty)throw Error('EXPECTED_LEGACY_DEPARTMENT_FILTER_REPRO_NOT_OBSERVED');
  }else{
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==1||!query.canonicalOrganizeDepartmentNonempty)throw Error('CORRECT_ORGANIZE_DEPARTMENT_FILTER_NOT_OBSERVED');
  }
  await fs.writeFile(O+'/department-filter-evidence.json',JSON.stringify({reproducedLegacyKeyIgnored:!!wire.exerciseDepartmentBaseline,unfilteredRows:2,filteredRows:filtered.exerciseTotal,requestShape:query,actualOriginalBackendAndCompiledPage:true,onlyOwnSyntheticRecords:true,businessRowsChangedByFilter:false},null,2));
  cases.push({case:wire.exerciseDepartmentBaseline?'native-exercise-department-legacy-key-reproduces-two-unfiltered-rows':'native-exercise-organize-department-filters-two-records-to-one',passed:true,defectReproduced:!!wire.exerciseDepartmentBaseline});

  await until(()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')},rows=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(r=>r.getClientRects().length);return rows.length===1&&rows[0].textContent.includes(${JSON.stringify(exerciseName+'_FILE')})&&!rows[0].textContent.includes(${JSON.stringify(exerciseName+'_EMPTY')})})()`));
  stage='exercise-organize-department-reset-restores-parent-scoped-two-records';
  const beforeReset=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length;
  if(!await modalClick('演练记录','.table-search button','重置'))throw Error('EXERCISE_FILTER_RESET_BUTTON');
  await until(()=>http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length>beforeReset);
  const reset=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).at(-1),resetQuery=exerciseFilterRequests.at(-1);
  if(reset.httpStatus!==200||reset.businessCode!==0||reset.exerciseTotal!==2||resetQuery.canonicalOrganizeDepartmentNonempty)throw Error('EXERCISE_RESET_DID_NOT_CLEAR_CANONICAL_FILTER');
  await until(()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')},rows=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(r=>r.getClientRects().length);return rows.length===2&&rows.some(r=>r.textContent.includes(${JSON.stringify(exerciseName+'_FILE')}))&&rows.some(r=>r.textContent.includes(${JSON.stringify(exerciseName+'_EMPTY')}))})()`));
  await fs.writeFile(O+'/department-filter-reset-evidence.json',JSON.stringify({passed:true,filteredRows:1,resetRows:2,requestShape:query,resetRequestShape:resetQuery,actualVisibleRowsMatchedBothResponses:true,actualOriginalBackendAndCompiledPage:true,onlyOwnSyntheticRecords:true,businessRowsChangedByFilterOrReset:false},null,2));
  cases.push({case:'native-exercise-department-reset-restores-both-parent-scoped-records',passed:true});
  activeFormTitle=null;

  stage='close-own-exercise-details-and-create-delete-target';
  for(const title of ['演练记录']){
   if(!await evaluate(`(()=>{const d=${dialogTitle(title)},b=d?.querySelector('.el-dialog__headerbtn');b?.click();return!!b})()`))throw Error('OWN_MODAL_CLOSE_'+title);
   await until(()=>evaluate(`!(${dialogTitle(title)})`));
  }
  activeFormTitle=null;
  const deletionName=name+'_DELETE_ONLY';writes=count('save');
  if(!await click('.table-box button','新增'))throw Error('DELETE_TARGET_ADD');
  await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
  await fill('应急预案名称',deletionName);await fill('指挥长','OWN_DELETE_COMMANDER');await fill('指挥长电话','13800000000');
  if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('DELETE_TARGET_FILINGS');
  await fill('处置措施','OWN_DELETE_ONLY_NO_CHILDREN');await click('button','提交');await until(()=>count('save')>writes);
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  const deletePage=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName));
  if(Number(deletePage.total)!==1||deletePage.records[0].id===id)throw Error('DISTINCT_OWN_DELETE_TARGET_REQUIRED');
  deleteTargetId=String(deletePage.records[0].id);
  const ownTargetExercises=await ownAPI('emergencyExercise','getPage?current=1&size=5&emergencyPlanId='+encodeURIComponent(deleteTargetId));
  if(Number(ownTargetExercises.total)!==0)throw Error('DELETE_TARGET_MUST_HAVE_NO_CHILDREN');
  if(await value('应急预案名称')===null)await click('.table-search button','更多');await fill('应急预案名称',deletionName);
  let searches=count('getPage');await click('.table-search button','搜索');await until(()=>count('getPage')>searches);
  async function deleteOwnTarget(){
   if(!await evaluate(`(()=>{const r=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(deletionName)}));const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_DELETE_ROW_BUTTON');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("是否删除"))'));
  }
  stage='native-delete-cancel-does-not-send-request';
  const beforeCancel=count('removeById');await deleteOwnTarget();
  if(!await click('.el-message-box__btns button','取消'))throw Error('OWN_DELETE_CANCEL');
  await until(()=>evaluate('!Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length)'));await sleep(200);
  if(count('removeById')!==beforeCancel)throw Error('CANCEL_SENT_DELETE');
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==1)throw Error('CANCEL_REMOVED_PLAN');
  cases.push({case:'native-plan-delete-cancel-no-request-record-kept',passed:true});
  stage='native-delete-false-response-keeps-record-no-success';injectPlanDeleteFalse=true;
  await deleteOwnTarget();if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_DELETE_FALSE_CONFIRM');
  await until(()=>count('removeById')===beforeCancel+1);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message--error")).some(e=>e.getClientRects().length&&e.textContent.includes("删除未完成"))'));
  if(http.filter(x=>x.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==false)throw Error('FALSE_DELETE_NOT_OBSERVED');
  if(await evaluate('Array.from(document.querySelectorAll(".el-message--success")).some(e=>e.getClientRects().length&&e.textContent.includes("删除成功"))'))throw Error('FALSE_DELETE_REPORTED_SUCCESS');
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==1)throw Error('INJECTED_FALSE_DELETE_CHANGED_SERVER');
  cases.push({case:'native-plan-delete-browser-false-no-server-write-keeps-record-and-reports-failure',passed:true,realSQLFailureClaimed:false});
  stage='native-delete-real-confirm-once-and-control-record-retained';
  const beforeReal=count('removeById');await deleteOwnTarget();if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_DELETE_REAL_CONFIRM');
  await until(()=>count('removeById')===beforeReal+1);
  if(http.filter(x=>x.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==true)throw Error('REAL_DELETE_NOT_CONFIRMED');
  await until(()=>evaluate(`!Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(deletionName)}))`));
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==0)throw Error('REAL_DELETE_NOT_PERSISTED');
  const control=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));
  const controlExercise=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  if(control.emergencyPlanName!==name||control.disposalMeasures!=='OWN_PLAN_REVISED_R222'||controlExercise.emergencyPlanId!==id||controlExercise.fileList?.length!==1||controlExercise.participants?.split(',').length!==2)throw Error('UNRELATED_CONTROL_PLAN_EXERCISE_OR_ATTACHMENT_CHANGED');
  cases.push({case:'native-plan-delete-real-confirm-once-parent-disappears-unrelated-plan-exercise-and-file-kept',passed:true});

  stage='create-unrelated-control-before-parent-with-exercises-delete';
  const keepName=name+'_KEEP_AFTER_PARENT_DELETE';writes=count('save');
  if(!await click('.table-box button','新增'))throw Error('PARENT_DELETE_CONTROL_ADD');
  await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
  await fill('应急预案名称',keepName);await fill('指挥长','OWN_PARENT_DELETE_CONTROL');await fill('指挥长电话','13800000000');
  if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('PARENT_DELETE_CONTROL_FILINGS');
  await fill('处置措施','OWN_UNRELATED_KEEP_AFTER_PARENT_DELETE');await click('button','提交');await until(()=>count('save')>writes);
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  const keepPage=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(keepName));
  if(Number(keepPage.total)!==1||String(keepPage.records[0].id)===String(id))throw Error('DISTINCT_OWN_KEEP_CONTROL_REQUIRED');
  const keepId=String(keepPage.records[0].id),keepBefore=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(keepId));
  const exercisesBefore=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  if(Number(exercisesBefore.total)!==2||!exercisesBefore.records.some(r=>r.id===exercise.id))throw Error('TWO_OWN_EXERCISES_BEFORE_PARENT_DELETE_REQUIRED');
  const fileExerciseBefore=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  if(fileExerciseBefore.fileList?.length!==1||fileExerciseBefore.participants?.split(',').length!==2)throw Error('CHILD_FILE_AND_PEOPLE_BEFORE_PARENT_DELETE_REQUIRED');
  stage='actual-original-parent-delete-with-two-existing-exercises';
  await filterOwn();deleteTargetId=String(id);
  if(!await evaluate(`(()=>{const r=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(name)})&&!e.textContent.includes(${JSON.stringify(keepName)}));const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_PARENT_WITH_EXERCISES_DELETE_BUTTON');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("是否删除"))'));
  const parentDeleteBefore=count('removeById');
  if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_PARENT_WITH_EXERCISES_DELETE_CONFIRM');
  await until(()=>count('removeById')===parentDeleteBefore+1);
  if(http.filter(r=>r.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==true)throw Error('PARENT_DELETE_DID_NOT_COMPLETE');
  const removedParent=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(name));
  if(removedParent.records.some(r=>String(r.id)===String(id)))throw Error('PARENT_STILL_IN_ORIGINAL_LIST');
  if(await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id))!==null)throw Error('DELETED_PARENT_DETAILS_NOT_NULL');
  const exercisesAfter=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  const fileExerciseAfter=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  const keepAfter=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(keepId));
  if(Number(exercisesAfter.total)!==2||JSON.stringify(exercisesAfter.records.map(r=>String(r.id)).sort())!==JSON.stringify(exercisesBefore.records.map(r=>String(r.id)).sort()))throw Error('ORIGINAL_CHILD_EXERCISE_RETENTION_CHANGED');
  if(JSON.stringify(fileExerciseAfter)!==JSON.stringify(fileExerciseBefore)||JSON.stringify(keepAfter)!==JSON.stringify(keepBefore))throw Error('CHILD_DETAILS_OR_UNRELATED_PLAN_CHANGED');
  await until(()=>evaluate(`!Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(r=>r.getClientRects().length&&r.textContent.includes(${JSON.stringify(name)})&&!r.textContent.includes(${JSON.stringify(keepName)}))`));
  cases.push({case:'native-parent-with-two-exercises-delete-retains-original-child-details-and-unrelated-plan',passed:true,originalBehaviorCharacterization:true,childCascadeDeletionClaimed:false});
  stage='exercise-attachment-object-still-readable-after-parent-delete';
  const childObject=new URL(currentLink.href);
  if(childObject.origin!==wire.base)throw Error('OWN_CHILD_ATTACHMENT_ORIGIN_REQUIRED');
  const objectResponse=await fetch(childObject.href,{headers:{Authorization:token,'User-Agent':await evaluate('navigator.userAgent')},redirect:'error',signal:AbortSignal.timeout(15000)});
  if(objectResponse.status!==200)throw Error('OWN_CHILD_OBJECT_NOT_READABLE_AFTER_PARENT_DELETE');
  const objectBytes=Buffer.from(await objectResponse.arrayBuffer());
  if(!objectBytes.equals(png))throw Error('OWN_CHILD_OBJECT_BYTES_CHANGED_AFTER_PARENT_DELETE');
  cases.push({case:'native-child-attachment-metadata-and-real-object-bytes-kept-after-parent-delete',passed:true,objectStoreCascadeDeletionClaimed:false});
  await fs.writeFile(O+'/parent-delete-with-exercises-evidence.json',JSON.stringify({passed:true,parentDeleteRequests:1,parentAbsentFromListAndDetails:true,childExercisesBefore:2,childExercisesAfter:2,childDetailsPeopleAndFileMetadataUnchanged:true,realChildAttachmentHTTP:objectResponse.status,realChildAttachmentBytesIdentical:true,unrelatedOwnPlanExactDetailsUnchanged:true,actualOriginalServiceAndNormalRoleUI:true,onlyOwnSyntheticRecords:true,originalBehaviorCharacterizedNotNewCascadeRule:true,allSixResourceRelationsPopulatedOrVerifiedByThisCase:false},null,2));



  stage='deleted-parent-old-detail-URL-normal-navigation';
  const oldDetailReads=()=>http.filter(r=>r.path.endsWith('/emergencyPlan/getById')).length;
  let detailReadsBefore=oldDetailReads();
  await send('Page.navigate',{url:ownPlanDetailURL},session);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  await until(()=>oldDetailReads()>detailReadsBefore);
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_OLD_DETAIL_MUST_NOT_RENDER_STALE_FORM');
  if(!http.filter(r=>r.path.endsWith('/emergencyPlan/getById')).slice(-1).every(r=>r.httpStatus===200&&r.businessCode===0))throw Error('DELETED_PARENT_UI_DETAIL_RESPONSE');
  cases.push({case:'deleted-parent-actual-old-detail-route-shows-friendly-error-without-stale-form',passed:true});
  stage='deleted-parent-old-detail-retry';detailReadsBefore=oldDetailReads();
  if(!await click('.el-alert button','重试'))throw Error('DELETED_PARENT_RETRY_BUTTON_REQUIRED');
  await until(()=>oldDetailReads()>detailReadsBefore);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_RETRY_STALE_FORM');
  cases.push({case:'deleted-parent-detail-retry-uses-original-endpoint-and-keeps-friendly-empty-state',passed:true});
  stage='deleted-parent-old-detail-refresh';detailReadsBefore=oldDetailReads();
  await send('Page.reload',{ignoreCache:true},session);
  await until(()=>oldDetailReads()>detailReadsBefore);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_REFRESH_STALE_FORM');
  cases.push({case:'deleted-parent-detail-full-refresh-keeps-normal-auth-and-friendly-empty-state',passed:true});
  await fs.writeFile(O+'/deleted-detail-navigation-evidence.json',JSON.stringify({passed:true,actualCapturedNormalDetailURLUsed:true,navigationRetryAndRefreshChecked:true,originalDetailAPIHTTP200AndCode0:true,deletedDetailsNullVerifiedEarlier:true,staleFormAbsentOnAllThree:true,originalControllerAndCandidateService:true,onlyOwnSyntheticRecords:true},null,2));

  if(exceptions.length)throw Error('CANDIDATE_ORIGINAL_UI_EXCEPTION');
 }
 await Promise.allSettled([...reads]);
 await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,baseline:!!wire.baseline,originalNormalLoginAndNativeRoutes:true,onlyOwnedSyntheticPlanExerciseRows:true,fullNangangOrWholeModuleAccepted:false,publicOrFormalOrDesktopChanged:false,http,blocked,exceptions:exceptions.map(x=>({text:x.text,optionalJoinObserved:/join|undefined/.test(x.description||'')}))},null,2));

}catch(e){failed=String(e.message);const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads,debuggerObservations};try{diagnostic.resourceDeletionSteps=resourceDeletionSteps;diagnostic.visibleBoxes=await evaluate(`(${boxVisible}).map(e=>({text:e.innerText,buttons:Array.from(e.querySelectorAll('button')).map(b=>({text:b.textContent,disabled:b.disabled}))}))`)}catch{}try{if(stage!=='normal-login')diagnostic.visible=await evaluate('({path:location.pathname,text:document.body.innerText.slice(-1800)})')}catch{}await fs.writeFile(O+'/failure.json',JSON.stringify(diagnostic,null,2));}
finally{wire.password='';token='';if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}if(chrome)await new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));await fs.writeFile(O+'/browser-terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,normalBrowserClose:true,forceTerminationUsed:false}));}
if(failed)throw Error(failed);
