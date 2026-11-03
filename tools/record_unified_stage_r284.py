from pathlib import Path
import ast, datetime, hashlib, json

R=Path('D:/Project/Zhumadian'); A=R/'Application'; T=A/'tools'
V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103'
VERIFY=A/'deploy/verification/unified_original_mappers_r38_20261103'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(value,encoding='utf-8')
def jout(p,value):write(p,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

manifest=D/'delivery/delivery-manifest.json'
assert sha(manifest)=='72b7d48b25ce0e14504c20d99fddc6adde0c930f00bc0036bcce3a3c17a002d3'
md=load(manifest)
for rel,pin in md['files'].items():
    f=D/'delivery'/rel
    assert len(f.read_bytes())==pin['bytes'] and sha(f)==pin['sha256']
assert sum(p['bytes']for p in md['files'].values())+manifest.stat().st_size==2111659
assert load(D/'mapper-input-gate-cases.json')['wrapperSHA256']==md['files']['deploy_unified_mappers_r38.py']['sha256']
assert load(D/'completed-fixture-cleanup-r283.json')['passed']
held=A/'native/main.cpp'; held_sha=sha(held)
other=R/'Document/Engine/project/驻马店三维_当前工作断点.md'; other_sha=sha(other)
sources=[
 'prepare_unified_mapper_bundle_r274.py','prepare_unified_full_preflight_r275.py',
 'verify_unified_full_program_r275.py','verify_unified_composition_recovery_r276.py',
 'prepare_unified_static_transport_r277.py','verify_unified_static_transport_r277.py',
 'verify_unified_nginx_transport_r278.py','build_unified_delivery_r279.py',
 'verify_unified_delivery_r280.py','add_mapper_input_gate_r281.py',
 'verify_mapper_input_gate_r282.py','cleanup_unified_fixtures_r283.ps1',
 'record_unified_stage_r284.py',
]
app_files=[];source_pins=[]
for name in sources:
    src=V/name; dst=T/name
    raw=src.read_bytes();raw.decode('utf-8')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    if dst.exists():assert dst.read_bytes()==raw,'EXISTING_SOURCE_DRIFT:'+name
    else:dst.write_bytes(raw)
    app_files.append(dst.relative_to(A).as_posix())
    source_pins.append({'path':dst.relative_to(A).as_posix(),'sha256':sha(dst),'bytes':len(raw),'executedSourcePreserved':True})
for src,rel in [(T/'original_public_test_update_r38_unified_20261103.py','tools/original_public_test_update_r38_unified_20261103.py'),
                (D/'delivery/deploy_unified_mappers_r38.py','tools/deploy_unified_mappers_r38_20261103.py')]:
    dst=A/rel
    if dst!=src:
        if dst.exists():assert dst.read_bytes()==src.read_bytes()
        else:dst.write_bytes(src.read_bytes())
    ast.parse(dst.read_bytes(),filename=rel)
    app_files.append(rel);source_pins.append({'path':rel,'sha256':sha(dst),'bytes':dst.stat().st_size,'exactFinalDeliveryBytes':True})

nginx=load(V/'static-nginx-r278/verified-result.json')
assert nginx['passed'] and nginx['normalNginxExitAndDescendantsZero']
jout(D/'actual-nginx-new-frontend-r278.json',nginx)
failure={'case':'new-R38-dotnet-transport-harness','passed':False,'stage':'compiled-baseline-executable-start',
 'exception':'PermissionError [WinError 5] Access is denied','newAspNetTransportCasesExecuted':False,
 'oldProxySourceUnchanged':True,'oldProxyEvidenceNotPromotedToNewR38Run':True,
 'quarantineRestorationOrSecurityBypass':False,
 'normalOwnedNginxExit':0,'ownedActiveProcessesAfterQuit':0,
 'causeMalwareOrAntivirusNotEstablishedByThisException':True}
exit_proof=load(V/'static-transport-r277/baseline/exit.json')
assert exit_proof['processExit']==0 and exit_proof['ownedActiveProcesses']==0
jout(D/'new-dotnet-harness-not-executed-r277.json',failure)
summary={
 'schema':'xnby.r284.unified-candidate-evidence.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'candidate':'R38','publicUploaded':False,'publicDeployed':False,'newPublicGitPushed':False,
 'r37PreviouslyUploadedAndCheckOnlyPassed':True,'r37HumanApplyResultNotReceived':True,
 'r38AcceptsOnlyExactR36Base':True,'r38MayNotBeUsedAfterR37WithoutRebase':True,
 'transportFiles':8,'transportBytes':2111659,'manifestSHA256':sha(manifest),
 'writes':186,'removals':177,'totalInstallPaths':363,
 'actualOriginalSpringXMLRegistered':226,'nativePlanExerciseStages':11,'nativeTaskParallelStages':9,
 'nativeBusinessRunsFromR272NotNewR38ApplyTransaction':True,
 'fullProgramPreflightFiles':15557,'negativeCompositionCases':45,
 'actualFileRecoveryScenarios':14,'mapperInputGateChecks':13,
 'actualNginxRequestsEachMode':12,'newAspNetRepeatPassed':False,
 'newUpdaterApplyUpdateOrRollbackLifecycleRun':False,
 'lifecycleFunctionASTUnchangedFromR37':True,
 'actualServerIISHTTPSAndAuthenticatedTimingPending':True,
 'sourceJarSQLAuthPrivateConfigurationDataUploadsAndSafetyFrontendPreserved':True,
 'schemaOrOriginalBusinessRowsModified':False,'fullCloneReady':False,
 'completedOwnFixturesRemoved':True,'sourcePins':source_pins}
jout(D/'verified-stage-r284.json',summary)
proofs=['delivery-manifest.json','full-program-preflight.json','composition-negative-cases.json',
 'composition-and-recovery.json','independent-fixed-delivery-verification.json',
 'mapper-input-gate-cases.json','response-checker-cases.json','actual-nginx-new-frontend-r278.json',
 'new-dotnet-harness-not-executed-r277.json','completed-fixture-cleanup-r283.json','verified-stage-r284.json']
for name in proofs:
    src=D/name; dst=VERIFY/name
    write(dst,src.read_text(encoding='utf-8-sig'))
    app_files.append(dst.relative_to(A).as_posix())

explanation='''# R38 统一候选固定范围与验证说明

本文件记录后台已完成的候选准备，不代表公网已经更新。R37 已上传且此前服务器预检通过，但手动执行结果尚未收到；最后一份完整交付回执仍是 R36。现有 R37 批准继续有效，不自动替换成 R38，也不要求用户重复执行已运行的命令。

## 候选内容与基线

R38 组合原项目 XML 扫描默认值、已验证的预案/演练及任务前端修正、R37 压缩/缓存控制。只接受精确 R36 基线；如果 R37 已执行，必须先核服务器实际状态并重新制作、验证基于 R37 的候选，不能直接使用本包。

原业务 Jar 和其中 SQL、已有鉴权/独立意见历史、数据库、真实配置、上传、安全端前端、IIS 映射保持。业务参数只在没有显式 Mapper 路径时补原 Jar 的 `/xml/**/*.xml` 扫描；部署包装器在停服前拒绝未知或空的显式路径，既有配置仅在内存计算，不输出值或凭据。没有业务表结构变更，没有自动插入公网测试业务。

最终运输为 8 文件、2,111,659 字节，清单 SHA256：
`72b7d48b25ce0e14504c20d99fddc6adde0c930f00bc0036bcce3a3c17a002d3`。
目录 `delivery` 内 7 载荷加清单；186 写入、177 旧应急前端移除，共 363 安装路径。最终包装器 SHA 为 `ef35576ada07170dc252a5f93f2861a2b3441cdfc4c69f0659575446cbe1bb7a`。
早期 `delivery-manifest-r279-draft.json` 仅保留审计，不执行；最终 R281 包装器补了停服前配置门槛，R282 十三项验证通过。

拟定 FTP 目的地 `/Zhumadian/Zhumadian_Unified_Original_Mappers_20261103_R38/`，当前尚未上传或部署，也没有创建新的公开 Git 对象。本包不属于旧固定 R37 清单；只有确定服务器基线和本轮具体发布范围后再安排上传。

## 已有证据与边界

| 检查 | 当前证据 | 证明范围 |
| --- | --- | --- |
| 原 SQL 注册与实际业务 | R272 两轮原六组件：226 原 XML 语句全注册、预案演练 11 阶段及任务/双分支/附件 9 阶段通过 | 实际产品参数、R268 运行声明以及原生业务行为；不代表全部 SQL 执行或全南港模板验收 |
| 完整程序预检 | 15,557 原 R36 程序、22 候选控制、363 变更路径通过 | 真实 load_bundle、保留字节、候选预算、IIS 源钉住及漂移拒绝；仅本地目标/虚构私有清单适配 |
| 文件安装与恢复 | 45 组合拒绝，实际 backup/replace/restore 的 11 正常/故障及 3 外部漂移场景通过 | 精确文件事务，不包括新更新器 apply_update/rollback 的六组件生命周期 |
| 包装器前置检查 | 28 响应校验样例、5 恢复守卫、真实归档提取/候选预算及 13 Mapper 输入门槛通过 | 服务调用由显式 spy 禁止或替代；不能宣称服务器身份/就绪实测 |
| 实际静态传输 | 新前端 836+341 文件，真实 Nginx 两模式各 12 请求；解压内容一致 | JS 减少约 69%、CSS 约 85%；HTML/API/错误不长期缓存；不是公网登录后耗时 |
| 新 .NET 测试重复 | 编译后的测试程序启动被 Windows 以 WinError 5 拒绝 | 本轮 ASP.NET 重跑未通过；不恢复隔离、不修改杀软、不以该异常判定木马或误报。既有字节相同代理的历史验证保留 |

最终更新器正常停启、备份替换及恢复函数的 AST 保持 R37；新增装配/传输合同完整验证，但尚未独立调用该最终文件的 apply_update/rollback 六组件生命周期，不能合并表述为已完成。线上 IIS、外网 HTTPS、登录后体验和数据一致性仍待验收。原 398 模型定义未变；226 是原 SQL 语句数量，不是完成功能数量。

## 后续发布与恢复

先取得 R37 执行结果并核实际版本。若仍是 R36，才可按另行确定的 R38 固定范围上传并逐 SHA 核对，check-only 必须先通过。正常停启六组件后检查原 11 项就绪，再由包装器检查 gateway 和本机 IIS TLS 的 14 项编码、缓存及解压 SHA。包装器检查失败应停止并使用本轮精确记录决定恢复，不宣称静态探测失败必然自动回滚。

恢复仅使用本次 updateId、前后 SHA 与自有 before 记录，退出归属不明则停止，不强杀。成功后还要核外网 HTTPS、正常登录后的首页、预案/演练/任务入口与必要只读详情；不自动写公网测试业务。只有通过验收，才按绝对范围、精确旧清单、已停无引用、无重解析清理退役运输包和旧代码副本，数据/上传/配置全部保留。

用户要求原生蓝边/鼠标接管提示。当前 Computer Use 技能禁止通过 GUI 直接或间接执行终端命令，不能在远程桌面代输或以资源管理器双击脚本绕过。上传/回读可用原生桌面接口；固定执行命令需用户手动提交或另有正常命令通道。桌面前提示、焦点变化停输入、结束交还。

## 本轮存储与状态

四个已完成的自有预检/文件事务副本经绝对路径、无进程引用和无重解析核验后清理，移除 21,948 文件项，逻辑 1,651,386,732 字节；观察 D 盘空闲增加 271,519,744 字节。大量原程序是只读硬链接，逻辑量不等于实际释放，磁盘变化也不作独占归因。固定 bundle/delivery、源码与小型证据保留；数据库、资产、用户浏览器、正式 18891、8767 及另一三维会话不变。

完整目标仍包括 UE 对标引擎、独立 EXE GIS/DLG 点线面/图层/旗杆多源标牌、网页三维和全南港 B/S。按一套系统唯一业务去重，不把八入口、226 SQL 或 1,177 静态文件当作进度分母；fullCloneReady=false，新的完成百分比仍待验收分母闭合。
'''
write(D/'固定候选说明.md',explanation)
handbook='''# 原 SQL 映射、预案演练与加载优化的体验状态

R38 是本地已验证候选，尚未上传或上线。R37 的手动执行结果仍待收到，最后已完整验收的线上版本是 R36。不要把下面候选功能当作已在公网交付，也不要重复执行已经运行的 R37。

候选将支持：预案必填与联系电话校验、新增/编辑/只读详情；演练参与人员空选保存与父级列表回读；真实附件上传、上传尚未发出时阻止提交并保留输入、失败保留和一次重试；任务保存中重复点击只发一次请求、处置反馈、双独立审批分支、末级已办与附件下载。以上已在自有原六组件和普通角色测试中通过，仍需具体上线版本核验及真实南港全模板验收。

用户复测建议从“敏捷应急管理”的预案/演练和“应急处置”的任务/个人流程进入，同一权限从综合入口和快捷入口访问同一记录，应得到一致状态与附件；切换流程节点后旧节点不能继续审批。公网复测使用有权查看的记录，新增或审批测试记录需明确安排，自动验证不写正式业务。

加载优化采用哈希静态资源缓存及 gzip；HTML、API 和错误响应继续及时获取。实际本地 Nginx 测得主 JS 传输减少约 69%，不是已承诺公网首页加速到某秒。上线后分别体验首次进入、第二次进入、同一页刷新和跨模块，记录入口、网络、冷/暖缓存、成功或错误状态与等待时间，不能用“列表空”代替区分认证、接口错误和真实空数据。

尚存验收项：新统一更新器整套 apply_update/rollback 生命周期、真实服务器 IIS/HTTPS、登录后耗时、全原模板/权限及综合与快捷入口一致性。新 .NET 测试启动被 Windows 拒绝，本轮未重复通过 ASP.NET 测试；没有恢复隔离或改变安全设置。原 SQL 注册 226/226 是自有测试容器实测，不是公网缺失 223 条的直接测量，也不表示删除了原数据。

固定说明及证据：D:\\Project\\Zhumadian\\Document\\Deployment\\public_test_unified_mappers_r38_20261103。R38 当前仅接受精确 R36；R37 如果已经执行，先重制基线适配候选再发布。公开 Git 本轮未推送，先前 30 文件待答范围不自动扩大。
'''
hp=A/'deploy/handbook/unified_original_mappers_r38_20261103.md';write(hp,handbook);app_files.append(hp.relative_to(A).as_posix())
dp=A/'deploy/handbook/unified_original_mappers_r38_fixed_scope_20261103.md';write(dp,explanation);app_files.append(dp.relative_to(A).as_posix())
stage='''## 2026-11-03 R274—R284：R38统一候选固定、文件预检恢复与实际Nginx通过，尚未上线

R38组合原XML默认扫描、R224预案/演练任务前端及R37静态性能：8文件2111659B、最终manifest72b7d48b25ce0e14504c20d99fddc6adde0c930f00bc0036bcce3a3c17a002d3，186写入+177移除。仅精确R36；R37已上传/预检，最新用户置前后仍需手动提交命令，执行结果未收到，不能猜已部署或直接换R38。若R37实际已运行先重制候选。

15557程序真实load_bundle、45组合拒绝、363路径实际backup/replace/restore的11正常故障+3漂移场景通过；最终包装器13映射配置门槛（停服前）、28响应/5恢复守卫通过，身份/就绪在包装器顺序测试为显式spy。新前端836+341真实Nginx两模式各12请求、解压一致，JS约69%/CSS约85%减量。新.NET重复启动WinError5未执行，保留失败，不判定木马/误报或绕过杀软；旧代理历史证据不冒称新重跑。R272真实原六组件226注册/11预案演练+9任务阶段证据保持，但最终R38 apply_update/rollback六组件生命周期仍未独立跑，AST保持不等同执行通过；实际IIS/外网/登录后耗时待验。源码/交付哈希和故障边界均有证据，仍fullCloneReady=false。

清理4个已完成自有副本21948文件项/逻辑1651386732B、D观察+271519744B不独占归因；固定bundle/delivery/源/证据保留，无进程强杀，不动DB、资产、正式18891/8767、用户浏览器和另一三维断点。本轮桌面未操作、未上传公网或新公开Git；旧30公开范围仍待答。先核R37执行状态，统一包不擅自替换已批准包。详Deployment/public_test_unified_mappers_r38_20261103。完整引擎/EXE/Web3D/全南港目标保持active，不以八入口、SQL数或静态文件数计完成率。

'''
engine_files=[]
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8')
    if not old.startswith('## 2026-11-03 R274—R284：'):write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine_files.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8')
marker='## 2026-11-03 R284统一候选与临时副本收尾'
if marker not in old:write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1])
engine_files.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/原SQL映射与统一候选_R38_20261103.md';write(ep,stage+explanation);engine_files.append('docs/project/原SQL映射与统一候选_R38_20261103.md')
assert sha(held)==held_sha and sha(other)==other_sha
jout(D/'local-stage-files-r284.json',{'application':app_files,'engine':engine_files,
 'heldNativeSHA256':held_sha,'other3DBreakpointSHA256':other_sha,
 'publicScopeNotAuthorizedByThisRecord':True,'sourceSyntaxUTF8AndFinalTransportPinsPassed':True})
print(json.dumps({'passed':True,'applicationFiles':len(app_files),'engineFiles':len(engine_files),'finalTransportManifestUnchanged':sha(manifest),'heldNativeAndOther3DBreakpointUnchanged':True,'publicPushed':False}))
