"""Check actual native outcomes, query-only recovery, original list filtering and lifecycle."""
from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r123';W=R/'work/user_feedback_20261031/emergency-workflow-source-r6';A=R/'_e/Application'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for attempt in ['r4','r5']:
 b=read(C/attempt/'workflow-browser-reviewer/failure.json');assert b['message']=='APPROVAL_RESPONSE_LOST_MUST_REFRESH_AUTHORITATIVE_STATE'
 case=next(x for x in b['cases']if x['case']=='real-success-response-lost-authoritative-completed-flow');assert case['realResponseObservedBeforeLoss']and case['activeApprovalFormStillShown']and not case['passed']
assert read(C/'r6/failure.json')['message']=='OWN_CONTROLLER_SCHEMA_AFTER_FAILED'
assert not(C/'r6/result.json').exists()
assert read(C/'r7/schema-reader-outcome.json')['exitCode']==0
assert read(C/'r9/schema-reader-outcome.json')['exitCode']==0
assert read(C/'r8/workflow-browser-reviewer/failure.json')['message']=='OWN_WORKFLOW_MENU_MISSING'
assert read(C/'r8/workflow-browser-reviewer/owned-page-diagnostic.private.json')['path'].endswith('/login')
for attempt in ['r4','r5','r6','r7','r8','r9']:
 terminal=read(C/attempt/'controller-terminal.json');receipt=read(C/attempt/'scoped-controller-receipt.json')
 assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed']
 assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']
 assert set(receipt['exitCodesBeforeJobClose'])=={'mysql','redis','store','platform','business','gateway'}and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 actors=['operator','reviewer']if attempt in ['r4','r5','r8']else['operator','reviewer','operator-readback']
 source=C/attempt/'workflow-browser-source.mjs';raw=source.read_bytes();assert b'Fetch.fulfillRequest'not in raw and b'/eventTask/callback'not in raw and b'/eventTask/updateById'not in raw
 for actor in actors:
  browser=C/attempt/('workflow-browser-'+actor)
  assert read(C/attempt/('workflow-browser-'+actor+'-started.json'))['sourceSHA256']==sha(source)
  assert read(browser/'browser-terminal.json')['normalBrowserClosed']
  if attempt not in ['r4','r5','r8']:assert read(browser/'result.json')['passed']
for attempt in ['r5','r6','r7','r8','r9']:
 b=read(C/attempt/'workflow-browser-operator/result.json');cases={c['case']:c for c in b['cases']}
 assert cases['actual-task-list-existing-state2-search-and-render']['passed']and cases['actual-task-list-search-reset-clears-state-and-name']['passed']
 filtered=[x for x in b['http']if x['path'].endswith('/eventTask/getPage')and x.get('taskStatusQuery')=='2']
 assert any(x['businessCode']==0 and x['ownTaskNameQueryMatched']and x['ownTaskReturned']and x['allReturnedTasksState2']for x in filtered)
for attempt in ['r6','r7']:
 b=read(C/attempt/'workflow-browser-reviewer/result.json');c=next(c for c in b['cases']if c['case']=='real-success-response-lost-authoritative-completed-flow')
 assert c['passed']and c['originalHTTPStatus']==200 and c['originalBusinessCode']==200 and not c['activeApprovalFormStillShown']
 assert len([x for x in b['http']if '/FlowBefore/Audit/'in x['path']])==1
 assert any(x.get('nativeFlowState')==2 for x in b['http']if x.get('templatePresent'))
 assert any(x.get('correctTaskFlowRead')and x.get('taskStatus')=='1'for x in b['http'])
b=read(C/'r7/workflow-browser-reviewer/result.json');assert next(c for c in b['cases']if c['case']=='failed-authoritative-read-keeps-opinion-and-double-recheck-sends-no-extra-audit')['passed']
b=read(C/'r9/workflow-browser-reviewer/result.json');cases={c['case']:c for c in b['cases']}
assert cases['actual-invalid-required-transfer-no-mutation-and-unlocked-opinion-retained']['passed']
assert cases['actual-audit-transport-failure-visible-error-opinion-retained-unlocked-original-task-pending']['passed']
assert cases['actual-native-audit-double-click-attempt-count']['requests']==1
assert cases['assigned-reviewer-real-ui-one-native-audit-and-original-callback-task-2-to-1']['passed']
assert any(x['path'].endswith('/FlowBefore/List/1')and x['businessCode']==200 for x in b['http'])
for attempt in ['r7','r9']:
 assert read(C/attempt/'result.json')['allPassed']and read(C/attempt/'schema-after.json')==read(C/'schema-before.json')
 reopened=read(C/attempt/'workflow-browser-operator-readback/result.json');assert reopened['afterApprovalReadback']
 assert next(x for x in reopened['cases']if x['case']=='normal-initiator-relogin-completed-native-flow-and-read-only-task-state')['passed']
build=read(W/'independent-build-verification.json');assert build['compiledFiles']==338 and build['selectedSourceFiles']==234 and build['uncertainOutcomeDeclaredChangedFiles']==2 and build['undeclaredSourceDifferences']==0
for name,pin in read(W/'build-result.json')['files'].items():assert sha(A/'frontend/emergency_pc'/name)==pin['sha256']
assert all(x['generatorReproducesActualBytes']and x['reverseToR5ByteExact']for x in read(C/'reconcile-source-generation-proof.json'))
before=next(x for x in read(C/'r5/workflow-browser-reviewer/failure.json')['http']if x.get('templatePresent'));after=read(C/'r5/workflow-browser-reviewer/owned-completed-native-shape.json')
assert before['noOperateAuth']is True and after['noOperateAuth']is True
fixed=R/'Document/Deployment/public_test_unified_r23_20261101';assert sha(fixed/'public-git-sync-manifest.json')=='184cab1fc01ecdcbccea96e39280a49fbd1f0d4f7e32c963fc3c55a6fbec88aa';assert sha(fixed/'delivery-manifest.json')=='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
proof={'schema':'xnby.workflow-outcome-reconcile-r126.v1','passed':True,'realLostSuccessBaselineRuns':2,'candidateActualNormalRoleBrowserRuns':9,'candidateWholeControllerAndSchemaPassedRuns':2,'r6UIOnlyPassedSchemaReadFailedPreserved':True,'r6SchemaReadFailureCauseStillUnconfirmed':True,'r8LoginRenderingRacePreservedAndDriverCorrected':True,'realNativeSuccessThenLostResponseRecovered':True,'failedFirstConfirmationReadDraftPreservedThenQueryOnly':True,'extraAuditPOSTAfterRecheck':0,'unprocessedRequestNativePendingAndSameNodeSafeRetryPassed':True,'realTaskListFilterAndResetBrowserRuns':5,'database398DefinitionsUnchangedOnR7R9':True,'allAttemptsNormalStopNoForce':True,'compiledFiles':338,'selectedSourceFiles':234,'assetReferences':1521,'compiledJSChecked':173,'changedSourceComponents':2,'generatorExactAndReverseProof':True,'noOperateAuthNotUsedAsApprovalPermission':True,'multiNodeCountersignTransferRejectFullMatrixAccepted':False,'realNangangDefinitionOrManualDisposalAccepted':False,'publicOrFormalOrUserManualDataChanged':False,'fullCloneReady':False}
(C/'independent-outcome-reconcile-r126.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
