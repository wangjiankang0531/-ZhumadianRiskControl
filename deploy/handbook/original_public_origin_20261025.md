# HTTPS 前置代理下的原系统网关来源与跳转

## 问题与结果

原本机网关使用HTTP监听地址生成绝对跳转，并把当前HTTP scheme传给原后台。在现有HTTPS网站后接入时，这个默认行为不足以表达公网入口：本次真实Nginx先实测到裸手机路径跳转包含127.0.0.1及本机端口，转发的协议为http，即使请求提供了https头也如此。

prepare_original_frontend_gateway.py新增显式--public-origin，例如https://www.joinlinksmart.com。它只定义既有TLS前端的规范来源，不启用公开监听、不配置证书、不修改IIS或认证。未传此参数时保留原本机模式。

## 实现与使用

来源必须为独立HTTPS DNS origin，可有显式有效端口；域名规范化为小写，默认443省略。拒绝账号密码、路径、查询、片段、控制字符、Nginx元字符、空端口、IP字面量和无效DNS标签。非法值在创建输出目录前拒绝。origin与/zhumadian等应用路径分别配置，原API路径映射不改。

显式模式中，业务API、平台API、管理API、管理静态代理及业务WebSocket统一向后端传配置好的Host、X-Forwarded-Host、https协议及外部端口；不从来访请求决定这些值，并移除来访Forwarded、X-Forwarded-Prefix、X-Forwarded-Server。认证头、Cookie、请求体和原后端状态仍透传，不创建账号或Token。

网关自身的跳转使用absolute_redirect off保持相对Location，使浏览器在既有HTTPS来源内解析，不带回环端口。[Nginx官方相对跳转说明](https://nginx.org/en/docs/http/ngx_http_core_module.html#absolute_redirect)与[proxy_set_header说明](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header)分别明确这项行为及空值移除转发头的规则。没有设置X-Forwarded-Prefix来猜测原应用上下文，也没有新增上游绝对Location/Refresh重写规则。

生成配置的既有CLI增加--public-origin https://www.joinlinksmart.com，仍须提供--output、固定Nginx --runtime、--port、五个既有静态root、--business-port、--platform-port及独立--admin-frontend-port；所有后端和监听仍为回环地址。receipt记录canonicalPublicOrigin和nginxRedirectsRelative，publicProductionReady仍false。

## 验证

初版21项规范检查通过，集成接线后22项通过，包含原部署/原入口/管理端回归、新来源校验和实际CLI的有效/非法参数。默认“无上游”和“完整上游加管理静态”两种模式，旧新配置在只归一化各自输出目录后逐字节一致。

真实固定SHA Nginx按旧本机模式、新显式来源模式各启动一次。2个独立回环HTTP协议夹具分别代表后台传输端和管理静态传输端，返回刻意的418与protocol-only标志，不代表原后台或业务通过。测试验证6类根/裸子路径跳转及查询保留；4条代理路线的路径、POST二进制体、合成认证头/Cookie、状态和Set-Cookie保留；配置的规范HTTPS来源不会被恶意来访Host/Forwarded等覆盖。WebSocket实际101、规范来源和双向ping帧通过。

2个Nginx均经quit自然退出0，2个夹具线程已停止，网关端口关闭，无强制结束。首次夹具错误地把管理静态端口与后台设成相同，被既有校验拒绝，没有启动Nginx；该失败收据保留，修夹具后使用全新目录通过。当前测试增加CLI及集成入口检查后的verify_runtime函数AST与实际成功版本一致，网关源码字节同实际运行，未为纯源码整理重复启动原应用。

原Reference/静态资源/数据库未复制，只有少量自有协议夹具与日志。现有j13配置不重写，其仍为本机模式；集成控制器源码现已增加同名--public-origin，在访问工作目录、锁和进程前验证；记录gatewayCanonicalPublicOrigin并把值传入网关。非法参数实际CLI拒绝。除这4处参数/验证/记录及1处传参外，原控制器AST不变；22项参考运行件检查及5DTO通过。当前j13的冻结控制器仍为新增参数前的版本，不能声称当前j13或公网已经启用这项设置。

## 上线前仍需完成

这不是已完成的服务器安装包。仍须将集成控制器的显式来源纳入独立服务器运行配方，并核对本机与共享目录依赖，验证Java8平台、Java17业务、MySQL、Redis、对象存储及持久文件的部署和正常生命周期。当前参考候选依赖的实验准备路径与120分钟租约不当作生产运行机制。

实际IIS/TLS链路、原应用对Forwarded头的处理、原账号正常登录、角色、全部模块、附件/上传和WebSocket认证尚未由本次协议夹具证明；上游应用生成的绝对Location/Refresh、Cookie路径及外部集成地址需在原应用链路另验，不把协议通过当全部URL生成正确。不更改原Spring认证、白名单或凭据去换取成功。

正式8767与现有公网保留，完整严格复刻及长期引擎、EXE/Web/图层/迁移目标active，fullCloneReady=false。仅本自有网关源码、测试和handbook同步Git；原资源、配置、数据、运行件、截图和持有修改不上传。
