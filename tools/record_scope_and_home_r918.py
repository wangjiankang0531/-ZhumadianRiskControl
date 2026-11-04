"""Record received component pins, remaining single-system work and tested local R46; no publish."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,importlib.util,json,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_home_transfer_r46_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
assert J(D/'verified-transport-r917.json')['passed']and J(R/'Document/Deployment/home_sparse_update_r914_20261104/verified-files-r915.json')['passed']
messages=R/'Document/Coordination/交接消息';message=messages/'驻马店三维同步服务生命周期候选_给驻马店3_20261104_d68.json';msg=J(message)
assert not msg['publicInstallRequested']and not msg['serverChangesPerformed']
for field in ['sourceArchive','runtimeArchive']:
 p=Path(msg[field]);assert sha(p.read_bytes())==msg[field+'SHA256']
 if field=='runtimeArchive':assert p.stat().st_size==msg['runtimeArchiveBytes']
 with zipfile.ZipFile(p)as z:
  assert len(z.namelist())==len(set(z.namelist()))
  if field=='runtimeArchive':
   assert set(z.namelist())==set(msg['runtimeFilePins'])
   for n,pin in msg['runtimeFilePins'].items():b=z.read(n);assert len(b)==pin['bytes']and sha(b)==pin['sha256']
for n,pin in msg['sourceFiles'].items():assert sha((A/n).read_bytes())==pin
ack={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维','receivedAt':datetime.now(timezone.utc).isoformat(),
 'message':str(message),'messageSHA256':sha(message.read_bytes()),'sourceArchiveSHA256Verified':msg['sourceArchiveSHA256'],
 'runtimeArchiveSHA256Verified':msg['runtimeArchiveSHA256'],'runtimePinsIndependentlyMatched':28,'declaredWorkingSourcePinsIndependentlyMatched':6,
 'sender165ChecksIndependentlyRerun':False,'archiveCodeExecuted':False,'publicInstalled':False,'kind':'received-review-candidate-not-install-request',
 'componentNestedWindowsJobHelperMustNotReplaceOriginalApplicationHelper':True,'existingSixComponentNoForceLifecycleRetained':True,
 'remaining':msg['remainingBeforeDeployment'],'currentPublicAssetReleaseNotChangedByThisReview':True,'directMessageOrAutomaticWakeupClaimed':False}
ackpath=messages/'驻马店3已读D68生命周期候选_20261104_r918.json';assert not ackpath.exists();ackpath.write_bytes(enc(ack))
rows=[
 {'item':'天津原功能清单去重及验收归档','state':'待闭合验收分母','remaining':'按业务实体、操作、状态和角色归并八入口；原源码与历史菜单已对齐，逐项挂接公网和本地证据，确认停用或缺父菜单。'},
 {'item':'双重预防、巡检、特殊作业、重大危险源及平台其余业务','state':'已有原页面及业务基础，深度验收不齐','remaining':'逐业务完成筛选/详情/增改删/适用导入导出/统计/权限/审批闭环；共用能力只计一次，各单据专属规则仍须单独核。'},
 {'item':'应急全事件闭环','state':'已有分阶段正常原SDK链及事件关闭证据','remaining':'全新事件一次连续走通上报、研判、派发、反馈、审批、处置和关闭，再正常重启核同记录；按252真实模板及公网实际责任角色复测。'},
 {'item':'原模板、多角色审批和表单','state':'加签意见时间已上线，退回/转审/会签/或签等已有范围测试','remaining':'逐实际南港模板核主管/部门/并行分支、节点切换、旧待办失效、原字段及回调；自建合成模型不替代真实模板验收。'},
 {'item':'预案演练、资源和值班','state':'维护与多项原生测试已通过，六类预案关联29项有证据','remaining':'适用部门/组织边界、附件和完整流程的公网正常角色复测；只验原项目实际启用功能，额外版本评审或智能扩展另列。'},
 {'item':'附件、模板、导入导出、督办PDF','state':'多类附件/下载/错误回滚已有证据；督办修正仅本地','remaining':'各适用单据附件跨提交/审批/重启/跨角色下载，以及异常格式/部分写入/中文PDF公网回归；督办文件失败修正待固定上线。'},
 {'item':'提醒与外部联动','state':'提醒入口启用范围已核，外部真实送达未验','remaining':'核252实际启用的待办提醒、Dock/Socket等接收/应答/失败处理；短信微信邮件仅在原项目确实启用时计入，不把关闭示例当缺失功能。'},
 {'item':'跨入口、权限、统计和性能回归','state':'共享系统口径已固定，R45加载优化已公网','remaining':'同记录从综合/快捷入口保持状态附件权限一致；普通/主管/不同部门统计对齐，刷新和直接地址；R46资源包待现场预检和公网冷暖实测，小脚本/API延迟及favicon404仍待。'},
 {'item':'正式交付与可复现构建','state':'多次版本及公开Git已交付，整系统签收未完成','remaining':'统一去重清单逐项签收；保留现场数据的升级恢复/版本清理；补构建依赖和部署说明，当前公开检出仍不能承诺一键完整构建。'}]
assessment={'schema':'xnby.bs.remaining-work.single-system.v1','date':'2026-11-04','scope':'天津南港B/S一套信息系统、八入口去重；三维/EXE和需求新增扩展分别验收',
 'completionPercent':None,'reason':'唯一业务分母及全部真实模板/角色验收未闭合，不重用已撤回百分比','items':rows,
 'latestPublicReleaseObserved':'R45','localHomeTransferR46PreparedNotPublished':True,'priorSixteenFeedbackIssuesTesterConfirmedResolved':True,
 'laterFeedbackSnapshotNotClaimedCurrentlyClosed':True,'fullCloneReady':False}
table='|工作项|当前状态|剩余事项|\n|---|---|---|\n'+''.join('|'+x['item']+'|'+x['state']+'|'+x['remaining']+'|\n'for x in rows)
text='# 单系统南港B/S复刻剩余工作核对（2026-11-04，R918）\n\n八入口属于同一套系统，按独立业务功能去重。当前已能使用多数原页面及核心流程；剩余同时包括具体修正上线、真实模板/角色联调、系统性回归和交付，不把未验收说成未开发。旧比例已撤回，本轮不编造新的完成率。\n\n'+table+'\n三维与EXE→公网→252协同另列；D68组件归档和28运行pin/6工作源已独立核同，仅审阅，未执行其165测试、未接线或部署。组件自带Job辅助须留独立命名空间，不覆盖原六组件Job模块。\n\nR46固定八运输文件4,015,289B、清单a31f4ee74685637fcbbb182873a366e436d592ba88ccb29bfc35d3eb4f8c392e；七写零删，正常/第四写恢复与14拒绝过，运输解压/45拒绝与22模拟响应过。模拟不当真实IIS/TLS，原完整应用18断言和真实Nginx三分辨率/缓存范围保持。第一次运输测试误核未经品牌过滤的原文件，随后HTML亦需同既有sub_filter；测试器已按原过滤规则核同响应字节，发布包未改，这两次验证失败保留。尚未上传或部署；发布前精确R45/现场控制器路由与三维差异重核，新基线未知则拒绝。没有新公开Git推送或腾讯完成回填。\n'
(D/'remaining-work-r918.json').write_bytes(enc(assessment));(D/'复刻剩余工作与R46候选状态.md').write_text(text,encoding='utf8')
files=[]
for name in ['prepare_home_sparse_r914.py','original_public_test_update_home_r46_r914.py','verify_home_sparse_r915.py','build_home_delivery_r916.py','verify_home_delivery_r917.py','record_scope_and_home_r918.py']:
 src=V/name;ast.parse(src.read_text('utf8'));dest=A/'tools'/name;assert not dest.exists();dest.write_bytes(src.read_bytes());files.append('tools/'+name)
for rel,raw in {'deploy/verification/home_sparse_r914_prepared.json':(R/'Document/Deployment/home_sparse_update_r914_20261104/prepared-sparse-r914.json').read_bytes(),
 'deploy/verification/home_sparse_r915_files.json':(R/'Document/Deployment/home_sparse_update_r914_20261104/verified-files-r915.json').read_bytes(),
 'deploy/verification/home_transfer_r46_transport_r917.json':(D/'verified-transport-r917.json').read_bytes(),
 'deploy/verification/bs_remaining_single_system_r918.json':enc(assessment),
 'deploy/verification/layer_sync_d68_received_r918.json':enc(ack),
 'deploy/handbook/bs_remaining_and_home_transfer_r918_20261104.md':text.encode('utf8'),
 'deploy/candidates/home_transfer_r46/delivery-manifest.json':(D/'delivery-manifest.json').read_bytes(),
 'tools/deploy_home_transfer_r46.py':(D/'delivery/deploy_home_transfer_r46.py').read_bytes()}.items():
 q=A/rel;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);files.append(rel)
header='## 2026-11-04 R918：B/S去重剩余工作已列；R46七写零删运输验证通过，未发布\n\n'
body='用户反馈公网加速明显且功能基本可用。按一系统去重列剩余真实模板/角色、全新事件单轮与关闭后重启、其他业务域深验、跨入口权限统计、附件通知和交付；既有闭环不退回未开发，旧比例不重用。R46八文件4015289B/清单a31f4ee7，七写零删；14文件拒绝/正常及第四写恢复过，9成员运输和45拒绝/22模拟响应过；原完整SDK18断言/Nginx像素缓存证据保持，模拟不是实际IIS。测试器前两次漏应用原品牌响应过滤失败保留、产品包未改。准备源和实际包固定，仅本地Git，无上传部署/公开推送/腾讯回填。D68两归档28运行pin/6工作源核同并写自己的回执，165测试未重跑、不安装，独立Job helper不得覆盖原六组件；仍待可信登录/角色ACL/父接线/网关CAS与两实机。现场发布需重新发现基线及三维差异，不套旧j2。hf915纯代码夹具尚待清理，无服务/网络/数据库；完整长期目标active/fullCloneReady=false。\n\n'
rel='docs/project/B_S剩余工作与首页候选_20261104_r918.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md']:p.write_bytes((header+body).encode('utf8')+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
spec=importlib.util.spec_from_file_location('local_r918',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.commit(A,'8eae54ca05d6034f614d0d76aa518069acd1300a','review/workplace-r19-live-local-20261031',files,'app-r918',message_override='docs: audit remaining single-system B/S work and verify sparse home resource transport',update_existing=True)
e=h.commit(E,'01a60f16c4bed8f96cb83140ba463f540744f0ec','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md'],'engine-r918',message_override='docs: retain full goal and record remaining B/S acceptance and received D68 candidate',update_existing=True)
(D/'local-review-git-r918.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False}));print(json.dumps({'recorded':True,'rows':len(rows),'application':a,'engine':e,'publicChanged':False}))
