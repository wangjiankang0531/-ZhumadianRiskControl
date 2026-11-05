from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import shutil

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'
TEST=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,value):
    assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    prepared=read(D/'prepared-r1051.json');transport=read(D/'verified-transport-r1052.json')
    full=read(TEST/'verified-real-apply-resume-r1053.json');restore=read(TEST/'independent-restoration-r1054.json');cleanup=read(TEST/'cleanup-r1055.json')
    assert full['passed']and transport['passed']and restore['successfulCIMOwnedGReferences']==0
    assert prepared['deliveryManifestSHA256']==sha(D/'delivery/delivery-manifest.json')=='8f0d27eb66c2d4cffb317aa00dcd56c17eebb8948be27b30133253b5626797a6'
    assert prepared['files']==9 and prepared['bytes']==25690504
    assert len(full['terminals'])==5 and all(t['controllerExitCode']==0 and t['allSixChildrenExitedZero']for t in full['terminals'])
    note='''2026-11-05 R1056：R48原发布失败后，后台使用既有G合成库完成真实apply_update连接点验证。R1049先启动旧R45，实际执行原apply_update复现停服/替换后static_declared同错，原recover_pending正常恢复并启动旧六组件；随后以逐字81cc5e3d修正runtime实际apply_update，正常启动新六组件、健康和原匿名HTTP通过。测试器误要求pending.completed字段发生KeyError，实际core finally写回receipt无此字段；旧失败/源码保留，不改产品迎合断言。候选及三轮控制器均正常0、Job零后，R1053仅沿同一已成功升级且已停候选续接；未重跑apply，正常启动当前候选，再执行原rollback_latest、旧R45健康和正常退出。共5轮控制器/六组件全0、两Job实零/无强杀；独立核719代码前像、3受保护配置/安装/存储pin、原指针和元数据恢复，成功CIM G零。测试入口适配仅G目标、端口和本地合成配置哈希；IIS入口为真实本机HTTP绑定，非真实IIS/TLS，未登录浏览器或提交新业务。
独立R48第三稿已固定：9文件25690504B、运输清单8f0d27eb66c2d4cffb317aa00dcd56c17eebb8948be27b30133253b5626797a6、目标release161ccba60e2258e2a65be5467c5583b2f2fa69b9f8a9febe1e7381ca296de5f9。更新器81cc5e3d与上述实际升级/回滚测试逐字相同；旧R48包不变。相对旧ZIP仅更新器、release/payload元数据和两变体清单5成员有意改变，前端业务/督办Jar/控制器/原鉴权配置数据/IIS源码字节保持。运输wrapper全部函数AST保持，仅固定常量变化，3CMD新增结束码/暂停且更名R48_R3防误点；两基线实际解压全SHA及3篡改拒绝过。24控制全图严格检查及停服前桥55过；R47仅本轮运输/严格源与继承预检来源，不冒称独立重跑其完整生命周期。第三稿未上传/部署、真实公网IIS/TLS/正常用户页面仍待。
公网最后直接观察仍502；用户固定旧R48 Recover结果尚未收到，不能宣称R45已恢复，也不能用第三稿Recover处理旧失败。已请求的旧包恢复只执行一次，后续先验恢复与精确现场身份，再按新固定范围处理第三稿，不重复Deploy/不强杀/不删服务器恢复材料。按清理skill实核两Job/CIM/源SHA/边界无重解析，仅清本轮1112自有代码副本、逻辑111312070B，同期D可用增56123392B非独占归因；保全部数据、日志/失败、小型证明和新候选。旧本地测试before已退役，不再承诺用其旧入口直接回滚。
D79来源归档10007234B及发送方7真实原生场景报告SHA、两源提交对象已独立核接收；未重跑/未安装公网，身份仍合成/本地HTTP，真实原登录/公网TLS/252仍待。195份公开同步此前已完成，本轮源码证据仅原本地分支，不混入旧公开清单、不发私有祖先。完整长期UE效果效率引擎、EXE GIS/DLG点线面图层/多源标牌、Web3D及单系统南港B/S继续active/fullCloneReady=false。
'''
    explanation='''# 固定R48第三稿候选说明

旧R48在停服和代码替换后被旧静态控制检查拒绝，新服务未启动。第三稿增加严格24控制全图桥接，并在停服前执行相同检查；没有放宽为子集检查或跳过哈希。

- 运输：9文件、25,690,504字节。
- 清单SHA256：8f0d27eb66c2d4cffb317aa00dcd56c17eebb8948be27b30133253b5626797a6。
- 更新器SHA256：81cc5e3d27062002bc18b142b577530ac940800b9e75dbc7c268f74d246a3211。
- 目标release SHA256：161ccba60e2258e2a65be5467c5583b2f2fa69b9f8a9febe1e7381ca296de5f9。
- 拟FTP目录：/Zhumadian/Zhumadian_Event_Write_Results_20261105_R48_R3/；尚未上传。
- R45为187写入+175旧应急文件移除，R47为180写入+175移除。保留原业务Jar/鉴权/历史/配置/数据库/上传/安全前端/IIS映射及其他站点；未知三维差异立即拒绝。

本轮真实G隔离测试完成原apply失败复现、recover_pending、修正后完整apply和rollback_latest。5轮六组件正常退出0，两Job实零；初次测试器completed字段KeyError及续接来源保留。IIS入口使用本机HTTP绑定，不把该结果说成真实IIS/TLS或公网角色UI验收。R47本轮完成真实运输解压，未独立重跑全生命周期。

旧R48恢复命令及结果仍属于旧固定目录；须先恢复并核实原R45可用，不能拿第三稿Recover去恢复旧包。新包应独立上传逐SHA回读，现场精确基线/运行与数据身份/就绪/Mapper/预算及同一静态控制检查通过后才能正常停启。失败只按第三稿自身updateId、前后SHA和新备份恢复，退出不明即停。CheckOnly/Deploy/Recover仍由用户在服务器手动运行；新CMD保留最后输出并显示结束码。需要桌面操作前先协调，焦点变化停止。

本候选不含公网业务测试写入、腾讯回填、公开Git或本轮服务器删除。原R48具体批准不等于已批准第三稿的新字节；尚无本稿上传/部署。公网恢复、HTTPS/压缩缓存/解压SHA、正常用户只读页面仍待；所有原数据与服务器恢复材料保留。
'''
    assert not(D/'固定候选说明.md').exists();(D/'固定候选说明.md').write_text(explanation,encoding='utf-8',newline='\n')
    marker='BS_R48_R3_REAL_APPLY_VERIFIED_R1056_20261105'
    for rel in ['Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md']:
        p=R/rel;assert marker not in p.read_text('utf-8-sig')
        with p.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n<!-- '+marker+' -->\n'+note+'<!-- '+marker+'_END -->\n')
    app=R/'Application';engine=R/'XNBYEngine'
    handbook=app/'deploy/handbook/r48_r3_real_apply_and_recovery_20261105.md'
    assert not handbook.exists();handbook.write_text('# R48第三稿与真实升级回滚验证\n\n'+note,encoding='utf-8',newline='\n')
    engine_note=engine/'docs/R48第三稿_实际升级回滚验证_20261105_r1056.md'
    assert not engine_note.exists();engine_note.write_text('# R48第三稿阶段进展\n\n'+note,encoding='utf-8',newline='\n')
    afiles=[handbook]
    source_root=app/'tools/verification/event_result_r1056';source_root.mkdir(exist_ok=False)
    for name in ['prepare_real_apply_bridge_r1049.py','run_real_apply_bridge_r1049.py','launch_real_apply_bridge_r1049.py','resume_real_apply_bridge_r1053.py','launch_real_apply_resume_r1053.py','build_r48_r3_transport_r1051.py','verify_r48_r3_transport_r1052.py','cleanup_real_apply_temps_r1055.py',Path(__file__).name]:
        source=V/name;ast.parse(source.read_text('utf-8'));target=source_root/name;shutil.copyfile(source,target);afiles.append(target)
    candidate=app/'deploy/public_candidates/r48_r3_20261105';candidate.mkdir(parents=True,exist_ok=False)
    for source in (D/'delivery').iterdir():
        if source.suffix=='.zip':continue
        target=candidate/source.name;shutil.copyfile(source,target);assert sha(target)==sha(source);afiles.append(target)
    proof_root=app/'deploy/verification/event_result_r1056'
    sources=[TEST/'prepared-r1049.json',TEST/'verified-real-apply-resume-r1053.json',TEST/'independent-restoration-r1054.json',TEST/'cleanup-r1055.json',
        R/'work/ua1049/actual-parent-terminal-r1049.json',R/'work/ua1049/actual-parent-terminal-r1053.json',R/'work/ua1049/failure.private.json',
        D/'prepared-r1051.json',D/'verified-transport-r1052.json',V/'public-recovery-observation-r1048.json',V/'peer-d79-ack-r1050.json']
    for source in sources:
        target=proof_root/(source.name if source.name!='failure.private.json'else'initial-harness-keyerror-r1049.json')
        dump(target,read(source));afiles.append(target)
    peer=read(V/'peer-d79-ack-r1050.json')
    original_peer=R/'Document/Coordination/交接消息/驻马店三维D79原生两端协同已验证_给驻马店3_20261105.json'
    assert sha(original_peer)==peer['handoffSHA256']
    dump(R/'Document/Coordination/交接消息/驻马店3已读D79原生协同候选_20261105_r1056.json',peer)
    stage={'r48R3PreparedAndTransportVerified':True,'files':9,'bytes':25690504,
        'manifestSHA256':prepared['deliveryManifestSHA256'],'realOwnedApplyAndRecoveryAccepted':True,
        'originalTesterFailureAndExactResumeRetained':True,'independentRestorationAccepted':True,
        'serverRecoveryResultReceived':False,'newPackageUploadedOrDeployed':False,'newPublicGitPushed':False,
        'serverVersionsDeleted':False,'fullCloneReady':False}
    dump(D/'publication-stage-r1056.json',stage)
    spec=importlib.util.spec_from_file_location('local_review_helper_r1056',V/'commit_r18_local_review.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    a=helper.commit(app,'0f3755af7af5e01ec24964e4f314ce0fd0805c37','review/workplace-r19-live-local-20261031',
        [str(p.relative_to(app)).replace('\\','/')for p in afiles],'app-r1056',message_override='Verify actual failed apply recovery, repaired upgrade and rollback; prepare separate R48 third draft',update_existing=True)
    e=helper.commit(engine,'6457748a61ea2eb77d9664122addc1abbe073cd6','review/workplace-r19-live-progress-local-20261031',
        ['docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md',str(engine_note.relative_to(engine)).replace('\\','/')],
        'engine-r1056',message_override='Record exact upgrade rollback proof and retain public recovery pending state',update_existing=True)
    receipt={'application':a,'engine':e,'stage':stage};dump(D/'local-git-completed-r1056.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
