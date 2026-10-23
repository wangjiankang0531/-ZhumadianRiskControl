# 天津原测试库导出与恢复后导出内容比对

本工具用于严格复刻验收中的数据核对：输入一次原测试库封存导出，以及恢复后数据库重新导出的封存结果。先对两份 `tj-original-jdbc-hex-v1` 导出分别执行既有完整性验证，再比较原始字段字节、重复行数量及元数据。工具本身不连接数据库、不执行导出里的 DDL、不给业务表补造记录，也不进行恢复操作。

当前已完成工具和自有夹具验证；原测试库导出尚未到位，没有执行原库恢复、真实 MySQL 字段往返或真实业务验收。夹具中的记录仅验证工具行为，不是供天津或驻马店系统使用的测试数据。

## 为什么不能只比较流摘要

原导出器通过 `HEX(CAST(column AS BINARY))` 保存字段，SQL NULL 保留为 JSON null，生成列不输出到行流。原查询没有保证行排序。两次合法查询即使数据相同，也可能产生不同的流 SHA。因此本工具以完整规范行字节为键，比较多重集合，忽略行的枚举顺序，同时保留每种行的重复次数。

SQLite 仅用作本机私有临时计数文件；键包含 schema、表名和完整规范行，不仅比较行摘要，不存在“不同数据碰巧相同摘要就当作同一行”的判断。重复缺失、多出、NULL 与空字符串互换、同样总行数下替换内容，均形成差异。行按照导出列顺序比较；同时检查列定义及顺序，不能把两个不同列布局的同样行字节算作完整一致。

## 元数据与报告含义

数据库、表、视图、触发器、事件、过程和函数按对象标识配对，比较捕获的完整定义。只忽略对象枚举顺序及 sourceState.sourceTime；不改写 DDL、AUTO_INCREMENT、生成表达式、索引、外键、字符集、排序规则、DEFINER、SQL mode、服务端版本或辅助对象时间元数据。定义差异只记录对象键摘要和左右摘要，供私下进一步核对，不自动“修正”原定义。

因此合法恢复产生的对象创建时间等差异也可能报告为元数据差异，需要结合原始私有文件判断。工具采取保守判定，不能以忽略未知差异获得验收通过。

报告主要字段：

| 字段 | 含义 |
| --- | --- |
| rowMultisetsEqual | 两份导出中非生成列的规范行字节及重复次数相同 |
| metadataExactlyEqual | 捕获的全部对象定义一致，忽略对象枚举顺序 |
| sourceContextEqualExceptCaptureTime | 除采集时刻外，两份导出 sourceState 一致 |
| exportedContentEqual | 上述三项均成立 |
| restoreExecutionVerified | 恒 false；文件比较不证明执行过恢复 |
| fieldTypeRestorationVerified | 恒 false；还需要真实 MySQL 与字段类型往返证据 |
| generatedColumnValuesCompared | 恒 false；现有导出不包含生成列值 |
| originalBusinessBehaviorVerified / fullCloneReady | 恒 false；仍需原业务和全部页面操作验收 |

报告不输出原字段值、原 DDL、对象名或本机路径；对象差异以摘要引用，表报告保留固定 schema 名及表键摘要。文件 SHA 能证明给定文件内容完整，不能独立证明来源真实性、授权、业务正确性或恢复目标身份。

## 运行与存储

输入两份 manifest SHA 必须来自各自封存记录，不能用临时重算来掩盖文件变化。源、目标、临时目录必须分离；报告在这三者之外写入新文件，拒绝覆盖。输入自身为符号链接或 Windows reparse point 时拒绝，导出内文件沿用既有逐项检查。运行结束再次验证输入大小、身份、时间和全部 SHA，以发现比较期间的变化。

```powershell
python tools/compare_original_database_exports.py `
  --source-directory D:/PrivateExport/original `
  --source-manifest-sha256 <原封存SHA256> `
  --target-directory D:/PrivateExport/restored `
  --target-manifest-sha256 <恢复后封存SHA256> `
  --scratch-parent D:/PrivateScratch `
  --spool-limit-mib 256 `
  --report D:/PrivateReports/comparison.json
```

以上为路径占位示例，不表示原导出已经存在。临时目录应位于私有、非 Git、非公网静态目录的现有目录下。临时 SQLite 含原数据，禁止发布或上传。默认大小上限 256 MiB，另保留至少 256 MiB 可用空间；使用 SQLite max_page_count 限制文件增长，不生成 journal/WAL 和外部排序副本。启动前核算磁盘可用空间和上限，空间不足在创建临时文件前拒绝。可显式调整上限至最多 4 GiB，超过 1 GiB 同样需满足预检峰值和剩余空间预算。

仅创建和清理自己的随机临时子目录；成功、输入变化或空间不足等异常路径均关闭 SQLite 后清理。运行时原行流采用有界读取，沿用原验证器的压缩、解压、行、字段字节和时间限制，比较总时间默认 20 分钟。进程被外部强制结束或 Windows 崩溃时不能保证 Python finally 执行，残留应按实际进程与文件归属人工核对后处理，不自动删除未知旧目录。

CLI 退出码：0 表示这两份文件的 exportedContentEqual；1 表示比较完成但存在差异，报告保留；2 表示输入、预算、时间或 I/O 验证失败，不写成功报告。既有报告不覆盖。

## 验证与验收边界

自有测试覆盖：行重排与重复保留、重复数量变化、同总数替换与 NULL/空值、私有值不进入报告与源文件不变、DDL/生成表达式/辅助对象/排序规则变化、零行表缺失、上下文模式变化、对象/列顺序、摘要或流损坏、比较中输入变化、临时文件大小上限与空间预算、目录重叠、CLI 三类退出码和拒绝覆盖。

测试使用现有导出验证器的自有 Fixture，不接触原库。原始导出生成列值未捕获、原数据在来源端的完整性/一致性、非事务元数据并发变化、主外键、认证与角色权限、写入/审批/导出、手机端和全部模块操作，均还需要独立真实环境证据。本工具不能单独满足天津项目严格复刻的上线门槛。
