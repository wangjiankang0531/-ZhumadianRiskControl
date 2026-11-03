from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2'
D1=R/'Document/Deployment/public_test_unified_mappers_r38_20261103'
G=R/'Document/Deployment/original_mapper_install_preflight_r285_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
prep=J(D/'preparation-result.json');md=J(D/'delivery-manifest.json');clean=J(D/'completed-fixture-cleanup-r290.json')
assert sha(D/'delivery-manifest.json')==prep['manifestSHA256']=='3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956'
assert clean['passed'] and J(D/'independent-fixed-delivery-verification.json')['passed']
assert J(G/'verified-cases-r287.json')['checks']==20
for name,pin in md['files'].items():p=D/'delivery'/name;assert p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']
assert sum(p.stat().st_size for p in(D/'delivery').iterdir())==2114220
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_pin=sha(held);other_pin=sha(other)
app=[];engine=[];sources=[]
names=['reproduce_mapper_preflight_gap_r285.py','prepare_mapper_install_gate_r286.py','verify_mapper_install_gate_r287.py',
 'prepare_unified_snapshot_candidate_r288.py','verify_unified_full_program_r288.py','verify_unified_composition_recovery_r288.py',
 'build_unified_snapshot_delivery_r289.py','verify_unified_snapshot_delivery_r289.py','prepare_snapshot_cleanup_r290.py',
 'cleanup_unified_snapshot_fixtures_r290.ps1','record_mapper_snapshot_stage_r291.py']
for name in names:
    src=V/name;dst=T/name;raw=src.read_bytes();raw.decode('utf-8')
    if name.endswith('.py'):ast.parse(raw,filename=name)
    if dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());sources.append({'path':app[-1],'sha256':sha(dst),'bytes':len(raw)})
for src,dst in [(T/'original_public_test_update_r38_mapper_preflight_r286.py',T/'original_public_test_update_r38_mapper_preflight_r286.py'),
                (D/'delivery/deploy_unified_mappers_r38.py',T/'deploy_unified_mappers_r38_r2_20261103.py')]:
    if src!=dst:
        if dst.exists():assert dst.read_bytes()==src.read_bytes()
        else:dst.write_bytes(src.read_bytes())
    ast.parse(dst.read_bytes());app.append(dst.relative_to(A).as_posix());sources.append({'path':app[-1],'sha256':sha(dst),'bytes':dst.stat().st_size})
for source,name in [(G/'reproduction.json','mapper-preflight-gap-r285.json'),(G/'candidate-preparation-r286.json','mapper-candidate-preparation-r286.json'),(G/'verified-cases-r287.json','mapper-install-gate-r287.json')]:write(D/name,source.read_text(encoding='utf-8'))
summary={'schema':'xnby.r291.unified-snapshot-candidate.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'previousUnpublishedCandidateWithdrawn':True,'previousManifestSHA256':sha(D1/'delivery-manifest.json'),
 'manifestSHA256':sha(D/'delivery-manifest.json'),'transportFiles':8,'transportBytes':2114220,
 'writes':186,'removals':177,'sourcePins':sources,'mapperGapActuallyReproduced':True,
 'sameSnapshotInstallPreflightChecks':20,'configurationChangeAfterOuterGateAndAfterSnapshotRefusedBeforeStop':True,
 'fullProgramPreflightFiles':15557,'negativeCompositionCases':45,'actualFileBackupReplaceRestoreScenarios':14,
 'independentClosedArchiveAndWrapperChecksPassed':True,'newUpdaterApplyUpdateSixComponentLifecyclePassed':False,
 'actualApplyUpdatePreStopRejectionPathsUsedExplicitIdentityIngressSpies':True,
 'realServerIISHTTPSAndAuthenticatedTimingStillPending':True,'actualNginxR278UnchangedByteEvidenceReused':True,
 'publicUploadedOrDeployed':False,'newPublicGitPushed':False,'r37HumanApplyResultStillMissing':True,
 'r37ApprovalAndFixedPayloadUnchanged':True,'acceptsOnlyR36R37RequiresRebase':True,
 'heldNativeAndOther3DBreakpointUnchanged':True,'fullCloneReady':False}
jout(D/'verified-stage-r291.json',summary)
proof_names=['delivery-manifest.json','bundle-preparation-r288.json','preparation-result.json','full-program-preflight.json',
 'composition-negative-cases.json','composition-and-recovery.json','independent-fixed-delivery-verification.json',
 'response-checker-cases.json','mapper-preflight-gap-r285.json','mapper-candidate-preparation-r286.json',
 'mapper-install-gate-r287.json','completed-fixture-cleanup-r290.json','verified-stage-r291.json']
for name in proof_names:
    dst=A/'deploy/verification/unified_original_mappers_r38_r2_20261103'/name
    write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
withdraw=A/'deploy/verification/unified_original_mappers_r38_20261103/withdrawn-status-r285.json'
write(withdraw,(D1/'withdrawn-status-r285.json').read_text(encoding='utf-8'));app.append(withdraw.relative_to(A).as_posix())
scope=f'''# R38 第二稿：安装事务内的配置快照检查

本稿尚未上传或部署。最终八文件共 2,114,220 字节，清单 SHA256 为 `{prep['manifestSHA256']}`，FTP 候选目录为 `/Zhumadian/Zhumadian_Unified_Original_Mappers_20261103_R38_R2/`。186 写入、177 旧应急前端移除。完整文件清单见同目录 delivery-manifest.json。

## 撤回第一稿的原因和修正

R285 用虚构配置实测：第一稿只在外层包装器验证 Mapper 设置。外层检查通过后、apply_update 重新取配置快照前，若配置变化为未知显式扫描路径，内部原数值预算检查仍可通过并进入 owned_ready。六项复现保留；测试在显式 spy 处截停，没有实际停启服务、查询数据库或访问公网。这是候选部署前置检查缺口，不是已经证实的公网事故。

第二稿把配置检查加入 candidate_runtime_pool_preflight：Mapper 和连接预算使用同一份有界原始配置，既有停服前 SHA 守卫继续核该快照。未知、空、冲突及不支持的显式路径在服务检查前拒绝；快照之后配置变化则由既有 SHA 守卫在 normal_stop 前拒绝。只有未显式指定或精确原 Jar `/xml/**/*.xml` 路径接受，配置值及凭据不输出。正常停服、启动、备份替换、恢复及回滚函数保持；原产品参数默认扫描行为未另改。

未上传的第一稿清单 `72b7d48b...` 已撤回，保留历史字节与证据，不再发布。R37 固定性能包和已有批准完全不变。R38 第二稿仍仅接受精确 R36；如 R37 已手动执行，先查当前版本并重新制作基线适配包，不能直接套用本稿。

## 证据和限制

- 新增 20 检查通过：配置、环境、JVM/应用参数、空值/冲突/类型，以及真实 apply_update 前置体中的两种变化拒绝。owned_ready/ingress 在拒绝路径中明确为测试 spy，服务函数禁止调用，不能宣称已跑实际六组件发布生命周期。
- 新源码 SHA `{md['newUpdaterSHA256']}` 的完整 15,557 程序 load_bundle 预检通过，原只读程序未变，候选参数和事务内检查通过。
- 45 组合边界全部拒绝；363 路径实际 backup/replace/restore 的 11 正常/故障加 3 漂移场景通过，私有/用户数据哨兵保持。
- 八文件哈希、闭合 ZIP、全部 186 载荷、实际解包、预算顺序、28 响应校验样例及 5 本次恢复守卫通过。包装器身份/就绪为显式 spy，服务器实际身份未在本轮核验。
- 前端和代理字节与前稿相同，复用 R278 真实 Nginx 两模式各 12 请求结果：JS 传输约减 69%、CSS 约减 85%、解压一致；不是公网登录后耗时。未再运行被 Windows 拒绝的 .NET 测试程序，未恢复隔离或修改安全设置。
- R272 的实际原六组件 226 原 XML 注册、预案演练 11 阶段及任务/并行/附件 9 阶段证据保持。这不是全部南港 SQL、模板、权限和入口一致性已验收。

最终源码尚未独立执行完整 apply_update/rollback 六组件生命周期；公网 IIS/HTTPS、登录后体验和真实全流程仍待。安装后的包装器含 gateway 与本机 IIS TLS 的 14 项探测，只有运行后才能计通过。探测失败时保留本轮精确记录，按退出归属和前后 SHA 决定恢复，不假称所有失败自动回滚，不强杀。

原业务 Jar/SQL、鉴权、独立意见历史、数据库结构和原行、真实配置、上传、安全端前端、IIS 映射保持；不自动写公网测试业务。成功核 HTTPS/正常用户页面后才按精确旧清单、已停无引用及无重解析清旧运输包和代码副本，全部数据保留。

## 状态与存储

R37 已上传且此前 check-only 通过，手动执行结果尚未收到；不重复执行、不假定已上线，也不自动换成新候选。Computer Use 禁止 GUI 直接/间接运行终端命令，桌面需先提示并取得当前交接，固定命令须用户手动提交或采用另有正常命令通道；本轮未操作桌面。

四个已完成的自有第二稿临时副本清理 {int(clean['removedFileEntries']):,} 文件项，逻辑 {int(clean['logicalBytes']):,} 字节；D 盘空闲观察增加 {int(clean['observedDFreeDelta']):,} 字节，不把只读硬链接逻辑尺寸当成释放量，也不独占归因。固定源码/bundle/delivery/证据保留，数据库、Assets、正式 18891、8767 和另一三维断点不变。

完整 UE 对标引擎、EXE GIS/DLG 点线面/图层/旗杆多源标牌、网页三维和全南港 B/S 目标继续 active。按一套系统的唯一业务验收，不以八入口、SQL 数量或静态文件数量计算百分比；fullCloneReady=false。公开 Git 本批尚未推送，旧 30 文件待答范围不扩大。
'''
write(D/'固定候选说明.md',scope)
hp=A/'deploy/handbook/unified_original_mappers_r38_r2_fixed_scope_20261103.md';write(hp,scope);app.append(hp.relative_to(A).as_posix())
experience='''# 预案/演练、任务与加载优化：第二稿体验说明

第二稿尚未上线。第一稿已撤回；R37 的手动执行结果仍待确认。当前不能把本地测试成绩当作公网体验结果。

业务修正沿用已验证候选：预案新增/编辑/只读详情和校验；演练空选人员的保存与列表回读；附件上传未发出/失败时阻止提交并保留输入、一次重试；任务防重复保存、处置反馈、独立并行分支、末级已办和附件下载。上线后从“敏捷应急管理”及“应急处置”按相同角色核同一记录，综合与快捷入口的数据、状态、附件和节点权限应一致。

加载优化验证分首次访问、再次访问、刷新和跨模块记录。真实本地 Nginx 主脚本传输约减少69%，HTML/API/错误不长期缓存；公网登录后等候多少秒仍待测量。遇列表空要区分接口失败、认证失败与真实无数据，不据此判断原数据已删除。

本轮补的是部署前配置变化保护，不改变上述业务 UI。没有新增公网测试数据；真实业务新增/审批需要安排测试者按权限操作。完整原模板、权限、通知及实际服务器部署生命周期仍未全部验收。固定范围及证据见 D:\\Project\\Zhumadian\\Document\\Deployment\\public_test_unified_mappers_r38_20261103_r2。
'''
hp=A/'deploy/handbook/unified_original_mappers_r38_r2_experience_20261103.md';write(hp,experience);app.append(hp.relative_to(A).as_posix())
notice='> 2026-11-03：本第一稿已撤回，不再发布。安装事务内配置快照检查的第二稿见 D:\\Project\\Zhumadian\\Document\\Deployment\\public_test_unified_mappers_r38_20261103_r2；第二稿也尚未上线。\n\n'
for p in [D1/'固定候选说明.md',A/'deploy/handbook/unified_original_mappers_r38_20261103.md',A/'deploy/handbook/unified_original_mappers_r38_fixed_scope_20261103.md']:
    old=p.read_text(encoding='utf-8')
    if not old.startswith('> 2026-11-03：本第一稿已撤回'):write(p,notice+old)
    if p.is_relative_to(A):app.append(p.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R285—R291：统一候选事务内配置快照缺口复现并修正，第二稿验证完成未上线

R285六项复现第一稿外层Mapper检查后配置变化可进入内部服务核验；没有实际服务/SQL/公网操作。R286只改candidate_runtime_pool_preflight并加纯检查，Mapper与预算同一原始配置/停服前SHA；R287二十项通过，真实apply_update前置体在未知配置或快照后变化时均在normal_stop前拒绝，身份/ingress明确spy。不得把它称六组件安装/回滚生命周期通过。

第二稿8文件2114220B，manifest3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956，源码f4eae55e，186写入+177移除。15557完整程序、45拒绝、14文件恢复/漂移场景、闭合归档与包装器28响应/5守卫再核通过；正常停启/替换恢复函数保持，完整新更新器生命周期、实际IIS/HTTPS/登录后耗时仍待。R278相同前端/代理传输证据复用，不重跑被拒绝.NET，不碰隔离/杀软；R272原六组件226注册及11+9业务阶段保持。旧72b7第一稿明确撤回，历史证据保留。

R37原批准与包不变，手动执行结果仍缺；新稿只接受精确R36，若R37已运行先核版本并重制。未接管桌面、未上传/部署或新公开Git。清本轮4自有副本{int(clean['removedFileEntries'])}文件项/逻辑{int(clean['logicalBytes'])}B、D观察+{int(clean['observedDFreeDelta'])}B不独占归因，源/固定包/DB/资产/正式18891/8767及另一三维断点保持。完整长期目标active/fullCloneReady=false，按一系统业务去重，未给新百分比。详Deployment/public_test_unified_mappers_r38_20261103_r2。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8')
    if not old.startswith('## 2026-11-03 R285—R291：'):write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R291事务内快照检查第二稿'
if marker not in old:write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1])
engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/原SQL安装预检第二稿_R38r2_20261103.md';write(ep,stage+scope);engine.append('docs/project/原SQL安装预检第二稿_R38r2_20261103.md')
assert sha(held)==held_pin and sha(other)==other_pin
jout(D/'local-stage-files-r291.json',{'application':app,'engine':engine,'heldNativeSHA256':held_pin,
 'other3DBreakpointSHA256':other_pin,'publicScopeNotAuthorizedByThisRecord':True})
print(json.dumps({'passed':True,'applicationFiles':len(app),'engineFiles':len(engine),'finalManifestSHA256':sha(D/'delivery-manifest.json'),'oldCandidateWithdrawn':True,'publicPushed':False}))
