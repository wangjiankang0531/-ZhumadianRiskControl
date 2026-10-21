# Web 完整优先级跨帧预算扫描

日期2026-10-21。阶段为本机实验；完整引擎/EXE/Web业务/迁移目标继续active。基线5d541eb：惰性排序和严格状态memo降低重复试算，但已知不可行候选仍会在同一次maintain里累计至300.5ms。

## 算法与集成

source_allocation.js抽出同一orderedSourceCandidates供同步选择与SourceAllocationScan使用。扫描保存完整有序数组与游标；每一帧在场景render提交之后至多执行一个约4ms扫描片段，检查时间发生在不可拆分probe之间。无候选数量上限、无截断、无跳过；最后一项仍可被选中。未知GPU代价仍只请求元数据，不试算其它已知项；首个可行候选终止。一个probe本身可能超过4ms，不能据此声称硬实时或单帧上限4ms。

viewer只在indexedCutsRequested且可见性已准备时接入；pending.type=planning串行占据加载槽，避免另一加载事务同时改变候选代价和增益。animate每帧调用continueAllocationScan，而maintain的700ms节流不限制游标推进。候选状态变化则取消并令下一帧重新采样；已完成且找不到候选时保留正常700ms重试间隔。找到赢家后释放自己的planning槽并立刻调用既有loadFine/loadWebFamily，实际prepare/upload仍新鲜验预算、恢复共存峰值、SHA和租约，不复用可行性执行计划。

每片段重新比较epoch、fine/photo开关与透明度、visibilityReady、visibility snapshot身份、精确相机/投影/FOV、视口、detailLimit/驻留容量/held/staging、restoreFailed、frontier身份和cutVersion/bytes/visible/bundle实际页；状态比较独立于有容量上限的memo，超大context关闭memo时仍能正确取消。侧栏相对viewport的实际遮挡矩形、卫片开关及透明度也参与，避免遮挡变化后继续沿旧可见性排序。sourceOcclusionRects与可见性采样共用实现。

同步候选枚举、排序、状态序列化和一个不可拆分的budget probe仍在主线程；此次分片不宣称这些工作完全离开主线程。profile新增allocation_state和allocation_slice，和原maintain/budget_probe分别展示，帧CPU包括所有这些同步工作，不能只看移出maintain后的数值。allocationScan显示开始/完成/取消/片段/让出/试算计数、最大候选数及最近游标，元数据有固定字段，最近记录不累积历史数组。

## 自动验证

全Web457项通过（旧450加7个扫描测试）。新增5000组随机完整候选和随机时间分片，逐对象核对同步赢家及probe前缀；501候选最后一项获胜，访问顺序和次数完整；中途状态变更无后续probe及陈旧赢家；19ms不可拆分probe后立即让出；未知代价/空队列/零收益、异常/异步probe、非法时间与预算均覆盖。状态比较验证visibility/frontier对象身份、序列化内容和超过memo容量context。这里算法对照不代替原始OSGB GPU来源/深度质量验收。

## 包与首版记录

首版W9/package identity4982ed15dc8452b7829e8dc06fdfb5a840d42354ffc618fa97f2f1f4c9cefd30，仅近景验证，随后补显示遮挡取消；它不能代表最终源码。首版service17764已owner204/exit0；全部证据单独保留。

最终包W9/guarded_mode/package identityfb36a8a31e95db6a00f72822f9069b6f8c9737fa075d13c43321c3da128411ce，viewer SHA256 ddcdd8512d43d05293244104e5f647b2902adc7f577b277878ec1b141492a838。均从前版5840项声明文件复制，仅viewer.js变更；GIS仍外部只读，无旧UserData复制。guarded_mode多一层目录使继承的相对Data绑定首次启动失败（服务52740退出1，尚未ready）；失败日志保留，重新解析同一既有Data后显式绑定，未复制/改写GIS、未改manifest载荷，修复后的服务27008已ready。最终实机结果与回收终态见下节，首版和前版证据保持独立。

## 未完成范围

冷缓存20秒完整性、全区与原始来源深度、8K、Web严格两轮、多视角长稳、满预算视口放大和覆盖桥接仍需独立验证。严格完整cut、2倍质量迟滞及2px缺口准则保持；没有提高512MiB细层预算。旧25已同步ed5fafc；新增14固定镜像0925990等待用户具体批准，当前扫描改动不混入该固定载荷。

## 最终包实测与验收边界

实际WebGL仍RTX5080/D3D11。最终近景采样56.840秒：21根/4082613三角形/363 draw/held536817528，与前版这些数量相同；近景未逐cut核对。中景采样183.092秒，前版160.271秒；根80/前80，三角形4043043/前4043043。保存的最终中景80根逐项核对id、visible节点名称、depth、bytes，和前版followup/final快照全部相同（mid_frontier_comparison.json）；这不是GPU深度/纹理身份验证。加载过程未锁定且未清OS缓存，不能给同画质受控速度倍数或冷20秒结论。

| 指标 | 前版约160秒中景 | 当前最终中景 |
| --- | ---: | ---: |
| 帧CPU最大 | 302.90ms | 16.40ms |
| 帧CPU最近256帧P95 | 2.50ms | 2.80ms |
| 帧间隔最大 | 293.40ms | 40.10ms |
| 帧间隔最近256帧P95 | 13.40ms | 13.40ms |
| maintain最大 | 300.50ms | 8.10ms |
| allocation_slice最大 | 无独立阶段 | 14.10ms |
| allocation_state最大 | 无独立阶段 | 0.70ms |

中景扫描累计开始3406、片段4918、让出1512；统计跨机位累计不等同中景阶段独有。扫描工作移到每帧后，最近P95不一定比前版低；需同时看包含扫描的frame_cpu，不能只以maintain下降宣称工作消失。单probe/片段仍可能大于4ms。原始启动shader帧CPU尖峰保留在近景初始phase，不能与中景phase混为零长帧。

实际近/中/道路/总览四站及额外相机切换；累计覆盖464、拒绝4、恢复8、恢复错误0。源加载事务取消2次，但planning扫描取消计数为0；切换时未命中活跃扫描，不能把单元测试当成UI取消分片的实测。道路视口1280×573，单次道路不构成严格两轮或全场景质量验收。

道路source_upload最高75.70ms、帧间隔最高66.80ms、coverage最高49.20ms，仍存在加载长耗时。frame_cpu只包围animate回调，包含本次移入的扫描，但不覆盖回调外异步加载续体的全部CPU工作；不能凭道路frame_cpu最大18.4ms宣称整个主线程均无长任务。当前没有把上传峰与某个帧间隔做逐事件因果配对。下一步除满预算resize外，需分解并处理这类上传/覆盖尖峰。

最终roots/active/retained/coverage均0、held1024，峰536870112字节≤512MiB，仅细层账目非整个浏览器VRAM。最终服务27008、session9331已owner204/exit0，读取进程closed、保护写0，最终lease/job/waiter和原始样本SHA见guarded_mode运行回执/最终私有--check日志。服务总时长414.921秒含停留和额外机位，不是加载时间。源码冻结SHA及重建viewer逐字节相同。

新入口Application/实验入口/地景加载优化_20261020/启动Web跨帧调度实验.cmd已生成未代运行，guarded_mode/manual_runs每次独立日志。前版保留可回滚，公网/EXE/用户DLG/业务库未切换，数据库结构未变。冷20秒、外围细节合理覆盖、满预算视口放大/桥接、全区/Web严格两轮/原始OSGB深度及8K仍未完成。
