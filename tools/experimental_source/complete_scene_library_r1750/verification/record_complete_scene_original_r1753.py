"""Record qualified complete-scene UI, original Java restart and exact local source commits."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sqlite3
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).parent;S=A/'tools/experimental_source/complete_scene_library_r1750';D=R/'Document/Deployment/fine_browser_original_r1748_20261107'
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(raw)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
assert not(D/'local-git-completed-r1753.json').exists()
clean=J(D/'cleanup-complete-scene-r1758.json');assert clean['completed']and clean['freshSuccessfulProcessMatches']==0 and clean['allSavedSceneFilesAndDLG_SQLiteJSONWriteIntentsRetained']
first=J(R/'work/su1749/ui-restart/result.json');firstRun=J(R/'work/su1749/verified-result.json');firstHTTP=J(R/'work/su1749/ui-restart/scene-file-http-summary.json')
ui=J(R/'work/su1760/ui-restart/result.json');run=J(R/'work/su1760/verified-result.json');term=J(D/'actual-parent-terminal-r1760.json');http=J(R/'work/su1760/ui-restart/scene-file-http-summary.json')
assert not first['passed']and first['driverPhase']=='normal-unsaved-leave-cancel'and firstHTTP['successfulScenePOSTs']==1 and firstHTTP['originalDLGPosts']==0
assert firstRun['originalCodeRestored']and firstRun['originalPointerRestored']and firstRun['allActualJobsZeroBeforeClose']
assert ui['passed']and ui['readOnlyExistingSceneAfterOriginalServiceRestart']and len(ui['checks'])==34
assert run['passed']and run['originalCodeRestored']and run['originalPointerRestored']and run['allActualJobsZeroBeforeClose']and term['exitCode']==0 and term['actualOuterJobZero']
assert http['successfulScenePOSTs']==0 and http['originalDLGPosts']==0 and not http['confirmedCreateReplayed']
for rr in [firstRun,run]:
 tr=rr['actualTerminals'][0];assert tr['normalOwnedShutdown']and len(tr['componentExitCodes'])==8 and all(v==0 for v in tr['componentExitCodes'].values())
 fs=tr['spatialShutdown']['fineSourceShutdown'];assert fs['nativeExitCode']==0 and fs['actualJobZero']and fs['protectedWrites']==0
intent=J(R/'work/su1749/scene-file-write-intent.private.json');scene=R/'work/scene-files-original-r1748/cloud-scenes'/intent['name'];assert intent['confirmed']and J(scene)==intent['expected']
expected=J(R/'work/su1522/expected-document.private.json');assert J(R/'work/si1460/project-files/原SDK网页工程_r1522.json')==expected
c=sqlite3.connect((R/'work/si1460/layer-data/layers.sqlite').as_uri()+'?mode=ro',uri=True)
try:c.execute('PRAGMA query_only=ON');rows=c.execute('SELECT revision,payload FROM dlg_documents').fetchall();assert len(rows)==1 and rows[0][0]==2 and json.loads(rows[0][1])==expected
finally:c.close()
build=J(R/'Document/Deployment/scene_model_visibility_build_r1736_20261107/qualified-build-r1736.json');backend=J(R/'Document/Deployment/scene_library_original_package_r1737_20261107/actual-backend-proof-r1739.json');component=J(R/'Document/Deployment/scene_library_component_r1740_20261107/actual-component-proof-r1740.json');static=J(R/'Document/Deployment/scene_fine_auth_stage_r1743_20261107/actual-static-gateway-r1744.json')
assert build['passed']and build['nodeTests']['pass']==827 and backend['passed']and component['passed']and len(component['checks'])==9 and static['passed']and len(static['checks'])==1125
network=J(R/'work/su1760/ui-restart/fine-network-status-summary.json');near=J(R/'work/su1760/ui-restart/near-source-summary.json')
ssh=load('r1753_ssh',A/'tools/remote_publish/zhumadian_ssh_channel.py').probe();assert ssh['passed']and ssh['releaseSHA256']=='d2918cf14933b7a903368a0f88e6b2075116081cdbb847ca435b67bd01c8ea88'and not ssh['serverChanged']
proof={'schema':'xnby.complete-scene.original-host.acceptance.v1','stage':'R1753','sceneTests':build['nodeTests'],'actualMainInputs':169,'sourceInputs':266,'fiveOutputs':build['fiveOutputs'],'qualifiedBackendInputs':35,'qualifiedBackendManifestSHA256':sha(R/'work/scene-file-frontend-r1735/backend/package-manifest.json'),'backendChecks':len(backend['checks']),'crossLanguageCases':24,'actualCASProcesses':4,'CASWinners':1,'CASConflicts':3,'componentBrowserChecks':9,'actualNginxChecks':1125,'firstOriginalRunPassed':False,'firstOriginalRunCompletedChecks':len(first['checks']),'firstOriginalCompleteSceneCreateReadOpenCancelOverwriteCancelAndPageRefreshFivePassed':True,'firstOriginalRunFailure':'after save/open, old unsaved-leave test assumed a dirty model; actual model was correctly clean; failure retained','firstCreateConfirmedExactlyOnce':True,'secondOriginalRunPassed':True,'secondOriginalRunChecks':34,'secondOriginalRunReadsConfirmedSceneAfterOriginalEightServiceRestart':True,'secondOriginalRunScenePOSTs':0,'bothOriginalRunsDLGPOSTs':0,'originalExistingSyntheticNonadminJavaAccounts':2,'actualOriginalLoginAndCurrentUserUsed':True,'syntheticCurrentUserHTTPUsedInOriginalParent':False,'bothEightAndNativeNormalExit0JobsZeroBeforeCodeMetadataRestore':True,'normalUnsavedModelEditLeaveCancelAndLogoutDeniedAccountVerified':True,'newSceneFileSHA256':sha(scene),'sameSQLiteRevision2AndOriginalJSONRetained':True,'qualifiedOriginAndFineAuthorizationASTKeptDuringBackendRebase':True,'failedR1746PreflightStringPathMismatchBeforeRunAllocationAndNoPOST':True,'failedR1741ASTGuardBeforeWritingSupport':True,'componentPendingScreenshotInspected':True,'network':network,'nearSource':near,'SSHReadOnlyProbe':ssh,'softwareWebGLNotHardwarePerformanceOrUE':True,'fullBusinessRowDigestAuditPerformed':False,'newPersistentSceneJSONNotDeletedOrReplayed':True,'modelLiveSyncD130D131NotMerged':True,'actualPublicIIS_TLS252OrEXEAccepted':False,'publicUpdated':False,'publicPushed':False,'fullCloneReady':False,'remaining':['receive D130/D131 independently and merge live instance collaboration without overwriting scene files or identity retirement','actual two-author original Java scene CAS/multi-tab and denied scene-library account coverage','production storage/minimal whole GIS closure and private asset paths; actual IIS/TLS cache/range/roles, EXE-public-252','source units/original complete scene layout, all unique Nangang flows/templates and UE G1-G10','formal Windows sshd port22 takeover and reboot persistence']}
put(D/'stage-proof-r1753.json',enc(proof));snapshot=J(S/'snapshot.json');files=list(snapshot['applicationFiles'])+[(S/'snapshot.json').relative_to(A).as_posix()];efiles=[]
def app(n,raw):put(A/n,raw);files.append(n)
def engine(n,raw):put(E/n,raw);efiles.append(n)
for n in ['prepare_scene_original_readonly_restart_r1751.py','original_configuration_lifecycle_r1751.mjs','run_original_configuration_lifecycle_r1751.py','launch_original_configuration_lifecycle_r1751.py','prepare_scene_readonly_scope_r1752.py','original_configuration_lifecycle_r1752.mjs','run_original_configuration_lifecycle_r1752.py','launch_original_configuration_lifecycle_r1752.py','prepare_scene_memory_resume_r1755.py','launch_original_configuration_lifecycle_r1755.py','launch_original_configuration_lifecycle_r1757.py','receive_scene_model_protocol_d130_r1754.py','check_d130_frontend_closure_r1756.py','prepare_scene_trusted_leave_probe_r1759.py','original_configuration_lifecycle_r1760.mjs','run_original_configuration_lifecycle_r1760.py','launch_original_configuration_lifecycle_r1760.py','cleanup_complete_scene_tests_r1758.py','record_complete_scene_original_r1753.py']:
 raw=(V/n).read_bytes();raw.decode('utf8')
 if n.endswith('.py'):ast.parse(raw)
 app((S/'verification'/n).relative_to(A).as_posix(),raw)
for n,value in [('complete_scene_original_r1753.json',proof),('complete_scene_qualified_http_r1739.json',backend),('complete_scene_component_r1740.json',component),('complete_scene_original_first_failed_r1749.json',first),('complete_scene_original_readonly_restart_r1760.json',ui),('complete_scene_parent_path_fix_r1747.json',J(R/'Document/Deployment/scene_catalog_parent_r1747_20261107/path-comparison-proof-r1747.json'))]:app('deploy/verification/'+n,enc(value))
guide='''# 完整场景工程库与原系统重启联测 R1753

完整场景工程库已接入本方真实原系统宿主：新按钮保存和读取同份landscape/models/lighting，确认打开才替换当前草稿，不用断开协同来绕过原本地文件保护。文件名.scene.json；新建只允许目标不存在，覆盖须先读取旧SHA并确认，冲突保服务器赢家和本地编辑。未知提交结果保当时快照、禁重复提交，仅回读完整相同内容才确认；不同内容可下载待核对快照，账号退役清对话框与已读内容。原DLG文件库和现有即时标绘接口保留。

实际构建827检查/77文件，169真实主输入与266完整源固定，五产物逐SHA；实际静态Nginx1125项通过。完整后端不能直接套用首R1731旧基线：本轮重基已接受的原平台Origin与精细资产鉴权包，保OriginalPlatformAccess.check和scene_read_authorization AST及原project_files_api字节，原监督器和Job保持。35源包真实HTTP、24跨语言格式、四进程CAS一成功三409、替换故障和上传途中撤权均过；配置回环Origin仅精确已声明源可用。

独立真实Chrome组件9组通过：保存、读取、打开取消确认、覆盖取消、真实409、重新读取、提交已落盘但回执丢失的回读确认、读回不同内容保待核对、身份清退。该层上游/模型适配明确合成，不能替代原Java/WebGL；已另外实跑下述完整宿主。

原Java首次R1749确认创建一个整份场景文件，仅一次POST。真实模型与光照及原丰富点线面同存，取消打开保现有、确认打开恢复、取消覆盖不重发、整页刷新后重读恢复五项通过，原DLG POST零。随后旧测试仍假定模型未保存，实际新保存/打开后正确干净，于离页dirty断言失败；原失败没有改通过。此轮八组件/native均正常0、所有Job零后还原代码指针/私有配置。新R1760沿相同已保存文件和同库重启八组件，禁止重建文件；最终34项全部通过，验证正常登录后读取并恢复相同模型/光照/标绘，再刷新仍同；新建一次真实本地模型修改后离页取消保护通过，正常退出旧context清退、无权普通账号切换明确403/无成功资产通过。第二轮场景POST零、两轮DLG POST零。两轮都未创建或审批原业务任务/上传/赋权，未做全业务行摘要。

原R1746启动前因预检将scene静态行file字符串与Path直接比较误拒，尚未分配run或POST；修为严格规范路径比较，同目录接受、其他文件/route拒绝，其余函数/类AST保持。R1741保护AST定位旧类名先拒于写入前，R1738测试缺格式驱动先拒，R1734准备器字符串替换过宽先拒，均保小失败；不是放松鉴权或模型目录哈希。R1751原八启动后因浏览器驱动输出目录仍指旧轮，被精确守卫在浏览器创建前拒绝，正常八/native0恢复；新R1752提前Node正负路径检查通过。两次资源低于原15GiB门槛均未启子进程，空目录仅非递归退役，门槛前移分配之前，回升后由R1757启动器执行同一只读R1752任务，门槛未降。R1752重启恢复和再次刷新31项通过后，离页阶段未触发原生确认框并超时，保原失败/正常退出恢复；最终R1760增加测试浏览器原生鼠标点到场景专题、核sticky用户激活及模型面板可见，再从原控件建立未存编辑，原保护不变后完整34项通过。D130核收器首次pin路径重复candidate在写入前拒绝，按实际清单相对路径修正后316逐Git/后端4与前端273pin过，仅源码接收，不把对方运行测试当本方通过。

当前仅本地独立候选，原八已停止并恢复，不能把临时动态端口当长期用户入口。三维会话8803仍是其D129演示；未擅自覆盖或接入其数据。公网仍R49，未发布本阶段。后续整项上线后的用户步骤为：正常登录项目→场景编辑→布放模型/光照和标绘→完整场景工程库→输入工程名→保存；另一页同项目读取比较→确认打开。覆盖前先读取，收到冲突重新比较；结果未知先核对/下载快照，勿反复保存。首次D盘文件夹授权仅适用于本地目录功能，云场景库不要求用户搬JSON。

生产sceneProjectsRoot须稳定私有且与DLG/原工程/运行/模型目录分开，sceneModelCatalog及SHA绑定实际展示模型库。新库原子JSON/跨进程锁与完整SHA CAS，无SQL/原库DDL迁移；只存模型id/SHA引用，不写GIS/GLB字节。测试新场景/旧revision2及原工程JSON全部保留，新的库目录绝不当临时垃圾清除。完整格式与维护见配套模型说明。

软件WebGL用于真实行为测试，不是硬件FPS、全园区品质或UE对标验收。实际双作者原账号CAS/多页、D130/D131即时模型协同、原单位/南港完整布局、生产存储最小闭包/IIS TLS压缩缓存Range/真实EXE公网252仍待；当前直接GIS估计49.29GB对服务器C最近43.12GB空闲仍缺存储方案，未删业务/减地景凑空间。正式SSH服务22接管/重启持久和全部去重南港业务、UE G1—G10也未宣称完成。

源码按272项前端/支持闭包复用已封存输入，只增加九个差异源及新支持；本方现有本地Git分支保存，不改main/held native或发私有祖先。公开新增范围未推，不宣称公开干净检出一键完整构建。阶段结束按技能只清已退终态浏览器profile和逐SHA同当前的代码before，所有库/场景JSON/意图/失败/源码/GIS模型保留；无本轮服务器删除。完整目标继续active/fullCloneReady=false。
'''
put(D/'阶段结果与体验边界_r1753.md',guide.encode());app('deploy/handbook/complete_scene_original_r1753_20261107.md',guide.encode());engine('docs/project/B_S_完整场景库原登录与重启联测_r1753_20261107.md',guide.encode())
model={'schema':'xnby.complete-scene-library.persistence-model.v2','existingSQLSchemaUnchanged':True,'DDLPerformed':False,'storage':'stable private sceneProjectsRoot / valid .scene.json; complete landscape/models/lighting snapshot, atomic replace and cross-process file lock','fields':['schema','scene','landscape','models','lighting'],'formatVersions':['xnby.scene-project.v1','xnby.scene-project.v2'],'createCAS':'expectedSHA256=null, path must not exist','overwriteCAS':'exact current whole file SHA256; 409 keeps winning file','authorization':'original CurrentUser project read/write ACL and account binding, upload second check; no new database account/grant','modelAssets':'fixed id/SHA references checked against the exact displayed catalog; never upload GIS/GLB bytes in JSON','separateRoots':['sceneProjectsRoot','projectFilesRoot','dataRoot','runRoot'],'unknownCommit':'retain frozen full scene and block repeat POST; GET identical complete content confirms; different content retains pending','localVerifiedFileRoot':str(scene.parent),'productionInstalled':False,'normalOriginalEightRestartVerified':True,'retirement':'preserve all saved scene files and protected write intents independently of reconstructible code/profile cleanup'}
app('deploy/database/complete_scene_library_original_r1753.json',enc(model));put(R/'Document/Database/完整场景工程库存储与维护_r1753.json',enc(model))
app('deploy/verification/complete_scene_cleanup_r1758.json',enc(clean))
app('deploy/verification/D130_receiver_frontend_boundaries_r1756.json',enc(J(R/'Document/Deployment/d130_source_receiver_r1754_20261107/frontend-closure-and-merge-boundaries-r1756.json')))
ack={'schema':'xnby.coordination.complete-scene-library.original-ui.v1','sender':'驻马店3','recipient':'驻马店三维','stage':'R1753','state':'receiver-original-host-tested-not-peer-ack','route':'/zhumadian/api/spatial-sync/v2/project/scenes','schemas':model['formatVersions'],'clientMethods':['listSceneFiles','readSceneFile','saveSceneFile'],'fullSceneFirstCreateCount':1,'firstOriginalRunFailureRetained':True,'readOnlyOriginalRestartChecks':34,'bothOriginalRunsDLG_POSTs':0,'originalEightNativeJobsNormalZero':True,'wholeFileCASAndUnknownCommitReadback':True,'D130D131LiveModelSyncNotMerged':True,'D130Archive316Frontend273Backend4VerifiedButNotInstalled':True,'doNotOverwriteOwnCloseStateIdentityAndPrivateAssetReader':True,'exactFrontendClosure':str(S/'source-closure.json'),'publicUpdated':False,'peer8803OrWorkingSourcesChanged':False,'actualIIS_TLS252Pending':True}
put(R/'Document/Coordination/交接消息/驻马店3完整场景库原登录保存及只读重启通过_r1753_20261107.json',enc(ack));app('deploy/verification/peer_complete_scene_original_r1753.json',enc(ack))
note='R1753：整份场景库接原宿主CurrentUser/账号/原ACL，保原DLG/本地assertLocal；landscape模型光照同份SHA CAS、未知提交保快照禁重发仅GET同内容确认。827场景169主266源五产物/1125Nginx、原Origin精细鉴权重基35源/24格式/四进程1赢3冲突、真实Chrome组件9组过。R1746预检str与Path误比启动前拒，无run/POST，严格规范路径修复其他AST保。原JavaR1749新场景仅一次POST，五新保存读开取消覆盖取消/刷新恢复过，旧dirty断言在已保存干净模型失败保，八/native0恢复；R1760同文件同库只读八组件重启34项全过，场景POST0/两轮DLG POST0，再真实本地编辑离页取消/退出旧context及无权账号403零成功过。所有Job0后代码指针私有配置恢复，revision2原JSON与新scene意图保，无原业务任务上传赋权重放/全行摘要未做。272闭包和差异九源原本地Git，公开未推/公网仍R49无发布，peer8803/D130D131未动；生产最小GIS闭包/存储49.29GB对C43.12GB待答/IIS TLS EXE252、双作者真实CAS和全南港/UE G1-G10/正式SSH22持久仍待，active/fullCloneReady=false。'
marker='BS_COMPLETE_SCENE_ORIGINAL_R1753_20261107';block=('\n\n<!-- '+marker+' -->\n'+note+'\n<!-- '+marker+'_END -->\n').encode();seen=set()
for p in[R/'Document/Engine/project/htengine_goal_state.md',E/'docs/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md',E/'docs/project/当前工作断点.md',R/'Document/Engine/showcase_demo_completion.md',E/'docs/showcase_demo_completion.md']:
 st=p.stat();identity=(st.st_dev,st.st_ino)
 if identity not in seen:
  assert marker.encode()not in p.read_bytes()
  with p.open('ab')as f:f.write(block)
  seen.add(identity)
 if p.is_relative_to(E):efiles.append(p.relative_to(E).as_posix())
put(D/'local-source-files-r1753.json',enc({'application':files,'engine':efiles,'publicPushed':False}));held=sha(A/'native/main.cpp');commit=load('r1753_commit',V/'commit_r18_local_review.py')
a=commit.commit(A,'f633b448949ade91dbd1401aa38c6e838b0257bd','review/workplace-r19-live-local-20261031',files,'r1753-app','Connect whole scene file library to original identity and verify durable original-service restart; retain first-run test failures',True)
e=commit.commit(E,'6bdd77124aa2eacd02bf2cce247a28f3be0e9dd9','review/workplace-r19-live-progress-local-20261031',efiles,'r1753-engine','Record whole scene snapshot original-login and restart evidence with full UE and application goals active',True);assert sha(A/'native/main.cpp')==held
out={'application':a,'engine':e,'heldNativeUnchanged':True,'publicUpdated':False,'publicPushed':False};put(D/'local-git-completed-r1753.json',enc(out));print(json.dumps(out))
