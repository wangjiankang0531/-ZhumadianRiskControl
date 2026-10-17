# 网页 0.7 / API 0.2 认证适配与独立验收

2026年10月14日。用户已明确：统一身份认证暂未提供，先完成接口与独立验收。此版本将网页五张图接到受控只读 API，使用 OAuth2 授权码 + S256 PKCE 公共客户端适配；真实身份、真实业务源和正式公网部署尚未接入。原有 EXE 0.9.2 和本地图层入口继续可用。

## 一键手动体验

在完整本地工作目录双击 D:/Project/Zhumadian/run_api_web_qa.cmd，打开 http://127.0.0.1:8790/。该入口使用独立 services/.venv，不要求用户配置生产账户。点击“登录业务平台”，选择合成验收账号；页面明确说明没有生产身份平台、没有密码采集。

| 选择 | 预期结果 |
| --- | --- |
| 验收 A 企业 | 3 个对象：A企业点、A企业道路线、公共区域；保留在同一授权图层，A 企业台账可读，B 企业不可见 |
| 验收 B 企业 | 1 个 B 企业计量位置，能源一张图数量为 1；只读 B 企业台账 |
| 验收公共点位账号 | 1 个公共区域，不显示所属企业或业务引用、私有台账 |
| 验收 A 企业 · 15秒有效 | 初始 3 个对象，到期自动清空授权图层、列表和选中详情，提示登录到期 |

在 A 企业界面点击点/线/区域名称，再点“定位选中标注”，检查位置和详情。关闭“授权图层 1显隐”时三类标注同时隐藏，已选中的详情立即清空；再次打开可继续选择。滑动整层透明度检查图标、线和填充。点击“切换账号”或“退出”验证旧企业数据即时清空。

B 企业计量位置只是能源空间分类验收，业务引用仍指向 B 企业台账，不代表已有实时计量值或趋势。公共账号只允许基础空间投影。真实监管业务统计尚未接入，页面数量为授权空间对象数量。

验收账号、授权码、签名私钥与合成业务文件仅由本地 QA 进程生成。临时文件在系统临时目录，不发布到 Assets，不改写用户 DLG；QA 服务正常退出时清理。该 QA 授权选择页面没有身份鉴别能力，禁止作为生产登录平台使用。账号选择不是对任何真实用户授予权限。

## 接口与配置

现有 API：GET/HEAD /api/v1/session、spatial_objects、business_records 与业务三元组单条查询。Authorization 只在请求头内传递。服务端可信授权文件决定企业范围，客户端筛选或 JWT 中的 roles/enterprises 不能扩权。生产身份所需的 JWT profile、issuer、audience、tenant、公钥和主体映射见 services/README.md；示例配置默认无公钥、无授权主体。

services/examples/portal.example.json 是可审查的公共客户端配置模板。复制到 Assets/Configuration/portal.json 后，需实际提供 issuer、clientId、authorizationEndpoint、tokenEndpoint、scope。模板地址使用 .invalid，不创建可用生产登录，也不包含 clientSecret。端点固定在可信配置中，不由回调参数或令牌指定。

完整工作目录下先启动 API，然后启动同源网关：

```powershell
cd D:/Project/Zhumadian/Application
services/.venv/Scripts/python.exe -m services.api --config ../Assets/Configuration/api.json --port 8780
# 另一终端：
services/.venv/Scripts/python.exe tools/authenticated_portal_server.py --portal-config ../Assets/Configuration/portal.json --api-port 8780 --port 8781
```

网关只监听 127.0.0.1；网页和 /api/v1 走同源。真实部署需要前置 HTTPS 网关和进程管理，使用正式页面的准确 origin + pathname 注册 redirect_uri。令牌端点需要允许该公共客户端页面来源的 CORS。授权响应需要返回匹配可信 issuer 的 iss；当前适配明确拒绝缺失或不匹配的 iss。真实提供方若使用其它响应约定、不透明令牌或额外认证机制，应另做明确适配和回归，不能通过放宽校验直接宣称兼容。

development=true 仅供浏览器在 loopback 页面使用 HTTP 授权/令牌端点联调，issuer 始终要求 HTTPS。正式配置使用 development=false。公共配置由 /application/config.json 返回，拒绝未定义字段和 clientSecret。

## 浏览器生命周期和数据一致性

PKCE verifier 和 state 的一次性事务存在 sessionStorage，最长 5 分钟，回调消费后删除。访问令牌只存在私有内存字段；不保存 access/refresh/ID token 到浏览器持久存储，不接收 ID Token 作为业务访问令牌。回调先清理地址栏参数再加载资产；授权码只交给固定 token endpoint，访问令牌只发给同源 API，日志不记录这些凭据。刷新页面需要重新登录。当前“退出”清空本应用会话和授权画面，不执行身份提供方 SSO 注销或撤销其令牌。

网页先读 session，分页读取授权空间与台账，再复核 session，整批一次性采用。datasetVersion 表示服务器源文件快照；authorizationVersion 表示实际有效权限，policyVersion 保留操作人员版本标记。跨页/跨数据源版本变化、同版本号下的企业授权变化、重复对象、过大响应、会话失效或错误数据都不能混合采用。读取失败时清空授权数据显示明确错误；源台账未配置保持“未接入”，不伪造空业务记录。到期定时器、15秒权限检查及回到页面后的刷新及时清空旧授权数据；已经注销的迟到请求不能恢复它。

空间 DTO 保留经过校验的颜色、线型、宽度、透明度、图标和文字，私有对象可带合法自定义 PNG；公共对象使用名称标牌并去除私有引用/企业/自定义图标。layer + drawOrder 保留编辑器保存的原分组、显隐和绘制顺序，独立空间分类不重新分组。仅当层内全部对象均授权且包含企业私有对象时保留原层名；混合权限层使用“授权图层 N”，纯公共层使用“公共图层 N”，不泄漏隐藏层名或隐藏对象的排序号。源层标识哈希后输出，只有实际获准对象的层和连续绘制顺序可见。

受控模式隐藏本地 DLG/台账/目录导入，并在网关禁止 /layers、/business、/spatial 原始文件路由。普通本地图层体验仍由 run_web.cmd 提供，只用于本机；不把 8767 的原始文件入口公开。共享地景资产目前按本机公共背景提供，正式 GIS 资产权限、租户资源隔离和云渲染会话管理仍需后续实现。

## 验证与下一步

最终 120 项网页回归和 63 项真实 loopback HTTP/API/网关/PKCE 测试通过，网页正式构建及体验包更新完成。浏览器实测 A/B 企业、公共投影、整层显隐、退出和15秒到期；正式身份未接入，不将合成验收称为真实平台联调。证据在完整工作目录 Document/Deployment/web_auth_20261014。

下一阶段继续 R1 的业务时间/企业维度与来源可追溯指标，用户尚未提供的数据以独立验收模型推进；随后三个轻量闭环。正式源接口、云端信能本源视频和输入、机理模型、数据中台/治理、完整性能/长稳/国产化及 UE 效果效率对标目标持续有效。生产审计防篡改、TLS、安全资源发布、容量与恢复验证不能用本地原型替代。


API0.3门户增加精确重点问题POST白名单：只代理固定集合和feedback/track/review/archive/reopen路径，校验Origin、JSON类型、内容长度及幂等头，后端继续验证JWT/企业/角色。可选publicOrigin必须是运维配置的固定HTTPS源，适配Apache转发；不从请求Host或任意转发头决定可信来源。受控门户禁止绕过API读取数据库原始DLG路径。

模拟验收入口run_focus_qa.cmd，角色为A/B园区跟踪、A企业反馈、A只读及公共点位。模拟记录持久化于work/focus_qa/focus.sqlite，重启不会重置用户体验修改；授权码/密钥仍仅在本次进程内临时生成。OAuth回调支持精确根路径和portal.html，兑换绑定原回调及请求scope。
