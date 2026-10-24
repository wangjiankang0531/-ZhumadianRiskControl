# 原业务配置启动接线与实际Bean绑定验证（2026-10-24）

记录时间：2026-10-24T18:16:44.385439+08:00。本轮把上一阶段的原业务语义配置准备器接入联合控制器的显式选项，并验证原配置类确实能绑定这些值。当前own-j4继续使用已冻结旧代码，没有改运行配置、重启应用或连接原库；下一候选own-j5尚未创建和启动。本阶段是启动接线准备与原Bean绑定验证，不是新后台实际运行或认证业务验收通过。

## 启动顺序与限定内部调用

serve_original_integrated_candidate.py增加--original-business-config与--original-business-config-sha256，两项必须成对且固定SHA。未指定时仍保持原诊断模式。指定时改为先启动平台，再等待自有Popen及数据库/Redis均存活、原main返回、原流程初始化完成和普通列表关键字段签名保留。仅ApplicationReady或端口文件存在不能放行业务。前次终态收据和独占控制器锁继续保留。

平台通过后，控制器检查其匿名登录配置接口，取得该自有平台的真实端口，保留初始诊断配置副本，并按新端口重新生成20键业务语义配置。只为这次业务进程增加该精确平台回环端口；不开放其它端口、源机或任意网络。配置只在启动新业务进程前应用，不改已在运行的业务进程。初始诊断输入和生成结果都保留，可比对SHA；不使用上一次运行的过期端口和凭据。

新OriginalInternalPlatformObservation计划在实际业务上下文Ready时检查14项原SystemParams/FlowConfig Bean绑定、两内部地址的实际Bean值及本机目标、两个实际DataSource的JDBC URL/原GMT+8配置，再由业务JVM发两个匿名GET检查本机平台配置200和未登录CurrentUser600。该观察器的HTTP与JDBC路径尚未实际运行，通过编译不能记成HTTP互调通过；未来也不把匿名GET记成登录或流程业务通过。

## 已实际通过的验证

6项Python门槛检查覆盖显式配置/固定pin、仅精确不同自有端口、Ready不能替代原main、原初始化与存活条件、依赖退出拒绝、失败收据及非法端口拒绝。4项真实CLI拒绝检查含参数缺一、原模式前次未终态、语义模式固定输入有效但前次仍未终态，均在创建own-j5目录前停止；没有新应用或数据库启动。

用真实Spring Binder和原SystemParams/FlowConfig两个普通配置类，对本地未应用配置完成16项绑定核对：14项原业务参数和两个内部URL全部相同。两原类SHA分别2d81f9622423dd349119b3584ce13efedaeab4ec5ee17177917cc14d345fd432、e81328ed9e1908902b9478c1b6eecc77752602ea0e98863097628c3034fa6296；flat原应用、原219依赖和顺序再次完整核验。只构造两个原配置POJO，没有启动SpringApplication、HTTP请求、数据库连接或真实登录。

新增收据发布先写pending、完整关闭后同目录原子移动，拒绝覆盖现有收据。真实Windows/Java夹具验证发布后完整可读、无pending残留、第二次发布被拒绝，避免控制器读到空或半份结果。最终可复现工具CLI完整通过，未用旧源检查代替最终源码检查；首次source编译记录仍保留。

## 复现与状态

原Bean工具：python -B tools/verify_original_business_bindings.py --workspace <既有tianjin_native_20261023> --candidate-properties <本地私有准备配置> --candidate-sha256 <固定SHA> --output <全新目录>。它核验原flat包/依赖和两类SHA，编译自有观察器与夹具，执行实际Binder和原子收据验证，日志private，不输出原业务值或密码。

下一次联合运行沿用tools/serve_original_integrated_candidate.py，除既有workspace/name/previous-receipt/gateway-port/minutes外，传入上阶段已核SHA的Y盘原配置快照及SHA。执行前必须确认当前own-j4已终态、检查各组件退出码和强制结束标记，不以观察超时重复启动。当前old own-j4/controller-source.py SHA bb323c6ad4e3cb6ebe5c536a6ce1f6e6e9b65e1c1e2a2f63e24e03a0ce8c933c保留，新磁盘控制器SHA不同不代表当前进程热更新；原Python进程已经加载的旧代码继续执行，约18:34租约结束，同句柄8344观察。

下一候选真实运行后必须核验businessInternalPlatformObservation.passed、14项业务绑定、两URL、两JDBC时区、内部匿名HTTP及完整进程终态。缺一不算通过。随后继续真实原账号/验证码、CurrentUser、角色/菜单、认证HTTP业务、流程、保存恢复、日期/上传及全模块与原站对照；15项非敏感配置、原快照与实际有效配置的关系、9孤立流程记录和4缺失定义仍待。

6份自有源码/夹具/测试加本handbook共7文件；原类/原配置/Reference/数据/运行包/私有生成物/凭据及held不入Git。正式公网及250/252三维演示保持，250starts1/失败及保护写入0，14held SHA相同。fullCloneReady=false，完整长期目标继续active。
