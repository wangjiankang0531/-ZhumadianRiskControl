# 驻马店 R1 查询 API 0.2

本阶段提供受签名访问令牌和服务端企业范围约束的只读接口。输入是既有 DLG、空间目录与业务台账文件快照；尚未连接真实业务系统或统一身份认证。网页 0.7 已通过受控 API 和 OAuth2 授权码 + S256 PKCE 适配的独立验收。真实统一身份暂未提供，先完成接口与独立验收；入口和配置见 [PORTAL.md](PORTAL.md)。正式 HTTPS 部署、真实接口联调继续属于 R1 待办。

## 本地环境与验收

在 Application 目录执行，使用 Python 3.12：

```powershell
python -m venv services/.venv
services/.venv/Scripts/python.exe -m pip install -r services/requirements.txt
services/.venv/Scripts/python.exe -m pip check
services/.venv/Scripts/python.exe -m unittest discover -s services/tests -v
services/.venv/Scripts/python.exe tools/probe_business_api.py
```

本机独立环境已准备。双击 Application/verify_business_api.cmd 可看六组实际 HTTP 验收结果；--no-pause 用于命令行。全部测试数据以 QA/TEST 标识，密钥只在进程内生成，文件写入系统临时目录并在退出时清理。没有默认生产账户或密码。

## 正式配置前置

从 services/examples 复制示例到 Assets/Configuration，分别命名 api.json、authorization.json、public-jwks.json。issuer、audience、tenantClaim、tenant 和受信任 RSA 公钥须由真实身份提供方确认。示例公钥列表为空，服务启动会明确拒绝；示例 principals 为空，任何用户都没有权限。不要把生产配置、令牌或密钥提交到源码仓库。

api.json 路径相对配置文件目录解析。data.layers 必填；business 和 spatial 为可选的可信服务器文件路径。未配置业务源时业务接口返回 503 BUSINESS_SOURCE_NOT_CONFIGURED，不把缺失源解释为业务记录为零。可配置业务文件 Assets/BusinessData/business_records.json 和空间目录 Assets/Spatial/spatial_catalog.json；当前真实文件均未发布。

配置完成后运行 Application/run_business_api.cmd，或：

```powershell
services/.venv/Scripts/python.exe -m services.api --config ../Assets/Configuration/api.json --port 8780
```

服务只监听 127.0.0.1。它是标准库 HTTP 原型，最多 16 个并发工作线程，单连接超时 10 秒；尚未验证需求中的正式并发、长稳和性能门槛。上线需放在受控 HTTPS 网关后，配置 TLS、访问限制、请求大小/速率限制、监控、进程管理和审计存储。不能直接把本地查看器 8767 的 /layers、/business、/spatial 文件路由公开作为正式业务入口；否则会绕过此 API 的权限。

## 接口

| 方法与路径 | 返回或用途 |
| --- | --- |
| GET/HEAD /api/v1/health | 无需令牌，进程运行状态；不代表外部身份/业务源就绪 |
| GET/HEAD /api/v1/session | 已验证主体及当前服务端权限、企业列表、策略版本 |
| GET/HEAD /api/v1/spatial_objects | 授权后的空间对象及坐标定义、图层指纹 |
| GET/HEAD /api/v1/business_records | 授权后的台账记录及快照时间/有效时长 |
| GET/HEAD /api/v1/business_records/{sourceSystem}/{objectType}/{businessId} | 三元组唯一记录，路径段分别 URL 编码 |

受控接口只接受单个 Authorization: Bearer 头，不接受 URL 中的令牌。POST/PUT/PATCH/DELETE/OPTIONS 返回 405。没有任意服务器文件读取路由。

列表通用参数 search、enterpriseId、offset、limit；空间查询另有 topic、category，业务查询另有 objectType、sourceSystem。专题和类别来自 shared/spatial_types.json，22 类空间对象与 13 类既有业务引用共用一个定义。limit 默认 50，范围 1..200，offset 0..10000；重复、空值、未知参数返回 400。企业条件只缩小已经授权的集合。total 在授权和筛选之后计算，不返回无权企业的总数。

空间 DTO 包含 id/name/type/positions/category/themes/access、经过校验的 style/label、源分组 layer{id,name,order,visible} 与授权对象的 drawOrder。保留原分组而不按分类重新分层；混合权限层和纯公共层使用安全层名，源层标识采用哈希，只有全部子对象授权且包含私有对象时保留原层名。公开基础 label 只使用对象名称，自定义内嵌图标只用于授权私有对象。公开基础对象需同时有服务端 publicSpatialIds 明确发布和主体 publicSpatial 授权；返回 public_basic 投影，不返回所属企业、业务引用、原图层名称、任意来源 label 或内嵌图标。企业对象由经过校验的台账 enterpriseId 确定归属；没有对应记录时可使用服务器 DLG 引用中的企业编号。已有记录缺失企业归属时拒绝继承 DLG 归属；两处非空企业编号冲突时整次数据读取返回 503。

读取企业私有对象需要 spatial:read 和企业范围；业务详情另需 business:read。仅有 spatial:read 时不下发 business 引用。公开基础点位不授予业务详情访问。业务记录缺失企业归属时不可访问。无权与不存在的单条业务记录统一 404。

业务响应标记 source=file_snapshot，state 为 ready/stale/future；不是实时监管数据。数据上限：图层 16 MiB、台账 8 MiB、目录 4 MiB，各最多 10000 对象/记录；DLG 每个对象最多 1000 顶点，兼容原生 point/line/region。目录图层指纹校验沿用网页 v1 精确顺序与 ECMAScript 数字序列化，包含浮点和 Unicode 排序的跨语言回归。

## 身份与权限

JWT 验证固定 RS256、issuer、audience、tenant；只读取配置的本地受信任公钥，不接受令牌自带 jku/x5u。要求 iat/exp 为整数、有效期不超过配置值，过期/未来/错误签名拒绝。默认 rfc9068 配置要求 at+jwt 类型及 client_id、jti；ID Token 不可当作访问令牌。legacy_access 只供已明确的其它 JWT 接口适配，须额外配置 accessTokenClaim 的名称和值；不表示已经兼容任意现有身份平台或不透明令牌。

实际企业范围来自 authorization.json 中的 subject 记录，忽略令牌中的 roles/enterprises。permissions 支持 spatial:read、business:read、focus:read、focus:track、focus:feedback，最终权限为服务端配置与令牌 scope 的交集。enabled、validFrom、validUntil、allEnterprises、publicSpatial 都由服务器管理，默认最小范围。授权和公钥每请求重新读取，文件原子替换即可撤销或更新；身份/策略/数据配置损坏时失败拒绝，不回退到宽权限旧副本。

对外错误只含 requestId 与稳定代码，不暴露路径、令牌或记录内容。401 UNAUTHENTICATED、403 FORBIDDEN、404 NOT_FOUND、400 INVALID_QUERY/INVALID_REQUEST、405 METHOD_NOT_ALLOWED；源未配置或不可用、授权配置不可用、审计失败返回 503。响应 no-store、Vary: Authorization、nosniff。

审计只写请求 ID、UTC、接口类型、状态、错误代码，以及已验证主体/策略版本；不写令牌、查询参数、企业业务属性。审计失败时不下发数据。当前 JSONL 仅是可验证基础，生产的防篡改、留存和统一安全审计平台尚未接入。

固定依赖版本见 requirements.txt；.venv、.deps 和真实配置不入 Git。认证实现依据 [PyJWT 官方 API](https://pyjwt.readthedocs.io/en/latest/api.html)、[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) 和 [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html)。指纹标量使用 [rfc8785 官方实现](https://github.com/trailofbits/rfc8785.py)，保留现有协议对象键顺序，没有改写用户 DLG。

## 网页一致性字段（0.2）

session 返回 expiresAt 与 authorizationVersion；每个受控响应都带 policyVersion 和 authorizationVersion，后者覆盖实际有效主体/租户/权限/企业范围和可发布公共对象。数据响应另带 datasetVersion（全部输入文件规范化内容 hash）。前端需要复核完整分页与读取前后 session 一致，再一次性采用；不得仅依赖人工 policyVersion 判断权限变化。健康版本是 0.2.0。图层最多1000层，其他对象/文件边界沿用前述限制。

本版本 63 项 API/网关/合成 OAuth HTTP 回归通过；网页 120 项回归通过。合成 QA 仅用于独立验收，不包含真实身份或监管业务数据。完整本地目录可双击 run_api_web_qa.cmd；受控网关与正式提供方配置见 PORTAL.md。


## API 0.3：SQLite重点问题与DLG

配置xnby.api.config.v1可增加businessDatabase（相对配置文件目录，受原relative路径规则限制）。data.layerDocument指定数据库文档编号时，DLG通过同租户SQLite读取，layers路径字段保留兼容但不再读取文件；未指定时沿用原文件适配。BusinessData业务快照仍是JSON，不等于所有业务都已入库。

GET /api/v1/focus_issues支持enterpriseId、status、flag、search、offset、limit；GET /ID返回详情，GET /ID/events返回分页历史。POST集合创建；POST /ID/feedback、track、review、archive、reopen执行辅助跟踪操作。身份来自相同JWT及服务端企业策略，每请求复核；focus:read为基础，track允许园区登记/跟踪/复查/归档，feedback只允许企业反馈。所有统计在企业授权之后计算。

写入请求为application/json、最多32768字节，要求32位十六进制Idempotency-Key。更新命令携带整数revision，冲突409；相同幂等键/人员/内容重放原结果，内容不同409。错误和重试不能覆盖新版本。反馈6项为cause、measures、plan、completion、improvement、materialVersion；复查result仅允许rectified、inadequate、continue、special-inspection、emergency。归档要求最新复查已整改；新反馈和重新关注清除旧复查结论。

SQLite事务原子保存问题快照、人员/策略/命令历史、幂等结果。外部审计失败在写入前拒绝；成功后的权威写入历史在同库events，不以外部JSONL补记失败误报提交失败。当前不是防篡改审计。无附件上传、无生产身份，也未完成容量长稳验收。

模型与恢复说明见Document/Database；仓库deploy/database保存目标MySQL DDL和结构指纹。请勿把SQLite数据库、导出文件或真实授权配置提交Git。正式MySQL驱动及目标实例验收尚未实现。

## 公共气体异常接口（隔离候选）

`/api/v1/gas_alerts`已接JWT/策略和同源网关；须显式gas适配器配置及业务库副本才启用，默认未启用。来源和应急回执身份必须分别固定，浏览器GasClient不提供来源/回执/租约工作者路由。所有气体读写还校验当前无企业归属的公共DLG点位，企业材料/说明再按企业范围隔离。

详见Document/Design/气体异常HTTP与浏览器会话合同.md。数据库仍v4；新接口不会自动部署或替换既有站点。现阶段尚无气体操作页面、真实源或实际网络投递器；MySQL/Apache仍待实机验收。


气体独立页面：构建后打开`gas.html`。显式启动合成QA可运行`python tools/serve_gas_portal_qa.py --database <全新独立QA.sqlite> --static <已构建静态目录> --port 8822`；不对正式库运行。QA无真实密码、真实监测或应急网络发送。手测与限制见Document/Deployment/gas_ui_20261019/手动测试指南.md。
