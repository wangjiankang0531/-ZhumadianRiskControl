from pathlib import Path
import ast,datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;D=R/'Document/Deployment/public_test_pending_visibility_r34_20261102';W=R/'work/user_feedback_20261031';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=datetime.datetime.now().astimezone().isoformat()
prep=J(D/'preparation-result.json');independent=J(D/'independent-fixed-delivery-verification.json');order=J(D/'transport-order-verification.json');full=J(R/'work/r34gv-r1/full-preflight-result.json');tx=J(W/'r34-pending-visibility-candidate-r1/result.json');native=J(R/'Document/Deployment/workflow_pending_visibility_r178_20261102/verified-result.json');manifest=J(D/'delivery-manifest.json');git=J(R/'Document/Deployment/original_transfer_addsign_r171_20261102/public-git-completed-r175.json')
assert prep['passedPreparation']and independent['passed']and order['allPassed']and full['allPassed']and tx['allCompositionContractsPassed']and native['passed']
assert sha(D/'delivery-manifest.json')==prep['manifestSHA256']=='d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af'
assert prep['transportFiles']==8 and prep['transportBytes']==1964748 and manifest['writes']==176 and manifest['obsoleteAssetRemovals']==172
assert git['files']==27 and git['application']['commit']=='c67c17fc0397e0c2e94cea3a71ccf2d866f4d0f6'and git['engine']['commit']=='5a4e3bcebe80e8a1d2de081d82b14ef4dcec7ed7'
sources=['prepare_pending_updater_r179.py','prepare_sparse_pending_tools_r179.py','prepare_pending_visibility_sparse_r179_20261102.py','prepare_full_pending_tools_r179.py','verify_pending_visibility_full_program_r179_20261102.py','prepare_pending_delivery_tools_r179.py','build_pending_delivery_r179_20261102.py','prepare_pending_delivery_checks_r179.py','verify_pending_delivery_r179_20261102.py','verify_pending_transport_order_r179_20261102.py','record_pending_delivery_r179.py']
pins={}
for name in sources:
 target=A/'tools'/name;assert not target.exists();raw=(V/name).read_bytes();ast.parse(raw,filename=name);shutil.copyfile(V/name,target);pins['tools/'+name]={'bytes':len(raw),'sha256':sha(target)}
source=A/'tools/original_public_test_update_r34_20261102.py';pins['tools/'+source.name]={'bytes':source.stat().st_size,'sha256':sha(source)}
(D/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
proof={'schema':'xnby.r179.fixed-r34-pending-visibility-candidate.v1','at':now,'fixedTransportFiles':8,'fixedTransportBytes':1964748,'manifestSHA256':prep['manifestSHA256'],'FTP':manifest['targetFTP'],'oldPublicReleaseSHA256':manifest['oldReleaseSHA256'],'newReleaseSHA256':manifest['newReleaseSHA256'],'writes':176,'oldEmergencyFrontendRemovals':172,'installPaths':348,'compositionNegativeCases':29,'normalAndFaultRecoveryScenarios':7,'foreignCodeDriftRefusedBeforeAnyRestore':True,'completeProgramFilesVerified':15553,'all20ControlsAndRetainedNonFrontendProgramsVerified':True,'runtimePoolBudgetCheckedBeforeOwnershipHealthOrServiceAction':True,'transportChecksUseExplicitOwnerAndHealthSpies':True,'originalR33LifecycleBackupAndRecoveryFunctionsASTUnchanged':True,'newUpdaterLifecycleIndependentlyStarted':False,'nativeFinalCandidateRoleSessions':10,'nativeFinalCandidateChecks':manifest['actualNativeBrowserChecks'],'nativeAllThreeRoundsRoleSessions':27,'nativeAllThreeRoundsChecks':243,'sourceDeltaFromR33':['src/components/workflow/info.vue'],'independentBeforeAddsignOpinionGapUnresolved':True,'actualServerPreflightAndPublicTLSOrUIStillPending':True,'publicUploadedOrInstalled':False,'TencentWritePerformed':False,'publicGitFixed27Completed':True,'publicGitApplicationCommit':git['application']['commit'],'publicGitEngineCommit':git['engine']['commit'],'R176ThroughR179PublicGitIncluded':False,'fullCloneReady':False}
(D/'candidate-summary.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(A/'deploy/verification/pending_visibility_r34_candidate_20261102.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(A/'deploy/verification/public_git_r175_completed_20261102.json').write_bytes((R/'Document/Deployment/original_transfer_addsign_r171_20261102/public-git-completed-r175.json').read_bytes())
description=f'''# 固定 R34 公网候选：精确待办处理节点的审批显示

准备时间：{now}。

8个运输文件，共1,964,748字节。清单SHA256：`{prep['manifestSHA256']}`。清单位于本目录delivery-manifest.json；运输文件在delivery。FTP目的地：`101.201.65.94 /Zhumadian/Zhumadian_Pending_Visibility_20261102_R34/`。目标应用：`C:\\inetpub\\wwwroot\\Zhumadian\\Application`。

## 具体行为

修正应急端工作流详情：只在正常当前用户仍持有此流程的精确待办处理节点时显示原审批表单；原审批人加签等待时或同流程其它处理节点的旧链接，仅显示查看提示；待办状态查询失败则提示刷新重试且不提供审批操作。原后端本已拒绝提前审批，本次不改变原权限或审批接口。

相对R33只有workflow/info.vue一个编译输入变化，原头像、驻马店图标、首页路由及其它既有适配保留。安装176写入+172旧应急前端移除，共348路径；只增加固定契约更新器及两清单，安全端前端、原Jar/任务/物资/队伍/鉴权、配置、数据库、上传、其它19控制与IIS保持。

## 已完成验证及限制

- 原六组件最终候选10阶段/{manifest['actualNativeBrowserChecks']}检查，三轮27次原生角色会话/243检查；两个旧处理节点链接不显示审批、有效审批人的查询故障不提供审批、恢复后正常完整加签链与引擎待办0/历史结束通过。全部组件正常0、实际后代零，前端和假配置精确恢复，398模型保持。
- 338个编译文件、1522本地引用、独立Vue再生通过。
- 29项越界/错误声明拒绝，7类正常与故障恢复、外来代码漂移拒绝，完整15553程序文件及20控制预检通过；使用合成私有配置，无真实凭据/种子/业务数据读取。
- 运输ZIP逐成员和每路径SHA、5项精确恢复归属、实际固定运输器check-only顺序通过。运输器的归属/健康明确为测试替身，完整load_bundle程序视图另行实际通过；不冒称公网运行身份或真实IIS/TLS已验。
- 新更新器只增加R34契约/分发分支，其余所有函数含生命周期/备份恢复AST与实际公网R33更新器相同；本轮未独立实际启动新更新器六组件生命周期。

审批前加签独立意见留痕仍未修复；真实南港全部模板角色/并行通知/其它附件和全B/S验收仍待。包尚未上传/部署、公网仍最近已验R33；不回填腾讯完成状态，不宣称整模块或UE目标完成。

## 拟执行范围

仅操作用户交接的公网RDP/FTP窗口，必要目标窗口截图核焦点；上传8文件并逐SHA核对。服务器内核精确R33（旧release `330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13`）、运行/文件归属、数据身份、10份就绪和停服前连接预算。原配置只在服务/预算子进程内存使用，不回传原文/凭据。预检通过正常停启六组件并安装；失败仅按本轮updateId/新旧SHA/自有备份恢复，退出归属不明即停止，不强杀。

公网UI沿用正常登录授权，只读核页头、菜单、本人有权查看的待办/已办详情和审批区；正常页面可能呈现必要姓名/任务名称，记录仅布尔、条数、阶段和HTTPS摘要，截图裁掉业务行/名单，不复制导出原始业务或账号/会话，不读回Cookie/令牌/口令。不会自行新建或修改公网业务记录。登录或安全验证异常时停止并交用户处理。

成功及HTTPS/UI核验后，按用户“只留最新”要求，核精确旧清单、已停/无引用、绝对范围和无重解析后，清退役R32/R33运输目录及相应已停旧代码副本；保留运行R34、数据、上传、配置和资产。不操作其它站点，不迁移目录。桌面操作前提示、焦点变化即停、结束交还。

本候选发布不包含新的公开Git或腾讯回填。固定27公开源已按call_b2d1d1f8c75e48d2833fd3feeea16402批准同步应用c67c17fc/引擎5a4e3bce，后续R176—R179源仍仅本地，不夹带进旧范围。
'''
(D/'固定候选说明.md').write_text(description,encoding='utf-8');(A/'deploy/handbook/pending_visibility_r34_candidate_20261102.md').write_text(description,encoding='utf-8')
progress=f'''## {now} 固定R34审批显示更新包本地就绪，27公开范围已按明确批准同步

R34八文件1964748B/manifest{prep['manifestSHA256']}，176写入172移除/348路径；只应急前端、固定契约更新器和两清单。29边界拒绝/7正常故障恢复与外来漂移、15553完整程序/20控制、真实运输ZIP/5恢复归属/预算先于任何停服通过。新更新器只增加契约及分发，所有既有其它函数AST保持；本轮未独立跑新更新器实际六组件停启。实际候选原生10阶段/{manifest['actualNativeBrowserChecks']}、全三轮27会话243/398模型/正常停机/精确前端与配置恢复证据保持。审批前独立意见仍缺，真实南港全部验收仍待。

公开固定27已获call_b2d1d1f8c75e48d2833fd3feeea16402明确批准，重新核原头及全部字节，应用c67c17fc0397e0c2e94cea3a71ccf2d866f4d0f6、引擎5a4e3bcebe80e8a1d2de081d82b14ef4dcec7ed7，复用原两分支/逐Blob/闭合树/唯一父/最终ref通过。旧自动拒绝已解决，不再待答；R176—R179新代码不在其内。完成回执Deployment/original_transfer_addsign_r171_20261102/public-git-completed-r175.json。

R34尚未上传/部署，公网最近已验R33，服务器旧版本清理未执行；待本轮桌面交接后按固定范围上线核验，未取得交接不操作桌面。8767恢复/登录自启保持。全UE/EXE GIS DLG多源空间标牌/Web3D/全南港B/S目标active，0整模块/fullCloneReady=false。详Deployment/public_test_pending_visibility_r34_20261102。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
 p=R/rel;p.write_bytes(progress.encode()+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n\n'+progress).encode())
(R/'Document/Engine/project/pending_visibility_r34_candidate_20261102.md').write_text(progress,encoding='utf-8')
print(json.dumps({'recorded':True,'transportFiles':8,'transportBytes':1964748,'manifestSHA256':prep['manifestSHA256'],'newSourceFiles':len(pins),'public27SyncCompleted':True,'R34UploadedOrInstalled':False}))
