"""Wire the staged original callbacks, real UI feedback and same-data restart."""
from pathlib import Path
import ast, hashlib, json
V=Path(__file__).resolve().parent;D=V/'feedback_r880';R=Path('D:/Project/Zhumadian')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
    assert s.count(a)==1,a[:120]
    return s.replace(a,b)
def main():
    s=(V/'run_research_task_ui_business_r810.py').read_text('utf8')
    s=s.replace("W=O/'task-ui-r806';P=W/'resume-r810'","W=O/'feedback-r880';P=W/'runtime'")
    s=s.replace("V/'run_task_ui_callbacks_r806.py'","V/'run_callbacks_r880.py'")
    s=s.replace('task-ui-r810-source-pins.json','feedback-r880-source-pins.json')
    s=s.replace("T/'factory_integrated_full_health_r696.py'","V/'feedback_health_r880.py'")
    s=s.replace("classes=W/'classes-r810'","classes=W/'classes-r880'")
    s=s.replace("V/'task_ui_r810/OwnManagerBusinessReadbackR783.java'","V/'OwnManagerBusinessReadbackR783.java'")
    s=s.replace("V/'task_ui_r810/OwnOriginalManagerDirectoryR609.java'","V/'OwnOriginalManagerDirectoryR609.java'")
    s=s.replace('snapshot-r810-','snapshot-r880-')
    s=s.replace('create_task_normal_browser_r810.mjs','create_task_browser_r880.mjs').replace('ui-create-r810','ui-create-r880')
    s=s.replace('normal_manager_browser_r806.mjs','normal_manager_browser_r880.mjs').replace("'-r806'","'-r880'")
    anchor="  else:\n   assert link is not None;script=V/'normal_manager_browser_r880.mjs';folder=W/('ui-'+mode+'-r880')"
    branch="""  elif mode in ['feedback-submit','feedback-readonly']:
   assert link is not None;script=V/'feedback_browser_r880.mjs';folder=W/('ui-'+mode+'-r880')
   wire.update(mode=mode,eventId='a5320000000000000000000000000006',taskName=flight['taskName'],feedback='OWN_FEEDBACK_'+nonce,evaluation='OWN_EVALUATION_'+nonce,
    opinion=flight['approval'],versionId=d['versionId'],**{k:link[k]for k in ['taskId','instanceId','operatorId','engineTaskId']})
"""
    s=one(s,anchor,branch+anchor)
    s=one(s,"inspected=snapshot('inspect');researchRequired=inspected['existingOwnedEventConfirmed']=='false';directory('inspect');managerMayNeedRestore=True;directory('apply')", "inspected=snapshot('inspect');assert inspected['existingOwnedEventConfirmed']=='true','EXISTING_OWN_CONFIRMED_EVENT_REQUIRED';researchRequired=False;directory('inspect');managerMayNeedRestore=True;directory('apply')")
    s=one(s,"callbackStage=W/'normal-restart';callbackStage.mkdir();", "callbackStage=W/'first-start';callbackStage.mkdir();")
    s=one(s,"cb=callbacks.run_callback_setup('normal-restart',", "cb=callbacks.run_callback_setup('first-start',")
    anchor="   submitted=snapshot('submitted');ui=browser('pending-approve',submitted);assert ui['approvalRequests']==1"
    s=one(s,anchor,"   submitted=snapshot('submitted');feedback=browser('feedback-submit',submitted);assert feedback['feedbackUpdateRequests']==1 and feedback['feedbackSaveConfirmed']\n   checked=snapshot('feedback');assert checked['originalFeedbackEvaluationTimeMatched']=='true'and checked['activeEngineTasks']=='1'and checked['originalProcessEnded']=='false'\n   ui=browser('pending-approve',submitted);assert ui['approvalRequests']==1")
    anchor="   submitted=props(W/'snapshot-r880-submitted.properties');ui=browser('completed-readonly',submitted);assert ui['approvalRequests']==0"
    s=one(s,anchor,anchor+"\n   feedback=browser('feedback-readonly',submitted);assert feedback['feedbackUpdateRequests']==0")
    anchor="  assert final['originalReadOnlyFormValuePreserved']=='true'and final['originalManagerOpinionPersisted']=='true'"
    s=one(s,anchor,anchor+"and final['originalFeedbackEvaluationTimeMatched']=='true'")
    s=s.replace('business-result-r810.json','business-result-r880.json')
    s=one(s,"taskAndApprovalMutationsRetried=False,APIsMocked=False", "originalFeedbackEvaluationAndTimePersisted=True,taskAndApprovalMutationsRetried=False,APIsMocked=False")
    q=D/'feedback_probe_r880.py';assert not q.exists();q.write_text(s,encoding='utf8');ast.parse(s)
    # The helpers inherited from the old source directory remain immutable;
    # only new candidate sources are resolved from this independent package.
    q=D/'callback_plan_r880.py';s=q.read_text('utf8')
    s=one(s,"runtime=load('manager_callback_owned_runtime_r769',UPDATER)","runtime=load('manager_callback_owned_runtime_r769',UPDATER)")
    q.write_text(s,encoding='utf8');ast.parse(s)
    for q in D.glob('*.py'):ast.parse(q.read_bytes(),filename=q.name)
    dependencies=[V/'attest_owned_windows_process_r746.py',V/'original_public_test_update_r45_bootstrap_r847.py',
      R/'Application/tools/owned_callback_runtime_plan_r663.py',R/'Application/tools/OwnedOriginalCallbacksR648.java',
      R/'Application/tools/OwnedOriginalCallbackProvisioningR659.java',R/'Application/tools/OwnedWindowsProcessArgumentsR747.java',
      R/'Application/tools/owned_task_configuration_r637.py',R/'Application/tools/owned_candidate_code_transaction_r543.py',
      R/'Application/tools/owned_run_pointer_r717.py',R/'Application/tools/owned_run_terminal_r709.py',R/'Application/tools/bounded_build_job_r671.py',
      V/'prepare_feedback_runtime_r880.py',V/'prepare_feedback_browser_r880.py',Path(__file__)]
    own=[p for p in D.rglob('*') if p.is_file()and p.suffix in ['.py','.mjs','.java','.json','.properties']]
    pin={'files':{str(p):sha(p)for p in [*own,*dependencies]},'actualBusinessFlowAccepted':False,'servicesStarted':False,'sourceOnlyPrepared':True}
    q=D/'feedback-r880-source-pins.json';assert not q.exists();q.write_text(json.dumps(pin,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'preparedSourcesAndDependencies':len(pin['files']),'runtimePlanFixed':True,'servicesStarted':False,'businessWrites':False}))
if __name__=='__main__':main()
