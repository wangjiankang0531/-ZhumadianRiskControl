# 手机登录页应急标识与H5图片基路径

2026-10-25，本机手机端实际渲染检查发现：项目名称和浏览器标签图标已更新，但登录表单上方仍为中远海运LOGO。原组件为mobile/src/pages/login/login.vue，构建资源固定为logo-C4nOa3Mc.png。

修正仅在original_project_branding.py添加该确切资源URL的静态响应替换，并把既有自绘应急SVG同时挂载于/zhumadian/h5/project-icon-20261025.svg。原Reference、构建产物、账号、验证码、登录加密、表单和四个业务/API代理块保持。不将普通公司名称或其它业务图片整体替换。自绘SVG不是官方徽章。

不能简单把uni-image的src改为根目录/zhumadian/project-icon-20261025.svg：原框架wg→_g会把不在H5基路径内的绝对路径重新拼入/zhumadian/h5/。实测该尝试导致图片为空，现改用H5基路径内URL，原框架无需修改。曾测试SVG显式尺寸，未解决路径问题，已恢复原598字节SVG/SHA509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d。

本机18891只平滑reload既有Nginx，PID19296保持、后台不重启。实际登录chunk不含旧LOGO URL，新H5图标HTTP200且与原SVG逐字节一致。浏览器DOM确认image.complete=true，naturalWidth/Height=150，显示120×120，截图已保存。另由更新后的源码重新生成canonical HTTPS网关，真实nginx -t通过，四API块逐字节等于未加branding的生成基线。第一次检查因换行差异在任何写入前停止；首次reload后立即读取曾看到旧worker，随后读取到新响应，未以此重启后台。

封存交接ZIP仍为0a9174d21fc9815697f57ac49fbef7e75bee09ac4cbcb9508a1e0f2663564f8e，本修正尚未进入该包，不修改用户可能正在复制的固定载荷。服务器该包发布后需另行交付受控的branding增量并验证新旧控制器清单；不能直接覆盖受SHA约束的已安装源码。当前仅本机显示通过，公网发布、手机真机登录/审批和完整复刻均未验收。源码同步状态另见Git收据。

私有证据：Document/Deployment/original_mobile_login_logo_20261025，含原配置/源码快照、语法日志、receipt.json、DOM和本机截图。截图、运行配置、Reference、数据库、运行包、凭据不提交Git。
