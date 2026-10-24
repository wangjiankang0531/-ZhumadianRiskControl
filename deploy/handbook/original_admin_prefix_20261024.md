# 原管理前端子路径部署适配与验证（2026-10-24）

记录时间：2026-10-24T15:40:49+08:00。本阶段使原快速开发平台交付前端在/zhumadian/admin/下保持原登录页、资源与路由行为，继续推进完整天津复刻。原归档和原JNPF类未改，本候选未发布到公网；下午项目演示版20261024-demo1及250/252本机场景保留运行。

## 适配边界

原归档固定SHA f64765343660b98322554a800f05ff8b76da14c92e3729d7f01ff2d9f85a3b08，1589文件。新增adapt_original_admin_archive.py及配套.mjs只在内存处理该版本；主脚本SHA35e93f07…1e7d、公开配置SHAd66b5197…e0bf均强校验。使用现有锁版本@babel/parser7.29.9，不安装或下载依赖；转换阶段解析原JS，不执行它。

JS用AST定点改变原路由base、子应用路由base、模块预加载base、getJnpfAppId中两处部署路径读取和公开API基址；静态绝对资源地址只在对应原文件/目录存在时加前缀。HTML/CSS按资源URL改部署前缀。保留业务路由、表单、组件、权限和数据处理源码内容；原appId提取前先去除部署前缀。API_URL设为/zhumadian/admin，原/api/oauth/...拼接为/zhumadian/admin/api/oauth/...，没有重复/api层。

本原包实际改动24个文本文件，另19个对应.gz以mtime=0重新生成，共43个文件；其余1546个原文件字节保持。64处资源URL及7类部署锚点有清单，原固定结构匹配数不符即失败。工具也验证动态模板与文件名前缀场景，但本原包templateAssetURL实际为0，不能把自有夹具当作原页面覆盖。产物保留原文件名；后续部署该命名空间须重新校验/禁用缓存，不能用旧文件名长期immutable缓存。

## 可复现工具

从Application运行python tools/adapt_original_admin_archive.py，必需参数：--archive、--sha256、--base、--node、--parser、--output。base使用/zhumadian/admin，Node与Babel必须指向既有程序/解析器文件；output必须全新且在原输入之外。默认只输出差异SHA和锚点清单，不写原资源。

增加--serve-minutes（1至20）可在独立回环端口查看适配后的原页面，结束时在本次output目录创建stop文件。可选--platform-owner-root只接当前已核验PID/可执行文件/启动根的自有原平台，且仅转发getLoginConfig和CurrentUser两个匿名GET；登录POST及其它API不处理。它是原静态交付物的诊断工具，不能直接当完整业务网关上线。统一网关的admin静态/API挂载、原门户syslink及全部认证业务尚待接入验收。

## 实际验证

1. 21项自有部署检查通过，包含旧PC/手机配方回归、原点线地图URL适配、真实HTTP静态/路径边界/匿名GET限制，以及AST路径和子应用ID的执行夹具；本机没有跳过Node/Babel案例。只执行自有JS夹具，原脚本由浏览器正常运行。
2. 新子路径下1589文件的HTTP字节逐个等于内存产物，共30,217,902字节。最新CLI的43个变更后SHA与该轮产物逐项相同，未变文件来自相同原归档SHA，因此复用已通过的完整HTTP校验，不重复启动后台。
3. 真实浏览器从/zhumadian/admin/进入/zhumadian/admin/login?redirect=/home，深链接完整刷新成功。原配图三次引用均完成加载、宽度非零，脚本/图像均在正确前缀下，账号密码为空。原样页面截图及可见DOM保存在Document/Deployment/original_admin_prefix_20261024。
4. own-pboot-r27原JNPF返回真实getLoginConfig，浏览器两次通过/zhumadian/admin/api/oauth/getLoginConfig取得HTTP200、104字节、SHAb7ac34f7…9ffe，与直接原接口相同。原应用码200；未登录CurrentUser仍600/data=null。没有登录、填验证码或伪造会话。
5. 第一轮另有1次未记录路径的404，不能直接判定是业务资源缺失。对同字节产物增加路径记录后复现的唯一404为根/favicon.ico，页面声明的原图标/脚本均已使用管理前缀。独立诊断origin补齐根图标到应用图标的重定向；后续静态复查missingPaths为空。该复查有意不接后台，唯一503为getLoginConfig，不把它当真实业务响应成功。公网全站根图标由后续站点配置管理，本轮未改公网根路由。

## 原后台与存储状态

own-pboot-r27仍在原后置Flowable初始化报缺失部署定义，main未返回。该轮到180秒上限后控制器结束自有Java，退出1，ContextClosedEvent未观察到；不是优雅退出通过。自有MySQL/Redis均正常退出0。此前r26的关闭事件与20秒未退出事实单独保留，不能混用。原流程记录、源库和原包未改，不重复导出；原MySQL恢复副本继续保留。

三个子路径测试服务及浏览器临时标签均已关闭，原资源没有解压/复制到D，也未落盘改写后的43个资源。新增仅自有配方/测试、JSON清单、截图和限额启动日志。250末次8767 starts=1/alive=true/failed=false，失败/保护写入0；252正式场景的既有双机验证保持。原20秒外围全部清晰仍未验收。

## 源码与剩余验收

本阶段精确4个自有工具/测试及本handbook，共5文件；原归档、原JS/class、数据库、GIS、截图、配置和凭据不入Git，14held不变。先本地提交并独立镜像检查，不扩大此前bc23a392待授权6文件范围。

仍需完成统一网关和原门户入口、原管理平台真实登录、IEMP/JNPF联合认证、所有PC/H5与子应用内部保存/审批/Excel/地图/其它外部集成、公网同版。当前验证仅覆盖未登录页面、部署路径和两个匿名接口，authenticatedOperationsVerified=false、fullCloneReady=false。完整UE级引擎、驻马店EXE/网页图层及迁移归档目标保持active，阶段完全达成后再通知正式复核。
