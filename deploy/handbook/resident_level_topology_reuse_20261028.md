# 常驻LEVEL拓扑复用与需求观察

本轮仍为默认关闭的QA实验，未部署公网、未替换8767/18891/252。长期UE效果与效率、独立EXE编辑器、Web图层查看器、严格天津B/S/后台/H5复刻及目录迁移目标均继续active，fullCloneReady=false。

先加有界需求观察：qa=1&demandAudit=1，仅在maintain之前记录相机、需求集合和退出原因。最多32事件、每事件20个退出详情，明确截断；不改变需求或GPU预算。不把此前根数骤降直接解释为预算抖动。本次固定近景中相机/需求未变化且没有根退出，不能证明旧现象原因已经解决。

常驻根的SourceFrontier已持有经过原始索引SHA校验、递归冻结的完整拓扑，但准备子族时仍访问16根LRU；近景31根导致部分重复加载。显式qa=1&retainedTopology=1允许tile(id,retained)复用同一索引实例私有WeakSet确认的原对象。克隆、其它索引实例、其它根及仅通过公开validator的对象均拒绝；先检查取消，原16根LRU及并发上限不变。WeakSet不额外强持有数据，离开常驻集后无新增资源所有权。实际源页/拓扑/完整性/SHA/预算/收益和原子提交仍按原逻辑复核。
独立最终本地、源码闭包和干净review树各909项Web检查通过，新增6项需求观察及5项拓扑归属/取消/缓存边界检查。Python未变，不冒称重跑此前101项。首次编辑脚本把4处await调用误计5处导致断言中止；核验部分写入SHA后确定性重建。首次接入遗漏measureAsync主回调，真实hits=0记录保留，随后修正并重跑全部检查、正常停止该自有进程再更新；没有热修改运行Python，也没有重试任何原生读取器。

CSS1920×776、固定100米近景，优化前稳定31根/held2044119769B、拓扑等待8284.89999961853ms、源请求启动2115。优化后稳定31根，规范可见切面/包键/每根源bytes相同=True，held相同=True；复用2084次、实际拓扑加载31次，等待11.200000017881393ms，源请求启动2115。规范对比排除局部cutVersion计数与Map插入顺序，不是GPU对象或纹理readback逐像素相同证明。两次新鲜采样pending空且完整扫描无候选。相机变化0、同机位需求变化0、根退出0。

实际64次常驻请求序列/18根重放：旧实际tile读取20→18，46次复用、16根LRU不变，全部返回拓扑SHA序列相同；共享暖后端与OS，仅元数据重放，不代表整页冷启动A/B。真实场景拓扑等待减少，但整体近景仍需持续细化，20秒全幅清晰未通过，不宣称整体稳定提速。

近景完整分配后返回中景稳定184根、held2117595301B，源峰2132012357B<2147483648B。整绘制视口基础0、角[0, 0]、代理超阈809117；扣除面板可见区域基础0、角[0, 0]、代理超阈676655。独立来源ID仍差35，不能将覆盖补齐当全区画质通过。dense检查后cut/账恢复=True。

前阶段文档口径已纠正：关闭覆盖恢复组的3971/610与3049是整个视口，1193/610与271是扣面板可见区域。启用组首次代理809156全幅/676694可见，返回823863全幅/691390可见；两种均未改善。原始ZIP、失败与来源差异保留，phase-result增加明确scope字段。
独立候选Application/Packages/candidates/WebDemandAudit_20261028_Experimental约1.73MB，只读引用现有GIS/0.9.7/准备页/LEVEL/纹理/DLG；不复制GIS、不写资产页/业务库。当前PID48464/58491/session21977，状态Application/UserData/WebDemandAudit_20261028/web-service.json；动态端口以归属状态为准，控制密钥不归档。前两个自有运行44744/59392和41800/62312均正常stop0/会话0，不动51061及用户服务。

体验：http://127.0.0.1:58491/?qa=1&retainedTopology=1&levelIndex=1&regionResidual=1&coverageSeed=strict&visibilityGrid=160&recoveryHeadroom=adaptive&completion=coverage&coverageRecovery=1&topic=emergency&inspect=-317,-1988,43&height=350 。需要观察时加profile=1&profileMode=manual&demandAudit=1；先展开明细，再刷新并读新generation。两份fresh完整切面/held一致、pending空且扫描done/candidate空才记稳定。性能对照固定相机和CSS尺寸，不将自然窗口或密集诊断混入加载速度比较。回退到保留的51061父候选。

Source/测试/handbook以临时Git索引精确检查点保存，不修改正式HEAD/index，不写main。新载荷同步需按实际推送结果记录，不能把本地镜像当外发成功。代码不含Reference/资产/业务库/运行包/凭据/旧held修改。只清理逐SHA封存的本轮临时副本和具名脚本，保留活动候选及共享资源；记录逻辑删除量与磁盘实测差，不能混称。
