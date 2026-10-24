# 原平台启动辅助组件的源码重建配方

独立业务组件接线后，原平台的启动与配置辅助类仍从既有实验目录复用编译产物。本阶段把实际运行所需的一组自有辅助源码纳入项目，新增固定输入校验与可复现构建配方，解除这部分构建对旧实验收据及旧编译目录的依赖。它不是完整服务器安装包，当前集成控制器仍使用此前编译的、字节相同的辅助类。

## 源码和输入

新增 10 个自有 Java 源文件：5 个 Java 8 兼容的归档/资源连接辅助源码、4 个原平台启动与元数据观察源码，以及 Java 17 的配置构建器。另复用项目已跟踪的 SourceClasspathProbe、OriginalIdGeneratorShutdown、PlatformWritableObservation、OriginalBootstrapOrphanGuard 4 个源码。所有来源均为本项目先前编写并运行的辅助代码，不包含原 Reference/JNPF 业务源码。

original_platform_support.lock.json 固定 14 份自有源码 SHA、JDK17 编译器指纹、Boot loader/进程边界/SnakeYAML 指纹、8 个编译依赖库和预期 21 个自有 class 的 SHA。构建器只读取明确指定的这些小型既有输入，不读取原平台大 JAR、Reference、数据库或实验收据。私有 inputs JSON 仅列出已安装 JDK 与依赖路径，不能加入 Git。

## 构建与验证

```text
python -B tools/build_original_platform_support.py --inputs <私有依赖路径JSON> --output <全新输出目录>
python -B -m unittest discover -s tools -p test_original_platform_support.py
```

私有输入对象字段必须恰为 schema、javaHome、bootLoader、guard、yaml、libraries；schema 为 xnby.original-platform-support.inputs.v1。libraries 以锁定的 8 个库文件名为键，值为现有文件路径。缺少/额外字段、重复 JSON 键、文件或编译器 SHA 不符、非普通文件、源文件缺失/变化、已存在或重定向输出目录均拒绝。创建输出和执行 javac 前完成校验，禁止注解处理器；构建后再次检查源码、依赖和编译器。失败收据保持 passed=false。

实际构建使用固定 JDK17 javac，包装类与观察类使用 --release 8，配置构建器使用 --release 17。结果为 8 个包装 class、12 个观察/生命周期/启动守卫 class、1 个配置构建 class，共 21 个，全部逐 SHA 等于既有基线，也逐项等于当前实际运行的 j14 对应 class。观察 JAR 的 12 个 class 和 spring.factories 共 13 个成员与实际运行版本字节相同；ZIP 时间和顺序规范化，因此不要求整个 JAR ZIP 字节与旧时间戳版本相同。

实际初次构建输出约 127 KiB，没有复制原平台大 JAR、8 个依赖、JDK、原数据库或共享目录。10 项边界/失败回归验证变更源码、依赖与编译器拒绝、输入角色、重复键、非普通文件、既有输出保留和编译失败记录。合成失败测试不启动真实应用；真实编译结果另行保存，不能把合成测试当作原业务通过。

## 行为边界与后续部署

归档辅助源码保持原 Boot 类定义/委派和依赖顺序，只沿用既有资源连接生命周期管理；被动观察器不替换原认证。源码同时保留当前候选已存在的测试隔离行为，例如原调度器不在候选运行、已有孤立工作流记录仅在启动初始化阶段隔离、普通业务调用和数据保留。它们不能被误认为生产功能已完成，也不能据 class 相同推导出整个天津项目已验收。

当前 j14 没有重启，仍使用之前编译的同字节组件；本阶段完成可复现构建，不宣称新配方已被集成启动器选择。仍需把这些产物接入完整服务器配方，补齐平台归档、JRE、MySQL、Redis、对象存储、前端、配置和持久化管理，以及原账号登录后的全模块/附件/手机真机/IIS-TLS/公网同版验证。fullCloneReady=false。

正式 8767 与公网保持原状。无新增数据库字段、索引、状态或归属；原业务数据、Reference、GIS、用户图层与持久目录不变。Git 仅同步本阶段自有源码、固定哈希配方、边界测试和本说明，不同步私有输入路径文件、原 JAR/SDK、数据库、配置密码或运行包。
