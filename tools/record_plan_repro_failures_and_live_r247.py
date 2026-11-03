from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_plan_repro_progress_r247_20261103';V=Path(__file__).resolve().parent
if D.exists():assert not any(D.iterdir())
else:D.mkdir(parents=True)
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def enc(x):return(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
failed=[]
for attempt in ['r115','r117']:
 root=C/attempt;P=C/('prepared-'+attempt);receipt=J(root/'scoped-controller-receipt.json');outer=J(C/(attempt+'-outer-terminal.json'));terminal=J(root/'controller-terminal.json')
 assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())and terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']
 assert J(P/'frontend-restored.json')['passed']and J(P/'plan-mapper-restored.json')['passed']and J(P/'history-runtime-restored.json')['passed']
 browser=root/'plan-browser/failure.json';b=J(browser)if browser.exists()else{}
 failed.append({'attempt':attempt,'hostFailure':J(root/'failure.json'),'normalSixComponentExitCodes':receipt['exitCodesBeforeJobClose'],'allActualDescendantsZero':True,'allFrontendMapperUpdaterAndSyntheticConfigBytesRestored':True,'nativeBrowserCasesPassed':len(b.get('cases',[])),'browserStage':b.get('stage'),'exerciseSaveRequestsObserved':len([x for x in b.get('http',[])if x['path'].endswith('/emergencyExercise/save')]),'original398ModelComparisonReached':False,'publicFormalAndDesktopChanged':False})
run=C/'r119';result=J(run/'result.json');repro=J(run/'plan-browser/baseline-reproduction.json');outer=J(C/'r119-outer-terminal.json');receipt=J(run/'scoped-controller-receipt.json')
assert result['allPassed']and result['nativeBrowserCases']==6 and result['original398ModelsUnchanged']and repro['reproduced']and repro['actualUndefinedJoinErrorObservedViaDebugger']and not repro['actualUndefinedJoinErrorObservedViaRuntimeOrConsole']
assert outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose']and receipt['allOwnedChildrenExited']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())and J(C/'prepared-r119/history-runtime-restored.json')['passed']
assert sha(R/'_g/Application/release-manifest.json')==J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256']
live=None
proof={'failedAttempts':failed,'liveAttemptSnapshot':None,'actualBaselineResultR119':result,'actualBaselineReproductionR119':repro,'normalAllSixComponentsBrowserAndActualDescendantsZero':True,'allOriginalBytesRestoredAfterR119':True,'productCodeModifiedToCreateOrSuppressError':False,'R37CompletionAnd30FilePublicApprovalStillAwaited':True}
put(D/'failed-and-live-state.json',enc(proof))
names=[]
for folder,key in [('original_plan_exercise_fixture_identity_r243_20261103','outputPins'),('original_plan_submit_observation_r245_20261103','sources')]:
 pins=J(R/'Document/Deployment'/folder/'preparation.json')[key]
 for name,pin in pins.items():assert sha(A/'tools'/name)==pin;names.append('tools/'+name)
for name in ['prepare_plan_baseline_r242.py','prepare_plan_exercise_fixture_identity_r243.py','prepare_plan_baseline_r244.py','prepare_plan_submit_observation_r245.py','prepare_plan_baseline_r246.py','record_plan_repro_failures_and_live_r247.py']:
 target=A/'tools'/name;assert not target.exists();put(target,(V/name).read_bytes());names.append('tools/'+name)
text='''# 预案与演练原生验证阶段（2026-11-03，R242—R247）

完整目标保持为一套系统多入口的全南港B/S复刻及UE效果效率引擎/EXE GIS DLG图层空间标牌/Web3D，不以验证脚本数量或单路径通过替代完成率。当前优先两应急视角、同时保留R37静态性能交付。

r115实际原六组件、原历史模块和精确原XML运行就绪通过，在浏览器启动前读取已消失的历史合成角色JSON时报FileNotFoundError。r117驱动改从已编译合成种子id(100)=a531...0064推导固定角色，不创建修改账号或口令，保留正常登录/CurrentUser精确身份断言；五个原生阶段（普通角色正常入口、必填拒绝、电话拒绝、预案真实新增、修改及只读详情）通过。演练活动子弹窗地点已填写，但等Runtime/Console的join异常超时，零保存请求/零捕获异常，r117本身不能宣称错误已复现或演练通过。两轮六组件全部正常0/实际后代零，原前端、映射/更新器、虚构配置与清单逐字恢复；这两轮398定义比较未到达，不能记通过。

R245仅加强验证驱动：提交按钮必须真实可见/未禁用且点击函数返回true，记录DOM footer命中；仅在旧前端复现阶段开启调试器捕获被处理异常并立即resume，未修改产品异常/处理函数。后续候选附件文件输入仅定位活动演练弹窗，避免同名旧表单干扰。r119已完成六阶段，真实可见/未禁用的确定按钮命中、活动子弹窗地点已填写且无校验错误，可选人员留空后由调试器实测捕获undefined/join的promiseRejection；Runtime/Console依然未收到该异常，零演练保存请求、输入保留。原398定义和实际连接容量比较通过；六组件、Chrome正常0及实际后代零，原前端/映射/更新器/虚构配置/清单精确恢复，_g回到原e9dcd876基线。session3167已终态0，不再轮询或重启；r120候选未准备/未运行。原R227的r116和R243的r118未运行，不误用旧包。

测试用旧R35/R36编译前端时，为到达演练入口已临时补回原Jar字节相同的XML并用严格R225声明；这不是“完全未改公网R36”的复现宣称。R224十四源码候选341文件完整构建已通过，但尚未完成最终原生全流程，不发布。若以后与性能版组合，必须基于实际R37精确版本保留静态/IIS/缓存控制，不用R225旧R36专属更新器覆盖R37。

R37固定8文件已上传/服务器预检通过，尚未取得执行完成回执；最近匿名HEAD仍no-store/无gzip。原生ComputerUse通过当前node_repl直接@oai/sky已真实可用，用户要求今后桌面保留蓝色边缘/大黑三角提示，具体显示待用户反馈；无桌面输入。本轮按技能要求不代输GUI终端命令，已给用户一行原固定Deploy命令。公开Git固定30文件309475B/5dea0df5范围待答，尚未上传新GitHub对象；本地既有review已保存R37候选。另一三维专属断点、8767/资产和正式18891保持，fullCloneReady=false。
'''
put(D/'阶段说明.md',text.encode());put(A/'deploy/handbook/plan_exercise_repro_progress_r247_20261103.md',text.encode());put(A/'deploy/verification/plan_exercise_repro_progress_r247_20261103.json',enc(proof));names += ['deploy/handbook/plan_exercise_repro_progress_r247_20261103.md','deploy/verification/plan_exercise_repro_progress_r247_20261103.json']
put(R/'Document/Engine/project/预案演练原生验证进展R247_20261103.md',text.encode())
entry='''## 2026-11-03 R242—R247：r119六阶段通过并真实复现可选人员undefined.join，全部正常恢复

r115六组件/就绪后旧合成角色JSON缺失、浏览器前失败，正常恢复；R243从已编译种子推导固定角色ID并保留正常登录，r117五预案阶段通过但仅等Runtime/Console超时，两失败保留并全部正常恢复。R245加强可见提交命中/DOM记录、仅复现阶段调试器捕获即resume，产品未改；r119六阶段已通过，活动子弹窗地点填写/确定命中后实测undefined/join promiseRejection、零保存/输入保留，Runtime/Console未观测到该异常。原398定义/连接容量通过、六组件/Chrome正常0和后代零，原前端/映射/更新器/虚构配置/清单精确恢复，_g基线e9dcd876。exec session3167已终态0不可再轮询；r120候选未准备。R224十四源码候选仍待全流程，不发布。R37已上传/服务器预检过等手动执行回执，30文件公开Git待答、未创建对象；官方@oai/sky原生接口可用，桌面交还无新输入。详Deployment/original_plan_repro_progress_r247_20261103。完整长期目标active/fullCloneReady=false，另一三维断点、8767/资产/正式18891保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
put(D/'local-stage-files.json',enc({'application':names,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/project/预案演练原生验证进展R247_20261103.md','docs/showcase_demo_completion.md']}));print(json.dumps({'recorded':True,'failedAttemptsPreserved':2,'nativePlanCasesPassedR117':5,'R119PassedCases':6,'R119OriginalJoinErrorActuallyReproduced':True,'R119NormalAllExitedAndRestored':True,'newPublicOrDesktopOperations':False}))
