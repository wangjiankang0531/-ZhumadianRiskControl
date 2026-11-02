# 第三方单位资质独立保存、长度预检与主从事务

本机原页面一次合成新增，列表总4→5、唯一名称0→1；保存前资质1项，详情重开和整页刷新后0项，主表字段仍在。原源save将资质insertBatch置于事故非空分支：没有事故不保存资质，事故存在而资质null/空会分别在XML foreach构建/SQL空VALUES阶段失败。故障样本保持，未直接SQL补数据。

固定Reference SHA ba420cb3938e31d105ad2c1fe6636089664acc53c65c1d7f209fe3db66074a7d，构建独立候选，不改原参考源。最终V2把资质插入移到自身非空分支；保存/编辑在原重复校验之后、身份/正式写入之前，按原varchar(16)拒绝超过16个Unicode字符的证书名，提示“证书名称不能超过16个字符”；两方法显式@Transactional(rollbackFor=Exception.class)。原接口/字典、重复提示与优先顺序、主键/信用码/归属、人员及评价/事故/对接逻辑保持，字段不扩宽。

原/候选严格内存各18场景：null/空/1/2资质 × 有无事故 × 有无评价、重复企业、17字符名称。真实原方法和原MyBatis/XML+MySQL各22场景，除组合/重复/长度外，核验主表及三个子列表编辑回读，保存第2写、编辑第3写故障在候选真实Spring AnnotationTransactionAttributeSource/TransactionInterceptor代理下整组回滚；原不经代理路径的临时部分写作对照。超长新增和编辑均在任何INSERT/UPDATE/DELETE前拒绝。实际执行candidate class SHA 1bac35eef2c07fc8cfb44af14260730bb24b0b3bed09f89f097b8b302850f67b一致。18内存与22 SQL是两层对照，不是完整角色业务验收。

SQL最多2连接，只对4张连接内同名TEMPORARY表写入，每次DML先验TEMP及封闭表集合；永久四表完整行多重集/DDL前后相同，临时表DROP、连接关闭。合成身份接入原helper，DockUtil用严格记录器，未真实登录/HTTP/Redis/外部数据局调用。隔离注解代理证据不证明当前运行容器Bean、真实权限或HTTP失败回滚。

阶段证据：初单调用移动候选内存17/SQL17通过；R1—R4夹具失败全部保留（null foreach阶段判断、异常链不足、合成证书名超16、合成事故类型超2），仅改夹具并依完整物理模型收敛后R5通过。V2内存R2为18、SQL R6新增回滚19、R7完整新增/编辑22通过。没有扩大原字段或弱化TEMP/进程边界。最初真实样本证书名19字符，原前端没有maxLength；最终后台会明确拒绝，前端即时长度提示尚需补齐。

当前阶段不装运行class、不重启本机、不发布公网；250 j41/controller35292/18891/release3f1ee528，公网R5保持，预约事务V2仍未装。后续须组合已验证修正、校验同一基线与白名单、正常停启/备份、实际容器代理和同数据重启，正常登录原页面复验合法资质、超长零写入与编辑保留。全B/S/H5/历史附件/公网隐患500仍未完成，fullCloneReady=false，LOD暂缓。
