from pathlib import Path
import datetime,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';E=R/'XNBYEngine';V=Path(__file__).resolve().parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r130';W=R/'work/user_feedback_20261031/emergency-workflow-source-r11'
J=lambda p:json.loads(p.read_bytes());D=R/'Document/Deployment/emergency_query_and_manual_r130_20261101';D.mkdir(exist_ok=True);now=datetime.datetime.now().astimezone().isoformat()
for n in ['r1','r2','r11']:
 v=J(C/n/'result.json');assert v['allPassed']and v['allSixComponentsNormallyExitedZero']and v['original398DefinitionsUnchanged']
assert J(C/'r1/material-browser/actual-response-order-proof.json')['originalDefectReproduced']and J(C/'r2/material-browser/actual-response-order-proof.json')['candidateProtected']
b=J(C/'r11/material-browser/result.json');assert b['passed']and len(b['cases'])==8
vue=J(C/'table-hook-lifecycle-proof.json');assert vue['allPassed']and len(vue['cases'])==4
git=J(R/'Document/Deployment/public_test_unified_r24_20261101/public-git-r128-execution-r130-20261101.json');assert len(git['readbacks'])==68
preview=J(C/'material-manual-preview-r1/ready.json');assert preview['ready']
proof={'schema':'xnby.r130.query-order-native-manual-acceptance.v1','at':now,'actualOriginalResponseOrderBugReproduced':True,'candidateActualOldResponseCannotOverwriteNewResultOrLoading':True,
 'actualServerResponsesOnlyNoFulfillment':True,'actualVueLifecycleCases':vue['cases'],'nativeManualAddCases':b['cases'],
 'syntheticDictionaryExactOldRoot1000ReusedAndTwoOwnRowsAdded':True,'dictionaryNormalAPIPassedAfterFullRestarts':True,
 'realNativeMapMouseSelectionAndPersistedCoordinatesPassed':True,'baseMapImageryOrRealZhumadianGISAccepted':False,
 'exactOldPublishedSameOriginMapURLRestored':True,'originalMapCenterUnchanged':True,'threeCompleteControllerRunsPassed':True,'allStartedComponentsNormalExitNoForce':True,
 'original398DefinitionsUnchanged':True,'compiledFiles':338,'sourceInputs':235,'sourceOverlays':53,'assetReferences':1521,'JSSyntaxFiles':173,
 'publicApproved68PublishedAndReadbackPassed':True,'laterR129R130NotPublicPublished':True,'publicDeploymentInThisTurn':False,'newTencentCompletions':0,
 'completeMaterialModuleOrRealNangangRolesAccepted':False,'fullCloneReady':False,'strictCompleteModules':0}
(D/'scoped-acceptance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
doc=f'''# R130查询竞态、物资新增与公开源码同步

时间：{now}。完整UE对标XNBY/EXE GIS/DLG/Web3D/天津B/S目标active；近期M02/M07，严格0/8/fullCloneReady=false。旧整体百分比和工期不再使用。正式18891、8767及公网本轮未操作；公网最后已验R24，新候选尚未部署。

## 实际新增证明

原WF9真实原SDK登录，在服务已返回200后暂停旧列表响应，先让新筛选结果显示，再释放旧响应，稳定复现旧数据覆盖新筛选。WF10仅改共享hooks/useTable.ts：最新请求拥有行、总数、加载和回调，卸载后忽略迟到结果；其余原钩子字节可逆还原。真实两种反序通过：旧成功迟到不覆盖新结果；最新请求仍挂起时旧请求完成不清加载。没有伪造HTTP返回或用DTO替代服务。另有真实Vue渲染/卸载下4项回调、旧错误、非分页、0/false筛选边界。

WF11仅恢复旧R21已验/zhumadian/map/同域瓦片URL，保留原坐标逻辑/原中心；235源/53覆盖、338输出、1521资源引用、173 JS及声明外差异0，独立从固定前像再生请求保护和地图URL通过。原WF9操作保护、WF7导入及WF6工作流源均保留。

r11普通角色原生UI 8项通过：空表单必填不发保存、原字典接口类型下拉、真实部门树、OpenLayers原生鼠标选点并回填只读坐标、新增保存与正常API列表/详情核对、详情类型标签/数量回显、已有坐标只读查看。字段没有通过内部Vue对象/假回调设置，服务返回真实code0/data=true。字典只在未交付_f精确复用旧自建root1000(Own safety codes)，新增两行自建类型；原表结构、旧行、原398模型不改，正常全组件重启后仍可查。

r1/r2/r11三轮完整六组件/十就绪/398模型一致/正常0退出和实际后代归零通过。字典准备前几轮因旧表名及旧自建根已存在被严格拒绝，保留限定阶段/SQLState/错误码，不改原表；修正为当前原生表名并核旧夹具源码后精确复用。后续部门树DOM、地图初始画布/点击状态及嵌套字符串转义等驱动错误均保留，不算产品缺陷或通过。原生指针事件和确认按钮启用证据在r9；最终r11全链通过。

底图影像、驻马店实际GIS/默认中心仍需单独验收；当前证明是坐标选取/持久化逻辑。真实南港角色矩阵、专家队伍值班完整UI、多节点/人工处置反馈附件和其他模块仍待。

## 本机手动体验

入口：{preview['url']} 。预计到期：{preview['estimatedExpiresAt']}，到期正常停机。凭据仅见本机private文件：{preview['loginFile']}；不是公网账号。建议先按“物资名称”搜索OWN_F_MANUAL_R130_查看已保存的合成样本，再新增一条自己的测试记录、选择类型/部门/坐标、保存后重开详情。模板/导入/编辑/删除/导出可按既有阶段说明测试；本入口审批菜单不属于当前体验验收。

此为独立合成环境；不把地图底图和真实南港流程宣称通过。_f现已交用户，后续录入可能成为用户数据；禁止自动业务读取/写入/替换/清理/克隆，到期后也永久保留保护。后续自动验证必须另建未交付的自有根，不能复用_c/_d/_e/_f。

## Git实际结果

用户批准的固定68文件/533292B/清单c1be43f5…af9cba7已执行。应用公开既有review/workplace-r19-verified-partial-20261031更新9cd65bfbf869ff468cd1ae6ba1cb0714638aa04e；引擎既有review/workplace-r19-verified-progress-20261031更新8534656db7db33e849cb388653c56d35c5e6f6ba。全部68远端blob逐字节回读、完整树清单外0、唯一公开父提交、两分支/main回读均通过。未新分支、未发本地私有祖先，后续R129/R130源码不在冻结公开快照中。

本轮新源和说明仅追加既有本地review。下一优先准备精确R24的新统一公网包，合并已验事务/保存保护/查询修正/同域URL，完成完整运行/恢复证明及具体范围确认再上线。不得借R24或68源码批准发布不同载荷。腾讯本轮新增标记0。
'''
(D/'验证结果与手动体验.md').write_text(doc,encoding='utf-8')
appfiles=['tools/original_table_request_order_compat.py','tools/verify_full_controller_material_r130_20261101.py','tools/verify_full_controller_material_browser_r130_20261101.mjs','tools/verify_full_controller_material_add_browser_r130_20261101.mjs','tools/install_owned_table_order_candidate_r130_20261101.py','tools/install_owned_map_candidate_r130_20261101.py','tools/java/material_full_controller_r1/OwnMaterialDictionaryFixture.java','tools/serve_material_manual_preview_r130_20261101.py','tools/build_emergency_workflow_source_20261101.mjs','tools/verify_emergency_workflow_source_20261101.py']
for name in ['verify_r130_table_hook_lifecycle.mjs','prepare_r130_table_request_order.py','prepare_r130_map_and_manual_host.py','extend_r130_independent_source_verifier.py','finalize_r130_query_and_manual.py']:
 shutil.copyfile(V/name,T/name);appfiles.append('tools/'+name)
for folder in ['emergency-table-request-order','emergency-map-same-origin']:
 for p in(T/'frontend'/folder).rglob('*'):
  if p.is_file():appfiles.append(p.relative_to(A).as_posix())
for source,target in [(D/'验证结果与手动体验.md','deploy/handbook/emergency_query_and_manual_r130_20261101.md'),(D/'scoped-acceptance.json','deploy/verification/emergency_query_and_manual_r130_20261101.json'),(C/'table-hook-lifecycle-proof.json','deploy/verification/table_hook_lifecycle_r130_20261101.json')]:
 (A/target).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,A/target);appfiles.append(target)
entry=f'''## {now} R130查询反序修复与原生新增通过；68公开同步完成/物资体验已开

完整UE对标XNBY渲染效果效率、EXE GIS/DLG点线面/样式/图层/旗杆多源标牌、Web3D及南港B/S目标保持active；近期M02/M07、严格0/8/fullCloneReady=false，旧工期估计仍撤回。本轮progress。

共享useTable旧请求盖新筛选以真实服务响应暂停/释放稳定复现；WF10只改一钩子，最新请求拥有行/总数/加载/回调，卸载忽略迟到。两真实响应反序、4真实Vue生命周期边界通过。WF11另只恢复旧R21已验同域/zhumadian/map/URL，保留原中心/坐标逻辑。235源/53覆盖/338文件/1521引用/173 JS/声明外0及独立再生通过。r11原生普通角色必填、类型、部门树、真实鼠标选坐标、保存和列表详情/类型回显、只读坐标共8项通过；r1/r2/r11三完整六组件十就绪/398模型/全部正常0退出/后代0，无强杀。

字典只精确复用旧自建root1000+新增两行，当前原生表名；早期严格拒绝、DOM/鼠标/转义驱动失败均保留，不算产品缺陷/全通过。底图影像/驻马店实际GIS与原中心仍待，专家队伍值班/真实南港角色/多节点/人工反馈附件等继续。

固定68文件获明确批准并公开同步完成，逐blob/整树/唯一公开父/分支及main回读通过：应用9cd65bfb、引擎8534656d，不新分支、不发私有祖先；R129/R130新内容仅本地。公网最后已验R24，本轮无部署/桌面/腾讯新增标记，正式18891/8767未操作。

新_f物资体验session35334，入口{preview['url']}，预计{preview['estimatedExpiresAt']}正常停。账号只在本机private文件，不入Git。_f已交用户，永久禁止自动业务读写/替换/清理/克隆，与_c/_d/_e共同保护；下一自动测试须另建未交付自有根。详细Deployment/emergency_query_and_manual_r130_20261101。下一准备精确R24的新统一公网包/完整运行和恢复证明，不借旧清单授权。

'''
enginefiles=[]
for rel in ['project/htengine_goal_state.md','project/当前工作断点.md','project/测试反馈与首页适配进展_20261031.md','showcase_demo_completion.md']:
 p=R/'Document/Engine'/rel
 if 'R130查询反序修复与原生新增通过'not in p.read_text(encoding='utf-8')[:200]:p.write_text(entry+p.read_text(encoding='utf-8'),encoding='utf-8')
 q=E/'docs'/rel
 if not p.samefile(q):shutil.copyfile(p,q)
 enginefiles.append('docs/'+rel)
p=R/'Document/Design/驻马店实施基线.md'
if 'R130查询反序修复与原生新增通过'not in p.read_text(encoding='utf-8')[:200]:p.write_text(entry+p.read_text(encoding='utf-8'),encoding='utf-8')
p=R/'Document/Deployment/public_test_risk_r22_20261101/continuation-state.json';state=J(p);roots=state.get('protectedUserManualRoots',[])
if str(R/'_f/Application')not in roots:roots.append(str(R/'_f/Application'))
state.update({'at':now,'lastGoalTurnClassification':'progress','consecutiveNoProgressTurns':0,'publicGitPushed':True,'laterR129R130ChangesPublished':False,'materialListResponseOrderingGapOpen':False,'syntheticMaterialDictionaryGapOpen':False,'materialNativeManualAddPassed':True,'materialBaseMapAndActualZhumadianGISGapOpen':True,'ownFStoppedAndNotYetUserProtected':False,'materialUserPreviewFHandedOver':True,'protectedUserManualRoots':roots,'manualMaterialPreview':str(C/'material-manual-preview-r1/ready.json'),'manualMaterialPreviewExecSession':35334,'lastLocalCheckpointScope':'R130 real list response ordering/manual add and approved68 public publication','next':'Prepare fixed R25 from public R24 using immutable WF11 and material classes; never auto-read/write/replace/clean/clone user_c/d/e/f even after expiry. Fresh automated fixture must be an unhanded root. Full deployment/recovery proof before new approval. Real Nangang definitions/roles/full M02/M07 and actual GIS remain incomplete.'})
p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'local-git-scope-r130.json').write_text(json.dumps({'application':sorted(set(appfiles)),'engine':enginefiles,'newLocalChangesPublicPushed':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nativeManualCases':len(b['cases']),'newLocalAppFiles':len(set(appfiles)),'engineFiles':4,'manualURL':preview['url'],'expires':preview['estimatedExpiresAt'],'public68Done':True,'newCandidatePublicInstalled':False},ensure_ascii=False))
