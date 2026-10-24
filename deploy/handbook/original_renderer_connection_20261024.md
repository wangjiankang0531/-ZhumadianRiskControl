# 原大屏渲染与交互接线阶段记录

## 问题与实现

原大屏不是静态页面：它依赖原云渲染 SDK、WebRTC 视频、业务后台、第三后台及两类 WebSocket。原参考配置缺少 interactWsAddress，导致原页面的交互连接没有有效端点；原环境实际运行配置有该字段。本次保持原 UI 源码、云渲染分支及业务方法，只在自有配置生成器明确补入同源交互地址，并以可选参数接通原云渲染。

prepare_original_bigscreen_gateway.py 验证有 SHA 固定的既有匿名 SDK 探测收据，只接受显式、规范的私有 IPv4 和非特权端口。启用时仅代理精确 SDK 路径及 /player，剥离 Cookie、Authorization、Referer；网关仅绑定本机回环。默认渲染仍明确不可用，不根据配置完成就宣告视频成功。

prepare_original_bigscreen_config.mjs 对固定原 config 和解析器做 SHA 校验，以 AST 范围替换已有端点，补入唯一缺失的交互字段。其它原配置属性原字节保持，未切换桌面 SDK。serve_original_bigscreen_candidate.py 接受成对的 --renderer-probe 和 --renderer-probe-sha256，启动前校验，网关就绪后验证实际 SDK HTTP 字节 SHA；浏览器视频与业务操作另行验收。

## 实际验证

34 项工具检查通过，包括错误端点和凭据拒绝、探测收据归属与 SHA、默认分支只补缺失交互端点、启用分支只另改 SDK 入口、两个实际 nginx -t，以及旧失败/成功收据关闭分类。测试工具依赖本地已有的私有参考夹具，不下载或启动原应用、原渲染服务。复现命令如下，输出目录必须不存在：

```powershell
python -B tools/test_original_renderer_gateway.py --workspace work/tianjin_native_20261023 --output work/tianjin_native_20261023/own-renderer-check-new
```

独立 SDK r3 的一次 WebSocket 握手实际完成 API_READY、VIDEO_LOADED，显示 800×450 视频；手动释放后原 SDK destroy/WS close、网关自然退出均观察到。此前 r1 自有换行误判、r2 上游断开/自动重连/4010 保留，不能归结唯一原因或称全部首次通过。

完整原页面 j4 实际在总览、应急、指挥、动画四路由显示 1920×856 视频。原年度巡检 32/1/1，物资弹窗实际 162 行。动画方案播放、暂停、继续、停止及实际三维变化均已观察。原应急统计有 API、静态 JSON、模板常量混合来源，保持原逻辑，不把全部数值宣称为实时数据。

完整原页面 j5 使用修正后的交互字段，原交互 WS 实际连接；向自有第三后台发送一次“预案匹配”，HTTP 成功后，原页面收到一次指令并显示原匹配界面。另一条接收日志为连接成功提示；重复指令未被证实，不据此修改原前端。j4/j5 均实际正常退出，原 Java ContextClosed、网关和后台 exit0、Mock 停止、原参考库和归档 SHA 不变。

## 限制与后续验收

现场核查仍有两轮均出现的压缩脚本不明错误“i”，尚未定位。测试摄像头后台只连本机不可用假端点，视频查询失败不能记为真实摄像头通过；未访问或控制真实设备。PDF/历史附件预览、原账号与角色全部流程、H5 真机、公共部署同版尚未验收。两轮只证明明确列出的原界面、数据与交互，不代表完整复刻完成。

原渲染依赖可达的原服务；本阶段使用顺序会话，未证明并发容量。测试释放后恢复原机原页面；未改原 SDK、渲染配置、授权限制、安全设置或复制 GIS/ISO/整库。截图、原 SDK、业务数据和私有配置只留本地证据，不入 Git。已有持久对象存储及管理附件目录、身份、密钥、重启探针不得作为缓存删除。

本阶段没有发布公网。原正式本机三维服务继续运行，原公网版本保持。完整天津复刻及长期引擎、编辑器、网页、迁移目标保持 active，fullCloneReady=false。详细证据位于 Document/Deployment/original_renderer_connection_20261024。
