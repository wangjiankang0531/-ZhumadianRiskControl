# 新EXE静态地景界面实际验收（2026-10-27）

记录2026-10-27T05:37:38.731988+08:00。新EXE固定SHA5232228d30252b48138fa7ca65f67b669717694e970dbdef5cfd3b883030bebd，16个运行库/版权文件候选保留work/native_static_shell_20261027/candidate。不是正式便携包，没有修改Packages/active_release.json或250/252快捷方式、公网。

## 固定源码与验收模式

使用此前封存的应用f570414/引擎b89578af及两容量修正文件，共390文件，不编入14held原生修改。仅对固定main.cpp SHA cb86cba5应用native_static_shell_patch.py：新增显式--editor-static-shell-qa，只允许编辑器--editor-shell-probe且stats非空，拒绝截图渲染/业务/拾取/原生探针/纯文档等混合方式；该模式在交互renderFrame跳过nativePager.service，保留初始化、基础地景绘制、界面/窗口流程。默认false，原始正式LOD路径不变。

输入固定SHA不匹配或替换边界不唯一即拒绝；工具不直接覆盖工作树。完整隔离源码和SHA封存isolated-source.private.zip。源码准备首次因CRLF边界不匹配在创建文件前停止，按全文件CRLF精确保留后成功。原同ABI缓存恢复1738必要文件123743016B，未下载。CMake Release编译/链接exit0，有原有编译警告；组包误把licenses目录当文件而停止，随后只恢复组包，最终16文件齐全，没有重复构建。

## 一次真实图形执行

候选仅启动1次，PID37496，8.741秒、exit0、无超时/强杀/WM_CLOSE干预。读取既有0.9.7包中的驻马店基础地景作为只读资源；CLI--layers指向自有合成3图层文件，--stats指向新建空输出目录。运行器核对所有EXE/DLL/版权SHA、输入SHA及27保护文件；不启动旧0.9.7、原生读取器或ETW，不复制GIS、改业务库/附件/用户DLG。

实际Vulkan选择NVIDIA GeForce RTX5080，日志preset=zhumadian、scene_config=loaded、9584599顶点/11668083索引；惠炼GLTF0、信能源源模型/LOD模型均0。现有editorShellProbe执行8个实际窗口状态：启动最大化、隐藏面板、左停靠、右停靠、1366x768、1024x640、面板滚动793、恢复最大化。逐状态检查窗口客户区/视口/交换链范围、面板显隐/停靠、非空图形帧，并确认图层文档和草稿完全不变。未注入鼠标键盘。8张原始图形帧捕获成功，首张已人工查看，驻马店卫片与基础摄影可见。捕获仅渲染视口，不含GDI编辑面板；面板布局由实际Win32位置和显隐检查证明，不把图形帧称完整桌面截图。

不证明：点/线/区域实际绘制修改、图层增删锁定/移动、千层交互、保存重开/跨Web全过程、细层加载质量、20秒外围清晰度、200ms交互或UE对标。8.74秒包含该次启动和8个状态，不是首屏或交互性能指标。旧0xC0000043问题没有重试或修复。本轮静态模式验证不能替代正式完整LOD模式验收。

## 重建、部署和使用

先从上述固定隔离源恢复390文件，仅对原始main应用tools/native_static_shell_patch.py的patched_main(bytes)，返回候选字节；不得对当前held main.cpp应用。构建配置沿用native_capacity_isolated_build_20261025的精确ABI和configure-r4-started.json，把source/build/dependencies前缀换成本阶段独立目录。完整实际命令及exit记录在本阶段configure/build-started及result。无需恢复整个旧工作目录或GIS。

本次已执行的命令包含--editor-static-shell-qa --editor-shell-probe --frames=80 --layers=<自有合成文件> --stats=<新建空目录>/stats.json，工作目录为既有0.9.7资源根。具体SHA、绝对路径和一次执行门禁在graphical-plan.private.json；它是已完成历史计划，不是再次双击入口。运行器要求新空结果目录；CLI只验证stats非空，不声称其自行阻止任意路径覆盖。

后续正式交付须绑定只读驻马店资源形成完整便携清单，再验证新EXE原界面点线面编辑、保存重开、Web互读和250/252，确认完整LOD路径后才切换默认包。当前新候选不含GIS，直接双击默认仍走原native路径，不能当只读静态测试入口。现有正常包与回滚资料保留，不替换用户启动入口。

## 文档、Git、空间

设计、部署、使用、验收与连续性更新；新增自有固定源补丁生成工具和本说明共2文件独立本地Git检查点，父e6f66bdd。HEAD/index和27保护文件保持，不push、不改旧待批载荷。引擎远端main8966e32b未变，无新增可合并；250业务仍j40/PID44620/18891/release3f1ee528，公网R5保持。

编译与运行进程已终态，候选16文件SHA核同，source逐SHA ZIP可读后，移除本轮source/build/dependencies可重建重复物；七张捕获和执行源码归档，保留首张可直接查看和全部统计/日志。不删除GIS、Reference、缓存源ZIP、用户图层、业务库或旧0.9.7故障证据。全目标active/fullCloneReady=false。
