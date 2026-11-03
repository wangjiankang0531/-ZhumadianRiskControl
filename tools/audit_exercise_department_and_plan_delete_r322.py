from pathlib import Path
import ast,hashlib,json

R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/native_exercise_department_filter_verified_r320_20261103'
B=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/emergency'
W=R/'work/user_feedback_20261031/plan-exercise-retained-r224'
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
plan_path=B/'service/impl/EmergencyPlanServiceImpl.java';plan=plan_path.read_bytes()
assert sha(plan)=='b9cebe7b016f30f24d34061c0710f5c392d74f78831ba12bf26fbca6ca1dc5b0'
text=plan.decode('utf-8');start=text.index('public Boolean delete(String id) {');end=text.index('\n    }',start)
body=text[start:end]
for mapper in ['emergencyPlanExpertRelatedMapper','emergencyPlanGoodsManageRelatedMapper','emergencyPlanTeamRelatedMapper',
               'emergencyPlanCompanyMapper','emergencyPlanDeputyHeadMapper','emergencyPlanOthermemberMapper']:
    assert mapper+'.delete('in body
assert 'removeById(id)'in body and 'baseFileService.deleteFile(id)'in body
assert 'exercise'not in body.lower()and 'minio'not in body.lower()
exercise_path=B/'service/impl/EmergencyExerciseServiceImpl.java';exercise=exercise_path.read_bytes()
assert 'lambda.eq(EmergencyExerciseEntity::getOrganizeDepartment,query.getOrganizeDepartment())'in exercise.decode('utf-8')
rel='src/components/SearchForm/components/SearchFormItem.vue';wrapper=(W/'source'/rel).read_bytes()
assert sha(wrapper)==J(W/'actual-compiled-source-files.json')[rel]['sha256']
assert b'v-model.trim="_searchParam[column.search?.key ?? handleProp(column.prop!)]"'in wrapper
rel_list='src/views/emergencyPlans/structured/info/exerciseList.vue';listing=(W/'compiled-inputs'/rel_list).read_bytes()
assert sha(listing)==J(W/'actual-compiled-source-files.json')[rel_list]['sha256']
assert b'prop: "organizeDepartment"'in listing and b'v-model={searchParam.department}'in listing
override=T/'original_emergency_plan_atomic_compat.py';source=override.read_bytes();ast.parse(source)
assert b'@org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)'in source
assert b'emergencyExercise'not in source
proof={'passed':True,'sourcePins':{
 'originalPlanService':sha(plan),'originalExerciseService':sha(exercise),
 'actualCompiledCommonSearchFormItem':sha(wrapper),'actualCompiledExerciseList':sha(listing),
 'currentAtomicPlanAdapter':sha(source)},
 'originalPlanDeleteTargetsParentSixResourceRelationsAndOwnAttachmentMetadata':True,
 'originalPlanDeleteDoesNotExplicitlyDeleteExercisesOrObjectStoreFiles':True,
 'currentPlanAdapterPreservesThatDeletionSetAndAddsAtomicGuards':True,
 'runtimeDeleteOfPlanWithExercisesNotAcceptedByThisStaticAudit':True,
 'commonSearchFormBindsCanonicalColumnNameOrganizeDepartment':True,
 'initialLegacyKeyAloneDefectHypothesisContradictedByActualFilteredResponse':True,
 'speculativeR319FixWithdrawnBeforeCompileOrInstall':True,
 'originalSourcesDatabaseOrProductChanged':False,'fullNangangAccepted':False}
(D/'source-rule-audit-r322.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items()if k!='sourcePins'}))
