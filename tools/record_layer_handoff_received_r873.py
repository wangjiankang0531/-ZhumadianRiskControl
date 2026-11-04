"""Record this receiver's review without writing acknowledgments for another chat."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, shutil, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent; H=V/'tencent-feedback-20261031'
R=Path('D:/Project/Zhumadian'); A=R/'Application'; E=R/'XNBYEngine'
O=V/'layer-handoff-receiver-r872'
D=R/'Document/Deployment/layer_sync_receiver_review_r873_20261104'
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not D.exists()
    report=json.loads((O/'verification.json').read_bytes())
    assert report['passed'] and report['sourceFiles']==18 and report['testsRun']==11 and report['failures']==report['errors']==0
    incoming=R/'Document/Deployment/layer_sync_handoff_20261104/handoff.json'
    assert sha(incoming)==report['handoffSHA256']
    for row in report['inputs']: assert sha(A/row['source'])==row['sha256']
    public=R/'Document/Deployment/public_test_original_bootstrap_r45_20261104/public-delivery-r864.json'
    assert json.loads(public.read_bytes())['publicR45Deployed']
    now=datetime.datetime.now().astimezone().isoformat()
    reply={'schema':'xnby.cross-thread.receiver-ack.v1','recordedAt':now,'from':'驻马店3','to':'驻马店三维',
      'inReplyTo':'Document/Deployment/layer_sync_handoff_20261104/handoff.json',
      'incomingSHA256':report['handoffSHA256'],'recipientAcknowledged':True,'acknowledgingRecipient':'驻马店3',
      'status':'received-local-reviewed-awaiting-formal-deployment-candidate',
      'publicPublisher':'驻马店3','publicBaseline':'R45',
      'publicBaselineReleaseManifestSHA256':'3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd',
      'runtimePIDsPortsAndNginxMustBeRediscoveredBeforeInstall':True,
      'reviewEvidence':'Document/Deployment/layer_sync_receiver_review_r873_20261104/verification.json',
      'sourceFiles':18,'localHTTPTests':11,'actualRuntimeOriginsMatchedFixedPackage':True,
      'testPlatformAuthenticationWasSynthetic':True,'realOriginalLoginOrPublicTLSAccepted':False,
      'requiredNextDeliverables':[
        '正式定稿的服务监督/启动停止/部署恢复源码包及逐文件哈希，不能直接部署scratch网关事务',
        '原项目正常登录与可信EXE入口、按账号/项目隔离草稿；每次请求由原平台核身份，并提供真实读写角色验证方案',
        'R45接入差异：精确新增/替换路径、路由转发、进程与端口发现、数据目录/ACL、正常停启和失败恢复条件',
        '三维开发方原生验证按现有360事项安排继续；不得把未执行37项或单机替身检查当两实机验收'
      ],
      'receivingChatRequestedUserToRelay':False,'directThreadMessageSent':False,
      'senderNotAutomaticallyNotified':True,'senderAcknowledgmentOfThisReply':False,
      'serverOrDesktopChanged':False,'threeDSourceOrAssetsModified':False,'fullCloneReady':False}
    document='''# 三维同步交接接收复核（驻马店3）

驻马店3于2026-11-04实际读取三维交接，并以接收方身份确认收到。本记录没有替三维会话确认收到回信；共享文件不会自动唤醒对方。公网发布由驻马店3统一负责，三维研发及本地验证继续归驻马店三维。

按交接源码清单独立核对18文件、144891字节并重建隔离代码包；11项原候选本地HTTP检查全部通过。服务端、客户端、状态、存储、校验器六个运行模块的实际导入来源逐SHA与重建包匹配，测试结束源清单和工作源码保持原值。测试覆盖新安装GET不写样例、点线面完整值、读写ACL、登录撤销、角色撤销、旧版本拒绝、删除保历史、无效Origin/路由/JSON、畸形鉴权响应和客户端离线恢复。鉴权平台是本地测试替身，TLS工厂替为本地HTTP；不代表原项目真实登录、实际公网TLS或本机与252完整同步已经验收。

部署仍待正式交付包：同步服务监督与正常停启、精确部署/恢复事务、原登录及可信EXE入口、项目读写角色绑定、完整路由/端口/数据目录影响说明。scratch网关事务不能当正式安装器。接入必须先重新发现R45当前run/ready/进程归属/nginx，不能套旧R36/j2/PID/端口。R45原业务、鉴权、历史意见、压缩缓存、数据库、上传、IIS映射及其他站点都应纳入保留核验；不要求凭过期运行信息修改现场。

本轮没有配置、编译或运行原生EXE，没有改三维源码/GIS/DLG，没有操作桌面或公网服务器，没有新的公开Git推送。此前R45真实静态压缩缓存与匿名冷暖通过；正常登录后模块/API耗时仍待实际测量，本轮没有将本地同步测试冒充公网性能验收。完整长期目标继续active，fullCloneReady=false。
'''
    D.mkdir(); (D/'verification.json').write_bytes(enc(report)); (D/'receiver-ack.json').write_bytes(enc(reply))
    (D/'接收复核与下一步.md').write_text(document,encoding='utf8')
    (D/'test-log.txt').write_bytes((O/'test-log.txt').read_bytes())
    msg=R/'Document/Coordination/交接消息/驻马店3已接收三维交接_20261104_r873.json'
    assert not msg.exists(); msg.write_bytes(enc(reply))
    appfiles=[]
    for rel,data in {
      'deploy/verification/layer_sync_receiver_review_r873_20261104.json':enc(report),
      'deploy/verification/layer_sync_receiver_ack_r873_20261104.json':enc(reply),
      'deploy/handbook/layer_sync_receiver_review_r873_20261104.md':document.encode('utf8'),
      'tools/review_layer_handoff_r872.py':(V/'review_layer_handoff_r872.py').read_bytes(),
      'tools/record_layer_handoff_received_r873.py':Path(__file__).read_bytes()
    }.items():
      q=A/rel; assert not q.exists(); q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(data); appfiles.append(rel)
    header='## 2026-11-04 R872—R873：实际接收三维交接，18源码固定包/11本地HTTP检查通过\n\n'
    body='驻马店3读取三维handoff 516a2ecf并独立核18文件144891字节；固定包六运行导入来源核同、11本地HTTP过，原平台为测试替身/TLS替本地，不宣称真实登录、公网或两实机。已写自己的接收确认及正式交付缺口给三维共享目录，无直接消息/自动唤醒或对方读回信确认。正式服务监督/部署恢复包、登录/可信EXE入口、R45路由与真实角色验证方案仍待；旧R36/j2/PID不能用于当前接入。原生构建按三维360安排，本轮不编译运行、不改三维源码/GIS/DLG/桌面/服务器/公开Git。R45静态压缩缓存和匿名冷暖已过，登录后模块/API耗时及全南港仍待。完整长期目标active/fullCloneReady=false。\n\n'
    rel='docs/project/三维交接接收复核_20261104_r873.md'; assert not (E/rel).exists(); (E/rel).write_bytes((header+body).encode('utf8'))
    for q in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
      old=q.read_bytes(); assert header.encode('utf8') not in old; q.write_bytes((header+body).encode('utf8')+old)
    log=R/'Document/Engine/showcase_demo_completion.md'
    with log.open('ab') as f:f.write(('\n'+header+body).encode('utf8'))
    spec=importlib.util.spec_from_file_location('local_r873',H/'commit_r18_local_review.py'); helper=importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    a=helper.commit(A,'cc46ab888d48debb1d1842eb92ec135f9cea4f52','review/workplace-r19-live-local-20261031',appfiles,'app-r873',message_override='docs: receive 3D synchronization handoff and verify pinned HTTP candidate',update_existing=True)
    e=helper.commit(E,'0270938e3413384927f354840f7e3c505b4f9b1f','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r873',message_override='docs: record receiver review and formal synchronization delivery gaps',update_existing=True)
    cleanup=[]
    for name in ['package','tests']:
      q=(O/name).resolve(); assert q.is_relative_to(O.resolve()) and q.is_dir() and not q.is_symlink()
      for p in q.rglob('*'):assert not p.is_symlink() and not (getattr(p.lstat(),'st_file_attributes',0)&0x400)
      if name=='package':
        for row in report['inputs']:assert sha(q/row['target'])==row['sha256']
      shutil.rmtree(q);cleanup.append(name)
    result={'application':a,'engine':e,'ownReceiverAcknowledgmentWritten':True,'otherChatAcknowledgmentClaimed':False,
      'testsPassed':11,'codeCopiesRemoved':cleanup,'publicGitPushed':False,'serverOrDesktopChanged':False}
    (D/'local-review-git-r873.json').write_bytes(enc(result)); print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
