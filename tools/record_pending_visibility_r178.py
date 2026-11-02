from pathlib import Path
import ast,datetime,hashlib,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163';W=R/'work/user_feedback_20261031/workflow-pending-visibility-r178';D=R/'Document/Deployment/workflow_pending_visibility_r178_20261102';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=datetime.datetime.now().astimezone().isoformat()
assert not D.exists();D.mkdir();trials={};browser_count=0;checks=0
for trial,phases in [('r76',8),('r77',9),('r78',10)]:
 root=C/trial;proof=J(root/'result.json');terminal=J(root/'controller-terminal.json');outer=J(C/(trial+'-outer-terminal.json'));receipt=J(root/'scoped-controller-receipt.json')
 assert proof['allPassed']and proof['actualExecutedNativeBrowserPhases']==phases
 assert terminal['exitCode']==outer['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']
 assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 assert J(C/('prepared-'+trial)/'configuration-restored.json')['exactOriginalBytesRestored']
 if trial!='r76':assert J(C/('prepared-'+trial)/'frontend-restored.json')['exactFrontendAndManifestBytesRestored']
 assert J(root/'schema-after.json')==J(R/'work/event_delivery_consistency_20261030/full-controller-r131/schema-before.json')and J(root/'schema-fresh-after.json')==J(root/'schema-after.json')
 assert J(root/'schema-after.json.capacity.json')['Connection_errors_max_connections']==0
 rows=[]
 for folder in sorted(root.glob('workflow-browser-*')):
  if not folder.is_dir():continue
  b=J(folder/'result.json');t=J(folder/'browser-terminal.json');assert b['passed']and not b['exceptions']and t['normalBrowserClosed']and t['chromeExitCode']==0 and not t['forceTerminationUsed'];browser_count+=1;checks+=len(b['cases']);rows.append({'phase':folder.name.removeprefix('workflow-browser-'),'checks':len(b['cases']),'passed':True})
 assert len(rows)==phases
 final=J(root/'state-reviewer-final.json');assert final['pendingEngineTasks']==0 and final['originalEngineHistoryHasEndTime']
 pending=J(root/'state-reviewer-early-probe.json');assert pending['pendingEngineTasks']==2 and not pending['originalEngineHistoryHasEndTime']
 trials[trial]={'phases':rows,'allSixComponentsAndActualDescendantsZero':True,'original398ModelsUnchanged':True,'configurationAndFrontendRestored':True,'actualHostSHA256':sha(root/'actual-host-source.py'),'actualBrowserSHA256':sha(root/'actual-browser-source.mjs')}
baseline=J(C/'r76/workflow-browser-reviewer-early-probe/early-approval-observation.json');stale=J(C/'r78/workflow-browser-reviewer-early-probe/early-approval-observation.json');other=J(C/'r78/workflow-browser-operator-other-node-link/early-approval-observation.json');fault=J(C/'r78/workflow-browser-operator-membership-unavailable/membership-lookup-failure-check.json')
assert baseline['originalSavedDetailApprovalVisible']and baseline['oneEarlyApprovalProbeSubmitted']and baseline['backendApprovalRejected']and baseline['businessCode']==400
assert stale['UIBlocksEarlyApproval']and not stale['oneEarlyApprovalProbeSubmitted']and stale['businessTaskAndAuditRecordSignatureUnchanged']
assert other['pendingListContainedInstance']and other['sameProcessDifferentOperatorLinkChecked']and other['UIBlocksEarlyApproval']and not other['oneEarlyApprovalProbeSubmitted']
assert fault['passed']and fault['onlyOnePendingLookupFailureInjected']and fault['approvalFormHidden']and fault['retryMessageVisible']and fault['auditRequests']==0
graph=J(W/'graph-and-source-verification.json');assert graph['passed']and graph['compiledFileCount']==338 and graph['missingAssets']==0
gap=J(C/'r78/workflow-browser-operator-completed-readback/addsign-sequence-and-opinion-observation.json');assert gap['opinionRetentionGapRemains']
sources=['prepare_early_addsign_probe_r176.py','verify_full_controller_early_addsign_r176_20261102.py','verify_native_early_addsign_browser_r176_20261102.mjs','run_early_addsign_r176_20261102.py','original_workflow_pending_visibility_r177.py','original_workflow_pending_visibility_r178.py','build_pending_visibility_r177.py','build_pending_visibility_r177.mjs','build_pending_visibility_r178.py','build_pending_visibility_r178.mjs','prepare_pending_visibility_runtime_r177.py','restore_pending_visibility_runtime_r177.py','prepare_pending_visibility_runtime_r178.py','restore_pending_visibility_runtime_r178.py','prepare_pending_visibility_probe_r177.py','prepare_exact_operator_candidate_r178.py','verify_full_controller_pending_visibility_r177_20261102.py','verify_native_pending_visibility_r177_20261102.mjs','run_pending_visibility_r177_20261102.py','verify_full_controller_pending_visibility_r178_20261102.py','verify_native_pending_visibility_r178_20261102.mjs','run_pending_visibility_r178_20261102.py','verify_pending_visibility_graph_r178.py','record_pending_visibility_r178.py']
pins={}
for name in sources:
 source=V/name;target=A/'tools'/name;assert not target.exists();raw=source.read_bytes()
 if name.endswith('.py'):ast.parse(raw,filename=name)
 elif name.endswith('.mjs'):
  r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(source)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
 shutil.copyfile(source,target);pins['tools/'+name]={'bytes':len(raw),'sha256':sha(target)}
for name in ['WorkflowInfoPendingVisibilityR177.vue','WorkflowInfoPendingVisibilityR178.vue']:
 p=A/'tools/frontend'/name;pins['tools/frontend/'+name]={'bytes':p.stat().st_size,'sha256':sha(p)}
proof={'schema':'xnby.r178.exact-pending-operator-candidate-verified.v1','at':now,'passed':True,'status':'local-candidate-only','normalNativeBrowserPhases':browser_count,'checks':checks,'trials':trials,'originalBackendAlreadyRejectedEarlyApproval':True,'originalUIStillExposedStaleApproval':True,'candidateStaleOriginalReviewerDetail':stale,'candidateSameProcessOtherOperatorDetail':other,'candidateActiveReviewerLookupFailure':fault,'candidateActualFullAddsignChainCompleted':True,'candidateNormalInitiatorAndCompletedReadbackPassed':True,'sourceAndGraph':graph,'beforeAddsignIndependentOpinionStillMissing':True,'publicVersion':'R33','publicInstalled':False,'transportAndNewUpdaterFullPreflightPending':True,'publicGitFixed27PendingUnchanged':True,'newCandidateIncludedInPrior27':False,'desktopInputSent':False,'fullCloneReady':False}
(D/'verified-result.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
(A/'deploy/verification/workflow_pending_visibility_r178_20261102.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text=f'''# 待办详情审批显示修正候选（R176—R178，2026-11-02）

问题：审批前加签后，原审批人已不在当前待办列表，但重开原待办详情地址仍显示“通过”等动作。原后端会拒绝提前审批：R176正常原账号/原页面仅提交一次，HTTP200/业务400，原任务与记录保持，实际引擎仍2待办未结束。此为前端状态显示缺陷，不能写成后端允许越序审批。

候选只修改 `src/components/workflow/info.vue`：页面初始隐藏审批区，先正常读取详情，再分页核实当前用户仍持有此流程的精确处理节点；匹配后显示原审批表单。已转走/加签等待中的旧地址显示“当前任务暂不可审批，请在待办列表中查看最新状态”；查询失败显示“暂时无法核实待办状态，请刷新后重试”，不提供审批按钮。不读取/伪造鉴权，不改原审批接口、权限或业务模型；“我发起的”撤回规则与完成/历史详情模式保持。

R177首版原生9阶段通过；继续补上同流程不同处理节点匹配后形成R178最终候选。R178完整10阶段通过：新增任务/68字节PNG附件、处置、审批前加签、原审批人旧链接、同流程另有待办的接收人打开旧节点链接、有效接收人待办查询一次503故障、恢复正常后接收人审批、原审批人接续、末级完成、发起人终态回看。

三个执行轮共{browser_count}次原生浏览器会话/{checks}项检查，六组件/浏览器/控制器正常0与实际后代零，前端和假配置按顺序精确恢复，398模型保持、连接拒绝0。末级实际引擎待办0、历史结束；任务/事件/附件/反馈保持。相对R33完整编译输入只改变上述1组件，338编译文件与1522本地引用通过；头像、项目图标、首页兼容和其它既有适配保留，构建副本已恢复原源字节。

验收范围仅自建两级模板/两个普通角色的隔离环境。审批前加签独立意见留痕仍缺失，本轮未解决；真实南港全部模板角色/并行、其它附件和通知仍待。候选尚未封装公网运输包，新的更新器全程序预检/恢复与公网验收尚未执行；公网保持R33。不得将本候选称已上线或整模块完成。

后续上线体验：原审批人加签后再开旧待办地址应仅可查看；接收人进入自己的当前待办应可正常审批。此行为目前只能在隔离候选中确认，待公网部署通过后再通知测试团队。此前27文件公开范围保持冻结且仍待答，新候选代码不夹带其中。

证据：`Document/Deployment/workflow_pending_visibility_r178_20261102/verified-result.json`，原执行小型记录保留在 `work/event_delivery_consistency_20261030/full-controller-r163/r76` 至 `r78`。完整UE引擎/EXE GIS DLG多源标牌/Web3D/全南港B/S目标active，fullCloneReady=false。
'''
(D/'审批状态显示修正与本地验收.md').write_text(text,encoding='utf-8');(A/'deploy/handbook/workflow_pending_visibility_r178_20261102.md').write_text(text,encoding='utf-8')
progress=f'''## {now} R178审批显示候选原生十阶段通过，旧地址与同流程异节点不再提供审批，公网尚R33

R176原生8阶段确认原后端会拒绝提前审批（一次POST业务400/任务记录保持/引擎2待办），原前端旧地址仍显示按钮；R177候选9阶段通过；R178按流程+精确处理节点核当前用户待办，10阶段通过，包含原角色旧链接/同流程另有待办角色的异节点旧链接/一次查询503不提供审批/恢复后正常加签审批链与终态。三轮{browser_count}原生会话/{checks}检查，原六组件正常0/实际后代零、前端再假配置精确恢复、398模型/拒绝0。相对R33仅workflow/info.vue一个编译输入变化，338文件1522引用通过，源恢复；原头像/项目图标/首页与其它适配保持。

仍为本地候选：未封装新公网包/新更新器全程序与恢复预检，未上线/腾讯回填。审批前加签独立意见仍缺，真实南港全模板角色/并行附件通知仍待。原27文件248180B/106acb82待具体公开答复，固定树365ffb00/a937295c及原公开父cba03d84/4309ab94保持，新R176—R178不夹带。R33服务器旧包清理未执行；后台工作不抢桌面。8767恢复/已批准登录自启保持。完整UE/EXE GIS DLG多源标牌/Web3D/全B/S目标active，0整模块/fullCloneReady=false；详Deployment/workflow_pending_visibility_r178_20261102。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
 p=R/rel;p.write_bytes(progress.encode()+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as out:out.write(('\n\n'+progress).encode())
(R/'Document/Engine/project/workflow_pending_visibility_r178_20261102.md').write_text(progress,encoding='utf-8')
print(json.dumps({'recorded':True,'normalNativeBrowserPhases':browser_count,'checks':checks,'sourceFiles':len(sources),'candidateOnly':True,'publicInstalled':False,'old27ScopeUnchanged':True}))
