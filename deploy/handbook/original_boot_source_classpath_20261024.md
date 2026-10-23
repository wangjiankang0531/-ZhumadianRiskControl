# 原 Java 后端共享依赖与源码类路径核验

该工具为严格复刻的原 Java 后端准备可复现的依赖核验步骤。它直接读取既有 Spring Boot 运行包中的依赖，并优先加载原源码重建的类和原资源。运行包可位于已授权的共享目录，不需要复制或解包大型 JAR。

入口为 `tools/probe_original_boot_classpath.py`，自有 Java 检查程序位于 `tools/java/SourceClasspathProbe.java`。Python 需要 3.9 以上，JDK 需要支持 `javac --release 8`，运行原业务类还必须满足该业务实际需要的 Java 版本。

## 执行方法

先用已有源码构建配方生成原业务类，确认原运行包 SHA-256。随后在 PowerShell 中指定既有 JDK、原包及新输出目录，替换示例路径和哈希占位值后执行：

```powershell
python tools/probe_original_boot_classpath.py --java-home D:/ExistingJDK17 --runtime-jar D:/ExistingRuntime/service.jar --runtime-sha256 YOUR_VERIFIED_LOWERCASE_SHA256 --overlay-classes D:/ExistingBuild/classes --overlay-resources D:/OriginalSource/src/main/resources --output D:/PrivateEvidence/new-classpath-check
```

省略两个 overlay 参数时，工具检查原包的 `BOOT-INF/classes` 顶层应用类。输出目录必须尚不存在，不能放在源码类或资源目录内。工具先校验原包 SHA，再编译自有检查器；运行时清除继承的 `LOADER_*`、Java 注入选项和 `CLASSPATH`，使用独立空 loader 配置和显式自有 main，避免误启动原应用。运行包在核验前后还需保持大小和修改时间稳定。

程序逐项核对选中的类和资源字节 SHA。对类调用 `Class.forName(name, false, loader)` 并解析声明的方法、构造器和字段；不创建业务对象、不请求类初始化、不调用原应用 main。错误字节、资源缺失、类型解析失败、结果条目缺失或进程失败都不能计为通过。输出包括 `receipt.json`、结果 TSV、编译及启动日志；这些文件含原类名和资源清单，应保留在私有证据目录，不能上传 Git 或作为公网静态资源。

## 已实测范围与验收边界

2026-10-24，既有专用检查已在共享原运行包上通过 768 个源码重建业务类、97 个原资源及 16 个原平台顶层类。检查没有启动原业务应用或连接数据库，两个大型 JAR 没有复制到本机。原专用检查另通过五项安全夹具验证。通用工具的独立测试使用自有 Java 类验证静态初始化哨兵、错误 SHA、缺失资源、缺失方法类型依赖、既有证据保护，以及输入和继承环境约束；必须记录实际执行结果，不能将跳过的 Java 测试计为通过。

类路径核验不能证明全部依赖行为兼容、业务语义一致或原数据库恢复成功。Reference 源码与原运行包存在版本差异，仍需隔离启动原平台及原业务，使用原测试数据逐模块核对列表、详情、关联、审批、Excel、地图和手机操作。严格复刻第一阶段与公网新版尚未完成。

## 运维与存储

只读引用原运行包和源码资源，禁止在共享原数据库目录上读写启动 MySQL。此工具仅生成自有小型检查类、清单及日志；后续启动应用必须先具备隔离数据库及外部接口配置。无需为核验制作新的全量 ZIP、GIS 副本或原环境镜像。源码、原包、业务数据和凭据不能放进本工具的 Git 提交。

官方类路径说明：[Spring Boot 3.1.6 可执行 JAR 与 PropertiesLauncher](https://docs.spring.io/spring-boot/docs/3.1.6/reference/html/executable-jar.html)。

通用工具已独立通过8项测试，并在原共享业务包865项和原共享平台包16项上全部实测通过；仍未启动原应用或连接数据库。

独立夹具可在指定现有 JDK 后执行：

```powershell
$env:SOURCE_PROBE_TEST_JAVA_HOME = 'D:/ExistingJDK17'
python -m unittest discover -s tools -p test_probe_original_boot_classpath.py -v
```
