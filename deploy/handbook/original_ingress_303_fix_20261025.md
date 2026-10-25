# 原系统服务器303跳转预检兼容修复

2026-10-25，项目测试版，真实服务器发布仍未验收。

用户在101.201.65.94执行只读诊断，实际输出READ_ONLY_PREFLIGHT_BEGIN、HTTPS_TARGET 127.0.0.1 /zhumadian/、HTTP_STATUS 303，随后旧预检抛出通用失败。说明这一请求已完成原CA/SNI/主机名校验并收到HTTP响应；具体跳转目标未读取，不推断登录状态或完整业务可用。R3安装器只接受200/301/302，将303误判失败。此为部署器兼容缺陷，不要求改服务器TLS或认证设置。

修正：既有站点连通性预检接受200、301、302、303、307、308；仅检查经验证的原始响应，不跟随Location，不读取或记录正文/认证头。401、403、500等错误仍拒绝。后续新版本页面、图标、PC/H5/API检查维持原门槛。预检保存每个地址的HTTP状态或TLS/连接异常类型和说明到原部署报告，并显示阶段输出，避免再丢失根因。TLS默认信任、SNI、主机名检查完全保留。

真实回环transport扩展为8个测试方法，包含六种受支持状态、三个拒绝状态、未受信任证书、错误主机名；TLS/HTTPConnection和preflight函数实走，只有磁盘/.NET/IIS机器前置条件与443→临时本机端口为夹具，不启动业务子进程。基线明确复现303失败，保留日志；修后transport8、重启归属5、IIS文件事务6、离线更新12，共31项。测试方法中的subTest不重复计数。

build_original_ingress_transport_repair.py新增明确R3/R4标签，默认R3保留；R4固定controllerRevision=20261025-r4-303-preflight，从精确R3清单生成后继。离线更新器字节不变，仍在同一个Windows归属锁下核验固定前一guard、旧release与全部controller SHA；初始化后拒绝新覆盖、相同已应用修复幂等。六目标仍为branding、安装器、三个CMD、新release清单，branding不变。原包和R2/R3不重建。

R4：11文件35576字节，patch SHA b329ba3bc057718b63b92f30d3efdcb4d5cde86a7388cf1dc319ae6a0bbd9793；旧release d28624f2ba9bee22b135407475108d0467a1ddebec1c6f63e8ded36fa6bd7cc3；新release 12b56e076bf9fa578d45b400155663242e4325798881336d1f8580b420e2d1d4。仅从封存ZIP提取18个自有文件131733B，实走base→R2→R3→R4、真实Windows锁、三份备份保留、全部controller读回、初始化marker后相同修复幂等、驱动真实更新器、模拟安装边界非零73传播、工具漂移零子进程通过；临时夹具已清理。没有打开原库或启动原后台；首个未交付R4因保持原CRLF重新封存，旧候选逐11文件核验后移除，正式以上述pin为准。

服务器交付目录应为C:/FTP_Root/Zhumadian/ZhumadianOriginal_Update_20261025_r2/transport_fix_r4，先复制拒绝HTTP的web.config，再其余内容；只有完成交付后，用户手工双击Deploy_Original_20261025_R4.cmd一次。不要再运行旧R2/R3入口。已有运行安装将被首装增量拒绝，此时反馈现场，不绕过保护。正常预检与新后台ready后才备份切换IIS，原回滚路径保留。实际编译/启动/公网PC与手机/原账号全模块仍待，不以本轮测试代替上线。

复现：python -B -W error::ResourceWarning -m unittest discover -s tools -p test_original_ingress_transport.py -v；同样执行test_original_ingress_restart.py、test_original_iis_cutover.py、test_original_server_offline_update.py。没有数据库模式变更。fullCloneReady=false，完整UE/EXE/Web/图层和严格复刻目标保持。
