# 天津原大屏第三后台：源码与协议接入阶段

本阶段使用参考目录的 bigscreen_java 原源码和原 tjwhyq-base.jar，验证原行为，尚未替换当前网页或公网。完整天津项目复刻未验收。既有 PC/H5/平台原版候选及正式 8767 三维入口保持。

原六套工程中，大屏另有独立 Spring 后台。原 /collaborate/{userId} 提供协同标绘；/interact 与 POST /wsi/interact 转发交互消息；另有海康查询/检索/控制接口。两个先前接入的原后台不能代替此组件。

## 已验证证据

- 固定 Java 8、原 73 个依赖及 Lombok 1.18.2 重编 26 个原 Java 源文件，27 个 class 与原包逐字节一致，原源码/JAR 未修改。
- 固定 SQLite JDBC 3.36.0.3 及 Windows x64 单 DLL，13 项实际 JNI/范围拒绝检查通过。两项 Maven 官方 SHA1 匹配，SHA256 为本地固定值；不得写成官方 SHA256 核验。
- 原 main 实际启动并绑定自有回环端口，两客户端读取原四条数据、同步增删并提交 SQLite、HTTP 转发至交互 WebSocket 均通过。原空视频参数校验通过；未连接真实视频设备、未执行 PTZ 控制。
- 原程序在最后客户端退出时清空 SURVEY。首客户端退出保留四行、末客户端退出清空的原行为已验证，仅影响自有 12 KiB 副本；参考库和驻马店 DLG 不作运行数据库。
- 测试正常关闭，ContextClosed 和进程退出 0 均观察到；非零、未就绪、协议失败或强制终止不能算通过。初次自有协议脚本 HTTP 名称遮蔽错误的失败记录保留，修正后独立新目录通过。
- 大屏静态清单为 9 文件、104 调用：16 个 Mock、85 个原业务、3 个独立大屏后台调用，另 2 个动态调用未解析。没有以默认快照替换全部原业务逻辑。
- 16 个原匿名 Mock GET 默认响应共 3886 字节已采集，本地只读服务 25 项检查逐字节一致。未发送项目 Cookie/JWT/查询参数；不是同一时点事务快照，带参筛选与写入语义未验证，数据不入 Git。
- 原共享请求封装会向外部 Mock 附加 Cookie token。自有适配只把 Cookie 派生 token 限定同源、Mock 改为本机挂载，39 项无网络/合成 Cookie 检查通过。当前构建尚未应用，禁止把此结论写成运行网页已修复。

## 复现与部署运维

在 Application 使用 Python 3.11+，依次执行 tools/verify_original_bigscreen_source.py、verify_original_bigscreen_native.py、verify_original_bigscreen_protocol.py 的 --help 并按显式参数提供既有 workspace 和全新 output。source 可用 --reuse-dependencies 指向同 SHA 的既有依赖，以硬链接复用约 47.9 MB；不复制整个原 JAR、GIS 或数据库。

工具依赖 workspace 内既有 own-pboot-r32/preparation.json 的固定 Java 8 与自有兼容 helper，并校验原包、原库和 JNI 固定 SHA。它们为当前工程复现工具，不是脱离既有准备目录的独立发行包。protocol 只在新根运行，最多 300 秒；请求正常关闭后等待 18 秒，若强制终止必须记失败，不作为正常通过。

专用 Java 边界只允许自有根内准确路径/长度/SHA 的 SQLite DLL，不放宽已有两后台边界。JNI 可绕过 Java 文件拦截；此机制不是可执行不可信 SQL 的操作系统沙箱。真实受控原 SQL 和副本路径已核对。原启动日志存在 8 次可选 APR 原生库拒绝、3 次本机名称 DNS 拒绝、1 次 Tomcat 关闭自连拒绝，均保留，不称零拒绝；服务回退 Java NIO 并正常关闭。

持久化前必须区分驻马店用户 DLG 与原 SURVEY 临时协同数据。若未来产品要改变末用户退出即清空行为，应形成独立需求和数据迁移方案；本阶段保持原逻辑，不静默改变。SURVEY 原字段 id(TEXT 主键)、user(TEXT 非空)、type(TEXT)、data(TEXT)，原库无本轮 schema 修改。

当前平台 UserData/TianjinOriginalObjectStore 与 UserData/TianjinOriginalPlatform 是持久用户数据，严禁作为测试缓存清理。公网 R2 和现有 8767 保持原样。本阶段只上传自有工具/测试/本文/依赖指纹，不上传原源码、SDK/JAR/DLL、SQLite、匿名响应、业务资料、截图或凭据。

## 后续验收缺口

应用同源适配后重建独立原大屏网页；接入第三后台与 16 默认数据的网关；核对两处动态调用及真实筛选/写入；原登录、角色、PC/H5 全模块、附件关联/历史对象、手机实机、252 原环境配置和公网同版均待。完成全部阶段矩阵后通知用户复核，不以组件通过声明完整复刻上线。
