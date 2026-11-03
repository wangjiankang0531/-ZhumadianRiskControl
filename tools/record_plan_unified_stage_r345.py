from pathlib import Path
import ast,hashlib,json

R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'verified-stage-r345.json').exists()
prepared=J(D/'updater-preparation-r337.json');bundles=J(D/'bundle-preparation-r338.json')
full=J(D/'full-program-verification-r343.json');clean=J(D/'completed-file-fixture-cleanup-r344.json')
assert full['passed']and clean['passed']
source=T/'original_public_test_update_r39_plan_runtime_r337.py'
assert sha(source)==prepared['sourceSHA256']==bundles['candidateUpdaterSHA256']==full['candidateSourceSHA256']
variants={}
for label in ['r36','r37']:
    program=J(D/label/'full-program-preflight.json');tx=J(D/label/'composition-and-recovery.json');ready=J(D/label/'plan-readiness-boundaries-r340.json')
    assert program['allPassed']and program['fullProgramFilesVerified']==15557 and tx['passed']and ready['passed']
    assert tx['negativeCompositionCases']==57 and len(tx['normalAndFaultFileRecoveryCases'])==16 and len(ready['cases'])==8
    assert tx['updaterSHA256']==sha(source)and tx['writes']==187 and tx['removals']==177 and tx['changePaths']==364
    variants[label.upper()]={'programFiles':15557,'compositionNegativeCases':57,'actualFileRecoveryScenarios':16,
      'planRuntimeReadinessByteScenarios':8,'writes':187,'removals':177,'changePaths':364,
      'oldControls':program['oldDeclaredControls'],'newControls':program['newDeclaredControls'],
      'allOriginalProgramSourcesKept':program['sourceProgramsUnchanged'],
      'estimatedFixturePeakBytes':tx['peakAllocationBudgetBytes']}
assert bundles['variants']['R36']['newReleaseSHA256']==bundles['variants']['R37']['newReleaseSHA256']
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_sha=sha(held);other_sha=sha(other)
app=[source.relative_to(A).as_posix()];engine=[];pins=[{'path':app[0],'sha256':sha(source),'productionCandidate':True}]
names=['prepare_plan_unified_updater_r337.py','build_plan_unified_bundles_r338.py','prepare_plan_unified_full_views_r339.py',
 'run_plan_unified_full_views_r339.py','verify_plan_unified_full_r36_r339.py','verify_plan_unified_full_r37_r339.py',
 'prepare_plan_unified_transactions_r340.py','verify_plan_unified_transactions_r36_r340.py','verify_plan_unified_transactions_r37_r340.py',
 'prepare_r37_full_view_dependency_r341.py','verify_plan_unified_full_r37_r341.py','prepare_plan_transaction_bounds_r342.py',
 'run_plan_unified_transactions_r342.py','verify_plan_unified_transactions_r36_r342.py','verify_plan_unified_transactions_r37_r342.py',
 'verify_r37_full_view_resume_r343.py','cleanup_plan_unified_views_r344.ps1','record_plan_unified_stage_r345.py']
prototypes={'verify_plan_unified_full_r37_r339.py','verify_plan_unified_full_r37_r341.py',
 'verify_plan_unified_transactions_r36_r340.py','verify_plan_unified_transactions_r37_r340.py'}
for name in names:
    src=V/name;raw=src.read_bytes();raw.decode('utf-8-sig')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    dst=T/name
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':sha(dst),'failedOrSupersededDriver':name in prototypes})
summary={'schema':'xnby.r345.plan-unified-candidate.v1','passedProgramAndFileTransactionStage':True,
 'candidateUpdaterSHA256':sha(source),'newReleaseSHA256':bundles['variants']['R36']['newReleaseSHA256'],
 'newPayloadManifestSHA256':bundles['variants']['R36']['newPayloadManifestSHA256'],
 'variants':variants,'sameFinalPayloadForBothBases':True,'eachVariantStillAcceptsOneExactInstalledBase':True,
 'onlyHealthLoadBundleAndCompositionFunctionsChanged':prepared['changedExistingFunctions'],
 'normalLifecycleBackupRestoreAndPoolPreflightFunctionsASTRetained':True,
 'exactPreviouslyNativeTestedPlanClassSHA256':bundles['candidatePlanClassSHA256'],
 'previousNative18CasesNotClaimedAsNewUpdaterWholeLifecycle':True,
 'newUpdaterWholeSixComponentApplyRollbackExecuted':False,'newCombinedCandidateNativeUIExecuted':False,
 'actualIISHTTPSOrPublicDeploymentPassed':False,'publicTransportWrapperPrepared':False,
 'initialR37MissingSharedHistorySourceAndWrongExpectedIISCodeDriverFailuresRetained':True,
 'allFileViewsCleanedAndOriginalGReleasePreserved':True,'publicFormalSceneAndDesktopChanged':False,'fullCloneReady':False}
jout(D/'verified-stage-r345.json',summary)
scoped={k:v for k,v in clean.items()if k!='targets'};scoped['targets']=[{k:v for k,v in row.items()if k!='path'}for row in clean['targets']]
jout(D/'scoped-file-fixture-cleanup-r344.json',scoped)
jout(D/'source-pins-r345.json',{'sources':pins,'publicPushed':False,'acceptedCandidateSourceSHA256':sha(source)})
guide=f'''# R39预案事务、原XML、前端及加载优化统一候选

## 组成与两份严格基线

统一了R333实际18场景使用的预案事务类384462cf、原XML默认扫描、R224真实编译前端及R37静态gzip/缓存。业务JDK17预案class major61，平台JDK8、原业务Jar/原SQL、鉴权、私有配置、数据库/上传和其余控制保持。新更新器SHA256 {sha(source)}，236206字节；只改已有health/load_bundle/组合合同并新增两个纯声明/字节就绪函数，停启/备份/替换/恢复/回滚及预算函数AST保持。该保持不等于本轮完整生命周期已运行。

本地work/r39-plan-runtime-unified-r1下r36与r37各一份bundle，每份仍只接受自己精确的旧release，不能互相替代。R36旧daaf0be2、R37旧909b64aa；最终release均为{summary['newReleaseSHA256']}、payload均为{summary['newPayloadManifestSHA256']}。两者187写入+177旧前端移除，共364路径，22个新控制；R36原21、R37原22。新预案类作为精确白名单路径加入清单，不覆盖原Jar；旧版本中若已有未登记的同路径类则停服前拒绝。

## 已验证范围

每种基线完整load_bundle核15557程序。保留程序/控制SHA、候选类合同、同一配置快照Mapper/连接预算及原程序/IIS漂移拒绝通过。R37先因驱动只从六文件增量包查共享历史依赖而在视图创建前失败，补R36共享精确来源后装载通过；之后故意IIS漂移正确以FILE_PIN_MISMATCH拒绝，驱动仍期待旧R36的UNKNOWN_OLD_ENTRY_SCRIPT导致断言失败。最终按登记状态验证精确错误码，重新核全部自有视图及原程序，加入意外旧预案类存在的拒绝检查后通过。两个失败保留，候选字节未因驱动修正改变。

每种基线57项组合拒绝、16项真实backup_code/replace_code/restore_code故障与外来漂移情景通过，含预案class写后故障和外来class拒绝覆盖；八种已安装/运行副本字节就绪边界通过。它们是文件及声明检查，未启动服务/执行SQL，不据此宣称新的实际更新器已完成三轮六组件或IIS/TLS。此前同一class的R143普通角色18场景属于组件业务证据，仍需在最终更新器生命周期中合并核验。

## 存储和状态

生成前核D盘余量，文件交易两变体保守额外预算1GiB、每份动态上限512MiB，实算约350MB；程序依赖仅只读硬链接，独立可变副本每份限128MiB，不复制GIS/数据库/凭据。验证结束核十个精确目录、无活动驱动/引用及无重解析后清{int(clean['removedFileEntries'])}文件项、逻辑{int(clean['logicalBytes'])}B，D观察增加{int(clean['observedDFreeDelta'])}B，不把硬链接逻辑体积当实际回收或独占归因。候选shared/r36/r37包、R37旧合同、源码、证据和两份resolution映射保留，G仍e9dcd876。

当前未制作外发ZIP/固定运输包装器，未上传或部署R39。下一步在自有G环境用这份精确源，分别实际启动旧基线→apply_update→rollback_latest并正常停止，核候选预案字节就绪/原398模型/HTTPgzip及正常角色业务，再按实际证据固定运输。入口采用明确回环HTTP适配时不能叫IIS/TLS通过。R37实际部署完成回执仍待；不因缺回执猜当前服务器版本。426文件公开Git同步已完成（应用faba43bf/引擎edadba4c），本轮新源不包含在旧批准范围，仍仅本地。

全UE对标引擎、EXE GIS/DLG点线面图层旗杆多源标牌、网页三维及一系统全南港B/S目标active/fullCloneReady=false。真实南港模板、权限、综合/快捷入口一致性及实际公网体验仍待；不以测试、SQL/静态文件数当功能完成率。
'''
write(D/'统一候选组成与文件验证阶段说明.md',guide)
for name in ['updater-preparation-r337.json','bundle-preparation-r338.json','full-program-verification-r343.json',
 'verified-stage-r345.json','scoped-file-fixture-cleanup-r344.json','source-pins-r345.json']:
    dst=A/'deploy/verification/native_plan_unified_r345_20261103'/name;write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
for label in ['r36','r37']:
    for name in ['full-program-preflight.json','composition-and-recovery.json','composition-negative-cases.json','plan-readiness-boundaries-r340.json','verified-transactions-r342.json']:
        dst=A/'deploy/verification/native_plan_unified_r345_20261103'/label/name;write(dst,(D/label/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
hp=A/'deploy/handbook/native_plan_unified_r345_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R337—R345：R39统一候选两精确基线程序/文件恢复通过，实际生命周期待做

预案事务类384462cf与原Mapper、R224前端、R37性能已组合。新更新器e935f51a（236206B），只改health/load_bundle/合同，加声明/运行副本字节检查；停启/备份替换恢复回滚/预算AST保持。R36/R37各一独立bundle、每份仅认一精确旧基线，最终同release9a3a878a/payload773049fb，187写入+177移除/364路径，控制21或22→22。

两份各15557完整程序、57拒绝、16实际文件恢复/外来漂移及8字节就绪边界通过。R37先缺共享R36历史来源（分配前），后IIS已正确拒绝但驱动期望旧错误码，均保留不当候选失败；修测试来源/断言并重新核自有视图通过，候选源未改。没有服务/SQL/公网操作，不把上述文件检查或R143同class18场景冒充本源实际apply/rollback/IIS通过。

清43520文件项、逻辑3293340935B（含硬链接），D观察+517738496B不独占归因；保留两包/shared、源码/结果/resolution及原G e9，资产/数据/上传/正式18891/8767/另一三维断点保持。下一用精确e935源在自有G分别实际旧基线→apply→rollback三轮六组件并核原398模型/候选类/HTTP静态和普通角色，再做运输包装；外网IIS/TLS仍待。R37执行回执缺，不能猜当前服务器版；公开426同步已完成faba43bf/edadba4c，本轮仅本地Git。详Deployment/native_plan_unified_candidate_r39_20261103/统一候选组成与文件验证阶段说明.md。全UE引擎/EXE DLG图层旗杆标牌/Web3D/全南港目标active/fullCloneReady=false，真实模板权限/跨入口仍待，不报新百分比。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith('## 2026-11-03 R337—R345：');write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R345两精确基线统一候选程序与文件恢复'
assert marker not in old;write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/统一预案候选文件验证_R345_20261103.md';write(ep,stage+guide);engine.append('docs/project/统一预案候选文件验证_R345_20261103.md')
assert sha(held)==held_sha and sha(other)==other_sha and len(app)==len(set(app))and len(engine)==len(set(engine))
jout(D/'local-stage-files-r345.json',{'application':app,'engine':engine,'heldNativeSHA256':held_sha,'other3DBreakpointSHA256':other_sha,
 'sourceSHA256':sha(source),'actualWholeUpdaterLifecyclePending':True,'publicPushed':False})
print(json.dumps({'recorded':True,'applicationFiles':len(app),'engineFiles':len(engine),'eachVariantProgramFiles':15557,'fileScenariosEach':16,'actualLifecyclePending':True,'publicPushed':False}))
