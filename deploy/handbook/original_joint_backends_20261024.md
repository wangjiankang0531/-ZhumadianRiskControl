# 两套原后台共享资源联合诊断（2026-10-24）

记录时间：2026-10-24T16:31:14+08:00。本阶段在250的独立回环环境同时运行原业务后台及原JNPF平台，共用一个既有自有只读MySQL副本和一个全新私有Redis。实际原Bean跨进程缓存往返通过，原只读服务11项通过；真实HTTP登录、权限、工作流及完整复刻仍未通过。本轮未发布公网，也未操作正式8767和252画面。

## 设计与源码

tools/verify_original_joint_backends.py 为本机冻结候选的诊断控制器，显式接受 --workspace、--name 和 --previous-receipt。workspace为既有Application/work/tianjin_native_20261023；name必须是全新own-j数字短目录，程序会检查临时路径不超过80字符；previous-receipt须证明上轮自有应用已退出、MySQL/Redis正常退出0。该工具依赖既有own-pboot-r27、own-dbboot-r5、own-mysql-r26、原共享flat运行目录、已验证Java8/17、加载器和进程约束，并非可直接部署的成品服务。

工具先核对原归档、运行时和自有边界/加载器SHA，只编译自有观察器。原JNPF归档仍从Y读取，原业务flat及219依赖复用现有目录；自有加载器/构建器硬链接复用，没有复制原归档、GIS、物理源库或整套252环境。MySQL仍为自有UUID c0a47e62-cf57-11f1-9120-10ffe0e39b19，事务与全局super_read_only均打开，事件和异步调度维持既有诊断隔离。未启用真实写业务模式。

新Redis仅绑定127.0.0.1，随机口令，禁持久化，96MiB上限。两个原应用采用同一连接元数据，经prepare_original_shared_redis.py分别生成spring.redis和spring.data.redis覆盖项，并在本轮各自配置位置列表最后加载。控制器只在新MySQL已就绪且PID一致后更新自有所有者文件，避免启动失败时冒认现存服务。

tools/java/OriginalJointRedisObservation.java 仅在实际Servlet Web上下文的ApplicationReadyEvent后执行。它核对主机、端口、数据库和口令与私有期望值一致，但公开观察结果只写比较布尔值；通过实际连接PING和INFO server核对Redis真实process_id，两侧均与控制器新建Redis一致。此处有真实Redis网络连接，均限本轮自有回环端口。

随后平台侧从实际Spring上下文取得原RedisUtil Bean，构造六个字段均为合成值的原LoginUser，写入本轮随机的 __xnby_joint_wire_ 前缀键。该键不是原用户缓存前缀，不含真实用户，不生成或接入JWT/HTTP会话。业务侧取得原SessionManager和Jsons，读同一键并逐字段比较，再删除且确认不存在。直接Bean检查不代表通过HTTP鉴权，也不能据此授予用户权限。

## 实际结果

从Application源码CLI运行的own-j3完成原Bean真实跨JVM缓存写读：六字段一致，合成键删除，两侧有效配置均匹配同一私有Redis进程。两个原Web上下文都观察到ApplicationReady事件。业务原Service/Mapper、数据库身份、事务与全局只读、零行更新仍被MySQL1290拒绝、中文正则、企业组织读取等11项全部通过。

原平台getLoginConfig仍为HTTP200/应用200/104字节，SHA b7ac34f7f2fe2750dbfed40ad7b318b8eea223c85da9379a596b52fdffa99ffe；未登录CurrentUser仍为HTTP200/应用600/data=null。业务无认证头请求/checkItems/page仍为原HTTP500/应用100000，保留原SecurityInterceptor空头异常行为，不把它称为正常鉴权成功或本轮业务API验收通过。没有提交登录、密码或验证码。

平台后置Flowable初始化的既有缺失定义错误仍存在，original main未返回。本轮向两个自有上下文发送关闭文件请求，两个ContextClosed事件均已观察；业务正常退出0，平台20秒后仍存活，由控制器结束该自有进程、退出1。不能把关闭事件或本轮缓存通过写成平台初始化/优雅停机通过。Redis和MySQL通过各自正常协议退出0，所有本轮进程已终态。

完整收据在Application/work/tianjin_native_20261023/own-j3/receipt.json，两侧joint-redis-observation.properties不含口令；实际凭据、配置和启动参数文件仍属私有工作产物，不入Git。本诊断控制器会保留失败收据并打印摘要，进程退出码本身不是验收依据；必须检查收据各项及原平台错误/强制终止标记。

## 失败记录与修正范围

首轮own-joint-backends-r1因新目录层级太深，JDK17选择器的本地套接字路径过长，退回内部TCP回环，被既有端口约束拒绝。只缩短新目录，未放宽进程约束；该轮业务/平台退出1，资源正常0，记录保留。

第二轮own-j2中业务成功启动，自有观察器误在非Web引导上下文提前查找redisTemplate，记录NoSuchBeanDefinitionException。限定Servlet上下文后第三轮完成真实往返。前两轮控制器和观察器源码、错误记录均保留；没有修改原认证或原后台类来消除自有诊断错误。

## 使用、维护与边界

从Application/tools执行python verify_original_joint_backends.py --workspace <既有候选工作目录> --name <全新own-j数字短名> --previous-receipt <上轮已终态收据>。每轮启动等待最多150秒，应用关闭等待20秒，再正常关闭自有Redis/MySQL；不重复使用旧name，不把收据文件单独当作进程仍活或已经退出的证明。运行前应实际核验没有其它进程占用这份自有MySQL数据目录；MySQL自身目录锁和本工具控制器锁不能替代全部外部进程审查。

工具启动两个原应用，内存上限各512MiB；只读引用原资源。原库和用户DLG不改，数据库字段/索引/状态/归属不变，不涉及数据库模型生成物更新。三维演示仍由独立正式8767运行，复查starts=1/alive=true/failed=false、store.failures=0、protectedWrites=0。原20秒外围清晰度仍未验收。

下阶段需保留原完整业务数据与认证，完成真实登录、CurrentUser与HTTP业务请求、写业务的独立备份/恢复设计、Flowable数据/交付物关系及停机修复、所有PC/H5/子应用操作、公网同版。现有诊断配置仍禁外部集成和定时任务，不能直接作为正式业务部署配置。fullCloneReady=false，长期完整目标保持active。

本轮2个自有源码（诊断控制器及观察器）加本handbook，共3文件仅本地保存；不含原Reference、业务数据、GIS、原运行包、私有配置/口令、截图或14项held。不扩大待确认14文件镜像7c21b8c2的范围。
