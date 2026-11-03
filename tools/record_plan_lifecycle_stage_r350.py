from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'verified-lifecycle-stage-r350.json').exists()
candidate=T/'original_public_test_update_r39_plan_runtime_r337.py'
assert sha(candidate)=='e935f51aa3c7a5aae3346c632b90423ce99f6a0887b1d44781ea0ed8e8c16d8f'
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
class_rel='payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
assert not(R/'_g/Application'/class_rel).exists()
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md'
held_pin=sha(held);other_pin=sha(other)
app=[];engine=[];variants={};copies=[];clean_total_files=0;clean_logical=0;clean_observed=0
for label in ['r36','r37']:
    d=D/('lifecycle-'+label);o=R/('work/r39-actual-lifecycle-'+label+'-r346')
    name='verified-lifecycle-r346.json'if label=='r36'else'verified-lifecycle-r347.json'
    proof=J(d/name);terminal=J(o/'terminal.json');cleanup=J(d/'completed-code-fixture-cleanup-r349.json')
    assert proof['passed']and cleanup['passed']and terminal['failure']is None and terminal['originalGCodeAndPointersRestored']
    assert terminal['allOwnedControllerHandlesTerminal']and len(terminal['controllers'])==3
    assert proof['candidateUpdaterSourceSHA256']==sha(candidate)and proof['rollbackRestoredPlanClassAbsence']
    controls=[]
    for c in terminal['controllers']:
        assert c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']and c['receipt']['allOwnedChildrenExited']
        exits=c['receipt']['exitCodesBeforeJobClose'];assert set(exits)=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in exits.values())
        controls.append({'controllerExitCode':0,'actualDescendantsZero':True,'normalOwnedShutdown':True,'sixChildExitCodes':exits})
    scoped={'passed':True,'controllers':controls,'originalGCodeAndPointersRestored':True,'noRuntimeUUIDsPIDsOrBusinessRowsIncluded':True,'forceTerminationUsed':False,'actualIISTLS':False}
    jout(d/'scoped-terminal-r350.json',scoped)
    static=J(o/'candidate-static-HTTP.json');assert static['passed']and len(static['checks'])==4
    jout(d/'candidate-static-summary-r350.json',static)
    plan=J(o/'candidate-plan-runtime-ready.json');assert plan['installedAndRuntimeClassCopyMatched']and not plan['actualBusinessFlowAcceptedByReadinessAlone']
    jout(d/'candidate-plan-runtime-summary-r350.json',plan)
    scoped_clean={k:v for k,v in cleanup.items()if k!='targets'}
    scoped_clean['targets']=[{'files':x['files'],'logicalBytes':x['logicalBytes'],'absoluteScopeNoReferencesAndNoReparseVerified':x['absoluteScopeNoReferencesAndNoReparseVerified']}for x in cleanup['targets']]
    jout(d/'scoped-cleanup-r350.json',scoped_clean)
    variants[label.upper()]={'passed':True,'actualApplyUpdateAndRollbackLatest':True,'actualControllers':3,'allControllerAndSixChildExitsNormalZero':True,
      'original398ModelsUnchanged':True,'candidateInstalledAndActualRuntimePlanClassMatched':True,'rollbackRestoresClassAbsence':True,'fourGatewayGzipDecodedHashesPassed':True,
      'original894CodeAndPointerPreimagesRestored':True,'native21CasesOnThisVariant':label=='r37','explicitHTTPIngressAdapterNotIISTLS':True}
    clean_total_files+=int(cleanup['removedFileEntries']);clean_logical+=int(cleanup['logicalBytes']);clean_observed+=int(cleanup['observedDFreeDelta'])
    for file in [name,'scoped-terminal-r350.json','candidate-static-summary-r350.json','candidate-plan-runtime-summary-r350.json','scoped-cleanup-r350.json','owned-attempt-receipt-summary-r349.json']:
        copies.append((d/file,label+'/'+file))
browser_root=R/'work/event_delivery_consistency_20261030/full-controller-r163/r145'
browser=J(browser_root/'plan-browser/result.json');native=J(D/'lifecycle-r37/candidate-native-ui-r347.json')
assert browser['passed']and len(browser['cases'])==21 and not browser['exceptions']and native['passed']
assert J(browser_root/'browser-outer-terminal.json')['actualDescendantsZero']
assert J(browser_root/'plan-browser/browser-terminal.json')['chromeExitCode']==0
case_summary={'passed':True,'actualFinalR39UpdaterAndRuntime':True,'actualNormalRoleAndOriginalController':True,
 'cases':browser['cases'],'javascriptExceptions':0,'onlyOwnedSyntheticRecords':True,'deletedOldDetailNavigationRetryRefresh':True,
 'allSixPlanRelationsOrFreshSQLFaultTestClaimed':False,'wholeNangangAccepted':False}
jout(D/'native-21-cases-r350.json',case_summary)
copies.extend([(D/'native-21-cases-r350.json','native-21-cases-r350.json'),(D/'lifecycle-r37/candidate-native-ui-r347.json','candidate-native-ui-r347.json')])
sources=['prepare_plan_lifecycle_drivers_r346.py','plan_lifecycle_inspect_r36_r346.py','plan_lifecycle_prepare_r36_r346.py','plan_lifecycle_run_r36_r346.py',
 'plan_lifecycle_inspect_r37_r346.py','plan_lifecycle_prepare_r37_r346.py','plan_lifecycle_run_r37_r346.py',
 'prepare_plan_native_lifecycle_r347.py','verify_native_unified_plan_r347.mjs','plan_lifecycle_run_r37_native_r347.py',
 'finalize_plan_lifecycle_ui_driver_r348.py','prepare_plan_lifecycle_cleanup_r349.py','cleanup_plan_lifecycle_r36_r349.ps1','cleanup_plan_lifecycle_r37_r349.ps1',
 'record_plan_lifecycle_stage_r350.py']
pins=[]
for name in sources:
    src=V/name;raw=src.read_bytes();raw.decode('utf-8-sig')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    dst=T/name
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':sha(dst),'bytes':len(raw),'unexecutedSuperseded':name=='plan_lifecycle_run_r37_r346.py'})
for name in ['plan-lifecycle-drivers-r346.json','plan-native-lifecycle-drivers-r347.json','plan-native-lifecycle-driver-final-r348.json','plan-lifecycle-cleanup-prepared-r349.json']:
    jout(D/name,J(V/name));copies.append((D/name,name))
summary={'schema':'xnby.r350.plan-unified-actual-lifecycle.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'candidateUpdaterSHA256':sha(candidate),'finalR37HostSHA256':sha(V/'plan_lifecycle_run_r37_native_r347.py'),'browserSourceSHA256':sha(V/'verify_native_unified_plan_r347.mjs'),
 'bothExactBaselinesPassed':True,'variants':variants,'actualControllersAcrossBothVariants':6,
 'r37CandidateNormalRoleActualCompiledUI21CasesPassed':True,'deletedParentOldDetailNavigateRetryAndRefreshPassed':True,
 'newProductSourceChangedInThisStage':False,'actualIISHTTPSOrPublicDeploymentPassed':False,'transportWrapperStillPending':True,
 'ingressOnlyExplicitLoopbackHTTPAdapter':True,'updaterIdentityHealthLifecycleAndFileTransactionBodiesNotStubbed':True,
 'allCodePrivateConfigurationAndPointersRestored':True,'syntheticDatabaseCopiedOrReplaced':False,
 'cleanupFileEntries':clean_total_files,'cleanupLogicalBytes':clean_logical,'sumObservedDFreeDeltaNotUniquelyAttributed':clean_observed,
 'r348InitialCRLFDriverAssertionRefusedBeforeAnyWriteThenCorrected':True,
 'sources':pins,'publicGitPushedByThisStage':False,'publicFormal18891Scene8767OrDesktopChanged':False,'fullCloneReady':False}
jout(D/'verified-lifecycle-stage-r350.json',summary);copies.append((D/'verified-lifecycle-stage-r350.json','verified-lifecycle-stage-r350.json'))
for src,name in copies:
    dst=A/'deploy/verification/native_plan_unified_lifecycle_r350_20261103'/name;write(dst,src.read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
guide=f'''# R39两基线实际更新回滚与普通角色21场景验收

本轮使用同一最终更新器e935f51a（SHA256 {sha(candidate)}），分别从严格R36、R37基线实际启动、执行apply_update、rollback_latest并正常停机。每份仍仅接受自己的精确旧release；只为自有合成环境适配目标目录、动态回环端口和虚构私有配置清单指针。身份、健康、停启、备份/替换/恢复与回滚函数体未替换为spy。每种基线保存并恢复894个代码/指针前像，原配置与安装身份摘要保持；最终G回e9dcd876，新增预案覆盖类恢复为原先不存在。

两种基线各三次真实六组件启动，共六个控制器；每次控制器及store/mysql/redis/platform/business/gateway均正常退出0，实际Windows Job后代数为0后才恢复代码。更新前/更新后/回滚后398张原表结构摘要一致，不据此称业务行未变化；未复制、覆盖或回滚数据库。候选运行时安装类与实际b/classes副本SHA均为384462cf，回滚恢复类缺失。四个主JS/CSS实际网关gzip、缓存策略和解压SHA在两份候选均通过。

R37路线在候选更新成功后，用自有非管理员角色正常登录原控制器和最终编译页面，21项浏览器场景、零JS异常通过。覆盖预案校验、新增编辑只读详情、演练的空人员与正常人员选择、附件真实对象字节、提交保护/false响应、部门筛选重置、删除取消/false/确认、带两个演练的父预案删除且原子记录/人员/附件及另一预案保持。新增三项从实际详情操作捕获的旧URL出发，检查删除后导航、重试、整页刷新均出现“详情未取得或数据不完整，请重试。”且不显示旧表单；原getById为HTTP200/code0/null。该轮未填满全部六种预案资源关联或重跑新SQL故障；历史同class事务证明仍是历史证据。

正常角色使用合成账号和限定合成菜单/字典；自有数据留在自有库，不在公网注入测试业务。Chrome正常关闭0，外层Node及实际后代为0。浏览器失败处理在执行前补齐：即使UI断言失败也继续真实回滚/正常停机/原像恢复，然后报告失败，不能跳过恢复或伪造通过；最初补充生成器因CRLF匹配断言在写文件前拒绝，改用通用换行读取后准备成功，不是产品故障。R346的R37无UI旧运行源未执行，由最终R347+R348准备后的源取代；当前最终宿主SHA {summary['finalR37HostSHA256']}。

## 证据边界与下一步

入口核验使用显式自有回环HTTP适配器，未访问或改变IIS、证书和其他站点。更新器原回执的TLS字段不作为TLS通过证据；真实公网IIS/TLS、正常登录耗时和全部真实南港模板/权限/跨入口仍待。R39运输ZIP/最终双基线选择包装器尚未固定，没有上传或部署R39。R37原包已上传/预检但手动执行结果仍缺，不猜当前公网精确版本。

完成后按精确计划/备份SHA、实际进程退出、无引用、绝对范围及无重解析清理{clean_total_files}文件项，逻辑{clean_logical}B（含硬链接），两次D空闲变化合计{clean_observed}B，仅观察、不独占归因。原候选shared/r36/r37及源码/小型证据保留；合成数据库/上传/配置、正式18891、本机三维8767、项目资产和另一三维会话保持。426文件公开同步已完成；本批新增证据仅本地Git，未混入旧批准的公开清单。

下一固定运输包，逐文件和ZIP闭合/SHA、选择器及恢复身份边界验证后，再依据服务器实际版本走对应的严格预检与公网更新。完整UE对标引擎、EXE GIS/DLG点线面图层旗杆多源标牌、Web3D及单系统全南港B/S目标仍active/fullCloneReady=false，不新增完成比例。
'''
write(D/'实际双基线生命周期与21场景验收.md',guide)
hp=A/'deploy/handbook/native_plan_unified_lifecycle_r350_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R346—R350：R39两基线实际更新回滚通过，最终候选普通角色21场景通过

精确e935源分别从R36/R37执行真实旧版→apply_update→rollback_latest→正常停机，每份三控制器/每次六组件均0、实际Job后代零，398模型三时点一致；候选安装/运行预案类384462cf匹配、回滚恢复原缺失，四主JS/CSS gzip/缓存解压SHA均通过。每份894代码/指针前像及原虚构配置/安装身份恢复，G回e9dcd876；没有复制/覆盖数据库。

R37最终候选原控制器/编译页面/非管理员21场景0JS异常通过，含预案演练/附件/筛选重置/删除保护及带两演练父删除保持子记录、另预案与对象字节；新补旧详情导航/重试/刷新均明确提示且无旧表单，原API200/code0/null。未填满六关联或新跑SQL故障，不把这些或398结构当全南港验收。R348补充生成器初次CRLF断言在写前拒绝，修读取未改产品；旧R346无UI的R37运行源未执行。

两次清{clean_total_files}文件/逻辑{clean_logical}B（含硬链接），D变化合计{clean_observed}B不独占归因。仅回环HTTP入口适配，不是IIS/TLS；R39运输包装器/ZIP及公网验收仍待，R37手动执行回执缺，不能猜当前服务器版。本批仅本地Git，已完成426公开同步头faba43bf/edadba4c不变。无桌面/正式18891/8767/资产/另一三维断点变更。完整UE引擎/EXE DLG图层旗杆标牌/Web3D/全南港目标active/fullCloneReady=false，真实模板权限/跨入口仍待，不报新百分比。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith(stage.split('\n',1)[0]);write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R350两基线实际更新回滚与21场景'
assert marker not in old;write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/统一预案候选实际生命周期_R350_20261103.md';write(ep,stage+guide);engine.append('docs/project/统一预案候选实际生命周期_R350_20261103.md')
assert sha(held)==held_pin and sha(other)==other_pin and len(app)==len(set(app))and len(engine)==len(set(engine))
jout(D/'local-stage-files-r350.json',{'application':app,'engine':engine,'heldNativeSHA256':held_pin,'other3DBreakpointSHA256':other_pin,'publicPushed':False,'fullCloneReady':False})
print(json.dumps({'recorded':True,'applicationFiles':len(app),'engineFiles':len(engine),'bothActualLifecyclesPassed':True,'normalRoleBrowserCases':21,'publicPushed':False}))
