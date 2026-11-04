"""Derive a read-only original-status check; never reopen/submit a completed task."""
from pathlib import Path
import ast, hashlib, json, subprocess
V=Path(__file__).resolve().parent; A=Path('D:/Project/Zhumadian/Application'); T=A/'tools'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)
def write(name,s):
    p=V/name; assert not p.exists(); p.write_text(s,encoding='utf8')
    if p.suffix=='.py':ast.parse(s)
    else:
        r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True)
        assert r.returncode==0,r.stderr[:500]
    return p
def main():
    pins=json.loads((V/'r45-compatibility-source-pins-r850.json').read_bytes())
    for path,pin in pins['files'].items():assert sha(Path(path))==pin
    s=(V/'verify_r45_original_backend_browser_r850.mjs').read_text('utf8')
    s=s.replace("work/bootstrap-browser-r850'","work/task-status-browser-r874'")
    s=one(s,"const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];", "const assets=[];let loginVisibleMs=0;let loginStarted=0;let anonymousAssets=[];let taskList=null, taskRow=null, taskDetail=null;")
    a="   if(row.path.endsWith('/oauth/Login')){if(body.code!==200)problem='ORIGINAL_NORMAL_LOGIN_REFUSED';token=body.data?.token||''}"
    s=one(s,a,a+"\n   if(row.path.endsWith('/eventTask/getPage')&&body.code===0)taskList=body.data;\n   if(row.path.startsWith('/zhumadian/api/serv/eventTask/getById')&&body.code===0)taskDetail=body.data;")
    a="  cases.push({case:'original-business-list-and-registered-form-components',route,passed:true,navigationMs:Date.now()-start});"
    extra=r'''
  if(route==='/emergencyResponse/taskSend'){
   stage='original-completed-task-list-and-status';
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-form-item")).some(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="任务名称"&&!!e.querySelector("input"))'));
   taskList=null;
   await evaluate(`(()=>{const item=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()==='任务名称');const input=item.querySelector('input');input.value=${JSON.stringify(w.taskName)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));const button=Array.from(document.querySelectorAll('.table-search button')).find(e=>e.textContent.trim()==='搜索');if(!button)throw Error('ORIGINAL_TASK_SEARCH_REQUIRED');button.click()})()`);
   await until(()=>Array.isArray(taskList?.records));
   const matches=taskList.records.filter(r=>r.id===w.taskId&&r.taskName===w.taskName);
   if(matches.length!==1||matches[0].flowId!==w.instanceId||matches[0].taskStatus!=='1')throw Error('EXACT_APPROVED_OWN_TASK_STATUS_REQUIRED');
   taskRow=matches[0];
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).filter(e=>e.textContent.includes('+JSON.stringify(w.taskName)+')).length===1'));
   const actions=await evaluate('(()=>{const row=Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).find(e=>e.textContent.includes('+JSON.stringify(w.taskName)+'));return Array.from(row.querySelectorAll("button")).filter(e=>e.getClientRects().length).map(e=>e.textContent.trim())})()');
   if(actions.includes('处置')||!actions.includes('详情'))throw Error('ORIGINAL_COMPLETED_STATUS_DISPOSAL_VISIBILITY_CHANGED');
   cases.push({case:'original-approved-status-one-hides-disposal-without-forcing-route-or-changing-status',passed:true});
   taskDetail=null;
   await evaluate('(()=>{const row=Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).find(e=>e.textContent.includes('+JSON.stringify(w.taskName)+'));Array.from(row.querySelectorAll("button")).find(e=>e.textContent.trim()==="详情").click()})()');
   await until(()=>taskDetail?.id===w.taskId&&evaluate('location.pathname.endsWith("/taskSend/detail")'));
   const view=await evaluate('({editableFeedback:Array.from(document.querySelectorAll("textarea")).some(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly),submit:Array.from(document.querySelectorAll("button")).some(e=>e.getClientRects().length&&e.textContent.trim()==="提交"),judge:new URL(location.href).searchParams.has("judge")})');
   if(view.editableFeedback||view.submit||view.judge||taskDetail.flowId!==w.instanceId||taskDetail.taskStatus!=='1')throw Error('COMPLETED_TASK_DETAIL_MUST_REMAIN_ORIGINAL_READONLY');
   const empty=k=>taskDetail[k]===null||taskDetail[k]===undefined||taskDetail[k]==='';
   cases.push({case:'original-approved-task-detail-keeps-same-instance-and-readonly-feedback-fields',passed:true,feedbackPreviouslyEmpty:empty('feedbackInfo'),evaluationPreviouslyEmpty:empty('evaluationSum'),disposeTimePreviouslyEmpty:empty('disposeTime')});
  }
'''
    s=one(s,a,a+extra)
    p1=write('verify_task_status_sequence_browser_r874.mjs',s)
    s=(V/'probe_r45_original_backend_r850.py').read_text('utf8')
    s=s.replace('component-bootstrap-r850','task-status-sequence-r874').replace('bootstrap-browser-r850','task-status-browser-r874')
    s=s.replace('verify_r45_original_backend_browser_r850.mjs','verify_task_status_sequence_browser_r874.mjs')
    s=one(s,"    assert label=='normal-restart' and children_exited() and not OUT.exists()", "    assert label=='normal-restart' and children_exited() and not OUT.exists()")
    s=one(s,"'mode':'completed-readonly','opinion':flight['approval']", "'mode':'completed-readonly','taskName':flight['taskName'],'opinion':flight['approval']")
    s=one(s,"    static=load('r45_static_gateway_probe',V/'probe_r45_original_gateway_r850.py').run_probe(row,label,gateway_port,nonce)\n    assert static['passed'];proof['actualGatewayGzipCacheAndDecodedSHAValidated']=True", "    assert any(c['case']=='original-approved-status-one-hides-disposal-without-forcing-route-or-changing-status' and c['passed'] for c in result['cases'])\n    proof['originalCompletedTaskDisposalVisibilityAndReadOnlyDetailVerified']=True\n    proof['feedbackOrApprovalSubmitted']=False")
    s=s.replace('business-result-r850.json','business-result-r874.json')
    p2=write('probe_task_status_sequence_r874.py',s)
    s=(V/'run_r45_original_backend_r850.py').read_text('utf8')
    s=s.replace("P=O/'component-bootstrap-r850';Z=R/'work/original-backend-full-r850'", "P=O/'task-status-sequence-r874';Z=R/'work/task-status-full-r874'")
    s=s.replace('probe_r45_original_backend_r850.py','probe_task_status_sequence_r874.py')
    s=one(s,"prior=J(R/'work/bootstrap-full-r845/verified-component-bootstrap-r845.json')", "prior=J(R/'work/original-backend-full-r850/verified-component-bootstrap-r850.json')")
    s=s.replace('verified-component-bootstrap-r850.json', 'verified-task-status-sequence-r874.json')
    # The prior proof is immutable; only the new output gets the new name.
    s=s.replace("prior=J(R/'work/original-backend-full-r850/verified-task-status-sequence-r874.json')", "prior=J(R/'work/original-backend-full-r850/verified-component-bootstrap-r850.json')")
    s=s.replace('r45-backend-not-started-r850.json','task-status-not-started-r874.json').replace('r45-backend-full-result-r850.json','task-status-full-result-r874.json')
    anchor="for source,pin in J(V/'r45-compatibility-source-pins-r850.json')['files'].items():assert sha(Path(source))==pin,'COMPONENT_BOOTSTRAP_SOURCE_DRIFT'"
    s=one(s,anchor,anchor+"\nfor source,pin in J(V/'task-status-source-pins-r874.json')['files'].items():assert sha(Path(source))==pin,'TASK_STATUS_REVIEW_SOURCE_DRIFT'")
    p3=write('run_task_status_sequence_r874.py',s)
    profiles={'files':{str(p):sha(p) for p in [p1,p2,p3,Path(__file__)]},'businessWritesIntended':False,'newNativeBuildOrRun':False,'originalPublicR45BackendAndFullFrontend':True}
    target=V/'task-status-source-pins-r874.json';assert not target.exists();target.write_text(json.dumps(profiles,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'prepared':True,'files':len(profiles['files']),'onlyReadOnlyTaskUI':True,'servicesStarted':False}))
if __name__=='__main__':main()
