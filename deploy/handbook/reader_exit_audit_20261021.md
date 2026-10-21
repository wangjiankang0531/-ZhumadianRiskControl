# 原始地景读取进程退出审计（2026-10-21）

状态：诊断功能与正常细层集成回归通过；旧W14退出原因仍未复现、未定，不宣称根因修复。完整项目目标active。

W14 reader37692在首个有效响应前stdout关闭，原代码只在完整响应后增加requests计数，且失败时立即关闭kill-on-close Job，因此requests0不能区分握手/首请求，清理可能覆盖原生退出码。本次保留phase（launch/handshake/request_write/response/ready/held/closed）、handshakeComplete、attemptedRequests/成功requests、首个failure.phase/type/winerror、nativeExitCode/Hex、cleanupExitCode与ownerTerminated。审计不复制异常文本或stderr内容，避免公开本机路径。

EOF时只对已拥有且确实存在的子进程等待最多0.25秒，使自然退出码有机会可读，再执行原hold和自有Job清理；清理等待最多1秒。未增加失败重启或解码重试，不放松读帧、源SHA、只读或预算规则。原生退出与所有者终止码明确分开，首个失败阶段不被随后close覆盖。5新增故障/成功路径测试，加原帧/内存读取/存储共32Python测试通过；覆盖自然NTSTATUS、活进程EOF清理、写/响应计数、启动winerror225不重试、成功正常close退出0。

一次独立受控复现包d8ec29f7fe35b3c9bb4f335879b6aa354c9b5397e813350591ec17eeac98e561，5840文件，只改application/tools/osgb_stdio_worker.py与manifest。25个读取器EXE/DLL/插件文件与W13已通过包、W14失败包逐SHA相同。先请求原失败api/lod-plan/118/3，202后200，启动1/响应1/握手通过、没有失败。随后正常浏览器：近景21根/4082613三角形/363draw，held536817528；道路218页、最终3根/3858445三角形/36draw/held230757468，与W12基线完整前沿和11覆盖事件逐项同；中景56.220s/124根仍pending，是阶段回归，不当全区稳定完成。

reader55700共779次尝试/779有效响应，启动1、失败0、未重启。累计覆盖262/拒绝4/恢复错误0，峰536869332≤512MiB；总览1214位图全关闭、owned0、roots/active/retained/coverage0、held1024。controller57456/service58352/port58423/session42487已owner204/exit0，worker最终closed/nativeExit0/ownerTerminated=false、保护写0，tab24已关闭。旧W14不复现不能据此排除输入、系统加载或安全软件等原因；没有新证据前不改安全配置、不执行自动重启。未来同类故障可直接读取精确阶段与自然退出码。

证据位于Document/Deployment/reader_exit_audit_20261021。尚非Web严格双轮/冷20秒/场景深度RGBA完整验收；原始GIS、用户图层、数据库、native held与安全hold保持。实现仅本地Git，旧14镜像授权待答，不将本批混入。
