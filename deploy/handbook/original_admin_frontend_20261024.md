# 原管理前端与真实登录配置接线（2026-10-24）

记录时间：2026-10-24T15:18:01+08:00。本阶段推进原天津门户“访问后台”对应的原交付前端及真实原接口接线，保留完整复刻范围；尚未登录、全部模块操作与公网同版尚未验收。下午已发布的项目演示版不切换，250/252正式场景保留运行。

## 原交付物与原样页面

共享原环境TJZY/home/tool/nginx/www/ap/dist_new.tar.gz为原快速开发平台前端，归档13,095,102字节、SHA f64765343660b98322554a800f05ff8b76da14c92e3729d7f01ff2d9f85a3b08，1589个普通文件展开30,216,262字节，声明3.6.0-1721122038215。原_app.config.js短名jnpf，API/WS/前缀字段为空；首页声明根路径/static、/assets、/fonts和配置文件，资源在归档内齐全。完整SHA清单只存私有工作证据，不上传原前端到Git。

新增tools/readonly_original_static_archive.py把固定SHA归档读入内存提供独立回环静态检查，绝不解压文件，也不复制归档/原资源到D。压缩64MiB、展开128MiB、目录项20000的上限，拒绝遍历、重复、链接/特殊文件、SHA不符；仅127.0.0.1随机非特权端口、全新证据目录、默认15分钟最多20分钟。停止标记和超时只关闭本轮自有服务。该工具是原交付物的只读诊断服务，不是生产后台或可办理业务的替代版本。

第一次独立页面按原字节渲染“登录 - 快速开发平台”，实际重定向/login?redirect=/home，空账号/密码、原配图与登录表单显示。暂未接API时明确503，浏览器真实请求记录仅/api/oauth/getLoginConfig；与此前试探的/api/oauth/Config、/api/oauth/GetConfig不同。这次原前端证据纠正了接口核对目标，不将HTTP200或旧路径600误判成真实配置接口不可用。

## 真实原接口和浏览器对照

own-pboot-r26使用未改的原opm-service-admin-3.6.0.jar、原依赖顺序、既有Java8和自有只读恢复MySQL/Redis。16个自有诊断payload硬链接复用，未复制230MB原JAR、原class或数据库。既有2501原组件/14 Mapper和Java8预检SHA未变，复用已通过证据；原类不注入替代认证或业务Bean。

实际GET /api/oauth/getLoginConfig：HTTP200、原应用码200，104字节，SHA b7ac34f7f2fe2750dbfed40ad7b318b8eea223c85da9379a596b52fdffa99ffe，data含redirect/socialsList/ticketParams/url，redirect=false。未登录GET /api/oauth/CurrentUser?systemCode=mainSystem：HTTP200、原应用码600、data=null，66字节。没有使用凭据、生成/识别验证码、提交登录或伪造token。

第二次独立原前端通过--platform-owner-root指向该自有运行；先核验原JAR身份、ready文件、HTTP监听PID、Java可执行文件路径和完整启动根目录参数。只转发getLoginConfig及CurrentUser两个GET，不转发登录POST或任意业务写入，也不转发认证会话。其它API明确503，非原资源404；没有合成成功业务响应。浏览器真正取得原getLoginConfig响应，200/104字节/SHA与直接接口完全相同，原登录页正常显示且无503提示。账号密码仍为空、未点击登录。

4项有意义的工具检查通过：固定SHA/大小/重复及链接拒绝、HTTP路径遍历拒绝、真实HTTP原静态字节/SPA/404/HEAD/503、两个GET白名单透传及登录POST拒绝。单元夹具只证明传输限制；原104字节响应证据来自实际原JNPF与恢复数据库，不是夹具。

## 生命周期与存储结果

两个独立静态服务正常停止，测试标签关闭，原资源未落盘。新增仅小型源码、SHA/JSON、截图和限额启动日志。本轮原Java有ApplicationReadyEvent及ContextRefreshedEvent，原main仍在后置FlowableLoadUtil.init报缺失流程定义，mainReturned=false；不能把配置接口正常记作工作流或全部平台正常。仍未删除、屏蔽或改写原节点记录。

检查完成后通过自有停止标记请求context.close，已观察到ContextClosedEvent，但JVM仍未在随后20秒限定内退出，控制器结束该自有Java进程，退出1，ownPlatformTimedOut/Terminated事实保留。因此本轮不声称Java优雅退出完成；ContextClosedEvent本身不足以证明所有线程与Bean销毁完成。自有MySQL/Redis分别正常退出0，原源库未连接、不重复导出。后续需要定位停机剩余线程和原后置初始化问题，保持原行为对照。

250本机演示8767在本轮末仍starts=1/alive=true/failed=false、失败0、保护写入0；没有重启或清理其运行目录。25214:48正式场景复查及13:21公网演示发布证据保持，原20秒外围全部清晰仍未验收。

## 使用与剩余交付

从Application运行python tools/readonly_original_static_archive.py，显式提供--archive、--sha256和--output。仅静态模式不需要原JNPF。读取两个匿名接口时额外提供--platform-owner-root，必须是当前确实运行的自有own-pboot-rN目录；工具不负责启动、登录或重启原后台。--minutes只能1至20。结束时在该独立output中创建stop文件，工具正常关闭；不要使用其它进程的停止标记。

原管理前端按根路径编译，/zhumadian/admin/部署仍需根资源与真实路由base适配；不能直接改门户syslink就算接入。真实原登录、全部后台管理/PC/H5保存审批、IEMP与JNPF联合认证、工作流与数据库行为、公网同版均未验收。fullCloneReady=false、publicOriginalCandidateDeployed=false。

本轮Git载荷仅两个自有工具/测试和本说明，共3文件，先本地提交；不包含原Reference、前端归档、原class、数据库、GIS、截图、配置/凭据或14项held。此前bc23a392的6文件推送仍待单独授权，本轮不扩大该范围、不重试外发。完整UE级引擎、驻马店EXE/网页图层和迁移归档目标继续active。
