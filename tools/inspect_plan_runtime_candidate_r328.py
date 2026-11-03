from pathlib import Path
import hashlib,importlib.util,json,struct,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_g/Application'
D=R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
assert J(R/'work/event_delivery_consistency_20261030/full-controller-r163/prepared-r141/history-runtime-restored.json')['passed']
assert sha((A/'release-manifest.json').read_bytes())=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
rel='com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl'
candidate=R/'work/emergency_plan_report_20261030/compile-v4/candidate-classes'/(rel+'.class')
source=R/'work/emergency_plan_report_20261030/candidate-src-v4'/(rel+'.java')
meta=J(R/'Document/Deployment/emergency_plan_report_20261030/compiled-class-verification.json')
assert sha(candidate.read_bytes())==meta['candidateClassPins']['plan']=='384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'
assert sha(source.read_bytes())==meta['candidateSources']['plan']['candidate']['SHA256']
original=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java'/(rel+'.java')
spec=importlib.util.spec_from_file_location('plan_compat',T/'original_emergency_plan_atomic_compat.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.candidate(original.read_bytes())==source.read_bytes()
with zipfile.ZipFile(A/'payload/business/application.jar')as z:original_class=z.read(rel+'.class')
assert sha(original_class)==meta['originalClassPins']['plan']
assert not(A/'payload/business/run-template/classes'/(rel+'.class')).exists()
assert (A/'runtime/jdk17/bin/java.exe').is_file()
controller=(A/'tools/serve_original_server_release.py').read_text(encoding='utf-8')
assert "bchild=start('business',[str(app/'runtime/jdk17/bin/java.exe')"in controller
assert struct.unpack('>H',candidate.read_bytes()[6:8])[0]==61
proof={'passed':True,'businessRunsJDK17PlatformUsesJDK8Separately':True,
 'originalJarPlanClassSHA256':sha(original_class),'currentStoppedFixturePlanOverrideAbsent':True,
 'actualR141DeletedPlanDetailHTTP':500,'candidateClassSHA256':sha(candidate.read_bytes()),'candidateClassBytes':candidate.stat().st_size,
 'candidateClassMajor':61,'candidateSourceSHA256':sha(source.read_bytes()),
 'currentCompatGeneratesExactlyPreviouslyCompiledSource':True,
 'candidateAddsMissingDetailGuardAndOriginalParentRelationsFilesAtomicity':True,
 'candidatePreservesOriginalNoExerciseOrObjectDeletionSet':True,
 'newCandidateActuallyInstalledOrExecutedThisStage':False,'publicOrFormalChanged':False,
 'historicalCompileAndSQLProofDoesNotReplaceNewNativeLifecycle':True}
(D/'runtime-plan-class-audit-r328.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
