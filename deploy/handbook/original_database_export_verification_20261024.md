# 原数据库逻辑导出文件校验与恢复前置要求

本工具补上只读导出候选与隔离恢复之间的文件完整性检查。它只读指定导出目录，在目录外生成新报告；不连接数据库，不运行文件中的SQL、触发器、事件、过程或函数，也不把页面采集的JSON冒充完整数据库。

## 使用

只使用原导出器成功完成的单次输出目录。先在可信位置固定manifest.json的SHA-256，再运行：

```powershell
python -B tools/verify_original_database_export.py --export-directory <私有导出目录> --manifest-sha256 <固定SHA256> --report <导出目录外的新报告路径>
```

导出目录必须恰有manifest.json、catalog.json、jnpf.rows.jsonl.gz、tj_endanger.rows.jsonl.gz四文件。FAILED.json、缺少成功清单、不认识的文件、重复JSON键、路径越界、文件链接、文件SHA/大小错误、压缩CRC或截断错误均拒绝。固定SHA只防止载荷被悄悄替换，并不单独证明数据来源真实。

按原列顺序读取每个表，生成列依据原GENERATION_EXPRESSION排除。每行必须保持Java写入器的标准UTF-8 JSON行编码、非空值为偶数长度大写十六进制、SQL NULL为JSON null；空十六进制字符串仍是非NULL空值。验证全部BASE TABLE均为InnoDB，表清单与行数清单顺序/范围完全对应；逐表重新计算实际行数和原始行流SHA，空表也必须有清单项和空流SHA。视图不允许混入数据行，重复或逆序表段拒绝。

流式读取限制为总压缩文件和元数据512MiB、单元数据文件32MiB、单行9MiB、单行原值合计4MiB、解压行流16GiB和1200秒；不会将整个行流装入内存或写一份全量解压副本。超过限制明确停止，不能跳过大表后称完整。报告路径不得在原导出目录内或覆盖已有报告。检验期间原文件变化会导致失败。

## 验证证据的范围

23组自有正反例覆盖NULL/空值、Unicode/控制字符、生成列、空表、文件/行流SHA、压缩损坏/截断、目录逃逸、重复键、字段错位、大小写冲突、元数据与表范围、资源限制，以及CLI报告不覆盖。首次反例发现应先整体检查文件名集合、再读取文件；修正后通过。原SHOW CREATE结果须与表/视图名一致；触发器、事件、过程、函数分别要求真实对应的SQL定义字段非空，不能以成功清单掩盖缺失定义。元数据读入有独立字节上限，并检查哈希后、解析前发生的变化。

run_original_export_artifact_fixture.py使用明确提供的既有Java17、固定SHA的自有导出器JAR及既有SnakeYAML，仅调用原导出实现的export方法，Connection/Statement/ResultSet全部由自有内存代理提供。它不调用原导出GUI/main，不读真实配置，不调用DriverManager，不进行实际数据库连接。Java实际生成catalog、两个gzip和manifest，Python校验器再独立读取这些字节；不能只由Python测试夹具复制同一序列化规则来证明跨语言兼容。

```powershell
python -B tools/run_original_export_artifact_fixture.py --java-home <既有JDK17> --exporter-jar <自有候选ReadOnlyExport.jar> --exporter-sha256 <固定SHA> --yaml-jar <既有snakeyaml.jar> --yaml-sha256 <固定SHA> --output <工具目录外的新夹具目录>
python -B -m unittest discover -s tools -p test_original_database_export_verifier.py -v
```

真实原数据库导出仍需独立执行许可；本夹具不消耗或代替该次许可，也不修改既有封包。原包、配置、业务数据、HAR和截图保持私有，仅通用工具、夹具和说明可进入源码候选。

## 隔离恢复仍须证明的事项

文件完整不代表恢复完成。恢复目标必须是独立测试实例，检查MySQL实际版本、字符集/排序规则、lower_case_table_names、UTC与sql_mode；不得覆盖原库或现有业务数据库。必须逐种验证BIGINT/DECIMAL精度、BIT、二进制、Unicode及非UTF8列、JSON、日期/时间与零日期等转换，生成列按原表达式重算后另核对。报告会保留类型统计与大小写冲突，但不凭十六进制格式宣布这些类型已经往返成功。

恢复后要重新导出、比较原ID/原值/行数/关系与业务统计；检验主键唯一性、外键及原历史缺失关联，不能为使关联齐全而补造记录。读取的DDL中可能含DEFINER、触发器、事件和外部调用；本校验器不执行它们，后续需按隔离恢复方案逐项处理。原导出器对表定义有前后检查，但辅助SQL对象的并发稳定性不能由本文件校验器独立证明，报告如实标为未验证。

SQL定义字段依据MySQL官方[SHOW CREATE TRIGGER](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/show-create-trigger.html)、[SHOW CREATE EVENT](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/show-create-event.html)及[SHOW CREATE PROCEDURE/FUNCTION](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/show-create-procedure.html)。官方说明某些仅有例程执行/创建权限的身份会取得NULL定义，因此只见成功查询不足以证明定义可恢复。Java夹具中的SQL正文全部是自有惰性文本，不是实际可执行建库语句。

报告的restoreVerified、fieldTypeRestorationVerified、primaryKeyUniquenessVerified、foreignKeyIntegrityVerified、applicationParityVerified均保持false，直到真实隔离库和原Java业务联调产生对应证据。本轮无原业务字段、索引或状态迁移，不生成替代原库的假模型。
