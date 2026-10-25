# 原系统服务器HTTP/TLS部署预检修复

2026-10-25，项目测试版，公网发布尚未完成。

实际服务器在R2六文件更新成功后，进入HTTPS预检，因安装器的http函数覆盖同名http模块而报AttributeError。失败点在启动新控制器和切换IIS之前。此前文件事务测试替换整个tls_local，未覆盖此调用；失败不得视为完整服务器验收通过。

安装器改用独立http_client模块名，HTTP和TLS连接都使用该模块；保留默认CA、SNI、主机名验证。新增真实回环HTTP/TLS测试，不替换HTTPConnection和tls_local；通过时检查SNI/Host，负向检查自签名未信任、主机名不匹配均被拒绝。临时证书仅测试目录生成，不写系统证书库；需要Git附带的openssl或PATH上的openssl。

安装器增加预检、就绪等待和切换阶段输出，每10秒报告启动等待，原540秒就绪上限保留。现有同版本重启/回滚归属及IIS备份事务保护不变。

离线更新工具仅在同一server-owner字节锁下，允许新固定清单提供previousReservation，且必须逐字匹配已知前一增量guard；当前发布清单、全部旧文件及controller哈希仍须匹配。原服务器一旦初始化，继续拒绝覆盖；没有动态热更新、业务库修改或后端重启。新增三项测试验证精确后继、缺失前一guard、前一pin不符。

新工具build_original_ingress_transport_repair.py以已封存R2清单和自有源码构建小型R3。六目标为同两控制源码、三个CMD和新release-manifest；branding字节保持。新入口CMD使用已经安装的runtime/python运行固定路径修复驱动；驱动验证离线工具/清单SHA、调用同一固定更新器，读回新pin后才进入原安装器。没有PowerShell执行策略修改、批量解除来源、证书信任修改，也不内联执行脚本正文。

R3：11文件34959字节，patch SHA 1e370546e659ea63bf7c21eb96f730906a50b285c5b55b05e7d06923fe732b21；base release c2d94d1d014ac644555bedd90dc1189d5c77bf9740377129655aa905d63544f2；new release d28624f2ba9bee22b135407475108d0467a1ddebec1c6f63e8ded36fa6bd7cc3。原1.05GB ZIP及R2原11文件保留，不重新生成全包。交付位置为R2目录下transport_fix_r3子目录，先复制其web.config，再其余内容；只双击新Deploy_Original_20261025_R3.cmd一次。

验证：真实transport4、重启归属5、IIS文件事务6、离线更新12，共27项独立源码镜像回归。原真实transport基线4项中2项复现同AttributeError；错误记录保留。另仅从封存ZIP提取18个自有文件/131733字节，实际base→R2→R3，真实Windows锁、两份旧备份、初始化marker后alreadyApplied、驱动实际调用更新器、模拟部署非零73传播、工具漂移在任何子进程前拒绝通过。只验证文件与传输，不启动原后台、不打开数据库；夹具清理完成。首夹具因缺少两个自有IIS源码/模板白名单在读取前拒绝，按实际14控制文件清单精确补充后通过。

复现命令：python -B -W error::ResourceWarning -m unittest discover -s tools -p test_original_ingress_transport.py -v；同样运行test_original_ingress_restart.py、test_original_iis_cutover.py、test_original_server_offline_update.py。真实服务器IIS/TLS预检、持久启动、原账号PC/H5全业务、252入口和历史附件仍需验收。fullCloneReady=false；源码测试、传输完成均不能代替公网发布成功。
