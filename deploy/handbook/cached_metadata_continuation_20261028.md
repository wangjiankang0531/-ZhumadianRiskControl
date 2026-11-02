# 缓存元数据有界续跑实验

QA metadataContinuation=1且qa=1才启用，默认关闭。SourcePlanCache.readCached仅返回该缓存中原有的私有固定计划，检查取消与路由边界、不发网络请求、不授租约。prepareSourceAllocation须实际命中该入口、LEVEL请求计数不变、全为RAM原像素页、客户端裁切关闭，且仅在计划重排、已知成本或精确输入收益缓存拒绝时标记metadataOnly。未命中、提前加载lookahead、准备页/裁切、实际源包、载荷读取、上传、取消或错误均维持原路径。

根/局部请求开始时保存epoch、相机、规范可见切面、面板/透明度/显示状态及GPU held；finally释放原有对象、pending清空后，仅同状态可申请元数据续跑。每步仍让出postTask/通道任务，累计配置4ms/最多4步，窗口到期或guard改变恢复32ms普通节流；不会在同一microtask循环无限推进，也不增加并行Source事务。allocation scan原有4ms探测、256MiB源RAM、租约、2GiB源GPU、源SHA、完整页、覆盖/收益与原子切换保持。不可分操作可能超过时间窗口，不能把配置当硬CPU截止。

首版实际发现guard本身耗时后maxMetadataStartMs达4.1ms。R2把窗口检查移至guard之后，增加“guard耗时计入窗口”测试；首版结果保留而非回填，独立新进程验证R2，没有运行中热替换。新增8个调度边界与2个缓存来源测试，总927项本地与独立全过、无跳过；后端未变，沿用已独立验证的源包等待后端。独立首轮漏带shared空间词表、空库schema清单及覆盖基准源码导致失败，补齐固定父提交原字节后全过；Windows构建工具GBK输出及ESM绝对路径问题修复记录保留。独立编译viewer与实际候选逐字节一致。
同机位CSS1920×776/100m，固定先关闭、再首版、再R2，均新RAM进程，复用暖OS缓存，非随机/冷缓存基准。两组最终31根/held2044119769B，规范cut/保留bundle键/源字节同=True，整幅及扣面板可见区域诊断同=True；actual admission audit未启用，不能声称已采到实际准入顺序。源候选请求2115→2115，最后一次请求结束时刻169388.300→157706.000ms（单轮提前11682.300ms，不是完整画面完成时刻或普遍提速保证）；请求间累计调度等待49438.000→38950.200ms（减少10487.800ms）；源包累计等待41015.300→40866.100ms，与调度等待不可相加为总CPU时间。R2实际快速续跑345、恢复普通290，最大记录起步窗口3.9000000059604645ms、调度错误0。

5/20/40秒实际观察：关[20, 31, 31]，开[21, 31, 31]，实际时刻及可见性见phase-result，不回填。96像素宽稀疏采样不能证明全视口清晰。稳定近景独立来源ID差39/39，仍未通过。返回中景184根/held2117595301B，基础/超阈/角全幅与可见区域见JSON，独立ID差35；边长/texel代理不是真实几何误差，20秒整幅质量与最终UE目标未通过。所有长任务原始事件保留，累计统计受采样时长影响，不把稳定后p95或FPS当拖动验收。
候选Application/Packages/candidates/WebMetadataContinuation_20261028_R2_Experimental，37文件/1735492B，只读引用既有GIS/索引/图层/纹理，不复制资产。R2自有46932/53669/session46435；关闭组32464/63687/session45933和首版41204/54479/session54022均正常停止、exec退出0。保留55923父候选，不修改8767、18891、公网R5或252，不调用被隔离原生fixture/读取器。

体验：http://127.0.0.1:53669/?qa=1&metadataContinuation=1&bundleWait=1&retainedTopology=1&levelIndex=1&regionResidual=1&coverageSeed=strict&visibilityGrid=160&recoveryHeadroom=adaptive&completion=coverage&coverageRecovery=1&topic=emergency&inspect=-317,-1988,43&height=350 。QA性能诊断另加profile=1&profileMode=manual&witness=1&denseAudit=manual&denseReference=1。稳定后才手工诊断，不混入启动计时；两份新快照pending空、扫描done/candidate空且cut/held同才收敛。回退使用保留55923父候选或关metadataContinuation；候选不自动发布公网。

新代码使用自有临时Git索引封存，正式HEAD/index及27保护/5194源索引图层守护单独核验。精确源/镜像及实际Git结果见review-payload；不得把本地提交冒称远端同步。源包等待旧11文件尚待具体授权，本轮新增载荷不可套用旧7文件许可。源码镜像不含Reference、SDK、GIS、索引数据、业务库、运行包、截图、凭据或held改动。资料齐备后本轮临时副本逐SHA归档清理，活动状态/控制密钥不归档，保留小型候选与共享源。

下一优先：两组末尾元数据请求均出现约1秒主线程长任务，须定位并在保持完整准入顺序与当前切面复核的前提下拆分同步工作，不把本轮续跑当交互已通过；之后推进实际LEVEL后代切面跳转和几何误差/纹理质量，缩短20秒内仍逐级细化的过程。继续分析独立源ID差，不以根数、内存下降或性能代替视觉验收。长期UE效果/效率、驻马店独立EXE/PNG点线面/图层、Web、严格天津B/S后台/H5与迁移目标保持active/fullCloneReady=false。
