# 原业务接口与登录权限契约复核

本轮使用自有ASM只读工具扫描既有候选应用包的768个class，发现85个直接控制器和687条直接Spring映射。执行classpath只含自有读取器和已有Spring Core；原应用包仅作为ZIP字节输入，不定义或执行原应用类。工具读取RequestMapping及Get/Post/Put/Delete/Patch映射的直接path/value和method条件，记录父/子方法冲突及其它条件是否存在，不输出header条件值。继承/组合注解、库控制器和运行时注册不在覆盖范围。

自有EndpointInventoryFixture产生不会加载的合成class字节，验证多路径、HTTP方法交集/冲突、默认路径/ANY、未标注方法排除、条件值不输出和JSON转义等10项。运行工具前应固定既有application.jar和Spring Core SHA，输出必须为新文件；本轮输入包和依赖前后SHA/大小/mtime保持，未下载或复制依赖。

原PC/应急PC/H5的117个API/服务文件与Reference逐字节一致。633处识别请求表达式中，438为静态已知包装器业务请求，431路径和HTTP方法直接对应；7项无应用类直接映射、0方法冲突。动态/其它服务/平台/未知外部包装器保留待核，不把API声明存在当页面正在调用或功能通过。PC下载包装器实际为GET；前缀比对沿用原网关serv转发规则。

7项直接映射未定位的声明，在891个业务src文件未发现直接导入/重导出；电脑端模板引用和手机端脚本调用两项正例均能找到。该结果不证明未使用，不能删除原声明、补造后台或假报修复完成；间接barrel、动态引用、第三方src/uni_modules和角色需实机核对。验收重点保留在私有项目文档，原端点清单、Reference原源、class、SDK、配置、业务数据和账号不进入Git。

原登录PermissionModel.button的元素PermissionVO.visible为String；管理端ButtonModel.visible为Integer，两者不可混用。原Java8/Jackson2.13.5的原DTO构造访问器及本方合成序列化11检查通过，与既有Java17字节一致；原前端三段纯函数执行10检查通过，完整原应用/数据库/认证未执行。原前端路由合并只收path与urlAddress均非空项，按modelId挂载，操作visible为字符串0时隐藏侧栏但保留路由，组件定位按原index.vue规则。

本阶段不改变应用、权限、元数据或数据库。Y共享恢复后仍须启动完整候选、正常账号登录，逐模块对照页面/字段/筛选分页/增改删/导入导出/特殊作业/审批与附件/H5真机，最后才可公网部署与用户复核。静态匹配和合成检查不是上线或阶段目标完成证明。
