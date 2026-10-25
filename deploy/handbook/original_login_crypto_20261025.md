# 原登录加密协议兼容性修正（2026-10-25）

## 问题与最终行为

原 PC 与 H5 登录将密码先 MD5，再用 CryptoJS AES/ECB/PKCS7 加密并发送十六进制字符串。原请求封装发送表单，后续请求通过 Authorization 传递登录返回的令牌。原 PasswordTokenGranter.authenticatePassword 调用 DesUtil.aesOrDecode(password, false, true)，读取 security.SecurityKey 完成解密，然后继续原账号校验。

先前的隔离配置生成器使用通用敏感键名规则，将 security.SecurityKey 替换为本方随机 ownSecret，而原前端保持原有公开协议常量。这会导致前后端不匹配。对当前候选进行离线合成数据验证，原前后端键一致、候选键不一致，解密失败类型为 BadPaddingException。该判断没有通过提交真实登录、读取账号密码、验证码或会话令牌获得。

本次仅将精确属性 security.SecurityKey 视为原浏览器中公开携带的 AES 协议常量并保留；检查 UTF-8 字节长度为 16/24/32。其它 password、secret、token、access-key、securityKey 等属性仍替换，原外部服务地址仍重定向到本方隔离范围。security.EnablePreAuth 保持原配置。账号、验证码、权限、密码校验、令牌生成和过期逻辑没有改动，不伪造登录成功。

本项例外只针对已经核对的原工程版本。原 PC、应急 PC、H5 的加密工具以及已准备的原管理端静态文件均公开包含同一常量；原后端属性与该值一致。该常量不是数据库密码、账户凭据、JWT 签名键或会话令牌。不将原配置文件、常量值、原前端资源、数据库或私有运行件写入 Git。

## 实现与验证

自有 OriginalPlatformConfigBuilder 新增精确属性例外与 AES 长度检查，平台辅助构建锁同步源文件及 builder class 指纹。实际重建 21 个自有辅助 class，产物 130149 字节；只修改 builder class，沿用其余启动与观察逻辑。

新增四项真实 javac/builder 合成回归，覆盖公开协议键保留、其它凭据替换、EnablePreAuth 不变、外部服务隔离、24/32 字节键和非法长度拒绝。使用既有固定 SHA 的 SnakeYAML，不下载依赖、不启动原应用或数据库。既有 23 项平台支持检查继续通过。

自有 OriginalLoginKeyContract 离线诊断工具只输出布尔关系、长度有效性和异常类型，不输出键、凭据、明文、密文。用修正后 builder 与真实原配置结构生成离线候选，前后端键一致、合成数据解密成功，EnablePreAuth 与原值一致；没有执行原认证函数或提交登录。

## 运行与交付边界

本轮自有 j16 正常关闭：六组件自然退出码均 0，两个 Spring ContextClosed、持久文件锁释放。后续自有 j17 使用修正后的平台辅助组件、既有独立业务组件、预适配管理端，以及前一阶段已核验的五个前端/二维地图根。j17 恢复探针仅使用 j16 的真实正常收据与本方归属；不能复用旧实例收据。实际启动、数据保留与入口结果以对应私有 progress/收据为准，不能由本说明代替。

正式 8767 服务保持；本项不构成公网严格复刻发布，不证明真实账号、全部业务模块、附件写入、H5 真机、IIS/TLS 或驻马店三维外围清晰度通过。阶段目标仍需按原站逐模块、原操作和原测试数据验收。

## 运维复现

准备阶段用跟踪的构建器和可信锁生成小型平台辅助产物，再将收据及 SHA 显式传入受控启动器。不要手工更改正在运行实例的配置、回填原数据库密码、复制浏览器会话或关闭认证。若更换原前端版本，应先重新核对公开加密常量与后台协议，不能只旋转后端这一项。

执行合成回归前设置 ORIGINAL_CONFIG_JDK 为既有 JDK17 目录、ORIGINAL_CONFIG_YAML 为已固定 SHA 的 SnakeYAML jar，再执行 python -B -m unittest test_original_login_crypto_config test_original_platform_support。离线诊断工具需与本方 builder 类及 SnakeYAML 一同编译运行，四个路径参数依次为原前端 common.ts、原平台归档、候选 application.properties、候选 own-integration.properties；路径和诊断结果仅保存在私有验收目录。

没有数据库字段、索引、状态或归属变化，无需更新数据库模型。没有创建全量 Reference/Y/GIS/数据库副本。本轮私有证据位于 Document/Deployment/original_login_crypto_20261025。
