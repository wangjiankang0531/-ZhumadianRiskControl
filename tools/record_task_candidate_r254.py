from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/original_task_attachment_verified_r254_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def enc(x):return(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
assert not D.exists()
r=J(C/'r122/result.json');o=J(C/'r122-outer-terminal.json');receipt=J(C/'r122/scoped-controller-receipt.json')
assert r['allPassed']and r['actualExecutedNativeBrowserPhases']==9 and r['original398ModelsUnchanged']and r['connectionCapacityWithoutRefusals']
assert o['exitCode']==0 and o['actualDescendantsZeroBeforeClose']and not o['forceTerminationUsed']
assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
for n in ['frontend-restored.json','history-runtime-restored.json','configuration-restored.json']:assert J(C/'prepared-r122'/n)['passed']
original=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256']
assert sha(R/'_g/Application/release-manifest.json')==original
phases=['operator','operator-disposal','reviewer-preview','operator-added','operator-waiting-parallel-b','reviewer-after-added','reviewer-final','reviewer-handled-readback','operator-completed-readback']
phaseproof=[]
for label in phases:
 root=C/'r122'/('workflow-browser-'+label);b=J(root/'result.json');t=J(root/'browser-terminal.json')
 assert b['passed']and not b['exceptions']and t['normalBrowserClosed']and t['chromeExitCode']==0 and not t['forceTerminationUsed']
 phaseproof.append({'phase':label,'passed':True,'normalChromeExitCode':0,'cases':[x for x in b['cases']if x.get('passed')is True]})
first=phaseproof[0]['cases'];names={x['case']for x in first}
assert {'shared-candidate-uploader-held-before-network-blocks-task-submit-and-keeps-input','shared-candidate-task-save-has-one-inflight-request-and-retains-form-until-confirmed'}<=names
failed=J(C/'r121/failure.json');fo=J(C/'r121-outer-terminal.json');fr=J(C/'r121/scoped-controller-receipt.json')
assert failed['phase']=='native-two-level-workflow-browsers'and fo['actualDescendantsZeroBeforeClose']and fr['allOwnedChildrenExited']
assert not(C/'r121/own-menu-visibility-scope.private.txt').exists()
assert J(C/'prepared-r121/frontend-restored.json')['passed']and J(C/'prepared-r121/history-runtime-restored.json')['passed']
offline=J(V/'mapper-offline-registration-r251-r2/result.json')
assert offline['originalXMLParsed']==96 and not offline['parseErrorTypes']and not offline['pendingResolutionErrorType']
proof={'schema':'xnby.r254.verified-task-attachment-candidate.v1','result':r,'phaseResults':phaseproof,
       'normalSixComponentExitCodes':receipt['exitCodesBeforeJobClose'],'allActualDescendantsZeroAndOriginalBytesRestored':True,
       'priorFailedAttemptR121':{'failure':failed,'normalExitAndExactRestorePassed':True,'hardcodedRootGuardRejectedBeforeDatabaseConnection':True,'nativeBusinessBrowserStarted':False},
       'offlineOriginalMapperRegistration':offline,'offlineRegistrationIsNotRuntimeSpringProof':True,
       'originalNangangWholeAcceptancePassed':False,'publicDeploymentOrDesktopOrNewPublicGitPerformed':False}
put(D/'verified-result.json',enc(proof))
text='''# 任务附件候选回归与原Mapper核对（R250—R254，2026-11-03）

R224十四源码/341文件候选继预案演练r120十一项通过后，在r122完成原SDK九阶段双普通角色并行审批回归。实际任务页面上传请求在发往服务器前暂停，点击提交不产生保存请求且任务名称保留；真实上传完成后保存请求暂停，再次点击提交仍只有一个请求，确认成功才回列表。任务处置必填拒绝、反馈保存、两个独立分支各自待办、A处理后等待B、B处理后唯一末级、最终已办/发起回看、实际下载锚点文件内容一致均通过。原398模型定义、连接容量及普通审批无额外加签记录检查保持。九个Chrome与六组件正常0、实际后代零，原前端/更新器/历史模块/虚构配置/清单精确恢复，_g原基线e9dcd876已核同。

首轮r121被自有菜单观察Java类遗留r108硬编码目录拒绝，位于数据库连接之前；没有生成菜单更改范围文件，浏览器未启动。这是验证工具问题，不是任务功能失败。原失败/恢复失败标记如实保留（恢复尝试也因同一目录守卫被拒）；六组件正常0和所有代码/配置精确恢复已独立核实。R252克隆类只允许新r122精确目录，原三条合成菜单身份/字段/事务与恢复断言未放宽，r122隐藏/恢复菜单均通过。

原业务Jar有96份xml/映射；项目实际MybatisPlus默认资源扫描仅看到外置队伍成员Mapper。以实际依赖离线解析全部96份，零解析/待解析错误，完全限定注册语句总数1319（包含框架自动注入语句，不能当作1319项业务完成或原XML语句数量）。原cqweh自动配置类没有设置MapperLocations的方法。以上仍不能代替实际Spring SqlSessionFactory逐原语句注册证明，也不证明其余业务全部故障。后续需要在自有容器观察真实注册清单，核对原配置并处理默认扫描目录；不能盲加全局xml与mapper双扫描导致重复注册，也不能仅补单个预案就宣称全映射完成。

R37静态性能固定包保持已上传/预检通过、待手动执行完成回执；未重新部署。此任务候选也未上公网。后续统一候选必须以实际R37为基线保留压缩/缓存/IIS控制，不覆盖既有鉴权、数据、上传及意见历史；全部真实南港模板/通知和整系统验收仍待。公开Git固定30范围待答，本轮仅本地Git。完整引擎UE效果效率、EXE GIS/DLG点线面图层空间标牌及多源绑定、Web3D和一系统多入口B/S复刻目标active/fullCloneReady=false；另一三维会话专属断点、8767/资产、正式18891均保持。
'''
put(D/'阶段说明.md',text.encode());put(A/'deploy/handbook/task_attachment_verified_r254_20261103.md',text.encode());put(A/'deploy/verification/task_attachment_verified_r254_20261103.json',enc(proof));put(R/'Document/Engine/project/任务附件候选回归R254_20261103.md',text.encode())
entry='''## 2026-11-03 R254：任务候选九阶段通过、全部恢复；原XML整体注册待运行容器核实

R224十四源码候选r122实际上传未发网阻止提交/保留输入、保存中重复点击仅一次请求、处置反馈、原SDK双角色独立并行分支至末级/已办/附件实际下载九阶段通过。398模型/容量/无非目标加签保持，九Chrome/六组件正常0及实际后代零，前端/模块/假配置/清单精确恢复，_g原e9dcd876。session26808终态0不可再轮询。r121旧菜单观察类硬编码目录在数据库连接前拒绝，失败保留且代码配置正常恢复；R252仅克隆精确r122目录，菜单隐藏/恢复通过。原96XML用实际依赖离线解析零错误、1319含自动注入语句不能作业务计数；默认扫描只见外置队伍成员，仍需实际Spring工厂逐原语句证明，不盲双扫描或宣称其他模块均坏。R37已上传/预检过待执行回执，30公开Git待答；本轮未操作桌面/公网/正式18891/三维8767。详Deployment/original_task_attachment_verified_r254_20261103。完整目标active/fullCloneReady=false，另一三维专属断点保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
names=[]
for folder in ['original_task_attachment_candidate_r250_20261103','original_task_attachment_candidate_r252_20261103']:
 pins=J(R/'Document/Deployment'/folder/'preparation.json')['sources']
 for name,pin in pins.items():assert sha(A/'tools'/name)==pin;names.append('tools/'+name)
extra=['prepare_task_attachment_candidate_r250.py','prepare_task_fixture_r250.py','prepare_task_suite_retry_r252.py','prepare_task_attachment_candidate_r252.py','prepare_task_fixture_r252.py','inspect_mapper_and_task_inputs_r250.py','inspect_mapper_runtime_inputs_r251.py','inspect_original_mapper_registration_r251.py','audit_mapper_settings_r253.py','record_task_candidate_r254.py']
for name in extra:
 p=A/'tools'/name;assert not p.exists();raw=(V/name).read_bytes();ast.parse(raw.decode('utf-8'));put(p,raw);names.append('tools/'+name)
names+=['deploy/handbook/task_attachment_verified_r254_20261103.md','deploy/verification/task_attachment_verified_r254_20261103.json']
put(D/'local-stage-files.json',enc({'application':names,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/project/任务附件候选回归R254_20261103.md','docs/showcase_demo_completion.md']}))
print(json.dumps({'recorded':True,'actualNativePhases':9,'newTaskGuardsPassed':2,'normalRestorationPassed':True,'originalMapperXMLParsedOffline':96,'publicOrDesktopChanged':False}))
