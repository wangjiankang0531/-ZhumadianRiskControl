"""Close the real diagnosis; retain the unstarted transaction candidate and data."""
from pathlib import Path
import ast,copy,hashlib,json,os,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/hazard_attachment_original_r1207_20261106';P=R/'work/hazard-attachment-probe-r1207';Z=R/'work/ha1207'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return{'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_bytes(v if isinstance(v,bytes)else v.encode('utf8'))
assert not(D/'stage-summary-r1216.json').exists()
runtime=j(Z/'verified-hazard-runtime-r1207.json');outer=j(D/'parent-terminal-r1208.json');main=j(P/'ui-mainflow/result.json');reopen=j(P/'ui-reopen/result.json')
assert runtime['passed']and runtime['failure']is None and runtime['codeRestored']and runtime['originalCurrentPointerRestored']and runtime['privateConfigurationUnchanged']
assert outer['exitCode']==0 and outer['actualJobDescendantsZero']and outer['callbackJournalUnchanged']
assert len(runtime['terminals'])==2 and all(x['controllerExitCode']==0 and x['normalOwnedShutdown']and x['actualJobDescendantsZero']and all(v==0 for v in x['exitCodes'].values())for x in runtime['terminals'])
assert main['passed']and reopen['passed']and len(main['cases'])==7 and len(reopen['cases'])==2
assert main['writeCounts']=={'upload':1,'create':1,'failedEdit':1}and all(x==0 for x in reopen['writeCounts'].values())
assert main['writeResponses'][1]['status']==500 and main['writeResponses'][1]['businessCode']==100000
assert len(main['attachmentBefore'])==1 and main['attachmentCountAfter']==reopen['attachmentCountAfter']==0
assert main['attachmentAtomicityPreserved']is False and reopen['attachmentAtomicityPreserved']is False
assert all(x['attachmentAtomicityDefectObserved']and x['allPreExistingHazardAndBaseFileRowsFingerprintUnchanged']for x in runtime['businessChecks'])
for folder in [P/'ui-mainflow',P/'ui-reopen']:assert j(folder/'terminal.json')['chromeExitCode']==0
flight=P/'hazard-attachment-flight.private.json';f=j(flight);flightPin=pin(flight);assert f['phase']=='mainflow-completed'and f['ownId']==main['ownRecordId']==reopen['ownRecordId']and f['requests']==main['writeCounts']
plan=j(D/'full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for key in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
 for n,b in plan[key].items():rows[n]={'before':b}
for n,row in rows.items():assert pin(G/n)==row['before'],'RESTORED_CODE_DRIFT:'+n
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert j(Z/'code-transaction/journal.json')['phase']=='restored';snapshot=j(Z/'pointer-snapshot/snapshot.private.json');assert snapshot['phase']=='restored'and pin(G/'UserData/OriginalServer/current-run.json')==snapshot['before']
callback=R/'work/original-manager-full-lifecycle-r609/attachment-r1072/resume-r1095/normal-restart/callback-normal-restart-journal.private.properties';assert sha(callback)=='b876d9aeb58fedcfeb1d17e5a718a4c9bc1f5d3c6826f06b00ea020ef3687c58'
candidateD=R/'Document/Deployment/hazard_attachment_transaction_r1214_20261106';candidateH=V/'hazard_transaction_r1214';candidatePlan=j(candidateD/'full-source-and-restore-plan.private.json')
assert not(R/'work/ht1214').exists()and not(R/'work/hazard-transaction-probe-r1214').exists()and not(candidateD/'parent-r1215.private.log').exists()
assert j(R/'Document/Deployment/hazard_attachment_transaction_r1212_20261106/parent-terminal-r1213.json')['actualJobDescendantsZero']
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { $c=($_.CommandLine -replace '\\\\','/').ToLowerInvariant(); $c.Contains('d:/project/zhumadian/_g/application') -or $c.Contains('run_hazard_runtime_r1207.py') -or $c.Contains('hazard_attachment_browser_r1207.mjs') -or $c.Contains('hazard_transaction_browser_r1212.mjs') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0','SUCCESSFUL_FRESH_PROCESS_QUERY_REQUIRED'
targets=[Z/'code-transaction/before',P/'classes',V/'hazard_attachment_r1207/compile-check',P/'ui-mainflow/profile',P/'ui-reopen/profile',V/'hazard_transaction_r1212/compile-check'];entries=[]
for root in targets:
 assert root.resolve(strict=True)==root.absolute()and(root.is_relative_to(R/'work')or root.is_relative_to(V))and root not in [R/'work',V]
 count=size=0
 for folder,dirs,names in os.walk(root,followlinks=False):
  for q in [Path(folder),*[Path(folder)/n for n in dirs+names]]:assert not q.lstat().st_file_attributes&0x400
  for name in names:count+=1;size+=(Path(folder)/name).stat().st_size
 entries.append({'path':str(root),'files':count,'logicalBytes':size})
free=shutil.disk_usage(R).free
for root in targets:shutil.rmtree(root)
assert all(not q.exists()for q in targets)and pin(flight)==flightPin
for n,row in rows.items():assert pin(G/n)==row['before']
classPath='payload/business/legacy-classes/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class'
assert sha(Path(candidatePlan['sources'][classPath]['source']))==candidatePlan['sources'][classPath]['sha256']
cleanup={'completed':True,'exactPaths':entries,'files':sum(x['files']for x in entries),'logicalBytes':sum(x['logicalBytes']for x in entries),'freeBefore':free,'freeAfter':shutil.disk_usage(R).free,'freeDeltaNotExclusiveAttribution':True,'allDataUploadsSourceLogsAndLatestCompiledCandidateRetained':True,'privateOriginalAndResumeFlightsRetained':True,'oldOriginalAttemptNotDirectlyReplayable':True,'publicFTPAndIISOrPeerPreviewCleanup':False}
summary={'schema':'xnby.hazard-original-attachment-failure-diagnosis.v1','diagnosisCompleted':True,'actualOriginalFullFrontendMyFormAndSDK':True,'actualOrdinaryNonadminLoginAndUI':True,'UIPhasesIncludingRestartRepetition':9,'ownNewHazardCreate':1,'ownPNGUpload':1,'ownOverlengthStatusEdit':1,'originalEditReturnedHTTP500':True,'originalMainRowUnchangedByFailedEdit':True,'attachmentAssociationsBefore':1,'attachmentAssociationsAfterFailedEdit':0,'attachmentLossPersistsAcrossNormalRestart':True,'uploadedObjectRemainedReadableDuringMainflow':True,'allPreExistingHazardAndBaseFileFingerprintsUnchanged':True,'ownMainRowAndAttachmentFingerprintsStableAcrossRestart':True,'metadataReprepared':False,'normalSixComponentLifecycles':2,'allComponentsControllersAndActualJobsNormalZero':True,'restoredCodePaths':len(rows),'privateConfigurationInstallationAndCurrentPointerRestored':True,'oldTaskCallbackUnchanged':True,'candidateOnlyTwoServiceMethodsChanged':True,'candidateCompiledAgainstOriginalArchive':True,'candidateClassSHA256':candidatePlan['sources'][classPath]['sha256'],'candidateFirstAttemptRefusedBeforeBackupForMissingSourceFields':True,'candidateSecondAttemptRefusedBeforeAllocationByUnchangedMemoryGate':True,'candidateActualLifecycleOrFixAccepted':False,'latestCandidatePrepared':True,'noNewCreateInCandidateResume':True,'publicOrFormal18891Or8767Changed':False,'publicGitPushed':False,'wholeTaskOrNangangAccepted':False}
verify=A/'deploy/verification/hazard_attachment_r1216';paths=[]
def review_ui(value):
 out=copy.deepcopy(value)
 for key in ['ownRecordId','attachmentBefore','attachmentAfter']:out.pop(key,None)
 out['reviewCopyIsSanitizedProjection']=True;out['rawOriginalRetainedOutsideGit']=True;return out
for name,value in [('stage-summary-r1216.json',summary),('cleanup-result-r1216.json',cleanup),('original-mainflow-review-r1207.json',review_ui(main)),('original-restart-review-r1207.json',review_ui(reopen)),('original-runtime-r1207.json',runtime),('outer-terminal-r1208.json',outer),('uploaded-png-proof-r1207.json',j(P/'ui-mainflow/verified-png.json')),('candidate-source-compile-r1211.json',j(R/'Document/Deployment/hazard_attachment_transaction_r1210_20261106/candidate-source-compile.json')),('preallocation-refusal-r1213.json',j(candidateD/'previous-preallocation-refusal.json')),('peer-D97-source-receipt-r1209.json',j(V/'receiver-d97-source-check-r1209.json'))]:
 write(D/name,enc(value));dst=verify/name;write(dst,enc(value));paths.append(dst)
for tag in ['hazard_attachment_r1207','hazard_transaction_r1212','hazard_transaction_r1214']:
 h=V/tag;pinName='source-pins-'+tag.rsplit('_',1)[1]+'.json';pins=j(h/pinName)['files']
 for src in sorted(p for p in h.iterdir()if p.is_file()):
  if str(src)in pins:assert sha(src)==pins[str(src)]
  if src.suffix=='.py':ast.parse(src.read_text('utf8'))
  dst=A/'tools/verification/hazard_attachment_r1216'/tag/src.name;write(dst,src.read_bytes());assert sha(dst)==sha(src);paths.append(dst)
for name in ['prepare_hazard_attachment_diagnosis_r1207.py','hazard_attachment_probe_r1207.py','hazard_attachment_observer_r1207.jsfrag','hazard_attachment_main_r1207.jsfrag','launch_hazard_attachment_r1208.py','review_peer_browser_d97_r1209.py','prepare_hazard_transaction_source_r1210.py','verify_compiled_hazard_transaction_r1211.py','prepare_hazard_transaction_runtime_r1212.py','derive_hazard_transaction_observer_r1212.py','hazard_transaction_main_r1212.jsfrag','hazard_transaction_observer_r1212.jsfrag','launch_hazard_transaction_r1213.py','prepare_hazard_transaction_sourcepin_r1214.py','launch_hazard_transaction_r1215.py','close_hazard_attachment_diagnosis_r1216.py']:
 src=V/name
 if src.suffix=='.py':ast.parse(src.read_text('utf8'))
 dst=A/'tools/verification/hazard_attachment_r1216'/name;write(dst,src.read_bytes());paths.append(dst)
service=A/'source-review/hazard-source-attachment-transaction-r1210/src/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.java';paths.append(service)
text='''# 危险源附件保存失败诊断及事务候选 R1216

原完整安全前端、原MyForm/上传控件、原鉴权和原后端在G合成环境普通E实际执行：新建一条自有危险源、一次PNG上传并形成一条base_file关联，实际GET读回上传字节。编辑页只在草稿移除附件，再填原status varchar(4)不能容纳的12345并提交一次，原HTTP500/code100000失败；候选前端保留输入，但原后台先删附件、后更新主记录且无事务，导致主记录仍旧值、关联已丢。原详情和独立只读SQL一致，正常六组件重启后仍丢；7主阶段+2重启阶段，不是9个独立模块，也不算修复验收。源文件对象在首轮失败后仍可读取，重启轮只核主记录/关联，没有声称重启后再次读对象。

所有先存危险源/base_file行排除精确本轮唯一新记录的整表摘要保持；旧任务b876回调、身份角色授权字典保持，11元数据仅verify。两轮控制器/六组件/Chrome正常0、真实Job后代零，1422原代码路径和私有配置/安装/current-run恢复，不改正式18891/8767、用户预览或公网。私有flight在work/hazard-attachment-probe-r1207/hazard-attachment-flight.private.json，mainflow-completed；禁止重建或重放upload/create/failedEdit。本条保留活记录及原上传对象供后续修正，数据未回滚。

最小服务候选只改save(HazardSourceVo)与updateById(HazardSourceVo)：两者rollbackFor=Exception事务，主表insert/update精确成功才处理关联；update false在所有附件写前返回。Reference/原Jar/表结构/权限不变。候选Java17 class已与原归档依赖编译，两个运行时事务注解核实。首次javap用UTF8读取Windows默认编码失败，编译本身已成功；仅显式Java UTF8重新读取，未重复编译或写业务。该候选尚未通过实际Spring生命周期、附件插入阶段故障回滚及通知提交后语义验收，不能把编译或源码注解当运行验收。

R1212首次尝试在CodeTransaction构造时因3条mutation漏source字段拒绝，备份/代码/服务/UI前退出，仅产生marker；真实Job零且每条原代码pin同。保失败，R1214仅补显式source，class/前端相同。固定续接同一个新记录、零create、最多一次新PNG/修复编辑/保附件失败/正常纠正重试/移除草稿失败。R1215在9GiB物理及commit门槛拒绝，未分配父进程、工作目录或parent log，不能说候选运行失败或已启动等待。不得降低门槛或关另一会话窗口；资源满足后核scope/源/current基线，再执行同一尚未分配的R1215入口，不重跑旧R1207/R1213。

按清理SKILL鲜查CIM零、正常终态和恢复SHA后，仅清本轮已恢复before、自有class检查与Chrome profiles，保全部业务/上传/GIS/DLG、最新候选class/dist/计划/私有flight/所有源码和失败日志。原attempt因此不可直接重放。服务器FTP/IIS未清：尚无正常后台通道，固定R48第三稿未上传；沿六任务整项集中发布，不为这份诊断单独更新公网。

D97草稿恢复交接ZIP/SHA/CRC与8个实际Git Blob已独立核收；未重跑其浏览器/RTX测试、未安装合成登录/预览、不代表正常账号宿主/V2/IIS/TLS252接通。源码回执是共享文件，不是实时消息。SSH最后用户前台22222可监听，服务1067原因待服务文件日志，认证仍未过；未再次尝试公网主机或重复安装/启动脚本。完整UE引擎/驻马店GIS DLG多源空间标牌/Web3D及单系统南港目标继续。
'''
handbook=A/'deploy/handbook/hazard_attachment_diagnosis_r1216_20261106.md';write(handbook,text);paths.append(handbook)
progress=E/'docs/project/B_S危险源附件失败与事务候选_r1216_20261106.md';write(progress,text)
marker='BS_HAZARD_ATTACHMENT_FAILURE_REPRODUCED_R1216_20261106'
entry='\n\n<!-- '+marker+' -->\nR1216：原普通E/MyForm/上传/SDK实际新建1危险源+1PNG+1超长status失败，主行保持但关联1→0，原详情/只读SQL及正常重启同；9阶段含重复、是缺陷诊断非修复通过。既有业务摘要/元数据/b876保持；两六组件/控制器/Chrome正常0/Job零、1422代码/配置安装指针复原，精确清已恢复before/class/profile，保活测试记录/上传/flight/源失败/最新候选。只改原save/update两方法的事务+主表先确认候选class已编译；javap编码观察失败保留后显式UTF8核，未重复编译。R1213漏source预分配拒绝后仅补三路径同字节；R1215因9GiB资源门槛未分配/未启动/零业务，待资源满足后续同一新记录，禁重建/重放旧flight。D97 8Blob独立源码接收、未装/未复跑/非实时；正常账号宿主与TLS252仍待。SSH服务文件日志待用户、认证未过；R48第三稿保持未上传，无正式18891/8767/公网/新公开Git，六任务整项发布；完整UE效果效率/EXE条件退役/驻马店GIS DLG多源标牌/Web3D/单系统南港active/fullCloneReady=false。\n<!-- '+marker+'_END -->\n'
for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/showcase_demo_completion.md']:
 assert marker not in p.read_text('utf8')
 with p.open('a',encoding='utf8')as out:out.write(entry)
ack=R/'Document/Coordination/交接消息/驻马店3已核D97草稿恢复源码_r1216_20261106.json';write(ack,enc({'from':'驻马店3','to':'驻马店三维','receiverSourceReviewComplete':True,'D97ActualGitBlobsMatched':8,'senderCommit':'1b7c1eb1cdeb4b764bf86036bf7ba76ed088c93f','proof':str(D/'peer-D97-source-receipt-r1209.json'),'senderRuntimeBrowserOrPerformanceTestsIndependentlyReplayed':False,'peerPreviewsOrUserDataTouched':False,'publicOrUserNativeInstalled':False,'normalAccountHostAndTLS252StillPending':True,'sharedFileNotRealtimeCommunication':True}))
scope={'application':[p.relative_to(A).as_posix()for p in paths],'engine':[progress.relative_to(E).as_posix(),'docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md']};write(D/'local-source-files-r1216.json',enc(scope))
print(json.dumps({'recorded':True,'realOriginalAttachmentDefectConfirmed':True,'UIPhases':9,'originalLifecycles':2,'candidateActualRuntimeStarted':False,'cleanupFiles':cleanup['files'],'cleanupLogicalBytes':cleanup['logicalBytes'],'localSourcePaths':len(paths),'publicChanged':False}))
