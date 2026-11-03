from pathlib import Path
import datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
C=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
D=R/'Document/Deployment/public_test_plan_resources_r40_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(D/'local-stage-files-r405.json').exists()
proof=J(D/'verified-fixed-transport-r403.json');cleanup=J(D/'completed-fixture-cleanup-r404.json');prep=J(D/'preparation-result-r402.json');manifest=J(D/'delivery-manifest.json')
assert proof['passed']and cleanup['passed']and sha(D/'delivery-manifest.json')==proof['manifestSHA256']==prep['manifestSHA256']
assert J(C/'release-verification/completed-r401.json')['passed']and J(C/'verified-stage-r399.json')['actualNormalRoleCases']==29
for n,pin in manifest['files'].items():assert (D/'delivery'/n).stat().st_size==pin['bytes']and sha(D/'delivery'/n)==pin['sha256']
assert (D/'delivery/delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
assert sha(R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery-manifest.json')=='4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de'
assert sha(R/'Document/Deployment/public_source_plan_delivery_r369_20261103/public-git-sync-r369-manifest.json')=='c10870e318047506c1ca0de42467a4fd8be602e5f8a85d5a5f40f3a9bcfe7ed1'
result={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'transportFiles':8,'transportBytes':prep['transportBytes'],
 'manifestSHA256':prep['manifestSHA256'],'updaterSHA256':manifest['newUpdaterSHA256'],'finalReleaseSHA256':manifest['newReleaseSHA256'],
 'exactBaseVariants':['R36','R37'],'fullProgramFilesEachBase':manifest['fullProgramFilesEachBase'],
 'negativeCompositionCasesEach':manifest['negativeCompositionCasesEach'],'fileRecoveryScenariosEach':manifest['fileRecoveryScenariosEach'],
 'actualCandidateBusinessCases':29,'actualCandidateBusinessExceptions':0,'r37ActualUpdaterApplyAndRollbackPassed':True,
 'r36ThisR40ActualLifecycleNotRepeated':True,'wrapperLifecycleIdentityAndIISChecksInOfflineTestsAreSpies':True,
 'offlineWrapperMainPaths':proof['actualWrapperMainPreflightAndPostcheckScenarios'],'closedArchiveAndExactReproductionPassed':True,
 'serverActualIISHTTPSAndLoggedInTimingPending':True,'publicDeployed':False,'publicPushed':False,'fullCloneReady':False}
dump(D/'verified-stage-r405.json',result)
text=f'''## 2026-11-03 R401—R405：R40完整程序/恢复与八文件运输通过，尚未公网部署

R40固定8文件{prep['transportBytes']}B，清单SHA256 {prep['manifestSHA256']}，FTP {manifest['targetFTP']}。187写入+177移除，22控制；每份仅认精确R36或R37，两个分支同最终release {manifest['newReleaseSHA256']}。预案事务类与原Mapper、性能及三资源取消修正统一，固定R39/184公开源码旧清单未改。

两基线各15557程序、63组成拒绝、16实际文件正常/故障恢复/外来漂移拒绝、8字节就绪边界通过；只读共享原依赖、仅自有代码视图与虚构配置，不读原业务库或启动服务。R40本轮实际六组件apply/rollback为R37三控制器，最终普通角色29业务/0JS异常独立验证保持；R36本轮未重复同R40六组件生命周期，R39原生命周期函数/类AST完整保留，限制照录。

运输190闭合成员/187载荷，14归档解包边界、28合成静态响应、5基线选择、12恢复守卫、10包装器main路径与3外来/超限回执拒绝通过；真实候选Mapper/预算先于服务检查。包装器测试的完整安装身份/生命周期/IIS明确spy，不当实际公网证明。最终构建器逐字重建8文件，最长展开路径237；四静态核验绑定本次真实编译入口SHA，避免旧文件名。

清理{cleanup['removedFiles']}临时代码文件项，逻辑{cleanup['logicalBytes']}B含硬链接，观察D空闲变化{cleanup['observedDFreeDelta']}B不独占归因；固定候选/源码/小型证据/数据库/上传/资产及另一三维会话保持。尚未上传或部署，公网精确当前版本仍须服务器限定回执核实，实际IIS/HTTPS/正常登录后耗时及真实南港模板/权限/跨入口待验。

接续先协调WinSCP桌面交接和服务器正常命令通道；当前Computer Use禁止通过GUI直接或间接输入终端命令，不能用RDP/文件管理器代打发布脚本。已有概括发布授权保留，桌面时间仍需协调，服务器脚本若无正常命令通道需用户手动执行。不恢复360隔离文件、不改变安全设置。不包含新的公开Git或腾讯回填。

完整UE效果效率引擎、EXE GIS点线面图层/多源旗杆标牌、Web3D和单系统南港B/S目标active/fullCloneReady=false，三维正式8767和业务18891保持，不报未去重证实的百分比。
'''
(D/'固定候选说明.md').write_text(text,encoding='utf-8')
tools=['prepare_r40_release_checks_r401.py','run_r40_release_checks_r401.py','verify_r40_full_r36_r401.py','verify_r40_full_r37_r401.py',
 'verify_r40_transactions_r36_r401.py','verify_r40_transactions_r37_r401.py','build_plan_resources_delivery_r402.py',
 'prepare_r40_transport_verifier_r403.py','verify_plan_resources_delivery_r403.py','cleanup_r40_release_fixtures_r404.ps1','record_r40_fixed_delivery_r405.py']
files=[]
for n in tools:shutil.copyfile(V/n,T/n);files.append('tools/'+n)
source=A/'deploy/source/plan_resources_r40_20261103';source.mkdir(parents=True,exist_ok=False)
for p in (D/'delivery').iterdir():
 if p.suffix=='.zip':continue
 # Runtime updater already has its exact source in tools; retain the transport copy as an explicit deployment source.
 shutil.copyfile(p,source/p.name);files.append((source/p.name).relative_to(A).as_posix())
verification=A/'deploy/verification/plan_resources_r40_20261103';verification.mkdir(parents=True,exist_ok=False)
sources=[(D/n,n)for n in ['preparation-result-r402.json','verified-fixed-transport-r403.json','archive-cases-r403.json',
 'selection-and-recovery-cases-r403.json','wrapper-order-cases-r403.json','response-cases-r403.json','completed-fixture-cleanup-r404.json','verified-stage-r405.json']]
for label in ['r36','r37']:
 for n in ['full-program-preflight.json','composition-and-recovery.json','composition-negative-cases.json','plan-readiness-boundaries-r340.json']:
  sources.append((C/'release-verification'/label/n,label+'-'+n))
for p,n in sources:shutil.copyfile(p,verification/n);files.append((verification/n).relative_to(A).as_posix())
hand=A/'deploy/handbook/plan_resources_r40_20261103.md';hand.write_text(text,encoding='utf-8');files.append(hand.relative_to(A).as_posix())
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
 p=R/rel;old=p.read_text(encoding='utf-8');assert 'R401—R405'not in old;p.write_text(text+'\n'+old,encoding='utf-8')
with(R/'Document/Engine/showcase_demo_completion.md').open('a',encoding='utf-8')as f:f.write('\n'+text)
(R/'Document/Engine/project/R40固定发布运输验收_R405_20261103.md').write_text(text,encoding='utf-8')
dump(D/'local-stage-files-r405.json',{'application':files,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md',
 'docs/showcase_demo_completion.md','docs/project/R40固定发布运输验收_R405_20261103.md'],'publicPushed':False,'publicDeployed':False})
print(json.dumps({'recorded':True,'applicationFiles':len(files),'engineFiles':4,'transportBytes':prep['transportBytes'],'manifestSHA256':prep['manifestSHA256'],'publicDeployed':False}))
