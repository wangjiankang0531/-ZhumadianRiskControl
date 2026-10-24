# 原测试库导出 v2：FLOAT 保真及恢复表达式

真实 MySQL 8.0.44 自有夹具证明：旧 `HEX(CAST(float_column AS BINARY))` 会因 FLOAT 文本表示的精度改变原生值，重新导出的 HEX 仍可能相同。旧 v1 文件可以继续作完整性诊断，但不能据此宣布 FLOAT 无损恢复。原库数据、原库版本及完整业务联调仍未完成。

## 格式与版本边界

新生产器输出 `tj-original-jdbc-hex-v2`。manifest 和 catalog 同时写入下面的完整 rowProjection 合同，验证器要求两处与固定定义完全一致，拒绝只改版本标签：

```json
{"float":"hex(cast(cast(column as double) as binary))","default":"hex(cast(column as binary))","sqlNull":"json-null","generatedColumns":"excluded"}
```

只有原列 DATA_TYPE 为 FLOAT 时，先提升为 DOUBLE，再转 BINARY 文本并 HEX。其余列保留原表达式；SQL NULL 与非 NULL 空值仍分别为 JSON null 与空字符串；生成列不写入行流。行大小上限使用与实际字段相同的投影计算，保持每行 4 MiB 值预算。

有可写 FLOAT 列时，生产器及验证器均要求已识别的 MySQL 版本至少为 8.0.17；MariaDB、过旧或未知版本拒绝，不以猜测回退。CAST AS DOUBLE 从 8.0.17 加入，参见 [MySQL 官方转换函数文档](https://dev.mysql.com/doc/refman/8.0/en/cast-functions.html)。原版本仍须通过原环境实际核对，不能把本机 8.0.44 当作原版本。

验证器兼容读取 v1，报告 legacyFormatDiagnosticOnly；当 v1 有可写 FLOAT 时，legacyFloatEncodingRisk 为 true。恢复表达式模块对 v1 FLOAT 明确拒绝。已经因旧文本表示丢失的位不能靠给文件改标签或改恢复程序找回，必须重新读取原数据。文件、摘要及失败证据保留，不静默改写。

## 恢复表达式

original_export_codec.py 只产生含占位符的表达式及验证 HEX 参数，不连接数据库、不执行原 DDL 或 DML，也不是一个已经完成的整库恢复执行器。

| 列类型 | 参数化表达式 |
| --- | --- |
| v2 FLOAT、其它数值、日期时间、二进制 | UNHEX(?)，由目标列执行原类型赋值 |
| JSON | CONVERT(UNHEX(?) USING utf8mb4) |
| BIT | CAST(CONV(?,16,10) AS UNSIGNED) |
| 有字符集的文本、枚举、集合 | 按已校验列字符集 CONVERT(UNHEX(?) USING charset) |
| 空间值 | UNHEX(?)，保留 MySQL 内部字节与 SRID，不自行改轴顺序 |

原数据始终作为参数，不能拼入 SQL。列类型、字符集及 HEX 形状不合法时拒绝；生成列禁止显式恢复。实际恢复还必须验证目标独立实例身份、原 DDL/索引/外键/权限、版本/SQL mode/字符集及字段原生值。上述表达式已在选定自有样本验证，不能外推所有空间类型、字符集、SQL mode 或所有 MySQL 版本。

## 实测证据范围

Java 自有检查 34 项，分别在既有 JDK 和精简 JRE 上通过；新封包中的同一组 34 项也通过，这不是 102 个不同测试。Python 共 49 个不同测试：导出验证 28、恢复表达式 6、文件多重集合比对 15。新旧格式即使行内容相同，也报告 exportFormatEqual=false，不能判定完整导出内容一致。

真实独立 MySQL 中，24 个字段覆盖 21 种 SQL DATA_TYPE，三组边界/NULL/空值的 72 项恢复语句、HEX 和原生签名均一致。Python 恢复表达式逐项与实际执行的 Java 表达式一致。另有 2,048 个确定性有限 FLOAT 位样本，包括正负零、非正规数、最小正规数、最大有限值和固定种子随机值；输入均被接受，源存储未改变输入位，v2 恢复原生位变化为 0；旧表达式对照为 1,975 个变化。该样本覆盖不是对全部 FLOAT 位型的穷举证明。

新生产器还在实际只读一致性事务中生成了 6 张自有夹具表、6,153 行的 v2 封存产物；Python 完整性验证通过，实际回滚结束。全部是本机自有数据，没有原数据库连接或原业务写入。验证器的 fieldTypeRestorationVerified 仍为 false：单独验证文件不证明实际执行过恢复；真实字段夹具的证据另行保存。

## 独立候选与上线门槛

新 GUI 候选保持旧原配置路径、源主机及预期配置 SHA，使用新的独立输出根 F:\TianjinReadOnlyExportV2_20261024\exports。通过 174 个硬链接复用现有 JRE/依赖，仅替换新目录中的 JAR 和配置文件；旧 176 个文件逐 SHA 不变。目录逻辑体积约 50 MB 不能当作新增加同等物理空间，也不能将删除硬链接当作已释放全部逻辑字节。

新候选仅在本地封包并执行 CLI 自有检查，没有启动 GUI、上传共享盘或读取当前原配置。原库首次运行之前，必须重新核配置 SHA、当前源版本及候选所有文件，并获得该新 GUI/一次原站只读导出的行动时确认；旧 GUI 或旧载荷授权不能扩成新候选。仍沿用一次源连接、20 分钟、512 MiB 压缩输出、只读一致性事务、结束回滚/关闭及失败留证的约束。

旧 v1 GUI 和旧 22 文件固定镜像继续保留并停用，不能因收到旧确认就发布。新格式及恢复规则没有改变项目业务数据库字段/索引/状态/归属，不生成替代原库模型。原完整测试数据恢复、Java/JNPF 真实业务、登录/角色、保存/审批/导出、电脑和手机全模块及公网同版验收仍未完成，第一阶段未达成。
