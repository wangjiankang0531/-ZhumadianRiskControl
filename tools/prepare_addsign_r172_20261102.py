from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
def put(name,s):
    p=V/name;assert not p.exists();p.write_text(s,encoding='utf-8')
    if p.suffix=='.py':ast.parse(s)
host=(V/'verify_full_controller_transfer_r171_20261102.py').read_text(encoding='utf-8')
host=once(host,'verify_native_transfer_browser_r171_20261102.mjs','verify_native_addsign_browser_r172_20261102.mjs')
start=host.index("        assert options.attempt=='r71'")
end=host.index('        state_source=',start)
host=host[:start]+'''        assert options.attempt in ['r72','r73'] and options.variant=='combined' and not(options.closed_readback_only or options.return_existing_pending or options.resubmit_returned)
        add_type='1' if options.attempt=='r72' else '2'
        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('reviewer-addsign','own_reviewer_b','reviewer',False,False),('operator-added','own_operator_a','reviewer',True,False)]
        if add_type=='1':phases.append(('reviewer-after-added','own_reviewer_b','reviewer',True,False))
        phases += [('reviewer-final','own_operator_a','reviewer',True,False),('operator-completed-readback','own_operator_a','operator',False,False)]
'''+host[end:]
host=once(host,"'transferOnce':label=='reviewer-transfer','expectTransferredAbsence':label=='reviewer-no-longer-assigned','listsOnly':label=='reviewer-no-longer-assigned'","'addsignOnce':label=='reviewer-addsign','addsignType':add_type")
host=once(host,"observe=label in ['reviewer-transfer','reviewer-no-longer-assigned']","observe=label in ['reviewer-addsign','operator-added','reviewer-after-added']")
host=host.replace('actualCreateFeedbackTransferAndTargetApprovalBrowsersPassed','actualCreateFeedbackAddsignAndNativeSequenceBrowsersPassed').replace('actualNativeCreateUploadFeedbackTransferAndTargetApprovalPassed','actualNativeCreateUploadFeedbackAddsignAndTargetApprovalPassed').replace('xnby.r171.original-transfer-association-check.v1','xnby.r172.original-addsign-association-check.v1').replace("'actualTransferThenTwoReviewsCompleted':True","'actualAddsignAndRemainingReviewsCompleted':True,'addsignType':add_type")
put('verify_full_controller_addsign_r172_20261102.py',host)
browser=(V/'verify_native_transfer_browser_r171_20261102.mjs').read_text(encoding='utf-8')
browser=once(browser,"'operator-transferred'].includes(wire.phaseName)","'operator-transferred','reviewer-addsign','operator-added','reviewer-after-added'].includes(wire.phaseName)")
start=browser.index('  if(wire.transferOnce){');end=browser.index('  if(wire.rejectOnce){',start)
block=browser[start:end]
block=block.replace('wire.transferOnce','wire.addsignOnce').replace('reviewer-transfer','reviewer-addsign').replace('转审','加签').replace('/FlowBefore/Transfer/','/FlowBefore/freeApprover/').replace('OWN_R171_TRANSFER_TO_OPERATOR','OWN_R172_ADDSIGN_OPERATOR')
block=once(block,"   const before=http.filter",'''   if(!['1','2'].includes(wire.addsignType))throw Error('EXACT_ORIGINAL_ADDSIGN_TYPE_REQUIRED');
   const typeLabel=wire.addsignType==='1'?'审批前':'审批后';
   if(!await click('.audit-form .el-radio',typeLabel))throw Error('ORIGINAL_ADDSIGN_MODE_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==='+JSON.stringify(typeLabel)+')'));
   cases.push({case:'original-addsign-before-or-after-mode-selected',type:wire.addsignType,passed:true});
   const before=http.filter''')
block=block.replace('original-transfer-empty-target-blocked-before-request','original-addsign-empty-target-blocked-before-request').replace('original-user-selector-and-one-transfer-post-preserve-business-associations','original-user-selector-and-one-addsign-post-preserve-business-associations').replace('nativeTransferRequests:1','nativeAddsignRequests:1,addsignType:wire.addsignType')
browser=browser[:start]+block+browser[end:]
browser=once(browser,"nativeRecords.some(x=>x.handleOpinion==='OWN_R171_TRANSFER_TO_OPERATOR'","nativeRecords.some(x=>x.handleOpinion==='OWN_R172_ADDSIGN_OPERATOR'")
browser=browser.replace('completed-transfer-two-review-chain-native-records-and-file-feedback-retained','completed-addsign-native-records-and-file-feedback-retained')
browser=browser.replace("case:wire.phaseName==='operator-resubmit'?'original-applicant-resubmits-returned-start-node':wire.phaseName==='reviewer-again'?'first-review-after-return-retains-feedback':wire.phaseName==='reviewer-first'?'first-native-review-retains-existing-feedback':'final-native-review-completes-engine-and-retains-feedback'","case:'original-addsign-chain-one-native-approval-'+wire.phaseName")
put('verify_native_addsign_browser_r172_20261102.mjs',browser)
runner=(V/'run_transfer_r171_20261102.py').read_text(encoding='utf-8')
runner=once(runner,"attempt='r71';assert len(sys.argv)==1;","attempt=sys.argv[1]if len(sys.argv)==2 else'';assert attempt in ['r72','r73'];")
runner=once(runner,'verify_full_controller_transfer_r171_20261102.py','verify_full_controller_addsign_r172_20261102.py')
put('run_addsign_r172_20261102.py',runner)
run=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_addsign_browser_r172_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert run.returncode==0,run.stderr.decode()
print(json.dumps({'preparedSources':3,'syntaxPassed':True,'ownedAttempts':['r72','r73'],'beforeAndAfterAddsignOriginalModes':True,'productOrConfigurationChanged':False}))
