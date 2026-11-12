"""Document actual approved R51 delivery and separate local D175 tests; local Git only."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_home_same_window_r51_20261112';QA=R/'Document/Deployment/resource_control_http_r2429_20261112'
S=A/'tools/experimental_source/r51_delivered_control_http_r2430';P=A/'deploy/verification/r51_delivered_control_http_r2430'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def copy(src,dst):
 assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
 with src.open('rb')as r,dst.open('xb')as w:shutil.copyfileobj(r,w)
 assert sha(src)==sha(dst)
def main():
 assert not S.exists()and not P.exists()
 upload=j(D/'server-upload-readback-r2385.json');pre=j(D/'server-check-submission-r2386.json');apply=j(D/'server-apply-observation-r2424-3.json');external=j(D/'external-https-r2427-1.json')
 assert all(r['shaAndBytesMatch']for r in upload['files'])and pre['passed']and apply['operation']['operationExitCode']==0 and external['passed']
 assert apply['postApply']['programWritesSHA256Matched']==526 and apply['postApply']['retiredFilesMissing']==520 and apply['postApply']['originalRuntimeDataIdentityMatched']
 assert sha(D/'prepared-manifest.json')=='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
 qa=j(QA/'verification.json');outer=j(QA/'outer-terminal.json');retirement=j(QA/'retirement-result.json')
 assert qa['passed']and qa['distinctChecks']==49 and outer['rootExitCode']==0 and outer['actualJobBeforeClose']==0 and retirement['retiredFiles']==4712
 held=sha(A/'native/main.cpp')
 summary={'at':datetime.datetime.now().astimezone().isoformat(),'actualRelease':'R51','releaseSHA256':apply['actualReleaseSHA256'],'preparedManifestSHA256':sha(D/'prepared-manifest.json'),
  'explicitUserApprovalReceived':True,'actualUploadedFiles':4,'actualUploadedBytes':5614188,'uploadedFilesAllSHAMatched':True,'exactR50PreflightPassed':True,
  'originalApplyExitCode':0,'originalHealthReadyAndDataIdentityMatched':True,'programWriteSHAMatches':526,'retiredFrontendPathsMissing':520,
  'durableWrapperOwnedAndRealControllerHandleRetained':apply['wrapper']['owned']and apply['postApply']['actualControllerHandleRetainedByApprovedWrapper'],
  'operationalControllerAndWrapperIntentionallyRunningNotJobZeroClaimed':True,'wrapperAndControllerNumericPIDsOmittedFromReviewSummary':True,
  'rawScopedOperationEvidenceRetainedLocally':True,'externalFirstAcceptanceAt':external['at'],'externalChecksPassed':len(external['checks']),
  'normalOriginalLoginBrowserAnd252AcceptancePending':True,'userNotifiedImmediatelyAfterExternalSuccess':True,'250UserRetestAskedAwaitingReply':True,
  'databaseUploadsGISModelsConfigurationEmergencyAndIISChanged':False,'resourceControlD175OrD176Published':False,'serverHistoryDeleted':False,'publicGitPushed':False}
 put(D/'actual-delivery-summary-r2430.json',summary);put(P/'actual-delivery-summary.json',summary)
 copy(D/'external-https-r2427-1.json',P/'external-https.json')
 for name in('verification.json','outer-terminal.json','retirement-result.json','support-view-storage-plan.json'):copy(QA/name,P/('local-D175-'+name))
 qa_scope={'actualNewQualifiedTenPlus953':True,'sourceDriverSHA256':outer['driverSHA256'],'distinctChecks':49,
  'actualOriginal44ManagedWorker':True,'originalCurrentUserAndGISProviderExplicitlySynthetic':True,
  'onlyQARegisteredGISFactoryAndSyntheticLauncherAdapted':True,'originalProductModulesAndHTTPHandlersUnmodified':True,
  'actualOriginalStopProtocolAndKernelExitHandles':True,'actualQualifiedConfigurationSaveBetweenOwnedRoots':True,
  'liveControllerBlocksRootChange':True,'managerRootZeroNotFalselyClaimedAsJobZero':True,
  'GISOutlivesFirstManagerThenNewManagerReusesAndNormallyStopsIt':True,'allOuterAndInnerRootsAndJobsFinallyNormalZero':True,
  'real250ConfigurationInstallManifestActiveAndOwnerUnchanged':True,
  'rawOSGBDataCopiedOrVerifiedOrRendered':False,'originalProvider_start_ownedAndV2GuardRecoveryAccepted':False,
  'ordinaryUserPublicLoginTLSBrowserAnd252Accepted':False,'localPortsOnlyDynamicNever18767Or18768':True,
  'inheritedTestHeaderStillSaysD172ActualConstantsAndProgrammePinAreD175':True}
 put(QA/'evidence-scope.json',qa_scope);put(P/'local-D175-evidence-scope.json',qa_scope)
 recipes=['upload_fixed_home_r51_r2385.py','run_fixed_home_r51_r2386.py','poll_fixed_r51_r2424.py','verify_public_r51_r2427.py',
  'resource_control_http_backend_r2422.py','resource_control_chain_body_r2422.py','prepare_control_chain_r2422.py','test_resource_control_chain_r2422.py',
  'run_control_chain_r2423.py','retire_control_support_views_r2429.py','record_r51_delivered_and_control_http_r2430.py']
 for name in recipes:copy(V/name,S/'recipe'/name)
 for name in('public_home_r51_controller.py','durable_original_operation_r2327.py'):copy(D/name,S/'fixed-server-source'/name)
 for name in('prepared-manifest.json','fixed-transport-scope.json'):copy(D/name,S/'fixed-transport'/name)
 note='''R2430 固定R51已上线；正常两机最终验收仍待

用户已明确批准固定R51四文件/5,614,188字节/清单47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed。沿固定主机密钥SSH上传至指定FTP目录并逐SHA回读通过；prepare/check均0，服务器精确R50与完整文件/模型、原就绪、运行/数据库身份、Mapper和停机前预算通过。只提交一次已核独立WMI后台包装器，正常停启原受控应用，实际部署操作返回0；不是凭新release文件存在认定成功，也不把仍持有运行控制器的包装器误当应当Job0的泄漏。

实际R51 release SHA b36491663db37033ae2fc450b0209e864d5ebd7b7b7ed1bba7fda6a7e5545323。独立回核新控制器和包装器真实映像/命令归属与Popen句柄保持；原健康就绪及原数据身份一致，526个写入文件逐SHA匹配，520退役安全端前端路径已无文件。没有改原Jar、鉴权、真实配置、数据库、上传、GIS、29场景模型、应急端或IIS，未混入D175/D176/资源新功能，也未执行服务器历史清理。原始限定回执在本部署目录；供源码审阅的summary刻意不含实际公网控制器/包装器数字PID、运行UUID、账号或原日志。

2026-11-12 16:12:33（北京时间）首轮公网13项通过：根与/home/sceneViewer HTTPS200，新HTML引用index-BuFDAtvn而非旧BYn，新入口引用Home index-ChrBvWBP；实际Home7834字节SHA c8c88dbf…符合真实原Nginx品牌过滤证据，保同窗口.push("/sceneViewer")且不再window.open该scene入口或旧8767。真实gzip解压逐字一致、immutable/Vary保持，旧index-w-VlSjlt返回404，原scene/index.html SHA370aa6ce…保持，原getLoginConfig code200，本机250带可信Origin的18767 discovery200/ready。未读取/回传验证码答案、口令、令牌/Cookie、业务原文或discovery实例/challenge值。已在首验后立即向用户通知R51上线，并请250从正常公网首页Ctrl+F5后点击复测；未等文档/Git收尾才通知。

体验路径：https://www.joinlinksmart.com/zhumadian/ →正常登录→首页Ctrl+F5刷新→点击“敏捷应急指挥”，预期当前页面正常路由进入三维。此前已打开的旧页面可能仍持旧应用脚本，需刷新后复测。250实际地景/企业标牌仍等用户确认，冷Windows登录未重测；252正规D174十文件已预置但未在252本机执行/登记/启动，仍需当前桌面交接与其正常账号体验。不能把本轮HTTPS/静态与发现就绪当原Java正常登录和真实两机渲染已验收。

失败恢复范围保持本次固定updateId/前后SHA和新before，原恢复脚本与备份暂保；无未知归属时不恢复、不强杀。此次R51已正常成功，没有运行recover/rollback。用户明确本次不含服务器历史删除与公开Git，这两项均未执行；后续退旧须在验收与相应范围内重新核，不能因只留最新要求先删当前恢复材料。

独立D175联测在R51获批前已启动，过程中未改现用服务，并与三维D176浏览器任务分工。新44源managed worker/OriginalPlatformAccess合成CurrentUser→已资格D175十模块+953依赖→实际本机HTTP，49个不同检查标签通过（重复续期轮询不膨胀计数）。只读者能看状态不能启停、外部项目不能取grant、未知安装拒409、跨账号操作不可见404，caller PID/command body拒绝；live原归属控制器阻止更根并保配置。实际正常停止旧QA控制器后，经原QualifiedResourceSettings完整程序和2356支持文件资格才能保存新QA根，保原六相对路径，再显式启动新根。

GIS创建器是qa=True显式注入的固定合成控制器，端口随机且不是18767/18768；核心RegisteredGIS.execute/原stop、真实配置保存和HTTP处理器保持，不能据此宣称真实provider _start_owned或v2 guard/recover已验。两QA raw Data目录为空，本轮没有拷贝/核查/渲染原OSGB；两套支持资源是原2356文件只读硬链接，不是重复全GIS复制。继承测试前言仍写D172，但固定C常量、bdf6d7e1…manifest和实际十源资格均为D175，完整执行driver SHA e9159446…保留，不改已执行源码抹历史。

生命周期重点实证：首资源管理进程正常退出0时，原Job仍有GIS成员，不报告假Job0；保被跟踪的同一内核进程句柄/出生和映像，新管理进程能接管观察该已注册GIS、start只复用原进程、不重复启动，并经原正常stop结束它后，旧管理Job才真实归零。两个合成控制器同一内核句柄实得exit0，五个内层根/Job和总外层root/Job最终全0，无强杀；峰362,831,872B低3GiB。原250配置、安装清单、active字节及真实owner全程保持，新自有14图层表空，合成平台Authorization未写入QA记录。CurrentUser仍合成、无原Java/生产TLS/浏览器或252验收；不借这些检查代替未答_h七周期。

按清理SKILL核真实终态、鲜CIM零及两根4712逐SHA后，仅退两套自有支持硬链接视图，逻辑1,031,120,912B；原2356支持文件、全部raw GIS与源码及QA SQLite/配置/意图/终态/日志保持。未清共享Readonly属性（held0），盘空332136099840→332136886272B只作观察，不把1.03GB逻辑量当物理释放；已退QA支持视图不能直接重跑旧测试。

配套文档与明确本方源码同步原本地两个review分支，未改正式HEAD/index/main或held native/main.cpp，未公开push。R51只是紧急首页会话入口维护，完整UE效果效率引擎G1—G10、EXE GIS DLG分层点线面多源空间牌/Web3D两机协同/单系统天津南港完整B/S目标继续active/fullCloneReady=false，不宣称公开干净检出一键完整构建。
'''
 handbook=A/'deploy/handbook/R51实际交付与本机GIS控制隔离验证_r2430_20261112.md';handbook.parent.mkdir(parents=True,exist_ok=True)
 with handbook.open('x',encoding='utf8')as f:f.write(note)
 with(D/'R51实际部署与体验说明_r2430.md').open('x',encoding='utf8')as f:f.write(note)
 for name in('Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md'):
  with(R/name).open('a',encoding='utf8')as f:f.write('\n\n## 2026-11-12 R2430：R51实际上线首验通过，本机控制49项正常收尾\n\n'+note)
 engine=E/'docs/project/R51实际上线与本机控制HTTP验证_r2430_20261112.md'
 with engine.open('x',encoding='utf8')as f:f.write(note)
 spec=importlib.util.spec_from_file_location('r2430own_git',V/'commit_r18_local_review.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 files=[p.relative_to(A).as_posix()for root in(S,P)for p in root.rglob('*')if p.is_file()]+[handbook.relative_to(A).as_posix()]
 a=g.commit(A,'409d24440d9075a20b753a0f30ace54beb9bd81e','review/workplace-r19-live-local-20261031',sorted(files),'r2430-app','Record actual approved R51 public delivery and isolated original-authority GIS-control lifecycle validation',update_existing=True)
 e=g.commit(E,'af4c5e81f52965428e6f8bb02b3acfb74a087682','review/workplace-r19-live-progress-local-20261031',[engine.relative_to(E).as_posix()],'r2430-engine','Record delivered same-window Home and exact remaining real user two-machine acceptance',update_existing=True)
 assert sha(A/'native/main.cpp')==held
 put(D/'local-review-git-r2430.json',{'application':a,'engine':e,'publicPushed':False,'heldNativeUnchanged':True})
 print(json.dumps({'R51ActuallyDelivered':True,'externalChecks':13,'localControlDistinctChecks':49,'application':a,'engine':e,'publicPushed':False,'normal250252Accepted':False},ensure_ascii=False))
if __name__=='__main__':main()
