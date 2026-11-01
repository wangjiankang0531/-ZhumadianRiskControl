from pathlib import Path
import ast
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
s=(T/'verify_full_controller_pool_layout_browser_r139_20261101.mjs').read_text(encoding='utf-8');s=s.replace('full-controller-r139','full-controller-r142').replace("const O=root+'/duty-browser'","const O=root+'/task-feedback-browser'")
s=s.replace("if(!['dutyPersonnel','dutySchedule','dutyLog'].includes(kind)","if(!['eventInfo','eventTask'].includes(kind)")
s=s.replace("['dutyPersonnel','dutySchedule','dutyLog'].some","['eventInfo','eventTask'].some").replace("/dutyManage/dutyPersonnel'},session)","/emergencyResponse/taskSend'},session)")
s=s.replace("e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)","e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)}&&Array.from(e.querySelectorAll('input,textarea')).some(n=>!n.disabled&&!n.readOnly));const e=a?Array.from(a.querySelectorAll('input,textarea')).find(n=>!n.disabled&&!n.readOnly):null;if(!e||e.disabled||e.readOnly)")
start=s.index(" await mark('native-duty-menu');");end=s.index('\n}catch(e){failed=',start)
body=r'''
 await mark('task-native-list');await until(()=>evaluate('!document.querySelector(".login-body")&&!!document.querySelector(".table-box")'));
 cases.push({case:'original-sdk-normal-login-and-compiled-task-route',passed:true});
 async function business(kind,action,body=null){
  if(!['eventInfo','eventTask'].includes(kind)||!['save','updateById','removeById'].includes(action.split('?')[0]))throw Error('OWN_TASK_WRITE_SCOPE');
  const ua=await evaluate('navigator.userAgent'),response=await fetch(wire.base+'/zhumadian/api/serv/'+kind+'/'+action,{method:body?'POST':'GET',headers:{Authorization:token,'User-Agent':ua,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
  const v=await response.json();if(response.status!==200||v.code!==0||v.data!==true)throw Error('OWN_ORIGINAL_TASK_PREPARATION_FAILED_'+kind+'_'+action.split('?')[0]);return v.data;
 }
 async function makeTask(suffix){
  const taskName='OWN_R142_'+root.split('/').at(-1)+'_'+suffix;
  await business('eventInfo','save',{eventName:taskName,eventContent:'Own isolated feedback test',eventType:'1',eventLevel:'1',eventLocation:'Own test site',reportTime:'2026-11-01 09:00:00'});
  const events=await ownAPI('eventInfo','/getPage?current=1&size=10&eventName='+encodeURIComponent(taskName)),event=events.records.find(x=>x.eventName===taskName);if(!event)throw Error('OWN_EVENT_NOT_FOUND');
  await business('eventInfo','updateById',{id:event.id,researchStatus:'1',eventLevel:'1',researchResult:'Own confirmed'});
  await business('eventTask','save',{infoId:event.id,eventNumber:event.eventNumber,eventName:taskName,taskName,taskContent:'Own feedback and evaluation',dispatchTime:'2026-11-01 09:10:00'});
  const tasks=await ownAPI('eventTask','/getPage?current=1&size=10&taskName='+encodeURIComponent(taskName)),task=tasks.records.find(x=>x.taskName===taskName);if(!task?.id||!task.flowId||task.taskStatus!=='2')throw Error('OWN_ORIGINAL_PENDING_TASK_AND_INSTANCE_REQUIRED');return task;
 }
 async function openDisposal(task){
  await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyResponse/taskSend'},session);await until(()=>evaluate('!!document.querySelector(".table-box")'));
  await fill('任务名称',task.taskName);if(!await click('.table-search button','搜索'))throw Error('NATIVE_TASK_SEARCH_BUTTON');
  await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(e=>e.textContent.includes(${JSON.stringify(task.taskName)}))`));
  if(!await evaluate(`(()=>{const row=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.textContent.includes(${JSON.stringify(task.taskName)}));const b=row?Array.from(row.querySelectorAll('button')).find(e=>e.textContent.trim()==='处置'):null;if(!b)return false;b.click();return true})()`))throw Error('ORIGINAL_TASK_DISPOSAL_ACTION_MISSING');
  await until(()=>evaluate("location.pathname.endsWith('/taskSend/detail')&&new URL(location.href).searchParams.get('judge')==='1'&&document.querySelectorAll('textarea:not(:disabled)').length===2"));
  cases.push({case:'original-task-list-disposal-action-opens-real-feedback-form',passed:true});
 }
 async function fillFeedback(feedback,evaluation){
  await until(()=>evaluate("['处置时间','反馈信息','评估总结'].every(label=>Array.from(document.querySelectorAll('.el-form-item')).filter(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===label).some(e=>Array.from(e.querySelectorAll('input,textarea')).some(n=>n.getClientRects().length&&!n.disabled&&!n.readOnly)))"));
  await fill('处置时间','2026-11-01 09:30:00');await evaluate(`(()=>{const input=Array.from(document.querySelectorAll('.el-form-item')).filter(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='处置时间').flatMap(e=>Array.from(e.querySelectorAll('input'))).find(e=>!e.disabled&&!e.readOnly);input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true}));input.blur()})()`);
  await fill('反馈信息',feedback);await fill('评估总结',evaluation);
 }
 const task=await makeTask('normal');await openDisposal(task);await mark('feedback-required');let before=count('eventTask','updateById');await click('button','提交');await until(()=>evaluate('document.querySelectorAll(".el-form-item__error").length>0'));if(count('eventTask','updateById')!==before)throw Error('INVALID_FEEDBACK_SAVED');cases.push({case:'native-disposal-required-fields-do-not-call-update',passed:true});
 await mark('feedback-save');await fillFeedback('OWN_R142_FEEDBACK','OWN_R142_EVALUATION');await evaluate(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(e=>e.getClientRects().length&&e.textContent.trim()==='提交');b.click();b.click()})()`);
 await until(()=>count('eventTask','updateById')>before);await until(()=>evaluate("location.pathname.endsWith('/emergencyResponse/taskSend')"));if(count('eventTask','updateById')!==before+1)throw Error('FEEDBACK_DOUBLE_SUBMIT_REACHED_BACKEND');
 const saved=await ownAPI('eventTask','/getById?id='+encodeURIComponent(task.id));if(saved.id!==task.id||saved.flowId!==task.flowId||saved.taskStatus!=='1'||saved.feedbackInfo!=='OWN_R142_FEEDBACK'||saved.evaluationSum!=='OWN_R142_EVALUATION'||saved.disposeTime!=='2026-11-01 09:30:00')throw Error('NATIVE_FEEDBACK_FIELDS_NOT_PERSISTED');cases.push({case:'one-native-feedback-update-persists-time-feedback-evaluation-and-original-instance',passed:true});
 await mark('feedback-readonly');await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyResponse/taskSend/detail?id='+encodeURIComponent(task.id)},session);await until(()=>evaluate("['OWN_R142_FEEDBACK','OWN_R142_EVALUATION'].every(value=>document.body.innerText.includes(value)||Array.from(document.querySelectorAll('input,textarea')).some(e=>e.getClientRects().length&&e.value===value))"));if(await evaluate("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length&&e.textContent.trim()==='提交')"))throw Error('READONLY_TASK_DETAIL_HAS_SUBMIT');cases.push({case:'real-compiled-readonly-task-detail-renders-persisted-feedback-without-submit',passed:true});
 const stale=await makeTask('stale');await openDisposal(stale);await fillFeedback('OWN_R142_STALE_FEEDBACK','OWN_R142_STALE_EVALUATION');await business('eventTask','removeById?id='+encodeURIComponent(stale.id));before=count('eventTask','updateById');await mark('stale-row-save');await click('button','提交');await until(()=>count('eventTask','updateById')>before);await sleep(300);
 const falseSave=http.filter(x=>x.path.endsWith('/eventTask/updateById')).at(-1);if(falseSave?.businessCode!==0||falseSave.saved!==false)throw Error('ACTUAL_FALSE_SAVE_RESPONSE_REQUIRED');
 const outcome=await evaluate("({stayed:location.pathname.endsWith('/taskSend/detail'),feedback:Array.from(document.querySelectorAll('textarea')).some(e=>e.value==='OWN_R142_STALE_FEEDBACK'),successMessage:Array.from(document.querySelectorAll('.el-message')).some(e=>e.textContent.includes('操作成功'))})");await fs.writeFile(O+'/false-save-response-proof.json',JSON.stringify({actualCodeZeroDataFalse:true,...outcome},null,2));
 if(!outcome.stayed||!outcome.feedback||outcome.successMessage)throw Error('FALSE_DISPOSAL_SAVE_LOST_INPUT_OR_REPORTED_SUCCESS');cases.push({case:'native-code-zero-data-false-keeps-input-and-does-not-report-success',passed:true});
 await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,cases,originalSDKAndCompiledNativePages:true,actualOriginalFeedbackBusinessAPIsUsed:true,realNangangDesignerTemplateOrWholeFlowAccepted:false,http,blocked,exceptions},null,2));
'''
s=s[:start]+body+s[end:];(T/'verify_full_controller_task_feedback_browser_r142_20261101.mjs').write_bytes(s.encode())
p=(T/'verify_full_controller_pool_layout_r139_20261101.py').read_text(encoding='utf-8').replace("base=R/'work/event_delivery_consistency_20261030/full-controller-r139'","base=R/'work/event_delivery_consistency_20261030/full-controller-r142'")
p=p.replace("if options.variant=='combined':prepared_base=base/'candidate-install-r3'","if options.variant=='combined':prepared_base=R/'work/event_delivery_consistency_20261030/full-controller-r139/candidate-install-r3'")
p=p.replace('verify_full_controller_pool_layout_browser_r139_20261101.mjs','verify_full_controller_task_feedback_browser_r142_20261101.mjs').replace('duty-browser/','task-feedback-browser/').replace('actual-native-duty-browser','actual-native-task-feedback-browser').replace('actualNormalRoleNativeDutyBrowserPassed','actualNormalRoleNativeTaskFeedbackBrowserPassed').replace('OWN_NATIVE_DUTY_BROWSER_FAILED','OWN_NATIVE_TASK_FEEDBACK_BROWSER_FAILED').replace('xnby.r139.native-generated-primary-controller-check.v1','xnby.r142.native-task-feedback-controller-check.v1')
p=p.replace('root=base/options.attempt;assert not root.exists();root.mkdir()','root=base/options.attempt;assert not root.exists();root.mkdir(parents=True)')
ast.parse(p);(T/'verify_full_controller_task_feedback_r142_20261101.py').write_bytes(p.encode());print('R142_EXACT_COMPILED_NATIVE_TASK_FEEDBACK_AND_FALSE_SAVE_TEST_READY')
