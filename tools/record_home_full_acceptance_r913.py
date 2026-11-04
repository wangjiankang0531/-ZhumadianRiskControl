"""Independently accept actual SDK/UI evidence, preserve failures and retire owned copies."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,subprocess,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';G=R/'_g/Application'
D=R/'Document/Deployment/home_transfer_full_verified_r913_20261104';assert not D.exists()
P=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def props(p):return dict(s.split('=',1)for s in p.read_text('ascii').splitlines()if'='in s and not s.startswith('#'))
proof=J(R/'work/hf912/verified-home-transfer-r912.json');ui=J(R/'work/home-browser-r912/result.json')
assert proof['passed']and proof['failure']is None and proof['codeRestored']and proof['privateConfigurationUnchanged']and proof['originalCurrentPointerRestored']
assert ui['passed']and not ui['APIsMocked']and ui['approvalRequests']==0 and ui['normalSecurityHomeOriginalSDKAccepted']
assert len(ui['cases'])==18 and all(c['passed']for c in ui['cases'])
assert not any(n.endswith('/YouSheBiaoTiHei-fahbdFno.ttf')or n.endswith('/background-BHYqFd8n.png')for n in ui['homeResourceRequests'])
assert any(n.endswith('home-background-415f7103fab4437c.webp')for n in ui['homeResourceRequests'])and any(n.endswith('YouSheBiaoTiHei-7af84bf1c97ae44e.woff2')for n in ui['homeResourceRequests'])
static=J(R/'work/hf912/normal-restart-static-result.json');assert static['passed']and len(static['rows'])==10
stage=R/'work/original-manager-full-lifecycle-r609/home-transfer-r912/normal-restart'
for n in ['browser-job-terminal.json','home-metadata-terminal.json']:
 t=J(stage/n);assert t['exitCode']==0 and t['actualJobDescendantsZero']and not t['forceTerminationUsed']
oldmeta=R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-result.private.properties'
newmeta=R/'work/original-manager-full-lifecycle-r609/home-transfer-r912/home-navigation-readback.private.properties'
old,new=props(oldmeta),props(newmeta)
assert old['homeSystemBefore']=='0'and old['insertedMetadataRows']=='33'and old['allOtherMetadataDigestsMatched']=='true'and old['accountsRolesBusinessTablesAndSchemaWritten']=='false'
assert new['phase']=='readback-verified'and new['verifiedMetadataRows']=='33'and new['persistentWritesIssued']=='false'and new['exactPreviouslyPreparedMetadataRowsMatched']=='true'
assert sha(P/'full-source-and-restore-plan.private.json')=='6802586b505476efd80c750f9271d6eb6f59ed667aba5f76d973b58a1082c82b'
plan=J(P/'full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for key in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
 for n,before in plan[key].items():assert n not in rows;rows[n]={'before':before,'after':None}
assert all(pin(G/n)==p['before']for n,p in rows.items())
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
cleanup=[];runs=[]
for number in [906,910,912]:
 w=R/'work'/('hf'+str(number));p=J(w/('verified-home-transfer-r'+str(number)+'.json'))
 assert p['codeRestored']and p['privateConfigurationUnchanged']and p['originalCurrentPointerRestored']
 for t in p['terminals']:assert t['controllerExitCode']==0 and t['actualJobDescendantsZero']and t['normalOwnedShutdown']and set(t['exitCodes'].values())=={0}and not t['forceTerminationUsed']
 assert J(w/'code-transaction/journal.json')['phase']=='restored'
 pointer=J(w/'pointer-snapshot/snapshot.private.json');assert pointer['phase']=='restored'and pin(G/'UserData/OriginalServer/current-run.json')==pointer['before']
 before=w/'code-transaction/before';assert before.is_dir()
 for f in before.rglob('*'):
  if f.is_file():
   name=f.relative_to(before).as_posix();assert name in rows and pin(f)==rows[name]['before']and pin(f)==pin(G/name)
 cleanup.append(before)
 browser=R/'work'/('home-browser-r'+str(number));b=J(browser/'browser-terminal.json');assert b['normalBrowserClosed']and b['exitCode']==0 and not b['forceTerminationUsed'];cleanup.append(browser/'chrome-profile')
 runs.append({'stage':'R'+str(number),'aggregatePassed':p['passed'],'normalSixComponentExitAndCodeConfigurationPointerRestored':True,'failure':p['failure'],'browserCaseCount':len(J(browser/'result.json')['cases'])})
for root in cleanup:
 assert root.is_dir()and root.resolve().is_relative_to((R/'work').resolve())and root.resolve()!= (R/'work').resolve()
 for p in [root,*root.rglob('*')]:assert not(p.lstat().st_file_attributes&0x400),'NO_REPARSE_CLEANUP'
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { $c=([string]$_.CommandLine -replace '\\\\','/').ToLowerInvariant(); $c.Contains('d:/project/zhumadian/_g/application') -or $c.Contains('d:/project/zhumadian/work/home-browser-r906') -or $c.Contains('d:/project/zhumadian/work/home-browser-r910') -or $c.Contains('d:/project/zhumadian/work/home-browser-r912') } | Measure-Object).Count"
live=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW);assert live.returncode==0 and live.stdout.decode('utf-8-sig').strip()=='0'
freed=[{'path':str(root.relative_to(R)).replace('\\','/'),'files':sum(p.is_file()for p in root.rglob('*')),'logicalBytes':sum(p.stat().st_size for p in root.rglob('*')if p.is_file())}for root in cleanup]
free=shutil.disk_usage(R).free
for root in cleanup:
 assert root.resolve().is_relative_to((R/'work').resolve());shutil.rmtree(root)
ack=R/'Document/Coordination/交接消息/驻马店3已读D67开发协议_20261104_r907.json';a=J(ack);assert a['receiverReadAndVerified']and a['archiveBytesAndTwelveDeclaredSourceHashesMatched']and not a['serverChanged']
review=[]
for folder in ['home_full_r905','home_full_r909','home_full_r912']:
 for p in (V/folder).iterdir():
  if p.is_file()and p.suffix in ['.py','.mjs','.java','.json']:review.append((p,'tools/experimental_source/'+folder+'/'+p.name))
for n in ['prepare_home_full_candidate_r905.py','prepare_home_browser_r906.py','OwnHomeNavigationFixtureR909.java','prepare_home_fixture_retry_r909.py','prepare_home_async_retry_r912.py','record_home_full_acceptance_r913.py']:
 review.append((V/n,'tools/'+n))
for p,rel in review:
 if p.suffix=='.py':ast.parse(p.read_bytes(),filename=rel)
report={'schema':'xnby.home-transfer.original-sdk-acceptance.v1','recordedAt':datetime.datetime.now().astimezone().isoformat(),'passed':True,
 'sameFourFrontendCandidateFilesAsR903':True,'completeProgramSources':15589,'actualOriginalCompiledApplicationAndSDK':True,'APIsMocked':False,
 'UIAssertionsIncludingRepeatedLoginAndDetailChecks':ui['cases'],'assertionCount':18,'actualGatewayGzipAndDecodedChecks':10,
 'normalOriginalNonadminLoginBothPortals':True,'eightAsyncNavigationEntriesRendered':True,'newHomeResourcesRequestedWithoutOldLargeFiles':True,
 'businessCRUDOrApprovalOrCallbackRebindingIssued':False,'originalAuthenticationSigningAndAuthorizationCodeRetained':True,
 'fixtureMetadataPreparation':{'onlyExistingOwnedSyntheticG':True,'homeSystemWasAbsent':True,'metadataRowsInsertedOnce':33,'tables':['base_system','base_module','base_authorize'],'existingUserAndRoleTablesUntouched':True,'allOtherExistingMetadataDigestsMatchedDuringPreparation':True,'latestReadbackWasReadOnly':True,'latestReadbackRows':33,'seedNotRepeated':True,'journalSHA256':sha(R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-journal.private.properties')},
 'runHistory':runs,'finalSixComponentAndBrowserJobsNormallyExited':True,'independentRestoredCodeConfigurationAndPointerReadback':True,
 'ownedCleanup':freed,'observedFreeSpaceDeltaNotExclusiveAttribution':shutil.disk_usage(R).free-free,
 'threeDDevelopmentD67ReceivedArchiveAndTwelvePinsVerified':True,'threeDPackageExecutedOrInstalled':False,
 'publicInstalled':False,'publicTransportAndRecoveryNotYetPrepared':True,'publicAuthenticatedTimingAfterThisCandidateStillPending':True,
 'interceptedFullAppProbeIsNotCacheOrPerformanceBenchmark':True,'sourceReviewFiles':[{'target':rel,'bytes':p.stat().st_size,'sha256':sha(p)}for p,rel in review],'fullCloneReady':False}
text='''# 首页资源优化完整应用验收（R913）

同一份R900四文件候选已经在完整原应用与原SDK中通过18条页面断言，包含重复登录和详情检查，不代表18个独立新功能。本轮没有公网部署。

原六组件/原11项就绪和鉴权健康通过；普通合成账号实际完成应急端登录、两个业务列表、既有已完成流程详情及原字段/意见回看、刷新和退出，再完成安全端登录、首页八个异步导航入口、新背景/字体实际使用、刷新和退出。核心登录和非管理员身份检查保持原逻辑，无接口替身、业务创建/审批或回调重绑。新首页不请求旧大PNG/TTF；网关另有10项原JS/CSS压缩缓存及解压SHA检查通过。

## 测试环境问题与保留的失败

R906通过原应急端13条检查和安全端首次显示，但导航CurrentUser返回业务400，整轮false。检查确认自有G从未准备home应用元数据。R910在精确库UUID/端口/目录和新命名空间下，仅新增base_system/base_module/base_authorize三表合成首页导航33行，未改用户/角色表、原签名鉴权、业务行或结构；原有其他元数据摘要保持。R910随后因探针在异步菜单响应前立即断言八入口而失败，该失败保留。

R912没有重发准备事务，只读事务核同原33行及原准备journal，再等待真实菜单返回。两个入口正常非管理员身份保持，CurrentUser包括home均返回原成功结构，真实八入口出现后完成刷新/退出。原鉴权检查没有针对home放宽或增加例外。合成导航不是公网数据，也不代表测试覆盖了八入口下所有业务。schema/字段/索引/业务状态语义未变，本轮不需要重生成物理模型。

R906/R910/R912三轮六组件均正常0、实际Job后代0，原配置/安装身份/代码/本轮原运行指针恢复，独立再次逐SHA核对。只清三份已还原代码备份和三个已退出测试浏览器缓存；保留全部数据库、模型、任务、33行合成导航、前像journal、执行日志和最终资源。最新业务回调仍以feedback-r880/after-submit-r889的已核链为前像；本轮只读，不重绑到临时端口。

## 仍未完成的发布工作

四个实际前端文件与R903静态呈现验证一致：背景4854984→2591292B，字体1414784→745328B，全部7194字形/字符映射和原ICC保留。R903实际Nginx与1366/1920/3840逐像素/缓存检查保持。本轮完整应用为请求拦截保护下的功能检查，不把其耗时或缓存作为普通浏览器性能基准。

下一步以固定公开R45基线准备稀疏更新器/文件清单/正常及失败恢复验证，随后再确定公网交接范围。发布前重新发现实际现场版本/控制器/路由/三维已落地差异；不使用过期j2，不覆盖新三维改动。公网MIME/缓存/正常角色体验和实际耗时要在部署后再验。应急入口favicon404、小脚本首次加载和列表API耗时仍在台账，不据此宣布所有页面优化完成。

已读取三维D67更新，归档104806B的SHA与12项声明源码哈希匹配，未执行归档或重跑对方149测试；它明确不是部署请求，可信EXE入口/服务监督/部署恢复尚待。已写自身接收回执，仍无直接会话消息/自动唤醒能力，本轮未改IIS或三维接口。

源码和文档只追加原本地两分支，不新建分支、不改main、不发私有祖先，尚无本轮公开Git推送。公开干净检出一键完整构建未宣称。UE效果效率引擎、EXE GIS/DLG点线面图层/多源空间标牌、Web3D和单系统南港全部B/S目标继续active/fullCloneReady=false。
'''
D.mkdir();(D/'verified-original-sdk-home-r913.json').write_bytes(enc(report));(D/'完整应用验收与下一发布范围.md').write_text(text,encoding='utf8')
files=[]
for p,rel in review:
 q=A/rel;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());files.append(rel)
for rel,raw in {'deploy/verification/home_transfer_full_r913_20261104.json':enc(report),'deploy/handbook/home_transfer_full_r913_20261104.md':text.encode('utf8')}.items():
 q=A/rel;assert not q.exists();q.write_bytes(raw);files.append(rel)
header='## 2026-11-04 R913：首页四文件候选在完整原应用18断言通过，准备固定发布包\n\n'
body='R906原应急13断言/安全首次显示过，home CurrentUser400整轮false；G确缺home元数据。R910仅精确自有库新增33条合成系统/菜单/授权，其他既有元数据摘要保持、用户角色表/原鉴权/业务结构不改，后探针过早断言异步菜单失败。R912只读复核同33条不再准备，等待原响应，双入口普通非管理员实际登录/八导航/新图字体/刷新/原流程详情/退出共18含重复断言、网关10检查过。原核心身份检查未放宽；不当八入口全部业务验收。三轮六组件全0/Job零及代码配置原指针独立恢复；只清三before/三退profile，保全部数据/导航/journal日志，最新callback仍after-submit-r889/441a3970。与R903同四前端字节；拦截式完整应用测试不当性能基准。D67已核归档与12声明源码且写自身回执，无部署/对方149重跑。下一固定R45稀疏运输/恢复及发布前现场重新发现，不套j2/覆盖三维。公网仍最后已核R45，新候选未部署/新公开Git未推，favicon404/小脚本/API耗时和全南港仍待。完整长期目标active/fullCloneReady=false。\n\n'
rel='docs/project/首页候选完整应用验收_20261104_r913.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:p.write_bytes((header+body).encode('utf8')+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
spec=importlib.util.spec_from_file_location('local_r913',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.commit(A,'50b17f0e9d17e587494a0c5859b85659a2e4b18a','review/workplace-r19-live-local-20261031',files,'app-r913',message_override='test: accept lossless home assets through original SDK and scoped normal-user navigation',update_existing=True)
e=h.commit(E,'2de83d813c807f037aeff54cb3c2618f56ffa2f9','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r913',message_override='docs: record original-app home acceptance and received D67 development contract',update_existing=True)
(D/'local-review-git-r913.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False}));print(json.dumps({'passed':True,'assertions':18,'actualGatewayChecks':10,'sourceReviewFiles':len(review),'application':a,'engine':e,'publicInstalled':False}))
