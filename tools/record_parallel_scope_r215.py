from pathlib import Path
import datetime,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/original_parallel_countersign_r215_20261103';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D.mkdir(exist_ok=False)
J=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=[]
for stage in ['r214','r215']:
 names += ['configure_owned_parallel_countersign_'+stage+'.py','prepare_personal_workflow_frontend_'+stage+'.py','restore_personal_workflow_frontend_'+stage+'.py','restore_production_history_runtime_'+stage+'.py','prepare_production_history_runtime_'+stage+'.py','OwnPersonalWorkflowMenuVisibility'+stage.upper()+'.java','OwnParallelWorkflowReadback'+stage.upper()+'.java','verify_native_parallel_countersign_'+stage+'_20261103.mjs','verify_full_controller_parallel_countersign_'+stage+'_20261103.py','run_parallel_countersign_'+stage+'_20261103.py']
assert len(names)==20 and all((T/n).is_file()for n in names)
pins={n:{'bytes':(T/n).stat().st_size,'sha256':sha(T/n)}for n in names}
assert sha(T/'original_public_test_update_r36_20261103_r2.py')=='67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca'
f=J(C/'r105/workflow-browser-operator-waiting-parallel-b/failure.json');assert f['message']=='INITIATOR_READBACK_MUST_NOT_APPROVE_WAITING_COUNTERSIGN'
assert J(C/'r105-outer-terminal.json')['actualDescendantsZeroBeforeClose'] and J(C/'prepared-r105/history-runtime-restored.json')['passed']
proof={'at':datetime.datetime.now().astimezone().isoformat(),'onlyOwnedSyntheticFixture':True,'ordinaryApprovers':2,'nativeCounterSign':1,'stages':2,'browserPhases':8,'testPlan':['normalCreateAndAttachment','disposalFeedback','firstOrdinaryApprover','firstNoLongerPendingAndInitiatorOnlyOriginalWithdraw','secondOrdinaryApproverStillAtFirstNode','finalNodeOnlyAfterBoth','handledReadOnly','completedOpinionsOrderAndAttachment'],'newProductSourceOrRealTemplateChanges':False,'currentPublicVersionKept':'R36','originalWithdrawMustBePreserved':True,'r105FailedHarnessAssumptionPreserved':True,'r105ActualFirstApprovalRetainedEngineNotEnded':True,'r105NormalSixComponentExitAndExactRestore':True,'r106ExecutionPending':True,'fullNativeNangangAcceptanceClaimed':False,'fullCloneReady':False,'sources':pins}
(D/'scope-and-source-pins.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scopeFixed':True,'sourceFiles':len(pins),'previousFailureAndRestoreProven':True,'onlyOwnSyntheticFixture':True,'publicOrDesktopChanged':False}))
