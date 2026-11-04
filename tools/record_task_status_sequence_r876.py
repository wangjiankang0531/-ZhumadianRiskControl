"""Record real compiled status behavior and preserve the untested feedback chain."""
from pathlib import Path
import ast, hashlib, importlib.util, json, shutil, subprocess, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent; R=Path('D:/Project/Zhumadian'); A=R/'Application'; E=R/'XNBYEngine'
Z=R/'work/task-status-full-r875'; O=R/'work/task-status-browser-r875'
D=R/'Document/Deployment/original_task_status_sequence_r876_20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def main():
    assert not D.exists()
    proof=json.loads((Z/'verified-task-status-sequence-r875.json').read_bytes())
    browser=json.loads((O/'result.json').read_bytes())
    assert proof['passed'] and proof['codeRestored'] and proof['privateConfigurationUnchanged'] and proof['originalCurrentPointerRestored']
    assert len(proof['terminals'])==1
    for t in proof['terminals']:
      assert t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and t['normalOwnedShutdown'] and all(v==0 for v in t['exitCodes'].values())
      assert t['jobMemoryBudget']['activeProcesses']==0
    assert browser['passed'] and not browser['APIsMocked'] and browser['approvalRequests']==0 and len(browser['cases'])==15
    facts=next(x for x in browser['cases'] if x['case']=='original-approved-task-detail-keeps-same-instance-and-readonly-feedback-fields')
    assert facts['feedbackPreviouslyEmpty'] and facts['evaluationPreviouslyEmpty'] and facts['disposeTimePreviouslyEmpty']
    assert json.loads((O/'browser-terminal.json').read_bytes())['normalBrowserClosed']
    index=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/敏捷应急管理前台代码/agile-emergency-response-dev/src/views/emergencyResponse/taskSend/index.vue'
    service=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/emergencyResponse/service/impl/EventTaskServiceImpl.java'
    assert "scope.row.taskStatus!='1'" in index.read_text('utf8')
    source=service.read_text('utf8'); callback=source[source.index('public Boolean callback('):source.index('public boolean save(')]
    assert 'updateWrapper.set(EventTask::getTaskStatus, result);' in callback and all(x not in callback for x in ['setFeedbackInfo','setEvaluationSum','setDisposeTime'])
    query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
    assert p.returncode==0 and int(p.stdout.decode('utf-8-sig').strip())==0
    plan=json.loads((R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json').read_bytes())
    g=R/'_g/Application'
    for name,row in plan['mutations'].items():
      q=g/name; pin=row['before']
      assert (not q.exists()) if pin is None else (q.is_file() and q.stat().st_size==pin['bytes'] and sha(q)==pin['sha256'])
    originalSources={str(p.relative_to(R)):sha(p) for p in [index,service]}
    summary={'schema':'xnby.original-task.status-sequence.v1','passed':True,'actualUICases':15,'APIsMocked':False,
      'originalNonadminLogin':True,'samePreviouslyUIApprovedOwnedTaskAndInstance':True,'normalRestartReopen':True,
      'approvedTaskStatusOneHidesDisposal':True,'completedDetailIsReadonly':True,
      'feedbackEvaluationAndDisposalTimeRemainEmpty':True,'originalApprovalOpinionAndNativeFieldPreserved':True,
      'feedbackSubmitOrApprovalPerformed':False,'callbackRebindingPerformed':False,
      'fullFeedbackBeforeApprovalChainAccepted':False,'realNangangTemplatesAccepted':False,
      'sourceInputs':originalSources,'cases':browser['cases'],'terminals':proof['terminals'],
      'codePrivateConfigurationAndCurrentPointerRestored':True,'freshCIMOwnedGReferences':0,
      'publicOrDesktopTouched':False,'newNativeBuiltOrRun':False,'fullCloneReady':False,
      'priorR874Refusal':'Probe expected an older restoration-proof field; failed before attempt allocation, code replacement or service start; new R875 uses actual privateConfigurationUnchanged field'}
    document='''# 原任务状态、审批和反馈的验收顺序核实

本轮使用与公网R45对应的完整前端及原后端，在既有自有G环境正常启动一次六组件。合成普通账号通过真实编译登录页面访问同一条此前由真实页面创建、主管审批过的任务，完成15项检查。没有业务API替身，没有再提交审批、反馈或回调重绑，没有改变原业务行。

实际页面确认：该任务状态1；列表保留“详情”等入口，隐藏“处置”；从列表点击详情后没有judge参数、没有可编辑反馈文本框和提交按钮。反馈信息、评估总结、处置时间均仍为空；原任务/流程关联、原只读表单值和主管审批意见在正常重启后继续保留。页面刷新、发起人卡片打开和正常退出也通过。

原南港前台index.vue仅在taskStatus不等于1时显示“处置”。原EventTaskServiceImpl.callback只把传入result写到taskStatus，不填写反馈、评估、处置时间。该特定自有主管模型的通过回调返回1；不能由此声称所有真实南港模板都采用同一回调配置。

因此，“审批通过、状态1、正常重启回看”与“反馈完整业务链”是不同验收项，前者不能替代后者。本轮没有为了测通而改状态、直接强开judge入口或补造反馈。下一完整验证应新建一条自有任务，在原页面允许处置时填写反馈，再经原正常角色审批并核回调/刷新/重启后信息保持；涉及原流程模板的先后顺序还须对照真实南港配置。现有G回调链已绑定旧运行端口，后续有写测试前须按上轮已核plan/journal续接并验证R45代码基线，不能复用过期端口或覆盖已执行stage。

启动前保留6GiB物理/提交余量门槛，控制器3GiB及浏览器1GiB非终止Job。六组件正常全0、控制器0、Job实际子进程0后恢复本轮代码、私有配置和原运行指针，最终CIM核G引用0。先前R874测试器读取旧恢复字段名失败发生在分配/替换/启动之前；失败源码和记录保留，R875仅改正确字段名与新独立输出范围。测试结束仅清理本轮已核同的代码备份和浏览器profile，保留业务库、模型、回调链、日志和全部GIS/DLG。

本轮没有新的公网部署或公开Git推送，没有接管桌面，也没有原生EXE配置/编译/运行。文档和工具进入原本地分支。15项页面检查不能作为公网登录后性能或全南港验收证明；完整UE对标引擎、EXE标绘标牌、Web3D与B/S全面复刻目标继续active，fullCloneReady=false。
'''
    D.mkdir(); (D/'verification.json').write_bytes(enc(summary)); (D/'原任务状态与反馈验收顺序.md').write_text(document,encoding='utf8')
    (D/'lifecycle-result.json').write_bytes((Z/'verified-task-status-sequence-r875.json').read_bytes())
    (D/'r874-refused-before-allocation.json').write_bytes((V/'task-status-r874-refused-before-allocation.json').read_bytes())
    files=[]
    for n in ['prepare_task_status_sequence_r874.py','prepare_task_status_sequence_r875.py','verify_task_status_sequence_browser_r874.mjs','verify_task_status_sequence_browser_r875.mjs','probe_task_status_sequence_r874.py','probe_task_status_sequence_r875.py','run_task_status_sequence_r874.py','run_task_status_sequence_r875.py','task-status-source-pins-r874.json','task-status-source-pins-r875.json','record_task_status_sequence_r876.py']:
      q=A/'tools'/n; assert not q.exists(); raw=(V/n).read_bytes()
      if n.endswith('.py'):ast.parse(raw)
      q.write_bytes(raw); files.append('tools/'+n)
    for rel,raw in {'deploy/verification/original_task_status_sequence_r876_20261104.json':enc(summary),
      'deploy/handbook/original_task_status_sequence_r876_20261104.md':document.encode('utf8')}.items():
      q=A/rel; assert not q.exists();q.write_bytes(raw);files.append(rel)
    header='## 2026-11-04 R874—R876：真实已审批任务状态/只读详情15项过，反馈链不冒充完成\n\n'
    body='完整R45自有G/原SDK合成普通登录，同一真实UI已审批任务状态1、列表隐藏处置、原详情只读且反馈/评估/处置时间为空；原意见/原字段和流程关联保持。Reference前台条件与原callback仅更新status相符；只验证本自有主管模型回调1，不当真实南港全部模板。15UI过、业务/审批/反馈/SQL写和回调重绑0。R874旧恢复字段KeyError在分配前拒绝；R875只核实际privateConfigurationUnchanged证据并新输出，失败保留。六组件全0/控制器0/实际Job零，恢复本轮全部代码/私有配置/原指针，CIM G0；不强开judge、不造反馈、不改原状态。下一新自有任务按原允许处置时填写反馈，再审批/回调/刷新/重启完整联测；先核R45与上轮callback plan/journal链，旧端口stage不可复用。仅本地Git、后台，无公网/桌面/公开推送/原生编译运行。公网登录后耗时、真实南港模板及全链仍待，完整长期目标active/fullCloneReady=false。\n\n'
    rel='docs/project/原任务状态与反馈验收顺序_20261104_r876.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
    for q in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
      old=q.read_bytes();q.write_bytes((header+body).encode('utf8')+old)
    with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
    spec=importlib.util.spec_from_file_location('local_r876',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    app=h.commit(A,'1f3450ac0d7bdc843fbb8c5ba2e6eee6e3efa90d','review/workplace-r19-live-local-20261031',files,'app-r876',message_override='test: verify original approved task visibility and distinguish pending feedback workflow acceptance',update_existing=True)
    engine=h.commit(E,'57c59c15a2dff5aef0df338f6749753d29d227e6','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r876',message_override='docs: record native task status semantics and remaining complete feedback chain',update_existing=True)
    cleaned=[]
    root=Z/'code-transaction/before'
    if root.exists():
      assert root.resolve().is_relative_to(Z.resolve()) and not root.is_symlink()
      for q in root.rglob('*'):
        assert not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400)
        if q.is_file():
          rel=q.relative_to(root).as_posix();pin=plan['mutations'].get(rel,{}).get('before')
          if pin is None:pin=plan['retiredKnownFrontendPaths'].get(rel) or plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].get(rel)
          assert pin and q.stat().st_size==pin['bytes'] and sha(q)==pin['sha256'] and sha(g/rel)==pin['sha256']
      shutil.rmtree(root);cleaned.append('restored-exact-code-before')
    profile=O/'chrome-profile'
    if profile.exists():
      assert profile.resolve().is_relative_to(O.resolve()) and not profile.is_symlink()
      for q in profile.rglob('*'):assert not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400)
      shutil.rmtree(profile);cleaned.append('terminal-own-browser-profile')
    receipt={'application':app,'engine':engine,'UIcases':15,'cleanup':cleaned,'publicPushed':False,'publicOrDesktopChanged':False,'fullFeedbackChainAccepted':False}
    (D/'local-review-git-r876.json').write_bytes(enc(receipt)); print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
