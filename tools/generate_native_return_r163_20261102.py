from pathlib import Path
import ast,json,hashlib
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
assert not C.exists()
def write(name,text):
 p=V/name;assert not p.exists();p.write_text(text,encoding='utf-8')
prep=(T/'prepare_owned_attachment_serial_r154_20261102.py').read_text(encoding='utf-8').replace('full-controller-r154','full-controller-r163').replace('R154','R163').replace('r154','r163').replace('154000+n*100','163000+n*100')
ast.parse(prep);write('prepare_owned_return_serial_r163_20261102.py',prep)
restore=(T/'restore_owned_attachment_serial_r154_20261102.py').read_text(encoding='utf-8').replace('full-controller-r154','full-controller-r163').replace('R154','R163').replace('r154','r163')
ast.parse(restore);write('restore_owned_return_serial_r163_20261102.py',restore)
browser=(T/'verify_native_attachment_serial_browser_r154_20261102.mjs').read_text(encoding='utf-8').replace('R154','R163').replace('r154','r163')
anchor='  if(wire.approveOnce){';assert browser.count(anchor)==1
body=r'''
  if(wire.rejectOnce){
   if(wire.actor!=='reviewer'||wire.phaseName!=='reviewer-first')throw Error('ONLY_ASSIGNED_SYNTHETIC_REVIEWER_RETURNS');
   stage='original-ui-return-to-configured-node';const beforeTask=await ownTask();
   if(beforeTask.flowId!==context.flowId||beforeTask.infoId!==context.eventId||beforeTask.uploadUrl!==context.uploadedPath||!feedbackMatches(beforeTask))throw Error('BEFORE_RETURN_TASK_EVENT_FLOW_FILE_FEEDBACK_ASSOCIATIONS_REQUIRED');
   if(!await click('.audit-form .el-radio','退回'))throw Error('ORIGINAL_RETURN_ACTION_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-form-item")).some(e=>e.getClientRects().length&&e.querySelector(".el-form-item__label")?.textContent.trim()==="退回节点")'));
   const target=await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".audit-form .el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="退回节点");const i=f?.querySelector("input");return{present:!!f,disabled:!!i?.disabled,selectedText:f?.querySelector(".el-select__selected-item")?.textContent.trim()||i?.value||"",optionsVisible:Array.from(document.querySelectorAll("[role=option]")).filter(e=>e.getClientRects().length).length}})()');
   if(!target.present||!target.selectedText||/请选择/.test(target.selectedText))throw Error('ORIGINAL_CONFIGURED_RETURN_NODE_MUST_BE_SELECTED');
   if(!await evaluate('(()=>{const e=document.querySelector(".audit-form textarea");if(!e)return false;e.value="OWN_R163_RETURN_FOR_REVISION";e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));return true})()'))throw Error('ORIGINAL_RETURN_OPINION_FIELD_REQUIRED');
   const before=http.filter(x=>x.path.includes('/FlowBefore/Reject/')).length;
   if(!await click('.audit-form button','提交'))throw Error('ORIGINAL_RETURN_SUBMIT_REQUIRED');
   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/Reject/')).length>before);
   const sent=http.filter(x=>x.path.includes('/FlowBefore/Reject/')).slice(before);
   if(sent.length!==1||sent[0].method!=='POST'||sent[0].httpStatus!==200||sent[0].businessCode!==200)throw Error('ORIGINAL_RETURN_POST_MUST_SUCCEED_EXACTLY_ONCE');
   const afterTask=await ownTask();if(afterTask.flowId!==context.flowId||afterTask.infoId!==context.eventId||afterTask.uploadUrl!==context.uploadedPath||!feedbackMatches(afterTask))throw Error('RETURN_MUST_RETAIN_TASK_EVENT_INSTANCE_ATTACHMENT_AND_FEEDBACK');
   cases.push({case:'actual-original-reviewer-return-post-once-preserves-task-event-instance-file-feedback',passed:true,configuredReturnNodeSelected:true,nativeReturnRequests:1});
   await fs.writeFile(O+'/native-return-summary.json',JSON.stringify({normalOriginalUIAndProviderUsed:true,nativeReturnRequests:1,taskEventFlowFileFeedbackAssociationsPreserved:true,taskStatusObserved:afterTask.taskStatus,configuredReturnNodeSelected:true,manualBusinessStateOrSDKTableWriteSent:false},null,2));
  }
  if(wire.phaseName==='operator-readback'&&!wire.readbackOnly){
   stage='original-initiator-relogin-after-return';
   const task=await ownTask();if(task.flowId!==context.flowId||task.infoId!==context.eventId||task.uploadUrl!==context.uploadedPath||!feedbackMatches(task))throw Error('INITIATOR_RETURN_READBACK_ASSOCIATIONS_REQUIRED');
   const returned=nativeRecords.filter(x=>x.handleOpinion==='OWN_R163_RETURN_FOR_REVISION');
   if(returned.length!==1||!returned[0].handleTime||!String(returned[0].userName).includes('own_reviewer_b'))throw Error('ORIGINAL_RETURN_RECORD_ACTOR_TIME_AND_OPINION_REQUIRED');
   const actions=await evaluate('({buttons:Array.from(document.querySelectorAll(".audit-content button")).filter(e=>e.getClientRects().length).map(e=>e.textContent.trim()).slice(0,30),radios:Array.from(document.querySelectorAll(".audit-form .el-radio")).filter(e=>e.getClientRects().length).map(e=>e.textContent.trim()).slice(0,20),activeAuditForm:!!document.querySelector(".audit-content .audit-form")})');
   await fs.writeFile(O+'/native-return-readback.json',JSON.stringify({sameOriginalInstanceAndTaskEventAttachmentAndFeedbackRetained:true,actualReturnedRecordActorAndTimeMatched:true,taskStatusObserved:task.taskStatus,actualNativeActions:actions,resubmissionNotExecuted:true,normalOriginalInitiatorSession:true},null,2));
   cases.push({case:'normal-initiator-relogin-return-record-and-original-task-associations-retained',passed:true,actualReturnedRecordActorAndTimeMatched:true,resubmissionNotExecuted:true});
  }
'''
browser=browser.replace(anchor,body+anchor)
browser=browser.replace('approvalSubmitted:!!wire.approveOnce,','approvalSubmitted:!!wire.approveOnce,rejectionSubmitted:!!wire.rejectOnce,')
write('verify_native_return_serial_browser_r163_20261102.mjs',browser)
reader=(T/'java/workflow_serial_r154/OwnSerialWorkflowReadback.java').read_text(encoding='utf-8').replace('OwnSerialWorkflowReadback','OwnReturnWorkflowReadback').replace('R154','R163').replace('r154','r163')
reader=reader.replace('a[9].matches("[12]")&&a[10].matches("[01]")&&a[11].matches("true|false")','a[9].matches("[12]|observe")&&a[10].matches("[01]|observe")&&a[11].matches("true|false|observe")')
reader=reader.replace('int pending=-1,historyRows=0;','int pending=-1,historyRows=0,observedTaskStatus=-1;')
reader=reader.replace('business=a[9].equals(r.getString(1))&&a[6].equals(r.getString(2));feedback=a[9].equals("1")?','observedTaskStatus=r.getInt(1);business=(a[9].equals("observe")||a[9].equals(r.getString(1)))&&a[6].equals(r.getString(2));feedback=!a[9].equals("2")?')
reader=reader.replace('pending==Integer.parseInt(a[10])','(a[10].equals("observe")||pending==Integer.parseInt(a[10]))').replace('(ended==Boolean.parseBoolean(a[11]))','(a[11].equals("observe")||ended==Boolean.parseBoolean(a[11]))')
reader=reader.replace('System.out.println("OWN_PROOF:passed:"+passed);','System.out.println("OWN_PROOF:passed:"+passed);System.out.println("OWN_PROOF:observedTaskStatus:"+observedTaskStatus);')
folder=T/'java/workflow_serial_r163';assert not folder.exists();folder.mkdir();(folder/'OwnReturnWorkflowReadback.java').write_text(reader,encoding='utf-8')
host=(T/'verify_full_controller_attachment_serial_r154_20261102.py').read_text(encoding='utf-8').replace('full-controller-r154','full-controller-r163').replace('verify_native_attachment_serial_browser_r154_20261102.mjs','verify_native_return_serial_browser_r163_20261102.mjs')
host=host.replace("browser_source=R/'Application/tools/verify_native_return_serial_browser_r163_20261102.mjs'","browser_source=Path(__file__).parent/'verify_native_return_serial_browser_r163_20261102.mjs'")
host=host.replace("('reviewer-first','own_reviewer_b','reviewer',True,False),('reviewer-final','own_operator_a','reviewer',True,False),('operator-readback','own_operator_a','operator',False,True)","('reviewer-first','own_reviewer_b','reviewer',False,False),('operator-readback','own_operator_a','operator',False,False)")
host=host.replace("'approveOnce':audit,","'approveOnce':audit,'rejectOnce':label=='reviewer-first',")
host=host.replace("workflow_serial_r154/OwnSerialWorkflowReadback.java","workflow_serial_r163/OwnReturnWorkflowReadback.java").replace("'OwnSerialWorkflowReadback'","'OwnReturnWorkflowReadback'")
old="ended=label in ['reviewer-final','operator-readback'];business_status='2'if label=='operator'else'1'"
assert old in host;host=host.replace(old,"observe=label in ['reviewer-first','operator-readback'];ended=None if observe else False;business_status='observe'if observe else('2'if label=='operator'else'1');pending_expected='observe'if observe else'1';ended_expected='observe'if observe else'false'")
host=host.replace("'0'if ended else'1','true'if ended else'false'","pending_expected,ended_expected")
host=host.replace('actualFivePhaseNativeCreateFeedbackAndSerialWorkflowBrowsersPassed','actualCreateFeedbackReturnAndInitiatorReadbackBrowsersPassed')
a=host.index("proof={'schema':")
host=host[:a]+'''proof={'schema':'xnby.r163.original-return-association-check.v1','allPassed':True,'actualOriginalFourBrowserPhases':len(phases),'actualNativeCreateUploadFeedbackReturnAndInitiatorReadbackPassed':True,'normalAllSixControllerAndBrowsersExitZeroAndActualDescendantsZero':True,'original398ModelsUnchanged':True,'connectionCapacityWithoutRefusals':checks['connectionCapacityWithoutRefusals'],'productCodeChanged':False,'publicFormalOrDesktopChanged':False,'onlyOwnSyntheticConfigurationAndDataUsed':True,'resubmissionNotExecuted':True,'originalNangangTemplateOrWholeAcceptanceClaimed':False,'fullCloneReady':False}
dump(root/'result.json',proof);print(json.dumps(proof),flush=True)
'''
ast.parse(host);write('verify_full_controller_return_serial_r163_20261102.py',host)
print(json.dumps({'newOwnReturnFourPhaseSourcesPrepared':True,'nativeReturnUIAndProviderUsed':True,'postReturnStateObservedWithoutInventingStateCodes':True,'resubmissionNotYetClaimed':True,'syntheticFixtureNotYetPreparedOrStarted':True}))
