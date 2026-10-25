# 原系统首次安装R2小型增量与重启后的回滚归属

2026-10-25。仅用于已封存原系统测试包的首次安装，不将新源码直接覆盖到已初始化服务器。独立候选已真实两轮启动/正常关闭/同数据重启，实际IIS和公网仍待验收。

## 修正与验证

既有发布工具发现同版本IIS文件和TLS已正常时直接返回，导致后台重启后active-deployment仍保留旧PID/run，后续回滚遗漏新控制器。临时文件完整安装/回滚流程已复现，基线5项中4失败。修正为：保留首次IIS备份和原文件，只验证并刷新当前ready自有控制器的PID/run；同一owner不改写记录。路径须位于本安装runs/jN，拒绝并发记录变化及越界run。修正5项通过，原IIS事务6项通过。进程、编译和TLS边界在这组夹具中模拟，不宣称实机IIS通过。

手机LOGO修正复用已同步main f5020beb的固定原路径替换及H5内SVG别名。SVG598B/SHA509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d不变。原Reference/编译产物/登录角色/业务库/四API块不变。

## 固定交付

原大包ZhumadianOriginal_Private_20261025/ZhumadianOriginal_20261025.zip，1050340997B，SHA0a9174d21fc9815697f57ac49fbef7e75bee09ac4cbcb9508a1e0f2663564f8e，完全保持。

新增目录ZhumadianOriginal_Update_20261025_r2：36704B，11文件；更新ID 23962ce0-58c3-493f-bdd5-abadbe512b7d；update-manifest SHA 9fe2ab0563f7b34b98435e08c40ae498f05c0b4f9225489b1815634cfa818c85；更新后的release-manifest SHA c2d94d1d014ac644555bedd90dc1189d5c77bf9740377129655aa905d63544f2。仅替换两个自有控制源码、三个CMD和发布清单。目录含受控离线应用工具、校验清单、R2启动CMD/PS1及拒绝HTTP下载的web.config；包内不再复制SDK/库/GIS。

离线工具校验固定基版本、全部基控制文件和六个新/旧文件SHA；借用server-owner.lock同一字节锁隔离并发首启。已有安装数据即拒绝，已精确应用同版则只核验返回；失败恢复原控制文件，若发现外部编辑保留外部字节和证据。9项真实文件/字节锁检查通过，含被占用锁、初始化后拒绝覆盖、幂等、载荷/清单/已装漂移、写入失败恢复、并发编辑及越界成员。无服务启停、DB打开、IIS配置或OS设置修改。

R2 PS1先沿用旧包SHA和路径预检/独立解压，再调用离线工具，成功后以新清单SHA启动发布工具。脚本为ASCII，PowerShell解析0错误；没有在本机执行服务器脚本，不改执行策略。已初始化旧版本会明确拒绝，不自动停止原服务或强制升级。若服务器已运行旧包，先反馈结果，另行安排正常停止及受控更新。

## 实机隔离结果与空间

独立D:/Zqr220261025/Application，15400个已逐SHA验证的不可变文件用同盘硬链接复用；570文件独立复制725603688B（主要关闭测试种子），额外复制上限800MiB、阶段临时峰值6GiB。首轮准备在旧QA清单与最终交付清单不同处拒绝，未启动；仅改为从固定ZIP取5个顶层清单/CMD后逐SHA复用已有部分文件，没有再次复制种子。

实际包内Python/Java/MySQL/Redis/MinIO/Nginx执行j1和同数据j2，六组件每轮自然0、两个Spring上下文关闭、无强制Job收尾。数据库UUID 165c68a5-9c28-44f1-baff-298f2ef98d94和平台owner保持；初始化后重跑同一增量实际返回alreadyApplied且数据保留。每轮10匿名HTTP通过：PC/H5/admin/应急、两路径SVG、934B公网手机二维码、登录配置200、CurrentUser业务600、手机登录chunk为新LOGO路径且SHA同本机已渲染版本。不是原账号业务、手机真机、IIS或公网验收。

两轮后15400个共享不可变源文件再次逐SHA一致，当前CIM无自有残留、18902可独占绑定；保存小型收据/日志后清本轮自有QA根。观测D盘空闲差731852800B，不将同期变化全部归因本次清理；不把硬链接逻辑2.13GB当成物理释放。旧独立QA、原ZIP、r26种子、当前j18和8767保留。

## 服务器操作边界

两个交付目录都放服务器C:/FTP_Root/Zhumadian下；各先放web.config再放其它文件。现有WinSCP已由协议对话框确认FTP，不传私有包。仅用已登录RDP的文件复制/现有驱动器重定向或已确认的加密传输，不更改RDP安全设置。旧包尚未启动时，运行新目录的Deploy_Original_20261025_R2.cmd一次，取代旧CMD；两个CMD不要都点。若旧包已经启动，不再执行R2离线首装工具，先反馈。

Windows Computer Use禁止通过GUI直接/间接执行终端命令，所以最终CMD由用户手工双击。当前向RDP发送Ctrl+L的动作又被自动审批拒绝，理由是上一轮用户中断及远端焦点不能确认，现已停止所有远程输入并单独请求恢复文件传输；未复制本轮文件、未执行服务器命令。实际复制/正常启动/公网PC-H5-原账号/252本机三维/角色审批/历史附件/20秒外围质量均待，fullCloneReady=false。

证据Document/Deployment/original_ingress_restart_20261025：baseline/fixed/cutover/offline日志、small-update-build.json、r2-j1/j2-receipt、每轮10项HTTP、r2-isolated-result.json、r2-qa-cleanup.json。固定清单生成在QA前，实机证据绑定其SHA，不为改通过字段重写已验证对象。无数据库字段/索引/状态结构变化，不重生成模型；原14held保持，Git结果另见源码镜像收据。
