from pathlib import Path
import datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_unified_r24_20261101';M=R/'Document/Deployment/material_import_full_controller_r128_20261101';M.mkdir(exist_ok=True)
J=lambda p:json.loads(p.read_bytes())
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
now=datetime.datetime.now().astimezone().isoformat();wire=J(D/'public-retained-gateway-verification.json');assert wire['allPassed']and wire['totalStaticFilesVerified']==1174
for stage in ['preflight','deployment']:assert J(D/f'server-{stage}-summary.json')['passed']
C=R/'work/event_delivery_consistency_20261030/full-controller-r128'
for attempt in ['r5','r6','r7']:
 p=J(C/attempt/'result.json');assert p['allPassed']and p['allSixComponentsNormallyExitedZero']and p['original398DefinitionsUnchanged']
b=J(C/'r7/material-browser/result.json');assert b['passed']and len(b['cases'])==9
material={'schema':'xnby.r128.material.import.scoped-acceptance.v1','at':now,'originalDefectActuallyReproduced':True,'originalFailed3001RowsPersisted':3000,
 'candidateFailed3001RowsPersisted':0,'old3000SyntheticRowsPreserved':True,'normalOriginalRoleBrowserCases':b['cases'],
 'threeActualWholeSixComponentLifecycleRunsPassed':True,'allTenReadinessReportsPassed':True,'original398DefinitionsUnchanged':True,
 'allStartedProcessesNormallyExitedZero':True,'testedOnlyOwnSyntheticF':True,'publicR24IncludesThisMaterialFix':False,
 'realNangangRolesAndCompleteMaterialModuleAccepted':False,'listAndDetailReadbackWasNormalAPI':True,'noOriginalBusinessRowsOrCredentialsIncluded':True}
write(M/'scoped-acceptance.json',material)
public={'schema':'xnby.r24.actual-public-deployment.v1','at':now,'version':'R24','approvedExactEightTransportFiles':True,
 'manifestSHA256':'0a6d7682ba9d0b39611ad91ed1dea01c9eafd5c44d246d8873048a00260567e6','transportFiles':8,'transportBytes':4506722,
 'exactR21PreflightPassed':True,'deploymentPassed':True,'writes':758,'oldFrontendRemovals':607,
 'httpsTLSRedirectAndAnonymousAuthenticationPassed':True,'staticFilesVerified':1174,'rawUnchangedFiles':1161,'pinnedGatewayTransformsVerified':13,
 'brandedEntryAndWorkflowFacadeURLsVerified':wire['brandedEntryAndFourWorkflowFacadeAssetURLsVerified'],
 'rawHashDiagnosticPreserved':True,'authenticatedRealAccountFullBusinessFlowPassed':False,'desktopHandedBack':True,
 'materialR128CandidateExcluded':True,'publicGitPushInThisAuthorization':False,'tencentWriteInThisAuthorization':False,
 'originalDatabasePrivateConfigJarsAndIISMappingPreserved':True,'fullCloneReady':False,'strictCompleteModules':0}
write(D/'actual-public-deployment.json',public)
guide=f'''# R24公网部署结果与体验说明

更新时间：{now}。R24已经部署至 https://www.joinlinksmart.com/zhumadian/ 。本记录替代旧候选说明中的“未批准、未上线”当前状态；固定运输文件和历史证明不改。

用户已明确批准固定8文件及桌面交接。8文件4,506,722字节，清单SHA256为0a6d7682ba9d0b39611ad91ed1dea01c9eafd5c44d246d8873048a00260567e6。FTP目录/Zhumadian/Zhumadian_Unified_Emergency_20261101_R24/。服务器内精确R21、文件与运行归属预检通过，正常停启六组件，758写入、607旧前端移除，更新后十份就绪通过。原业务/平台Jar、数据库、真实配置及IIS映射保持。远程操作结束，鼠标键盘已明确交还。

HTTPS证书验证、裸/zhumadian到/zhumadian/的301、主页/home/应急入口、登录配置和匿名访问原鉴权均通过。1174个静态文件已验证：1161个原字节一致，13个严格匹配精确固定的原网关品牌替换或图标别名输出，另验8个带品牌版本的入口资源/四工作流门面URL。首次原文件直接比较产生13处差异的诊断保留，不忽略差异、不改产品来迎合检查；纠正为实际网关输出标准后全部一致。真实账号登录后的公网完整业务链尚未验收。

## 可以如何体验

1. 打开上述公网地址，正常登录。若仍显示旧页面，可刷新后再进入；浏览器账号、密码、验证码由使用者自行输入。
2. 首页进入“敏捷应急管理”，查看“审批管理”下“我发起的”和“待办事宜”（菜单可因既有角色权限而异）。打开已有测试任务的流程详情，检查发起人、关联任务、审批记录及流程图是否显示。
3. 从首页“应急处置”进入任务列表，选择“处置中”状态、查询后重置；核对状态标签、任务详情及相关流程入口。
4. 有合法待办权限的测试角色可在明确的测试任务中检查意见必填、连续点击时提交保护，以及提交结果不明时的核对提示。普通用户未被授权的审批或业务写入不属于体验必需步骤。不要在真实任务上故意制造网络故障或重复审批。
5. 原生审批回调可更新关联任务状态；它并不证明人工处置反馈、附件、全部多节点流程已经完成。

这些功能的原生普通角色浏览器、合成业务及完整六组件运行已有本地证明；本次公网验证限部署、静态资源、就绪和匿名接口，不能等同真实南港角色/定义全链通过。如现有角色没有菜单，先反馈角色与缺失入口，不修改生产权限绕过验证。

## 仍有的缺口

真实南港流程定义及角色矩阵、多节点会签/转审/退回/加签、人工处置反馈与附件、通知和失败补偿、36字符组织兼容，以及M02队伍/专家/值班与资源完整业务尚待逐项核对。严格整模块仍0/8，fullCloneReady=false，不能声称全面复刻。

本轮另外在本机纯合成_f验证了物资Excel导入整文件回滚和弹窗过期响应保护；这项新候选不在固定R24，不可在公网宣称已修。腾讯问题表本轮没有回填，G12具体失败步骤仍待确认。源码、验证和说明纳入既有本地review同步范围，具体Git提交见本轮回执；本次授权不含新的公开Git推送。旧整体百分比和4—6周估算已撤回，未据本次检查数重算工期。
'''
(D/'公网部署结果与体验说明.md').write_text(guide,encoding='utf-8')
matdoc=f'''# M02物资Excel原生全组件验证R128

更新时间：{now}。仅独立自有纯合成_f，未操作正式18891、用户_c/_d/_e或8767。此候选未含在已上线固定R24，也没有被公开Git发布。

原实现真实复现：3001行文件最后一行非法，接口失败但前3000行已落库。候选仅适配原MaterialsController.importExcel和材料专用导入弹窗，保留其它原控制方法、公开ABI、参数名、鉴权和重复导入追加语义；使用文件事务使该失败文件新增0行，保留先前3000合成行。全局ImportExcel组件不改，表结构及原398定义不改。

实际原生普通角色登录、菜单和Chrome下载/上传通过。r5原基线、r6候选、r7重启及边界三轮均完整运行六组件、十就绪，所有控制器/组件正常0退出，后代归零，无强杀。r7共9条业务浏览器检查：原12列表头空模板、合法3行导入及列表/详情API核对、上轮3行跨全组件重启保留、3001行失败全回滚、假xlsx拒绝且旧行保留、仅表头空模板成功无操作、真实已提交成功响应延迟时保留新打开弹窗、同文件二次导入仍追加为6个不同ID。

前端WF7以WF6为底，仅替换物资页面导入组件接线并增加专用弹窗，完整338文件构建、235输入/34覆盖、1521引用、173 JS语法及声明外差异0均有证明。原WF6工作流修正保留。

测试驱动下载路径和早期自造OOXML兼容失败已保留原证据：改用Windows原生路径、原POI写入器后通过，不把这些驱动失败算产品缺陷。列表/详情回读走正常接口，尚不冒称其实际表格筛选/详情点击UI都已通过；真实南港权限、真实XLS、完整物资CRUD/地图/导出、队伍专家和值班继续待。

后续须将候选形成独立、可审阅、严格基线和恢复验证的新公网包；不得改写固定R24或借R24批准部署新增3类/前端。用户已交付体验根持续保护，到期后也不能用作自动测试数据或清理对象。
'''
(M/'验证结果与边界.md').write_text(matdoc,encoding='utf-8')
appfiles=[]
for name in ['verify_r24_public_https.py','verify_r24_retained_branding.py','build_material_excel_full_candidate.py','prepare_native_material_workbook_writer.py','prepare_wf7_material_import.py','install_owned_material_candidate_r128.py']:
 shutil.copyfile(V/name,T/name);appfiles.append('tools/'+name)
for rel in ['tools/verify_full_controller_material_r128_20261101.py','tools/verify_full_controller_material_browser_r128_20261101.mjs','tools/prepare_owned_material_workbooks_r128_20261101.py',
 'tools/java/material_full_controller_r1/OwnMaterialPortalMenusFixture.java','tools/java/material_full_controller_r1/OwnMaterialWorkbookWriter.java','tools/java/OriginalMaterialExcelImport.java',
 'tools/frontend/material-native-import/src/views/emergencyResources/materials/index.vue','tools/frontend/material-native-import/src/components/ImportExcel/OriginalMaterialExcelImport.vue',
 'tools/build_emergency_workflow_source_20261101.mjs','tools/verify_emergency_workflow_source_20261101.py']:
 if not(A/rel).is_file():
  # Source fixture paths are checked, never substitute another source silently.
  raise AssertionError('EXPECTED_SOURCE_MISSING:'+rel)
 appfiles.append(rel)
for source,target in [(D/'公网部署结果与体验说明.md','deploy/handbook/public_r24_actual_deployment_20261101.md'),(M/'验证结果与边界.md','deploy/handbook/material_import_full_controller_r128_20261101.md'),
 (D/'actual-public-deployment.json','deploy/verification/public_r24_actual_deployment_20261101.json'),(D/'public-retained-gateway-verification.json','deploy/verification/public_r24_retained_gateway_20261101.json'),(M/'scoped-acceptance.json','deploy/verification/material_import_full_controller_r128_20261101.json')]:
 (A/target).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,A/target);appfiles.append(target)
entry=f'''## {now} R128公网R24部署验证通过；物资整文件回滚仅本地候选

完整UE对标XNBY渲染效果/效率、EXE GIS/DLG点线面样式/图层/旗杆标牌多源绑定、Web3D和南港B/S目标保持active；近期M02/M07、严格整模块0/8/fullCloneReady=false。旧50—65%/4—6周无校准结论仍撤回，不用检查数冒充总工作量。

用户明确批准固定R24并交接桌面，8文件4506722B/清单0a6d7682…567e6已上传并逐SHA核，精确R21预检、正常六组件更新、758写+607移除、更新后十就绪通过。限定服务器结果回读成功，原Jar/真实配置/DB/IIS保持。HTTPS/TLS/裸地址301/匿名鉴权通过；1174静态文件中1161原字节一致、13处按保留网关的精确品牌替换/图标别名字节验证一致，8个品牌版本入口/四门面资源补验通过，原始13差异诊断保留。R24已上线；真实账号公网完整业务流程仍待，鼠标键盘已明确交还。说明见Deployment/public_test_unified_r24_20261101/公网部署结果与体验说明.md。

交接前在独立自有_f运行M02物资r5原基线/r6候选/r7重启边界，三次六组件十就绪/398原定义/正常退出通过。真实3001行最后非法文件原先写入3000行，候选整文件事务新增0且原3000保留；合法3行、跨重启、假xlsx拒绝、仅表头无操作、真实成功迟响应不关闭新弹窗、重复文件追加6行均通过。WF7仅物资接线+专用弹窗，338文件/235输入/34覆盖/1521引用/173 JS与声明外差异0。9条原生角色浏览器检查证明只覆盖此物资路径，列表/详情为API回读；不宣称完整物资模块。新3类/WF7未入R24。用户_c/_d/_e持续保护；_f未交付且已正常停。

原真实南港定义/权限、多节点会签转审退回加签、人工处置反馈附件/通知、组织36兼容、M02队伍专家值班和其余资源流程仍待。腾讯本轮新增回填0，G12具体失败步骤待。18891旧R4仍停、8767未动。源/文档同步既有本地review；本次R24明确不含公开Git，公开头仍应用68833422/引擎7ee7836e，不能称已含本轮新源。

'''
enginefiles=[]
def prepend_once(p):
 old=p.read_text(encoding='utf-8')
 if 'R128公网R24部署验证通过；物资整文件回滚仅本地候选'not in old[:180]:p.write_text(entry+old,encoding='utf-8')
for rel in ['project/htengine_goal_state.md','project/当前工作断点.md','project/测试反馈与首页适配进展_20261031.md','showcase_demo_completion.md']:
 p=R/'Document/Engine'/rel;prepend_once(p);q=E/'docs'/rel;q.parent.mkdir(parents=True,exist_ok=True)
 if not q.exists()or not p.samefile(q):shutil.copyfile(p,q)
 assert p.read_bytes()==q.read_bytes();enginefiles.append('docs/'+rel)
p=R/'Document/Design/驻马店实施基线.md';prepend_once(p)
p=R/'Document/Deployment/public_test_risk_r22_20261101/continuation-state.json';state=J(p)
state.update({'at':now,'lastGoalTurnClassification':'progress','consecutiveNoProgressTurns':0,'publicVersion':'R24','fixedPackageManifestSHA256':public['manifestSHA256'],
 'fixedTransportFiles':8,'fixedTransportBytes':4506722,'newUpdaterSHA256':'4931c7fbb58880f228423f8324d3b40cb22e500bc299f053a8fe455a742c7878','newGuardContractCases':157,'codeReplacementAndRecoveryScenarios':12,
 'publicServerPreflightPassed':True,'publicInstalled':True,'publicUploadedOrInstalled':True,'publicGitPushed':False,'priorR23PublicGit163Completed':True,
 'desktop':'R24 authorized RDP/FTP operations complete; desktop explicitly handed back; background checks only',
 'publicR24Approved':True,'publicR24Deployed':True,'publicR24HTTPSStaticAndAnonymousAuthPassed':True,'publicR24AuthenticatedFullFlowPending':True,
 'publicR23ApprovalAndDesktopHandoffPending':False,'r23DeploymentAndDesktopHandoffStillPending':False,'publicR23SupersededWithoutDeployment':True,
 'unifiedUpdaterPreflightAndRecoveryPending':False,'actualPublicReleaseAndPrivateIdentityPreflightPassed':True,
 'unifiedCandidateStage':str(R/'work/user_feedback_20261031/r24-unified-candidate-r1'),
 'publishedEmergencyFrontendFiles':338,'materialR128CandidateLocalOnly':True,'materialOriginalPartialImport3000Reproduced':True,'materialCandidateFailedFilePersistsZero':True,
 'materialWholeControllerBrowserCases':9,'materialUserPreviewFHandedOver':False,'manualTaskPreviewLiveStatusNotRechecked':True,
 'next':'Public R24 deployed and limited HTTPS/static/auth verification passed; authenticated real Nangang role/full M02/M07 flow remains pending. Material WF7/three-class transaction candidate proven only on stopped own_f; prepare a separate fixed package before public publication. Protect user_c/_d/_e permanently. Update local review checkpoints, preserve public Git approval boundary. No unsupported overall percentage or timeline.'})
write(p,state)
scope={'at':now,'application':sorted(set(appfiles)),'engine':enginefiles,'publicPushAuthorized':False,'formalHEADIndexAndHeldNativeMustRemainUnchanged':True}
write(D/'local-git-scope-r128.json',scope)
print(json.dumps({'publicR24LimitedAcceptancePassed':True,'materialCandidateCases':9,'appLocalFiles':len(scope['application']),'engineLocalFiles':len(enginefiles),'desktopHandedBack':True},ensure_ascii=False))
