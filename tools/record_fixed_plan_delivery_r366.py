from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_unified_plan_r39_20261103';C=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'verified-stage-r366.json').exists()
proof=J(D/'verified-fixed-transport-r364.json');local=J(C/'verified-lifecycle-stage-r350.json');manifest=J(D/'delivery-manifest.json')
assert proof['passed']and proof['cleanTransportBuilderReproducedAll8FilesByteForByte']and local['bothExactBaselinesPassed']
assert sha(D/'delivery-manifest.json')==proof['manifestSHA256']=='4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de'
assert sum(p.stat().st_size for p in(D/'delivery').iterdir())==2165296 and len(list((D/'delivery').iterdir()))==8
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_pin=sha(held);other_pin=sha(other)
app=[];engine=[];pins=[]
names=['build_unified_plan_delivery_r351.py','refine_unified_plan_wrapper_r352.py','verify_unified_plan_delivery_r353.py',
 'prepare_short_transport_verification_r354.py','verify_unified_plan_delivery_r354.py','prepare_bounded_transport_verifier_r355.py','verify_unified_plan_delivery_r355.py',
 'cleanup_transport_verifiers_r358.ps1','add_scoped_delivery_result_r362.py','prepare_final_transport_checks_r363.py','verify_unified_plan_delivery_r364.py',
 'prepare_final_verifier_cleanup_r365.py','cleanup_final_verifier_r365.ps1','record_fixed_plan_delivery_r366.py']
historical={'refine_unified_plan_wrapper_r352.py','verify_unified_plan_delivery_r353.py','prepare_short_transport_verification_r354.py','verify_unified_plan_delivery_r354.py',
 'prepare_bounded_transport_verifier_r355.py','verify_unified_plan_delivery_r355.py','add_scoped_delivery_result_r362.py','prepare_final_transport_checks_r363.py'}
for name in names:
    src=V/name;raw=src.read_bytes();raw.decode('utf-8-sig')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    dst=T/name
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());pins.append({'path':app[-1],'bytes':len(raw),'sha256':sha(dst),'historicalDriverNotFinalBuildEntry':name in historical})
wrapper=T/'deploy_unified_plan_r39_20261103.py';raw=(D/'delivery/deploy_unified_plan_r39.py').read_bytes()
assert not wrapper.exists();wrapper.write_bytes(raw);app.append(wrapper.relative_to(A).as_posix());pins.append({'path':app[-1],'sha256':sha(wrapper),'matchesFixedDelivery':True})
cleanup=[J(D/name)for name in ['completed-verifier-cleanup-r358.json','completed-final-verifier-cleanup-r365.json']]
assert all(v['passed']for v in cleanup)
clean={'passed':True,'removedFileEntries':sum(int(v.get('removedFiles',0))for v in cleanup),'logicalBytes':sum(int(v['logicalBytes'])for v in cleanup),
 'observedDFreeDeltaNotUniquelyAttributed':sum(int(v['observedDFreeDelta'])for v in cleanup),'fixed8FilesSourceProofDatabaseAndAssetsRetained':True,
 'noProcessStopped':True,'actualServicesOrPublicOrDesktopTouched':False}
jout(D/'scoped-cleanup-r366.json',clean)
summary={'schema':'xnby.r366.fixed-dual-plan-delivery.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'passed':True,'manifestSHA256':proof['manifestSHA256'],'transportFiles':8,'transportBytes':2165296,'writes':187,'removals':177,
 'eachVariantAcceptsOneExactBase':True,'sharedFinalPayload':True,'productionMaximumExtractionPathCharacters':237,
 'all8FilesReproducedByteForByte':True,'archiveAndExtractionCases':14,'staticResponseValidatorCases':28,'baseSelectionCases':5,'recoveryGuards':12,
 'actualWrapperMainTestScenarios':10,'wrapperTestLifecycleAndIdentityAndIISExplicitSpies':True,
 'sameActualUpdaterDualSixComponentAnd21NativeUIEvidenceRetained':True,'limitedResultContainsNoCredentialsBusinessRowsOrRuntimeUUID':True,
 'postcheckRollbackRequiresSameSelectedBaseAndUnchangedAppliedRecord':True,'limitedResultClearedBeforeApplyAndScopedRollbackPhaseReported':True,
 'twoInitialTemporaryPathLengthDriverFailuresKeptNotProductFailures':True,'temporaryPathBudgetCheckedBeforeAllocation':True,
 'backgroundSavedFTPProbeNotConnected':True,'noFTPPasswordReadOrExported':True,'noUploadOrServerDeploymentOrDesktopInput':True,
 'newPublicGitPushed':False,'sourcePins':pins,'fullCloneReady':False}
jout(D/'verified-stage-r366.json',summary)
guide=f'''# 固定R39统一预案、原SQL与加载优化更新

交付8文件、2165296字节，清单SHA256 {proof['manifestSHA256']}。本地delivery目录与delivery-manifest.json为唯一固定交付；目标FTP /Zhumadian/Zhumadian_Unified_Plan_Runtime_20261103_R39/，应用C:/inetpub/wwwroot/Zhumadian/Application。原未答R38不另执行。

## 组成和严格基线

ZIP只放一份最终187文件载荷和两份基线清单，共190成员；R36旧release daaf0be2、R37旧909b64aa，各清单只接受自己一个精确旧release及对应更新器。包装器先选择精确已装版本，未知版本或旧更新器交叉均拒绝；不以两种路线模糊匹配任何旧版。最终release9a3a878a/payload773049fb相同，更新187路径、移除177旧应急前端路径，共364；原21或22控制到22。

包含已实测预案事务类384462cf（业务JDK17）、原XML默认扫描、R224真实编译前端和R37静态gzip/哈希缓存/IIS代理源码。原业务Jar、原登录鉴权/历史意见模块、真实私有配置、数据库、上传、安全端前端、IIS映射及其他站点保持。预案修正保留原不连删演练/对象行为，不编造被覆盖的历史意见。

## 实际证据与包装器证据分开

最终运行更新器e935f51a已从R36/R37分别在自有合成环境真实启动→apply_update→rollback_latest→正常停止，共六控制器/每次六组件正常0且实际Job后代零，398结构三时点一致。安装/实际运行预案类匹配，回滚恢复原不存在；R37最终候选非管理员21实际浏览器场景、零JS异常通过，含旧详情URL导航/重试/刷新明确提示及无旧内容。四主JS/CSS实际网关gzip/缓存与解压SHA通过，业务JS约2.62/2.58MB降至0.82/0.81MB；这不是公网耗时结论。

最终包装器八文件/190归档成员/187载荷逐SHA和两种实际解包通过；14归档/提取边界、28合成静态响应检查、5基线选择、12恢复边界及10条实际main路径通过。身份/完整load_bundle/生命周期/IIS在这些包装器路径明确为spy；实际候选Mapper/数值预算函数在任何服务前使用，不能把包装器spy测试当新的IIS或六组件运行证据。此前真实生命周期证据独立保留。另测阶段回执及3种外来/超大摘要拒绝，当前构建器干净重跑逐字重建全部8文件，但不宣称完整公开检出一键编译全业务。

首轮深可视化目录解包因Windows路径过长退出1；第二轮项目测试目录在完整UserData/staging层次下仍过长，同样未启动服务。保留失败来源，第三轮在分配前核完整临时路径并采用work/v39通过；最终生产路径上限237，不降低产品路径守卫。R351/R352/R362制作时快照保留，后续最终权威清单及verified-fixed-transport-r364.json覆盖状态；历史修补器不重复执行，当前build_unified_plan_delivery_r351.py直接重建最终字节。

## 发布、恢复与限定结果

先运行Check_Only_Unified_Plan_R39.cmd，必须精确已装R36或R37、文件/运行/数据身份、原11就绪、Mapper和停服前预算通过；再运行Deploy_Unified_Plan_R39.cmd正常停启六组件。正常部署后核原11项及预案运行类副本，实际网关与本机IIS/TLS压缩、缓存和HTML入口策略。包装器写r39-scoped-result.json，只有已达到的预检/部署开始/部署完成/本轮检查失败后已回滚阶段与固定版本、两项数值预算；不含凭据、账户会话、业务原文、运行UUID或原始日志。server-static-performance-result.json仅固定静态请求的摘要，外网HTTPS和登录后体验另验。

上线后静态检查失败时，只在最新更新记录仍逐字等于本次apply刚完成记录、updateId/旧基线/新release均匹配时正常rollback_latest；记录漂移时拒绝自动回滚，不覆盖外来状态。Recover_This_Unified_Plan_R39.cmd仅接受本包两种固定updateId与精确旧新SHA、OriginalPublicUpdates下32位本轮尝试目录；正常退出归属不明时停止，不强杀。恢复代码不覆盖数据库、上传或配置。

当前未上传/未部署R39，也未接管桌面。R37仍缺手动执行完成回执，不能猜公网精确版本。正常WinSCP后台保存站点连接探测未成功，未读取/导出口令，未传输文件；需要协调已有登录FTP窗口或提供正常可用后台认证通道。原生桌面工具禁止通过GUI直接或间接运行Windows终端命令，因此若继续走RDP，服务器脚本需由用户手动执行，不能用双击cmd或终端粘贴绕开工具限制。FTP传输不等于部署已完成。

## 上线后体验路线

正常登录公网首页→敏捷应急管理→应急预案：新增/编辑/详情、演练记录、部门筛选与重置、人员/附件展示。仅在测试者自己创建的记录上验证删除取消/确认、删除后已打开详情页重试刷新；保留演练和附件行为按原版处理。记录丢失不显示旧表单。应急处置和个人待办既有入口同时回归，完整真实南港模板/权限/通知与跨入口仍待；本包不声明全系统100%完成。

清理两轮自有验证副本共{clean['removedFileEntries']}文件项、逻辑{clean['logicalBytes']}B，D空闲变化合计{clean['observedDFreeDeltaNotUniquelyAttributed']}B，仅观察不独占归因；源码、固定8文件、证据、数据库/上传/资产保持。全UE引擎/EXE GIS DLG点线面图层旗杆多源标牌/Web3D/一系统全南港B/S目标仍active/fullCloneReady=false，另一三维会话断点保持；不报新百分比。
'''
write(D/'固定候选说明.md',guide)
for name in ['delivery-manifest.json','verified-fixed-transport-r364.json','archive-cases-r353.json','selection-and-recovery-cases-r353.json','wrapper-order-cases-r353.json','response-cases-r353.json','scoped-cleanup-r366.json','verified-stage-r366.json']:
    dst=A/'deploy/verification/unified_plan_fixed_r39_20261103'/name;write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
hp=A/'deploy/handbook/unified_plan_fixed_r39_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R351—R366：R39八文件运输及限定回执验证通过，未上传

固定8文件2165296B，manifest4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de。一份187载荷+两份严格旧基线清单/190ZIP成员，各只认R36或R37精确release/updater；同最终9a3a878a，187写入+177移除，22控制。最终包装器5bde327f、运行源e935保持；本轮源/构建器逐字重建8文件通过。

14归档/解包、28合成静态响应、5选择、12恢复及10实际main路径通过；实际预算/Mapper先于服务，身份/生命周期/IIS明确spy，R350两基线真实六组件与21UI证据独立保留。限定阶段结果只有匹配/阶段/数值，无账户/业务行/运行UUID；部署开始先清旧阶段，后检查失败只认同一选定基线且本次apply记录逐字未漂移才回滚。两次测试路径过长在服务前失败保留，短目录预算前置后通过，生产最长237；历史修补器不重复执行。

清{clean['removedFileEntries']}临时文件/逻辑{clean['logicalBytes']}B，D变化合计{clean['observedDFreeDeltaNotUniquelyAttributed']}B不独占归因。WinSCP正常后台已存站点只读探测未连通，未读口令/传输/桌面输入；后续协调FTP及服务器正常脚本执行。R37手动结果仍缺；R39未上传/未部署，实际IIS/TLS/外网登录耗时/真实南港流程权限跨入口仍待。公开426头faba43bf/edadba4c已完成，本轮仅本地Git，资产/正式18891/8767/另一三维断点保持。完整长期目标active/fullCloneReady=false，不报新百分比。详Deployment/public_test_unified_plan_r39_20261103/固定候选说明.md。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith(stage.split('\n',1)[0]);write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R366统一R39固定运输及限定回执'
assert marker not in old;write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/统一R39固定运输_R366_20261103.md';write(ep,stage+guide);engine.append('docs/project/统一R39固定运输_R366_20261103.md')
assert sha(held)==held_pin and sha(other)==other_pin and len(app)==len(set(app))and len(engine)==len(set(engine))
jout(D/'local-stage-files-r366.json',{'application':app,'engine':engine,'heldNativeSHA256':held_pin,'other3DBreakpointSHA256':other_pin,'publicPushed':False,'fullCloneReady':False})
print(json.dumps({'recorded':True,'applicationFiles':len(app),'engineFiles':len(engine),'manifestSHA256':proof['manifestSHA256'],'transportBytes':2165296,'uploadedOrDeployed':False,'publicGitPushed':False}))
