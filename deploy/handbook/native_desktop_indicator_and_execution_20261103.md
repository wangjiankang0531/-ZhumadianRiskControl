# 桌面接管显示要求与官方接口（2026-11-03）

用户要求以后接管桌面时采用早期的屏幕边缘蓝色渐变透明提示、大黑色三角鼠标，避免看不出谁在操作。实际选择官方Computer Use入口，不以全局鼠标修改或自制覆盖层冒充官方指示；具体客户端视觉效果要实测/由用户确认，不能仅因API成功就声称颜色恢复。

已读本机computer-use/26.1013.40934/skills/computer-use/SKILL.md及guidance.md/confirmations.md。通过当前可用mcp__node_repl__js按技能直接import @oai/sky，list_apps返回精确公网WinSCP/远程桌面，sky.activate_window和get_window_state对公网WinSCP实际成功。无需改变config.toml；cua_repl的disabled条目不足以证明整体接口不可用，先前判断更正。禁止自建helper协议或直接启动ComputerUse helper；不混用旧PowerShell UIAutomation与原生操作，不盲打长脚本/快捷键。

官方技能的guidance.md写明“Do not run Windows terminal commands via UI automation directly or indirectly.” 原生桌面工具不代输终端命令；需要另有正常命令通道，或由用户手动执行已准备和核验的脚本。此约束不得被模糊说成新包未获批准：当前固定R37本身已明确批准，且服务器预检通过，部署输入尚未提交、未停服。后台代码/验证/文档继续。若因该技能要求用户操作或留下步骤待办，应向用户给出准确技能路径/引用和具体原因。

后续先提示目标窗口和内容，再按返回窗口对象定位；实际输入每步先观察后单动作并刷新，焦点/账号/安全验证等异常立即停止，结束明确交还。原生API已验证不等于所有应用/敏感操作已获授权；当前R37及此前会话具体范围持续有效。不要操作杀毒/认证/安全设置，也不恢复隔离的两种临时测试EXE。

官方说明：https://learn.chatgpt.com/docs/computer-use 。完整引擎/EXE GIS DLG标绘标牌/Web3D/南港B/S目标保持，另一三维专属断点、8767和正式18891保持。
