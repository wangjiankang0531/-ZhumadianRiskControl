"""Independently audit retained original-UI/SQL evidence, retire owned caches and record local acceptance."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil, subprocess, sys
sys.dont_write_bytecode = True
V = Path(__file__).resolve().parent
R = Path('D:/Project/Zhumadian'); A = R/'Application'; E = R/'XNBYEngine'; G = R/'_g/Application'
W = R/'work/original-manager-full-lifecycle-r609/feedback-r880'
D = R/'Document/Deployment/original_feedback_verified_r891_20261104'
J = lambda p: json.loads(p.read_bytes())
enc = lambda v: (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):
    return {'bytes':p.stat().st_size,'sha256':sha(p)} if p.is_file() else None
def props(p):
    return dict(s.split('=',1) for s in p.read_text('utf8').splitlines() if '=' in s and not s.startswith('#'))
def not_reparse(root):
    assert root.resolve() == root.absolute()
    for p in [root,*root.rglob('*')]:
        assert not (p.lstat().st_file_attributes & 0x400), 'REPARSE_POINT_REFUSE'
def referenced(paths):
    # Only inspect whether a selected owned directory appears; no command line is returned.
    needles = json.dumps([str(p).replace('\\','/').lower() for p in paths])
    query = "$ErrorActionPreference='Stop'; $needles=ConvertFrom-Json '"+needles.replace("'","''")+"'; $count=0; Get-CimInstance Win32_Process | ForEach-Object { $c=([string]$_.CommandLine -replace '\\\\','/').ToLowerInvariant(); foreach($n in $needles) { if($c.Contains($n)) { $count++; break } } }; $count"
    # The invoking command contains no literal needles, only this script path.
    # The child PowerShell does; omit its own PID from the selected reference scan.
    query = query.replace('Get-CimInstance Win32_Process |','Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID } |')
    p = subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode == 0, 'READ_ONLY_REFERENCE_CHECK_FAILED'
    return int(p.stdout.decode('utf-8-sig').strip())
def main():
    assert not D.exists(), 'UNISSUED_RECORD_REQUIRED'
    proof_path = R/'work/fb889/verified-feedback-chain-r889.json'; proof = J(proof_path)
    assert proof['passed'] and proof['failure'] is None and proof['actualTwoSixComponentLifecycles']
    for k in ['codeRestored','taskConfigurationRestoredBeforeCode','originalCurrentPointerRestored','originalPrivateConfigurationAndInstallationIdentityRestored','dataDirectoriesNeverClonedOrReplaced','actualOriginalManagerBusinessChainAndRestart']:
        assert proof[k], k
    for t in proof['terminals']:
        assert t['controllerExitCode']==0 and t['normalOwnedShutdown'] and t['actualJobDescendantsZero'] and not t['forceTerminationUsed']
        assert set(t['exitCodes']) == {'store','mysql','redis','platform','business','gateway'} and set(t['exitCodes'].values())=={0}
    stages=['ui-create-r887','ui-feedback-submit-r889','ui-pending-approve-r889','ui-completed-readonly-r889','ui-feedback-readonly-r889']
    ui=[]; receipts=[]
    for n in stages:
        p=W/n/'result.json'; d=J(p); terminal=J(W/n/'browser-terminal.json')
        assert d['passed'] and not d['APIsMocked'] and all(c['passed'] for c in d['cases'])
        assert terminal['normalBrowserClosed'] and terminal['exitCode']==0 and not terminal['forceTerminationUsed']
        ui.append({'stage':n,'assertionCount':len(d['cases']),'caseNames':[c['case'] for c in d['cases']],'sha256':sha(p)})
        receipts.extend([p,W/n/'browser-terminal.json'])
    made, feedback, approval, completed, reopened=[J(W/n/'result.json') for n in stages]
    assert made['taskSaveRequests']==1 and made['taskSaveConfirmed'] and not made['APIShortcutUsed']
    assert feedback['feedbackUpdateRequests']==1 and feedback['feedbackSaveConfirmed'] and feedback['approvalRequests']==0
    assert approval['approvalRequests']==1 and approval['approvalUIAccepted']
    assert completed['approvalRequests']==0 and reopened['approvalRequests']==reopened['feedbackUpdateRequests']==0
    snapshots={n:props(W/('snapshot-r889-'+n+'.properties')) for n in ['pending-resume','submitted','feedback','approved','restarted']}
    original=props(W/'snapshot-r887-submitted.properties')
    for n,s in snapshots.items():
        assert s['actualDatabaseIdentityMatched']=='true' and s['persistentWritesIssued']=='false'
        assert all(s[k]==original[k] for k in ['taskId','instanceId'])
        if n in ['pending-resume','submitted','feedback']:
            assert all(s[k]==original[k] for k in ['operatorId','engineTaskId'])
            assert s['activeEngineTasks']=='1' and s['originalProcessEnded']=='false'
        if n in ['pending-resume','submitted']: assert s['taskStatus']=='2'
        else: assert s['taskStatus']=='1' and s['originalFeedbackEvaluationTimeMatched']=='true'
        if n in ['approved','restarted']:
            assert s['activeEngineTasks']=='0' and s['originalProcessEnded']=='true' and s['ownManagerOpinionCount']=='1'
            assert all(s[k]=='true' for k in ['originalManagerOpinionPersisted','originalReadOnlyFormValuePreserved','nativeReadonlyValueSHA256Matched'])
            assert s['attemptedReadOnlyChangeCount']=='0'
        receipts.append(W/('snapshot-r889-'+n+'.properties'))
    for phase in ['first-start','normal-restart']:
        p=W/'runtime-resume-r889'/phase/'probe-terminals-r806.json'
        for t in J(p): assert t['exitCode']==0 and t['actualJobDescendantsZero'] and not t['forceTerminationUsed']
        receipts.append(p)
    journal=W/'after-submit-r889/callback-normal-restart-journal.private.properties'
    assert sha(journal)=='441a3970a72830e033a83087f3b352979354130463427c3b7207afa3b32f80b1'
    assert props(journal)['phase']=='readback-verified'
    plan=J(V/'feedback_r889/full-source-and-restore-plan.private.json')
    assert sha(V/'feedback_r889/full-source-and-restore-plan.private.json')=='9132ea7ba5a48b22f6a55fa27067c7be7bec7bbc6a869230aaaa91b3bedc9efc'
    assert pin(G/'private/server-configuration.json')==plan['configBefore']
    assert pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
    assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
    rows=dict(plan['mutations'])
    for k in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
        for n,before in plan[k].items(): assert n not in rows; rows[n]={'before':before,'after':None}
    assert all(pin(G/n)==s['before'] for n,s in rows.items()), 'INDEPENDENT_RESTORED_CODE_READBACK_REQUIRED'
    assert J(R/'work/fb889/code-transaction/journal.json')['phase']=='restored'
    # The current pointer must match the durable preimage retained by the completed transaction.
    pointer_summary=J(R/'work/fb889/pointer-snapshot/snapshot.private.json')
    assert pointer_summary['phase']=='restored' and pin(G/'UserData/OriginalServer/current-run.json')==pointer_summary['before']
    assert pin(R/'work/fb889/pointer-snapshot/before.private.json')==pointer_summary['before']
    cleanup=[R/'work/fb889/code-transaction/before']+[W/n/'chrome-profile' for n in stages if n!='ui-create-r887']
    assert all(p.is_dir() for p in cleanup)
    for p in cleanup:
        assert p.resolve().is_relative_to((R/'work').resolve()) and p.resolve()!= (R/'work').resolve(); not_reparse(p)
    before=cleanup[0]
    for f in before.rglob('*'):
        if f.is_file():
            rel=f.relative_to(before).as_posix(); assert rel in rows and pin(f)==rows[rel]['before'] and pin(f)==pin(G/rel)
    assert referenced([G,*cleanup])==0, 'OWN_PROCESSES_MUST_BE_TERMINAL_BEFORE_CLEANUP'
    cleanup_sizes=[{'path':str(p.relative_to(R)).replace('\\','/'),'files':sum(f.is_file() for f in p.rglob('*')),'logicalBytes':sum(f.stat().st_size for f in p.rglob('*') if f.is_file())} for p in cleanup]
    free_before=shutil.disk_usage(R).free
    for p in cleanup:
        assert p.resolve().is_relative_to((R/'work').resolve()); not_reparse(p); shutil.rmtree(p)
    assert all(not p.exists() for p in cleanup)
    report={'schema':'xnby.original-feedback.independent-acceptance.v1','recordedAt':datetime.datetime.now().astimezone().isoformat(),
      'passed':True,'originalTaskCreatedExactlyOnce':True,'sameTaskResumedWithoutRecreation':True,'feedbackSubmissions':1,'managerApprovalSubmissions':1,
      'UIStages':ui,'assertionCountIncludingRepeatedLoginAndReadonlyChecks':sum(s['assertionCount'] for s in ui),
      'independentSQLSnapshotsMatchedSameTaskAndInstance':True,'SQLSnapshotsUsedReadOnlyTransactions':True,
      'feedbackEvaluationDisposalTimeOriginalOpinionPersistAfterNormalRestart':True,'readonlyNativeValuePreservedIncludingAbsentNullNormalization':True,
      'twoActualSixComponentLifecyclesNormallyExited':True,'independentlyRecheckedRestoredCodeConfigurationAndInstallation':True,
      'lastVerifiedCallbackStage':'work/original-manager-full-lifecycle-r609/feedback-r880/after-submit-r889','lastVerifiedCallbackJournalSHA256':sha(journal),
      'ownedCleanup':cleanup_sizes,'observedFreeSpaceDeltaBytesNotExclusivePhysicalAttribution':shutil.disk_usage(R).free-free_before,
      'evidence':[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p)} for p in [proof_path,*receipts]],
      'normalPublicAuthenticatedNetworkTimingMeasured':False,'currentDesktopCheckFoundChromeWindowOrProcess':False,'desktopInputIssuedThisResume':False,
      'newPublicDeployment':False,'newPublicGitPush':False,'allRealNangangTemplatesAccepted':False,'fullCloneReady':False}
    text='''# 原任务创建、处置反馈、主管审批与重启回看：阶段验收（R891）

本阶段在自有隔离环境使用完整原编译页面和原SDK，通过同一条任务的真实业务链：创建一次 → 续接同一任务 → 处置反馈一次 → 主管审批一次 → 正常停止和重启 → 发起人流程详情及任务反馈详情回看。未使用接口替身或SQL写业务状态。R887创建后因探针误选只读控件中止，R889续接原任务，不能描述为一个不中断的单次运行。

五段页面结果合计33条断言，包含重复登录、静态加载和只读检查，不代表33个独立业务功能。原页面双击提交仅发出一次反馈更新，主管审批仅一次；独立只读SQL确认同任务/实例/处理节点、反馈/评估/处置时间、主管意见以及流程结束状态。原只读字段的缺失值在重开后以null规范化，原数据库和显示值仍匹配，未编造额外业务字段。

两轮真实六组件全部正常退出，实际Job后代为零；完成后代码、临时任务配置和原运行指针恢复。独立复核原配置/安装身份、全部代码前像后，仅清本轮已恢复的代码备份及4个已退出测试浏览器缓存；保留数据库、模型、任务、全部回调计划/journal、前像元数据和小型日志。逻辑清理字节与物理释放不同，不做独占归因。

最后已核回调链为feedback-r880/after-submit-r889，journal SHA256为441a3970a72830e033a83087f3b352979354130463427c3b7207afa3b32f80b1。以后续接必须核此新前像，不复用旧端口、不重发任务或审批，不覆盖旧journal。

这不是全部真实南港模板验收。事件新增/处置记录/关闭、多模板多节点、附件及真实通知、权限差异和完整系统回归仍按原清单推进。R885业务JVM原生分配失败、R886条件恢复及R887只读控件探针失败保留，不能改写为全部历史运行成功。

公网最近已核交付仍是R45；本轮仅修验证工具，没有新生产业务字节需要部署。上轮R45压缩缓存和匿名冷暖证据保持。此次用户交接后，原生窗口和进程重新检查均未找到Chrome，没有发送桌面输入，桌面已交还；公网登录后导航/API耗时尚未采到，不能宣布所有页面加载优化完成。

公网体验入口：https://www.joinlinksmart.com/zhumadian/ → 敏捷应急管理 → 我的待办/我的已办/我发起的 → 本人有权查看的详情、刷新及审批记录；应急响应管理 → 任务下达 → 任务详情。隔离环境本次合成任务未复制到公网，不要求测试者在公网寻找这条任务。需要验证真实处置/审批时，只按现有角色权限和原状态操作，不放开已完成任务的只读限制。

本阶段文档及审阅源码只追加原本地分支，不改main、不新建分支。此前153文件公开同步已完成，本轮新增验收内容尚未包含在已批准公开清单中；不宣称已推送。完整UE效果效率引擎、EXE GIS/DLG点线面图层/空间标牌多源绑定、Web3D和单系统南港B/S目标继续active，fullCloneReady=false。
'''
    D.mkdir();(D/'independent-acceptance.json').write_bytes(enc(report));(D/'阶段验收与体验说明.md').write_text(text,encoding='utf8')
    files=[]
    for rel,raw in {'tools/record_verified_feedback_r891.py':Path(__file__).read_bytes(),'deploy/verification/original_feedback_verified_r891_20261104.json':enc(report),'deploy/handbook/original_feedback_verified_r891_20261104.md':text.encode('utf8')}.items():
        q=A/rel; assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);files.append(rel)
    header='## 2026-11-04 R891：同任务反馈/主管审批及正常重启回看最终通过\n\n'
    body='独立复核R887创建1次和R889同任务反馈1次/主管审批1次，五段真实页面33断言含重复项；同库只读快照核任务/实例/反馈评估处置时间/原意见只读值持久，两六组件全0及Job零、代码配置指针恢复。仅清fb889已还原同SHA before和4个已退测试profile，保全部模型/数据/回调journal及日志；最新callback为after-submit-r889/441a3970，不用旧前像。保R885异常及R887工具失败。公网仍最后已核R45，无新生产改动；本次新交接后原生窗口/进程未见Chrome、桌面零输入且交还，登录后导航/API耗时仍待。审阅文档仅原本地Git，新公开范围未推送，不宣称真实南港全部模板/完整B/S完成。完整长期目标active/fullCloneReady=false。\n\n'
    rel='docs/project/任务反馈重启验收_20261104_r891.md'; assert not(E/rel).exists(); (E/rel).write_bytes((header+body).encode('utf8'))
    for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
        old=p.read_bytes(); assert p.read_bytes()==old; p.write_bytes((header+body).encode('utf8')+old)
    with (R/'Document/Engine/showcase_demo_completion.md').open('ab') as f:f.write(('\n'+header+body).encode('utf8'))
    spec=importlib.util.spec_from_file_location('local_r891',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    a=h.commit(A,'ecb30e822cba9d54a5fc298c13ae717762a3f886','review/workplace-r19-live-local-20261031',files,'app-r891',message_override='test: verify original task feedback, approval and persisted normal restart',update_existing=True)
    e=h.commit(E,'60d1f097e27baeba7e1994127074d4ff6448b9d9','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r891',message_override='docs: record accepted task feedback chain and unmeasured public timing',update_existing=True)
    (D/'local-review-git-r891.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False}))
    print(json.dumps({'passed':True,'assertionsIncludingRepeatedChecks':report['assertionCountIncludingRepeatedLoginAndReadonlyChecks'],'cleanupRoots':len(cleanup),'application':a,'engine':e,'publicTimingStillPending':True}))
if __name__=='__main__':main()
