"""Record verified public R870 refs and shared handoff locally, without further public writes."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
V=Path(__file__).resolve().parent
H=V/'tencent-feedback-20261031'
R=Path('D:/Project/Zhumadian'); A=R/'Application'; E=R/'XNBYEngine'
D=R/'Document/Deployment/public_source_r45_delivered_r865_20261104'
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def main():
    assert not (D/'local-review-git-r871.json').exists()
    raw=(V/'public-git-completed-r870.json').read_bytes(); p=json.loads(raw)
    assert p['phase']=='completed' and p['approvedFiles']==153 and p['approvedBytes']==1577090
    assert p['approvedManifestSHA256']=='7925fa717b208b092c39007b5ed816c125e6925c2200bca38517df4cb93943a0'
    assert p['all153RemoteBlobBytesAndSHA256Matched'] and p['allPublicRefsReadBackMatched'] and p['allMainAndOtherBranchesUnchanged']
    expected=['aa64ec6a208db3cbe9209dfed3c1967451c1cab4','49a6536d527716445e7179903f6f21109fc51f8f']
    assert [x['commit'] for x in p['finalRefs']]==expected
    for x in p['finalRefs']: assert x['branchReadbackMatched'] and x['mainAndOtherBranchesUnchanged'] and not x['force']
    appfiles=[]
    def add(rel,data):
        q=A/rel; assert not q.exists(); q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(data); appfiles.append(rel)
    (D/'public-git-completed-r870.json').write_bytes(raw)
    add('deploy/verification/public-r45-source-completed-r870.json',raw)
    coord=R/'Document/Coordination/会话协作与公网发布规范.md'
    handoff=R/'Document/Coordination/交接消息/R45已上线_驻马店3致驻马店三维_20261104.json'
    j=json.loads(handoff.read_bytes()); assert not j['recipientAcknowledged']
    add('deploy/handbook/shared_session_publication_rules_20261104.md',coord.read_bytes())
    add('deploy/verification/shared_r45_handoff_pending_20261104.json',handoff.read_bytes())
    header='## 2026-11-04 R870—R871：153文件公开同步完成，公网发布统一归驻马店3\n\n'
    body=('批准清单7925fa717b208b092c39007b5ed816c125e6925c2200bca38517df4cb93943a0，153文件1577090字节；应用149份公开提交'+expected[0]+'，引擎4份公开提交'+expected[1]+'。153个远端Blob逐字节/SHA核同，完整树仅批准变化、各唯一公开父及两个原分支最终ref回读通过；main和其余分支未变，不发私有祖先、不新建分支。一次固定Blob读取失败后仅补读同一对象并核同。\n\n'
      '用户指定公网发布由驻马店3负责，已写共享协作规范、根AGENTS引导及R45交接消息。当前工具没有直接联系既有三维会话的接口，消息仍pending-recipient-read；未通知、唤醒或代写接收确认。R45重启后旧R36/j2/PID/动态端口前像不能用于三维后续发布，需重新核当前状态。本次规则/回执只入本地记录，不混入已批准153文件公开范围；不操作桌面、不修改服务器。公网R45压缩缓存和匿名冷暖已通过，正常登录后模块/API及真实南港完整验收仍待，完整长期目标active/fullCloneReady=false。\n\n')
    add('deploy/handbook/public_r45_source_sync_completed_20261104.md',(header+body).encode('utf8'))
    add('tools/record_public_completion_r871.py',Path(__file__).read_bytes())
    rel='docs/project/R45公开源码同步完成与会话分工_20261104.md'
    q=E/rel; assert not q.exists(); q.write_bytes((header+body).encode('utf8'))
    for path in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
        old=path.read_bytes(); assert header.encode('utf8') not in old; path.write_bytes((header+body).encode('utf8')+old)
    spec=importlib.util.spec_from_file_location('local_r871',H/'commit_r18_local_review.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
    a=h.commit(A,'c9d419727cfdc3445b975f747c72755a834609ce','review/workplace-r19-live-local-20261031',appfiles,'app-r871',message_override='docs: record verified R45 public source sync and pending cross-chat handoff',update_existing=True)
    e=h.commit(E,'6d756d528d183f6ea64d7bbcf85489d1ab3a6997','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md'],'engine-r871',message_override='docs: record public source sync and single publisher coordination',update_existing=True)
    result={'application':a,'engine':e,'approved153PublicSyncComplete':True,'publicCommits':expected,'additionalPublicFilesSent':0,'desktopUsed':False,'serverChanged':False,'recipientAcknowledged':False}
    (D/'local-review-git-r871.json').write_bytes(enc(result)); print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
