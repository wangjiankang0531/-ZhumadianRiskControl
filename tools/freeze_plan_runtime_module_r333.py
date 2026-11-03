from pathlib import Path
import hashlib,json,struct
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103'
W=R/'work/user_feedback_20261031/native-plan-runtime-r333'
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
assert not W.exists()
assert J(C/'r143-outer-terminal.json')['exitCode']==0
assert J(C/'r143/ready-checks.json')['actualCandidatePlanOverrideRuntimeBytesMatched']
assert J(C/'r143/result.json')['allPassed']and len(J(C/'r143/plan-browser/result.json')['cases'])==18
assert J(C/'prepared-r143/plan-runtime-restored.json')['passed']
rel='com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl'
source=(R/'work/emergency_plan_report_20261030/candidate-src-v4'/(rel+'.java')).read_bytes()
binary=(R/'work/emergency_plan_report_20261030/compile-v4/candidate-classes'/(rel+'.class')).read_bytes()
assert sha(source)=='5ad79c9bbbfcf2cce8488e28cad2fecf153b993e242c1e24a8c34a4b525d9fc6'
assert sha(binary)=='384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'
assert struct.unpack('>H',binary[6:8])[0]==61
scope=J(C/'prepared-r143/plan-runtime-scope.json')
target='payload/business/run-template/classes/'+rel+'.class'
assert scope['newFiles'][target]['sha256']==sha(binary)
W.mkdir();files={'source/'+rel+'.java':source,target:binary}
for name,raw in files.items():
    dst=W/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
manifest={'schema':'xnby.native-plan-runtime.module.r333.v1','module':'native-plan-atomic-runtime',
 'runtimeRelativePath':target,'classSHA256':sha(binary),'classBytes':len(binary),'classMajor':61,
 'sourceSHA256':sha(source),'sourceBytes':len(source),
 'originalJarPlanClassSHA256':'3015417dfedfd3a2d0c139f79d7f1f4f5391f3919c9ce9b853a7aee8a8d744ce',
 'businessJDK':17,'platformJDK8Unchanged':True,'originalBusinessJarChanged':False,
 'modelAuthenticationConfigurationOrDataChanged':False,'actualNormalRoleNativeBrowserCases':18,
 'actualRuntimeClassCopySHAAssertAndDeletedOldDetailsNullPassed':True,
 'actualChildExercisePeopleMetadataObjectAndUnrelatedPlanKept':True,
 'exactClassHadHistoricalTemporaryTableAtomicFaultProof':True,
 'historicalFaultProofRerunInCurrentSixComponents':False,
 'originalNoExerciseCascadeSetPreserved':True,'currentFixedR38r2DoesNotContainThisClass':True,
 'fullCombinedPublicTransportBuiltOrDeployed':False,'fullCloneReady':False,
 'files':{name:{'bytes':len(raw),'sha256':sha(raw)}for name,raw in files.items()}}
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
(W/'module-manifest.json').write_bytes(raw)
(D/'native-plan-runtime-module-r333.json').write_bytes(raw)
proof={'passed':True,'moduleManifestSHA256':sha(raw),'moduleFiles':3,
 'moduleBytes':sum(len(v)for v in files.values())+len(raw),'exactNativeTestedClassPreserved':True,
 'freshRecompileOrNewUntestedClassNotSubstituted':True,'publicOrFormalInstalled':False}
(D/'module-freeze-r333.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
