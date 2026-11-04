"""Bind the real task disposal UI to one new owned task and one exact save."""
from pathlib import Path
import subprocess
V=Path(__file__).resolve().parent;D=V/'feedback_r880'
def one(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)
def main():
    q=D/'run_feedback_full_r880.py';s=q.read_text('utf8');s=one(s,"D=V/'feedback_r880'","D=V");q.write_text(s,encoding='utf8')
    q=D/'callback_plan_r880.py';s=q.read_text('utf8');s=one(s,"V/'attest_owned_windows_process_r746.py'","V.parent/'attest_owned_windows_process_r746.py'");q.write_text(s,encoding='utf8')
    s=(V/'verify_r45_original_backend_browser_r850.mjs').read_text('utf8')
    s=s.replace('task-ui-r806','feedback-r880').replace("['pending-approve','completed-readonly']","['feedback-submit','feedback-readonly']")
    s=one(s,"if(w.mode==='pending-approve'&&w.account!=='own_reviewer_b'||w.mode==='completed-readonly'&&w.account!=='own_operator_a')throw Error('EXACT_NORMAL_UI_ACTOR_REQUIRED');", "if(w.account!=='own_operator_a'||!/^OWN_MANAGER_[0-9a-f]{32}$/.test(w.taskName)||!/^OWN_FEEDBACK_[0-9a-f]{32}$/.test(w.feedback)||!/^OWN_EVALUATION_[0-9a-f]{32}$/.test(w.evaluation))throw Error('EXACT_NORMAL_FEEDBACK_ACTOR_REQUIRED');")
    s=one(s,"if(w.mode!=='completed-readonly')throw Error('READ_ONLY_EXISTING_TASK_ONLY');", "if(w.eventId!=='a5320000000000000000000000000006')throw Error('OWN_CONFIRMED_EVENT_REQUIRED');")
    s=one(s,"const O='D:/Project/Zhumadian/work/bootstrap-browser-r850';await fs.mkdir(O);", "const O=root+'/ui-'+w.mode+'-r880';await fs.mkdir(O);")
    s=one(s,"const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];", "const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];let taskList=null,taskDetail=null,feedbackIssued=0,feedbackConfirmed=false;")
    anchor="  if(u.origin===w.base&&!['GET','HEAD'].includes(request.method)&&u.pathname!=='/zhumadian/api/jnpf/oauth/Login'){"
    gate=r'''
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
'''
    s=one(s,anchor,gate+anchor)
    anchor="   if(row.path.endsWith('/oauth/Login')){if(body.code!==200)problem='ORIGINAL_NORMAL_LOGIN_REFUSED';token=body.data?.token||''}"
    s=one(s,anchor,anchor+"\n   if(row.path.endsWith('/eventTask/getPage')&&body.code===0)taskList=body.data;\n   if(row.path.startsWith('/zhumadian/api/serv/eventTask/getById')&&body.code===0)taskDetail=body.data;\n   if(row.path.endsWith('/eventTask/updateById')){feedbackConfirmed=body.code===0&&body.data===true;if(!feedbackConfirmed)problem='ORIGINAL_FEEDBACK_UPDATE_NOT_SAVED';}")
    start=s.index(" for(const [route,endpoint] of");end=s.index(" stage='normal-header-logout-business-root';",start)
    workflow=r'''
 stage='original-owned-task-list';taskList=null;
 await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/taskSend'},session);
 await until(()=>Array.isArray(taskList?.records)&&evaluate('!!document.querySelector(".table-search")'));
 async function fill(label,value){
  const ok=await evaluate(`(()=>{const item=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\s:：]/g,'')===${JSON.stringify(label)});const input=item?.querySelector('input,textarea');if(!input||input.disabled||input.readOnly)return false;input.value=${JSON.stringify(value)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));input.dispatchEvent(new Event('blur',{bubbles:true}));return true})()`);
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
  await evaluate('(()=>{const e=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="处置时间")?.querySelector("input");e.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",code:"Enter",bubbles:true}));e.blur()})()');
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
'''
    s=s[:start]+workflow+s[end:]
    s=one(s,"taskCreationUIAccepted:false,approvalUIAccepted:w.mode==='pending-approve',approvalRequests:audits,", "taskCreationUIAccepted:false,approvalUIAccepted:false,approvalRequests:audits,feedbackUpdateRequests:feedbackIssued,feedbackSaveConfirmed:feedbackConfirmed,actualOriginalTaskFeedbackUI:true,")
    s=one(s,"failure:error.message,cases,requests,approvalRequests:audits,APIsMocked:false", "failure:error.message,cases,requests,approvalRequests:audits,feedbackUpdateRequests:feedbackIssued,feedbackSaveConfirmed:feedbackConfirmed,APIsMocked:false")
    q=D/'feedback_browser_r880.mjs';assert not q.exists();q.write_text(s,encoding='utf8')
    assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(q)],capture_output=True).returncode==0
    print('R880_REAL_FEEDBACK_BROWSER_PREPARED')
if __name__=='__main__':main()
