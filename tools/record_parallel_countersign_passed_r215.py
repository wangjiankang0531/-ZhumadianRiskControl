from pathlib import Path
import ast,datetime,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_parallel_countersign_r215_20261103';J=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def js(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
scope=J(D/'scope-and-source-pins.json');assert all(sha(A/'tools'/n)==pin['sha256'] for n,pin in scope['sources'].items())
result=J(C/'r106/result.json');outer=J(C/'r106-outer-terminal.json');receipt=J(C/'r106/scoped-controller-receipt.json')
assert result['allPassed'] and result['actualExecutedNativeBrowserPhases']==8 and result['original398ModelsUnchanged'] and result['connectionCapacityWithoutRefusals'] and outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose'] and receipt['normalOwnedShutdown'] and receipt['allOwnedChildrenExited'] and all(x==0 for x in receipt['exitCodesBeforeJobClose'].values())
assert J(C/'prepared-r106/frontend-restored.json')['passed'] and J(C/'prepared-r106/history-runtime-restored.json')['exactOriginalBytesRestored']
phases=['operator','operator-disposal','operator-added','operator-waiting-parallel-b','reviewer-after-added','reviewer-final','reviewer-handled-readback','operator-completed-readback'];states=[]
for name in phases:
 p=C/'r106'/('workflow-browser-'+name);b=J(p/'result.json');term=J(p/'browser-terminal.json');assert b['passed'] and term['normalBrowserClosed'] and not term['forceTerminationUsed'];state=J(C/'r106'/('state-'+name+'.json'));assert state['passed'];states.append({k:state[k] for k in ['phase','observedTaskStatus','pendingEngineTasks','originalEngineHistoryHasEndTime','expectedBusinessStatusMatched']})
assert not states[2]['originalEngineHistoryHasEndTime'] and states[2]['pendingEngineTasks']>0 and not states[4]['originalEngineHistoryHasEndTime'] and all(s['originalEngineHistoryHasEndTime'] and s['pendingEngineTasks']==0 for s in states[5:])
waiting=J(C/'r106/workflow-browser-operator-waiting-parallel-b/result.json');assert any(x['case']=='first-countersign-approver-no-longer-has-same-instance-in-pending-list-before-second-approval' and x['passed']for x in waiting['cases']);withdraw=next(x for x in waiting['cases']if x['case']=='initiator-detail-keeps-only-original-withdraw-and-no-approval-while-other-countersign-pending');assert withdraw['passed'] and withdraw['originalWithdrawAvailable']
for phase in ['operator-added','reviewer-after-added']:
 node=J(C/'r106'/('workflow-browser-'+phase)/'native-two-approver-node.json');assert node['counterSign']==1 and node['title']=='OWN_APPROVE' and set(node['approvers'])=={'a5310000000000000000000000000064--user','a5310000000000000000000000000065--user'}
observation=J(C/'r106/workflow-browser-operator-completed-readback/parallel-countersign-observation.json');assert observation['bothOrdinaryApproversAndFinalNodeOpinionsExactlyOnce'] and observation['actualOrderFirstThenSecondThenFinal'] and observation['nonTargetApprovalCreatedNoAddsignHistory']
actual=J(C/'r106/actual-connection-budget.json');assert actual['mysqlMaxConnections']>=24
proof={'schema':'xnby.r215.two-ordinary-approver-countersign.v1','at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'browserPhases':8,'actualNativeCounterSign':1,'ordinaryApprovers':2,'firstApprovalWaitedForOtherRole':True,'firstApproverNoLongerHasPendingForInstance':True,'secondApproverStillAtFirstNodeBeforeApproval':True,'bothRequiredBeforeFinalNode':True,'originalInitiatorWithdrawPreservedWithoutApprovalActions':True,'threeDistinctOpinionsExactlyOnceAndActualTimeOrder':True,'taskEventFeedbackAndOriginalAttachmentRetained':True,'ordinaryApprovalCreatedNoNonTargetAddsignHistory':True,'finalR36R2UpdaterSHA256':'67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca','finalR36R2ActualSixComponentLifecycleNowVerified':True,'original398ModelsAndConnectionCapacityUnchanged':True,'normalSixComponentAndEightBrowserExitZeroActualDescendantsZero':True,'originalFrontendRuntimeAndFakeConfigurationRestoredExact':True,'r214OverbroadNoOperationFormAssertionFailureKept':True,'productCodeOrPublicDeploymentChanged':False,'newDatasourceOrDDL':False,'currentPublicVersion':'R36','wholeOriginalNangangTemplateAcceptanceClaimed':False,'fullCloneReady':False}
js(D/'verified-result.json',proof);js(D/'actual-native-state-checkpoints.json',states);js(A/'deploy/verification/parallel_countersign_r215_20261103.json',proof)
text='''# 双普通角色会签及发起人撤回边界（2026-11-03）

使用最终R36-r2更新器67545498、原SDK和原服务门控，在自有合成环境完成八个实际浏览器阶段：新增任务并上传附件、处置反馈、普通角色A首节点通过、A待办不再含本实例且发起详情仅原撤回、普通角色B仍在首节点通过、A末级通过、已办只读、发起终态回看。实际provider两次返回counterSign=1、OWN_APPROVE及两名预置普通角色；第一人通过后原引擎仍未结束，第二人通过后才进入OWN_FINAL_REVIEW，末级完成后原引擎结束且待办为零。

首节点两份与末级一份意见各恰一次，真实时间先后正确；任务/事件/附件/反馈关联保持，原锚点实际下载字节核验保持。全程不调用加签，终态没有新增状态10加签意见，证明历史模块对本普通会签路径没有误留痕。原398模型、连接容量无拒绝；最终R36-r2精确整文件六组件生命周期现已在本机实跑通过，所有八个Chrome与六组件正常0、实际Job后代零，原前端/运行模块/假配置/合成菜单标记精确恢复。

R214/r105第一轮误把发起人详情中的任何操作表单都当作可审批而失败。实际原组件在运行中按hasRevokeBtn提供“撤回”，页面无“通过/退回”。R215保留原撤回功能，改为精确断言可见选项只为撤回，不改变产品或降低多人等待、意见时间、待办归属等检查；原失败及正常恢复证明保留。本轮没有产品修复或新公网部署，公网仍为已验R36。

业务表单只读不等于运行中的发起人没有原版撤回操作。先前公网37项样本中的发起终态无审批已通过，不能据此外推所有运行中发起详情都没有操作区。已办仍无审批，待办审批按本人精确处理节点核实；发起人撤回按原版权限保持。

这是原SDK自建两节点/两普通角色的真实业务验证，不是252运行站全部真实模板或整个模块验收。真实南港全部条件分支、或签、并行节点、通知等仍待逐项核对，fullCloneReady=false。正式18891、8767/资产/DLG、另一三维断点、当前公网与桌面未改。
'''
write(D/'验证结果与剩余缺口.md',text);write(A/'deploy/handbook/parallel_countersign_r215_20261103.md',text);write(E/'docs/project/双人会签验证进展_20261103.md',text)
for p in [R/'Document/Deployment/public_test_native_history_r36_20261103/实际部署与清理及体验说明.md',A/'deploy/handbook/native_history_r36_actual_20261103.md']:
 s=p.read_text(encoding='utf-8-sig');old='本人当前处理节点才可出现审批区，已办与发起详情保持只读。';new='待办审批按本人当前处理节点核实，已办不提供审批操作。业务表单保持只读；运行中的发起人详情按原版权限仍可撤回。';assert s.count(old)==1;write(p,s.replace(old,new))
progress='''## 2026-11-03 R215：双普通角色会签八阶段通过，原发起人撤回保持，最终R36-r2生命周期补验完成

自有r106原SDK/provider实际counterSign=1及两普通角色，新增/附件/处置、A通过后不再待办但仍等B、发起详情仅原撤回、B仍首节点再通过、A末级、已办及终态回看八阶段通过。三份独立意见各一次/原时间顺序、附件实际下载/任务事件反馈保持；普通会签未误生成加签历史。原398模型/连接容量保持，六组件八Chrome正常0、实际后代零、前端/模块/假配置/菜单标记精确恢复。最终R36-r2更新器67545498整文件现已实际跑完整本机生命周期，不再只有r1 AST来源。

前轮r105过宽断言误把发起人原撤回当审批，失败原证据保留；本轮精确断言仅撤回、无通过退回，没有删除原功能或修改产品。本轮公网R36不变、桌面不输入；源/说明保存既有本地review，新的公开范围尚未混入旧105清单。证据Deployment/original_parallel_countersign_r215_20261103/verified-result.json；下一按原模板核或签/并行节点/通知，真实南港整模块未验，fullCloneReady=false。完整UE效果效率引擎/EXE GIS DLG图层旗杆多源标牌/Web3D/全南港B/S目标active，另一三维专属断点、8767/资产和正式18891保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
 s=p.read_text(encoding='utf-8-sig');assert not s.startswith(progress);write(p,progress+s)
p=R/'Document/Engine/showcase_demo_completion.md';write(p,p.read_text(encoding='utf-8-sig')+'\n'+progress)
for name in ['prepare_parallel_countersign_suite_r214.py','prepare_parallel_countersign_retry_r215.py','record_parallel_scope_r215.py','record_parallel_countersign_passed_r215.py']:
 s=(V/name).read_text(encoding='utf-8');ast.parse(s);write(A/'tools'/name,s)
files=['tools/'+n for n in scope['sources']]+['tools/'+n for n in ['prepare_parallel_countersign_suite_r214.py','prepare_parallel_countersign_retry_r215.py','record_parallel_scope_r215.py','record_parallel_countersign_passed_r215.py']]+['deploy/verification/parallel_countersign_r215_20261103.json','deploy/handbook/parallel_countersign_r215_20261103.md','deploy/handbook/native_history_r36_actual_20261103.md']
js(D/'local-stage-files.json',{'application':files,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md','docs/project/双人会签验证进展_20261103.md']});print(json.dumps({'verifiedEightPhasesAndNormalRestore':True,'sourceFiles':24,'newProductOrPublicChanges':False,'fullCloneReady':False}))
