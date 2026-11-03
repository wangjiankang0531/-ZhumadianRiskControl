from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_product_verified_r272_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert not D.exists();runs={}
for attempt in ['r131','r132']:
 root=C/attempt;prep=C/('prepared-'+attempt);result=J(root/'result.json');outer=J(C/(attempt+'-outer-terminal.json'));receipt=J(root/'scoped-controller-receipt.json');scope=J(prep/'mapper-product-scope.json')
 assert result['allPassed']and result['original398ModelsUnchanged']and result['connectionCapacityWithoutRefusals']and outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose']and not outer['forceTerminationUsed']
 assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 for name in ['frontend-restored.json','mapper-observer-restored.json','mapper-product-restored.json','history-runtime-restored.json','configuration-restored.json']:assert J(prep/name)['passed']
 report=J(root/'actual-mapper-registration.json');assert report['allFactoriesHaveEveryOriginalXMLStatement']and report['expectedOriginalXMLStatements']==226 and report['originalXMLResources']==96 and report['factoryCount']==1
 assert scope['newFiles']['tools/original_server_release_parameters.py']['sha256']==sha(A/'tools/original_server_release_parameters_r263_mapper_default.py')
 if attempt=='r131':
  browser=J(root/'plan-browser/result.json');assert result['actualR263ParameterFileUsedWithoutExplicitMapperSetting']and browser['passed']and len(browser['cases'])==11 and not browser['exceptions'];cases=browser['cases']
  assert scope['newFiles']['tools/original_public_test_update.py']['sha256']==sha(A/'tools/original_public_test_update_mapper_runtime_r265.py')
 else:
  assert result['actualProductParameterAndFinalRuntimeAdapterUsed']and result['actualExecutedNativeBrowserPhases']==9 and result['actualAll226OriginalXMLStatementsRegistered']
  assert scope['newFiles']['tools/original_public_test_update.py']['sha256']==sha(A/'tools/original_public_test_update_mapper_runtime_r268.py')
  labels=['operator','operator-disposal','reviewer-preview','operator-added','operator-waiting-parallel-b','reviewer-after-added','reviewer-final','reviewer-handled-readback','operator-completed-readback'];cases=[]
  for label in labels:
   browser=J(root/('workflow-browser-'+label)/'result.json');terminal=J(root/('workflow-browser-'+label)/'browser-terminal.json');assert browser['passed']and not browser['exceptions']and terminal['normalBrowserClosed']and terminal['chromeExitCode']==0 and not terminal['forceTerminationUsed'];cases.append({'phase':label,'passed':True})
 runs[attempt]={'result':result,'normalSixExitCodes':receipt['exitCodesBeforeJobClose'],'allActualDescendantsZeroAndOriginalBytesRestored':True,'cases':cases,'actualProductSourcePins':{n:p for n,p in scope['newFiles'].items()if n.startswith('tools/')}}
original=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256'];assert sha(R/'_g/Application/release-manifest.json')==original
boundaries=J(R/'Document/Deployment/original_mapper_runtime_declarations_r269_20261103/result.json');assert boundaries['passed']and len(boundaries['cases'])==13 and boundaries['updaterSourceSHA256']==sha(A/'tools/original_public_test_update_mapper_runtime_r268.py')
failed=J(R/'Document/Deployment/original_mapper_runtime_declarations_r267_20261103/failure.json');assert failed['case']=='pool-policy-missing'
proof={'schema':'xnby.r272.actual-product-mapper-lifecycle.v1','runs':runs,'finalDeclarationBoundaryChecks':boundaries,'priorDeclarationCheckFailurePreserved':failed,'actualProductParameterFileFullLifecyclePassed':True,'finalRuntimeAdapterHealthAndDeclarationsValidatedAgainstActualSixComponents':True,'newUpdaterApplyUpdateAndRollbackTransactionsExecuted':False,'temporaryConfigurationDidNotInjectMapperSetting':True,'originalJarSQLAuthAnd398ModelsKept':True,'publicTransportBundleAndCombinedStaticPerformanceAcceptanceStillPending':True,'newProductPublicDeployed':False,'fullNangangAcceptancePassed':False,'fullCloneReady':False}
put(D/'verified-result.json',enc(proof));put(A/'deploy/verification/mapper_product_lifecycle_r272_20261103.json',enc(proof))
text='''# 原SQL默认扫描产品代码完整运行（R265—R272，2026-11-03）

已补齐上一阶段缺少的产品代码实际运行。r131安装精确R263参数源（b804d7e2）和R265严格运行声明适配器，测试配置没有显式Mapper位置；实际产品materialize默认补原xml目录，运行工厂226条原SQL全部注册，预案/演练11浏览器阶段、原398模型、连接容量通过。六组件/Chrome正常0、实际后代零，前端→观察Jar/classpath→产品参数/声明→历史模块/虚构配置的本轮链逐字恢复，原_g基线已核同。

R267负面声明检查发现单独调用runtime_pool_declared时，新Mapper声明存在但池声明缺失未立即拒绝。失败在纯元数据检查中发现，未部署公网，原证据保留。R268在该入口先核严格Mapper声明，最终相对R37仅四个原声明选择/校验函数变化，所有停启/备份/替换/恢复函数AST保持。R269十三项有效旧/新声明与缺失、伪造、丢任务类、池/历史边界全部通过。

r132实际运行最终R268文件与同一R263产品参数代码，配置仍没有显式Mapper注入，运行工厂96资源/226语句全部注册、缺失0。R224候选下任务真实上传中阻止提交、保存中再点击仅一次请求、处置反馈、两个独立审批分支等待/推进、末级/已办回看及原锚点下载九阶段通过。原398模型与容量通过，普通并行审批未产生非目标加签记录；原六组件和九Chrome正常0、实际后代零，所有自有代码/配置精确恢复。参数文件已有真实六组件运行证据，最终运行声明模块已对该运行执行健康/身份/声明核验；新更新器的apply_update与回滚事务本轮尚未执行。

限制：运行声明适配器只完成新参数源/旧工作流/池预算/历史声明兼容；新的公网运输范围与完整替换/恢复组合尚未实现和验证，不可作为可发布更新器使用。R37静态性能仍仅已上传/预检过、无部署完成回执；后续需把已验证业务修正、整体Mapper默认加载和性能控制合成固定候选，验证精确原版本、全部文件边界、停服前预算、正常/故障恢复与HTTPS，再协调发布。现有固定R37授权不自动覆盖新包；本轮未改公网、正式18891、三维8767/资产或桌面。公开Git固定30仍待答，新增本方源码/说明先保存既有本地分支。

226是原XML语句数，不是业务功能数；本阶段不声称226条SQL全部被业务调用，也不声称全部真实南港模板/权限/通知或整系统验收。完整UE效果效率引擎、EXE GIS/DLG点线面图层旗杆标牌、多源绑定、Web3D与单系统多入口B/S复刻目标继续active/fullCloneReady=false，另一三维会话专属断点保持。
'''
put(D/'阶段说明.md',text.encode());put(A/'deploy/handbook/mapper_product_lifecycle_r272_20261103.md',text.encode());put(R/'Document/Engine/project/原SQL产品代码运行R272_20261103.md',text.encode())
entry='''## 2026-11-03 R272：实际产品参数及最终声明适配器完整运行通过，公网组合运输待完成

r131精确R263参数源/无显式Mapper注入，226原SQL全注册、预案演练11阶段/398模型/容量通过；r132最终R268声明文件同源实际六组件，226全注册、任务上传保护/一次保存/反馈/双分支至末级已办附件九阶段通过。两轮六组件/Chrome正常0/后代零，前端/观察/产品参数声明/历史/虚构配置清单精确恢复，_g原e9dcd876。session29023/1255终态0不可再轮询。R267缺池声明未立即拒绝的纯检查失败保留；R268仅新增该入口严格校验、R269十三边界通过。最终源码各有完整生命周期，不再仅渲染/AST来源；但新增公网运输合同/完整替换故障恢复和R37性能组合尚未实现/验，运行适配器不可直接发布。下一完成固定组合候选后才申请新包范围；R37无完成回执、30公开Git待答。本轮桌面/公网/正式18891/8767/资产及另一三维断点保持，完整长期目标active/fullCloneReady=false。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
names=['tools/original_public_test_update_mapper_runtime_r265.py','tools/original_public_test_update_mapper_runtime_r268.py']
for folder in ['original_mapper_product_suite_r266_20261103','original_mapper_product_task_r270_20261103']:
 for name,pin in J(R/'Document/Deployment'/folder/'preparation.json')['sources'].items():assert sha(A/'tools'/name)==pin;names.append('tools/'+name)
extras=['prepare_mapper_product_runtime_r265.py','prepare_mapper_product_suite_r266.py','prepare_mapper_product_fixture_r266.py','verify_mapper_runtime_declarations_r267.py','strengthen_mapper_declarations_r268.py','verify_mapper_runtime_declarations_r269.py','prepare_mapper_product_task_suite_r270.py','prepare_mapper_product_task_fixture_r270.py','record_mapper_product_lifecycle_r272.py']
for name in extras:
 p=A/'tools'/name;assert not p.exists();raw=(V/name).read_bytes();ast.parse(raw.decode('utf-8'));put(p,raw);names.append('tools/'+name)
names+=['deploy/verification/mapper_product_lifecycle_r272_20261103.json','deploy/handbook/mapper_product_lifecycle_r272_20261103.md']
put(D/'local-stage-files.json',enc({'application':names,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/project/原SQL产品代码运行R272_20261103.md','docs/showcase_demo_completion.md']}));print(json.dumps({'recorded':True,'productParameterAndFinalAdapterLifecyclePassed':True,'nativePlanCases':11,'nativeTaskPhases':9,'originalSQLRegistered':226,'declarationBoundaryChecks':13,'publicOrDesktopChanged':False}))
