# 本机三维恢复与当前账号登录自启（2026-11-02，R170）

三维入口：http://127.0.0.1:8767/?topic=emergency&mode=command 。用户刷新后已确认“已出现地景和企业标牌”。当前使用既有封装，不转换或复制 GIS 资产。

## 故障依据与实际恢复

故障时没有 8767 监听，也没有本包启动器/服务进程。机器最近启动时间为 2026-11-02 14:17:34+08:00，之前仅手动启动、没有登录自启；这些事实支持“重启后未重新启动本地服务”，未证明之前进程的确切退出原因。使用固定包原启动器一次正常启动后，页面、原 viewer.js、图层、图标及实际地景索引等 7 项 HTTP 检查通过。原 index/viewer 字节与固定包完全相同；图形效果由用户手动确认，未宣称自动 GPU、性能或 UE 对标验收。

首次检查误猜地景索引 URL、误猜源码相对路径的失败保留。原包初始化使 SQLite 物理 SHA 改变：只在文件头偏移 24 和 92 的两个四字节计数各加 1，内存还原后匹配启动前 SHA；其它所有字节及标注文档保持，quick_check 正常。诊断没有写回数据库。不能将此写成“启动前后数据库整个文件字节未变”。SQLite 格式依据：https://www.sqlite.org/fileformat.html 。

## 使用与自启

- 手动启动入口：`D:\Project\Zhumadian\Application\启动本机三维应急.cmd`。
- 统一启动器：`D:\Project\Zhumadian\Application\tools\scene_boot.py`。仅启动固定包的原 Python/原启动程序，后台运行，不弹浏览器，只使用本机 `127.0.0.1:8767`。
- 当前 Windows 账号的 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 下新增字符串 `XNBYZhumadianScene`。用户 call_4ccaf7f8ffcb46f28ae6ffb646b200a8 明确批准；写前确认值不存在，写后精确回读。
- 服务正常时按运行身份、进程映像及 viewer 字节核对后复用。命名互斥锁防止重复启动；异源占用/身份漂移拒绝，不强杀。四次并发、真实手动入口、异源端口拒绝、固定包拒绝等 6 项通过。
- 实际执行与注册表完全相同的启动命令，复用服务 PID 36628，无停启和重复进程；这轮安装验证期间数据库字节保持。未来一次真实注销/登录或开机登录的自动触发尚未测试，不为测试而重启用户电脑。
- 自启与服务运行结果：`Application\UserData\LocalEmergencyScene\latest-start.json`；详细启动日志在同一目录。

## 可逆撤销

如需关闭自启，先核 `XNBYZhumadianScene` 的完整值仍与 `Document\Deployment\local_scene_recovery_20261102\startup-proposal.json` 一致，再仅移除该注册表值。此操作不会停止已运行的三维服务；不删除 Run 键、不改其它启动项。若值已被用户修改，停止并保留现场。不要重新执行安装器覆盖已有项。

完整证据在 `Document\Deployment\local_scene_recovery_20261102`；本阶段代码与说明写入既有本地 Git 分支，不借旧 R33 固定 48 文件授权对外公开新内容。全程后台，无桌面输入；公网 B/S R33、IIS、业务数据保持。全南港业务验收仍待，fullCloneReady=false。
