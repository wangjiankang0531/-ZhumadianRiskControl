from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

R = Path('D:/Project/Zhumadian')
V = Path(__file__).resolve().parent
D = R/'Document/Deployment/public_test_event_write_results_r48_20261105'
M = 'ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a'
APP_PARENT = '0189ea18a0387ce3dc58f096487bebee3d8ca5a5'
ENG_PARENT = 'b07c00627350b4a87f77b9389378670302112c6d'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    assert not p.exists(), str(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def inspect():
    manifest=D/'delivery/delivery-manifest.json'
    assert sha(manifest)==M
    data=json.loads(manifest.read_text(encoding='utf-8-sig'))
    pins=[]
    for name,row in data['files'].items():
        p=manifest.parent/name
        assert p.resolve().parent==manifest.parent.resolve() and not p.is_symlink()
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
        pins.append({'name':name,**row})
    assert len(pins)==8
    total=sum(row['bytes']for row in pins)+manifest.stat().st_size
    assert total==25678280
    image=Path('D:/Temp/Administrator/codex-clipboard-1dd657ec-3234-4d24-9304-e99e9ea3af45.png')
    assert image.is_file()
    coord=R/'Document/Coordination/交接消息'
    peer_path=coord/'驻马店三维D78导入与新版原生验证_给驻马店3_20261105.json'
    peer=json.loads(peer_path.read_text(encoding='utf-8-sig'))
    package=Path(peer['localPackage'])
    assert sha(package/'native-editor-package.json')==peer['packageManifestSHA256']
    packaged=json.loads((package/'native-editor-package.json').read_text(encoding='utf-8-sig'))
    native=package/'bin/xnby_zmd_editor.exe'
    assert sha(native)==peer['nativeSHA256']==packaged['files']['bin/xnby_zmd_editor.exe']['SHA256']
    launcher=package/'驻马店标绘.exe'
    assert sha(launcher)==packaged['files']['驻马店标绘.exe']['SHA256']
    commits={}
    for key,repo in [('applicationCommit',R/'Application'),('engineCommit',R/'XNBYEngine')]:
        commits[key]=subprocess.check_output(['git','-C',str(repo),'rev-parse',peer[key]+'^{commit}'],text=True).strip()
        assert commits[key]==peer[key]
    return {'manifestSHA256':M,'transportFiles':9,'transportBytes':total,
        'allLocalDeliveryPinsRechecked':True,'screenshotSHA256':sha(image),
        'peerMessageSHA256':sha(peer_path),'nativePackageManifestMatched':True,
        'nativeExecutableMatched':True,'nativeRelativePath':'bin/xnby_zmd_editor.exe',
        'launcherSeparatelyMatchedManifest':True,
        'initialRootLauncherMistakenForNativeAssertionFailedBeforeAnyWrites':True,
        'peerCommitsExistLocally':commits}

def main():
    proof=inspect()
    if sys.argv[1:]!=['--persist']:
        print(json.dumps(proof,ensure_ascii=False));return
    moment=datetime.datetime.now().astimezone().isoformat()
    coord=R/'Document/Coordination/交接消息'
    preflight={'schema':'xnby.r48.user-screenshot-preflight-observation.v1','recordedAt':moment,
        **proof,'evidenceKind':'user-provided screenshot; visually reviewed in conversation',
        'serverWindowTitle':'101.201.65.94 - 远程桌面连接','selectedBase':'R45',
        'observedFinalMarker':'R48_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',
        'returnedToCommandPrompt':True,'serverPreflightFinalResultReceived':True,
        'serverScopedJSONReadbackPerformed':False,'serverDeploymentPerformedOrClaimed':False,
        'manualDeployRequestedOnce':True,'publicHTTPSAndLoggedInUIAccepted':False,
        'serverVersionsDeleted':False,'desktopInputsThisStage':False,'fullCloneReady':False}
    dump(D/'preflight-observation-r1044.json',preflight)
    cleanup_path=coord/'驻马店三维本地451项退役清理已完成_给驻马店3_20261105.json'
    cleanup=json.loads(cleanup_path.read_text(encoding='utf-8-sig'))
    readback_path=Path(cleanup['readback'])
    readback=json.loads(readback_path.read_text(encoding='utf-8-sig'))
    assert readback['deletedFiles']==451 and readback['remainingApprovedFiles']==[]
    cleanup_ack={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维',
        'recordedAt':moment,'messageSHA256':sha(cleanup_path),'senderReceiptSHA256':sha(readback_path),
        'senderReportsDeletionComplete':True,'senderDeletedFiles':451,
        'previousPendingStatusSuperseded':True,'receiverRepeatedDeletion':False,
        'receiverIndependentlyReauditedAllDeletedPaths':False,'publicChangePerformed':False}
    d78_ack={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维',
        'recordedAt':moment,'messageSHA256':proof['peerMessageSHA256'],
        'nativePackageManifestMatched':True,'nativeExecutableMatched':True,
        'sourceCommitObjectsExist':proof['peerCommitsExistLocally'],
        'senderNative37AndGPU15ReportedNotRerunByReceiver':True,
        'publicInstallationPerformed':False,'receiverExecutedNativeEditor':False,
        'remaining':['真实账号到可信EXE启动接线','现场发布身份与路由核验','公网TLS与EXE到252双机协同'],
        'R48FixedDeliveryUnchanged':True}
    ack1=coord/'驻马店3已读三维451项清理完成_20261105_r1044.json'
    ack2=coord/'驻马店3已读D78原生导入候选_20261105_r1044.json'
    dump(ack1,cleanup_ack);dump(ack2,d78_ack)
    note='''2026-11-05 R1044：用户在明确101.201.65.94远程桌面窗口手动运行R48 CheckOnly，截图含完整R48_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED并返回提示符，基线R45；不是旧R47中段。此前自动关闭窗口/FTP刷新无结果不作为失败或通过判据，现以用户截图闭合最终标志，限定JSON尚未回读。固定9文件25678280B/清单ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a再次本地逐SHA相同；已请用户只执行一次Deploy，部署与HTTPS/IIS/正常登录页面验收仍待，未声称上线/停服/服务器删除。当前仅后台文件工作，不接管桌面。195份公开同步此前已完成，本轮新增说明仅原本地分支，不混入旧公开清单。
三维最新451项退役清理完成交接及发送方readback已读，不再标待批准；未代删或重审全部删除路径。D78当前包清单及EXE SHA、两仓库提交对象核同，发送方37原生/15GPU结果只接收未重跑，未执行EXE/安装公网；真实账号可信启动、现场路由和EXE到252协同仍待。原生hold已由用户在三维会话解除，不继续当当前阻碍。R48不混入该候选，保GIS/DLG/业务库和三维当前工作。完整UE效果效率引擎、EXE GIS/DLG点线面图层/多源标牌、Web3D和单系统南港B/S目标继续active/fullCloneReady=false。
'''
    marker='BS_R48_PREFLIGHT_OBSERVED_R1044_20261105'
    for rel in ['Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md']:
        p=R/rel
        assert marker not in p.read_text(encoding='utf-8-sig')
        with p.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n<!-- '+marker+' -->\n'+note+'<!-- '+marker+'_END -->\n')
    handbook=R/'Application/deploy/handbook/event_write_results_r48_local_verified_20261105.md'
    with handbook.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n'+note)
    engine_note=R/'XNBYEngine/docs/R48_预检与三维交接_20261105_r1044.md'
    assert not engine_note.exists()
    engine_note.write_text('# R48预检与三维交接\n\n'+note,encoding='utf-8',newline='\n')
    source_target=R/'Application/tools/verification/event_result_r1029/record_r48_preflight_r1044.py'
    assert not source_target.exists()
    shutil.copyfile(Path(__file__),source_target)
    app_proof=R/'Application/deploy/verification/event_result_r1029/r48-preflight-observation-r1044.json'
    dump(app_proof,preflight)
    app_ack1=R/'Application/deploy/verification/event_result_r1029/peer-cleanup-ack-r1044.json'
    app_ack2=R/'Application/deploy/verification/event_result_r1029/peer-d78-ack-r1044.json'
    dump(app_ack1,cleanup_ack);dump(app_ack2,d78_ack)
    spec=importlib.util.spec_from_file_location('local_review_helper_r1044',V/'commit_r18_local_review.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    app=R/'Application';engine=R/'XNBYEngine'
    afiles=[str(p.relative_to(app)).replace('\\','/')for p in [source_target,app_proof,app_ack1,app_ack2,handbook]]
    efiles=['docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md',str(engine_note.relative_to(engine)).replace('\\','/')]
    a=helper.commit(app,APP_PARENT,'review/workplace-r19-live-local-20261031',afiles,'app-r1044',message_override='Record user-confirmed R48 preflight and latest peer delivery acknowledgements',update_existing=True)
    e=helper.commit(engine,ENG_PARENT,'review/workplace-r19-live-progress-local-20261031',efiles,'engine-r1044',message_override='Record R48 preflight and receive D78 without public installation',update_existing=True)
    report={'recordedAt':moment,'application':a,'engine':e,'serverDeploymentPerformedOrClaimed':False,
        'newPublicGitPushed':False,'fullCloneReady':False}
    dump(D/'local-git-completed-r1044.json',report)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
