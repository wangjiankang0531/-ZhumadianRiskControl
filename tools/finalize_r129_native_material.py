from pathlib import Path
import datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';E=R/'XNBYEngine';C=R/'work/event_delivery_consistency_20261030/full-controller-r129';W=R/'work/user_feedback_20261031/emergency-workflow-source-r9';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/emergency_resource_preservation_r129_20261101';D.mkdir(exist_ok=True);J=lambda p:json.loads(p.read_bytes());now=datetime.datetime.now().astimezone().isoformat()
baseline=J(C/'r5/material-browser/stale-save-baseline.json');assert baseline['falseSaveNavigatedAsSuccess']and baseline['originalActualCodeZeroFalse']
for attempt in ['r5','r6']:
 r=J(C/attempt/'result.json');assert r['allPassed']and r['allSixComponentsNormallyExitedZero']and r['original398DefinitionsUnchanged']
b=J(C/'r6/material-browser/result.json');assert b['passed']and b['productFixed']and len(b['cases'])==10
build=J(W/'independent-build-verification.json');assert build['allBuildBytesAndSourcePinsVerified']and build['undeclaredSourceDifferences']==0
proof={'schema':'xnby.r129.native-material-preserved-results.v1','at':now,'allScopedChecksPassed':True,
 'actualOriginalFalseSaveNavigatedAsSuccess':True,'actualGuardedFalseSaveKeepsEditorAndInputs':True,'actualNormalRoleBrowserCases':b['cases'],
 'nativeExportProof':J(C/'r6/material-browser/native-export-proof.json'),'allSixComponentsAndTenReadinessReportsPassed':True,
 'allStartedComponentsAndBrowsersNormallyExited':True,'original398DefinitionsUnchanged':True,'sourceOnlyThreeResourceFormsPlusFourteenOperationFilesChanged':True,
 'twoAlreadyChangedCallersComposedAndInvertedExactly':True,'restoredFourteenGuardsIndependentlyRegenerated':True,
 'buildFiles':338,'selectedSourceFiles':235,'sourceOverlayFiles':51,'assetReferences':1521,'emittedJSSyntaxFiles':173,'undeclaredDifferences':0,
 'fixtureOnlyNoFormalOrPublicBusinessDataTouched':True,'publicR24StillNotUpdatedWithThisCandidate':True,'fullMaterialModuleOrRealNangangRoleAccepted':False,
 'openGaps':['actual fast initial/query response ordering can overwrite latest UI results; not fixed','synthetic material type dictionary missing, original getInfo returns400; not a production dictionary claim','real Nangang roles and complete material CRUD/map/new-manual-add remain pending','full M02/M07 and other original modules remain pending'],
 'priorFourDriverRunsWereNotWholePasses':True,'pureSyntheticDataOnly':True,'newManualPreviewHandedOver':False}
(D/'scoped-acceptance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
doc=f'''# R129原生物资流程与既有保护恢复

更新：{now}。公网保持已验R24，本轮新修正仅在独立自有_f，未公开推送，未接手桌面，未填腾讯新完成格。完整引擎/EXE GIS/DLG/Web3D/南港B/S目标保持active，近期M02/M07，严格整模块0/8、fullCloneReady=false。旧整体百分比和工期仍撤回。

## 实际业务证据

r5在WF7上真实原SDK登录，原列表筛选、详情、编辑成功和重开后，经另一原生opener标签页删除同一合成记录，再从旧编辑页提交。服务实际返回code0/data=false，原页面仍离开编辑页并报成功；不是伪造HTTP成功。此为此前完整源码合并遗漏已有结果保护导致的回归。

r6换WF9后同一真实路径通过：code0/data=false保留编辑页和数量24并显示失败提示；取消删除0删除请求、原行保留；确认删除仅移除本轮选定合成行。筛选、重置、详情、编辑及重开、实际Chrome筛选导出10条浏览器检查通过。导出OOXML/CRC、表头和精确过滤记录数独立验证。r5/r6均实际六组件/十就绪/原398规范化定义/正常0退出、实际后代归零，无强杀。

前四次未算全通过：初始列表未稳定、隐藏筛选/导航等待、无opener标签页会话导致驱动提前或失去登录。r1同时留下真实响应乱序证据：筛选6条先返回，初始化3012条后返回覆盖表格；这项竞态没有因改驱动等待而算修复，继续待办。

## 恢复范围与来源

精确R21旧204文件公开编译快照内物资/专家/队伍各含保存结果保护，WF7全源重建丢失。本轮恢复三份原表单适配，并沿旧confirmed emergency构建链恢复业务错误码处理、三份值班保存、共享确认钩子及9个调用者，共14源。物资列表/任务列表已有WF7/WF6改动，只组合目录中精确await片段并逆回原字节，不覆盖新导入或任务状态修正。

WF8仅三资源表单源改变；WF9再加14份操作保护。14项由独立验证器从固定前像重新生成，最终235源/51覆盖、338编译文件、1521资源引用、173 JS语法、四工作流门面和声明外差异0通过。元数据缺组合后任务SHA的严格拒绝及旧日志保留，补完整前后变换链后重建并再验；未放宽不匹配。

仅自有_f在r5正常退出且实际PID消失后替换184路径、移除181旧前端，备份与精确SHA核验；三后端物资事务类沿R128保持，全部控制器/后端Jar/私有配置/数据库结构/原398定义不改。公网R24、固定交付、68待答公开源码快照、18891旧R4、8767及用户_c/_d/_e不动。_f未交给用户，六组件已停。

## 仍待

优先修复并实际重现/逆序响应回归测试列表竞态；补自有合成物资类型字典后才能验手工新增，当前getInfo400不能当生产字典问题。专家/队伍/值班仅恢复旧精确保护，尚未新增完整原生UI全链证明。真实南港定义/角色、多节点、人工处置反馈附件和其他资源流程继续待。

随后形成精确R24基线的统一新公网包，包含R128整文件事务/WF7弹窗和本轮保护，完成预检/恢复后请求该新固定载荷确认；不得借R24批准发布不同字节。68文件公开Git清单仍未答且快照不改，本轮内容不在其中。源和说明仅追加两个既有本地review；不新分支，不动正式HEAD/index和held原生代码。
'''
(D/'验证结果与下一步.md').write_text(doc,encoding='utf-8')
appfiles=['tools/verify_full_controller_material_r129_20261101.py','tools/verify_full_controller_material_browser_r129_20261101.mjs','tools/verify_owned_material_export_r129_20261101.py','tools/build_emergency_workflow_source_20261101.mjs','tools/verify_emergency_workflow_source_20261101.py']
for name in ['prepare_r129_native_material_ui.py','prepare_r129_preserved_resource_guards.py','audit_r129_retained_frontend_adapters.py','prepare_r129_full_retained_guards.py','finish_r129_source_history.py','install_owned_guard_candidate_r129.py','prepare_r129_guarded_runtime.py','add_r129_native_export.py','finalize_r129_native_material.py']:
 shutil.copyfile(V/name,T/name);appfiles.append('tools/'+name)
for folder in ['emergency-resource-preserved-guards','emergency-retained-operation-guards']:
 for p in(T/'frontend'/folder).rglob('*'):
  if p.is_file():appfiles.append(p.relative_to(A).as_posix())
for source,target in [(D/'验证结果与下一步.md','deploy/handbook/emergency_resource_preservation_r129_20261101.md'),(D/'scoped-acceptance.json','deploy/verification/emergency_resource_preservation_r129_20261101.json'),(W/'retained-operation-source-proof.json','deploy/verification/emergency_retained_operation_source_r129_20261101.json')]:
 (A/target).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,A/target);appfiles.append(target)
entry=f'''## {now} R129真实物资UI与旧保护恢复通过；响应乱序待修

完整UE对标XNBY、EXE GIS/DLG点线面样式/图层/旗杆多源标牌、Web3D及南港B/S目标active；近期M02/M07，严格0/8/fullCloneReady=false，工期旧估算仍撤回。本轮progress，公网R24未改、68公开源待答快照不改、无桌面/腾讯输入，保护用户_c/_d/_e及18891/8767。

r5真实原生SDK两页面复现删除后保存code0/false仍跳成功，证实全源合并漏保留旧保护。WF8恢复3资源表单，WF9沿旧R21构建链另恢复14份请求错误/值班/共享确认及9调用者；物资/任务已有变更精确片段组合和逆回，独立重生14项。235源/51覆盖/338输出/1521引用/173 JS/声明外0通过。严格验证先拒绝组合后SHA/元数据漏项，补全来源顺序后重建再验，不放宽。

r6_f真实登录、筛选重置、详情、编辑及重开、Chrome筛选导出、取消0删除请求、确认删除、实际false保存保留编辑页/数量24/失败提示等10项通过；r5/r6两完整六组件/十就绪/398定义一致/全部正常0退出和实际后代归零，无强杀。_f未交用户且已停；三物资事务类沿R128，原控制/Jar/配置/模型保持。前4轮驱动未全通过保留；首轮还暴露旧请求迟到覆盖新筛选的真实竞态，不把等待修正当产品修复。

下一优先原生响应逆序竞态、合成物资字典(getInfo400)及手工新增，再准备精确R24的新统一公网候选/恢复证明并阶段体验。专家队伍值班仍只有旧保护恢复，真实南港角色/定义/多节点/人工反馈附件继续待。源/文档追加既有两个本地review，公网新修正未部署，不公开推送。详细Document/Deployment/emergency_resource_preservation_r129_20261101。

'''
enginefiles=[]
for rel in ['project/htengine_goal_state.md','project/当前工作断点.md','project/测试反馈与首页适配进展_20261031.md','showcase_demo_completion.md']:
 p=R/'Document/Engine'/rel
 if 'R129真实物资UI与旧保护恢复通过'not in p.read_text(encoding='utf-8')[:200]:p.write_text(entry+p.read_text(encoding='utf-8'),encoding='utf-8')
 q=E/'docs'/rel
 if not p.samefile(q):shutil.copyfile(p,q)
 enginefiles.append('docs/'+rel)
p=R/'Document/Design/驻马店实施基线.md'
if 'R129真实物资UI与旧保护恢复通过'not in p.read_text(encoding='utf-8')[:200]:p.write_text(entry+p.read_text(encoding='utf-8'),encoding='utf-8')
p=R/'Document/Deployment/public_test_risk_r22_20261101/continuation-state.json';state=J(p);state.update({'at':now,'lastGoalTurnClassification':'progress','consecutiveNoProgressTurns':0,'lastLocalCheckpointScope':'R129 native material UI and preserved WF9 operation guards','materialWF9LocalOnly':True,'materialNativeUICases':10,'materialFalseSaveRealBaselineAndCandidateProven':True,'materialListResponseOrderingGapOpen':True,'syntheticMaterialDictionaryGapOpen':True,'ownFStoppedAndNotYetUserProtected':True,'next':'Fix actual list response ordering with real reversed responses, prepare synthetic dictionary/manual-add UI, then unified fixed R25 from public R24 with whole/recovery proof. Preserve immutable 68-file pending public snapshot and all user roots. No broad completion claims.'});p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'local-git-scope-r129.json').write_text(json.dumps({'application':sorted(set(appfiles)),'engine':enginefiles,'publicPushAuthorized':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nativeMaterialUICases':10,'oldGuardsRestored':17,'applicationLocalFiles':len(set(appfiles)),'engineFiles':4,'publicChanged':False}))
