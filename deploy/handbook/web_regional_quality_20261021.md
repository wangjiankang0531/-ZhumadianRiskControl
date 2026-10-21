# 屏幕九宫格质量优先级实验与读取器握手故障留证

状态：仅源码/单元测试通过，真实质量对比未完成；未切换用户运行版本。W18/W19提供给用户的8768仍为已验证包，企业14与台账14已恢复。不能把本实验称为角落清晰度修复完成。

假设：原总像素收益目标可能让中央更大面积持续优先，左右角的露出区域受面板面积影响。新增visibilityRegionWeights，在实际深度测试摄影像素上按3×3计算露出采样数量；各区域以有效区域平均样本数/本区域样本数补偿，因子严格限制0.5至2。遮挡区仍0.2、无摄影区不增加优先级。权重不依赖root/node编号，不依赖当前层级；所有原始几何、像素、采样、完整cut、覆盖与512MiB门槛不变。

仅qa=1&regionBalance=1开启。SourceVisibility的优先级、几何增益worker采样和退层损失都使用同一组权重；固定时刻独立诊断继续原始区域质量均值，不能把重加权后的总分降低当作画面变清晰。全Web518通过，包含旧策略等价、全无遮挡保持、左右面板下等区域影响、小露出上限、sky/编号不变等5项数值性质测试。是否改善真实20秒角落，需要成功的同视口/相机对照，尚无结论。

候选包identity32b5256d3ab282e8d28cb45923ac4feacf9bfb2bda6e4631ddeac246ba6f6488，viewer19f7572d0655ba40b9a8ad9915a317f076ea751b8562112f3f9b18c7d0c54044。5840声明文件逐SHA克隆W18，仅viewer变化，四源/测冻结。原Data仍只读，不复制GIS或UserData。

独立legacy对照controller49688/service54316/port50934/session7183，读取器6216握手前关闭stdout，starts1/handshakeComplete=false/attemptedRequests0/requests0；自然NTSTATUS0xC0000043、ownerTerminated=false，失败阶段handshake/EOFError。26个请求失败，其后保持held，无自动重启/旧实例重试；40秒全部2447采样为基础层。因此该轮无可比细层质量，balanced case尚未启动。25个reader EXE/DLL/插件逐SHA同成功W18，不能凭字节相同就推断运行必然等价。系统按时段查应用/CodeIntegrity/Defender日志未返回匹配记录，不据此宣称不存在安全或共享访问干预。故障服务已owner204/exit0、workerclosed、保护写0，失败记录不覆盖。

Microsoft MS-ERREF定义0xC0000043为STATUS_SHARING_VIOLATION：文件共享访问不兼容。此定义不能说明具体哪个文件/持有进程/组件导致本次退出；根因仍未知。来源：https://winprotocoldoc.z19.web.core.windows.net/MS-ERREF/%5BMS-ERREF%5D.pdf 。未改ACL、杀毒、文件权限、系统服务或防火墙；不通过绕开校验或重新启动失败reader把本轮伪造成通过。

现用户8768的reader57944保持alive/ready、一次启动且无失败，记录E20/user_scene_unaffected.json。W14原始退出亦未定因，本次有阶段/NTSTATUS补充证据，但不能追溯声称W14也是同原因。下一步应查只读文件占用/共享访问与启动时间线，并在明确受控前提后继续真实配对；必要时只在既有健康只读数据接口上做明确标注的前端专项测试，不能用其代替新包独立运行验收。

证据Document/Deployment/web_regional_quality_20261021，失败实例不可覆盖重启。全项目目标仍active，角落质量、冷20秒/全区/严格双轮/mip/RGBA深度以及EXE/业务/IAM/252/迁移继续待完成。
