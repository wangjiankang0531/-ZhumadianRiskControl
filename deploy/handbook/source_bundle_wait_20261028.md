# 源包有界就绪等待实验

本轮QA源包等待实验，qa=1&bundleWait=1且已协商RAM源格式才启用，默认关闭。完整UE效果/效率、独立EXE编辑器、Web图层、严格天津B/S/后台/H5与迁移目标保持active，fullCloneReady=false；未发布公网或替换8767/18891/252。

浏览器元数据计划可长于服务端RAM源包寿命。计划仍有效而源包被有界LRU回收时，旧grant返回202，客户端固定等待300ms；重建较快也承受完整延时。新grant(wait_ms)在同一Condition锁下注册、测试完成、等待及最终发放租约；0..200ms，bool/非整数/超界拒绝。等待期间没有租约，超时202、不发部分源包；与plan共享既有max_jobs等待上限，关闭和不可变源错误立即传播。RAM256MiB/128MiB构建余量、180秒TTL、租约数、源SHA/完整页/GPU2GiB及最终收益准入保持。

通用HTTP与indexed HTTP仅委托严格单字段wait_ms查询；实际纯数据PreviewOSGBDataLOD支持精确wait_ms=200。响应使用独立X-XNBY-Source-Bundle-Wait-Ms:200；仅精确确认可省额外300ms，旧400查询不支持仅退回原路一次，422源验证、认证/不可用/内部错误不当能力错误重试。准备页与未知格式不添加此查询。成功200转移活租约给调用者，先读取marker并接管租约，再检查晚到取消，避免已发租约被直接抛弃；后续源包/marker/SHA/预算/事务复核不省略。

已有plan传输只处理元数据的注释同步修正，编译viewer SHA保持afb92c7804e6afbd650259f75add2933b3a9a39d642f4f32c31a7ba7ce34f1ce。grant计数属于源包请求，等待耗时与浏览器累计等待有重叠，不相加为总用时；peakGrantWaiters表示grant等待时共享等待槽峰值。
同一候选、两次独立新RAM进程、CSS1920×776/100米近景，关闭组28228/64614正常stop0，开启组25900/55923。后台源码与资源相同，仅浏览器bundleWait=0/1不同；都启用retainedTopology=1和同样witness。共享暖OS缓存、固定先关后开各一次，不构成随机冷OS或稳定整体提速保证。

稳定均31根/held2044119769B，规范可见切面/保留包键/源bytes、实际准入marker SHA和成本序列一致；源请求启动均2115、源包观察均462。源包累计等待51809.700→41198.600ms，单轮减少10611.100ms（约20.48%），不是整页用时节省保证。RAM grant请求277→239，开启组66次等待完成/60次超时，构建均179，最终失败/活动租约/排队均0。reader identity仍b69079a0a8d86d1f54474d2ee6a7eb59141b8cfe6db021c46e2661f134c4e989。

5/20/40秒关闭根19/31/31，开启20/31/31；最高深度均3/4/6，96像素宽稀疏采样基础分别122/0/0与68/0/0，非全视口清晰证明。实际采样时刻、延迟及失败集合完整保存在phase-result/原始witness，不回填时间。近景稳定整视口与扣面板可见区域诊断分别见phase-result，两组完全一致；独立来源ID均差39。返回中景184根，整视口基础0/角[0, 0]，可见区域基础0/角[0, 0]，独立ID差35；源峰2132012357B低于2GiB。代理不等于真实几何误差或最终像素质量，20秒全幅清晰仍未通过。

本地和独立源码917项Web、69项Python全过、无跳过；包含共享等待数、等待中close唤醒、超时无租约、真实indexed HTTP及实际纯数据预览租约身份。独立首次失败暴露工作树indexed_family_source中的旧裁切/锁实验与公开基线接口不同；保留该held工作，仅将本轮查询委托补丁重放在已同步ad9cee6a源码，独立69项通过，不混入裁切依赖。编辑脚本对初始/轮询相同表达式计数失败及异步release测试未await的首个失败保留；修正后检查全过，无运行中热修Python或原生重试。
候选Application/Packages/candidates/WebBundleWait_20261028_Experimental：37文件/1733439B，实际部署只更新静态viewer/worker/html及两个纯Python运行模块，引用已有GIS/索引/0.9.7/纹理/DLG，不复制资产。当前25900/55923/session55144；状态Application/UserData/WebBundleWait_20261028/web-service.json，控制密钥不归档，端口以自有归属状态为准。

体验：http://127.0.0.1:55923/?qa=1&bundleWait=1&retainedTopology=1&levelIndex=1&regionResidual=1&coverageSeed=strict&visibilityGrid=160&recoveryHeadroom=adaptive&completion=coverage&coverageRecovery=1&topic=emergency&inspect=-317,-1988,43&height=350 。验收另加profile=1&profileMode=manual&witness=1&denseAudit=manual&denseReference=1；密集诊断只在稳定后手工执行，不能混入加载对照。两份fresh快照切面/held一致且pending空、扫描done/candidate空才记稳定。回退为保留58491父候选，公网R5/252/8767/18891不改。

源代码使用独立临时Git索引提交，正式HEAD/index与27受保护文件、5194源/索引/图层守护保持。仅本轮源码/测试/handbook镜像，不包含原Reference、GIS、数据库、运行包、截图、凭据或held裁切/锁改动；新的Git外发结果单独记录，不能以本地提交冒称推送。测试结束仅逐SHA封存并清理本轮临时树和具名脚本，保留活动候选与共享源。

下一性能优先：无收益缓存候选仍经过32ms工作调度，本轮2115次请求中仅462次需要源包；应对纯元数据拒绝/缓存命中做有界续跑并验证交互与切面，不能无条件取消节流。之后核对直接LEVEL后代切面与真实几何误差，避免将长三角形边长代理当实际误差。
