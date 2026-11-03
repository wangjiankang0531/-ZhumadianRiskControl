from pathlib import Path
import ast,datetime,hashlib,json

R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103'
D0=R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'verified-result-r334.json').exists()
result=J(C/'r143/result.json');browser=J(C/'r143/plan-browser/result.json')
checks=J(C/'r143/ready-checks.json');child=J(C/'r143/plan-browser/parent-delete-with-exercises-evidence.json')
assert result['allPassed']and result['original398ModelsUnchanged']and result['connectionCapacityWithoutRefusals']
assert browser['passed']and len(browser['cases'])==18 and not browser['exceptions']
assert checks['actualCandidatePlanOverrideRuntimeBytesMatched']and child['passed']
assert child['parentAbsentFromListAndDetails']and child['childExercisesBefore']==child['childExercisesAfter']==2
assert child['childDetailsPeopleAndFileMetadataUnchanged']and child['realChildAttachmentBytesIdentical']and child['unrelatedOwnPlanExactDetailsUnchanged']
assert sha(C/'r143/actual-host-source.py')==sha(T/'verify_full_controller_parent_delete_r330.py')
assert sha(C/'r143/actual-browser-source.mjs')==sha(T/'verify_native_parent_delete_r330_20261103.mjs')
for attempt,code in [('r141',1),('r143',0)]:
    outer=J(C/(attempt+'-outer-terminal.json'));terminal=J(C/attempt/'controller-terminal.json')
    receipt=J(C/attempt/'scoped-controller-receipt.json');bt=J(C/attempt/'plan-browser/browser-terminal.json')
    assert outer['exitCode']==code and outer['actualDescendantsZeroBeforeClose']
    assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']
    assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
    assert bt['chromeExitCode']==0 and bt['normalBrowserClose']
    names=['frontend-restored.json','mapper-observer-restored.json','mapper-product-restored.json','history-runtime-restored.json']
    if attempt=='r143':names+=['plan-runtime-restored.json']
    assert all(J(C/('prepared-'+attempt)/name)['passed']for name in names)
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
class_rel='payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
assert not(R/'_g/Application'/class_rel).exists()
scope=J(C/'prepared-r143/plan-runtime-scope.json')
assert sha(R/'_g/Application/payload/business/application.jar')==scope['originalJarSHA256']
module=J(D/'native-plan-runtime-module-r333.json');frozen=J(D/'module-freeze-r333.json')
assert frozen['passed']and module['classSHA256']==scope['newFiles'][class_rel]['sha256']
historical=J(R/'Document/Deployment/emergency_plan_report_20261030/sql-r9/result.json')
assert historical['candidateClassPins']['plan']==module['classSHA256']and historical['planParentSixRelationsAndAttachmentsAtomicityVerified']
clean=J(D/'completed-fixture-cleanup-r332.json');assert clean['passed']
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_sha=sha(held);other_sha=sha(other)
app=[];engine=[];pins=[]
for file in [D0/'prepared-result-r325.json',D/'prepared-result-r330.json']:
    for name,pin in J(file)['sourcePins'].items():
        p=T/name;assert sha(p)==pin;app.append(p.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':pin,'acceptedRuntimeSource':file.parent==D})
names=['prepare_parent_delete_exercises_r325.py','prepare_parent_delete_exercises_generated_r325.py','run_parent_delete_exercises_r326.py',
       'restore_parent_delete_prestart_r326.py','prepare_cleanup_parent_delete_r327.py','cleanup_parent_delete_r327.ps1',
       'inspect_plan_runtime_candidate_r328.py','prepare_plan_runtime_candidate_r330.py','prepare_plan_runtime_candidate_generated_r330.py',
       'run_plan_runtime_candidate_r331.py','restore_plan_runtime_prestart_r331.py','prepare_cleanup_plan_runtime_r332.py',
       'cleanup_plan_runtime_r332.ps1','freeze_plan_runtime_module_r333.py','record_plan_runtime_r334.py']
for name in names:
    src=V/name;raw=src.read_bytes();raw.decode('utf-8-sig')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    dst=T/name
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':sha(dst),
      'historicalUnusedPrototype':name in ['restore_parent_delete_prestart_r326.py','prepare_cleanup_parent_delete_r327.py','cleanup_parent_delete_r327.ps1']})
app.append('tools/original_emergency_plan_atomic_compat.py')
summary={'schema':'xnby.r334.native-plan-runtime.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'passed':True,'attempt':'r143','normalRoleActualCompiledBrowserCases':18,'javaScriptExceptions':0,
 'baselineR141ActualDeleteSucceededThenOldDetailHTTP500':True,'candidateDeletedOldDetailHTTP':200,'candidateMissingDetailDataNull':True,
 'actualRuntimeCopiedPlanClassSHA256':module['classSHA256'],'candidateClassMajor':61,'businessJDK17PlatformJDK8Kept':True,
 'originalBusinessJarUnchanged':True,'originalModelsComparedUnchanged':398,'originalXMLStatementsActuallyRegistered':226,
 'connectionCapacityWithoutRefusals':True,'childExerciseRetentionBeforeAfter':[2,2],
 'childPeopleAndFileMetadataAndRealObjectBytesUnchanged':True,'unrelatedControlPlanExactDetailsUnchanged':True,
 'originalNoExerciseCascadeBehaviorPreserved':True,'sixResourceRelationsAllPopulatedByThisBrowserCase':False,
 'historicalExactClassTemporarySQLAtomicProofAvailable':True,'freshRealSQLFaultInjectionInThisSixComponentRun':False,
 'originalControllerAndNormalRoleUIUsedWithExplicitCandidatePlanServiceClass':True,
 'rawFixtureOriginalServiceLabelDoesNotMeanUntouchedJarImplementation':True,
 'allComponentsAndChromeNormalZeroActualDescendantsZero':True,'sixRestoreLayersPassedAndOriginalGReleaseRestored':True,
 'metadataRunPointerNotClaimedRestored':True,'localModuleFiles':frozen['moduleFiles'],'localModuleBytes':frozen['moduleBytes'],
 'moduleManifestSHA256':frozen['moduleManifestSHA256'],'fullPublicCombinedTransportBuiltOrDeployed':False,
 'currentR38r2DoesNotIncludeThisFix':True,'publicFormalSceneAndDesktopChanged':False,'fullCloneReady':False}
jout(D/'verified-result-r334.json',summary)
normalized={k:v for k,v in child.items()if k!='actualOriginalServiceAndNormalRoleUI'}
normalized['originalControllerAndNormalRoleUIWithCandidatePlanServiceClass']=True
jout(D/'parent-child-object-evidence-r334.json',normalized)
scoped={k:v for k,v in clean.items()if k!='targets'};scoped['targets']=[{k:v for k,v in row.items()if k!='path'}for row in clean['targets']]
jout(D/'scoped-cleanup-r332.json',scoped)
jout(D/'source-pins-r334.json',{'sources':pins,'capturedHostAndBrowserExactlyMatchAcceptedSources':True,'publicPushed':False})

guide=f'''# 预案旧详情500复现与事务兼容类真实接入验收

## 问题和修正

R141真实普通角色在R224编译前端创建预案和两条演练，删除父预案返回成功；随后通过原鉴权读取旧详情，实际HTTP500/业务码100000，整轮未通过。当前运行模板中没有EmergencyPlanServiceImpl覆盖类，使用原Jar实现，缺失记录仍解引用。R324仅核了源码候选的删除范围，不能将源码存在当作运行装载。

本次接入既有已编译、逐字匹配当前生成器的预案事务兼容类，SHA256为{module['classSHA256']}，21713字节、major61，运行于业务JDK17；平台JDK8不动。它对不存在的详情返回null，并对预案父记录、六类资源/人员关联和附件元数据操作补事务/写入确认，保留原先不连删演练或对象文件的集合。原业务Jar、控制器、鉴权、数据库结构、配置和其余类保持。

R143实际运行目录复制类SHA已在启动后断言，原SDK普通角色及真实编译页面18场景通过，JavaScript异常0。删除后原详情GET正常HTTP200/code0/data null；两条演练仍可按原预案ID查询，人员/附件元数据逐字段不变，演练附件实际HTTP200且字节相同，另建对照预案详情精确保持。新分支没有在浏览器中填满六类关联，也不冒称本轮做过真实SQL故障注入；同一class的历史临时SQL事务证明保留，不能说成这轮重跑。

原始浏览器夹具曾使用“actualOriginalService”标签，该标签指原服务路径，不表示Jar实现未改；本报告明确限定为原控制器/普通角色UI加候选预案实现。R141失败及R330首次内存拒绝均保留。内存拒绝发生在分配前，当时未装类或启动；核根目录不存在、原清单及进程零后，可用内存恢复8.164GiB才继续，没有降低6GiB准备/4GiB运行门槛或关闭用户应用。

## 退出、恢复、存储

R141外层1、R143外层0；两轮控制器、六组件和Chrome正常0、真实Job后代零。候选六层恢复通过：前端、预案类、观察器、产品参数、历史模块与虚构配置；G原release回e9dcd876、预案覆盖类恢复为原先不存在。session62985终态0，不重复轮询/重启。R143原XML226注册/398模型及连接容量通过。

核精确绝对范围、逐SHA、无进程引用/无重解析后，清11份原像目录和2份Chrome配置：{int(clean['removedFileEntries'])}文件项，逻辑{int(clean['logicalBytes'])}B，D空闲观察增加{int(clean['observedDFreeDelta'])}B，不独占归因。源码、失败/成功证据、合成数据库与上传保持，未强杀进程。

## 交付状态和下一步

固定本地模块在work/user_feedback_20261031/native-plan-runtime-r333：3文件{frozen['moduleBytes']}字节，模块清单SHA256 {frozen['moduleManifestSHA256']}，只取实际跑过的同一class、对应源码及清单，没有以另一份新编译物替代测试字节。它是可审阅模块，不是完整公网更新器，未安装正式18891或公网。

当前R38第二稿不含这份预案修正。下一份统一候选需合并模块、原SQL默认扫描、前端及加载优化，完成固定运输/完整安装回滚核验后再发布；R37手动执行完成记录仍缺，须先核实际服务器基线，不能猜R36/R37。426文件公开Git候选e85505cd清单保持不变待答，本轮增量仅本地保存，不夹带修改既定范围。

本轮没有操作桌面、三维8767、正式18891或另一三维专属断点。全部南港真实模板/权限/综合与快捷入口一致性和实际IIS/公网性能仍待。完整UE对标引擎、EXE GIS/DLG点线面图层旗杆多源标牌、Web3D和一系统全南港B/S目标active/fullCloneReady=false，不给未去重的新完成率。
'''
write(D/'预案旧详情修正与真实运行验收.md',guide)
for name in ['verified-result-r334.json','parent-child-object-evidence-r334.json','scoped-cleanup-r332.json','source-pins-r334.json',
             'baseline-failure-r329.json','runtime-plan-class-audit-r328.json','retained-memory-refusal-r330.json',
             'native-plan-runtime-module-r333.json','module-freeze-r333.json']:
    dst=A/'deploy/verification/native_plan_runtime_r334_20261103'/name
    write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
hp=A/'deploy/handbook/native_plan_runtime_r334_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage='''## 2026-11-03 R325—R334：旧预案详情500真实复现，兼容类实际接入18场景通过，公网组合待做

r141删除带两条演练的自有父预案成功后，旧详情实际HTTP500，16旧场景不冒称整轮通过；运行模板无预案覆盖类、仍原Jar实现。R324源码候选核对不等同运行装载。r143接入精确既有384462cf预案事务类（major61/业务JDK17），启动后实际复制字节断言通过；普通角色/原控制器/R224真实前端18场景0JS异常，旧详情HTTP200/code0/null，两演练/人员/附件元数据、实际对象字节及另一预案保持。保留原不连删演练/对象集合；本轮未填满六类关联或做新SQL故障，历史同class事务证明不当新重跑。

R330首次6GiB内存准备守卫在分配前拒绝；核原e9清单/根不存在/零进程后，内存8.164GiB才继续，未降门槛。两轮六组件/Chrome正常0、Job后代零，r143外层/session62985终态0；六层代码/虚构配置恢复、G回e9dcd876、覆盖类原先不存在恢复。226原XML/398模型/容量通过。清1201文件/逻辑67102823B、D观察+68386816B不独占归因，源/证据/数据库上传保持。

同一实测类/源码/清单固定本地R333模块3文件43657B、清单656f5feb0e869136a57b32213b442fa467e8e4e12ab70d54cc5ce9aed31b16c4；它尚非完整公网更新包。R38第二稿不含此类，需下一统一候选合入再验运输及完整安装回滚；R37执行记录仍待，先核实际基线。426文件公开清单e85505cd不变待答，本轮仅本地Git；桌面/公网/正式18891/8767及另一三维断点保持。详Deployment/native_plan_runtime_candidate_r329_20261103/预案旧详情修正与真实运行验收.md。全UE引擎/EXE GIS DLG图层旗杆标牌/Web3D/全南港目标active/fullCloneReady=false，真实模板权限/跨入口/IIS公网仍待，不报新百分比。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith('## 2026-11-03 R325—R334：');write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R334预案真实500修正与候选运行验收'
assert marker not in old;write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/预案旧详情修正运行验收_R334_20261103.md';write(ep,stage+guide);engine.append('docs/project/预案旧详情修正运行验收_R334_20261103.md')
assert sha(held)==held_sha and sha(other)==other_sha and len(app)==len(set(app))and len(engine)==len(set(engine))
fixed=R/'Document/Deployment/public_source_checkpoint_r313_20261103/public-git-sync-r313-manifest.json'
assert sha(fixed)=='e85505cd4c17272cf03d76ee4897c934fe709ae101fd2df130be3d493ca2ac21'
jout(D/'local-stage-files-r334.json',{'application':app,'engine':engine,'heldNativeSHA256':held_sha,'other3DBreakpointSHA256':other_sha,
 'pending426PublicManifestUnchanged':True,'publicPushed':False})
print(json.dumps({'passed':True,'browserCases':18,'newLocalModuleFixed':True,'applicationFiles':len(app),'engineFiles':len(engine),'publicPushed':False}))
