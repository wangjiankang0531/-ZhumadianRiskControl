"""Save real failures, source corrections and current owned run without claiming acceptance."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine'
D=R/'Document/Deployment/original_feedback_checkpoint_r890_20261104';W=R/'work/original-manager-full-lifecycle-r609/feedback-r880'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
J=lambda p:json.loads(p.read_bytes())
def main():
 assert not D.exists()
 first=J(R/'work/fb880/verified-feedback-chain-r880.json');recover=J(R/'work/ep885/verified-recovery-r886.json')
 made=J(W/'ui-create-r887/result.json');prior=J(R/'work/fb887/verified-feedback-chain-r887.json');diagnostic=J(R/'work/event-picker-browser-r885/result.json')
 assert not first['passed']and first['codeRestored']and first['taskConfigurationRestoredBeforeCode']and first['originalCurrentPointerRestored']
 assert recover['passed']and recover['codeRestored']and recover['originalCurrentPointerRestored']and recover['normalSixComponentExitClaimed']is False
 assert made['passed']and made['taskSaveRequests']==1 and made['taskSaveConfirmed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']
 assert diagnostic['passed']and diagnostic['diagnosticCompleted']and diagnostic['taskSaveRequests']==diagnostic['researchRequests']==0
 full=diagnostic['queryDiagnostics'][0];assert full['domValueMatches']and full['query']['eventNameEqualsExpected']and full['query']['exactOwnedEventPresent']and full['direct']['ownEventPresent']and full['gateway']['ownEventPresent']
 ackPath=R/'Document/Coordination/交接消息/驻马店三维已读R45及r873回执_20261104_d66.json';ack=J(ackPath)
 assert ack['senderReadAndAcknowledged']and ack['publicPublisher']=='驻马店3'and not ack['serverChanged']
 for name,pin in ack['receivedBytesSHA256'].items():assert sha(ackPath.parent/name)==pin
 codeFiles=[]
 for dirname in ['feedback_r880','feedback_r887','feedback_r889','event_picker_r885']:
  for p in (V/dirname).iterdir():
   if p.is_file()and p.suffix in ['.py','.mjs','.java']:codeFiles.append((p,'tools/experimental_source/'+dirname+'/'+p.name))
 for name in ['prepare_feedback_runtime_r880.py','prepare_feedback_browser_r880.py','prepare_feedback_probe_r880.py','check_feedback_sources_r881.py','prepare_event_picker_diagnostic_r883.py','prepare_event_picker_retry_r884.py','prepare_event_picker_observation_r885.py','recover_event_picker_r886.py','prepare_feedback_resume_r887.py','prepare_existing_task_feedback_r889.py','check_feedback_sources_r889.py','record_feedback_checkpoint_r890.py']:
  codeFiles.append((V/name,'tools/'+name))
 for p,rel in codeFiles:
  if p.suffix=='.py':ast.parse(p.read_bytes(),filename=rel)
 active=J(R/'work/fb889/controller-handles.private.json');assert active['pids']==[26724,45944]
 stage=J(W/'runtime-resume-r889/first-start/business-result-r880.json');assert stage['passed']and stage['originalFeedbackEvaluationAndTimePersisted']and stage['actualOriginalManagerApprovalUI']
 summary={'schema':'xnby.original-feedback.checkpoint.v1','recordedAt':datetime.datetime.now().astimezone().isoformat(),
  'R880TaskSaveRequests':0,'R880CallbackStageCommittedAndVerified':True,'R880CodeConfigurationPointerRestored':True,
  'R883ProbeRefusedOldFixtureBeforeBrowser':True,'R884ProbeInspectedBeforeFirstPickerResponse':True,
  'R885CompletedReadOnlyDiagnostic':True,'fullSpacedNameMatchesDOMQueryDirectAndGateway':True,
  'broadQueryPageOneAbsenceDoesNotProveDataMissing':True,'queryDiagnostics':diagnostic['queryDiagnostics'],'encodingVariants':diagnostic['variants'],
  'R885BusinessNativeMemoryFailureAndConditionalRecovery':recover,
  'R887CreatedExactlyOneOriginalTask':True,'R887FeedbackUpdateRequests':J(W/'ui-feedback-submit-r880/result.json')['feedbackUpdateRequests'],
  'R887CodeConfigurationPointerRestored':True,'R887ReadonlyFieldWasSelectedByProbeNotProductFailureProven':True,
  'lastVerifiedCallbackBeforeR889':'work/original-manager-full-lifecycle-r609/feedback-r880/normal-restart',
  'lastVerifiedCallbackBeforeR889JournalSHA256':'234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc',
  'R889ObservedControllerPIDs':active['pids'],'R889ExecSession':90110,'R889WasLiveWhenObserved':True,
  'R889FirstFeedbackAndManagerApprovalStagePassed':True,'R889NormalRestartStillPending':True,
  'R889FullChainAcceptanceNotClaimed':True,'R889RestoreOrCleanupBeforeActualTerminalForbidden':True,
  'threeDSharedReplyActuallyReadAndItsTwoReceivedHashesMatched':True,'threeDReplySHA256':sha(ackPath),
  'publicEmergencyAuthenticatedHomeObserved':True,'publicAuthenticatedNetworkTimingCollected':False,
  'computerUseEndedBecauseBrowserURLCouldNotBeDeterminedReliably':True,'desktopReturned':True,
  'newPublicDeploymentOrPush':False,'fullCloneReady':False,
  'sourceReviewFiles':[{'target':rel,'bytes':p.stat().st_size,'sha256':sha(p)}for p,rel in codeFiles]}
 text='''# 原任务反馈联测断点与已核事实（R890）

本记录保留实际失败和已形成的数据，不宣称完整任务链已通过。完整UE对标引擎、EXE GIS标绘/图层/空间标牌、多源绑定、Web3D和单系统南港B/S全面复刻目标继续active。

R880使用固定R45自有任务运行清单，原模型两回调检查/提交/回读成功；原UI事件筛选处探针超时，任务与研判提交均0。两合成用户的临时主管关系已恢复；六组件正常0后代码/配置/原指针恢复。R883诊断器旧flight目录引用在浏览器分配前拒绝，R884又在首个事件响应返回前检查了默认空数组；这些是工具失败，不能当成产品筛选结论，原记录均保留。

R885明确等待真实响应后，完整18字符事件名称在输入框、实际请求、原业务端口和网关均匹配同一自有事件。单词/空查询第一页有10条而未包含该事件，不证明数据消失。原接口和网关的%20编码查询通过；末尾+编码原接口通过、网关502与业务JVM退出相邻，不能据此断言URL编码是根因。业务JVM的hs_err证明原生malloc分配32744字节失败；原控制器3GiB预算接近此前峰值，是否唯一成因未证明。所有原PID与G引用均0、ready/receipt归属绑定后，R886仅用本轮SHA/备份恢复代码/私有配置/原指针，保留业务退出1，不宣称正常六组件全0，不强杀、不重启或替换数据库。

R887将测试控制器预算改4GiB，同时把物理和提交余量门槛提高7GiB；产品字节与原R45保持，仅自有任务代码指向原模型。在新的未执行回调stage回读成功后，已通过真实普通账号页面创建同一flight的新任务一次。反馈探针随后选择了基础信息内同名只读控件，更新请求0；原Detail/index.vue本来就以disabled el-form渲染基础信息，不能改其只读属性来过测试。六组件均0并恢复代码/配置/原指针。

R889续接这条已创建任务，没有重建。探针只定位可见、未禁用、非readonly且唯一的原编辑控件；只读SQL确认任务/实例/处理节点与R887一致，在未执行after-submit-r889目录核最后234781eb journal后重绑回调，现已实际各提交一次反馈与主管审批，原意见/字段/反馈时间回读通过。第一控制器26724已正常停止，已观察到父exec session 90110进入第二轮正常重启、控制器45944；重启回看尚未验收。本文件不是进程活动证明，恢复时必须poll同一真实handle或重新核终态，不能凭文件/PID重启、恢复或清理。各issued/result/journal记录都要核，未知提交只能回读。

三维会话D66已经独立确认读到R45和r873回执，两个接收SHA与原文件一致；现在共享文件交接已有双方实际读取，仍无直接线程消息/自动唤醒。公网统一由驻马店3发布，三维正式接入包尚未交付，不部署scratch。

原生Computer Use只读看到公网首页→敏捷应急管理已登录首页、项目新图标及三个个人流程入口；工具因无法可靠识别Windows浏览器URL自动结束，已交还桌面，没有继续操作或采得网络耗时。本阶段没有新的公网部署、公开Git推送或原生EXE构建；公网登录后耗时、真实南港模板/多节点/附件通知及完整验收仍待。源码存档是实际路径及依赖的审阅输入，不宣称公开干净检出一键完整构建。
'''
 D.mkdir();(D/'checkpoint.json').write_bytes(enc(summary));(D/'原任务反馈联测断点.md').write_text(text,encoding='utf8')
 files=[]
 for p,rel in codeFiles:
  q=A/rel;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());files.append(rel)
 for rel,raw in {'deploy/verification/original_feedback_checkpoint_r890_20261104.json':enc(summary),'deploy/handbook/original_feedback_checkpoint_r890_20261104.md':text.encode('utf8')}.items():
  q=A/rel;assert not q.exists();q.write_bytes(raw);files.append(rel)
 receipt={'schema':'xnby.cross-thread.receiver-read.v1','from':'驻马店3','to':'驻马店三维','inReplyTo':str(ackPath.relative_to(R)),
  'replySHA256':sha(ackPath),'receiverReadAndVerified':True,'bothOriginalReceivedHashesMatched':True,'publicPublisher':'驻马店3','directThreadMessageSent':False,'publicChanged':False}
 (R/'Document/Coordination/交接消息/驻马店3已读D66回信_20261104_r890.json').write_bytes(enc(receipt))
 header='## 2026-11-04 R880—R890：任务已真实创建一次；R889同任务反馈/审批续接正在运行\n\n'
 body='已保存R880事件选择探针失败/回调提交成功，R883旧fixture、R884响应前空数组失败；R885只读完整名称DOM/API/网关同一事件，宽查询页一缺目标非丢数据。末尾业务JVM原生分配32744B失败/退出1，R886归属/所有原PID与G引用0后条件恢复代码/配置/原指针，不冒称正常。R887预算4GiB且物理/提交门槛7GiB，真实UI创建1次，反馈探针选只读基础信息控件故更新0；原Detail disabled守卫保持，六组件全0/恢复过。R889用未执行after-submit-r889续同一任务，没有再创建；首轮实际反馈1和主管审批1已过/原意见字段反馈时间回读匹配，26724正常全0；实际session90110已观察进入第二轮重启45944，重启回看尚待。此断点不算活动证明，续接必须poll真handle/核ready/receipt/各issued状态，未终态不恢复/清理。正式18891/三维/public业务保持。D66三维回信2SHA核同，已双方共享读取，无直发/自动唤醒。公网实际正常登录应急首页可见，原生CUA URL识别策略结束后已交还，未采网络耗时。仅原本地Git，R889全链/真实模板/公网耗时未接受，完整长期目标active/fullCloneReady=false。\n\n'
 rel='docs/project/原任务反馈联测断点_20261104_r890.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
 for q in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:q.write_bytes((header+body).encode('utf8')+q.read_bytes())
 with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
 spec=importlib.util.spec_from_file_location('local_r890',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 a=h.commit(A,'160245367f201d758baf643c951cedba8ab61bbd','review/workplace-r19-live-local-20261031',files,'app-r890',message_override='test: retain original task creation, diagnostic failures, exact recovery and live feedback continuation',update_existing=True)
 e=h.commit(E,'c74534ed09fc73ce63bb190d0d1c761ded7f4c04','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r890',message_override='docs: retain real workflow checkpoint and confirmed cross-chat handoff',update_existing=True)
 (D/'local-review-git-r890.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False,'R889AcceptanceClaimed':False}));print(json.dumps({'application':a,'engine':e,'sourceReviewFiles':len(codeFiles),'publicPushed':False}))
if __name__=='__main__':main()
