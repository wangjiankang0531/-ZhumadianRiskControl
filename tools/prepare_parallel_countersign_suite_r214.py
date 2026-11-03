from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).parent
def save(name,s):
 p=T/name;assert not p.exists(),name
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
def swap(s,a,b):
 assert s.count(a)==1,(a[:70],s.count(a));return s.replace(a,b)
config=(T/'configure_owned_countersign_r199.py').read_text(encoding='utf-8').replace('r99','r105')
config=swap(config,"node['properties']['counterSign']=1","node['properties']['counterSign']=1\nnode['properties']['approvers']=['a5310000000000000000000000000064--user','a5310000000000000000000000000065--user']")
config=config.replace("'onlySyntheticFirstNodeChangedToCountersign'","'onlySyntheticFirstNodeChangedToTwoApproverCountersign'").replace("'firstNodeCounterSignAfter':1","'firstNodeCounterSignAfter':1,'ownNormalApprovers':2,'productOrRealTemplateChanged':False")
save('configure_owned_parallel_countersign_r214.py',config)
for old,new in [('prepare_personal_workflow_frontend_r199.py','prepare_personal_workflow_frontend_r214.py'),('restore_personal_workflow_frontend_r199.py','restore_personal_workflow_frontend_r214.py'),('restore_production_history_runtime_r199.py','restore_production_history_runtime_r214.py')]:
 save(new,(T/old).read_text(encoding='utf-8').replace('r199','r214').replace('r99','r105'))
runtime=(T/'prepare_production_history_runtime_r208.py').read_text(encoding='utf-8').replace('prepared-r104','prepared-r105').replace("C/'r104'","C/'r105'")
runtime=swap(runtime,"'tools/original_public_test_update.py':W/'original_public_test_update.py'","'tools/original_public_test_update.py':R/'Application/tools/original_public_test_update_r36_20261103_r2.py'")
save('prepare_production_history_runtime_r214.py',runtime)
menu=(T/'OwnPersonalWorkflowMenuVisibilityR199.java').read_text(encoding='utf-8').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR214').replace('matches("r99")','matches("r105")');save('OwnPersonalWorkflowMenuVisibilityR214.java',menu)
java=(T/'java/workflow_serial_r163/OwnReturnWorkflowReadback.java').read_text(encoding='utf-8').replace('public final class OwnReturnWorkflowReadback','public final class OwnParallelWorkflowReadbackR214')
java=swap(java,'(a[10].equals("observe")||pending==Integer.parseInt(a[10]))','(a[10].equals("observe")?(pending>=1&&pending<=2):pending==Integer.parseInt(a[10]))')
save('OwnParallelWorkflowReadbackR214.java',java)
browser=(T/'verify_native_personal_workflow_r199_20261103.mjs').read_text(encoding='utf-8')
browser=swap(browser,"'reviewer-handled-readback'].includes(wire.phaseName)","'reviewer-handled-readback','operator-waiting-parallel-b'].includes(wire.phaseName)")
anchor=" if(!wire.expectEmptyFlowRejection){ const endpoint="
before=""" if(wire.phaseName==='operator-waiting-parallel-b'){
  const pendingRows=await menu('待办事宜','/FlowBefore/List/1');
  if(pendingRows.some(x=>x.processInstanceId===context.flowId||x.id===context.flowId))throw Error('FIRST_COUNTERSIGN_APPROVER_MUST_NO_LONGER_HAVE_PENDING_WORK');
  cases.push({case:'first-countersign-approver-no-longer-has-same-instance-in-pending-list-before-second-approval',passed:true});
 }
"""
browser=swap(browser,anchor,before+anchor)
anchor="  if(wire.approveOnce){\n"
guard="""  if(wire.phaseName==='operator-waiting-parallel-b'){
   if(await evaluate('!!document.querySelector(".audit-content .audit-form")'))throw Error('INITIATOR_READBACK_MUST_NOT_APPROVE_WAITING_COUNTERSIGN');
   cases.push({case:'initiator-detail-while-waiting-other-countersign-is-readonly',passed:true});
  }
  if(wire.approveOnce){
   if(['operator-added','reviewer-after-added'].includes(wire.phaseName)){
    const expected=['a5310000000000000000000000000064--user','a5310000000000000000000000000065--user'];
    const actual=nativeNodeProperties.approvers;
    await fs.writeFile(O+'/native-two-approver-node.json',JSON.stringify({counterSign:nativeNodeProperties.counterSign,title:nativeNodeProperties.title,approvers:actual,syntheticProviderOnly:true}));
    if(nativeNodeProperties.counterSign!==1||nativeNodeProperties.title!=='OWN_APPROVE'||!Array.isArray(actual)||actual.length!==2||!expected.every(x=>actual.includes(x)))throw Error('REAL_PROVIDER_MUST_RETURN_FIRST_COUNTERSIGN_NODE_AND_TWO_OWN_APPROVERS');
    cases.push({case:'actual-native-provider-two-ordinary-approver-countersign-before-'+wire.phaseName,passed:true});
    if(wire.phaseName==='reviewer-after-added'){
     const first=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_operator-added'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
     const secondDone=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-after-added'&&x.handleTime);
     if(first.length!==1||secondDone.length)throw Error('FIRST_APPROVAL_RETAINED_AND_SECOND_APPROVER_STILL_NOT_DONE_REQUIRED');
     cases.push({case:'after-first-approval-second-role-still-on-first-node-with-distinct-first-opinion',passed:true});
    }
   }
   if(wire.phaseName==='reviewer-final'&&nativeNodeProperties.title!=='OWN_FINAL_REVIEW')throw Error('SECOND_COUNTERSIGN_APPROVAL_MUST_ADVANCE_TO_FINAL_NODE');
"""
browser=swap(browser,anchor,guard)
start=browser.index("  const added=nativeRecords.filter",browser.index(" if(wire.phaseName==='operator-completed-readback')"));end=browser.index("\n }\n if(exceptions.length)",start)
browser=browser[:start]+"""  const first=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_operator-added'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  const second=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-after-added'&&x.handleTime&&String(x.userName).includes('own_reviewer_b'));
  const final=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-final'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  if(first.length!==1||second.length!==1||final.length!==1||Number(first[0].handleTime)>Number(second[0].handleTime)||Number(second[0].handleTime)>Number(final[0].handleTime))throw Error('THREE_DISTINCT_COUNTERSIGN_FINAL_OPINIONS_AND_REAL_TIME_ORDER_REQUIRED');
  if(nativeRecords.some(x=>String(x.handleStatus)==='10'||x.handleOpinion==='OWN_R172_ADDSIGN_OPERATOR'))throw Error('ORDINARY_COUNTERSIGN_MUST_NOT_CREATE_ADDSIGN_HISTORY');
  await fs.writeFile(O+'/parallel-countersign-observation.json',JSON.stringify({bothOrdinaryApproversAndFinalNodeOpinionsExactlyOnce:true,actualOrderFirstThenSecondThenFinal:true,nonTargetApprovalCreatedNoAddsignHistory:true,taskEventFeedbackAttachmentAssociationsRetained:true,wholeNangangAcceptanceClaimed:false},null,2));
  cases.push({case:'two-ordinary-countersign-approvers-and-final-node-distinct-opinions-and-order-preserved',passed:true});
"""+browser[end:]
save('verify_native_parallel_countersign_r214_20261103.mjs',browser)
host=(T/'verify_full_controller_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r214').replace('r99','r105').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR214')
host=host.replace("verify_native_personal_workflow_r214_20261103.mjs","verify_native_parallel_countersign_r214_20261103.mjs").replace("R/'Application/tools/java/workflow_serial_r163/OwnReturnWorkflowReadback.java'","Path(__file__).parent/'OwnParallelWorkflowReadbackR214.java'").replace("'OwnReturnWorkflowReadback'","'OwnParallelWorkflowReadbackR214'")
start=host.index("        add_type='2'");end=host.index("        state_source=",start)
host=host[:start]+"""        add_type='none'
        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('operator-added','own_operator_a','reviewer',True,False),('operator-waiting-parallel-b','own_operator_a','operator',False,False),('reviewer-after-added','own_reviewer_b','reviewer',True,False),('reviewer-final','own_operator_a','reviewer',True,False),('reviewer-handled-readback','own_reviewer_b','reviewer',False,False),('operator-completed-readback','own_operator_a','operator',False,False)]
"""+host[end:]
host=swap(host,"'addsignOnce':label=='reviewer-addsign'","'addsignOnce':False")
start=host.index("            context=read(root/'workflow-context.private.json');definition=");end=host.index("\n            state_args=",start)
host=host[:start]+"""            context=read(root/'workflow-context.private.json');definition=read(root/'own-serial-definition.json');ended=label in ['reviewer-final','reviewer-handled-readback','operator-completed-readback'];business_status='2' if label=='operator' else '1';pending_expected='0' if ended else 'observe';ended_expected='true' if ended else 'false'
""".rstrip()+host[end:]
host=host.replace("checks['actualCreateFeedbackAddsignAndNativeSequenceBrowsersPassed']","checks['actualCreateFeedbackParallelCountersignAndFinalApprovalBrowsersPassed']")
start=host.index("        opinion=read(root/'workflow-browser-operator-completed-readback/");end=host.index("        dump(root/'ready-checks.json'",start)
host=host[:start]+"""        opinion=read(root/'workflow-browser-operator-completed-readback/parallel-countersign-observation.json')
        assert opinion['bothOrdinaryApproversAndFinalNodeOpinionsExactlyOnce'] and opinion['actualOrderFirstThenSecondThenFinal'] and opinion['nonTargetApprovalCreatedNoAddsignHistory']
        checks['normalTwoApproverCountersignWaitsForOtherRoleThenFinalNodePassed']=True
"""+host[end:]
host=host.replace("'native-after-addsign-history-regression", "'native-parallel-countersign-regression")
host=host.replace('native-after-addsign-history-regression','native-parallel-countersign-regression').replace("'actualNativeCreateUploadFeedbackAddsignAndTargetApprovalPassed':True","'actualNativeCreateUploadFeedbackTwoApproverCountersignAndFinalApprovalPassed':True").replace("'independentAfterAddsignOpinionRetained':True","'ordinaryCountersignDidNotCreateNonTargetAddsignHistory':True").replace("'actualAddsignAndRemainingReviewsCompleted':not options.completed_addsign_readback","'actualTwoApproverCountersignAndFinalApprovalCompleted':True")
save('verify_full_controller_parallel_countersign_r214_20261103.py',host)
runner=(T/'run_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r214').replace('r99','r105').replace('verify_full_controller_personal_workflow_r214','verify_full_controller_parallel_countersign_r214')
save('run_parallel_countersign_r214_20261103.py',runner)
print(json.dumps({'preparedSuiteOnly':True,'attempt':'r105','actualOrdinaryApprovers':2,'browserPhases':8,'finalR36UpdaterUsed':True,'fixtureNotYetPreparedOrStarted':True,'publicOrDesktopChanged':False}))
