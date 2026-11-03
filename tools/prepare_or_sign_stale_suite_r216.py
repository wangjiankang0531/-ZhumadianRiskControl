from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools')
def save(name,s):
 p=T/name;assert not p.exists(),name
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
def swap(s,a,b):assert s.count(a)==1,(a[:75],s.count(a));return s.replace(a,b)
names=['prepare_personal_workflow_frontend_r215.py','restore_personal_workflow_frontend_r215.py','restore_production_history_runtime_r215.py','prepare_production_history_runtime_r215.py','OwnPersonalWorkflowMenuVisibilityR215.java','OwnParallelWorkflowReadbackR215.java']
for name in names:save(name.replace('r215','r216').replace('R215','R216').replace('OwnParallelWorkflowReadback','OwnOrSignWorkflowReadback'),(T/name).read_text(encoding='utf-8').replace('r215','r216').replace('R215','R216').replace('r106','r107').replace('OwnParallelWorkflowReadback','OwnOrSignWorkflowReadback'))
config=(T/'configure_owned_parallel_countersign_r215.py').read_text(encoding='utf-8').replace('r106','r107')
config=swap(config,"node['properties']['counterSign']=1","node['properties']['counterSign']=0").replace("'firstNodeCounterSignAfter':1","'firstNodeCounterSignAfter':0").replace('TwoApproverCountersign','TwoApproverOrSign')
config=config.replace("'onlySyntheticFirstNodeCounterSign':1","'onlySyntheticFirstNodeCounterSign':0")
save('configure_owned_or_sign_r216.py',config)
browser=(T/'verify_native_parallel_countersign_r215_20261103.mjs').read_text(encoding='utf-8')
browser=swap(browser,"'operator-waiting-parallel-b'].includes(wire.phaseName)","'operator-waiting-parallel-b','reviewer-preview','operator-stale-first-node','reviewer-stale-first-node'].includes(wire.phaseName)")
start=browser.index(" if(wire.phaseName==='operator-waiting-parallel-b'){\n  const pendingRows=");end=browser.index(' if(!wire.expectEmptyFlowRejection)',start)
stale=''' if(wire.stalePendingLink){
  stage='actual-old-operator-detail-after-or-sign-advanced';
  const old=context.oldPendingLinks?.[wire.account];if(!old||typeof old.relativeURL!=='string')throw Error('EXACT_SAVED_OWN_OPERATOR_LINK_REQUIRED');
  const target=new URL(old.relativeURL,wire.base);
  if(target.origin!==wire.base||target.pathname!=='/zhumadian/emergency/workflow/flowTodo/detail'||target.searchParams.get('id')!==old.operatorId)throw Error('SAVED_OWN_PENDING_DETAIL_SCOPE_REQUIRED');
  const rows=await menu('待办事宜','/FlowBefore/List/1'),same=rows.filter(x=>x.processInstanceId===context.flowId||x.id===context.flowId);
  if(wire.account==='own_operator_a'){
   if(same.length!==1||String(same[0].id)===old.operatorId)throw Error('SAME_PERSON_MUST_HAVE_NEW_FINAL_OPERATOR_NOT_OLD_FIRST_OPERATOR');
  }else if(same.length)throw Error('OTHER_OR_SIGN_CANDIDATE_MUST_NO_LONGER_HAVE_THIS_PENDING_INSTANCE');
  const beforeAudit=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
  for(let round=0;round<2;round++){
   const requestStart=http.length;
   if(round===0)await send('Page.navigate',{url:target.href},session);
   else{const oldLoader=(await send('Page.getFrameTree',{},session)).frameTree.frame.loaderId;await send('Page.reload',{ignoreCache:true},session);await until(async()=>(await send('Page.getFrameTree',{},session)).frameTree.frame.loaderId!==oldLoader);}
   await until(()=>http.slice(requestStart).some(x=>/\\/Engine\\/FlowBefore\\/[^/]+$/.test(x.path)&&x.httpStatus===200&&x.businessCode===200));
   await until(()=>evaluate('document.querySelector(".audit-content[role=status]")?.textContent.includes("当前任务暂不可审批")===true'));
   await until(()=>evaluate('!!document.querySelector(".left-content .form-content")'));
   if(!await evaluate('!document.querySelector(".audit-content .audit-form")&&!document.querySelector(".left-content input:not(:disabled),.left-content textarea:not(:disabled)")'))throw Error('OLD_NODE_MUST_KEEP_BUSINESS_READONLY_AND_NEVER_OFFER_APPROVAL');
   cases.push({case:'old-operator-detail-and-refresh-refuse-approval-'+wire.account+'-'+round,passed:true,sameProcessHasDifferentCurrentOperator:wire.account==='own_operator_a'});
  }
  if(http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length!==beforeAudit)throw Error('STALE_DETAIL_MUST_NOT_SEND_APPROVAL');
  const task=await ownTask();if(task.flowId!==context.flowId||task.infoId!==context.eventId||task.uploadUrl!==context.uploadedPath||!feedbackMatches(task))throw Error('STALE_DETAIL_MUST_KEEP_SAME_TASK_EVENT_FILE_FEEDBACK');
  await fs.writeFile(O+'/old-operator-visibility-observation.json',JSON.stringify({passed:true,normalOwnUser:true,oldOperatorIDMatchedSavedRoute:true,newOperatorOnSameProcessPresent:wire.account==='own_operator_a',otherCandidateHasNoPending:wire.account==='own_reviewer_b',initialAndRefreshedOldLinkOfferNoApproval:true,actualPendingUnavailableNotice:true,approvalRequestsSent:0,taskEventFileFeedbackRetained:true},null,2));
 }
'''
browser=browser[:start]+stale+browser[end:]
browser=swap(browser,' if(!wire.expectEmptyFlowRejection){ const endpoint=',' if(!wire.stalePendingLink&&!wire.expectEmptyFlowRejection){ const endpoint=')
start=browser.index("  if(wire.phaseName==='operator-waiting-parallel-b'){\n   const actualActions=");end=browser.index("   if(wire.phaseName==='reviewer-final'",start)
capture='''  if(['operator-added','reviewer-preview'].includes(wire.phaseName)){
   const expected=['a5310000000000000000000000000064--user','a5310000000000000000000000000065--user'];const actual=nativeNodeProperties.approvers;
   if(nativeNodeProperties.counterSign!==0||nativeNodeProperties.title!=='OWN_APPROVE'||!Array.isArray(actual)||actual.length!==2||!expected.every(x=>actual.includes(x)))throw Error('ACTUAL_PROVIDER_TWO_OR_SIGN_CANDIDATES_AND_FIRST_NODE_REQUIRED');
   const relativeURL=await evaluate('location.pathname+location.search'),u=new URL(relativeURL,wire.base),operatorId=u.searchParams.get('id');
   if(u.pathname!=='/zhumadian/emergency/workflow/flowTodo/detail'||!operatorId||!/^[0-9a-f-]{16,64}$/.test(operatorId))throw Error('OWN_NORMAL_PENDING_ROUTE_OPERATOR_REQUIRED');
   context.oldPendingLinks={...(context.oldPendingLinks||{}),[wire.account]:{relativeURL,operatorId}};await fs.writeFile(root+'/workflow-context.private.json',JSON.stringify(context));
   await fs.writeFile(O+'/native-or-sign-node.json',JSON.stringify({counterSign:0,title:nativeNodeProperties.title,ownApprovers:2,oldOperatorLinkSaved:true,normalRole:wire.account},null,2));
   cases.push({case:'actual-two-candidate-or-sign-first-node-and-normal-old-link-saved-'+wire.account,passed:true});
  }
  if(wire.approveOnce){
'''
browser=browser[:start]+capture+browser[end:]
browser=browser.replace('SECOND_COUNTERSIGN_APPROVAL_MUST_ADVANCE_TO_FINAL_NODE','ONE_OR_SIGN_APPROVAL_MUST_ADVANCE_TO_FINAL_NODE')
start=browser.index("  const first=nativeRecords.filter",browser.index(" if(wire.phaseName==='operator-completed-readback')"));end=browser.index('\n }\n if(exceptions.length)',start)
browser=browser[:start]+'''  const first=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_operator-added'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  const final=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-final'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  if(first.length!==1||final.length!==1||Number(first[0].handleTime)>Number(final[0].handleTime))throw Error('OR_SIGN_FIRST_AND_FINAL_OPINIONS_EXACTLY_ONCE_AND_TIME_ORDER_REQUIRED');
  if(nativeRecords.some(x=>String(x.handleStatus)==='10'||x.handleOpinion==='OWN_R165_reviewer-after-added'))throw Error('OR_SIGN_MUST_NOT_INVENT_ADDSIGN_OR_SECOND_REVIEWER_OPINION');
  await fs.writeFile(O+'/or-sign-and-old-links-observation.json',JSON.stringify({oneOrSignCandidateAdvancedToFinalNode:true,firstAndFinalDistinctOpinionsExactlyOnce:true,actualTimeOrderMatched:true,otherCandidateDidNotSubmitApproval:true,nonTargetApprovalCreatedNoAddsignHistory:true,taskEventFeedbackAttachmentRetained:true,wholeNangangAcceptanceClaimed:false},null,2));
  cases.push({case:'or-sign-first-and-final-opinions-time-order-file-feedback-and-no-second-human-approval',passed:true});
'''+browser[end:]
save('verify_native_or_sign_r216_20261103.mjs',browser)
host=(T/'verify_full_controller_parallel_countersign_r215_20261103.py').read_text(encoding='utf-8').replace('r215','r216').replace('R215','R216').replace('r106','r107').replace('OwnParallelWorkflowReadback','OwnOrSignWorkflowReadback').replace('verify_native_parallel_countersign_r216','verify_native_or_sign_r216')
start=host.index('        phases=[');end=host.index('\n        state_source=',start)
host=host[:start]+"        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('reviewer-preview','own_reviewer_b','reviewer',False,False),('operator-added','own_operator_a','reviewer',True,False),('operator-stale-first-node','own_operator_a','reviewer',False,False),('reviewer-stale-first-node','own_reviewer_b','reviewer',False,False),('reviewer-final','own_operator_a','reviewer',True,False),('reviewer-handled-readback','own_operator_a','reviewer',False,False),('operator-completed-readback','own_operator_a','operator',False,False)]"+host[end:]
host=swap(host,"'handledReadback':label=='reviewer-handled-readback'","'handledReadback':label=='reviewer-handled-readback','stalePendingLink':label in ['operator-stale-first-node','reviewer-stale-first-node']")
start=host.index("        opinion=read(root/'workflow-browser-operator-completed-readback/");end=host.index("        dump(root/'ready-checks.json'",start)
host=host[:start]+'''        opinion=read(root/'workflow-browser-operator-completed-readback/or-sign-and-old-links-observation.json')
        assert opinion['oneOrSignCandidateAdvancedToFinalNode'] and opinion['firstAndFinalDistinctOpinionsExactlyOnce'] and opinion['actualTimeOrderMatched'] and opinion['nonTargetApprovalCreatedNoAddsignHistory']
        for name in ['operator-stale-first-node','reviewer-stale-first-node']:
            old=read(root/('workflow-browser-'+name)/'old-operator-visibility-observation.json');assert old['passed'] and old['initialAndRefreshedOldLinkOfferNoApproval'] and old['approvalRequestsSent']==0
        checks['actualOrSignAdvancementAndBothOldOperatorLinksAfterDifferentNextNodePassed']=True
'''+host[end:]
host=host.replace('native-parallel-countersign-regression','native-or-sign-stale-operator-regression').replace('TwoApproverCountersign','TwoCandidateOrSign').replace('ordinaryCountersignDidNot','ordinaryOrSignDidNot').replace('actualCreateFeedbackParallelCountersignAndFinalApprovalBrowsersPassed','actualCreateFeedbackOrSignStaleOperatorsAndFinalApprovalBrowsersPassed')
save('verify_full_controller_or_sign_r216_20261103.py',host)
runner=(T/'run_parallel_countersign_r215_20261103.py').read_text(encoding='utf-8').replace('r215','r216').replace('r106','r107').replace('verify_full_controller_parallel_countersign_r216','verify_full_controller_or_sign_r216');save('run_or_sign_r216_20261103.py',runner)
print(json.dumps({'suitePrepared':True,'attempt':'r107','originalMode':0,'browserPhases':9,'bothOldOperatorLinksAndTheirReloadsRequired':True,'oneCurrentSameProcessDifferentOperatorRequired':True,'noNewProductOrPublicChanges':True,'testNotYetStarted':True}))
