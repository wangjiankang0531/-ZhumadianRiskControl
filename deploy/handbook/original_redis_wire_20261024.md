# 原平台与业务后台 Redis 会话序列化实测（2026-10-24）

记录时间：2026-10-24T16:15:48+08:00。本阶段以双方真实原组件检查会话字节兼容性，使用合成用户和内存Redis传输，不启动Spring、Redis、MySQL或原应用，不登录或创建JWT。结果只证明本轮所测会话编码链路兼容，不代表真实登录、权限、业务操作或完整复刻已通过。现有公网演示版及250/252本机三维保持运行。

## 原行为与实现

既有业务后台真实启动的bean清单已确认 redisTemplate 来自 com.cqweh.cloud.redis.RedisAutoConfiguration。原平台 jnpf.config.RedisConfig 使用 StringRedisSerializer 处理键、Jackson2JsonRedisSerializer(Object.class) 处理值；业务侧原配置使用字符串键与 GenericJackson2JsonRedisSerializer 值。

关键是保留原 RedisUtil.insert 路径：它先把 jnpf.model.LoginUser 转为JSON字符串，再交给平台模板编码。不能直接把业务对象放入模板并假定二者兼容。上一阶段已核对原 CurrentUser 使用该工具写入 cqweh:opm:userInfo: 加userId；业务侧原 SessionManager.getUser 读取该键，原 Jsons.readObject 再还原为业务 LoginUser。本阶段实际执行原工具、原模板、原读取和原JSON解析方法，未执行需登录的CurrentUser控制器。

自有 OriginalRedisWireProbe.java 只通过JDK动态代理提供内存连接工厂和Redis SET/GET/有效期命令。原模板及原用户模型不修改。平台侧在原Java8及原嵌套依赖顺序下产生字节文件；业务侧在原Java17及已核验的既有flat运行依赖下读取同一批字节。内存传输不模拟登录成功或业务接口，只替代网络连接，以便单独验证原序列化链路。

OriginalRedisWireLaunch.java 在加载原组件前安装已验证的自有进程约束，写入仅限本轮输出目录，允许的网络端口为空且禁止监听。该约束是自有测试进程约束，不是对恶意代码的操作系统沙箱。本轮两个进程均记录约束仍在，拒绝计数为空；没有真实网络请求、数据库或缓存连接。

## 真实验证结果

6组合成输入覆盖普通字段、中文与补充字符、引号/反斜线/换行、空字符串、空值、8192字长文本。每组比较 userId、deptId、name、userName、mobile、avatarPath 六字段，共36字段比较一致。平台6次写入、6次有效期命令，业务6次成功读取；另请求1个不存在的合成缓存键，原SessionManager按原逻辑抛出NullPointerException，未用假用户补齐。

本轮未加载应用配置的原工具默认有效期为28,800,000毫秒（8小时），已记录实际命令值；真实联合运行的登录/会话有效期与续期行为仍须核对，不由离线默认值证明。

合成wire文件为34,430字节，不含任何原用户、业务数据、原口令或令牌。两个JVM均在60秒限时内正常退出0，未终止或重启原服务。7个实际加载的原类SHA与既有归档/依赖核对一致，平台源归档前后SHA保持294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8；原业务归档SHA为4c5bcf1bb3f76a3865c0cd6969cfef845934a11343d2987413f33715411dc902。

先导r1自有内存夹具漏掉原工具的有效期命令而失败退出1，证据保留；只修正自有夹具后r2通过。r2用Windows文件路径指定Logback配置时存在资源查找警告，序列化仍通过；整理后的正式CLI改用文件URI，日志正常，完整独立运行再次通过。不得把首轮失败记录删除或把修正夹具写成修改了原后台。

最终可复现证据位于Application/work/tianjin_native_20261023/own-original-redis-wire-cli-r1/receipt.json、双方results.tsv、boundary.txt及小型日志。原静态类检查在own-redis-wire-audit-r1，共11个所选类33,860字节；原类/反汇编只保存在私有工作目录，不入Git。没有复制原运行归档、GIS、物理库或整套252环境。

## 可复现命令与维护

tools/verify_original_redis_wire.py 接受 --output（全新且不重叠输入目录）、--platform-metadata（既有已验证平台preparation.json）、--business-flat（既有原业务flat目录）和可重复的 --audit-receipt（原所选类SHA证据）。两个自有Java文件位于tools/java。工具依赖已入库的reference_flat_runtime.py，不安装新依赖、不复制运行时。

验证流程为：核对原归档、运行时、加载器和依赖SHA；以Java8字节码编译自有夹具；限时执行原平台写入与原业务读取；比较36字段、缺失项拒绝和7原类来源；核验进程终态和约束记录；最后再次核对原归档。生成的receipt明确 originalSerializationCompatibilityVerified=true，但 authenticatedBusinessVerified=false、fullCloneReady=false。

本次仅生成合成wire、编译类和小型日志，原源码、配置、业务库及用户DLG不改。结束后两个JVM均退出，回退只需不用本夹具，无运行服务需恢复。250正式8767复查仍原生starts=1/alive=true/failed=false、失败和保护写入0；公网与252演示不操作、不切换。20秒外围全部清晰仍未验收通过。

## 交付边界与下一步

此结果解除会话字节兼容性的一项未知；上一阶段的双命名空间共享Redis覆盖配置仍为运行准备。下一步用一个自有MySQL/Redis控制器运行两个原后台，按原Login→CurrentUser→鉴权业务接口验收；还要处理原后置Flowable定义缺失与停机、原源站登录对版、所有PC/H5页面和操作、公网同版。不能绕过认证、改原权限或删除流程记录来换取通过。

本轮精确3个自有源码文件（2Java夹具、1验证工具）和本handbook，共4文件，仅本地保存。原Reference、业务数据、数据库、GIS、原类、运行包、口令、截图、合成运行产物及14项held不入Git；不扩大待确认14文件镜像7c21b8c2。完整长期目标保持active，完整复刻验收达成后再通知正式复核。
