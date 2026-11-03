from pathlib import Path
import ast,datetime,hashlib,json

R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_exercise_department_filter_verified_r320_20261103'
D0=R/'Document/Deployment/native_exercise_department_filter_r317_20261103'
D1=R/'Document/Deployment/exercise_department_frontend_candidate_r319_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'verified-result-r324.json').exists()
result=J(C/'r139/result.json');browser=J(C/'r139/plan-browser/result.json')
evidence=J(C/'r139/plan-browser/department-filter-reset-evidence.json')
assert result['allPassed']and result['original398ModelsUnchanged']and result['connectionCapacityWithoutRefusals']
assert browser['passed']and len(browser['cases'])==16 and not browser['exceptions']
assert evidence['passed']and evidence['filteredRows']==1 and evidence['resetRows']==2 and evidence['actualVisibleRowsMatchedBothResponses']
assert evidence['requestShape']['canonicalOrganizeDepartmentNonempty']and not evidence['resetRequestShape']['canonicalOrganizeDepartmentNonempty']
assert sha(C/'r139/actual-host-source.py')==sha(T/'verify_full_controller_exercise_filter_r320.py')
assert sha(C/'r139/actual-browser-source.mjs')==sha(T/'verify_native_exercise_filter_r320_20261103.mjs')
for attempt,outer_exit in [('r137',1),('r139',0)]:
    outer=J(C/(attempt+'-outer-terminal.json'));term=J(C/attempt/'controller-terminal.json')
    receipt=J(C/attempt/'scoped-controller-receipt.json');bt=J(C/attempt/'plan-browser/browser-terminal.json')
    assert outer['exitCode']==outer_exit and outer['actualDescendantsZeroBeforeClose']
    assert term['exitCode']==0 and term['actualDescendantJobCountZeroBeforeClose']
    assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
    assert bt['chromeExitCode']==0 and bt['normalBrowserClose']
    for name in ['frontend-restored.json','mapper-observer-restored.json','mapper-product-restored.json','history-runtime-restored.json']:
        assert J(C/('prepared-'+attempt)/name)['passed']
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
old=J(C/'r137/plan-browser/failure.json')
assert old['message']=='EXPECTED_LEGACY_DEPARTMENT_FILTER_REPRO_NOT_OBSERVED'and old['http'][-1]['exerciseTotal']==1
withdrawn=J(D1/'withdrawn-status-r320.json');assert withdrawn['withdrawn']and not withdrawn['candidateCompiled']and not withdrawn['candidateInstalled']
clean=J(D/'completed-fixture-cleanup-r323.json');assert clean['passed']
rules=J(D/'source-rule-audit-r322.json');assert rules['passed']
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md'
held_sha=sha(held);other_sha=sha(other)
app=[];engine=[];pins=[]
for document in [D0/'prepared-result-r317.json',D/'prepared-result-r317.json',D1/'source-preparation-r319.json']:
    for name,pin in J(document)['sourcePins'].items():
        p=T/name;assert sha(p)==pin;app.append(p.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':pin,
            'withdrawnUncompiledCandidate':document.parent==D1})
for name in ['prepare_exercise_department_repro_r317.py','run_exercise_department_repro_r318.py',
             'restore_exercise_department_prestart_r318.py','prepare_exercise_department_fix_r319.py',
             'prepare_exercise_department_verified_r320.py','prepare_exercise_department_verified_generated_r320.py',
             'run_exercise_department_verified_r321.py','restore_exercise_department_prestart_r321.py',
             'audit_exercise_department_and_plan_delete_r322.py','prepare_cleanup_exercise_department_r323.py',
             'cleanup_exercise_department_r323.ps1','record_exercise_department_r324.py']:
    src=V/name;raw=src.read_bytes();raw.decode('utf-8-sig')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    dst=T/name
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':sha(dst),'localToolsOnlyThisStage':True})
summary={'schema':'xnby.r324.native-exercise-department.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'passed':True,'attempt':'r139','normalRoleActualCompiledBrowserCases':16,'newFilterAndResetCases':2,
 'cases':browser['cases'],'javaScriptExceptions':0,'originalXMLStatementsActuallyRegistered':226,
 'originalModelsComparedUnchanged':398,'connectionCapacityPassed':True,
 'departmentFilterRowsBeforeSelectedReset':[2,1,2],
 'canonicalOrganizeDepartmentParameterActuallySent':True,'legacyDepartmentAlsoPresentButNotUsedByOriginalQuery':True,
 'resetClearsBothParametersAndVisibleRowsMatchResponses':True,
 'initialLegacyBindingDefectHypothesisDisproved':True,'r137BadHypothesisAssertionRetainedNotCountedAsPass':True,
 'r319SpeculativeFixWithdrawnBeforeCompilationOrInstallation':True,
 'productCodeOrSchemaChangedByThisStage':False,'allOwnedComponentsAndChromeNormalZeroActualDescendantsZero':True,
 'allCodeAndSyntheticConfigurationRestoreLayersPassedOriginalGReleaseRestored':True,
 'metadataRunPointerNotClaimedRestored':True,'publicFormalOrSceneOrDesktopChanged':False,
 'planDeleteWithExercisesStillNotRuntimeAccepted':True,'fullNangangAccepted':False,'fullCloneReady':False}
jout(D/'verified-result-r324.json',summary)
jout(D/'department-filter-and-reset-r324.json',evidence)
failure={'attempt':'r137','phase':old['stage'],'message':old['message'],'completedEarlierCases':len(old['cases']),
 'actualFilteredRowsObserved':old['http'][-1]['exerciseTotal'],'javaScriptExceptions':len(old['exceptions']),
 'testHypothesisWrongNotProductFailure':True,'outerExitCode':1,'controllerAndSixComponentsNormalZero':True,
 'allRestoreLayersPassed':True,'candidateFixCompiledOrInstalled':False}
jout(D/'retained-hypothesis-failure-r324.json',failure)
scoped_clean={k:v for k,v in clean.items()if k!='targets'}
scoped_clean['targets']=[{k:v for k,v in row.items()if k!='path'}for row in clean['targets']]
jout(D/'scoped-cleanup-r323.json',scoped_clean)
jout(D/'source-pins-r324.json',{'sources':pins,'finalCapturedHostAndBrowserExactlyMatchSources':True,'newPublicGitPushed':False})
guide=f'''# 演练部门筛选及重置真实验收，原预案删除规则核对

## 实际结果

R139自有六组件、原SDK普通角色、R224真实编译前端完成16个场景，JavaScript异常0。在同一合成预案下建立两条演练，一条带组织部门、一条未选部门。真实列表选择组织部门并搜索后，实际GET携带organizeDepartment且返回1条；重置后两个部门参数均清空并恢复2条，页面可见记录与原后端响应一致。选择与重置不写业务数据；前期创建/编辑只涉及自有合成记录。

复测路径为“敏捷应急管理→应急预案→某预案的演练记录→组织部门→搜索→重置”。本次验收对象是本地候选，不能冒称当前公网页面已完成该验收。其余14场景沿用原普通角色新增、必填/电话校验、编辑/只读详情、选人、真实上传/失败保留/一次保存、附件下载以及无子记录删除取消/失败/确认往返。

## 撤回未经证实的修正

R137先推测页面render中searchParam.department与原后端organizeDepartment不一致会导致筛选失效；真实返回已经是1条，所以“应返回2条”的缺陷复现断言失败，完成的11旧场景不冒称整轮通过。通用SearchFormItem依据列prop再次绑定规范字段，实际请求同时有旧department和正确organizeDepartment。原查询使用正确字段，筛选生效。R139明确核规范参数、实际结果行及重置，16场景才通过。

R319仅准备了替换旧写法的独立适配/构建工具，尚未编译或安装；发现假设错误后明确撤回，保留来源和状态，不将其纳入产品或固定发布包。源文件中的旧写法不能单独作为实际故障证据，本轮没有新的产品修复。

## 删除关联范围

对固定南港Reference和当前原子事务适配器的源码核对表明：删除预案清父记录、六类资源/人员关联及其附件元数据，没有显式连带删除emergency_exercise或对象存储文件的代码。当前适配保留该集合并补事务/写入检查；这只是规则核对，不等于带演练父预案删除的实际运行验收，更不据此擅自扩大删除范围。该业务分支仍待实际验证。

## 退出、恢复和边界

R137外层测试退出1（错误假设断言），R139外层退出0；两轮实际六组件、Chrome及控制器均正常0，真实Job后代零，五层代码/虚构配置均精确恢复，G原release回e9dcd876。R139原XML226注册/398模型/容量均通过；这些数量不是功能完成率。会话90658已终态0，不重复轮询或重启。

按精确绝对路径、SHA、无活动引用/无重解析清本轮10份准备原像及2份已退出Chrome配置：{int(clean['removedFileEntries'])}文件项、逻辑{int(clean['logicalBytes'])}B，D盘观察增加{int(clean['observedDFreeDelta'])}B，不独占归因；源码、失败/成功证据、自有数据库/上传保留。

公网、正式18891、三维8767、用户桌面/浏览器及另一三维专属断点保持。R37执行完成记录仍待；R38第二稿8文件2114220B、manifest3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956保持、未上传，仅接受精确R36，若R37已执行先核版本重制。426文件公开候选清单e85505cd4c17272cf03d76ee4897c934fe709ae101fd2df130be3d493ca2ac21保持原字节待答，本轮新增源码/证据不擅自夹入。

完整UE对标引擎、EXE GIS/DLG点线面图层旗杆多源标牌、网页三维及一套信息系统的全南港B/S目标继续active。全部真实模板、权限/跨入口一致性、实际IIS/HTTPS及加载体验仍待；不报未经去重验收的新百分比，fullCloneReady=false。
'''
write(D/'演练部门筛选验收与假设修正.md',guide)
for name in ['verified-result-r324.json','department-filter-and-reset-r324.json','retained-hypothesis-failure-r324.json',
             'scoped-cleanup-r323.json','source-pins-r324.json','source-rule-audit-r322.json']:
    dst=A/'deploy/verification/exercise_department_r324_20261103'/name
    write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
dst=A/'deploy/verification/exercise_department_r324_20261103/withdrawn-status-r320.json'
write(dst,(D1/'withdrawn-status-r320.json').read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
hp=A/'deploy/handbook/exercise_department_r324_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage='''## 2026-11-03 R317—R324：演练部门筛选及重置16场景通过，推测性修正撤回

自有r139原六组件/普通角色/R224编译前端16场景0JS异常；同预案两演练部门筛选2→1、重置1→2，实际organizeDepartment参数及页面行均核对。R137曾据旧render写法推测无效，实际1条导致错误假设断言失败；SearchFormItem按列prop补规范绑定，请求旧/正确字段都有，不能据局部源码称故障。R319三个适配/构建源仅准备、未编译/安装，现明确撤回；本轮未改产品或模型。

两轮六组件/Chrome/控制器正常0、Job后代零，五层代码/虚构配置恢复、G回e9dcd876；r137外层1不冒称通过，r139/session90658终态0勿重复。226原XML/398模型/容量通过。清1195文件/逻辑64458160B、D观察+65736704B不独占归因，源/证据/数据库上传保持。原预案删除源码只显式清父/六关联/自有附件元数据，不连删演练或对象文件，带演练父删除运行验收仍待。

本轮后台自有验证，公网/正式18891/8767、用户桌面及另一三维断点保持。R37执行结果仍待；R38第二稿固定3882688c未上传/仅R36，若R37已执行先核版本重制。426文件公开候选e85505cd清单不变待答，本轮增量仅本地Git，不夹入固定公开范围。详Deployment/native_exercise_department_filter_verified_r320_20261103/演练部门筛选验收与假设修正.md。真实南港模板/权限/跨入口/IIS公网仍待；全UE引擎/EXE GIS DLG图层旗杆标牌/Web3D/南港B/S目标active/fullCloneReady=false，未给新比例。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith('## 2026-11-03 R317—R324：');write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8')
assert '## 2026-11-03 R324演练筛选真实验收与推测修正'not in old
write(log,old+'\n\n## 2026-11-03 R324演练筛选真实验收与推测修正\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/演练部门筛选真实验收_R324_20261103.md';write(ep,stage+guide);engine.append('docs/project/演练部门筛选真实验收_R324_20261103.md')
assert sha(held)==held_sha and sha(other)==other_sha and len(app)==len(set(app))and len(engine)==len(set(engine))
fixed=R/'Document/Deployment/public_source_checkpoint_r313_20261103/public-git-sync-r313-manifest.json'
assert sha(fixed)=='e85505cd4c17272cf03d76ee4897c934fe709ae101fd2df130be3d493ca2ac21'
jout(D/'local-stage-files-r324.json',{'application':app,'engine':engine,'heldNativeSHA256':held_sha,'other3DBreakpointSHA256':other_sha,
 'pending426PublicManifestUnchanged':True,'publicPushed':False})
print(json.dumps({'passed':True,'browserCases':16,'productFixWithdrawnBeforeCompile':True,'localApplicationFiles':len(app),'localEngineFiles':len(engine),'publicPushed':False}))
