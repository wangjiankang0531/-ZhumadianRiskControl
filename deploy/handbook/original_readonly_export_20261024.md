# 原测试数据库只读导出候选

本工具为天津原项目严格复刻取得可恢复的原结构和数据。它使用现有数据库身份，只查询原 `jnpf` 和 `tj_endanger`，不启动原Spring应用、不访问物理库目录，不构造业务记录。当前为候选，真实数据库连接、完整导出和恢复均未验收。

## 原库操作边界

图形界面点击开始后只发起一次连接。程序先固定当前连接为只读、REPEATABLE READ及UTC，建立一致性快照，并核验服务端实际状态。身份无法证明完整元数据可见性、源表非InnoDB、查询错误、数据行超过上限、结构改变、取消、超时或文件额度不足时均停止。不会自动重试登录或跳过失败表。

程序只执行SELECT、SHOW与当前连接的事务设置；读取的CREATE、触发器、过程、函数、事件、脚本或回调不执行。不会启动/停止原服务、修改全局数据库配置、权限、业务数据或安全设置。一次尝试标记使用CREATE_NEW，即使重复打开界面也不能发起第二次导出。日志仅显示阶段、表名、数量及经过约束的错误码，不显示或保存原连接密码。

默认时限20分钟，主要输出合计512MiB，单行原值合计不超过4MiB，JVM堆上限256MiB。读取大表会增加负载；一致性事务会保留MVCC旧版本，并可能延后并发DDL。真实运行必须在具体执行范围获准后进行，不能把源码检查或夹具通过当作原库运行许可或验收。

## 输出与恢复条件

`catalog.json`保存原库、表、视图、列类型/字符集及辅助SQL对象的定义。两个`.rows.jsonl.gz`按原列顺序流式保存非生成列的数据：NULL为JSON null，非空值为服务器`HEX(CAST(column AS BINARY))`。原类型、字符集、UTC时区和SQL模式均需在恢复时处理；这是项目传输格式，尚未验证为可直接恢复的SQL备份。

`manifest.json`只能在数据文件关闭、SHA计算、事务回滚及连接关闭后创建，含表行数、行流SHA和文件SHA。存在`FAILED.json`、缺失成功清单、压缩CRC或SHA不符的产物不能用于完整恢复。源数据和配置均应保留在私有目录，不能上传Git或公网。恢复还须验证原ID、类型、关系、业务统计及原Java后台，不能直接覆盖原库或现有业务数据库。

## 可复现构建

入口为`tools/build_original_readonly_export.py`，三个自有Java源文件在`tools/java/xnby/export`。构建需要现有Windows JDK17、原平台JAR、其已核验SHA及原配置路径/SHA；配置只用于无连接预检。构建工具仅提取原包内既有MySQL Connector/J 8.0.33和SnakeYAML 2.2，保留依赖JAR，不复制整个原运行包。

示例参数中的路径和占位值需要替换；远端启动参数路径当前要求无空白和引号：

```powershell
python tools/build_original_readonly_export.py --java-home D:/ExistingJDK17 --platform-jar D:/ExistingPlatform/platform.jar --platform-sha256 VERIFIED_PLATFORM_SHA256 --source-config D:/PrivateConfig/endanger --source-config-sha256 VERIFIED_CONFIG_SHA256 --source-host 192.168.1.10 --remote-config F:\OriginalConfig\endanger --remote-export-root F:\OwnExport\exports --output D:/PrivateBuild/new-export-candidate
```

已有同版小型运行时可以通过`--existing-runtime-image`只读复用，避免重复生成中间目录。所有输出必须放新目录、源码工具目录之外；未来清理暂存运行时须先逐SHA确认封包内有完整保留副本。

## 已验证范围

候选代码和封包内运行时各通过同组28项自有夹具，包含：标识符引用、NULL和Unicode、原配置身份/库名约束、私网目标、TLS参数保留、禁用重连/多语句、凭据隐藏、元数据权限可见性、UTC及只读事务顺序、失败状态拒绝、任意YAML对象构造哨兵、重复键、数值字节表示、大小/取消、证据保护、跨窗口一次尝试以及正常序列推进与结构变化区分。代理夹具没有连接真实MySQL。

自有独立候选约49.8MB，原两数据源同一身份和配置SHA的无连接预检通过。图形程序尚未启动、真实数据库连接次数0；数据库恢复、完整电脑/手机操作及严格复刻第一阶段均未完成。

原理参考：[MySQL一致性非锁定读](https://dev.mysql.com/doc/refman/8.0/en/innodb-consistent-read.html)。只读快照需要正确隔离级别，不能仅凭TCP接受连接或JDBC客户端标志认定成功。
