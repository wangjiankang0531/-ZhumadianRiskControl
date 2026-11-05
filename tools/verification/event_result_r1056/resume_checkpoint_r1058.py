"""Complete only the verified partial R1056 document/Git checkpoint."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'
T=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,value):
    assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    transport=read(D/'verified-transport-r1057.json');full=read(T/'verified-real-apply-resume-r1053.json')
    assert transport['passed']and transport['exactNineFilesBeforeAndAfterModuleInspection']and full['passed']
    manifest=D/'delivery/delivery-manifest.json';assert sha(manifest)==transport['deliveryManifestSHA256']=='8f0d27eb66c2d4cffb317aa00dcd56c17eebb8948be27b30133253b5626797a6'
    assert len(list((D/'delivery').iterdir()))==9 and all(p.is_file()for p in (D/'delivery').iterdir())
    app=R/'Application';engine=R/'XNBYEngine';afiles=[]
    old_sources=['prepare_real_apply_bridge_r1049.py','run_real_apply_bridge_r1049.py','launch_real_apply_bridge_r1049.py','resume_real_apply_bridge_r1053.py','launch_real_apply_resume_r1053.py','build_r48_r3_transport_r1051.py','verify_r48_r3_transport_r1052.py','cleanup_real_apply_temps_r1055.py','persist_real_apply_checkpoint_r1056.py']
    source_root=app/'tools/verification/event_result_r1056'
    for name in old_sources:
        target=source_root/name;assert target.is_file()and sha(target)==sha(V/name);afiles.append(target)
    candidate=app/'deploy/public_candidates/r48_r3_20261105'
    expected={p.name for p in (D/'delivery').iterdir()if p.suffix!='.zip'}
    assert {p.name for p in candidate.iterdir()}==expected
    for name in expected:
        target=candidate/name;assert sha(target)==sha(D/'delivery'/name);afiles.append(target)
    handbook=app/'deploy/handbook/r48_r3_real_apply_and_recovery_20261105.md'
    engine_note=engine/'docs/R48第三稿_实际升级回滚验证_20261105_r1056.md'
    assert handbook.is_file()and engine_note.is_file()and(D/'固定候选说明.md').is_file()
    marker='BS_R48_R3_CHECKPOINT_RESUMED_R1058_20261105'
    addition='''2026-11-05 R1058收尾续接：R1056首次文档/源码已写，复制运输来源时误把校验生成的__pycache__目录当文件而失败，尚未创建本地提交；不是沙箱拒绝或产品/业务失败。核单个31142B pyc魔数、源时间/长度和co_filename后退役，不改载荷；新R1057关闭bytecode并在导入前后严格核恰9文件，两真实解压/全SHA和3篡改拒绝再次过，固定清单8f0d27eb保持。R1056既有文档标记/源码逐字核后只补未完成收尾，不重跑apply/恢复/回滚或重复追加旧标记；R1049汇总KeyError及R1053同一已停候选续接来源继续保留。所有G控制器/两Job已0，719代码/配置安装存储pin/原指针元数据独立复核恢复。R1055清1112代码副本逻辑111312070B/观察空闲+56123392B，R1057另清371运输文件逻辑38069812B/观察空闲+38174720B，均不独占物理归因，另小pyc退役记录保留。固定新候选/全部数据/日志失败/小型证明保持，服务器恢复材料未删。旧包Recover结果/公网恢复、第三稿上传发布/真实IIS TLS正常登录验收均未确认；新源码只在原本地分支，不混旧195公开清单。D79仅自身回执并未安装；完整长期目标active/fullCloneReady=false。
'''
    for rel in ['Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md']:
        path=R/rel;assert marker not in path.read_text('utf-8-sig')
        with path.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n<!-- '+marker+' -->\n'+addition+'<!-- '+marker+'_END -->\n')
    for path in [handbook,engine_note]:
        with path.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n'+addition)
    afiles.append(handbook)
    for name in ['verify_r48_r3_transport_r1057.py','cleanup_strict_transport_stage_r1057.py',Path(__file__).name]:
        source=V/name;ast.parse(source.read_text('utf-8'));target=source_root/name;assert not target.exists();shutil.copyfile(source,target);afiles.append(target)
    sources=[T/'prepared-r1049.json',T/'verified-real-apply-resume-r1053.json',T/'independent-restoration-r1054.json',T/'cleanup-r1055.json',
        R/'work/ua1049/actual-parent-terminal-r1049.json',R/'work/ua1049/actual-parent-terminal-r1053.json',R/'work/ua1049/failure.private.json',
        D/'prepared-r1051.json',D/'verified-transport-r1052.json',D/'verified-transport-r1057.json',D/'transport-stage-cleanup-r1057.json',
        V/'public-recovery-observation-r1048.json',V/'peer-d79-ack-r1050.json',V/'delivery-bytecode-retirement-r1057.json']
    proof_root=app/'deploy/verification/event_result_r1056'
    for source in sources:
        target=proof_root/(source.name if source.name!='failure.private.json'else'initial-harness-keyerror-r1049.json')
        dump(target,read(source));afiles.append(target)
    peer=read(V/'peer-d79-ack-r1050.json')
    assert sha(R/'Document/Coordination/交接消息/驻马店三维D79原生两端协同已验证_给驻马店3_20261105.json')==peer['handoffSHA256']
    dump(R/'Document/Coordination/交接消息/驻马店3已读D79原生协同候选_20261105_r1056.json',peer)
    stage={'r48R3PreparedAndTransportVerified':True,'files':9,'bytes':25690504,'manifestSHA256':transport['deliveryManifestSHA256'],
        'realOwnedApplyAndRecoveryAccepted':True,'originalTesterFailureAndExactResumeRetained':True,
        'independentRestorationAccepted':True,'allOwnedProcessesAndJobsTerminal':True,'closedNineFileDirectoryVerifiedAfterImport':True,
        'serverRecoveryResultReceived':False,'newPackageUploadedOrDeployed':False,'newPublicGitPushed':False,
        'serverVersionsDeleted':False,'fullCloneReady':False}
    dump(D/'publication-stage-r1058.json',stage)
    partial={'earlierCheckpointFailedBeforeGitCommit':'PermissionError copying __pycache__ directory as file',
        'fixedPayloadBytesChanged':False,'existingR1056DocsAndSourcesMatchedBeforeResume':True,'noBusinessTestsRepeated':True}
    dump(D/'checkpoint-resume-r1058.json',partial)
    spec=importlib.util.spec_from_file_location('local_review_r1058',V/'commit_r18_local_review.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    a=helper.commit(app,'0f3755af7af5e01ec24964e4f314ce0fd0805c37','review/workplace-r19-live-local-20261031',
        [str(p.relative_to(app)).replace('\\','/')for p in afiles],'app-r1058',message_override='Verify real upgrade recovery and rollback; fix and freeze separate R48 third draft',update_existing=True)
    e=helper.commit(engine,'6457748a61ea2eb77d9664122addc1abbe073cd6','review/workplace-r19-live-progress-local-20261031',
        ['docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md',str(engine_note.relative_to(engine)).replace('\\','/')],
        'engine-r1058',message_override='Record exact upgrade rollback and strict transport closure while public recovery awaits result',update_existing=True)
    receipt={'application':a,'engine':e,'stage':stage};dump(D/'local-git-completed-r1058.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
