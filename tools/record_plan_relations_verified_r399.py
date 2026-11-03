from pathlib import Path
import datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103';O=R/'work/plan-six-relations-ui-r398'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(D/'local-stage-files-r399.json').exists()
proof=J(D/'lifecycle-r398/verified-native-r398.json');terminal=J(O/'terminal.json')
assert proof['passed']and proof['actualNormalRoleCases']==29 and terminal['failure']is None
assert terminal['allOwnedControllerHandlesTerminal']and terminal['originalGCodeAndPointersRestored']and len(terminal['controllers'])==1
for c in terminal['controllers']:
 assert c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']
 assert all(v==0 for v in c['receipt']['exitCodesBeforeJobClose'].values())
C=R/'work/event_delivery_consistency_20261030/full-controller-r163/r157';ui=J(C/'plan-browser/result.json')
assert ui['passed']and len(ui['cases'])==29 and not ui['exceptions']
assert J(C/'browser-outer-terminal.json')['exitCode']==0 and J(C/'browser-outer-terminal.json')['actualDescendantsZero']
assert J(C/'plan-browser/browser-terminal.json')['chromeExitCode']==0
prior=R/'work/plan-six-relations-typed-r390';pt=J(prior/'terminal.json')
assert pt['allOwnedControllerHandlesTerminal']and pt['originalGCodeAndPointersRestored']and len(pt['controllers'])==3
assert all(c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']for c in pt['controllers'])
assert J(prior/'before-update-398-models.private.json')==J(prior/'after-update-398-models.private.json')==J(prior/'after-rollback-398-models.private.json')
assert J(O/'before-ui-398-models.private.json')==J(O/'after-ui-398-models.private.json')
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert sha(R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery-manifest.json')=='4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de'
assert sha(R/'Document/Deployment/public_source_plan_delivery_r369_20261103/public-git-sync-r369-manifest.json')=='c10870e318047506c1ca0de42467a4fd8be602e5f8a85d5a5f40f3a9bcfe7ed1'
cleanup=J(D/'completed-fixture-cleanup-r392.json');assert cleanup['passed']
final={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'actualNormalRoleCases':29,'caseNames':[c['case']for c in ui['cases']],
 'javascriptExceptions':0,'originalLoginAndControllersUsed':True,'allSixRelationsSavedEditedAndReadonlyValuesVerified':True,
 'memberReadonlyActualDisabledInputValuesChecked':True,'cancelConfirmDialogsClosedBeforeNextAction':True,
 'candidateR40SourceSHA256':sha(T/'original_public_test_update_r40_resource_cancel_r385.py'),
 'sameProductCandidateAcrossTestDriverCorrections':True,'r390ActualApplyAndRollbackSeparateFromR398UIIteration':True,
 'r390ThreeControllersAndR398OneControllerNormalZero':True,'original398ModelsMatched':True,'originalGCodeConfigurationAndPointersRestored':True,
 'actualGatewayGzipAndDecodedSHAPassed':J(O/'candidate-static-HTTP.json')['passed'],
 'fixtureCleanup':{k:cleanup[k]for k in ['removedFiles','logicalBytes','observedDFreeDelta','observedChangeNotUniquelyAttributed']},
 'actualIISHTTPSAndPublicTimingAccepted':False,'publicDeployed':False,'publicGitPushed':False,'fullCloneReady':False}
dump(D/'verified-stage-r399.json',final)
names=['commit_resource_cancel_stage_r384.py', 'prepare_plan_cancel_composition_r385.py', 'verify_native_plan_six_relations_cancel_r386.mjs', 'plan_cancel_inspect_r386.py', 'plan_cancel_prepare_r386.py', 'plan_cancel_run_r386.py', 'prepare_plan_cancel_resume_r387.py', 'plan_cancel_resume_r388.py', 'prepare_plan_six_relations_retry_r389.py', 'verify_native_plan_six_relations_typed_r390.mjs', 'plan_typed_inspect_r390.py', 'plan_typed_prepare_r390.py', 'plan_typed_run_r390.py', 'cleanup_plan_six_relation_fixtures_r392.ps1', 'prepare_plan_relation_ui_r393.py', 'prepare_plan_relation_ui_fixture_r394.py', 'verify_native_plan_six_relations_dialog_r394.mjs', 'plan_relation_ui_r394.py', 'prepare_plan_relation_readonly_r396.py', 'prepare_plan_relation_ui_fixture_r396.py', 'verify_native_plan_six_relations_readonly_r396.mjs', 'plan_relation_ui_r396.py', 'prepare_plan_relation_download_r398.py', 'prepare_plan_relation_ui_fixture_r398.py', 'verify_native_plan_six_relations_disk_r398.mjs', 'plan_relation_ui_r398.py', 'prepare_plan_relations_record_r399.py', 'record_plan_relations_verified_r399.py']
files=['tools/original_public_test_update_r40_resource_cancel_r385.py']
assert len(names)==len(set(names)), 'DUPLICATE_SOURCE_SCOPE'
for n in names:shutil.copyfile(V/n,T/n);files.append('tools/'+n)
vf=A/'deploy/verification/plan_six_relations_r399_20261103';vf.mkdir(parents=True,exist_ok=False)
for n in ['composition-r385.json','resume-prepared-r387.json','retry-prepared-r389.json','ui-iteration-prepared-r393.json',
 'ui-fixture-prepared-r394.json','readonly-retry-prepared-r396.json','download-retry-prepared-r398.json','verified-native-r398.json','completed-fixture-cleanup-r392.json','verified-stage-r399.json']:
 source=D/'lifecycle-r398'/n if n=='verified-native-r398.json'else D/n
 shutil.copyfile(source,vf/n);files.append((vf/n).relative_to(A).as_posix())
disk=J(C/'plan-browser/attachment-disk-evidence.json');assert disk['passed']and disk['all68BytesExactlyMatched']and disk['finalNameMatched']
dump(vf/'attachment-disk-evidence.json',disk);files.append((vf/'attachment-disk-evidence.json').relative_to(A).as_posix())
failures=[]
for root,n in [(R/'work/plan-six-relations-cancel-r386','failure.json'),(R/'work/plan-six-relations-cancel-r386','verification-failure-r388.json'),
 (R/'work/event_delivery_consistency_20261030/full-controller-r163/r151/plan-browser','failure.json'),
 (R/'work/event_delivery_consistency_20261030/full-controller-r163/r153/plan-browser','failure.json'),
 (R/'work/event_delivery_consistency_20261030/full-controller-r163/r155/plan-browser','failure.json')]:
 f=J(root/n);failures.append({k:f[k]for k in ['phase','stage','message','type']if k in f})
dump(vf/'prior-driver-failures-retained.json',{'supersededDriverFailures':failures,'candidateCodeUnchangedDuringDriverCorrections':True});files.append((vf/'prior-driver-failures-retained.json').relative_to(A).as_posix())
text=f'''## 2026-11-03 R385—R399：六类预案关联29项原生普通角色通过，R40仍待公网运输验收

资源取消修正独立组成R40：341文件前端、只改三资源组件，相对R224其余编译输入保持；更新器只变三合同常量，所有函数/类AST保持R39。两精确R36/R37旧基线独立组成同release999144eb，187写入+177移除；固定R39/公开184字节未改。本轮没有新的公网部署或公开Git。

最终r157原控制器/正常登录非管理员真实29项，0JS异常：三成员组各两行/三资源选择A+B及去重，六关联保存后原接口ID/对象回读；三成员组改一行、三资源先取消保留两行再确认只保留B、六关联编辑回读；详情逐个成员字段的禁用输入框实际值与三资源只读行均通过。继续完成演练部门筛选/重置、人员及附件、重复提交/失败保留、父删除保持子记录对象、旧详情导航/重试/刷新。完整case列表见verified-stage-r399，不将29项冒称全部南港模板/权限或每个业务字段。

R390此前同候选真实apply_update/rollback_latest三轮六组件和398模型一致，正常0/后代零；R398是其后单控制器正常启动UI迭代，不冒称该UI轮重新执行更新器事务。更新回滚轮与最终UI轮原G代码/配置/894元数据前像恢复e9dcd876；Chrome和实际后代正常退出。五个驱动问题保留：旧静态文件名、队伍flat请求不符teams/members、跨资源弹窗未等关闭、只读误查textContent、下载完成事件后未等最终文件落盘。最终分别按实际编译入口SHA、原VO、单可见弹窗完整关闭、禁用输入值及最终文件名/字节等待验证，产品候选没有为测试变更。

清理可重建代码/浏览器副本{cleanup['removedFiles']}文件项，逻辑{cleanup['logicalBytes']}B、D空闲变化{cleanup['observedDFreeDelta']}B（非独占归因）；R40原候选/编译源/小型结果/数据/上传/配置保留。实际仅回环HTTP，IIS/TLS及公网登录耗时未验收，R40完整运输/预检恢复边界和公网体验仍待。184公开候选仍原冻结范围，不含本轮R40增量。

下一先完成R40新载荷运输与限定验收，再协调公网；不静默替换已固定R39。无桌面操作、正式18891/8767或另一三维会话断点改动。完整UE效果效率引擎、EXE GIS点线面图层/多源旗杆标牌、Web3D和单系统南港B/S目标active/fullCloneReady=false；真实南港全流程/权限/跨入口仍待，不报新百分比。
'''
(D/'六类预案关联29项实际验收说明.md').write_text(text,encoding='utf-8')
hand=A/'deploy/handbook/plan_six_relations_r399_20261103.md';hand.write_text(text,encoding='utf-8');files.append(hand.relative_to(A).as_posix())
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
 p=R/rel;previous=p.read_text(encoding='utf-8');assert 'R385—R399'not in previous;p.write_text(text+'\n'+previous,encoding='utf-8')
with(R/'Document/Engine/showcase_demo_completion.md').open('a',encoding='utf-8')as f:f.write('\n'+text)
(R/'Document/Engine/project/六类预案关联29项验收_R399_20261103.md').write_text(text,encoding='utf-8')
dump(D/'local-stage-files-r399.json',{'application':files,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md',
 'docs/showcase_demo_completion.md','docs/project/六类预案关联29项验收_R399_20261103.md'],'native29Passed':True,'publicPushed':False})
print(json.dumps({'recorded':True,'nativeCases':29,'applicationFiles':len(files),'engineFiles':4,'publicDeployed':False,'publicPushed':False}))
