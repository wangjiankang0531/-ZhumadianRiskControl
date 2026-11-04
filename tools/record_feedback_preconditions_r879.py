"""Persist next-lifecycle prerequisites; no SQL, service or public changes."""
from pathlib import Path
import ast, hashlib, importlib.util, json, shutil, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent; R=Path('D:/Project/Zhumadian'); A=R/'Application'; E=R/'XNBYEngine'
O=V/'feedback-preconditions-r878'; D=R/'Document/Deployment/feedback_original_preconditions_r879_20261104'
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not D.exists(); p=json.loads((O/'verification.json').read_bytes())
    assert p['passed'] and p['syntheticMetadataTestsPassed']==9 and p['productionJavaRowDigestParityPassed']
    assert not p['serviceStartPerformed'] and not p['databaseAccessPerformed'] and not p['callbackSQLPerformed'] and not p['taskCreateFeedbackApprovePerformed']
    assert len(p['unchangedOriginalDependencies'])==8
    for t in p['terminals']:assert t['exitCode']==0 and t['actualJobDescendantsZero'] and t['budget']['activeProcesses']==0
    for name,pin in p['actualProductionSources'].items():assert sha(Path(name))==pin
    predecessor=R/'work/original-manager-full-lifecycle-r609/task-ui-r806/normal-restart'
    assert sha(predecessor/'callback-normal-restart-journal.private.properties')==p['predecessor']['journalSHA256']
    text='''# 新自有任务反馈—审批完整联测前置核验

本阶段是原业务完整联测的前置，未提交新任务、反馈或审批，不作为完整业务链验收。上一轮R875已实际证明：已审批任务状态1隐藏处置、详情只读且反馈为空；下一轮要使用新的自有任务，按原页面允许顺序填写反馈，再经主管审批和重启回看，不能篡改上一条已完成任务。

本轮只读核对最后实际完成的回调链：task-ui-r806/normal-restart的journal SHA为6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98，phase为readback-verified，计划SHA、数据身份、原执行结果、两条17字段回调记录摘要均匹配。此记录证明历史前像，不能证明旧端口/PID仍活动，也不授权直接SQL重试；执行时必须重新核当前持有的控制器/数据库身份并比较两条记录。

旧已验运行版本与R45的固定清单中，八项原依赖（业务Jar/可移植运行定义/边界/调度隔离、平台Jar/边界/boot loader、Connector/J）哈希一致。现有自有G任务代码为OWN_FORM_CODE；纯内存计算仅把flow.event-task-handle改成tj_eventTask，其余配置值完全相同，且该配置结果与上一轮实际验过的原模型配置相同。新R45任务运行清单哈希会变化，不能拿旧releaseSHA的执行记录冒充新版本就绪，也不能绕过原执行journal对版本/目录的限制。

新增只读前像核验器拒绝错误计划/日志绑定、失败或重试的旧结果、错误阶段/发布/应用/数据目录、重复JSON/属性键、无效行标识与字段、非有限JSON、超限输入和控制字符；9项合成元数据测试通过。另在有界非终止Job内实际编译原OwnedOriginalCallbacksR648、OwnedOriginalCallbackProvisioningR659及原journal类，运行Java生产rowsSHA256，UTF8中文/null/17字段两行结果与Python核验器相同；Java仅计算摘要，没有建立JDBC连接或创建SQL意图。编译和运行均0，实际Job子进程0。

下一步应实现并核验仅针对这次固定旧→R45运行清单和新独立stage目录的执行交接，保持旧journal/计划、真实控制器与DB归属、原17字段、两行CAS、提交意图/回读和不重试约束；随后在6GiB门槛和既有有界Job内执行新任务页面创建→反馈→主管审批→回调→刷新/正常重启联测。当前尚未修改原执行器或Java journal，也未创建新执行stage、回调SQL或业务行，不能宣称该完整流程已通过。原模型/表/字段/状态未变，不需要生成数据库DDL迁移。

本轮没有服务启停、数据库访问、新原生EXE构建运行、桌面操作、公网部署或新公开Git推送。保留原任务/事件/流程/回调和全部GIS/DLG；文档及验证工具进入既有本地分支。生成class在核实际Job终态后清理。完整长期目标active，fullCloneReady=false。
'''
    D.mkdir(); (D/'verification.json').write_bytes(enc(p)); (D/'完整任务链前置与执行缺口.md').write_text(text,encoding='utf8')
    (D/'metadata-tests.log').write_bytes((O/'metadata-tests.log').read_bytes())
    files=[]
    for name in ['owned_callback_predecessor_r877.py','test_callback_predecessor_r877.py','verify_r45_feedback_preconditions_r878.py','record_feedback_preconditions_r879.py']:
      raw=(V/name).read_bytes();ast.parse(raw);q=A/'tools'/name;assert not q.exists();q.write_bytes(raw);files.append('tools/'+name)
    golden='tools/java/feedback_preconditions_r878/CallbackRowsGoldenR878.java';q=A/golden;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((O/'CallbackRowsGoldenR878.java').read_bytes());files.append(golden)
    for name,raw in {'deploy/verification/feedback_original_preconditions_r879_20261104.json':enc(p),
      'deploy/handbook/feedback_original_preconditions_r879_20261104.md':text.encode('utf8')}.items():
      q=A/name;assert not q.exists();q.write_bytes(raw);files.append(name)
    header='## 2026-11-04 R877—R879：下一原任务链前像/原依赖及生产Java行摘要核同，未业务写\n\n'
    body='只读核最后实际task-ui-r806/normal-restart journal 6d097be8，计划/原执行终态/数据与两17字段行摘要一致；新增只读核验器9合成元数据测试过，实际原Java生产rowsSHA256对中文/null行与Python同，编译/执行0和Job零。八原后端依赖在旧/R45固定清单哈希相同，仅内存计算OWN_FORM_CODE→tj_eventTask和两manifest新pin，配置与上一实际原模型相同，不写配置/运行stage/SQL。旧e957cf85执行journal与新R45任务运行SHA不同，不能复用或放宽旧路径/版本守卫；下一先实现固定版本过渡新stage执行交接，再新任务UI创建→反馈→主管审批→回调→刷新/重启联测，保全部旧记录且不重试未知提交。无服务/DB访问/业务写/桌面/公网/新公开Git/原生EXE构建运行，仅原本地Git；完整链、真实南港模板/公网登录后耗时仍待，长期目标active/fullCloneReady=false。\n\n'
    rel='docs/project/原任务反馈链前置核验_20261104_r879.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
    for q in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
      q.write_bytes((header+body).encode('utf8')+q.read_bytes())
    with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
    spec=importlib.util.spec_from_file_location('local_r879',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    app=h.commit(A,'4e70a90fccca5025084c72d1b0ea7235b4c24686','review/workplace-r19-live-local-20261031',files,'app-r879',message_override='test: validate prior callback chain and R45 original-task prerequisites without mutation',update_existing=True)
    engine=h.commit(E,'e3a6e1a4c8af50a59a84e1e18477465a42246832','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r879',message_override='docs: retain exact callback-chain prerequisite evidence and pending full business flow',update_existing=True)
    classes=(O/'classes').resolve();assert classes.is_dir() and classes.is_relative_to(O.resolve())
    for q in classes.rglob('*'):assert not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400)
    count=sum(q.is_file()for q in classes.rglob('*'));shutil.rmtree(classes)
    receipt={'application':app,'engine':engine,'metadataTests':9,'productionJavaDigestParity':True,'ownGeneratedClassFilesRemoved':count,
      'servicesOrDatabaseAccess':False,'publicOrDesktopChanged':False,'publicPushed':False,'completeBusinessFlowPassed':False}
    (D/'local-review-git-r879.json').write_bytes(enc(receipt)); print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
