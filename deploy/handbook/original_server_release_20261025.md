# 原前后端服务器发布准备与诊断修正

本阶段为当前已登录本机测试版的独立服务器发布准备，尚未上传或切换公网。公网仍为旧R2。用户已批准部署，后续必须发布配套后台与恢复测试数据，不能只用原前端替换旧首页后连接旧R2接口。

## IIS代理与本次弹窗

旧R2适配器只有GET/POST、不转发Authorization并限制2MiB响应，不能直接承载本次原系统。新适配器单独位于deploy/iis_original，固定127.0.0.1:18892及既有HTTPS域名，保留原账号认证、转发Authorization与Cookie，支持GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS、单字节范围下载，上传100MiB/响应128MiB边界；不是任意目的地代理。

自有proxy-contract.exe首次在普通.NET进程中无条件访问HttpContext.IsWebSocketRequest，触发PlatformNotSupportedException及Windows 0xe0434352弹窗。保留原失败日志，不将其记为成功或归因天津原后台。修正为只有Upgrade:websocket且路径/方法匹配时才调用IIS专用接口；普通HTTP不调用。非IIS环境的升级请求明确503。测试入口捕获异常并以非零退出码记录，合成失败路径实测退出1，避免未捕获异常弹窗。

修正后13项固定回环HTTP检查通过：3MiB正文完整长度/SHA、PUT/PATCH/DELETE请求体SHA、HEAD空正文、OPTIONS204、上游403、206范围、路径穿越404、错误域名403、不支持方法405、非IISWebSocket503及错误升级路径404；8次实际上游请求携带合成Authorization。未调用原业务后台、未登录、未改业务库。验证命令：python -B tools/verify_original_iis_proxy.py --output <新的独立证据目录>。工具只绑定本机18892，已有监听会失败，不停止或接管别人的端口。

这些是传输夹具结果，尚不是服务器IIS运行证明。实际.NET4.5以上、集成应用程序池、WebSocket支持、HTTPS和公网电脑/H5登录等须在切换前后验证。新模板不改旧部署目录，也没有自动安装IIS组件或修改安全设置。若响应已开始后上游失败，终止连接而不追加错误页污染正文；请求异常时释放自有上游连接。

## 独立服务器生命周期

ServerLifecycleObservation要求显式persistent模式、独立run目录和双字段owner标记，Spring实际ready后写ready，owner变化或自有停止文件触发正常关闭；不使用本机12小时候选的租约来冒充服务器常驻。原CandidateLifecycleObservation及当前j18租约不改。

自有事件夹具在Java8/Boot2和Java17/Boot3各6项通过，包含归属检查、ready/端口、正常停止与上下文关闭。不代表原整套前后端在新服务器已启动、重启恢复已通过。OriginalDeploymentProperties只将两个明确的prepared properties按Java实际规则解码到新的私有JSON，用于部署路径适配；输出含运行凭据，严禁入Git或公开。

## 空间、数据与回滚

当前运行依赖与前端约1.27GiB，计划加已由逻辑导出恢复、正常关闭的本方r26数据种子723048578B，估算未压缩合计2084088098B。先记录D盘实余量，临时峰值预算6GiB，服务器安装前要求至少12GiB；尚未制作归档。禁止复制正在运行的r27数据目录、252原物理库、全量GIS或整个Reference/Y盘。流式从现有文件封装，避免重复全目录镜像。

独立安装验证后再备份旧IIS入口/配置并切换；旧R2端口18874与旧库须保留，回滚用已封存原字节且核当前版本归属。新服务未真实ready、数据库身份不符或IIS传输不符则保持旧入口。当前未进行入口切换、上传、库修改或服务重启。

## 当前验收边界

250用户已经用原账号成功登录并确认新名称“驻马店重大风险防控”。新蓝色盾牌/黄色警示图标已在本机HTTP200/598B及SHA核验，电脑/应急/H5/大屏HTML均引用新图标；实际用户浏览器标签尚未复核。正式8767只读地景读取器保持starts1/alive，保护写0。

全部模块/角色/审批写入、历史附件、H5真机、252、公网同版、20秒外围三维清晰度与完整天津严格复刻仍未验收。fullCloneReady=false。无数据库字段/索引/状态结构变化，不重建数据库模型。完整长期目标保持active。
