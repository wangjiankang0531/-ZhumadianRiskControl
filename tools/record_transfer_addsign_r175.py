from pathlib import Path
import ast,datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_transfer_addsign_r171_20261102'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=datetime.datetime.now().astimezone().isoformat()
assert not D.exists();D.mkdir()
phases={};trials={};case_count=0;normal_browsers=0
for trial in ['r71','r72','r73','r74','r75']:
    root=C/trial;terminal=read(root/'controller-terminal.json');outer=read(C/(trial+'-outer-terminal.json'));restored=read(C/('prepared-'+trial)/'configuration-restored.json');receipt=read(root/'scoped-controller-receipt.json')
    assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and restored['exactOriginalBytesRestored']
    assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and not receipt['jobAssignmentFailureComponents']
    assert set(receipt['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
    for suffix in ['schema-after.json','schema-fresh-after.json']:assert read(root/suffix)==read(R/'work/event_delivery_consistency_20261030/full-controller-r131/schema-before.json')
    assert read(root/'schema-after.json.capacity.json')['Connection_errors_max_connections']==0
    rows=[]
    for folder in sorted(root.glob('workflow-browser-*')):
        if not folder.is_dir():continue
        t=read(folder/'browser-terminal.json');assert t['normalBrowserClosed']and t['chromeExitCode']==0 and not t['forceTerminationUsed'];normal_browsers+=1
        passed=(folder/'result.json').exists();p=read(folder/('result.json'if passed else'failure.json'));case_count+=len(p['cases']);rows.append({'phase':folder.name.removeprefix('workflow-browser-'),'passed':passed,'checks':len(p['cases']),**({'failure':p['message']}if not passed else{})})
    if trial in ['r71','r74','r75']:assert read(root/'result.json')['allPassed']and outer['exitCode']==0
    else:assert outer['exitCode']==1
    phases[trial]=rows;trials[trial]={'normalSixComponentsAndAllActualDescendantsZero':True,'allOriginal398ModelsUnchanged':True,'syntheticConfigurationRestoredExactBytes':True,'phaseResults':rows,'actualExecutedHostSHA256':sha(root/'actual-host-source.py'),'actualExecutedBrowserSHA256':sha(root/'actual-browser-source.mjs')}
assert len(phases['r71'])==7 and all(x['passed']for x in phases['r71'])
assert len(phases['r72'])==7 and sum(x['passed']for x in phases['r72'])==6
assert read(C/'r72/workflow-browser-operator-completed-readback/failure.json')['message']=='ORIGINAL_TRANSFER_RECORD_ACTOR_TIME_AND_OPINION_REQUIRED'
assert read(C/'r73/workflow-browser-reviewer-addsign/failure.json')['message']=='ORIGINAL_TRANSFER_POST_MUST_SUCCEED_ONCE'
rejected=read(C/'r73/workflow-browser-reviewer-addsign/failure.json');posts=[x for x in rejected['http']if'/FlowBefore/freeApprover/'in x['path']];assert len(posts)==1 and posts[0]['httpStatus']==200 and posts[0]['businessCode']==400
assert '或签节点不需要进行后加签'in read(C/'r73/workflow-browser-reviewer-addsign/owned-page-diagnostic.private.json')['text']
assert (C/'r74/workflow-context.private.json').read_bytes()==(C/'r72/workflow-context.private.json').read_bytes()
before=read(C/'r74/workflow-browser-operator-completed-readback/addsign-sequence-and-opinion-observation.json');after=read(C/'r75/workflow-browser-operator-completed-readback/addsign-sequence-and-opinion-observation.json')
assert before['addsignType']=='1'and before['actualAddedAndFinalReviewRecordsAndOrderMatched']and before['originalReviewerAfterAddedVerified']and before['opinionRetentionGapRemains']
assert after['addsignType']=='2'and after['actualAddedAndFinalReviewRecordsAndOrderMatched']
node=[x for x in read(C/'r75/workflow-browser-reviewer-addsign/result.json')['cases']if x['case']=='actual-provider-node-sign-type-before-addsign'];assert len(node)==1 and node[0]['counterSign']==1
for trial in ['r71','r72','r74','r75']:
    final=read(C/trial/'state-reviewer-final.json')if trial!='r74'else read(C/trial/'state-operator-completed-readback.json');assert final['passed']and final['pendingEngineTasks']==0 and final['originalEngineHistoryHasEndTime']
sources=['prepare_transfer_r171_20261102.py','verify_full_controller_transfer_r171_20261102.py','verify_native_transfer_browser_r171_20261102.mjs','run_transfer_r171_20261102.py','prepare_addsign_r172_20261102.py','verify_full_controller_addsign_r172_20261102.py','verify_native_addsign_browser_r172_20261102.mjs','run_addsign_r172_20261102.py','correct_addsign_observer_r172.py','prepare_addsign_completed_readback_r174.py','prepare_after_addsign_positive_r175.py','configure_owned_countersign_r175.py','inspect_addsign_provider_r172.py']
pins={}
for name in sources:
    source=V/name;target=A/'tools'/name;assert not target.exists()
    raw=source.read_bytes()
    if name.endswith('.py'):ast.parse(raw,filename=name)
    shutil.copyfile(source,target);pins['tools/'+name]={'bytes':len(raw),'sha256':sha(target)}
gaps=['审批前加签意见未作为独立历史记录保留；本轮只定位到原SDK写入原操作者记录，后续同人审批后该意见不可见，尚未修复。','未验证审批前加签期间原审批人提前操作是否被系统严格阻止；已按预期先后顺序实际执行。','自建两级模板/两普通角色/68字节PNG的隔离验证，真实南港全部模板、角色、并行/通知及其它附件仍待。','未在公网提交转审或加签测试业务；公网仍R33，本轮没有产品代码或发布包变更。','R33旧版本清理仍未执行，需桌面协调或实际可用受限后台发布通道。']
proof={'schema':'xnby.original-transfer-addsign-r175.verified-partial.v1','at':now,'nativeBrowserPhasesExecuted':normal_browsers,'recordedChecksAcrossPassingAndFailedPhases':case_count,'trials':trials,'transferFlowPassed':True,'beforeAddsignCoreSequencePassed':True,'beforeAddsignSameCompletedInstanceReadbackAfterRestartPassed':True,'afterAddsignCountersignCoreSequencePassed':True,'orSignAfterAddsignOriginalRejectionPreserved':True,'beforeOpinionObservation':before,'afterOpinionObservation':after,'original398DefinitionsUnchangedAllTrials':True,'normalSixComponentsAllTrials':True,'credentialsOrRawBusinessRowsExported':False,'desktopInputSent':False,'productCodeChanged':False,'publicVersion':'R33','publicDeploymentOrTencentWritePerformed':False,'fullAddsignFeatureAccepted':False,'fullCloneReady':False,'remainingGaps':gaps,'legacyR74HostCreateFlagNotUsedAsEvidence':'R74 only executed one readback phase; inherited generic host flags do not prove fresh creation or fresh approval.'}
(A/'deploy/verification/original_transfer_addsign_r175_20261102.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'verified-result.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
text=f'''# 原生转审与加签阶段结果（2026-11-02，R171—R175）

本阶段只在自有 `_g` 合成环境使用原六组件、原审批引擎、原登录及普通角色页面；没有修改产品/原 SDK、正式业务库或公网 R33，也没有桌面输入。

| 分支 | 实际结果 | 验收边界 |
|---|---|---|
| 转审 | 原人员选择器搜索选择另一角色，一次转审成功；原角色重新登录待办列表不含该任务，接收角色继续首审、末级审批完成 | 同一事件/任务/流程/附件/处置反馈保持；引擎待办0、历史结束 |
| 审批前加签 | 被加签人先审、原审批人接续、末级完成；正常重启后回看同一已完成实例，意见/时间/操作者匹配实际 DTO | 加签动作的独立意见未保留，不能标整项完整通过；未测试原审批人提前操作的强制阻止 |
| 或签节点审批后加签 | 原服务 HTTP200/业务400，页面明确“或签节点不需要进行后加签” | 保留原框架限制，首轮错误正向假设及失败完整保存 |
| 会签节点审批后加签 | 本轮自建首节点 counterSign=1，实际 provider 返回同值；原加签、接收人及末级实际审批完成 | 仅该自建模型和两普通角色，非全部真实南港模板 |

共执行 {normal_browsers} 次原生角色浏览器会话，记录 {case_count} 项检查（含失败阶段此前已完成检查，不冒充全通过数）。r71为7阶段转审；r72六阶段通过后末尾“独立加签意见必须存在”的假设失败；r73或签后加签被原服务拒绝；r74只重启回看r72同一已完成实例，不重建/重放审批；r75为会签审批后加签。r72/r73的失败保留，不能将整轮记首轮通过。

每轮所有六组件、Chrome、控制器正常退出，实际 Job 后代为零后关闭；假配置及两份清单精确恢复，398个原模型一致、连接拒绝0。首轮通用宿主字段在r74会留下创建字样，实际执行只有1次只读回看；聚合验收按实际阶段/请求/同实例SHA判断，不采信该泛化字段。

审批前独立意见缺口：原 SDK 的 freeApprover 接口会设置原操作者记录的 handleOpinion；该角色后续再次审批后，最终记录显示后续审批意见，没有独立加签动作历史。本轮通过只读原class方法调用及实际页面回看定位，尚未修改原SDK或新增审计表。后加签意见实际观察：{after['independentAddsignOpinionRetained']}。不得删除此缺口来获得全绿，也不将未上传新业务的公网称全流程已验收。

体验位置（公网现有R33）：首页“敏捷应急管理/应急处置”对应入口 → 审批管理 → 待办事宜 → 打开有权限的待办 → 操作“转审/加签” → 选择人员并提交。加签类型由节点配置约束；请使用专门测试流程，转审/加签会真正改变待办。此路径为原页面入口说明，本轮没有代用户在公网提交测试业务。

证据：`Document/Deployment/original_transfer_addsign_r171_20261102/verified-result.json`，执行原记录保留于 `work/event_delivery_consistency_20261030/full-controller-r163/r71` 至 `r75`；源码逐SHA见同证据目录 source-pins.json。公开干净检出一键完整构建仍未达成，所需原SDK/资产不外发。后续优先补审批前意见独立留痕与提前审批控制，再逐真实南港模板验收。完整UE引擎/EXE GIS DLG/多源旗杆标牌/Web3D/全南港B/S目标保持 active，fullCloneReady=false。
'''
(A/'deploy/handbook/original_transfer_addsign_r175_20261102.md').write_text(text,encoding='utf-8');(D/'原生转审加签验证与剩余问题.md').write_text(text,encoding='utf-8')
progress=f'''## {now} 原生转审与加签正向/原限制核对，独立意见留痕缺口保留

R171转审7阶段通过；R172审批前加签按预期先加签人再原审批人再末级完成，但独立加签意见未保留，末尾断言失败保留；R173或签后加签原服务拒绝“或签节点不需要进行后加签”，不放宽限制；R174正常重启仅回看R172同一已完成实例并核实际记录顺序，不重建/重放；R175自建会签节点counterSign=1且实际provider核同，审批后加签正向完成。{normal_browsers}原生角色浏览器会话，原六组件/后代零/假配置恢复/398模型/无连接拒绝均核验。原SDK方法读查显示意见写在原操作者记录，后续同人审批后独立意见不见，尚未产品修复；提前审批的强制阻止、真实南港全部模板角色/并行通知/其它附件仍待。fullAddsignFeatureAccepted=false/fullCloneReady=false。

本轮仅自有_g合成环境，正式/公网R33/三维8767/资产保持，桌面交还；R170当前账号登录自启已安装并验证复用，未来实际登录触发仍待。R33退役包/旧代码清理未执行，不能记已删。新源/验收先同步既有本地review，旧48公开头cba03d84/4309ab94保持，后续新公开范围需逐文件核验，不发私有祖先。详细Deployment/original_transfer_addsign_r171_20261102与Application/deploy/handbook/original_transfer_addsign_r175_20261102.md。完整长期UE效果效率/EXE GIS DLG多源空间标牌/Web3D/全南港B/S目标active，0整模块，不覆盖另一三维会话专属断点。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;p.write_bytes(progress.encode()+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as out:out.write(('\n\n'+progress).encode())
(R/'Document/Engine/project/original_transfer_addsign_r175_20261102.md').write_text(progress,encoding='utf-8')
print(json.dumps({'recorded':True,'normalRoleBrowserPhases':normal_browsers,'checksIncludingFailedAttempts':case_count,'originalSourceFiles':len(sources),'independentBeforeOpinionGapRemains':True,'fullCloneReady':False,'publicChanged':False}))
