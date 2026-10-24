# 原平台运行锁与ID生成器线程池关闭验收（2026-10-24）

记录时间：2026-10-24T17:01:59.492593+08:00。在已恢复验收的独立可写数据库上，两次原Java8 JNPF对照定位并修复了本候选的线程池关闭问题。原上下文关闭后，增加的自有关闭适配使ID生成器定时池正常终止、JVM自行退出。原缺失流程定义的后置初始化异常仍存在，JVM自然退出码仍为1；不能写成原平台正常启动/退出0、真实业务或全面复刻通过。

## 原包、配置与数据边界

原opm-service-admin-3.6.0.jar从Y只读使用，SHA294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8。使用既有自有Java8、原嵌套依赖顺序、缓存资源加载器与已验证进程约束。没有替换原业务、认证、Flowable或ID生成类；没有复制原JAR、GIS或新的整库目录。

数据库复用自有own-mysql-r27，UUID c4ae2011-cf86-11f1-9da8-10ffe0e39b19，两次实际DataSource检查均为正确jnpf/UUID/随机回环端口、JDBC和事务可写、服务器read_only/super_read_only均0、event_scheduler为OFF。本轮是可写候选运行，不能称只读。原252源库及封存、own-mysql-r26恢复基线保留。16:45全行相同证据是原平台运行前的恢复验收；本阶段没有运行后再次全量导出，不能将该历史相同结论扩展为目前工作候选仍逐字节相同。

原注解定时任务/外部集成仍沿用既有诊断隔离，不是完整业务部署配置；没有真实登录、密码、验证码或JWT操作。getLoginConfig两次均HTTP200/应用200/104字节，SHAb7ac34f7f2fe2750dbfed40ad7b318b8eea223c85da9379a596b52fdffa99ffe；未登录CurrentUser仍200/应用600/data=null，认证没有放宽。

## 已确认的两个关闭问题

前次只读own-j3的ProcessEngine.close会调用clearAllProcessInstanceLockTimes，释放运行锁时被只读连接拒绝。当前两次可写运行未再出现该只读SQL异常，两个ContextClosed均已观察。该证据只说明本轮没有复现该拒绝，不代表已验收全部工作流事务或锁竞争。

第一次可写own-pboot-r28仍在关闭20秒后存活，由自有控制器终止；0.5秒线程快照有Netty全局线程和sysTaskExecutor1，5秒只剩sysTaskExecutor1与DestroyJavaVM。线程栈停在ScheduledThreadPoolExecutor延时队列。

静态逐类SHA核对发现，原AsyncConfig提供sysTaskExecutor线程工厂；原IdGeneratorConfig.initIdWorker创建静态ScheduledThreadPoolExecutor，每1800秒续期Redis工作节点占用。它的私有onDestroy方法带javax.annotation.PreDestroy，但仅删除Redis键，没有关闭定时池。原类SHAb7ed1fb8a39644f77b90a385d04fe6945e8e88b02f8d68ca87e6a196ecb746a3。另有3个原任务类也创建类似池，未按线程名批量操作这些池。

## 自有关闭适配与实际对照

OriginalIdGeneratorShutdown只在显式own.platform.manage.id-generator-shutdown=true和实际Servlet上下文中启用。它先核验原所有者class资源SHA、已存在的唯一原Bean、静态字段名和精确ScheduledThreadPoolExecutor类型。未知版本、缺Bean或字段形状不符均记录失败并不触碰线程池，不按线程名寻找或停止线程。

就绪时只观察线程池，不改变其行为。ContextClosedEvent后，对这个准确所有的池调用shutdown并最多等待2秒；不调用shutdownNow、Thread.stop或System.exit，也不修改定时任务逻辑、原ID生成器和原销毁方法。原销毁流程随后照常执行。适配只负责资源生命周期，不能用于跳过原认证、流程初始化或数据异常。

第二次own-pboot-r29实际就绪记录池尚未shutdown、延时队列1项、已完成任务0。关闭记录原class pin通过、正常shutdown已调用、2秒内终止且队列0。平台JVM自行退出，收据无ownPlatformTerminated；MySQL和Redis正常0。Java适配前后的缺失定义标识SHA相同，原main仍未返回；自然退出1如实保留，未转换成0。lifecycleCloseVerified=true仅覆盖上述资源关闭，platformStartupVerified=false。

## 初始化分支核对

原JnpfAdminApplication.main在SpringApplication.run后执行FlowableLoadUtil.init，MultiTenancy=false时进入该分支。只读核对原application.yml确为MultiTenancy:false，pro/test配置的sharding-sphere-enabled也为false；不是为通过启动把隔离配置改成false或true。原初始化失败定义与封存数据中4个缺失定义之一一致，9条临时记录引用关系仍保留。没有删除、改ID、过滤原记录、跳过原初始化或替换原认证来得到成功结果。

## 源码、复现和验证范围

4个自有工具为tools/java/PlatformWritableObservation.java、tools/java/OriginalIdGeneratorShutdown.java、tools/prepare_original_platform_lifecycle.py、tools/verify_original_platform_lifecycle.py。依赖既有冻结own-pboot-r27加载器/观察基线、own-mysql-r27候选、Java/MySQL/Redis运行时和Y原包，并非仅从Git即可全新构建的最终交付包。

先运行prepare_original_platform_lifecycle.py --workspace <tianjin_native_20261023> --name <全新own-pboot-r数字> --previous-receipt <上轮已终态收据>；再运行verify_original_platform_lifecycle.py --workspace <同目录> --name <相同新名> --independent-wrappers --probe-admin-config-on-ready。准备阶段不启动应用。重复使用目录被拒绝；真实进程和数据库目录占用须在运行前重新核验，不能凭历史PID处理进程。

源码准备CLI已实际完成own-pboot-r30，两类编译字节与真实r28/r29运行字节完全相同；5项路径/基线/已有目录负例均在启动前拒绝。诊断CLI帮助通过，已增加共享控制器锁、观察收据汇总与明确资源关闭门槛；门槛不通过退出1，通过仅代表lifecycleCloseVerified，并另记platformStartupVerified。整理CLI没有再次运行原平台，不宣称其端到端单次全绿。r30仅准备、无attempt_started、无服务运行。

本阶段业务表字段、索引和模型未变，未做DDL更新。实际配置和参数、原字节码/反汇编及线程日志在私有work，不入Git。公开源码仅这4个自有文件及本handbook。

## 下一步与保留状态

继续保留全部原流程数据，处理缺失定义及启动失败边界，完成真实登录/CurrentUser/业务HTTP、工作流与PC/H5/管理子应用全操作、公网同版、备份运维及长稳验收。当前原平台不能作为全面复刻完成版发布。正式公网及250/252演示不改，20秒外围清晰度、EXE/网页协同及完整长期引擎目标仍未完成，fullCloneReady=false。
