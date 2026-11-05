"""Read completed receipts and restored hashes; emit only a workspace checkpoint.
Does not execute the approval-blocked file verifier, create program links, call
admin process APIs, mutate project files, or use an alternative execution route.
"""
from pathlib import Path
import ast,datetime,hashlib,json
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application'
J=lambda p:json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p)
 if not p.is_file():return None
 with p.open('rb')as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 return {'bytes':p.stat().st_size,'sha256':digest}
outp=V/'postfix-verified-checkpoint-r1012.json';assert not outp.exists()
first=J(R/'work/ev1004/browser/first-start/result.json');resume=J(R/'work/ev1010/browser/normal-restart/result.json')
assert first['passed']and resume['passed']and not first['APIsMocked']and not resume['APIsMocked']
firstcases={x['case']:x['passed']for x in first['cases']};resumecases={x['case']:x['passed']for x in resume['cases']}
assert firstcases['failed-save-keeps-editor-and-input-and-shows-failure']and firstcases['failed-save-does-not-resurrect-deleted-record']
assert resumecases['original-detail-UI-observes-real-null-and-displays-failure-notice']and resumecases['invalid-detail-does-not-corrupt-default-form-object']and resumecases['read-only-probe-business-mutations-zero']
assert first['eventCreatesObserved']==1 and resume['eventCreatesObserved']==0
terminals=[];pointers=[]
for n in [1004,1010]:
 z=R/('work/ev'+str(n));p=J(z/('verified-event-crud-r'+str(n)+'.json'))
 assert p['codeRestored']and p['privateConfigurationRestored']and p['originalCurrentPointerRestored']
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and t['normalOwnedShutdown']and set(t['exitCodes'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in t['exitCodes'].values())for t in p['terminals'])
 terminals.extend(p['terminals'])
 snapshot=J(z/'pointer-snapshot/snapshot.private.json');assert snapshot['phase']=='restored'and pin(G/'UserData/OriginalServer/current-run.json')==snapshot['before']
 cfg=J(z/'event-config/journal.private.json');assert cfg['phase']=='restored'and pin(G/'private/server-configuration.json')==cfg['before']['private/server-configuration.json']
 assert J(z/'code-transaction/journal.json')['phase']=='restored'
 pointers.append({'attempt':n,'originalPointerAndConfigurationHashMatched':True})
plan=J(R/'Document/Deployment/event_crud_native_r1010_20261105/full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for n,p in plan['retiredKnownFrontendPaths'].items():rows[n]={'before':p}
for n,p in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():rows[n]={'before':p}
for n,row in rows.items():assert pin(G/n)==row['before'],'CURRENT_RESTORED_PROGRAM_DRIFT:'+n
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert pin(G/'release-manifest.json')['sha256']==plan['baseOwnedReleaseSHA256']
assert J(R/'work/ev1004/event-context.private.json')['phase']=='delete-and-false-save-verified'
script=V/'verify_r48_real_file_contract_r1008.py';ast.parse(script.read_text('utf8'))
native=J(R/'work/ev1010/verified-event-crud-r1010.json');assert native['passed']
out={
 'at':datetime.datetime.now().astimezone().isoformat(),'passedAsCompletedNativeUIAndReadOnlyRestoreAudit':True,
 'normalCreateEditDeleteCancelConfirmAndFalseSaveInputRetentionPassed':True,
 'normalRestartDeletedListNullAPIAndActualMissingDetailFormGuardPassed':True,
 'selectedUIAssertionsIncludingRepeats':len(first['cases'])+len(resume['cases']),
 'firstStageInheritedRestartCaseLabelIsSameLiveEditorReadbackNotUsedAsRestartEvidence':True,
 'readOnlyResumeBroadInheritedCRUDFieldNamesNotUsedAsStandaloneCRUDProof':True,
 'oneNewRepairValidationEventAcrossBothAttempts':True,'newEventWritesInReadOnlyResume':0,'APIsMocked':False,
 'actualNormalSixComponentLifecycles':len(terminals),'allActualControllersAndComponentsExited0AndJobs0':True,
 'currentProgramAndCachePreimageHashesMatched':len(rows),'currentOriginalConfigurationInstallationAndPointersMatched':True,
 'pointerAudits':pointers,'globalCIMNotRepolledDuringApprovalOutage':True,
 'R48MetadataUnitContract':{'passed':J(R/'Document/Deployment/event_result_runtime_r1000_20261105/verified-metadata-contract-r1002.json')['passed'],'checks':36,'programFileIOStubbedInThatUnitTest':True},
 'approvalBlockedAction':{'script':str(script),'scriptSHA256':pin(script)['sha256'],'executed':False,'reason':'automatic approval review could not complete because usage limit was reached; not a safety determination','mustNotBypassApprovalCheck':True,'expectedFixtureRootExists':(R/'work/f48').exists()},
 'fullRealFileVerifierPassed':False,'sparsePublicApplyAndRecoveryValidated':False,'publicIISOrR48DeploymentPassed':False,
 'fixedR47PackageChanged':False,'R47UserLastScreenshotOnlyPartialPreflightFinalResultStillPending':True,
 'newProjectDocumentationAndLocalGitUpdateAfterR999NotPerformedDueApprovalOutage':True,
 'lastLocalCommits':{'application':'ebc445bf4e3df416e81abc7ef7cd5a16cbc1dafd','engine':'ccd36aecd56b87b3a8a5f4012fa952de3011f6a1'},
 'nextAfterReviewAvailabilityRestored':['Run the exact R1008 real-file verifier once if its fixture root is absent; never replay unknown or live work.',
 'Independently audit all new program/source links and successful runs; clean only verified own temporary directories.',
 'Persist R1000-R1012 evidence and D74 receipt to project documentation and exact existing local branches.',
 'Finish sparse update normal/fault recovery and transport package before any new public payload request.'],
 'goalStatus':'active','fullCloneReady':False,'rawCredentialValuesEmitted':False}
outp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'nativeUIAssertionsIncludingRepeats':out['selectedUIAssertionsIncludingRepeats'],'actualNormalSixComponentLifecycles':len(terminals),'currentRestoredCodeCachePaths':len(rows),'approvalBlockedVerifierExecuted':False,'projectOrGitWritten':False},ensure_ascii=False))
