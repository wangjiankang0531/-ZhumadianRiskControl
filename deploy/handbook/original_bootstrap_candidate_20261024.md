# 原流程资源核对与启动兼容候选验收（2026-10-24）

记录时间：2026-10-24T17:18:19.791954+08:00。本阶段保留全部原测试数据，在独立可写候选中验证了启动兼容处理：原初始化只对存在定义的记录继续执行；缺失定义且原Flowable查询确认没有运行/历史引用的孤立临时记录保留并报告。原main正常返回，平台、MySQL、Redis自然退出0。该改动改变了原包启动时的列表视图，属于兼容候选，不代表缺失模型已恢复或原行为完全等价，更不是全面复刻验收通过。

## 封存资源依据

只读使用252既有v2封存导出，manifest SHA cdac2c99a5d43a4daabea7bf547d7ea9fbda8b2a4a3b491f98b95a5fcfc76b5d。未重连源库或再导出。核对jnpf完整流127268733字节/SHA5814f66415248c1df04959c81598dbf190f55333ded982e36d0c05dc4aa8ce80，所选9表行数与封存清单相同。

645个act_ge_bytearray资源中80份可解析XML、565份非XML，得到7个不同BPMN过程Key；77个部署定义、80个部署、80条flow_template_json、16条flow_template、243条flow_definition均检查，act_re_model与flow_task各0行。4个缺失定义在现有资源/设计表中没有找到精确Key或定义引用恢复依据，也没有对应Key原始字节候选。该搜索不能证明未来其它备份或原运行内存缓存也无恢复依据，不能凭空补造定义或换成其它版本。

审计器仅输出计数/哈希，未保存原行、XML或模型内容；XML拒绝DTD/实体，大小受限，区分子串候选与精确过程Key。即使找到Key也不把它当作原版本、原部署及元数据精确恢复证明。7项Python检查覆盖命名空间、UTF8/UTF16实体拒绝、二进制/大小限制、子串误命中、候选合并、隐私输出和清单路径范围。

## 启动兼容策略与边界

OriginalBootstrapOrphanGuard为自有Spring初始器，只有显式own.platform.rehydrate-existing-definitions=true才启用。它逐SHA核验原FlowableLoadUtil、FlowRunAddNodeTemplateEntityServiceImpl及实体类，再通过Spring代理委托原对象。未修改原JAR、认证、用户权限或原GenerateActivityUtil方法。

线程局部标记仅在原FlowableLoadUtil.init调用期间存在。原Service.list得到完整原列表后，查询原RepositoryService确认每个定义是否存在；缺失时继续查询原RuntimeService和HistoryService，确认该定义和已提供实例ID均无运行/历史引用。查询失败、存在运行/历史引用、未知类型或class pin不符均失败，不作忽略。只有这些已确认孤立的临时记录在该次初始化列表视图中隔离；其余记录按原顺序、原实体对象交给原初始化继续执行。

这不是对数据库记录的删除、更新或搬迁，也不是普通业务列表过滤。原方法仍被真正调用；退出标记清理后再次通过原Service.list读取完整列表，比较记录ID、定义ID、实例ID及模型内容的签名。不存在全局租户/权限/认证放宽，也不把异常流程伪造成正常流程。

10项Java合成策略检查覆盖有效列表原对象、混合列表原对象保留、重复定义查询、运行引用、历史引用、实例引用、查询失败、无效定义和公开报告不含原标识。未知/仍有业务关联的数据拒绝隔离。失败收据不能作为成功计数使用，验收必须同时检查原方法完成、普通列表签名和进程状态。

## 实际原平台结果

own-pboot-r31复用own-mysql-r27自有可写候选与本轮私有回环Redis，原Java8 JNPF仍从Y只读加载。原初始化看到10条临时记录，其中1条有效记录执行完原初始化；9条关联4个缺失定义的孤立记录保留并按定义哈希报告。原方法调用与完成均观察到，作用域内Service.list只调用1次；退出作用域后普通列表仍10条，四项关键字段签名一致。没有本轮全数据库运行后导出，不将关键字段签名扩大成398表当前仍逐字节相同。

控制器等待原main返回或明确的初始化观察收据后才发送关闭请求，避免在ApplicationReady后置初始化尚未完成时提前关闭。原main确实返回，平台进程自然退出0，无强制结束；准确所有的ID续期池2秒内正常终止，MySQL和Redis正常0。实际原DataSource身份、端口和jnpf正确，JDBC/事务可写。源机、封存与own-mysql-r26原恢复基线保留，基线563文件SHA再次全部一致。

getLoginConfig为HTTP200/应用200/104字节，SHAb7ac34f7f2fe2750dbfed40ad7b318b8eea223c85da9379a596b52fdffa99ffe；未登录CurrentUser仍应用600/data=null。两个匿名GET发生在初始化完成前，原main最终状态以终态收据为准。没有执行真实登录、验证码、JWT或认证业务接口，不能将匿名配置成功写成登录通过。

## 源码、复现与维护

自有源码/测试为tools/audit_original_workflow_recovery.py、test_audit_original_workflow_recovery.py、java/OriginalBootstrapOrphanGuard.java、java/BootstrapOrphanPolicyFixture.java、prepare_original_bootstrap_candidate.py、verify_original_bootstrap_candidate.py，加本handbook共7文件；不含Reference原工程、原字节码、资源、业务数据、运行包或凭据。

审计命令接受--export、--manifest-sha256和全新--output。准备命令接受--workspace <既有tianjin_native_20261023>、--name <全新own-pboot-r数字>、--previous-receipt <上轮已终态收据>。准备过程核对固定Spring-AOP依赖SHA、运行10策略检查，再准备新独立目录，不启动应用。随后用verify_original_bootstrap_candidate.py --workspace <同目录> --name <相同新名> --independent-wrappers --probe-admin-config-on-ready运行。依赖既有冻结加载器、own-mysql-r27候选及运行时，不是全新Git检出即可直接部署的最终安装包。

整理控制器源码与实际成功运行版本逐字节相同。准备CLI已实际生成own-pboot-r32及bootstrap-build，5个守卫class与实跑字节完全相同；r32仅准备、没有启动，不需为源码整理再重复相同数据库试验。执行前仍需核验实际进程、目录占用和身份，不凭历史PID操作。原任务注解/外部集成保持既有诊断隔离，这不是完整生产业务配置。

候选进程现均已终态；历史随机端口不是可用体验入口。原9条记录仍需在后续数据质量界面/记录中明确提示并寻找真实模型恢复来源。下一步组合原PC/H5/管理前端和业务后台、共享缓存，完成真实登录/CurrentUser/HTTP业务、全部模块操作、数据写入/恢复及公网同版验收。正式演示不改，fullCloneReady=false，完整长期引擎与驻马店目标继续active。
