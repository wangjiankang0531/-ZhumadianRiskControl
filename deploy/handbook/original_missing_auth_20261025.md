# 原指挥页处置日志 500 与未登录鉴权诊断

原大屏“现场核查”出现的压缩错误 i，实际为处置日志 HTTP 请求的 AxiosError / ERR_BAD_RESPONSE / 500。独立 j6 页通过只读 DOM 观察保留错误描述，同时原三维视频 1920×856、ready4、paused=false。原 UI、SDK、业务方法未修改。

## 定位与证据

原 dealLog.vue 在事件变化时调用 /eventDisposalRecord/getListByEventId。以原事件列表取出的选定事件 ID 向自有测试网关只读请求，实际返回 HTTP500、业务 code100000。先前含糊错误不能称为三维绘面故障。

原 SecurityInterceptor.preHandle 先读取 X-TOKEN，若空则取 Authorization，并直接执行字符串替换。两个头都没有时触发 NullPointerException。用同一固定运行依赖、原控制器方法及空请求替身实际复现，错误位于原 preHandle 的 String.replace；未调用原控制器方法、没有数据库连接，没有读取、创建或伪造 Token，也没有改变认证规则。

另作排除检查：固定原运行控制器反射参数名存在；参考控制器虽无 MethodParameters，原 Spring 的局部变量回退仍能得到 eventId。两者实际参数解析均通过，不能把本次500归因参数名缺失。对自有测试库先核对 server UUID、启用只读事务，再查到处置记录39条，最近20条字段及 LocalDateTime 转换通过；这不等于所有记录或原服务完整链路通过。

## 自有工具

original_browser_error_observer.js 仅用于独立诊断页，通过被动 error/rejection 监听和 console.error 代理，把有限错误字段写入隐藏 DOM；保留原 console 调用的 receiver、参数、返回值，不阻止默认错误处理，不读 getter、不发网络请求。7组离线契约检查通过，记录最多40条，常见 URL Token 和 Bearer 文本遮盖；本地原错误证据仍按私有记录保存，不上传 Git。

diagnose_original_missing_auth.py 校验既有219依赖、固定应用与控制器字节、Java17，再编译自有 OriginalMissingAuthenticationProbe。只使用空请求替身复现失败，不启动后台或登录：

```powershell
python -B tools/diagnose_original_missing_auth.py --workspace work/tianjin_native_20261023 --output work/tianjin_native_20261023/own-missing-auth-check-new
node tools/test_original_browser_error_observer.mjs
```

j6在生成的独立配置前附加观察器，原生成配置作为精确后缀保持，原UI构建资源全部复用；不是生产前端覆盖。测试页关闭后，网关/第三后台自然exit0、原ContextClosed、Mock停止、参考SQLite与原归档SHA不变。原机页面已恢复。

## 处置与待验

保持原鉴权，不增加匿名白名单、不合成响应或登录Token。已打开并保留本机候选原登录页，请用户使用原账号正常登录，验证码由用户手动完成。随后复核带真实登录状态的处置日志、角色菜单、附件及完整 PC/H5 流程。目前只证明缺失认证分支会失败，尚不能声称带有效Token通过或问题已全部修复。

本轮未改数据库字段、索引、业务归属或原数据，不需重生成物理模型。持久附件/身份/密钥/重启探针保留，原公网和正式8767保持。完整复刻及长期引擎、编辑器、网页、迁移目标 active，fullCloneReady=false。详细证据仅本地 Document/Deployment/original_missing_auth_20261025。
