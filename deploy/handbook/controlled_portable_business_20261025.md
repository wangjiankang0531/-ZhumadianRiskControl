# 独立参考业务载荷接入受控组合启动器

天津严格复刻候选此前可以使用参考源码重建的业务 JAR，但启动选择仍依赖准备机的参考归档。现在受控启动器增加显式的独立业务载荷参数，实际新候选已使用该载荷完成原业务应用和原平台的组合启动。独立性仅覆盖业务组件选择；整套服务器仍需要 Java、平台运行件、数据库、Redis、对象存储、前端资源及当前运行配方。

## 实现与复现

serve_original_integrated_candidate.py 新增 --portable-business-runtime 与 --portable-business-runtime-sha256，必须成对传入，SHA 必须是构建侧可信的小写 64 位值。与旧 --reference-business-runtime 两参数互斥，且必须显式使用原业务语义配置；参数错误在工作目录、持久文件锁和服务创建前拒绝。portable_reference_business_runtime.select_for_launch 保留旧默认部署归档和参考源码选择路径，独立路径完成精确载荷验证后，只接受原入口 com.iemp.endanger.Application。

独立模式业务编译和 JVM 参数通过 application.jar 中已核验的相对 Class-Path 解析 220 个依赖，避免把依赖全部展开为 Windows 命令行。平台编译与启动路径保持既有配方。原认证入口、Spring 应用主类、数据库身份检查、共享 Redis 和文件持久目录继续由既有受控启动器管理。

在既有工作区、真实前次正常退出收据及必要运行件已验证的前提下，组合参数示例：

```text
python -B tools/serve_original_integrated_candidate.py --workspace <已有工作区> --name <全新own-j编号> --previous-receipt <真实前次receipt.json> --gateway-port <测试回环端口> --minutes 120 --original-business-config <只读原配置路径> --original-business-config-sha256 <可信配置SHA> --object-store-provider-receipt <已验证提供者收据> --object-store-provider-receipt-sha256 <可信收据SHA> --platform-storage --portable-business-runtime <私有载荷/portable_runtime.json> --portable-business-runtime-sha256 <可信清单SHA>
```

不因旧实例正常退出就复用其编号或恢复参数。只有确实存在本方探针标记、且前次实际正常退出与原文件回读证据匹配时，才使用 --platform-files-recover；无待恢复标记时不传。正常停止通过当前实例的自有 stop 文件提出，由控制器依次关闭组件并记录实际退出码、应用 ContextClosed 和文件锁释放。

## 实际验证

22 项合成完整性、选择互斥和真实错误 CLI 检查通过；旧参考运行件另 22 项检查及 5 项 DTO 检查通过。真实业务载荷约 134 MiB，独立 Python 选择不读取 Reference 或原 Boot 归档。实际控制器配方的业务辅助编译 classpath 为 2 项、265 字符；展开依赖则为 33211 字符，超过 Windows 单命令长度。实际编译 7 个辅助 class，与此前参考配方及本次完整实例逐 SHA 一致。业务运行时显式 classpath 为 5 项，依赖由 JAR 清单解析。

原自有候选 j13 经正常停止文件结束，实际六组件均自然退出 0，两应用 ContextClosed、持久文件锁释放，旧控制器和组件 PID 已消失。之后仅启动一次全新 j14，实际记录业务模式 reference-source-portable、220 依赖、768 class；原平台完成初始化后启动业务，两个应用 ready。共享 Redis 双端读写、原服务数据库读取、业务与平台内部路径绑定、原 Spring 对象存储上传及 HTTP 字节回读、平台原文件 helper 与 HTTP 回读通过。PC/H5/admin 三入口 HTTP 200，真实浏览器均展示原工程登录界面。

这些是启动和限定集成检查，不是认证后的完整模块验收。没有输入账号、密码、验证码，未伪造 JWT；全部角色、菜单、页面、操作流程、历史附件和手机真机尚未逐项通过。既有四组缺失工作流定义等历史数据问题仍保留。独立业务载荷不等于完整服务器交付包，IIS/TLS、真实公网转发行为与完整复刻同版上线仍待验证。fullCloneReady=false。

## 运行与空间保留

j14 的私有载荷在运行中被 JVM 使用，本轮保留这一份约 134 MiB 必要运行组件，不再复制成第二份。以前 r2/r3 的临时载荷已清理，本轮不重新复制 GIS、原数据库或 Y 盘目录。只有当前实例真实停止、归属与文件清单完整核对后，才可清理其运行组件；不能删除仍被服务使用的 JAR。

j14 本次新建的本方持久探针及恢复标记保留给下一次受控重启验证，须使用 j14 的真实正常结束收据作为前置，不能重用已消费的 j11 标记。正式 8767 和公网旧版保持运行，本轮没有将候选发布到公网。七份本地设计、验收、运维与连续性文档随实际结果更新；没有新增数据库字段、索引、状态或数据归属，无数据库模型变更。

Git 仅同步自有选择/控制源码、合成测试及本 handbook。私有清单、原配置与 JAR、参考资源、数据库、业务行、截图、凭据和其他未完成修改不纳入本批提交。
