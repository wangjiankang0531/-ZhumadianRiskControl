# 天津原后台联合认证与共享 Redis 准备（2026-10-24）

记录时间：2026-10-24T16:03:36+08:00。本阶段只读核对原类和源码，准备两个原后台共同使用一个自有 Redis 的覆盖配置。没有启动后台、登录、连接数据库、运行原类或变更公网。现有250/252演示服务保持运行。本阶段仅配置准备通过，真实联合认证仍未验收。

## 原有链路与证据

原安全PC的 src/utils/request.ts 直接将存储的令牌放入 Authorization，登录接口位于 /jnpf/oauth/Login；src/api/layout/index.ts 的 getUserInfo 默认 systemCode=safety，调用 /jnpf/oauth/CurrentUser。原JNPF的 JnpfTokenConfig 声明 Authorization 与 bearer 前缀。保留原前端、平台和网关的令牌行为，不另造令牌、用户或认证结果。

原 jnpf.controller.LoginController.currentUser 在取得用户及菜单后，构造原 LoginUser，并通过 RedisUtil.insert 写入 cqweh:opm:userInfo: 加 userId。原 IEMP SecurityContextHolder.getLoginUser 使用相同前缀读取；SessionManager.getUser 通过 RedisTemplate 取值且要求非空。因而原始登录、CurrentUser 成功和后续业务请求是同一联合验收链路；仅测匿名接口或仅测登录，均不能证明这条链路完成。

原业务拦截器读取 X-TOKEN 或 Authorization，并处理 Bearer/bearer。它的解析代码不是本次认证通过的证据；不利用其解析行为构造或伪造会话。原权限、令牌签名、登录加密和用户数据均不修改。

静态类证据：原平台归档SHA 294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8；安全依赖SHA 8911be24afea2a38862213aadef38070a7a1a13c7fe5e4c27bd389a97a6199ab。LoginController类SHA c96992057823ac3cfba728698126ae2b5bfe9fcc249897b329772ab1caddee47；业务SecurityContextHolder类SHA 4db35f34383d4b81e86800b2a8109741b41bad57cdb4433f240c5f7546cb9a43。小型私有类与反汇编证据在work/tianjin_native_20261023/own-auth-audit-r1及own-joint-auth-audit-r2，不入Git。

新增8个所选类共38,738字节；未复制原归档、原环境或GIS。首轮过滤只包含common-auth/common-redis，漏掉common-core中的CacheKeyUtil，静态检查停止；保留own-joint-auth-audit-r1/failure.json，修正依赖范围后第二轮完成。没有原类初始化或服务重试。

## 配置实现

此前 own-dbboot-r5 与 own-pboot-r27 是独立后台检查，各自使用自己的Redis；实读59项业务配置和214项平台配置，双方均回环、数据库编号均0，但完整Redis端点不同。这不是原项目配置缺陷；它表明此前两次独立诊断不能直接组成同一联合运行。下一次联合运行需由单一控制器管理一个MySQL、一个Redis及两个原应用，不能用两个独立控制器并发打开同一个MySQL数据目录。

tools/prepare_original_shared_redis.py 读取两个既有隔离构建器生成的显式配置及本轮私有连接元数据，生成 business-redis.properties 和 platform-redis.properties。业务侧使用 spring.data.redis，平台侧使用 spring.redis；四项host/port/database/password均指向同一个自有实例。只生成覆盖配置，不复制完整原配置，不更改认证、权限、工作流、数据库或原文件。

工具仅接受应用绑定127.0.0.1且端口0的隔离候选；拒绝远端端点、重复键、替代Redis命名空间及URL/cluster/sentinel覆盖，拒绝不明确JSON、重复JSON字段、非UUID4所有者、非特权端口和不合格式的自有随机口令。生成目录必须全新；已有文件不能覆盖。外部配置、Java Properties扩展语法或环境展开不受支持，遇到则停止。

输入连接JSON包含 schema=zhumadian.original.joint-redis.v1、ownerId、host、port、database、password。只能供本次自有运行使用；元数据和两个生成的properties均含口令，不入Git。源代码、示例文档和公开收据不含口令。CLI错误只输出固定诊断，不回显私有JSON或配置行。

运行方式：python tools/prepare_original_shared_redis.py --business <既有业务隔离application.properties> --platform <既有平台隔离application.properties> --connection <本次自有Redis连接JSON> --output <全新输出目录>。后续控制器应把匹配的覆盖配置作为各自配置位置列表的最后一项，并核对生效值；不得仅凭已生成文件假定Spring实际加载成功。

## 已完成验证与未完成项

7项自有测试通过：正确映射两个命名空间并保留原文件、既有端点等同性、错误/歧义/外部配置拒绝、私有元数据约束、输出保护、重复JSON字段拒绝、CLI错误不泄露口令。另在真实既有隔离配置上运行CLI，两个生成文件的四项逐字核对一致，输入SHA不变。证据位于work/tianjin_native_20261023/own-joint-redis-preparation-r1。

本次准备没有Redis监听器，所选端口只是准备值；未来启动须重新分配并核验端口归属，不能直接把本轮文件当作运行服务。receipt明确 runtimeStarted=false、runtimeReady=false、originalSerializationCompatibilityVerified=false、authenticatedBusinessVerified=false、fullCloneReady=false。

下一步仍需核对双方原序列化方式，并在同一自有Redis/MySQL控制器下以真实原登录流程验证 Login→CurrentUser→鉴权业务接口，再逐页比对PC/H5操作。源天津登录恢复仍待用户处理，不重置源账号、不读口令管理器、不解验证码。原JNPF后置Flowable缺失定义及停机问题保留未解决状态，不能以配置准备通过代替完整业务验收。

## 运维、数据及源码边界

本轮无服务启动或修改，回退仅弃用本次覆盖文件；原候选配置、源库和用户数据均未改。现有公网演示20261024-demo1与250/252自身8767保持运行；250复查原生starts=1/alive=true/failed=false、store.failures=0、protectedWrites=0。20秒外围清晰度仍未验收通过。

本轮仅两个自有源码/测试与本handbook共3文件作本地源码提交；生成私有连接、覆盖文件、原类、反汇编、数据库、GIS、Reference、运行包及14项held均不入Git。不扩大待确认14文件镜像7c21b8c2范围。完整长期目标保持active；天津完整复刻达成后再通知正式复核。
