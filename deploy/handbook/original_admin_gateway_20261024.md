# 原管理平台统一网关接线（2026-10-24）

记录时间：2026-10-24T15:49:13+08:00。本阶段补齐原管理平台静态服务与JNPF API在统一网关中的路径分流；仅独立回环配置及协议验证，原登录、联合认证及全部业务仍待验收。现有公网演示版和250/252正式三维不切换。

## 设计与实现

prepare_original_frontend_gateway.py新增可选--admin-frontend-port；默认不配置时旧安全PC、应急PC、H5和大屏行为保持。该端口必须是显式非特权回环端口，且不同于网关、业务和平台端口，防止自代理循环或把静态服务与后台端口混用。该低层配置工具不启动或验证服务身份，运行控制器必须核验实际自有服务的PID、版本和路径。

base-path为/zhumadian时，/zhumadian/admin重定向到带斜杠路径并保留查询；/zhumadian/admin/代理到同前缀的独立原管理静态服务。更长的/zhumadian/admin/api/直接映射到原JNPF的/api/，不经过静态服务的SPA回退或其只读检查限制。API请求方法、请求体、认证头、Cookie及WebSocket相关代理头沿统一规则传递。裸/admin/api明确404；平台未配置时admin API明确503。

现有/zhumadian/api/jnpf/到同一原平台/api/的路径保留。新增接线不合成业务结果，不改数据库字段、索引、状态或原配置/数据。HTTPS/IIS前置转发、真实认证和生产端口归属不由本次回环协议检查证明。

## 可复现验证

先在Application/tools运行python -m unittest test_original_frontend_deployment test_original_public_prefix test_readonly_original_static_archive test_adapt_original_admin_static test_original_admin_gateway -v。本机22项通过。

真实Nginx检查使用tools/test_original_admin_gateway.py的verify-runtime子命令，显式提供--runtime、--runtime-sha256、--roots-receipt和全新--output。roots-receipt来自已有原前端网关准备记录，引用现存静态目录；不复制资源。Nginx本轮固定SHA c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44。

测试只启动本轮两个回环协议夹具和两个短时Nginx。静态夹具标记admin-static-protocol-fixture；后台夹具标记backend-protocol-fixture并返回418，刻意不作为业务成功接口。检查实际HTTP：裸入口301与查询保留、静态完整子路径、admin API更长路径优先、GET/POST/请求体保留、合成认证头和Cookie保留、后端418正文与状态保留、裸API404、既有平台代理无退化、未接平台503且不回退HTML。

从已合入应用源码的CLI实际执行通过，两个Nginx正常退出0，协议夹具线程正常停止。配置检查和退出日志保留在Application/work/tianjin_native_20261023/original-admin-gateway-cli-r1。该证据仅证明网关传输；原前端此前取得真实getLoginConfig200的证据仍单独保留，不能把本轮夹具当成真实业务后台或实际登录通过。

## 运行及交付边界

本轮没有原JNPF/MySQL/Redis重启，没有源码归档、原环境、GIS或业务库复制。新增仅少量自有源码、配置和日志；250正式8767仍starts=1/alive=true/failed=false、失败及保护写入0。25215:43正式近景14企业/16标注及公网刷新会话已另行核对。演示服务保持运行，原20秒外围清晰度仍未验收。

尚需把实际管理静态服务、原平台和业务服务组合运行，再连接原门户syslink，完成真实登录、IEMP/JNPF联合认证、全部PC/H5/子应用操作和HTTPS公网同版。原后置Flowable缺失定义及停机问题仍未解决，fullCloneReady=false、publicDeployed=false。

本轮精确两个自有网关/测试源码和本说明，共3文件，仅本地提交；不扩大待确认的累计14文件镜像7c21b8c2范围。原Reference、业务数据、数据库、GIS、运行包、截图、凭据及14项held均不入Git。完整目标保持active，完整阶段达成后再通知正式复核。
