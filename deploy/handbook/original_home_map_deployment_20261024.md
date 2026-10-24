# 原首页菜单与地图部署适配（2026-10-24）

记录时间：2026-10-24T15:03:33+08:00。目标仍为天津原前端、后台、测试数据和PC/H5全部内部操作严格复刻。本阶段修正已发现的环境路径差异并验证原地图组件，不把局部检查当作完整业务通过。现有公网演示版20261024-demo1保持已发布，本原工程候选未发布。

## 问题和实现

原首页CurrentUser(home)从后台加载菜单，原库路径仍为/tianjinrisk。仅设置Vite base不会改变这些菜单值。安全PC可选--adapt-home-navigation将首页handleTo普通分支的路径按边界适配：/tianjinrisk或其子路径映射到目标应用base，查询参数、锚点和相近但不同前缀保留。外部地址及syslink独立管理站不改。菜单对象、菜单表、权限与用户数据不改；本机三维分支单独按--use-local-command指向127.0.0.1:8767，不传原token/用户名，使用noopener,noreferrer。

两套PC原地图组件另有固定/tianjinrisk/map/，编译base也不会改变它。新增显式--map-tile-base，仅替换src/components/Map/index.vue中的该字符串一次，保持window.origin、开发路径、XYZ格式、经纬度、缩放、点选、连线、排序、只读和暴露方法不变。两套组件均映射/zhumadian/map/，应急PC不能错误推导成/zhumadian/emergency/map/。

适配只在独立构建副本中临时执行，构建成功或失败均恢复原字节；拒绝Reference同目录、路径重叠、硬链接别名、逃逸路径、原标记缺失或重复。构建前后按原清单核对；Reference及六套源码副本7566项SHA再次一致。数据库结构/字段/索引/状态未变，不涉及数据库迁移。

## 可复现构建

使用既有固定依赖，不能在Reference原目录编译；输出必须为全新独立目录。安全PC在原构建参数上增加：

```text
--api-prefix /zhumadian/api --public-base /zhumadian/
--use-local-command --adapt-home-navigation --map-tile-base /zhumadian/map/
--mobile-qr-url https://www.joinlinksmart.com/zhumadian/h5/
```

应急PC增加--api-prefix /zhumadian/api --public-base /zhumadian/emergency/ --map-tile-base /zhumadian/map/，不使用首页适配选项。其余必需参数为--kind、--project、--source-project、--source-manifest、--node、--output，详见tools/build_original_frontend.py的参数帮助。H5沿用已验证构建，没有为本次PC改动重复编译。

## 实际验证

- 使用252既有封存导出进行只读流式菜单核对，没有连接源库、重复导出或复制原始行；jnpf全流127,268,733字节，SHA5814f66415248c1df04959c81598dbf190f55333ded982e36d0c05dc4aa8ce80一致。从原首页源码提取实际handleTo，执行其适配版本并以原11个有路径菜单验证：9内部路径、1本机指挥、1原外部管理站，全部符合预期，冻结菜单对象保持不变。这是跳转参数验证，不等于登录后11项业务功能通过。
- 15项自有部署测试通过，包含真实Node执行点击函数、查询/锚点和前缀边界、失败恢复、别名/硬链接拒绝、地图URL单点替换。此轮没有跳过Node案例。
- 两套PC原编译器成功：安全PC835文件17,789,942字节，应急PC204文件7,199,256字节。产物包含/zhumadian/map/{z}/{x}/{y}.png，不再包含旧/tianjinrisk/map/；输入2893/2514项分别恢复一致。
- 新候选经真实固定SHA Nginx完成1606静态文件、151,025,457 HTTP字节比对，SPA/重定向/404/503、两组共享地图挂载及既有协议夹具通过。协议夹具不是原业务后台。
- 将两套原Map组件直接挂载到明确标记的独立验证页，复用既有Vue/Element Plus/OpenLayers，唯一组件改动为地图URL；从Y共享底图实际显示。浏览器9项交互通过：安全PC点选回传和只读拒绝、实际点击A/B/C标记形成连线、上移/下移/删除、连线只读拒绝重新加入已删点、应急PC点选回传及只读拒绝。可见返回的经纬度在天津区域，连线ID顺序与操作一致，红色线及原排序列表实际渲染。截图和可见结果在Document/Deployment/original_home_map_20261024，不入Git。

独立组件夹具首次构建因自有dedupe设置把@vue/shared解析到无依赖的夹具根目录而失败，不是原组件错误。失败日志保留；移除错误去重配置后续接构建，原组件始终恢复、未改依赖或安装新包。首次失败未启动Nginx。最终验证标签已关闭、自有Nginx正常退出0；两个演示8767不动。

## 存储、运行和剩余验收

真实新候选通过后，逐文件核验旧SHA，仅删除本轮被替代的三个dist目录：r1安全PC、r1应急PC、r2仅菜单版安全PC。1874文件、逻辑42,778,969字节，D卷可用空间差值+45,576,192字节（卷差值受同期其它写入影响）。保留旧构建日志/哈希清单/收据、当前r3候选和原H5；不复制或删除GIS、Reference、原环境、恢复库或用户图层。明细见original-home-map-deployment-r3/obsolete_dist_cleanup.json。

本轮末250原生读取器starts=1、alive=true、failed=false，失败和保护写入均0。252正式场景已于14:48复查14企业/16标注，两个演示服务保留运行。原20秒外围全部清晰尚未验收。

原syslink仍为独立内网管理站，不能用其它页面替代。源站登录恢复仍待确认，原JNPF真实登录和后置Flowable缺失定义问题、所有PC/H5模块保存/审批/Excel/地图与业务数据一致性、公网同版均未验收。没有删改原流程记录、伪造token、绕过初始化或认证。fullCloneReady=false、businessParityVerified=false、publicOriginalCandidateDeployed=false。

本阶段Git精确新增修改为tools/build_original_frontend.py、tools/original_frontend_deployment_assets.py、tools/test_original_public_prefix.py及本handbook，共4文件；先本地提交，不擅自扩大此前待确认的6文件推送范围。此前精确镜像bc23a392仍等待其单独授权，没有重试外发。原工程/运行包/数据/截图/私有配置不入Git，14held不变。完整阶段达成后再通知用户正式复核。
