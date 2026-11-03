from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/native_plan_delete_roundtrip_r304_20261103'
D0=R/'Document/Deployment/native_plan_delete_roundtrip_r297_20261103';D1=R/'Document/Deployment/native_plan_delete_roundtrip_r301_20261103';D2=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
result=J(C/'r135/result.json');browser=J(C/'r135/plan-browser/result.json');terminal=J(C/'r135/controller-terminal.json');outer=J(C/'r135-outer-terminal.json');receipt=J(C/'r135/scoped-controller-receipt.json')
assert result['allPassed']and browser['passed']and len(browser['cases'])==14 and not browser['exceptions']
assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose']
assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
assert result['original398ModelsUnchanged']and result['connectionCapacityWithoutRefusals']
restored={name:J(C/'prepared-r135'/name)for name in ['frontend-restored.json','mapper-observer-restored.json','mapper-product-restored.json','history-runtime-restored.json']}
assert all(v['passed']for v in restored.values())and sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert sha(C/'r135/actual-host-source.py')==sha(T/'verify_full_controller_plan_delete_r304.py')
assert sha(C/'r135/actual-browser-source.mjs')==sha(T/'verify_native_plan_delete_r304_20261103.mjs')
assert J(C/'prepared-r135/mapper-product-scope.json')['newFiles']['tools/original_public_test_update.py']['sha256']=='f4eae55e6c2b35b4bee67d228bfc8904968ce49d86ea8265436e7e08b2e2964d'
clean=J(D/'completed-fixture-cleanup-r308.json');assert clean['passed']
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';heldpin=sha(held);otherpin=sha(other)
app=[];engine=[];sourcepins=[]
for prep,key in [(D0/'preparation-r297.json','sourcePins'),(D1/'prepared-result-r301.json','sourcePins'),(D/'prepared-result-r304.json','sourcePins')]:
    for name,pin in J(prep)[key].items():
        p=T/name;assert sha(p)==pin;app.append(p.relative_to(A).as_posix());sourcepins.append({'path':app[-1],'sha256':pin,'runtimeAccepted':name.endswith(('_r304.py','_r304_20261103.mjs'))})
names=['prepare_native_plan_delete_suite_r297.py','prepare_native_plan_delete_fixture_r298.py','run_native_plan_delete_fixture_r299.py',
 'restore_plan_delete_prestart_r300.py','prepare_retry_plan_delete_r301.py','restore_plan_delete_prestart_r302.py','run_retry_plan_delete_r302.py',
 'prepare_plan_delete_targeted_r304.py','restore_plan_delete_prestart_r305.py','run_plan_delete_targeted_r305.py',
 'probe_public_static_headers_r306.py','probe_public_static_get_r307.py','cleanup_native_plan_delete_r308.ps1','record_native_plan_delete_r309.py']
for name in names:
    src=V/name;dst=T/name;raw=src.read_bytes();raw.decode('utf-8')
    if name.endswith('.py'):ast.parse(raw,filename=name)
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());sourcepins.append({'path':app[-1],'sha256':sha(dst),'preparationToolsIncludeLaterCorrections':True})
summary={'schema':'xnby.r309.native-plan-delete-roundtrip.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'passed':True,'attempt':'r135','normalRoleActualCompiledBrowserCases':14,'newDeleteCases':3,
 'cases':browser['cases'],'javaScriptExceptions':0,
 'falseDeleteResponseInjectedInBrowserBeforeNetworkNotActualSQLFailure':True,
 'onlyNewOwnNoChildPlanDeletedAndUnrelatedOwnPlanExerciseAttachmentKept':True,
 'actualR263ParameterDefaultAndFinalR286RuntimeSourceUsed':True,
 'actualOriginalXMLStatementsRegistered':226,'originalModelsComparedUnchanged':398,
 'connectionCapacityWithoutRefusals':True,'controllerAndBrowserNormalZeroActualDescendantsZero':True,
 'allFourRestoreLayersPassedAndOriginalGReleaseRestored':True,
 'businessFixtureMetadataIsNotAnotherFixedPackageUpdate':True,
 'publicOrFormal18891OrScene8767OrDesktopChanged':False,'newProductCodeChangedByThisTest':False,
 'fullNangangTemplateOrWholeModuleAccepted':False,'fullCloneReady':False}
jout(D/'verified-result-r309.json',summary)
failures={'r133':{'reason':'available-memory-guard-before-allocation','minimumGiB':4,'casesExecuted':0,'normalReceiptsFabricated':False,'explicitPrestartRestorePassed':J(D0/'prestart-refusal-and-restore-r300.json')['passed']},
 'r134':{'reason':'test-driver-fixed-schema-reader-path-was-globally-replaced','phase':J(C/'r134/failure.json')['phase'],
 'casesExecuted':0,'actualSixComponentsNormallyExitedZero':True,'allRestoreLayersPassed':J(C/'prepared-r134/history-runtime-restored.json')['passed']},
 'r135':{'targetedASTAttemptConversionPreservesFixedDependencies':True,'admissionMinimumGiB':6,'passedBrowserCases':14},
 'noFailureCountedAsBusinessPass':True,'noMemoryThresholdLoweredOrUserApplicationsClosed':True}
jout(D/'retained-early-failures-r309.json',failures)
for src,name in [(V/'public-static-headers-r306.json','public-static-headers-r306.json'),(V/'public-static-get-r307.json','public-static-get-r307.json')]:write(D/name,src.read_text(encoding='utf-8'))
probe=J(D/'public-static-get-r307.json');assert probe['status']==200 and probe['decodedMatchesKnownUnchangedSecurityBundle']
scoped_clean={k:v for k,v in clean.items()if k!='targets'};scoped_clean['targets']=[{k:v for k,v in row.items()if k!='path'}for row in clean['targets']];jout(D/'scoped-cleanup-r308.json',scoped_clean)
source_report={'sourcePins':sourcepins,'actualFinalHostAndBrowserSourcesExactlyMatchCapturedRun':True,
 'failedPrototypeSourcesRetainedButNotAccepted':True,'publicPushed':False};jout(D/'source-pins-r309.json',source_report)
for name in ['verified-result-r309.json','retained-early-failures-r309.json','public-static-headers-r306.json','public-static-get-r307.json','scoped-cleanup-r308.json','source-pins-r309.json']:
    dst=A/'deploy/verification/native_plan_delete_r309_20261103'/name;write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
guide=f'''# 普通角色预案删除往返验收与公网静态观察

R135实际原六组件、正常非管理员登录及真实编译页面共14场景通过，JavaScript异常0。沿用此前预案/演练11场景，补充3项删除链：取消不发删除请求且记录保留；浏览器在发网前返回code=0/data=false时，记录保留并提示“删除未完成”，不提示成功；再次真实确认仅发一次删除，目标从列表和后台回读消失，另一条预案及其演练、人员与附件保持。

只删除本轮新建、确认无演练子记录的合成预案；没有据此宣称带子记录父预案的级联删除语义。失败响应是浏览器响应注入，没有执行SQL故障回滚。当前编译版本确认钩子原已正确，本阶段没有据旧Reference源码重复修改产品。

实际R263默认参数、最终f4eae55e运行模块及R224候选前端运行；原XML226注册、398张原表结构与连接容量均通过。该业务夹具的元数据适配不等于另一次固定包安装；固定包实际apply/rollback证据仍见R294。控制器、六组件、Chrome、外层Windows Job全部正常退出/后代零，前端、观察器、产品参数、历史模块和虚构配置逐哈希恢复，G原release回e9dcd876。session10369终态0，不重复轮询/重启。

## 两次未计通过的尝试

R133在分配测试根目录/启动服务之前被4GiB可用内存守卫拒绝，精确反向校验五层原像后恢复530路径，没有伪造正常停服回执。随后实际可用内存恢复，R134以新编号运行六组件，但测试驱动全局替换误改固定schema-reader目录，浏览器前失败，正常退出与恢复。R135改用AST只变测试编号字面量，启动前核固定目录并要求至少6GiB内存余量，才完成14场景。两次失败保留，不算产品通过；没有降低原运行门槛或关闭用户应用。

## 公网观察

匿名HEAD与GET均保留TLS校验，没有Cookie/登录/业务响应读取。{probe['at']}，公网主JS GET为200，传输{probe['wireBytes']}字节，未返回Content-Encoding，Cache-Control仍为no-store，解码SHA与已知安全端脚本一致。这说明该次请求未呈现候选gzip/哈希缓存优化；不能据它确认精确服务器发布版本。网页读取工具不可达并不等于网站不可达，独立HTTPS探测实际成功。

R37只知已上传/预检，手动执行结果与实际部署记录仍待；不假定已上线或要求重复执行。R38第二稿8文件2114220B、清单3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956保持，尚未上传，只接受精确R36。若R37已执行先核版本重制。实际IIS/TLS、外网优化与正常登录体验仍待，未完成全部南港真实模板/权限及综合与快捷入口一致性验收。

## 存储和目标

三次自有准备原像及一份已退出Chrome配置已核精确SHA、绝对范围、无进程引用/无重解析后清理：{int(clean['removedFileEntries'])}文件项、逻辑{int(clean['logicalBytes'])}B，D空闲观察增加{int(clean['observedDFreeDelta'])}B，不独占归因。源、失败/成功证据、原合成数据库与上传保留。公网/正式18891/8767、用户浏览器及另一三维断点保持。

完整UE对标引擎、独立EXE GIS/DLG点线面图层旗杆多源标牌、网页三维和全南港B/S目标继续active。按一套系统唯一业务验收，不把14测试、226 SQL或398模型当作完成率分母；fullCloneReady=false。公开Git本批未推送。
'''
write(D/'业务验收与当前公网状态.md',guide)
hp=A/'deploy/handbook/native_plan_delete_r309_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
note='> 后续业务验收：R135普通角色原预案/演练及删除往返共14场景通过；实际IIS/TLS与公网部署仍待。详 native_plan_delete_roundtrip_r304_20261103/业务验收与当前公网状态.md。\n\n'
fixed=D2/'固定候选说明.md';old=fixed.read_text(encoding='utf-8')
if not old.startswith('> 后续业务验收：'):write(fixed,note+old)
hp=A/'deploy/handbook/unified_original_mappers_r38_r2_fixed_scope_20261103.md';write(hp,fixed.read_text(encoding='utf-8'));app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R297—R309：普通角色14场景通过，删除取消/失败/确认及无关预案附件保持；公网仍未见压缩

r135实际六组件/原SDK正常角色/候选前端14场景0JS异常；新增3删除场景仅本轮新建无子记录预案，取消零请求、浏览器false无发网写入且失败提示、真实确认一次删除，另一预案演练两人员/附件保持。不是带子记录级联验收或SQL故障。226原XML注册/398结构/容量通过、Chrome/六组件/外层Job正常0后代零，五层代码配置精确恢复，G回e9dcd876。session10369终态0勿重复。

r133内存守卫在分配前拒绝，530路径按前像恢复且无伪造正常回执；r134驱动误改固定schema-reader路径，浏览器前失败、六组件正常退出恢复；均保留不计通过。r135用AST仅改编号并核固定依赖/6GiB前置，运行4GiB门槛未降。清1308文件项/逻辑73836581B、D观察+75505664B不独占归因，源/证据/DB上传/正式18891/8767/另一三维保持。当前无本轮进程。

16:57匿名公网GET主JS200/2624898B、无gzip且no-store，解码SHA匹配原安全脚本；仅说明该请求未呈现优化，不据此确认精确服务器版本。R37手动执行/记录仍缺、批准有效，R38第二稿固定3882688c不变/未上传/仅R36，若R37已运行先重制。未桌面接管、新公开Git或产品业务代码变更；仅补实证与测试驱动。详Deployment/native_plan_delete_roundtrip_r304_20261103。全南港真实模板及权限/跨入口/实际IIS公网仍待，完整长期目标active/fullCloneReady=false。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8')
    if not old.startswith('## 2026-11-03 R297—R309：'):write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R309普通角色预案删除往返与公网观察'
if marker not in old:write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1])
engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/预案删除普通角色验收_R309_20261103.md';write(ep,stage+guide);engine.append('docs/project/预案删除普通角色验收_R309_20261103.md')
assert sha(held)==heldpin and sha(other)==otherpin
jout(D/'local-stage-files-r309.json',{'application':app,'engine':engine,'heldNativeSHA256':heldpin,'other3DBreakpointSHA256':otherpin,'publicPushed':False})
print(json.dumps({'passed':True,'applicationFiles':len(app),'engineFiles':len(engine),'businessBrowserCases':14,'allOwnedRestored':True,'publicPushed':False}))
