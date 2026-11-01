"""Independently inspect real baseline/candidate browser, controller and source evidence."""
from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r123';W=R/'work/user_feedback_20261031'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=read(C/'r1/workflow-browser-reviewer/failure.json')
assert b['message']=='NATIVE_APPROVAL_DOUBLE_CLICK_MUST_SEND_ONCE'
assert next(x for x in b['cases']if x['case']=='actual-native-audit-double-click-attempt-count')['requests']==2
audits=[x for x in b['http']if '/FlowBefore/Audit/'in x['path']]
assert len(audits)==2 and [x['businessCode']for x in audits]==[200,400] and all(x['httpStatus']==200 for x in audits)
for attempt in ['r1','r2','r3']:
    terminal=read(C/attempt/'controller-terminal.json');receipt=read(C/attempt/'scoped-controller-receipt.json')
    assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose'] and not terminal['forceTerminationUsed']
    assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']
    assert set(receipt['exitCodesBeforeJobClose'])=={'mysql','redis','store','platform','business','gateway'}
    assert all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
    actors=['operator','reviewer']if attempt=='r1'else['operator','reviewer','operator-readback']
    source=C/attempt/'workflow-browser-source.mjs';raw=source.read_bytes()
    assert b'Fetch.fulfillRequest'not in raw and b'/eventTask/updateById'not in raw and b'/eventTask/callback'not in raw
    for actor in actors:
        assert read(C/attempt/('workflow-browser-'+actor+'-started.json'))['sourceSHA256']==sha(source)
        terminal=read(C/attempt/('workflow-browser-'+actor)/'browser-terminal.json');assert terminal['normalBrowserClosed']and not terminal['forceTerminationUsed']
for attempt,revision in [('r2','r4'),('r3','r5')]:
    proof=read(C/attempt/'result.json');assert proof['allPassed']and proof['actualTenReadinessChecksPassed']and not proof['publicOrFormalChanged']
    assert read(C/attempt/'schema-after.json')==read(C/'schema-before.json')
    assert proof['controllerSHA256']=='8b6006fac79e096939bfb7b2cffc333c1bcd39dc01f9d43070c68dee4f402660'
    assert proof['jobSHA256']=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
    build=read(W/('emergency-workflow-source-'+revision)/'independent-build-verification.json')
    assert build['compiledFiles']==338 and build['selectedSourceFiles']==234 and build['undeclaredSourceDifferences']==0
    for actor in ['operator','reviewer','operator-readback']:
        browser=read(C/attempt/('workflow-browser-'+actor)/'result.json');assert browser['passed']and not browser['exceptions']and not browser['completeNangangAcceptance']
        assert any(x['path'].endswith('/oauth/Login')and x.get('normalTokenReturned')and x.get('businessCode')==200 for x in browser['http'])
        cases={x['case']:x for x in browser['cases']}
        assert cases['actual-workflow-task-component-read-by-native-instance-and-rendered-read-only']['passed']
        assert cases['actual-initial-submitter-identity-not-current-approver']['passed']
        if attempt=='r3':
            state=cases['actual-existing-task-state-rendered-from-provided-entity-definition'];assert state['passed']and not state['persistentStateOrSchemaChanged']
            assert(state['state'],state['label'])==(('1','已处置')if actor=='operator-readback'else('2','处置中'))
    reviewer=read(C/attempt/'workflow-browser-reviewer/result.json');cases={x['case']:x for x in reviewer['cases']}
    for name in ['actual-invalid-required-transfer-no-mutation-and-unlocked-opinion-retained','actual-audit-transport-failure-visible-error-opinion-retained-unlocked-original-task-pending','actual-audit-submit-disabled-and-loading-during-real-pending-request','assigned-reviewer-real-ui-one-native-audit-and-original-callback-task-2-to-1']:
        assert cases[name]['passed']
    assert cases['actual-native-audit-double-click-attempt-count']['requests']==1
    assert cases['actual-native-audit-double-click-attempt-count']['retryAfterFailedTransport']
    audits=[x for x in reviewer['http']if '/FlowBefore/Audit/'in x['path']]
    assert len(audits)==2 and audits[0]['transportFailed']and 'httpStatus'not in audits[0]
    assert audits[1]['httpStatus']==200 and audits[1]['businessCode']==200
    assert not any('/FlowBefore/Transfer/'in x['path']for x in reviewer['http'])
    reopened=read(C/attempt/'workflow-browser-operator-readback/result.json');assert reopened['afterApprovalReadback']
    assert next(x for x in reopened['cases']if x['case']=='normal-initiator-relogin-completed-native-flow-and-read-only-task-state')['passed']
entity=R/'Application/work/tianjin_native_20261023/business_java/src/main/java/com/iemp/endanger/server/emergencyResponse/entity/EventTask.java'
assert '任务状态：0-待处置，1-已处置,2 处置中'in entity.read_text(encoding='utf-8')
closure=read(W/'emergency-workflow-source-r5/source-closure.json');assert len(closure['taskStateDisplayAdaptations'])==2
for rel,pin in closure['taskStateDisplayAdaptations'].items():
    assert not pin['persistentSchemaOrStateValueChanged']and pin['sourceEntitySHA256']==sha(entity)
    assert sha(W/'emergency-workflow-source-r5/source'/rel)==pin['adaptedSHA256']
    before=(W/'emergency-workflow-source-r4/source'/rel).read_bytes();after=(W/'emergency-workflow-source-r5/source'/rel).read_bytes()
    before=before.replace(b'\r\n',b'\n');after=after.replace(b'\r\n',b'\n')
    assert after.replace(',\n      { label: "处置中", value: "2" }'.encode('utf-8'),b'',1)==before
fixed=R/'Document/Deployment/public_test_unified_r23_20261101'
assert sha(fixed/'public-git-sync-manifest.json')=='184cab1fc01ecdcbccea96e39280a49fbd1f0d4f7e32c963fc3c55a6fbec88aa'
assert sha(fixed/'delivery-manifest.json')=='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
proof={'schema':'xnby.approval-resilience-r124.v1','passed':True,'baselineActualAuditAttempts':2,'baselineBusinessCodes':[200,400],'successfulCandidateNormalRoleBrowserRuns':6,'candidateRealApprovalRuns':2,'invalidRequiredActionSentNoMutation':True,'transportFailureBeforeServerOpinionRetainedAndUnlocked':True,'busyButtonDisabledWhileOriginalRequestPending':True,'retryDoubleClickRealSuccessfulAuditCountPerRun':1,'originalAutomaticCallbackAndFreshInitiatorReadback':True,'serverProcessedButResponseLostAccepted':False,'existingStatus2DetailLabelActualUIRuns':2,'completedStatus1DetailLabelActualUIRuns':1,'taskListStatusFilterActualUIStillPending':True,'persistentSchemaOrStateValuesChanged':False,'original398DefinitionsUnchanged':True,'allAutomatedChildrenNormallyExitedZero':True,'manualDisposalFeedbackOrRealNangangDefinitionAccepted':False,'fixedR23And163Unchanged':True,'publicDeploymentPerformed':False,'userManualRootsReadOrChanged':False,'fullCloneReady':False}
(C/'independent-approval-resilience-r124.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
