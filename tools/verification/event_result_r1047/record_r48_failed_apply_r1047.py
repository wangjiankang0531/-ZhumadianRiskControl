from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shutil

V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian')
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,value):
    assert not p.exists(),str(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    manifest=D/'delivery/delivery-manifest.json'
    assert sha(manifest)=='ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a'
    focused=json.loads((V/'static-control-bridge-r1046/focused-verification.json').read_bytes())
    assert focused['passed']and focused['focusedChecks']==55 and not focused['actualApplyUpdateSixComponentLifecycleTestPerformed']
    image=Path('D:/Temp/Administrator/codex-clipboard-44aec7d8-4d1b-4d44-8d99-9acd87ec92ac.png')
    assert image.is_file()
    rows=json.loads((V/'r48-public-entry-observation-r1045/measurements.json').read_bytes())
    assert len(rows)==1 and rows[0]['status']==502
    moment=datetime.datetime.now().astimezone().isoformat()
    report={'schema':'xnby.r48.failed-apply-observation.v1','recordedAt':moment,
        'userScreenshotSHA256':sha(image),'selectedBase':'R45','preflightPassed':True,
        'deploymentAttemptedByUser':True,'deploymentSucceeded':False,
        'exception':'R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED',
        'tracebackFunction':'apply_update -> static_performance_declared',
        'phaseFromExactPinnedSource':'after replace_code and codeApplied assignment; before launch',
        'replacementAndShutdownNotIndependentlyReadBackFromServerJSON':True,
        'externalHomeObservation':rows[0],'externalServiceRecovered':False,
        'originalFailureReproducedFromActualR48ReleaseMetadata':True,
        'fixedCandidateFocusedChecks':55,'complete24ControlMapRetained':True,
        'candidateLifecycleEndToEndAccepted':False,
        'manualRecoverRequestedOnce':True,'manualRecoveryResultReceived':False,
        'oldPackageOrBackupsDeleted':False,'fixedR48TransportChanged':False,
        'newPublicSourcePushed':False,'fullCloneReady':False}
    dump(D/'failed-apply-observation-r1047.json',report)
    dump(D/'static-control-bridge-focused-r1046.json',focused)
    note='''2026-11-05 R1047事件：用户在服务器执行固定R48 Deploy，最终失败而非已上线。截图含STOP与UPDATE_STOPPED；堆栈冻结core.apply_update第3395行static_performance_declared，异常R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED。按该精确源码顺序，此点位于正常旧服务退出、replace_code和codeApplied赋值后、新launch之前；尚未下载服务器原始JSON，不冒称已独立回读完整运行报告。外网匿名首页实际502，不把预检成功当发布成功。已请求用户仅运行一次固定Recover_This_Event_Write_Results_R48.cmd，沿原本次updateId/旧新SHA/本次备份恢复R45；恢复结果与外网200尚待，禁止重跑Deploy或先删旧包/本次before。没有强杀、绕GUI命令限制或操作业务库。
根因已以真实包内release元数据复现：旧static_declared只识别旧控制组合，遗漏新增督办控制桥；此前实际替换/恢复与六组件启动分别通过，没有覆盖apply_update完整连接点，这是本次验证缺口。隔离候选在wrapper增加严格24控制全图检查，并前移同一检查到候选preflight；55定向接受/漂移/缺失/额外控制拒绝过，冻结core/normal_stop/apply/recover函数体保持。仍未做实际完整apply_update生命周期，不当完整升级通过；候选未外发、未改固定R48包，后续修正包须独立固定与既有授权边界处理。
195份公开同步此前完成，本轮失败与修正来源仅原本地分支。D78已独立核包清单/主EXE与两源提交并回执，三维451清理完成已接收；不把其新EXE或本地清理结果当公网安装/EXE到252验收。完整UE效果效率引擎、EXE GIS/DLG图层多源标牌、Web3D及单系统南港B/S继续active/fullCloneReady=false。
'''
    marker='BS_R48_FAILED_APPLY_R1047_20261105'
    for rel in ['Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md']:
        p=R/rel;assert marker not in p.read_text(encoding='utf-8-sig')
        with p.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n<!-- '+marker+' -->\n'+note+'<!-- '+marker+'_END -->\n')
    handbook=R/'Application/deploy/handbook/event_write_results_r48_local_verified_20261105.md'
    with handbook.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n'+note)
    enote=R/'XNBYEngine/docs/R48_发布失败与恢复待验_20261105_r1047.md'
    assert not enote.exists();enote.write_text('# R48发布失败与恢复待验\n\n'+note,encoding='utf-8',newline='\n')
    ack={'schema':'xnby.cross-thread.public-incident.v1','from':'驻马店3','to':'驻马店三维',
        'recordedAt':moment,'publicReleaseAcceptance':False,'failedCandidate':'R48','recoveryTarget':'R45',
        'normalRecoveryRequested':True,'recoveryCompleted':False,'externalHomeStatusObserved':502,
        'new3DDeploymentOrOverwritePerformed':False,'fixedR48PackageChanged':False,
        'message':'R48本次升级失败，恢复待验；三维继续本地研发，公网现场基线应等待驻马店3后续实际恢复回执。'}
    dump(R/'Document/Coordination/交接消息/驻马店3_R48发布失败恢复待验_20261105_r1047.json',ack)
    app=R/'Application';engine=R/'XNBYEngine'
    base=app/'tools/verification/event_result_r1047';base.mkdir(exist_ok=False)
    afiles=[handbook]
    for source in [Path(__file__),V/'prepare_static_control_bridge_r1046.py',V/'verify_r48_external_static_r1045.py',V/'static-control-bridge-r1046/r48_update_runtime.py']:
        target=base/source.name;shutil.copyfile(source,target);afiles.append(target)
    for name,value in [('r48-failed-apply-r1047.json',report),('static-control-bridge-focused-r1046.json',focused),('public-incident-peer-notice-r1047.json',ack)]:
        target=app/'deploy/verification/event_result_r1047'/name;dump(target,value);afiles.append(target)
    spec=importlib.util.spec_from_file_location('local_git_helper_r1047',V/'commit_r18_local_review.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    a=helper.commit(app,'55fb2d1dab0ebcd3c3f40819feaec8d8da43d6ef','review/workplace-r19-live-local-20261031',
        [str(p.relative_to(app)).replace('\\','/')for p in afiles],'app-r1047',
        message_override='Record failed R48 post-replacement check and uninstalled exact-control repair',update_existing=True)
    e=helper.commit(engine,'550c5123441770d6c44b16f7bd10b25bbbe298f0','review/workplace-r19-live-progress-local-20261031',
        ['docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md',str(enote.relative_to(engine)).replace('\\','/')],
        'engine-r1047',message_override='Record R48 failed apply and pending normal recovery without claiming deployment',update_existing=True)
    receipt={'application':a,'engine':e,'failedR48Accepted':False,'recoveryResultReceived':False,'fullCloneReady':False}
    dump(D/'local-git-completed-r1047.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
