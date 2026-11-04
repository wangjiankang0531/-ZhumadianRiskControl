"""Record final compiled bootstrap and real SDK pages; retire only own verified temporary files."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/grouped_component_bootstrap_r846_20261104'
J=lambda p:json.loads(p.read_bytes())
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not D.exists()
 previous=load('cleanup_scope_r846',V/'record_research_task_ui_r812.py');previous.fixed()
 held=sha(A/'native/main.cpp')
 builds={tag:J(R/f'work/{folder}/verified-bounded-full-build-r673.json')for tag,folder in [
  ('r815','lazy-layout-full-r815'),('r818','authenticated-installer-full-r818'),('r828','authenticated-installer-map-r828'),('r829','authenticated-installer-grouped-r829'),('r835','canonical-bootstrap-full-r835'),('r841','canonical-bootstrap-compatible-r841')]}
 for b in builds.values():
  assert b['passed']and b['completeBuildExecuted']and b['sourceRestored']and b['terminal']['nodeExitCode']==0
  assert b['terminal']['actualJobDescendantsZeroBeforeClose']and b['maximumReportedJobMemoryBytes']<3*1024**3
 analysis=J(V/'canonical-compatible-analysis-r842/result.json');links=J(V/'verified-canonical-compatible-artifact-r843.json')
 assert analysis['passed']and links['passed']and links['compiledFiles']==344
 assert links['computedRuntimeImportsNotStaticallyProven']==0 and links['localReferencesChecked']==1773
 grouping=J(R/'work/canonical-bootstrap-compatible-r841/grouping-proof.json')
 assert grouping['passed']and grouping['sourceLateChunkCount']==37 and grouping['groupedChunks']==1 and not grouping['earlyModulesMoved']
 lifecycles={tag:J(R/f'work/bootstrap-full-{tag}/verified-component-bootstrap-{tag}.json')for tag in ['r822','r825','r833','r839','r845']}
 assert not lifecycles['r822']['passed']and lifecycles['r825']['passed']and lifecycles['r833']['passed']
 for proof in lifecycles.values():
  assert proof['codeRestored']and proof['taskConfigurationRestoredBeforeCode']and proof['originalCurrentPointerRestored']
  assert len(proof['terminals'])==1
  terminal=proof['terminals'][0]
  assert terminal['controllerExitCode']==0 and terminal['normalOwnedShutdown']and terminal['actualJobDescendantsZero']
  assert set(terminal['exitCodes'])=={'store','mysql','redis','platform','business','gateway'}and all(c==0 for c in terminal['exitCodes'].values())
 browsers={tag:J(R/f'work/bootstrap-browser-{tag}/result.json')for tag in ['r822','r825','r833','r839','r845']}
 assert browsers['r822']['failure']=='READONLY_BROWSER_UNEXPECTED_MUTATION_REFUSED'
 for tag in ['r825','r833','r839','r845']:
  proof=browsers[tag]
  assert proof['passed']and len(proof['cases'])==({'r825':11,'r833':11,'r839':12,'r845':13}[tag]) and proof['approvalRequests']==0 and not proof['APIsMocked']
  assert proof['actualCompiledApplicationAndOriginalSDK']and proof['fullInstallerRequestedOnlyAfterLogin']
  assert all(row['endpoint']in ['/zhumadian/api/jnpf/oauth/Login','/zhumadian/api/jnpf/permission/Users/ImUser/Selector/0']
   for row in proof['requests']if row['method']not in ['GET','HEAD'])
 for tag in browsers:
  assert J(R/f'work/bootstrap-browser-{tag}/browser-terminal.json')['normalBrowserClosed']
  p=R/f'work/original-manager-full-lifecycle-r609/component-bootstrap-{tag}/normal-restart/browser-job-terminal.json'
  terminal=J(p);assert terminal['exitCode']in [0,1]and terminal['actualJobDescendantsZero']and not terminal['forceTerminationUsed']
 query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
 p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert p.returncode==0 and int(p.stdout.decode('utf-8-sig').strip())==0
 code=load('component_code_pin_r846',A/'tools/owned_candidate_code_transaction_r543.py')
 plans={tag:J(R/f'Document/Deployment/{folder}/full-source-and-restore-plan.private.json')for tag,folder in [
  ('r822','authenticated_installer_candidate_r820_20261104'),('r825','authenticated_installer_candidate_r820_20261104'),('r833','grouped_installer_candidate_r831_20261104'),('r839','canonical_bootstrap_candidate_r838_20261104'),('r845','canonical_compatible_candidate_r844_20261104')]}
 assert sha(G/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
 D.mkdir();removed=[];freeBefore=shutil.disk_usage(R).free
 for tag,plan in plans.items():
  rows=dict(plan['mutations'])
  for key in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
   for name,pin in plan[key].items():assert name not in rows;rows[name]={'before':pin,'after':None}
  assert all(code.pin(G/n)==row['before']for n,row in rows.items())
  assert code.pin(G/'private/server-configuration.json')==plan['configBefore']and code.pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
  before=R/f'work/bootstrap-full-{tag}/code-transaction/before'
  assert J(before.parent/'journal.json')['phase']=='restored'
  files=previous.scan(before,R/'work');expected={n:row['before']for n,row in rows.items()if row['before']is not None}
  assert set(files)==set(expected)and all(code.pin(before/n)==pin for n,pin in expected.items())
  shutil.rmtree(before);removed.append(dict(scope=tag+'-restored-same-sha-before',files=len(files),logicalBytes=sum(files.values())))
 for tag in browsers:
  root=R/f'work/bootstrap-browser-{tag}/chrome-profile';files=previous.scan(root,R/'work');shutil.rmtree(root)
  removed.append(dict(scope=tag+'-normally-closed-browser-profile',files=len(files),logicalBytes=sum(files.values())))
 for tag,folder in [('r815','lazy-layout-full-r815'),('r818','authenticated-installer-full-r818'),('r828','authenticated-installer-map-r828'),('r829','authenticated-installer-grouped-r829'),('r835','canonical-bootstrap-full-r835')]:
  root=R/f'work/{folder}/dist';files=previous.scan(root,R/'work')
  assert set(files)==set(builds[tag]['files'])and all(code.pin(root/n)==pin for n,pin in builds[tag]['files'].items())
  shutil.rmtree(root);removed.append(dict(scope=tag+'-retired-rebuildable-compiled-output',files=len(files),logicalBytes=sum(files.values())))
 cleanup=dict(passed=True,removed=removed,allActualOwnProcessesExitedBeforeCleanup=True,
  observedVolumeFreeDeltaBytes=shutil.disk_usage(R).free-freeBefore,volumeDeltaNotExclusive=True,
  businessDataModelsCallbacksUploadsGISRemoved=False,finalR841OutputAndR828ModuleMappingRetained=True)
 (D/'verified-cleanup-r846.json').write_bytes(enc(cleanup))
 baseline=analysis['baseline'];candidate=analysis['candidate'];ui=browsers['r845']
 assert len(ui['anonymousJavaScriptRequests'])==3 and len(browsers['r833']['anonymousJavaScriptRequests'])==5
 assert not any('/emergency/assets/'in n for n in ui['allJavaScriptRequests'])
 assert any(c['case']=='normal-header-logout-returns-to-business-login-not-static-base'and c['passed']for c in ui['cases'])
 summary=dict(passed=True,actualFullBuilds=6,actualSixComponentLifecycles=5,finalUICases=13,
  loginJSBeforeBytes=baseline['loginClosure']['bytes'],loginJSAfterBytes=candidate['loginClosure']['bytes'],
  loginGzipBeforeBytes=baseline['loginClosure']['gzipBytes'],loginGzipAfterBytes=candidate['loginClosure']['gzipBytes'],
  authenticatedHomeJSBeforeBytes=baseline['authenticatedHomeBootstrapClosure']['bytes'],
  authenticatedHomeJSAfterBytes=candidate['authenticatedHomeBootstrapClosure']['bytes'],
  authenticatedHomeJSChunksBefore=baseline['authenticatedHomeBootstrapClosure']['files'],
  authenticatedHomeJSChunksAfter=candidate['authenticatedHomeBootstrapClosure']['files'],
  deferredChunksGroupedFrom=37,deferredChunksGroupedTo=1,anonymousInstallerNotFetched=True,anonymousJSURLsBeforeCanonicalization=5,anonymousJSURLsAfterCanonicalization=3,actualHeaderLogoutAtOriginalBusinessRootPassed=True,
  originalFullComponentsAvailableAfterNormalLogin=True,actualNormalNonadminListsAndCompletedWorkflowRefresh=True,
  businessMutationsOrCallbackRebinding=False,allCodeConfigurationPointersRestored=True,
  entirePublicOrAuthenticatedEndToEndSpeedupProven=False,publicChanged=False,publicGitPushed=False,fullCloneReady=False)
 (D/'verified-component-bootstrap-r846.json').write_bytes(enc(summary))
 doc='# 应急端登录加载与静态地址兼容验收（R815—R846，2026-11-04）\n\n最终本地候选保留原全部组件和业务，延迟全量全局组件注册、合并实际延迟模块、统一静态预加载地址。三份TS编译输入变化为global-import.ts、router/index.ts及新增OriginalAuthenticatedInstallerR817.ts；另有Vite构建选项变化，其他完整在线源输入均保持。原令牌门禁/白名单/CurrentUser/菜单规则和所有业务接口不改；Promise只共享代码加载，不缓存身份或业务。\n\n## 体积、请求与取舍\n\n| 范围 | 原完整在线基线 | 最终候选 |\n| --- | ---: | ---: |\n| 登录阶段静态JavaScript闭包 | 2,579,169字节 | 1,324,503字节 |\n| 同一闭包逐文件gzip估算 | 807,080字节 | 434,136字节 |\n| 登录至已登录首页累计JavaScript | 2,580,212字节 | 2,580,303字节 |\n| 累计首页脚本数 | 3 | 5 |\n\n登录阶段JS减少约48.6%，gzip估算减少约46.2%，不是公网耗时改善比例。CSS/字体/图片/API不在JS表内。完整登录至首页累计JS仍基本相同且多两个脚本，不声称所有模块整体加速。344文件、180JS、104CSS及1773处本地引用实际校验，无未证明的计算式导入。\n\n第一种仅延迟布局的实验只少约52KB且增加请求，未选用。原始全量组件延迟方案把首页所需JS拆为41块；同源码重建仅记录模块，全部输出SHA与前次一致；按真实模块图排除登录阶段已用模块，将37个延迟块/926模块显式合并为1块。Rollup onlyExplicitManualChunks及实际组内模块校验防止把早期依赖扫入。首页相关JS为5块，完整组件仍在。\n\n浏览器随后实际观察到未版本化assets与branding-20261025/assets两套URL，登录前3份文件出现5个不同URL。源代码证明网关对assets静态路径重写而Vite部分预加载由基础地址拼接，需统一构建静态base。R835/R839统一后12项页面与无别名请求过，但进一步源码审查发现应用BASE_URL还供退出登录、静态地图/编辑器资源使用，故该中间包未选用。最终R841将Vite静态base设为版本化地址，同时按实际已安装Vite的define顺序保留应用import.meta.env.BASE_URL原值及VITE_APP_BASE_PATH，原静态JSON/编辑器路径和业务退出跳转均保持。最终真实浏览器登录前只见3个版本化JS URL，整个所测模块导航没有未版本化预加载别名，并实际退出至正常业务登录页。\n\n## 实际服务与页面\n\n六次完整构建均真实0/Job零、源码恢复，沿用3GiB非终止Job、2GiB物理余量及提交余量。五次完整六组件原健康及正常关闭均全0，6GiB门槛、控制器3GiB/浏览器1GiB保持，不关闭用户窗口或强杀。\n\nR822前五项已通过但工具把原人员查询POST误作业务写而拒绝；保留失败。原user-select/API源码及原SDK前轮成功记录证明ImUser/Selector/0为挂载分页查询，R825只精确放行其四个固定分页/空关键词参数，其余业务写仍拒绝。R825和R833各11项、R839十二项通过；最终R845十三项实际页面过：匿名登录不下载完整安装器、普通A正常登录/非管理员、登录后原组件注册齐全、事件/任务两原列表HTTP及业务成功、原发起人卡片同一已完成实例、原只读字段/刷新/意见/无活动审批区、无未版本化脚本请求、真实页头菜单及原确认框退出到业务登录页。\n\n没有接口替身或直接API代替页面。仅正常登录与上述原查询POST，审批0次，无任务/事件新增、SQL修改或回调重绑；不输出账号响应、口令、令牌或业务原文。本机导航时间不外推公网。字段缺省/null仅按已证DB与显示等价规则，未放宽到任意值。\n\n## 恢复、清理与交付边界\n\nG正常停止，全部代码/私有任务配置/本轮运行指针、数据身份逐项恢复；旧ready不作活动证明。核真实句柄/Job终态及CIM无G引用后，仅清五份同SHA已恢复代码before、五个已闭浏览器profile和五份退役可重建dist；保留最终R841输出、R828模块图、全部源码/意图/前像/小日志、所有数据库/模型/回调/上传/GIS/DLG/三维。退役R820/R831/R838计划需重建输入，不能当现成安装包重跑。后续业务回调仍接task-ui-r806/normal-restart已核链，本轮未重绑。\n\n本候选基于完整在线前端，包含以前未公网交付的联测范围，不能直接覆盖公网并假定后端兼容。下一公开包应以精确公网来源保留既有业务兼容再形成固定范围/预检/验收。本轮没有部署、桌面或公开Git/腾讯写，R44固定八文件与待答31文件及来源SHA保持。公网此前仍未压缩/no-store的结论没有被本机结果覆盖，公网性能验收仍未通过。\n\n字段/索引/状态/归属模型不变，不运行无关DB迁移或生成。仅同步既有本地Git分支，依赖原SDK及本地私有准备数据，不宣称公开干净检出一键构建。完整UE效果效率引擎、EXE GIS/DLG图层多源标牌、Web3D与单系统南港B/S目标保持active，全模板/业务仍待，不估完成百分比。\n'
 (D/'应急端登录加载拆分与真实页面验收.md').write_text(doc,encoding='utf8')
 names=['original_lazy_layout_r815.py','run_lazy_layout_full_build_r815.py','build_lazy_layout_full_r815.mjs','build_lazy_layout_bootstrap_r815.mjs','analyze_lazy_layout_r816.mjs',
  'original_authenticated_installer_r817.py','run_authenticated_installer_full_build_r818.py','build_authenticated_installer_full_r818.mjs','build_authenticated_installer_bootstrap_r818.mjs',
  'analyze_authenticated_installer_r819.mjs','prepare_authenticated_installer_candidate_r820.py','authenticated_installer_health_r821.py',
  'probe_authenticated_installer_r822.py','verify_authenticated_installer_browser_r822.mjs','run_component_bootstrap_full_r822.py','component-bootstrap-r822-source-pins.json',
  'verify_authenticated_installer_artifact_r823.mjs','probe_authenticated_installer_r825.py','verify_authenticated_installer_browser_r825.mjs','run_component_bootstrap_full_r825.py','component-bootstrap-r825-source-pins.json',
  'analyze_authenticated_tradeoff_r827.mjs','run_authenticated_installer_map_r828.py','build_authenticated_installer_map_r828.mjs','build_authenticated_installer_bootstrap_r828.mjs',
  'prepare_grouped_installer_r829.py','run_grouped_installer_full_build_r829.py','build_grouped_installer_full_r829.mjs','build_grouped_installer_bootstrap_r829.mjs',
  'analyze_grouped_installer_r830.mjs','prepare_grouped_installer_candidate_r831.py','verify_grouped_installer_artifact_r832.mjs',
  'grouped_installer_health_r833.py','verify_grouped_installer_browser_r833.mjs','probe_grouped_installer_r833.py','run_grouped_component_full_r833.py','component-bootstrap-r833-source-pins.json','run_canonical_bootstrap_build_r835.py','build_canonical_bootstrap_full_r835.mjs','build_canonical_bootstrap_r835.mjs','analyze_canonical_bootstrap_r836.mjs','verify_canonical_artifact_r837.mjs','prepare_canonical_bootstrap_candidate_r838.py','canonical_bootstrap_health_r839.py','verify_canonical_bootstrap_browser_r839.mjs','probe_canonical_bootstrap_r839.py','run_canonical_bootstrap_full_r839.py','component-bootstrap-r839-source-pins.json','run_canonical_compatible_build_r841.py','build_canonical_compatible_full_r841.mjs','build_canonical_compatible_bootstrap_r841.mjs','analyze_canonical_compatible_r842.mjs','verify_canonical_compatible_artifact_r843.mjs','prepare_canonical_compatible_candidate_r844.py','canonical_compatible_health_r845.py','verify_canonical_compatible_browser_r845.mjs','probe_canonical_compatible_r845.py','run_canonical_compatible_full_r845.py','component-bootstrap-r845-source-pins.json',Path(__file__).name]
 files=[]
 for name in names:
  raw=(V/name).read_bytes()
  if name.endswith('.py'):ast.parse(raw,filename=name)
  if name.endswith('.json'):json.loads(raw)
  dest=A/'tools'/name;assert not dest.exists();dest.write_bytes(raw);files.append('tools/'+name)
 root=R/'work/canonical-bootstrap-compatible-r841'
 for name in ['src/global-import.ts','src/router/index.ts','src/OriginalAuthenticatedInstallerR817.ts']:
  raw=(root/'compiled-inputs'/name).read_bytes();assert code.pin(root/'compiled-inputs'/name)==J(root/'actual-compiled-source-files.json')[name]
  rel='source-review/authenticated-bootstrap-r817/'+name;dest=A/rel;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files.append(rel)
 artifacts={'deploy/verification/component-bootstrap-r846.json':enc(summary),'deploy/verification/component-bootstrap-cleanup-r846.json':enc(cleanup),
  'deploy/verification/component-bootstrap-static-graph-r832.json':enc(links),'deploy/verification/component-bootstrap-groups-r829.json':enc(grouping),
  'deploy/handbook/component_bootstrap_r846_20261104.md':doc.encode()}
 for rel,raw in artifacts.items():dest=A/rel;assert not dest.exists();dest.write_bytes(raw);files.append(rel)
 header='## 2026-11-04 R815—R846：登录前组件延迟/合并与静态地址兼容，真实普通角色13项通过\n\n'
 body='登录阶段JS2579169→1324503B、gzip估算807080→434136B；累计首页2580212→2580303B基本同、脚本原3/中间41/最终5。37延迟块显式合1，实际匿名JS URL5→3，构建静态base与应用BASE_URL/路由根分开，原地图编辑器路径保持；页头实际退出回正常登录。最终344文件/1773引用和普通A真实登录、完整组件/两列表/原已完流程卡片详情刷新/无重复预加载/退出13项过；不宣称公网或所有模块整体提速。保留查询POST过窄拒绝与路径语义风险中间方案，原业务写0、无SQL/回调重绑。六构建/五实际六组件均正常0/Job零，代码/私有配置/指针复原；清五before/五profile/五退役dist，保最终R841/模块图/全部数据模型日志GIS三维。公开兼容构建及真实IIS/冷暖/API仍待，R44八文件9a9db792/31文件385715bc待答来源保持，仅原本地Git，无桌面/公网/公开Git/腾讯写；完整UE/EXE GIS多源标牌/Web3D/单系统南港active/fullCloneReady=false。\n\n'
 for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
  raw=p.read_bytes();assert header.encode()not in raw;p.write_bytes((header+body).encode()+raw)
 with (R/'Document/Engine/showcase_demo_completion.md').open('a',encoding='utf8')as out:out.write('\n'+header+body)
 helper=load('component_local_git_r846',V/'commit_r18_local_review.py')
 app=helper.commit(A,'9b0debdcda714d951279afd4d99a2779e4fce128','review/workplace-r19-live-local-20261031',files,'app-r846',
  message_override='perf: defer complete authenticated components and coalesce verified late modules; verify real SDK pages',update_existing=True)
 engine=helper.commit(E,'d97217184151fbcd374f591ece71ee5f433ec812','review/workplace-r19-live-progress-local-20261031',
  ['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r846',
  message_override='docs: record final bootstrap split, actual normal-user regression and pending public acceptance',update_existing=True)
 previous.fixed();assert sha(A/'native/main.cpp')==held
 receipt=dict(application=app,engine=engine,heldNativeUnchanged=True,publicChanged=False,publicGitPushed=False,finalNormalUserUIAccepted=True)
 (D/'local-review-git-r846.json').write_bytes(enc(receipt));print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
