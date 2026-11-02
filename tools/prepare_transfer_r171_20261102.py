from pathlib import Path
import ast, hashlib, json, subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
def replace_once(s,old,new):
    assert s.count(old)==1,(old[:150],s.count(old))
    return s.replace(old,new)
def put(name,text):
    p=V/name;assert not p.exists();p.write_text(text,encoding='utf-8')
    if p.suffix=='.py':ast.parse(text)

# Reuse the existing explicit two-stage synthetic fixture, with a unique attempt ID.
# Keep its strict own-root / stopped-process / synthetic-config restore guards.
host=(A/'tools/verify_full_controller_return_serial_r163_20261102.py').read_text(encoding='utf-8')
host=replace_once(host,"browser_source=Path(__file__).parent/'verify_native_return_serial_browser_r163_20261102.mjs'","browser_source=Path(__file__).parent/'verify_native_transfer_browser_r171_20261102.mjs'")
start=host.index("        phases=[('operator',")
end=host.index("        state_source=",start)
host=host[:start]+'''        assert options.attempt=='r71' and options.variant=='combined' and not(options.closed_readback_only or options.return_existing_pending or options.resubmit_returned)
        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('reviewer-transfer','own_reviewer_b','reviewer',False,False),('reviewer-no-longer-assigned','own_reviewer_b','reviewer',False,False),('operator-transferred','own_operator_a','reviewer',True,False),('reviewer-final','own_operator_a','reviewer',True,False),('operator-completed-readback','own_operator_a','operator',False,False)]
'''+host[end:]
host=replace_once(host,"'rejectOnce':label=='reviewer-first'","'rejectOnce':False,'transferOnce':label=='reviewer-transfer','expectTransferredAbsence':label=='reviewer-no-longer-assigned','listsOnly':label=='reviewer-no-longer-assigned'")
host=replace_once(host,"observe=label in ['reviewer-first','operator-readback']","observe=label in ['reviewer-transfer','reviewer-no-longer-assigned']")
host=host.replace('actualCreateFeedbackReturnAndInitiatorReadbackBrowsersPassed','actualCreateFeedbackTransferAndTargetApprovalBrowsersPassed')
host=host.replace("'schema':'xnby.r163.original-return-association-check.v1'","'schema':'xnby.r171.original-transfer-association-check.v1'")
host=host.replace("'actualNativeCreateUploadFeedbackReturnAndInitiatorReadbackPassed':True","'actualNativeCreateUploadFeedbackTransferAndTargetApprovalPassed':True")
host=host.replace("'actualReturnResubmitAndTwoFinalReviewsCompleted':options.resubmit_returned","'actualTransferThenTwoReviewsCompleted':True")
put('verify_full_controller_transfer_r171_20261102.py',host)

browser=(A/'tools/verify_native_return_serial_browser_r163_20261102.mjs').read_text(encoding='utf-8')
browser=replace_once(browser,"'operator-completed-readback'].includes(wire.phaseName)","'operator-completed-readback','reviewer-transfer','reviewer-no-longer-assigned','operator-transferred'].includes(wire.phaseName)")
browser=replace_once(browser,"if(index<0)throw Error('OWN_PENDING_INSTANCE_NOT_IN_NATIVE_LIST');","if(wire.expectTransferredAbsence){if(index>=0)throw Error('TRANSFERRED_INSTANCE_STILL_IN_OLD_REVIEWER_PENDING_LIST');cases.push({case:'normal-original-reviewer-relogin-transferred-instance-absent-from-pending-list',passed:true});}else if(index<0)throw Error('OWN_PENDING_INSTANCE_NOT_IN_NATIVE_LIST');")
needle="  if(wire.rejectOnce){"
transfer=r'''  if(wire.transferOnce){
   if(wire.account!=='own_reviewer_b'||wire.phaseName!=='reviewer-transfer')throw Error('ONLY_OWN_ASSIGNED_REVIEWER_CAN_TRANSFER');
   stage='original-ui-transfer-required-target';
   if(!await click('.audit-form .el-radio','转审'))throw Error('ORIGINAL_TRANSFER_ACTION_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==="转审")'));
   await until(()=>evaluate('!!document.querySelector(".audit-form input[placeholder=请选择转审人员]")'));
   const before=http.filter(x=>x.path.includes('/FlowBefore/Transfer/')).length;
   if(!await click('.audit-form button','提交'))throw Error('TRANSFER_SUBMIT_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-form-item__error")).some(e=>e.textContent.includes("请选择人员"))'));
   if(http.filter(x=>x.path.includes('/FlowBefore/Transfer/')).length!==before)throw Error('EMPTY_TRANSFER_TARGET_MUST_NOT_POST');
   cases.push({case:'original-transfer-empty-target-blocked-before-request',passed:true});
   stage='original-ui-transfer-user-search-and-selection';
   if(!await evaluate('(()=>{const e=document.querySelector(".audit-form input[placeholder=请选择转审人员]");if(!e)return false;e.click();return true})()'))throw Error('TRANSFER_TARGET_INPUT_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-dialog")).some(d=>d.getClientRects().length&&d.querySelector("input[placeholder=请输入关键词查询]"))'));
   if(!await evaluate('(()=>{const d=Array.from(document.querySelectorAll(".el-dialog")).find(d=>d.getClientRects().length&&d.querySelector("input[placeholder=请输入关键词查询]"));const e=d?.querySelector("input[placeholder=请输入关键词查询]");if(!e)return false;e.value="own_operator_a";e.dispatchEvent(new Event("input",{bubbles:true}));return true})()'))throw Error('ORIGINAL_USER_SEARCH_INPUT_REQUIRED');
   if(!await evaluate('(()=>{const d=Array.from(document.querySelectorAll(".el-dialog")).find(d=>d.getClientRects().length&&d.querySelector("input[placeholder=请输入关键词查询]"));const e=d?.querySelector(".el-input-group__append button");if(!e)return false;e.click();return true})()'))throw Error('ORIGINAL_USER_SEARCH_BUTTON_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-dialog .user-body .user-con:first-child .list-item .name")).some(e=>e.getClientRects().length&&e.textContent.trim()==="own_operator_a")'));
   if(!await evaluate('(()=>{const e=Array.from(document.querySelectorAll(".el-dialog .user-body .user-con:first-child .list-item .name")).find(e=>e.getClientRects().length&&e.textContent.trim()==="own_operator_a");if(!e)return false;e.closest(".list-item").click();return true})()'))throw Error('EXACT_OWN_TRANSFER_RECIPIENT_REQUIRED');
   if(!await evaluate('(()=>{const d=Array.from(document.querySelectorAll(".el-dialog")).find(d=>d.getClientRects().length&&d.querySelector("input[placeholder=请输入关键词查询]"));const b=d?Array.from(d.querySelectorAll(".el-dialog__footer button")).find(e=>e.textContent.trim()==="确认"):null;if(!b)return false;b.click();return true})()'))throw Error('ORIGINAL_USER_SELECTION_CONFIRM_REQUIRED');
   await until(()=>evaluate('document.querySelector(".audit-form input[placeholder=请选择转审人员]")?.value==="own_operator_a"'));
   if(!await evaluate('(()=>{const e=document.querySelector(".audit-form textarea");if(!e)return false;e.value="OWN_R171_TRANSFER_TO_OPERATOR";e.dispatchEvent(new Event("input",{bubbles:true}));return true})()'))throw Error('ORIGINAL_TRANSFER_OPINION_REQUIRED');
   stage='original-transfer-one-real-post';
   if(!await click('.audit-form button','提交'))throw Error('ORIGINAL_TRANSFER_SUBMIT_REQUIRED');
   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/Transfer/')).length>before);
   const sent=http.filter(x=>x.path.includes('/FlowBefore/Transfer/')).slice(before);
   if(sent.length!==1||sent[0].method!=='POST'||sent[0].httpStatus!==200||sent[0].businessCode!==200)throw Error('ORIGINAL_TRANSFER_POST_MUST_SUCCEED_ONCE');
   const t=await ownTask();if(t.flowId!==context.flowId||t.infoId!==context.eventId||t.uploadUrl!==context.uploadedPath||!feedbackMatches(t))throw Error('TRANSFER_MUST_RETAIN_TASK_EVENT_FLOW_ATTACHMENT_AND_FEEDBACK');
   cases.push({case:'original-user-selector-and-one-transfer-post-preserve-business-associations',passed:true,nativeTransferRequests:1,manualEngineOrBusinessStateWrites:false});
  }
'''
browser=replace_once(browser,needle,transfer+needle)
browser=replace_once(browser,"if(!nativeRecords.some(x=>x.handleOpinion==='OWN_R163_RETURN_FOR_REVISION'&&x.handleTime)||!nativeRecords.some(x=>x.handleOpinion==='OWN_R165_APPLICANT_RESUBMIT'&&x.handleTime))throw Error('ORIGINAL_RETURN_AND_RESUBMIT_RECORDS_REQUIRED');","if(!nativeRecords.some(x=>x.handleOpinion==='OWN_R171_TRANSFER_TO_OPERATOR'&&x.handleTime&&String(x.userName).includes('own_reviewer_b')))throw Error('ORIGINAL_TRANSFER_RECORD_ACTOR_TIME_AND_OPINION_REQUIRED');")
browser=browser.replace('completed-return-resubmit-two-review-chain-native-records-and-file-feedback-retained','completed-transfer-two-review-chain-native-records-and-file-feedback-retained')
put('verify_native_transfer_browser_r171_20261102.mjs',browser)

runner=(A/'tools/run_return_workflow_r163_20261102.py').read_text(encoding='utf-8')
runner=replace_once(runner,"attempt=sys.argv[1]if len(sys.argv)==2 else'r1';assert attempt in['r1','r2','r3'];","attempt='r71';assert len(sys.argv)==1;")
runner=replace_once(runner,'verify_full_controller_return_serial_r163_20261102.py','verify_full_controller_transfer_r171_20261102.py')
put('run_transfer_r171_20261102.py',runner)
node=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_transfer_browser_r171_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert node.returncode==0,node.stderr.decode()
print(json.dumps({'preparedSources':3,'syntaxPassed':True,'syntheticAttempt':'r71','productOrConfigurationChanged':False}))
