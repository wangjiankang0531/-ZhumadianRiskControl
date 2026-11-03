from pathlib import Path
import hashlib, json, zipfile, xml.etree.ElementTree as ET

R=Path('D:/Project/Zhumadian'); A=R/'Application'; V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/original_plan_exercise_verified_candidate_r249_20261103'
J=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()

assert not D.exists()
run=C/'r120'; prep=C/'prepared-r120'
result=J(run/'result.json'); browser=J(run/'plan-browser/result.json')
outer=J(C/'r120-outer-terminal.json'); receipt=J(run/'scoped-controller-receipt.json')
assert result['allPassed'] and result['nativeBrowserCases']==11
assert result['original398ModelsUnchanged'] and result['connectionCapacityWithoutRefusals']
assert browser['passed'] and len(browser['cases'])==11 and not browser['exceptions']
assert outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose'] and not outer['forceTerminationUsed']
assert receipt['allOwnedChildrenExited'] and receipt['normalOwnedShutdown']
assert all(v==0 for v in receipt['exitCodesBeforeJobClose'].values()) and not receipt['forcedJobClosureComponents']
restores={n:J(prep/n) for n in ['frontend-restored.json','plan-mapper-restored.json','history-runtime-restored.json','configuration-restored.json']}
assert all(x.get('passed') for x in restores.values())
original=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256']
assert sha(R/'_g/Application/release-manifest.json')==original
scope=J(R/'Document/Deployment/original_plan_exercise_candidate_r248_20261103/source-and-execution-scope.json')
for name,pin in scope['sources'].items():assert sha(A/'tools'/name)==pin
proof={'schema':'xnby.r249.plan-exercise-verified-candidate.v1','actualAttempt':'r120',
       'result':result,'browserCases':browser['cases'],'javascriptRuntimeExceptions':len(browser['exceptions']),
       'sixNormalExitCodes':receipt['exitCodesBeforeJobClose'],'actualDescendantsZero':True,
       'originalFrontendMapperUpdaterConfigurationAndManifestRestored':True,
       'originalReleaseSHA256Restored':original,'sourcePins':scope['sources'],
       'failureInjectionWasBrowserResponseOnlyNotSQL':True,
       'sharedTaskUploaderRegressionStillPending':True,'originalNangangFullAcceptancePassed':False,
       'newProductPublicDeploymentOrPublicGitPerformed':False}
put(D/'verified-result.json',enc(proof))
inventory=[]
with zipfile.ZipFile(R/'_g/Application/payload/business/application.jar') as z:
    for name in z.namelist():
        if not name.endswith('.xml') or not ('mapper' in name.lower() or name.startswith('xml/')):continue
        b=z.read(name)
        try:root=ET.fromstring(b)
        except ET.ParseError:continue
        if root.tag!='mapper':continue
        inventory.append({'resource':name,'namespace':root.attrib.get('namespace'),
                          'statementIds':[n.attrib['id'] for n in root if 'id' in n.attrib],
                          'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
put(D/'original-jar-mapper-resource-inventory.json',enc({'readOnlyOriginalJar':True,'mappers':inventory,
    'globalMapperScanOrPublicRuntimeChanged':False,'allOriginalQueriesValidated':False}))
text='''# 预案与演练候选实际验证（R249，2026-11-03）

r119在原编译页面实测复现演练可选人员留空后undefined.join、没有保存请求。r120使用R224十四源码/341文件完整候选、原Jar精确XML及R36鉴权/历史模块，普通非管理员正常登录下11项原生浏览器检查全部通过：预案必填及电话拒绝、实际新增/修改/只读详情；演练可选人员为空正常保存、父预案范围列表回读、实际人员弹窗选两人；真实附件未上传完成时禁止保存，完成后可保存；浏览器返回失败保留输入/人员/附件、一次实际重试及重复提交保护；详情与原生下载锚点落盘文件逐字相同。无JavaScript运行异常。

失败返回由浏览器网络拦截模拟，未声称真实SQL故障回滚。测试全部使用自有合成环境；398项原模型定义与连接容量检查通过。六组件和Chrome正常退出、实际后代零；前端、XML/更新器、虚构配置及清单逐字恢复，原基线e9dcd876已核同，没有操作公网、正式18891、三维8767或用户桌面。

本轮不代表全部南港验收。共享附件组件涉及任务编辑，仍须对该候选执行任务/流程回归；原Jar其他XML和原配置扫描方式正在核对，不把一个映射补齐冒称全部业务映射已验。未来发布须以实际R37静态性能版为基线保留其代理/压缩/缓存控制，不能直接用旧R36专用R225更新器覆盖。当前尚未发布此候选。

R37固定8文件已上传、服务器预检通过；最新两入口匿名静态HEAD仍200/no-store/无gzip，没有部署完成回执。原生ComputerUse可用，但其指引禁止GUI终端命令，已请求用户手动执行固定Deploy脚本；既有R37发布授权仍有效，无需重复批准。固定30文件公开Git范围仍待答，未创建新公开对象或提交。完整UE效果效率引擎、EXE GIS/DLG图层空间标牌、多源绑定、Web3D及一套系统多入口南港B/S复刻目标继续，fullCloneReady=false；另一三维会话专属断点保持。
'''
put(D/'阶段说明.md',text.encode())
put(A/'deploy/verification/plan_exercise_verified_candidate_r249_20261103.json',enc(proof))
put(A/'deploy/handbook/plan_exercise_verified_candidate_r249_20261103.md',text.encode())
put(R/'Document/Engine/project/预案演练候选验证R249_20261103.md',text.encode())
entry='''## 2026-11-03 R249：r120候选11项实际通过、正常恢复；R37待执行回执

r119真实复现后，R224十四源码候选r120普通角色11项预案/演练/选人/真实上传/失败保留与一次重试/实际锚点下载通过，零JS异常；失败仅浏览器响应模拟，不宣称SQL故障。398模型与容量通过，六组件/Chrome正常0、实际后代零，原前端/映射/更新器/虚构配置/清单逐字恢复，_g原e9dcd876。session6843终态0，不再轮询。共享任务附件回归及原Mapper整体集成核对待完成，不发布候选；未来须基于实际R37保留静态控制。R37已上传/预检过，最新匿名静态HEAD仍无gzip/no-store，无完成回执；技能禁止GUI终端，等待用户手动固定Deploy命令，既有授权有效。30文件公开Git待答、未创建对象。详Deployment/original_plan_exercise_verified_candidate_r249_20261103。完整长期目标active/fullCloneReady=false，另一三维专属断点/8767/资产/正式18891保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
for name in ['prepare_plan_candidate_r248.py','record_plan_candidate_r249.py']:
    assert not (A/'tools'/name).exists();put(A/'tools'/name,(V/name).read_bytes())
stage=J(R/'Document/Deployment/original_plan_repro_progress_r247_20261103/local-stage-files.json')
stage['application']+=['tools/prepare_plan_candidate_r248.py','tools/record_plan_candidate_r249.py',
    'deploy/verification/plan_exercise_verified_candidate_r249_20261103.json','deploy/handbook/plan_exercise_verified_candidate_r249_20261103.md']
stage['engine']+=['docs/project/预案演练候选验证R249_20261103.md']
put(D/'local-stage-files.json',enc(stage))
print(json.dumps({'recorded':True,'candidateBrowserCases':11,'restored':True,'originalJarMapperResources':len(inventory),
                  'localStageApplicationFiles':len(stage['application']),'localStageEngineFiles':len(stage['engine']),
                  'newPublicOrDesktopOperations':False}))
