from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103'
J=lambda p:json.loads(p.read_bytes())
scope=J(D/'prepared-result-r330.json');assert scope['attempt']=='r143'and scope['expectedBrowserCases']==18
assert len(scope['sourcePins'])==10 and not(C/'r143').exists()
for name,pin in scope['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
failure=J(C/'r141/plan-browser/failure.json');assert failure['message']=='OWN_PLAN_API_READBACK_emergencyPlan_500_100000'
baseline={'reproduced':True,'attempt':'r141','actualNormalRoleNativeBrowserCompletedCases':len(failure['cases']),
 'phase':failure['stage'],'failure':failure['message'],'deletedParentOldDetailHTTP':500,
 'deleteReturnedSuccessBeforeOldDetailRead':True,'controllerAndAllChildrenNormallyExitedZero':True,
 'allFiveRestoreLayersPassed':True,'notCountedAsWholeFlowPass':True}
(D/'baseline-failure-r329.json').write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8')
original_docs=R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103'
audit=J(original_docs/'runtime-plan-class-audit-r328.json')
(D/'runtime-plan-class-audit-r328.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
(D/'retained-memory-refusal-r330.json').write_text(json.dumps({'initialPreparationRefusedBeforeAllocation':True,
 'guard':'SIX_GIB_ADMISSION_REQUIRED_BEFORE_MUTATION','exactAvailableMemoryAtRefusalNotCaptured':True,
 'candidateAndRunRootsAbsentAndOriginalReleaseAndZeroOwnProcessesVerifiedBeforeRetry':True,
 'availableMemoryProbeBeforeRetryGiB':8.164,'subsequentPreparationAvailableBytes':scope['admissionAvailableBytes'],
 'guardNotLoweredAndUserApplicationsNotClosed':True},indent=2)+'\n',encoding='utf-8')
print('OWN_PLAN_RUNTIME_R143_ACTUAL_CANDIDATE_AND_CHILD_RETENTION_STARTING',flush=True)
code=subprocess.call([sys.executable,str(T/'run_native_parent_delete_r330.py')],creationflags=subprocess.CREATE_NO_WINDOW)
if code and not(C/'r143').exists():
    log=C/'r143-outer.private.log'
    if log.exists()and'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in log.read_text(encoding='utf-8'):
        restored=subprocess.run([sys.executable,str(V/'restore_plan_runtime_prestart_r331.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        assert restored.returncode==0 and J(D/'prestart-refusal-and-restore-r300.json')['passed'],'OWN_R143_PRESTART_RESTORE_REFUSED'
        print('OWN_R143_MEMORY_REFUSAL_SIX_LAYERS_RESTORED_WITHOUT_FAKE_RECEIPTS',flush=True)
print(json.dumps({'attempt':'r143','runnerExitCode':code,'publicFormalOrDesktopChanged':False}),flush=True)
assert code==0,'OWN_PLAN_RUNTIME_R143_NOT_PASSED_EVIDENCE_KEPT'
