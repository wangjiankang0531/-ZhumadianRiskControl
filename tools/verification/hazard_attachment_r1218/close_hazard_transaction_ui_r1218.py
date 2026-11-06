"""Close scoped original UI failure/retry/restart; do not claim late-insert fault coverage."""
from pathlib import Path
import ast,copy,hashlib,json,os,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/hazard_attachment_transaction_r1214_20261106';P=R/'work/hazard-transaction-probe-r1214';Z=R/'work/ht1214';H=V/'hazard_transaction_r1214'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return{'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_bytes(v if isinstance(v,bytes)else v.encode('utf8'))
assert not(D/'stage-summary-r1218.json').exists()
runtime=j(Z/'verified-hazard-runtime-r1214.json');outer=j(D/'parent-terminal-r1215.json');main=j(P/'ui-mainflow/result.json');reopen=j(P/'ui-reopen/result.json')
assert runtime['passed']and runtime['failure']is None and runtime['codeRestored']and runtime['privateConfigurationUnchanged']and runtime['originalCurrentPointerRestored']
assert outer['exitCode']==0 and outer['actualJobDescendantsZero']and outer['callbackJournalUnchanged']
assert len(runtime['terminals'])==2 and all(x['controllerExitCode']==0 and x['normalOwnedShutdown']and x['actualJobDescendantsZero']and all(v==0 for v in x['exitCodes'].values())for x in runtime['terminals'])
assert main['passed']and reopen['passed']and len(main['cases'])==7 and len(reopen['cases'])==3
assert main['writeCounts']=={'upload':1,'repair':1,'failedKeep':1,'retry':1,'failedRemove':1}and not any(reopen['writeCounts'].values())
assert [x['kind']for x in main['writeResponses']]==['repair','failedKeep','retry','failedRemove']and all(x.get('status')==500 for x in main['writeResponses']if x.get('failed'))
assert main['normalRetryAccepted']and main['attachmentAtomicityPreserved']and reopen['attachmentAtomicityPreserved']
assert len(main['attachmentBefore'])==len(main['attachmentAfter'])==len(reopen['attachmentAfter'])==1
assert main['attachmentAfter'][0]['id']==reopen['attachmentAfter'][0]['id']
assert all(x['allPreExistingHazardAndBaseFileRowsFingerprintUnchanged']and x['attachmentRelationRetainedAfterFailedEdit']for x in runtime['businessChecks'])
for folder in [P/'ui-mainflow',P/'ui-reopen']:assert j(folder/'terminal.json')['chromeExitCode']==0
flight=P/'hazard-attachment-flight.private.json';f=j(flight);flightPin=pin(flight);assert f['phase']=='mainflow-completed'and f['ownId']==main['ownRecordId']==reopen['ownRecordId']and f['requests']==main['writeCounts']
oldFlight=R/'work/hazard-attachment-probe-r1207/hazard-attachment-flight.private.json';oldPin=pin(oldFlight);assert j(oldFlight)['ownId']==f['ownId']and j(oldFlight)['requests']=={'upload':1,'create':1,'failedEdit':1}
plan=j(D/'full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for key in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
 for name,b in plan[key].items():rows[name]={'before':b}
for name,row in rows.items():assert pin(G/name)==row['before'],'RESTORED_CODE_DRIFT:'+name
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert j(Z/'code-transaction/journal.json')['phase']=='restored';snapshot=j(Z/'pointer-snapshot/snapshot.private.json');assert snapshot['phase']=='restored'and pin(G/'UserData/OriginalServer/current-run.json')==snapshot['before']
callback=R/'work/original-manager-full-lifecycle-r609/attachment-r1072/resume-r1095/normal-restart/callback-normal-restart-journal.private.properties';assert sha(callback)=='b876d9aeb58fedcfeb1d17e5a718a4c9bc1f5d3c6826f06b00ea020ef3687c58'
for path,digest in j(H/'source-pins-r1214.json')['files'].items():assert sha(Path(path))==digest
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { $c=($_.CommandLine -replace '\\\\','/').ToLowerInvariant(); $c.Contains('d:/project/zhumadian/_g/application') -or $c.Contains('run_hazard_runtime_r1214.py') -or $c.Contains('hazard_transaction_browser_r1214.mjs') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0','SUCCESSFUL_FRESH_OWN_PROCESS_QUERY_ZERO_REQUIRED'
targets=[Z/'code-transaction/before',P/'classes',P/'ui-mainflow/profile',P/'ui-reopen/profile'];entries=[]
for root in targets:
 assert root.resolve(strict=True)==root.absolute()and root.is_relative_to(R/'work')and root!=R/'work'
 count=size=0
 for folder,dirs,names in os.walk(root,followlinks=False):
  for q in [Path(folder),*[Path(folder)/n for n in dirs+names]]:assert not q.lstat().st_file_attributes&0x400
  for name in names:count+=1;size+=(Path(folder)/name).stat().st_size
 entries.append({'path':str(root),'files':count,'logicalBytes':size})
free=shutil.disk_usage(R).free
for root in targets:shutil.rmtree(root)
assert all(not p.exists()for p in targets)and pin(flight)==flightPin and pin(oldFlight)==oldPin
className='payload/business/legacy-classes/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class';assert not(G/className).exists()and sha(Path(plan['sources'][className]['source']))==plan['sources'][className]['sha256']
cleanup={'completed':True,'exactPaths':entries,'files':sum(x['files']for x in entries),'logicalBytes':sum(x['logicalBytes']for x in entries),'freeBefore':free,'freeAfter':shutil.disk_usage(R).free,'freeDeltaNotExclusiveAttribution':True,'allDataUploadsSourcesFailureEvidenceCandidateClassAndDistRetained':True,'bothCompletedBusinessFlightsRetainedNeverReplay':True,'oldRuntimeAttemptNotDirectlyReplayable':True,'publicOrPeerPreviewCleanup':False}
summary={'schema':'xnby.hazard-attachment-main-update-failure-ui-accepted.v1','scopedCandidateAccepted':True,'actualOriginalFullFrontendMyFormAndSDK':True,'sameExistingOwnDiagnosticRecord':True,'newHazardCreates':0,'ownPNGUploads':1,'normalRepairEdits':1,'normalCorrectionsAndRetries':1,'failedEditsKeepingAndRemovingDraftAttachment':2,'bothFailuresHTTP500':True,'bothFailuresKeepUnsavedInputAndOriginalRelation':True,'normalOpenerReadsSameOriginalSessionWithoutTokenRead':True,'finalFailedRemovalPreservesExactAttachmentIdVerifiedBySQL':True,'allPreExistingHazardAndBaseFileFingerprintsUnchanged':True,'sameOwnRowAndAttachmentFingerprintAfterNormalRestart':True,'actualPNGBytesEqualBeforeAndAfterRestart':True,'UIPhasesIncludingRestartRepetition':10,'mainflowPhases':7,'normalRestartPhases':3,'normalSixComponentLifecycles':2,'allControllersComponentsAndActualJobsNormalZero':True,'restoredCodePaths':len(rows),'privateConfigurationInstallationAndRunPointerRestored':True,'originalBusinessJarAndSchemaUnchanged':True,'candidateClassSHA256':plan['sources'][className]['sha256'],'originalTaskCallbackUnchanged':True,'firstMissingSourceAndMemoryRefusalsRetained':True,'attachmentInsertStageFailureRollbackAccepted':False,'falseUpdateWithNonemptyAttachmentAndNotificationAfterCommitAccepted':False,'publicOrFormal18891Or8767Changed':False,'publicGitPushed':False,'wholeTaskOrNangangAccepted':False}
verify=A/'deploy/verification/hazard_attachment_r1218';paths=[]
def review_ui(value):
 out=copy.deepcopy(value)
 for key in ['ownRecordId','attachmentBefore','attachmentAfter']:out.pop(key,None)
 out['reviewCopyIsSanitizedProjection']=True;out['rawOriginalRetainedOutsideGit']=True;return out
for name,value in [('stage-summary-r1218.json',summary),('cleanup-result-r1218.json',cleanup),('candidate-mainflow-review-r1214.json',review_ui(main)),('candidate-restart-review-r1214.json',review_ui(reopen)),('candidate-runtime-r1214.json',runtime),('outer-terminal-r1215.json',outer),('png-mainflow-proof-r1214.json',j(P/'ui-mainflow/verified-png.json')),('png-restart-proof-r1214.json',j(P/'ui-reopen/verified-png.json'))]:
 write(D/name,enc(value));dst=verify/name;write(dst,enc(value));paths.append(dst)
dst=A/'tools/verification/hazard_attachment_r1218/close_hazard_transaction_ui_r1218.py';write(dst,Path(__file__).read_bytes());paths.append(dst)
archive=A/'tools/verification/hazard_attachment_r1216/hazard_transaction_r1214';sourceClosure=[]
for p in H.iterdir():
 if p.is_file()and str(p)in j(H/'source-pins-r1214.json')['files']:
  q=archive/p.name;assert q.is_file()and sha(q)==sha(p);sourceClosure.append({'path':q.relative_to(A).as_posix(),'sha256':sha(q)})
closure={'passed':True,'actualFrozenExecutableInputsMatchArchivedBytes':True,'files':sourceClosure,'runtimeGeneratedProofSeparatelyArchived':True,'publicCleanCheckoutOneClickBuildClaimed':False};write(D/'source-closure-r1218.json',enc(closure));dst=verify/'source-closure-r1218.json';write(dst,enc(closure));paths.append(dst)
text='''# 危险源附件失败保留与正常重试 R1218

同一条R1207新自有危险源续接，零新建。完整原前端/原MyForm/字典/鉴权及原业务Jar，仅替换独立编译的HazardSourceServiceImpl候选class。普通E正常原登录，在原编辑页上传一个PNG并正常修复关联；保留附件但填超长状态，原SQL500失败且保留输入；通过正常window.open浏览器继承会话的第二页面读原详情，确认原关联ID未重建/删除，不读取或复制令牌。回原同一表单改合法状态并只重试一次成功。随后再开编辑，草稿移除附件并填超长状态，第二次原SQL500失败；保输入与未提交草稿，取消后原详情和独立只读SQL确认上一合法主行及精确附件ID仍在。正常六组件重启同一条记录/附件摘要保持，上传PNG在两轮都逐字读回。7首轮+3重启阶段，不是10个独立模块，也不是完整南港验收。

两正常更新、两实际失败、一次PNG上传，重启写0；R1207创建/上传/失败没有重放。除精确本条新记录外，所有先存hazard_source/base_file摘要保持，旧任务b876不变；11元数据仅核验。两六组件/控制器/Chrome正常0、所有真实Job零，1423代码路径（含新增class恢复为不存在）、原私有配置/安装/current-run全部恢复；保新业务和上传，不用旧数据备份覆盖。两私有flight均mainflow-completed，后续不得重建或重放；当前数据保留状态2/Own material v2及一条关联供只读回看。

候选save/update的事务注解、更新主行成功后再处理附件，已证明在本轮主表SQL失败和正常纠正重试中保护关联；这不等于已覆盖后续附件INSERT异常的实际事务回滚、非空附件false更新、通知提交后触发或所有并发边界。下一项补后续附件SQL故障和false分支，不拿源码注解或当前正常/主表失败链替代这些验收。原业务Jar/数据库DDL/权限/原上传服务不改，Reference不改；公网仍没有安装该候选。

保留原R1213缺source停在代码备份/服务前拒绝与R1215首次资源门槛拒绝：补三源路径不改class；资源回升到原9GiB门槛以上后，同一未分配R1215入口才实际运行一次。没有降低门槛、强杀或关用户/三维窗口。按清理SKILL鲜查CIM零及SHA恢复，仅清本次4个已恢复before/class/profile目录，保全部数据、两个flight、源/失败/小证明、最新候选class/dist。原attempt不可直接重放。冻结实际运行源逐字匹配R1216归档，不把后来生成的证明当执行输入。

R1216记录的是启动前历史快照，本说明以实际最终结果续接，并保留其当时尚未启动状态。D97仅源码接收、正常账号宿主和TLS252仍待。SSH文件日志仍待服务器结果，真实后台认证尚未通；固定R48第三稿未上传，按六任务完成整项后集中评估公网版本，不为单个补丁频繁更新。正式18891/8767、三维预览、IIS/FTP和其他站点未改。完整UE引擎及驻马店GIS DLG多源空间标牌/Web3D/单系统南港目标继续。
'''
handbook=A/'deploy/handbook/hazard_attachment_failure_retry_r1218_20261106.md';write(handbook,text);paths.append(handbook)
progress=E/'docs/project/B_S危险源附件失败保留与重试_r1218_20261106.md';write(progress,text)
marker='BS_HAZARD_ATTACHMENT_FAILURE_RETRY_UI_ACCEPTED_R1218_20261106'
entry='\n\n<!-- '+marker+' -->\nR1218：同R1207新自有记录零create，候选原普通UI新增1PNG修复关联，保附件超长SQL500保输入/原关联ID，正常opener同会话读回不读token；原表单纠正重试成功，再草稿删附件超长SQL500仍保主行和精确关联，SQL/正常重启/两轮PNG字节同。7+3=10阶段含重复、只主表失败链验收，附件后续INSERT故障/非空false/通知提交后及全南港待，不能当全事务覆盖。既有业务摘要/11元数据/b876保持；两六组件/控制器/Chrome正常0/Job零，1423代码配置安装指针复原，精确清四before/class/profile，保数据上传双flight/源码失败/最新class dist。R1213漏源/R1215分配前资源拒绝保，门槛未降，内存回升后原未分配入口实际只启一次；冻结源逐字归档闭合。R1216启动前快照由此续接而非覆写。SSH文件日志待服务器、认证未通，D97源码接收非安装/实时通知；R48第三稿保持未上传，无正式18891/8767/公网/新公开Git，六任务整项集中发布；完整UE效果效率/EXE条件退役/驻马店GIS DLG多源标牌/Web3D/单系统南港active/fullCloneReady=false。\n<!-- '+marker+'_END -->\n'
for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/showcase_demo_completion.md']:
 assert marker not in p.read_text('utf8')
 with p.open('a',encoding='utf8')as out:out.write(entry)
scope={'application':[p.relative_to(A).as_posix()for p in paths],'engine':[progress.relative_to(E).as_posix(),'docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md']};write(D/'local-source-files-r1218.json',enc(scope))
print(json.dumps({'recorded':True,'actualScopedCandidateUIAndRestartAccepted':True,'UIPhases':10,'lateAttachmentInsertFailureAccepted':False,'sameRecordNewCreates':0,'cleanupFiles':cleanup['files'],'cleanupLogicalBytes':cleanup['logicalBytes'],'publicChanged':False}))
