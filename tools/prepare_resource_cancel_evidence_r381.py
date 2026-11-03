from pathlib import Path
import ctypes,hashlib,json,re
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/native_plan_six_relations_r372_20261103'
W=R/'work/plan-resource-cancel-r375';B=R/'work/user_feedback_20261031/plan-resource-cancel-r378/retry-r2'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(D/'verified-component-and-build-r381.json').exists()
components={}
for variant,rejections in [('baseline',6),('candidate',0)]:
    result=J(W/variant/'result.json');terminal=J(W/variant/'terminal.json');outer=J(W/(variant+'-outer-terminal.json'))
    assert result['passed']and len(result['cases'])==9 and result['actualUnhandledRejections']==rejections
    assert terminal['chromeExitCode']==outer['nodeExitCode']==0 and terminal['serverNormallyClosed']and outer['actualDescendantsZero']
    components[variant]={'passed':True,'cases':result['cases'],'unhandledRejections':rejections,'chromeNodeAndActualDescendantsNormalZero':True,
       'realResourceSFCAndElementPlus':True,'proTableDictionaryAndApiExplicitStubs':True,'normalRoleOrBackendAccepted':False}
build=J(B/'full-build-result.json');terminal=J(B/'build-terminal.json');restored=J(B/'source-restored.json')
assert build['passed']and build['fileCount']==341 and terminal['nodeExitCode']==0 and terminal['actualDescendantsZeroBeforeClose']and restored['allSevenOverrideLayersRestored']
actual=J(B/'actual-compiled-source-files.json');module=J(D/'resource-cancel-candidate-r376.json');changed=build['changedSourcePaths'];assert len(changed)==3
for row in module['candidateComponents']:
    rel='src/views/emergencyPlans/structured/components/'+row['component']+'.vue'
    assert rel in changed and sha(B/'compiled-inputs'/rel)==row['candidateSHA256']==actual[rel]['sha256']
reference=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包'
front=reference/'敏捷应急管理前台代码/agile-emergency-response-dev/src/views/emergencyPlans/structured/components/formList.vue'
backend=reference/'后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/emergency'
service=backend/'service/impl/EmergencyPlanServiceImpl.java';assert sha(service)=='b9cebe7b016f30f24d34061c0710f5c392d74f78831ba12bf26fbca6ca1dc5b0'
mapping=[('副指挥长','EmergencyPlanDeputyHeadEntity','emergencyPlanDeputyHeadList'),('其他成员','EmergencyPlanOthermemberEntity','emergencyPlanOthermemberList'),
 ('参与单位','EmergencyPlanCompanyEntity','emergencyPlanCompanyList'),('应急物资','EmergencyPlanGoodsManageRelatedEntity','emergencyGoodsManageIdList'),
 ('应急队伍','EmergencyPlanTeamRelatedEntity','emergencyTeamIdList'),('应急专家','EmergencyPlanExpertRelatedEntity','emergencyExpertIdList')]
contracts=[]
for label,entity,field in mapping:
    p=backend/'entity'/(entity+'.java');text=p.read_text(encoding='utf-8');table=re.search(r'@TableName\("([a-z_]+)"\)',text).group(1)
    contracts.append({'group':label,'entity':entity,'table':table,'originalRequestOrDetailField':field,'sourceSHA256':sha(p)})
proof={'passedComponentAndFullBuildStage':True,'components':components,'fullBuild':{'passed':True,'compiledFiles':341,'changedSourcePaths':changed,
 'allOtherActualR224InputsKept':True,'sameThreeComponentBytesActuallyCompiled':True,'nodeHeapLimitMiB':2048,'actualNodeAndDescendantsNormalZero':True,'allSevenSourceLayersRestored':True},
 'originalSixRelationContracts':contracts,'originalServiceSHA256':sha(service),'memberFormSHA256':sha(front),
 'compiledMemberFormStillMatchesOriginalBytes':actual['src/views/emergencyPlans/structured/components/formList.vue']['sha256']==sha(front),
 'r373SixComponentMemoryAdmissionRefusedBeforeAllocation':True,'availableMemoryMeasuredAfterRefusalGiB':2.261,'fullSixComponentAdmissionGiBStill':6,
 'sixComponent29CaseDriverSupersededBeforeAllocation':True,'reason':'Actual cancel/close rejection reproduced; full native suite must run against the new compiled frontend candidate and an exact new composition, not silently alter frozen R39.',
 'full29CaseNormalRoleAcceptancePending':True,'newCompiledFrontendInstalledOrPublicDeployed':False,
 'r377OriginalProjectScopeGuardRefusalAndR378HeapOOMRetained':True,'onlyExactDependencyJunctionRemovedNonRecursivelyAfterActualExit':J(D/'owned-build-junction-cleanup-r379.json')['passed'],
 'frozenR39ManifestSHA256':sha(R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery-manifest.json'),
 'frozenPublic184ManifestSHA256':sha(R/'Document/Deployment/public_source_plan_delivery_r369_20261103/public-git-sync-r369-manifest.json'),
 'fullCloneReady':False}
assert proof['frozenR39ManifestSHA256']=='4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de'
assert proof['frozenPublic184ManifestSHA256']=='c10870e318047506c1ca0de42467a4fd8be602e5f8a85d5a5f40f3a9bcfe7ed1'
(D/'verified-component-and-build-r381.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'r373-superseded-before-service.json').write_text(json.dumps({'superseded':True,'runStarted':False,'allocatedRunRoot':False,'replaceOnlyAfterNewFrontendExactContractAndRealNativeSuite':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'componentBaselineUnhandled':6,'candidateUnhandled':0,'componentCasesEach':9,'fullBuildFiles':341,'changedSources':3,'native29StillPending':True,'frozenR39And184Unchanged':True,'memberFormOriginalByteMatch':proof['compiledMemberFormStillMatchesOriginalBytes']}))
