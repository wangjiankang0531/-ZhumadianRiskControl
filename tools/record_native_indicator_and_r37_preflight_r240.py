from pathlib import Path
import json
R=Path('D:/Project/Zhumadian');A=R/'Application';D=R/'Document/Deployment/public_test_static_performance_r37_20261103'
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def enc(x):return(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
pre=json.loads((D/'server-preflight-summary.json').read_text(encoding='utf-8-sig'));assert pre['passed']and pre['candidateVersion']=='R37'and pre['fixedManifestSHA256']=='1bf56d75d5edb8b12dd82831ea863fde1e03dfaefa8ef2b37f5f471575baa1b4'
assert(D/'ftp-upload-submitted.json').exists()and(D/'remote-check-submitted.json').exists()and not(D/'remote-apply-submitted.json').exists()
status={'fixedR37Uploaded':True,'serverEightSHAAndDataIdentityAndCheckOnlyPassed':True,'serverPreflight':pre,'deploymentCommandSubmitted':False,'normalStopStarted':False,'publicRuntimeStillR36':True,'nativeComputerUsePackageImportAndListAppsActuallyPassed':True,'nativeWinSCPActivateAndWindowCaptureActuallyPassed':True,'blueBorderAndCursorAppearanceUserConfirmationPending':True,'codexConfigurationOrGlobalWindowsCursorChanged':False,'disabledCuaReplEntryWasNotSufficientDiagnosis':True,'originalR37DeploymentApprovalStillValid':True,'legacyTerminalUIInputNotResumedAfterNativePreference':True,'newPublicGitPushed':False}
put(D/'execution-handoff-status.json',enc(status));put(A/'deploy/verification/static_r37_server_preflight_20261103.json',enc(pre))
note='''补充状态（R240）：固定R37八文件已上传，服务器逐SHA、数据身份及check-only预检已通过；远程前台切回ChatGPT时在部署输入前停止，未提交apply、未停服。用户随后要求以后采用早期蓝色渐变边框/大黑三角鼠标的接管提示。已按本机Computer Use技能，通过现有node_repl直接import @oai/sky、list_apps，真实激活/取得公网WinSCP窗口状态；接口可用，不需修改配置。先前把cua_repl enabled=false直接当作原因不准确，已更正，它不是原生接口不可用的充分依据。具体视觉效果仍待用户确认。后续Windows窗口操作用原生Computer Use，后台文件/构建继续；原R37批准保持，服务仍R36。\n\n'''
for p in [D/'固定候选说明.md',A/'deploy/handbook/static_performance_r37_candidate_20261103.md',R/'Document/Engine/project/静态加载优化R37候选_20261103.md']:put(p,note.encode()+p.read_bytes())
policy='''# 桌面接管显示要求与官方接口（2026-11-03）

用户要求以后接管桌面时采用早期的屏幕边缘蓝色渐变透明提示、大黑色三角鼠标，避免看不出谁在操作。实际选择官方Computer Use入口，不以全局鼠标修改或自制覆盖层冒充官方指示；具体客户端视觉效果要实测/由用户确认，不能仅因API成功就声称颜色恢复。

已读本机computer-use/26.1013.40934/skills/computer-use/SKILL.md及guidance.md/confirmations.md。通过当前可用mcp__node_repl__js按技能直接import @oai/sky，list_apps返回精确公网WinSCP/远程桌面，sky.activate_window和get_window_state对公网WinSCP实际成功。无需改变config.toml；cua_repl的disabled条目不足以证明整体接口不可用，先前判断更正。禁止自建helper协议或直接启动ComputerUse helper；不混用旧PowerShell UIAutomation与原生操作，不盲打长脚本/快捷键。

官方技能的guidance.md写明“Do not run Windows terminal commands via UI automation directly or indirectly.” 原生桌面工具不代输终端命令；需要另有正常命令通道，或由用户手动执行已准备和核验的脚本。此约束不得被模糊说成新包未获批准：当前固定R37本身已明确批准，且服务器预检通过，部署输入尚未提交、未停服。后台代码/验证/文档继续。若因该技能要求用户操作或留下步骤待办，应向用户给出准确技能路径/引用和具体原因。

后续先提示目标窗口和内容，再按返回窗口对象定位；实际输入每步先观察后单动作并刷新，焦点/账号/安全验证等异常立即停止，结束明确交还。原生API已验证不等于所有应用/敏感操作已获授权；当前R37及此前会话具体范围持续有效。不要操作杀毒/认证/安全设置，也不恢复隔离的两种临时测试EXE。

官方说明：https://learn.chatgpt.com/docs/computer-use 。完整引擎/EXE GIS DLG标绘标牌/Web3D/南港B/S目标保持，另一三维专属断点、8767和正式18891保持。
'''
put(D/'原生接管与执行状态说明.md',policy.encode());put(A/'deploy/handbook/native_desktop_indicator_and_execution_20261103.md',policy.encode())
entry='''## 2026-11-03 R240：R37已上传且服务器预检通过；用户要求恢复原生接管指示

固定R37已实际八文件SHA/数据身份/check-only通过，apply输入尚未提交、未停服、公网仍R36；焦点守卫在前台回ChatGPT时停止。用户要求以后蓝色渐变边框/大黑三角指示，实际按本机ComputerUse技能以现有node_repl直接@oai/sky导入/list_apps/激活及状态捕获公网WinSCP均成功，无需改配置。此前cua_repl disabled条目被过早当成原因已更正；接口可用，视觉表现待用户确认。后续原生Windows UI按技能，后台exec代码继续；技能禁止GUI直接/间接代输终端命令，需要正常命令通道或用户手动执行已固定脚本，原R37授权不失效，不假称缺批准。详Deployment/public_test_static_performance_r37_20261103/execution-handoff-status.json和原生接管与执行状态说明.md。未部署、未新公开Git，长期目标active/fullCloneReady=false，预案演练候选继续待验，另一三维专属断点/8767/资产/正式18891保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
p=R/'AGENTS.md';tag='<!-- NATIVE_DESKTOP_INDICATOR_20261103 -->'
assert tag not in p.read_text(encoding='utf-8')
put(p,p.read_bytes()+('''
<!-- NATIVE_DESKTOP_INDICATOR_20261103 -->
用户要求今后桌面接管恢复官方可视提示（蓝色渐变边缘/大黑三角鼠标）。已安装ComputerUse技能可通过现有node_repl直接import @oai/sky调用；list_apps及公网WinSCP激活/捕获已真实成功，不应仅凭cua_repl enabled=false断言工具不可用或改配置。先读该技能/guidance/confirmations并依原生API观察-单动作-刷新；不要继续以隐藏的PowerShell UIA方式接管或修改全局鼠标冒充官方提示。后台文件/构建工作照常。具体视觉表现以实测和用户反馈为准；终端GUI/认证/安全应用限制按技能处理，若因此需要用户执行，明确准确技能来源，区分既有发布授权仍有效。桌面前提示/后交还继续保持。
<!-- NATIVE_DESKTOP_INDICATOR_20261103_END -->
''').encode())
staged=json.loads((D/'local-stage-files.json').read_bytes());staged['application']+=['deploy/verification/static_r37_server_preflight_20261103.json','deploy/handbook/native_desktop_indicator_and_execution_20261103.md'];put(D/'local-stage-files.json',enc(staged))
print(json.dumps({'recorded':True,'R37UploadedAndPreflightPassed':True,'deploymentSubmitted':False,'nativeComputerUseActuallyAvailable':True,'configOrCursorChanged':False}))
