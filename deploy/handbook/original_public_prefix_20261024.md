# 原前端公网路径候选与演示版边界（2026-10-24）

记录时间：2026-10-24T14:47:55+08:00。公网现有项目演示版已于13:21发布，presentationRevision=20261024-demo1，250、252实际从公网“敏捷应急指挥”进入各自本机8767并显示14企业/16标注。原天津完整复刻候选尚未发布。本文件记录部署准备，不能作为原认证、全部模块操作或阶段完成证明。

## 本次实现

原安全PC、应急PC、手机H5使用既有固定依赖分别按/zhumadian/、/zhumadian/emergency/、/zhumadian/h5/构建。自有构建配方增加可选部署适配；不重新设计原页面、组件或业务模块。安全PC的mjyjzh分支单独改为打开http://127.0.0.1:8767/?topic=emergency&mode=command，新标签使用noopener,noreferrer，不附加原公网token或用户名。仅独立构建副本在编译期间改动，finally恢复原字节；拒绝与Reference同路径、目录重叠、逃逸路径及硬链接别名。

手机二维码只替换候选输出qrcode.png，目标https://www.joinlinksmart.com/zhumadian/h5/。Reference原二维码及首页源码不改。二维码生成复用已有MIT许可qrcodegen；用原运行包已有ZXing3.5.0独立解码，确认精确目标，不把解码成功算作手机扫码登录通过。

prepare_original_frontend_gateway.py增加受限base-path参数；只改变HTTP路由前缀，不替换磁盘路径。保留原/tianjinrisk默认兼容行为；公网前缀不生成重复/zhumadian/根location。原jnpf/serv/WebSocket代理、缺资源404和未接后台503规则保持明确。未配置后台时不伪造业务成功响应。

## 验证及证据

现有7项部署测试及新增5项部署适配测试共12项通过。三套原前端编译成功：安全PC835文件17,789,767字节，应急PC204文件7,199,258字节，H5 191文件2,815,094字节，合计27,804,119字节。Reference和六套源码副本共7566项输入SHA重新逐项一致，所有临时源码改动均已恢复。

真实固定SHA Nginx完成1606静态文件、151,025,284 HTTP字节与磁盘SHA比对（含复用原大屏376文件）；SPA深路由、带查询参数的挂载重定向、静态404、未接后台503及两组只读共享地图路径通过。独立协议夹具完成URI/查询、表单POST、Authorization、Cookie、二进制206/Range/下载、错误码正文及WebSocket双向帧验证。夹具仅检查传输，不是原业务后端；所有自有Nginx进程已退出。

本地私有证据在Application/work/tianjin_native_20261023的original-public-prefix-frontends-r1、original-public-prefix-gateway-r1、original-public-mobile-qr-verification-r1。本次没有GIS、原环境或整库复制；编译产物约26.5MiB，独立二维码解码依赖602,282字节复用已有包，不下载新运行环境。原恢复库own-mysql-r26/data不是临时缓存，不删除。

## 尚未完成的原行为与部署适配

原首页菜单来自CurrentUser(systemCode=home)，不能只核对静态路由。只读流式核对已封存原jnpf导出，127,268,733字节SHA仍5814f66415248c1df04959c81598dbf190f55333ded982e36d0c05dc4aa8ce80；没有连接原库、重复导出或落盘复制原始行。原业务菜单路径包括/tianjinrisk/workplace、/emergency、/safeProduceSupervise、/intelligentInspection、/majorHazard、/work、/emergency/emergencyResponse、/workflow/flowTodo（以上除首项外均同/tianjinrisk前缀）。现有候选尚未改这些后端返回路径，切换前必须做有原始值对照的环境适配并逐项点击验收。原syslink仍指向独立管理站内网地址，该站交付与授权登录链路需核对；不得用一个不同页面替换冒充通过。原mjyjzh旧18080入口仅在上述可选构建适配中改为本机8767。

原JNPF已能返回真实JPEG验证码，未登录CurrentUser按原码600拒绝，但主流程后置Flowable初始化仍报缺失部署定义。保留原10条节点记录及77条流程定义，不删除或绕过初始化。原站当前停在验证码登录页，已请用户恢复既有登录，尚无确认；没有识别、填写或提交验证码、猜测账号、伪造token。真实原认证、原后台完整就绪、全部PC/H5模块保存/审批/Excel/地图和公网同版均未验收。

## 运维和验收边界

下午演示沿用已发布项目测试版；250/252的8767保持运行，不因原工程诊断重启或清理运行目录。本轮末核对250原生读取器starts=1、alive=true、failed=false，store.failures=0、protectedWrites=0。250和252已实际点击证据及公网备份/回滚步骤见deploy/handbook/demo_entry_20261024.md。原20秒左右角全部清晰要求仍未通过，本轮不声称解决。

Git仅同步5个自有构建/网关/部署适配/测试源码及本handbook，共6文件；不纳入Reference原工程、编译产物、原class、业务数据、GIS、截图、私有配置或14项held。精确同步收据保存在Document/Deployment/original_public_prefix_20261024/source_mirror.json。fullCloneReady=false，publicOriginalCandidateDeployed=false，当前演示版已发布的事实单独保留。完整复刻阶段完成后再通知用户正式复核。
