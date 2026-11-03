from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/unified_update_owned_lifecycle_r292_20261103';O=R/'work/unified-update-lifecycle-r293'
D2=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
proof=J(D/'verified-lifecycle-r294.json');terminal=J(O/'terminal.json');cleanup=J(D/'completed-code-fixture-cleanup-r295.json')
assert proof['passed']and cleanup['passed']and terminal['originalGCodeAndPointersRestored']and terminal['failure']is None
assert sha(A/'tools/original_public_test_update_r38_mapper_preflight_r286.py')==proof['candidateUpdaterSourceSHA256']
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert sha(D2/'delivery-manifest.json')=='3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956'
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_pin=sha(held);other_pin=sha(other)
app=[];engine=[];source_pins=[]
for name in ['inspect_owned_unified_lifecycle_r292.py','prepare_owned_unified_lifecycle_r293.py','run_owned_unified_lifecycle_r294.py','cleanup_owned_unified_lifecycle_r295.ps1','record_owned_unified_lifecycle_r296.py']:
    src=V/name;dst=T/name;raw=src.read_bytes();raw.decode('utf-8')
    if src.suffix=='.py':ast.parse(raw,filename=name)
    if dst.exists()and dst.read_bytes()!=raw:
        assert name=='record_owned_unified_lifecycle_r296.py'and sha(dst)=='7b50efaf976cef9aa53d9b5ab57c8da1bc89817a12a59694f4656079d87eb4db'
        dst.write_bytes(raw)
    elif dst.exists():assert dst.read_bytes()==raw
    else:dst.write_bytes(raw)
    app.append(dst.relative_to(A).as_posix());source_pins.append({'path':app[-1],'sha256':sha(dst),'bytes':len(raw)})
scoped_terminal={'passed':True,'originalGCodeAndPointersRestored':True,'allOwnedControllerHandlesTerminal':True,
 'controllers':[{'controllerExitCode':v['controllerExitCode'],'actualJobDescendantsZero':v['actualJobDescendantsZero'],'receipt':v['receipt']}for v in terminal['controllers']],
 'noRuntimeUUIDsPIDsOrBusinessRowsIncluded':True,'actualIISTLSNotTested':True,'forceTerminationUsed':False}
for v in scoped_terminal['controllers']:
    assert v['controllerExitCode']==0 and v['actualJobDescendantsZero']and all(x==0 for x in v['receipt']['exitCodesBeforeJobClose'].values())
jout(D/'scoped-terminal-summary-r294.json',scoped_terminal)
static=J(O/'candidate-static-HTTP.json');assert static['passed']and len(static['checks'])==4
jout(D/'candidate-static-HTTP-summary-r294.json',static)
clean_public={k:v for k,v in cleanup.items()if k!='targets'}
clean_public['targets']=[{'files':x['files'],'logicalBytes':x['logicalBytes'],'absoluteScopeNoReferencesAndNoReparseVerified':x['absoluteScopeNoReferencesAndNoReparseVerified']}for x in cleanup['targets']]
jout(D/'scoped-cleanup-summary-r295.json',clean_public)
summary={'schema':'xnby.r296.actual-owned-update-lifecycle.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'candidate':'R38-r2','fixedTransportManifestUnchanged':sha(D2/'delivery-manifest.json'),
 'sourcePins':source_pins,'actualApplyUpdateAndRollbackLatestExecuted':True,
 'actualSixComponentControllers':3,'allNormalZeroAndActualDescendantsZero':True,
 'original398ModelsUnchangedAcrossUpdateAndRollback':True,'fourActualCandidateGatewayGzipDecodedSHAMatches':True,
 'loadBundleTargetAndGatewayAndSyntheticPrivateManifestAdapted':True,
 'explicitIngressHTTPAdapterUsedAndNotAcceptedAsTLSProof':True,
 'identityHealthNormalStopLaunchBackupReplaceRestoreAndRollbackBodiesNotStubbed':True,
 'originalGCodePrivateConfigAndPointersRestored':True,'databaseCopiedReplacedOrRestoredFromBackup':False,
 'publicDeploymentHTTPSIISTLSAndNormalLoggedInBusinessUIStillPending':True,
 'publicOrFormal18891OrScene8767OrDesktopTouched':False,'newPublicGitPushed':False,'fullCloneReady':False}
jout(D/'verified-stage-r296.json',summary)
for name in ['verified-lifecycle-r294.json','scoped-terminal-summary-r294.json','candidate-static-HTTP-summary-r294.json','scoped-cleanup-summary-r295.json','owned-attempt-receipt-summary-r295.json','verified-stage-r296.json']:
    dst=A/'deploy/verification/unified_update_owned_lifecycle_r296_20261103'/name
    write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
guide=f'''# R38 第二稿自有环境真实更新与回滚验收

本阶段补齐的是实际更新器事务，不是模拟停启。源文件 SHA `{proof['candidateUpdaterSourceSHA256']}` 与固定第二稿完全一致。八文件交付清单保持 `3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956`，没有为了记录测试成绩重打固定包。

## 实际执行范围

在明确自有、无活动进程且没有 user-manual-protected 标记的 `_g/Application` 合成环境，保存893代码/指针原像，临时构成R36程序基线。保留同一合成数据库及原虚构配置，只适配清单的私有配置摘要、目标目录和动态回环端口。

真实启动基线六组件，调用最终源码的 apply_update，正常停服、备份、替换363路径、启动候选并核身份与健康；再调用 rollback_latest，正常停服、恢复代码并启动旧版；最后正常停机。三次控制器及每次 store/mysql/redis/platform/business/gateway 均退出0，实际 Windows Job 后代数均为0。身份、健康、正常停服、启动、备份、替换、恢复和回滚函数体未用 spy 替代。

更新前、更新后、回滚后使用同一限定DDL读取器核398张原表的定义，三份一致；不读取或导出业务原始行。原测试数据库没有复制、替换或从备份覆盖。测试环境原代码、虚构配置与指针逐哈希恢复，最终 `_g` 原 release SHA 为 e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4。

候选真实六组件上的四个主JS/CSS资源gzip响应与固定预期解压SHA全部匹配。此前Nginx独立传输证据与本次真实控制器网关证据互相补足。

## 仍未证明的范围

ingress_preflight 使用显式的自有回环HTTP适配器，以便不接触本机/公网IIS、证书和站点。即使更新器原回执里写了 serverLocalTLSVerified，该字段也不能用于本阶段TLS验收。实际IIS/TLS、外网HTTPS、真实登录后业务UI与耗时仍未通过本轮核验；不要把自有环境更新通过写成公网已部署。

既有R272的预案演练11阶段和任务/并行/附件9阶段，以及原SQL226注册证据保持；本阶段未重新执行这些登录后业务流程，也不宣称全部天津南港模板和权限验收完成。398是表结构比较范围，不是数据行未变化或功能完成数。

R289固定运输清单里的未执行字段是制作时的历史快照，本文件和 verified-lifecycle-r294.json 才是后续生命周期证据；运输字节和哈希不改。R37仍只知已上传/预检，手动执行结果未收到，原包和批准有效。R38第二稿只接受精确R36；若R37已执行，先核当前版本并重制基线适配包，不自动替换已批准包。

## 故障和清理记录

清理工具初次把 frontend/.../assets 错判成项目 Assets，在删除前拒绝。核实命中均为计划内前端代码后，改成精确363路径计划闭合及受保护根目录检查，未删除数据库/项目Assets。该拒绝保留在回执，不记作产品验证失败或安全软件问题。

已按绝对范围、实际进程退出、无引用/无重解析及代码备份哈希清除4个自有完成副本，共{int(cleanup['removedFileEntries'])}文件项、逻辑{int(cleanup['logicalBytes'])}B；观察D空闲增加{int(cleanup['observedDFreeDelta'])}B，不把硬链接逻辑量当作物理回收或独占归因。固定公共候选、源码、结构/运行小型证据与合成数据库、上传、配置保留。公网、正式18891、三维8767、用户桌面及另一三维会话不变。

完整UE对标引擎、EXE GIS/DLG点线面与分组图层/旗杆多源标牌、网页三维及全南港B/S目标仍active/fullCloneReady=false。按一套信息系统唯一业务去重，没有新增完成百分比。
'''
write(D/'实际生命周期验收说明.md',guide)
hp=A/'deploy/handbook/unified_update_owned_lifecycle_r296_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
fixed=D2/'固定候选说明.md';text=fixed.read_text(encoding='utf-8')
old='最终源码尚未独立执行完整 apply_update/rollback 六组件生命周期；公网 IIS/HTTPS、登录后体验和真实全流程仍待。'
new='后续R294已在自有合成环境真实执行最终源码的apply_update与rollback_latest，三次六组件正常0/后代零、398表结构与四项gzip解压SHA通过并精确恢复；入口使用明确HTTP适配器，不是IIS/TLS证据。公网IIS/HTTPS、登录后体验和真实全流程仍待。'
assert text.count(old)==1;text=text.replace(old,new)
old='owned_ready/ingress 在拒绝路径中明确为测试 spy，服务函数禁止调用，不能宣称已跑实际六组件发布生命周期。'
new='身份/ingress在该20项拒绝路径中明确为测试spy，服务函数禁止调用；这20项本身不证明六组件生命周期。后续R294真实六组件更新/回滚证据另列。'
assert text.count(old)==1;text=text.replace(old,new)
text='> 后续验收更新：R294自有环境真实更新/回滚通过；固定运输字节不变，实际IIS/TLS和公网仍待。详 unified_update_owned_lifecycle_r292_20261103/实际生命周期验收说明.md。\n\n'+text
write(fixed,text)
hp=A/'deploy/handbook/unified_original_mappers_r38_r2_fixed_scope_20261103.md';write(hp,text);app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R292—R296：最终第二稿真实六组件更新/回滚通过，原自有环境精确恢复

精确源f4eae55e在自有G环境，基线启动→实际apply_update→实际rollback_latest→正常停机三控制器/每轮六组件均0、真实Job后代零；398表定义前/更新/回滚一致，候选四主JS/CSS实际网关gzip及解压SHA匹配。目标/Gateway及虚构私有清单指针作明确本地适配，身份/健康/停启/备份替换恢复/回滚函数体未stub；ingress是显式回环HTTP适配器，不把原回执TLS标签当IIS证据。实际IIS/外网HTTPS、登录后业务/耗时仍待，本轮不重跑R272的11+9流程，不以398/226当业务完成率。

G原代码/虚构配置/指针893项恢复，release回e9dcd876，数据库未复制/覆盖。session41517终态0，不能重复轮询或重启；当前无本轮活动进程。清395文件/逻辑19782399B、D观察+12709888B不独占归因，原固定包/源/小型证据/数据库上传保持。清理初次误判frontend/assets在删除前拒绝，核精确计划及根保护后通过，记录保留。

固定第二稿8文件2114220B/manifest3882688ce2836d640530aef872b77b4306d665241e329522ae5c6dd7ebad0956不变；制作时未执行字段为历史快照，后续实跑证据见Deployment/unified_update_owned_lifecycle_r292_20261103。R37手动执行结果仍缺、旧批准有效；R38第二稿仍只接受R36，若R37已执行先重制。未接管桌面/公网/正式18891/8767或新公开Git，不动另一三维断点。完整长期目标active/fullCloneReady=false。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;oldtext=p.read_text(encoding='utf-8')
    if not oldtext.startswith('## 2026-11-03 R292—R296：'):write(p,stage+oldtext)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';oldtext=log.read_text(encoding='utf-8');marker='## 2026-11-03 R296最终更新器自有六组件事务验收'
if marker not in oldtext:write(log,oldtext+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1])
engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/统一更新器真实生命周期_R296_20261103.md';write(ep,stage+guide);engine.append('docs/project/统一更新器真实生命周期_R296_20261103.md')
assert sha(held)==held_pin and sha(other)==other_pin
jout(D/'local-stage-files-r296.json',{'application':app,'engine':engine,'heldNativeSHA256':held_pin,'other3DBreakpointSHA256':other_pin,'publicScopeNotAuthorizedByThisRecord':True})
print(json.dumps({'passed':True,'applicationFiles':len(app),'engineFiles':len(engine),'fixedManifestUnchanged':sha(D2/'delivery-manifest.json'),'publicPushed':False}))
