# 天津原平台 Java 8 启动对照与验收边界（2026-10-24）

本轮继续原前端、原后台、原测试数据和PC/手机内部操作严格复刻。完整UE级引擎及驻马店EXE/网页图层等长期目标保持active。此记录仅证明兼容性诊断推进，fullCloneReady=false。

## 原件与运行范围

只读引用共享opm-service-admin-3.6.0.jar，SHA256为294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8。原业务类、379个依赖及其顺序不改，不复制230MB整包。仅运行自有回环MySQL恢复副本和独立Redis；源数据库连接0，已授权的单次导出没有重复，外部源账号未用于连接。数据库super_read_only和transaction_read_only开启。没有更改Windows安全设置或安装系统服务。

自有原平台JVM由原Java17改为本机既有Zulu8u504，原工厂ScriptEngineConfig.nashornEngine()调用ScriptEngineManager.getEngineByName("js")，Java17缺失脚本引擎的原因得到确认。没有伪造ScriptEngine Bean、修改原工厂或跳过原工作流。自有观察/约束class目标major52，配置构建器及关闭MySQL工具继续用已验证Java17。

## 进程约束与实际对照

Java8的SocketOutputStream会调用描述符写检查，只为该bootstrap JDK类的精确调用路径兼容；直接标准输入/外部文件描述符写仍拒绝。Windows Selector通过bootstrap PipeImpl建立内部回环唤醒管道，只为该内部连接路径兼容，应用到未列明端口和非回环地址仍拒绝。最终26项夹具通过，含真实Selector、指定端口成功、未列明端口拒绝、外网/DNS/URL/NIO/数据报拒绝、直接描述符拒绝、进程/非JDK DLL/约束替换拒绝。Java11 HttpClient在Java8不存在，其原检查没有冒称执行，适用的直接SocketPermission/URLPermission另作检查。

Java8两组独立原Spring对照均通过：组件2501份，排序URL SHA256 3de893888ccaf0a67538faea221645d6e420aed6ad8eb57598b09446ae10ce15；Mapper14份，排序URL SHA256 988ebcd928eeb4e3af71294502ec8794ba7e7eff13b276d19286cb1677cdcfad。每组5个原class字节/链接、扫描后冷类和原Bean命名检查通过，实际JDK Nashorn的1+2计算通过。探针不等同原工作流操作通过。

前期自有诊断观察器显式setBeanNameGenerator改变了原Spring导入命名，导致jnpf.SwaggerConfig与org.springdoc.webmvc.ui.SwaggerConfig冲突。已移除该覆盖，未删除原Swagger模块。最新观察到两者分别保留原Bean名和完整限定名；12个预检相关class字节未变，原资源对照证据按SHA复用，没有重复全部夹具。

## 最新结果与主故障

own-pboot-r24原上下文刷新及ApplicationReady事件实际出现，但原main随后调用FlowableLoadUtil.init()时抛FlowableObjectNotFoundException，main未返回。因此originalPlatformReady=false，不能把Boot事件作为完整启动成功。180秒上限后仅结束本轮仍存活的自有Java，退出1、未正常执行关闭钩子；MySQL和Redis均正常退出0。日志和终态记录保留。

两个未登录GET /api/oauth/Config、/api/oauth/GetConfig的HTTP均200，实际应用返回码均600、data=null，原认证拒绝请求，登录配置尚未取得。没有尝试登录、猜测密码或伪造JWT；HTTP200不计作认证成功。

只读核对FlowableLoadUtil字节码：原main在SpringApplication.run后、非多租户分支执行该初始化器；初始化器读取FlowRunAddNodeTemplateEntityService.list并调用GenerateActivityUtil.addMultiNode。流式审查既有封存jnpf导出127,268,733字节，SHA256 5814f66415248c1df04959c81598dbf190f55333ded982e36d0c05dc4aa8ce80，与此前完整往返相同。

act_re_procdef原77行、flow_run_add_node原10行；其中9条临时节点记录引用的4个定义不在存储定义表，启动异常目标对应其中4条。该组合的隐式引用问题不是恢复漏行的证据。没有删除、屏蔽、改写原记录，没有复制原始行到D。当前尚未证明所选包及profile/外部配置与原站实际运行环境完全相同，不能直接推断源站冷启动行为。下一步核对实际在用配置及流程资源，按原行为恢复，不能通过跳过初始化或清空记录缩小验收范围。

## 演示及持续工作

13:21完成的公网项目测试版演示更新、250/252各自8767三维入口继续保留。此次原平台诊断没有更改公网文件、业务库或演示服务。演示入口不等于天津严格复刻阶段验收，20秒外围全部清晰要求也未验收通过。

本轮29份自有诊断源码按SHA私有封存于Application/work/tianjin_native_20261023/capture_tools_v4/original_platform_bootstrap_r24_20261024；运行收据、原字节码形状和只读关系审查在同一工作根目录及Document/Deployment/original_platform_bootstrap_20261024。它们不作为生产发布包；Reference原源码、业务数据、原class、运行包、凭据、私有日志及14项held不入Git。本次Git仅新增本说明文件。7份设计、实现、验收与部署运维连续性文档已更新；数据库字段、索引和归属没有变化。

仍需完成原认证/权限与工作流初始化、原业务HTTP、全部PC/手机模块操作、保存/审批/Excel/地图，以及公网同版验收。阶段达成后再通知用户复核。
