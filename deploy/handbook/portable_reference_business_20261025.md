# 参考源码业务运行件的独立载荷与中文路径搬迁

## 目标与边界

当前参考源码候选在启动选择时仍读取Reference、原构建归档和实验收据，不能直接当服务器独立运行包。本阶段实现业务应用及其原配套依赖的私有可搬迁载荷：准备阶段完整验证参考来源；运行件校验阶段只依赖载荷本身和显式可信清单SHA，不再读取Reference、原Boot归档或原实验收据。

这是业务运行组件，不是完整服务器安装包。Java运行环境、原JNPF平台、数据库、Redis、对象存储、启动配置和持久文件管理仍需组合；当前集成控制器尚未选择本载荷，未进行公网发布或完整Spring启动验收。

## 实现

tools/portable_reference_business_runtime.py提供plan、prepare、verify。准备复用reference_business_runtime的固定选择证明，核验863个源码/资源输入、源重编包、原平铺运行件及220依赖。输出必须为既有工作区内全新目录；先计算保守写入量和空间储备，不覆盖或恢复到已有输出。

载荷由application.jar、lib内220个原依赖及portable_runtime.json组成。只调整应用JAR清单，768个class和97个资源逐项保持原字节，所有依赖完整SHA相同。依赖改为相对lib/路径，保留显式包目录与资源目录。[JDK17 JAR规范](https://docs.oracle.com/en/java/javase/17/docs/specs/jar/jar.html#class-path-attribute)定义Class-Path相对包含JAR解析的规则，实际Java验证另行记录。

原配置资源完整保留，故载荷始终标为私有。应用JAR不提供直接Main-Class入口，原入口只以Original-Main-Class记录；应由受控启动器在生成当前环境配置、限定连接和目录后显式加载，不能把此组件当双击运行的安装包。校验清单头白名单同时拒绝大小写变体Main-Class及Launcher-Agent-Class。实际JDK直接java -jar返回1、提示无主入口，未进入应用。

校验要求显式64位SHA，与可信构建侧保存的清单SHA比对，而不是把下载文件自己计算的值当作真实性依据。检查221个载荷文件的精确集合、大小/SHA、865个应用成员、class/资源数、清单类路径和来源摘要；拒绝路径逃逸、Windows设备名、大小写碰撞、额外文件/目录、重解析点和重复JSON键。清单没有本机绝对构建路径。

依赖清单主段不得增加二级Class-Path；只按边界读取主段，保留签名库的大型逐成员摘要尾段，不修改任何依赖字节。另外检查JAR索引，只允许引用载荷声明的依赖文件。实际220依赖中14份索引、14个引用均在集合内；没有二级Class-Path。此为类路径元数据闭包，不表示原业务代码或配置中的所有网络集成都已验证。

## 实际验证

17项合成完整性/路径/CLI检查通过。合成fixture不执行真实Java业务；覆盖内容变化、成员/包目录缺失、额外文件、路径/设备名、重复键、类路径与JAR索引逃逸、大型签名清单、无直接入口及独立Python CLI等。首次真实准备因整个签名清单超过初版128KiB上限失败，尚未生成134MiB载荷；该失败保留，改为主段有界读取后通过。

实际最终r3载荷140516000字节（约134MiB），保守生成预算144656841字节；生成前D盘空间充足。原位置与中文加空格搬迁位置分别执行隔离Python -I校验及真实Java夹具，两个Java自然退出0。每处4项参考DTO契约、9个选定应用/依赖CodeSource、bootstrap资源SHA均通过；每处486条文件类加载来源均位于载荷、测试夹具或JDK范围内。Java编译和运行命令通过JAR清单解析依赖，不展开220项长命令行；实测classpath参数约215字符。

Java只调用合成DTO构造/序列化与类型元数据，应用主类使用不初始化加载；没有调用原服务、启动Spring或连接数据库。不能据这两处少量DTO和类加载观察宣告全768类行为、全部业务、权限、JNPF兼容或独立服务器运行通过。

r3执行后补充严格清单头白名单，实际载荷再次用最终隔离校验通过；生成函数AST与实际r3相同，没有再次生成大副本。随后补充JAR索引闭包检查，直接核验与实际载荷逐SHA相同的全部220个原依赖及应用成员证明，17项规范回归通过；未重复139MB构建。上述检查范围与执行顺序分别留档，不把后增验证器称为原先实际运行过的同一字节版本。

## 空间与数据保留

r2先验证基础搬迁后清理，r3加入受控入口再验证后清理。两次都先检查自有owner、显式清单SHA、222文件精确集合、工作区内绝对路径、两个Java已自然退出，随后使用原生PowerShell仅移除本轮临时载荷。两份约134MiB重复二进制均已移除，原flat与220个依赖SHA保持，UserData、Reference、GIS及原库未动。只保留小型源码/日志/class/清单证明；没有本轮原数据库、GIS或整目录复制。

## 复现与下一步

在准备机的Application/tools运行：

```powershell
python -B portable_reference_business_runtime.py plan --workspace <已有工作区> --selection <已核验selection.json> --selection-sha256 <固定SHA>
python -B portable_reference_business_runtime.py prepare --workspace <已有工作区> --selection <已核验selection.json> --selection-sha256 <固定SHA> --output <全新私有载荷目录>
python -I -B portable_reference_business_runtime.py verify --manifest <载荷/portable_runtime.json> --manifest-sha256 <构建侧可信SHA>
```

prepare需要完整参考构建证明；verify只需本自有标准库脚本与载荷、可信SHA，可单独放到无Reference的目录使用。清单owner每次新建，重新生成后必须采用新清单SHA，不复用已清理测试件的旧pin。测试实例的真实生命周期与公网服务不由本工具管理。

仍需给受控服务器启动器接入此载荷并完成原Spring、平台和持久数据的组合启动/停止，处理服务器依赖、正常登录、全模块、附件、H5真机、IIS/TLS和公网同版。原应用源码与配置不因搬迁测试通过而改写。当前j13及正式8767/公网保持原状；长期引擎和完整驻马店目标active，fullCloneReady=false。

仅自有打包/校验、合成测试、Java夹具和本说明同步Git。原JAR、依赖、配置、可信清单、业务数据、截图和原Reference均不上传Git。
