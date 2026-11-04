"""Record the exact R47 acceptance/failures, D69 receipt and local review commits."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,importlib.util,json,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_home_supervision_r47_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
assert sha(D/'delivery-manifest.json')=='cb537fbcb1103313229869137a52538a9f08e872660cca86e27972b09ef3f27f'
full=J(R/'work/sv931/verified-exact-supervision-r931.json');browser=J(R/'work/exact-supervision-browser-r931/result.json');transport=J(D/'verified-transport-r933.json')
assert full['passed']and full['codeRestored']and full['privateConfigurationUnchanged']and full['originalCurrentPointerRestored']and browser['passed']and len(browser['cases'])==19 and transport['passed']
assert J(D/'independent-restore-r934.json')['passed']and J(D/'cleanup-r934.json')['passed']
# D69 is an independently verified review handoff, never an installation request.
messages=R/'Document/Coordination/交接消息';path=messages/'驻马店三维网关与IIS发布恢复候选_给驻马店3_20261104_d69.json';msg=J(path)
assert not msg['publicInstallRequested']and not msg['publicChanged']and not msg['sharedCanonicalIISSourceChangedBySender']
for field in ['sourceArchive','runtimeArchive']:
 p=Path(msg[field]);assert sha(p)==msg[field+'SHA256']
 if field=='runtimeArchive':
  assert p.stat().st_size==msg['runtimeArchiveBytes']
  with zipfile.ZipFile(p)as z:
   assert len(z.namelist())==len(set(z.namelist()))and set(z.namelist())==set(msg['runtimeFilePins'])
   for n,pin in msg['runtimeFilePins'].items():raw=z.read(n);assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['sha256']
for n,pin in msg['sourceFiles'].items():assert sha(A/n)==pin
assert sha(Path(msg['priorD68AckActuallyRead']['path']))==msg['priorD68AckActuallyRead']['sha256']
ack={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维','receivedAt':datetime.now(timezone.utc).isoformat(),
 'messageSHA256':sha(path),'sourceArchiveSHA256Verified':msg['sourceArchiveSHA256'],'runtimeArchiveSHA256Verified':msg['runtimeArchiveSHA256'],
 'runtimePinsIndependentlyVerified':len(msg['runtimeFilePins']),'declaredWorkingSourcePinsIndependentlyVerified':len(msg['sourceFiles']),
 'sender214ChecksIndependentlyRerun':False,'archiveCodeExecuted':False,'publicInstalled':False,'kind':'received-ingress-review-not-install-request',
 'R47CandidateNotDeployed':True,'R47CandidateManifestSHA256':sha(D/'delivery-manifest.json'),'R47KeepsExistingIISAndGatewayControlSources':True,
 'D69MustRebaselineAfterAnyR47Deployment':True,'componentJobHelperMustRemainNested':True,'invalidSyntheticAuthRoutingProbeNotEquivalentToRealAccountAcceptance':True,
 'IISAppCodeReplacementMayActivateBeforeExplicitReloadAcknowledged':True,'pending':msg['remainingBeforeInstall'],'directMessageOrAutomaticWakeupClaimed':False}
ackpath=messages/'驻马店3已读D69网关恢复候选_20261104_r935.json';assert not ackpath.exists();ackpath.write_bytes(enc(ack))
report={'schema':'xnby.r47.fixed-candidate-acceptance.v1','passedAsFixedLocalCandidate':True,'transportFiles':9,'transportBytes':27840954,'manifestSHA256':sha(D/'delivery-manifest.json'),
 'acceptedBase':'exact-public-R45-only','writes':11,'removals':0,'exactPublicUpdaterAndCoreAndProgramBytesFullOriginalLifecycle':True,
 'normalNonadminOriginalUICasesIncludingRepeatedStages':19,'nativeExistingTwoPDFRecordsAndBytesReopened':True,'newBusinessWritesAndApprovalsInFinalProbe':0,
 'allSixComponentsControllerAndActualJobNormallyExited':True,'codeConfigurationInstallationAndFourDurablePointersRestoredIndependently':True,
 'originalCodeAndCachePathsIndependentlyChecked':1427,'normalAndFourthWriteSparseFileRecovery':True,'fileRefusalCases':11,'transportRefusalCases':47,'simulatedGatewayAndIISTLSCases':22,
 'realNginxPixelAndCacheEvidenceRetainedFromR902':True,'actualPublicIISOrTLSOrNewGenerationOrLedgerUIButtonAccepted':False,
 'priorFailuresRetained':['R921 ownership query timeout and missing observed ready for pointer restore; R923 exact recovery','R925 old read-only Java output path rejected before DB connection','R930 preparer eager default KeyError before directory allocation'],
 'harnessEightTimeoutDriftChecksPassed':True,'oldAndForeignJavaOutputRejectedBeforeSecretOrDB':True,'cleanupCompleted':True,
 'freshFeedbackReadR922':{'issueCount':3,'addedRows':[],'changedDescriptionRows':[],'changedCompletionRows':[],'anonymousReadOnly':True,'completionWriteAttempted':False},
 'D69ReviewedNotInstalled':True,'R46StandaloneWillNotBeDeployedSeparately':True,'publicUploadedOrDeployed':False,'newPublicGitPushed':False,'fullCloneReady':False}
(D/'fixed-acceptance-r935.json').write_bytes(enc(report))
text='''# 固定R47：首页资源与督办PDF统一更新候选（2026-11-04）

推荐只执行本统一包，不另部署未上传的R46。九运输文件27,840,954B，delivery-manifest SHA256 cb537fbcb1103313229869137a52538a9f08e872660cca86e27972b09ef3f27f。本目录delivery即完整运输目录；FTP目的地101.201.65.94的/Zhumadian/Zhumadian_Home_Supervision_20261104_R47/；应用目标C:/inetpub/wwwroot/Zhumadian/Application。候选新release为5e3ec6c0e63f4987bc412752357ba47ea17bc0b77aa7782f13cbf7b9416c439c。

十一安装路径、零移除：四个首页文件（HTML及新CSS/WebP/WOFF2）、督办Jar、其控制helper、原六组件控制器的督办接线、冻结R46更新内核、R47更新器和两份清单。背景4854984→2591292B、字体1414784→745328B，ICC/EXIF/像素及7194完整字形保持。督办模块通过Spring标准factories发现，不追加既有初始化器属性；原业务Jar、鉴权、历史意见、原业务结构和记录、真实配置、上传、IIS/网关原控制源码、其余站点及三维源保持。候选不改数据库结构、不自动生成公网测试记录。

## 真实本地验证

R927完整R45+首页+督办组合正常登录、原任务详情刷新、原导航及两既有PDF记录/字节回读通过。R931进一步逐字采用最终R47程序、控制器、更新器及冻结内核，只适配自有G私有配置清单pin；原健康加督办就绪、普通非管理员真实原应用19断言（含重复登录/详情），两个PDF精确回看和网关10压缩/解压SHA检查通过。原接口无替身，业务创建/审批/回调重绑零；服务/控制器正常0，实际Job后代零。独立1427代码/缓存路径、私有配置/安装身份及四轮指针前像核同。只清本轮已恢复before、两已退浏览器profile和纯代码夹具，数据库、上传、模型、源码、前像journal及原日志保留，逻辑硬链接字节不冒称物理释放。

R929实际冻结内核完整预检，11路径正常替换、第四写故障恢复及11拒绝通过；R933实际21成员归档/解压、47拒绝与22模拟网关/IIS响应通过，模拟不当真实IIS/TLS。R902真实Nginx及三分辨率像素/缓存证据保持。本轮原隐患台账督办按钮UI及新生成未执行；此前同Jar在完整原应用正常用户HTTP实际生成、错误字段拒绝/一次修正、PDF下载及同库重启已验（R697/R704/R706）。不把这些不同范围混写为本次19断言包含新生成或完整台账UI。

R921归属CIM查询超时后六组件正常退出，代码已还原但指针守卫拒绝缺失就绪对象；R923按实际43964/j189就绪/回执/真实Job零及持久前像精确恢复。R925原读取类硬编码旧输出，在连接数据库前拒绝；R927只允许本轮新输出，旧/外来路径在读口令和连库前实际拒绝。R924仅测试观察器对同一存活句柄/同一指针最多三次重查原身份查询，8超时/漂移检查过，不把超时当成功，不改原身份验证或产品生命周期。R930准备器首轮默认值求值KeyError在目录分配前拒绝，修后程序字节未变。原失败与限定恢复保留。

## 发布与体验范围

重新发现服务器release/current-run/ready、进程归属、数据身份、端口、IIS和三维接口；只接受精确R45，未知差异停止。上传九文件后逐SHA核同。CheckOnly在任何停服前核完整内外层清单、原Mapper、数据身份、原11就绪及候选有界连接预算和督办工厂配置。通过后Deploy正常停启六组件，十一写零删；成功核原11加督办共12就绪、网关与本机IIS TLS的静态压缩缓存/内容SHA及外网HTTPS。失败仅本轮updateId/前后SHA/自有新备份恢复；退出归属不明停止，不强杀。原更新内核逐字保留，旧/新release分别选择其原控制器pin，恢复旧版不会误用新控制器约束。

通过后的体验入口：/zhumadian/home正常登录、刷新与八导航；应急入口原列表/本人详情；隐患台账本人有权记录的详情和已有督办文件。公网首次/再次访问、IIS编译及真实角色和台账按钮仍须上线后验，不自动写公网业务。登录/安全验证由用户处理。回读仅匹配/阶段、PID映像/预算及HTTPS摘要，不导出账号会话、令牌口令、运行UUID、业务原文或原日志。本固定范围不含腾讯回填、公开Git或本轮服务器删除；先完成实际验收，再按既有只留最新要求清理已精确确认退役文件。

Computer Use原生桌面只在用户当前交接后使用，前提示/焦点变化停止/后交还。其guidance.md明确“Do not run Windows terminal commands via UI automation directly or indirectly.”及“Do not invoke Windows terminal commands indirectly inside File Explorer or system file dialogs.”，没有可用直接服务器执行工具时，CheckOnly/Deploy/必要Recover的CMD由用户手动运行，不通过桌面绕开限制。

新读取的三维D69两归档/34运行pin和13声明工作源独立核同（实际数量以回执为准），仅接收审阅，不执行对方214测试、不安装同步组件。IIS源码替换本身可能编译/激活，不能以未reload断言无影响；新Job helper继续独立命名空间。D69接入须以R47或届时现场基线重建，不套旧j2，不混入本包。

共享表R922匿名实时只读刷新仍三条，与上一快照无增删或描述/完成变化，未回填。源码/文档仅原本地分支；新的公开Git范围仍需固定审核，不宣称公开干净检出一键完整构建。完整UE引擎、EXE GIS/DLG图层与多源空间标牌、Web3D和单系统南港B/S目标保持active/fullCloneReady=false。
'''
text=text.replace('34运行pin和13声明工作源',str(len(msg['runtimeFilePins']))+'运行pin和'+str(len(msg['sourceFiles']))+'声明工作源')
(D/'固定候选说明.md').write_text(text,encoding='utf8')
files=[]
def copy_source(src,rel):
 q=A/rel;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(src.read_bytes());files.append(rel)
names=['prepare_current_supervision_r920.py','read_feedback_refresh_r922.py','recover_supervision_pointer_r923.py','owned_ready_observation_r924.py','verify_ready_observation_r924.py','prepare_current_supervision_retry_r925.py','prepare_current_supervision_reader_r927.py','prepare_unified_home_supervision_r928.py','verify_unified_home_supervision_r929.py','prepare_exact_unified_lifecycle_r930.py','build_unified_home_supervision_delivery_r932.py','prepare_unified_transport_verifier_r933.py','verify_unified_transport_r933.py','cleanup_unified_tests_r934.ps1','record_unified_candidate_r935.py','original_public_test_base_r46.py','original_public_test_home_supervision_r47_r928.py']
for name in names:
 if name.endswith('.py'):ast.parse((V/name).read_text('utf8'))
 copy_source(V/name,'tools/'+name)
for p in (V/'supervision_exact_r931').glob('*'):
 if p.suffix in ['.py','.mjs','.java']:copy_source(p,'source-review/unified-home-supervision-r931/'+p.name)
copy_source(D/'delivery/deploy_home_supervision_r47.py','tools/deploy_home_supervision_r47.py')
records={'deploy/verification/unified_home_supervision_r935.json':enc(report),'deploy/verification/layer_sync_d69_received_r935.json':enc(ack),
 'deploy/verification/home_fixture_cleanup_r919.json':(R/'Document/Deployment/home_sparse_update_r914_20261104/cleanup-r919.json').read_bytes(),
 'deploy/verification/unified_ownership_timeout_recovery_r923.json':(R/'Document/Deployment/supervision_current_full_r920_20261104/conditional-pointer-recovery-r923.json').read_bytes(),
 'deploy/verification/unified_readiness_observer_r924.json':(V/'ready-observation-r924-result.json').read_bytes(),
 'deploy/verification/unified_home_supervision_files_r929.json':(R/'Document/Deployment/unified_home_supervision_r928_20261104/verified-files-r929.json').read_bytes(),
 'deploy/verification/unified_home_supervision_full_r931.json':(R/'work/sv931/verified-exact-supervision-r931.json').read_bytes(),
 'deploy/verification/unified_home_supervision_transport_r933.json':(D/'verified-transport-r933.json').read_bytes(),
 'deploy/verification/unified_home_supervision_cleanup_r934.json':(D/'cleanup-r934.json').read_bytes(),
 'deploy/candidates/home_supervision_r47/delivery-manifest.json':(D/'delivery-manifest.json').read_bytes(),'deploy/handbook/unified_home_supervision_r47_fixed_r935.md':text.encode('utf8')}
for rel,raw in records.items():
 q=A/rel;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);files.append(rel)
header='## 2026-11-04 R935：统一R47最终更新器/原应用19断言通过，9运输文件固定待发布\n\n'
body='R927当前R45+新首页+工厂督办组合通过；R931逐字最终R47程序/控制器/更新器及冻结R46内核，仅自有私有manifest pin适配，真实普通用户原任务详情刷新/八导航/两既有PDF字节共19含重复断言、原健康+督办、网关10过；非本轮台账按钮/新生成验收。六组件及控制器0/实际Job零；独立1427代码缓存路径、配置安装和四指针前像核同，清四before/两退profile/纯代码夹具，保数据库上传/模型/全部日志journal。R921超时/指针守卫拒绝由R923精确恢复；R925旧只读class路径连接前拒绝，R927新路径两负例过；R924仅同存活句柄/同指针重查原验证8项，不弱化原身份或重启猜测。R930准备默认值KeyError连接前失败保留。R929冻结内核11写零删/正常及第四写恢复11拒绝，R933实际21成员/47拒绝/22模拟响应过；模拟非IIS。统一R47九文件27840954B/清单cb537fbc，推荐替代未执行R46，不另部署；公网仍最后已核R45，未上传/新公开Git/腾讯回填。R922表仍3条无变化。D69两归档及全部声明源码/pin核同、自身回执写出，214未重跑/不安装；IIS自动编译与独立Job命名空间要求保留，需按未来R47现场重基线。下一桌面交接/固定范围发布并公网验；仍缺原台账按钮、真实模板角色/全系统签收。完整长期目标active/fullCloneReady=false。\n\n'
rel='docs/project/统一首页督办候选验收_20261104_r935.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md']:p.write_bytes((header+body).encode('utf8')+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
s=importlib.util.spec_from_file_location('local_r935',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
a=h.commit(A,'89d10136660b1b125a7bfadb23203b3225c0bb79','review/workplace-r19-live-local-20261031',files,'app-r935',message_override='test: verify exact unified home and supervision updater, preserve failures and D69 review',update_existing=True)
e=h.commit(E,'669d47d021501094e4ce6fa05d3aa587621d2ce7','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md'],'engine-r935',message_override='docs: record unified R47 acceptance and retained full project scope',update_existing=True)
(D/'local-review-git-r935.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False}));print(json.dumps({'recorded':True,'application':a,'engine':e,'D69RuntimePins':len(msg['runtimeFilePins']),'D69SourcePins':len(msg['sourceFiles']),'publicChanged':False}))
