"""Record exact R45 readiness, retire verified own fixtures, sync existing local refs only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_original_bootstrap_r45_20261104'
C=R/'Document/Deployment/original_backend_bootstrap_r45_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def scan_shared(root):
 assert root.is_absolute()and root.resolve()==root and root.is_relative_to(R/'work')and root!=R/'work'
 for p in [root,*root.parents]:
  if not p.is_relative_to(R/'work'):break
  assert not p.lstat().st_file_attributes&0x400
 files=[];stack=[root]
 while stack:
  folder=stack.pop()
  with os.scandir(folder)as entries:
   for entry in entries:
    p=Path(entry.path);st=p.lstat();assert p.resolve()==p and not st.st_file_attributes&0x400
    if entry.is_dir(follow_symlinks=False):stack.append(p)
    else:assert not st.st_file_attributes&1;files.append((st.st_size,st.st_nlink))
 return files
def main():
 assert not(D/'verified-stage-r855.json').exists()
 guard=load('r45_fixed_guard_r855',V/'record_research_task_ui_r812.py');guard.fixed()
 assert sha(D/'delivery-manifest.json')=='1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876'
 manifest=J(D/'delivery-manifest.json');assert len(list((D/'delivery').iterdir()))==8
 for n,pin in manifest['files'].items():assert (D/'delivery'/n).stat().st_size==pin['bytes']and sha(D/'delivery'/n)==pin['sha256']
 assert (D/'delivery/delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
 held=sha(A/'native/main.cpp')
 run=R/'work/original-backend-full-r850';life=J(run/'verified-component-bootstrap-r850.json')
 assert life['passed']and life['codeRestored']and life['privateConfigurationUnchanged']and life['originalCurrentPointerRestored']
 assert len(life['terminals'])==1 and len(life['health'])==1 and life['health'][0]['newBackendOrSupervisionModulePresent']is False
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and t['normalOwnedShutdown']and all(v==0 for v in t['exitCodes'].values())for t in life['terminals'])
 ui=J(R/'work/bootstrap-browser-r850/result.json')
 assert ui['passed']and len(ui['cases'])==13 and not ui['APIsMocked']and ui['approvalRequests']==0
 assert J(R/'work/bootstrap-browser-r850/browser-terminal.json')['normalBrowserClosed']
 job=J(R/'work/original-manager-full-lifecycle-r609/component-bootstrap-r850/normal-restart/browser-job-terminal.json')
 assert job['exitCode']==0 and job['actualJobDescendantsZero']
 gateway=J(run/'normal-restart-static-result.json');assert gateway['passed']and len(gateway['rows'])==10
 files=J(C/'verified-full-bundle-files-r852.json');transport=J(D/'verified-transport-r854.json')
 assert files['passed']and len(files['negativeCases'])==22 and len(files['variants'])==2
 assert transport['passed']and len(transport['checks'])==17
 query="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); Get-CimInstance Win32_Process | Select-Object CommandLine | ConvertTo-Json -Compress"
 result=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert result.returncode==0
 live=json.loads(result.stdout.decode('utf-8-sig')or'[]');live=live if isinstance(live,list)else[live]
 targets=[run/'code-transaction/before',R/'work/bootstrap-browser-r850/chrome-profile',R/'work/r45-code-file-fixtures-r852',R/'work/v45-r854']
 # Check actual process command references before any scoped recursive deletion.
 for target in [G,*targets]:
  marker=str(target).replace('\\','/').lower()
  assert not any(marker in(r.get('CommandLine')or'').replace('\\','/').lower()for r in live),'ACTIVE_OWN_SCOPE_REFUSED'
 code=load('r45_code_restore_r855',A/'tools/owned_candidate_code_transaction_r543.py')
 plan=J(R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json')
 rows=dict(plan['mutations'])
 for key in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
  for name,pin in plan[key].items():assert name not in rows;rows[name]={'before':pin,'after':None}
 assert all(code.pin(G/n)==row['before']for n,row in rows.items())
 assert code.pin(G/'private/server-configuration.json')==plan['configBefore']and code.pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
 assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
 assert J(run/'code-transaction/journal.json')['phase']=='restored'
 expected={n:row['before']for n,row in rows.items()if row['before']is not None}
 before=guard.scan(targets[0],R/'work');assert set(before)==set(expected)and all(code.pin(targets[0]/n)==pin for n,pin in expected.items())
 removed=[];freeBefore=shutil.disk_usage(R).free
 for target in targets[:2]:
  observed=guard.scan(target,R/'work');shutil.rmtree(target)
  removed.append({'path':str(target),'files':len(observed),'logicalBytes':sum(observed.values()),'sharedProgramLogicalBytes':0})
 assert set(p.name for p in targets[2].iterdir())=={'r36','r37'}
 for label in ['r36','r37']:
  private=targets[2]/label/'Application/private/server-configuration.json'
  assert code.pin(private)==plan['configBefore']
 assert set(p.name for p in targets[3].iterdir())=={'extract-r36','extract-r37'}
 for target in targets[2:]:
  observed=scan_shared(target);shutil.rmtree(target)
  removed.append({'path':str(target),'files':len(observed),'logicalBytes':sum(size for size,_ in observed),
   'sharedProgramLogicalBytes':sum(size for size,links in observed if links>1)})
 cleanup={'passed':True,'removed':removed,'observedVolumeFreeDeltaBytes':shutil.disk_usage(R).free-freeBefore,
  'logicalHardlinkBytesNotClaimedAsPhysicalReclaimed':True,'volumeDeltaNotExclusive':True,
  'codeAndPointerRestoredAndActualProcessesExitedBeforeRemoval':True,'dataModelsCallbacksUploadsGISAndSourcePreserved':True,
  'fixedDeliveryAndFinalFullFrontendAndVariantSourcesRetained':True}
 (D/'verified-cleanup-r855.json').write_bytes(enc(cleanup))
 summary={'passed':True,'transportFiles':8,'transportBytes':2333477,'fixedManifestSHA256':sha(D/'delivery-manifest.json'),
  'writes':196,'retiredFrontendPaths':181,'sameFinalApplicationForExactR36R37':True,
  'originalR44BackendNoSupervisionModuleActuallyValidated':True,'actualOriginalBackendSixComponentLifecycles':1,
  'actualNormalUserUICases':13,'businessWritesOrApprovalsPerformed':False,'privateConfigurationUnchanged':True,
  'actualGatewayStaticGETs':10,'gzipIdentityHashesAndImmutableAssetsHTMLNoStorePassed':True,
  'codeOnlyFullBaselineRecoveryCases':2,'codeOnlyFourthWriteFaultRecoveryCases':2,'metadataAndPathNegativeCases':22,
  'closedTransportCases':17,'actualTransportExtractions':2,'archiveMembers':199,
  'publicUploadedOrDeployed':False,'publicIISHTTPSAndColdWarmStillPending':True,'fullCloneReady':False}
 (D/'verified-stage-r855.json').write_bytes(enc(summary))
 doc='''# 固定R45公网候选：原后端、在线表单与加载优化

交付8文件、2,333,477字节，清单SHA256：1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876。文件清单delivery-manifest.json和delivery目录位于本说明同级。FTP目标：101.201.65.94 /Zhumadian/Zhumadian_Original_Bootstrap_20261104_R45/；应用仍C:/inetpub/wwwroot/Zhumadian/Application。

本包保留R44的Mapper等价预检、静态压缩/缓存与IIS代理、预案/三资源取消/研判及工作台两图样式，合入完整在线表单适配和已验证的组件延迟/分组、版本化静态地址。实际341→344前端完整构建，R44输入到新输入仅七份TS/Vue变化，原SDK接口沿用。此前不能假定完整在线前端与原发布后端兼容；本轮已在不加入督办新模块、不改私有应用配置的原发布后端上实际证实13项正常用户页面通过，故不回退已完成修正。此为受控原模型/普通角色证据，不等于所有真实南港表单已验收。

## 本地实际验证

完整15,586程序/控制来源解析，原11项就绪及完整六组件原健康、正常停启/退出全0、真实Job后代零；普通A正常登录、完整组件、原事件/任务列表、原已完成流程卡片/详情/刷新、字段与意见、无活动审批区、无重复预加载和实际页头退出均过，13项。没有接口替身或业务写入/审批/回调重绑。私有配置从始至终保持，不引入新表、字段、索引、状态枚举或归属变化。

实际网关10次匿名静态GET过：安全端主JS 2624898→819234字节、应急端主JS 1320116→431938字节（identity→gzip），解压SHA相同，哈希资源一年immutable、HTML no-store。安全端JS存在既有品牌文本替换，因此按实际网关解码SHA固定，不误用源文件SHA。该证据不是公网IIS/TLS或用户冷暖导航耗时证明。此前登录阶段JS闭包2579169→1324503字节为本机完整基线比较，不外推公网提速比例，完整首页累计代码基本相同。

两精确基线各15,579程序/控制文件真实预检、196写入/181旧前端移除的正常恢复与第四写故障恢复过，22项描述/路径拒绝；代码夹具不启动进程/网络/库，不复制GIS或数据库，2.81GB逻辑程序仅共享硬链接，未冒算为磁盘释放。运输包两套实际解压、199成员、全部196文件逐SHA和17项闭合/篡改/路径/真实CSS与新JS响应校验过，最长服务器提取路径237字符。更新器只改一份组合契约函数及固定描述常量，原80停启/恢复/鉴权/健康函数AST保持；包装器仅调整压缩包固定计数，其余函数保持。

所有测试终态与代码/配置/本轮前指针恢复确认后，清本轮独立before/已关profile/代码夹具与运输解压目录，保留全部业务数据、原模型/回调、上传、GIS/DLG、三维、固定交付、最终编译输入和小型证据。后续回调仍从task-ui-r806/normal-restart已核链续接，本轮没有重绑。三维8767、正式18891及另一会话held原生代码未改。

## 公网执行范围与体验

未上传或部署。拟上传固定8文件并逐SHA核对；只接受精确R36或R37，先Check_Only核发布/文件/运行归属、数据身份、原11项就绪、原Mapper和停服前连接预算，配置只用于内存核验，不导出。通过后正常停启六组件并196写入/181旧前端移除；保留原Jar/鉴权/历史/数据库/真实配置/上传、安全端业务代码、IIS映射及其余站点，含R44已有IIS代理源码及两份安全端样式入口更新。失败仅本轮updateId/旧新SHA/新备份恢复，退出归属不明即停止，不强杀。读取限定匹配/阶段/PID映像/预算及HTTPS/压缩缓存摘要，不采账号、会话、业务原始行、口令、令牌、运行数据库UUID或原日志。

上线后拟复测首页/应急入口、事件/任务列表、本人有权查看的发起/待办/已办列表和原详情、刷新、正常退出及真实首次/再次导航与关键API。不自动创建或审批公网业务，不据本机文本字段样例声称所有原表单支持。必要截图只取目标窗口/页头和控件，避开名单与业务行；异常登录/安全验证由用户处理。成功后告知明确体验步骤与仍有缺口。本次包不含服务器旧版本删除、腾讯回填或新的公开Git；这些不混入固定八文件发布范围。

仅原生Computer Use操作已打开公网RDP/FTP，操作前提示、焦点变化停止、结束交还。技能D:/CodexData/home/plugins/cache/openai-bundled/computer-use/26.1013.40934/docs/guidance.md明确写明“Do not run Windows terminal commands via UI automation directly or indirectly.”，所以Check_Only/Deploy/Recover三个CMD须用户在服务器手动执行；这不影响后台构建、制包和文件验证。

旧R44/31文件待答范围未执行且字节保持，R45新清单需独立明确范围确认，不依据当前只读授权部署。当前所有真实公网IIS/HTTPS/冷暖/API、全南港业务与全表单验收仍待。完整UE效果效率引擎、EXE GIS/DLG点线面图层/多源空间标牌、Web3D及单系统南港B/S目标继续，fullCloneReady=false，不估完成百分比。
'''
 (D/'固定候选说明.md').write_text(doc,encoding='utf8')
 names=['prepare_original_backend_bootstrap_r847.py','original_public_test_update_r45_bootstrap_r847.py','prepare_r45_owned_backend_r848.py',
  'r45_original_backend_health_r849.py','run_r45_original_backend_r850.py','probe_r45_original_backend_r850.py',
  'verify_r45_original_backend_browser_r850.mjs','probe_r45_original_gateway_r850.py','r45-compatibility-source-pins-r850.json',
  'r45_file_fixture_builder_r851.py','verify_r45_bundle_files_r852.py','build_original_bootstrap_delivery_r853.py',
  'verify_original_bootstrap_transport_r854.py',Path(__file__).name]
 changed=[]
 for name in names:
  raw=(V/name).read_bytes()
  if name.endswith('.py'):ast.parse(raw,filename=name)
  if name.endswith('.json'):json.loads(raw)
  target=A/'tools'/name;assert not target.exists();target.write_bytes(raw);changed.append('tools/'+name)
 wrapper=(D/'delivery/deploy_original_bootstrap_r45.py').read_bytes();target=A/'tools/deploy_original_bootstrap_r45.py';assert not target.exists();target.write_bytes(wrapper);changed.append('tools/deploy_original_bootstrap_r45.py')
 artifacts={'deploy/verification/r45-original-backend-stage-r855.json':enc(summary),'deploy/verification/r45-original-backend-cleanup-r855.json':enc(cleanup),
  'deploy/verification/r45-file-recovery-r852.json':enc(files),'deploy/verification/r45-transport-r854.json':enc(transport),
  'deploy/verification/r45-original-gateway-r850.json':enc(gateway),'deploy/verification/r45-fixed-delivery-manifest.json':(D/'delivery-manifest.json').read_bytes(),
  'deploy/handbook/r45_original_backend_bootstrap_20261104.md':doc.encode('utf8')}
 for rel,raw in artifacts.items():target=A/rel;assert not target.exists();target.write_bytes(raw);changed.append(rel)
 header='## 2026-11-04 R847—R855：完整前端在原发布后端13项过，固定R45运输/恢复验证完成\n\n'
 body='原R44后端/鉴权/历史/IIS及数据pin保持，未加督办模块；完整在线表单和组件延迟/合并/地址兼容前端实际原11就绪/健康/六组件正常0/Job零，普通A真实登录、两列表、原完成流程详情刷新/字段意见、无重复预加载与退出13项过，业务写0/无SQL或回调重绑/私有配置始终不改。网关10 GET过：安全JS2624898→819234B、应急1320116→431938B，gzip/identity同SHA、哈希一年immutable/HTML no-store，非公网证明。两基线15579代码文件完整预检、196写/181移除正常及第四写恢复、22拒绝，运输两实际解压/199成员/17项过。固定R45八文件2333477B，清单1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876，尚未上传/部署；需要明确新范围/桌面交接，服务器CMD按原生技能由用户手动执行。清本轮before/profile/代码夹具/解压，不冒称2.81GB硬链接为物理回收；保全部业务模型/数据/回调/上传/GIS三维和最终交付源。R44/31文件待答来源保持，只原本地Git，无桌面/公网/公开Git/腾讯写；真实IIS/TLS/冷暖/API及全南港全表单/长期UE/EXE GIS标牌/Web3D继续active/fullCloneReady=false。\n\n'
 for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
  raw=p.read_bytes();assert header.encode()not in raw;p.write_bytes((header+body).encode()+raw)
 with(R/'Document/Engine/showcase_demo_completion.md').open('a',encoding='utf8')as out:out.write('\n'+header+body)
 progress=header+body+'\n本轮补证纠正此前无法假定兼容的边界：实际原发布后端已通过13项正常UI，未需督办新模块。R45仍未公网部署；不宣称全南港/全模型或公开干净检出一键构建。\n'
 specific='docs/project/R45原后端加载兼容固定候选进展_20261104.md';assert not(E/specific).exists();(E/specific).write_text(progress,encoding='utf8')
 helper=load('r45_local_git_r855',V/'commit_r18_local_review.py')
 app=helper.commit(A,'2ebe25737ce0f7913ab3791b801b9a99d74702df','review/workplace-r19-live-local-20261031',changed,'app-r855',
  message_override='release: verify original backend with full bootstrap frontend and freeze scoped R45 delivery',update_existing=True)
 engine=helper.commit(E,'da386ffd3b2a317c62eae3588097a335514d759e','review/workplace-r19-live-progress-local-20261031',
  ['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md',specific],'engine-r855',
  message_override='docs: record actual original-backend compatibility and fixed R45 pending public validation',update_existing=True)
 guard.fixed();assert sha(A/'native/main.cpp')==held
 receipt={'application':app,'engine':engine,'heldNativeUnchanged':True,'publicChanged':False,'publicGitPushed':False,
  'fixedR45ManifestSHA256':sha(D/'delivery-manifest.json')}
 (D/'local-review-git-r855.json').write_bytes(enc(receipt));print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
