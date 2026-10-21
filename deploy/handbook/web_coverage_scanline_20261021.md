# Web覆盖掩码扫描线判定与分段采样

日期2026-10-21。本机实验阶段，承接ec1b4c6；完整UE渲染效率/效果、EXE标注、Web业务、迁移目标active。本阶段聚焦道路覆盖检查CPU尖峰，不冒称满预算窗口放大或上传尖峰已解决。

## 依据与算法

在不可变的旧积分算法包中新增独立coverage_draw、coverage_readback、coverage_compute计时。RTX5080/D3D11道路11次检查：coverage最高49.5ms，CPU比较最高44.0ms；22次绘制提交最高0.3ms，22次同步读回最高3.0ms。这是函数段耗时而非整张GPU帧/完整主线程调度统计；绘制提交不等同GPU完成时间。source_upload仍最高64.4ms，需后续单独处理。

原判定在每个中心像素的裁剪5×5邻域中要求“父层每个像素有覆盖，且替代层每个像素无覆盖”。定义bad = (parent.red == 0) OR (child.red != 0)，原条件严格等价于邻域所有bad均0。先求每行裁剪±2像素的bad存在标志，再对上下±2行求存在标志；所有标志为0才累计loss。这是布尔OR的可分离滑动窗口，不是降采样或近似容差。

固定5行环形缓冲、1行bad、1行columns，均Uint8Array，共7×width字节；columns是最多5行的布尔标志计数，不会溢出。按输出行先移除过期环形行，再载入新行，避免环形槽覆盖仍在使用的行。每个父像素读入时计数一次，parentPixels精确保持。窄图、高度不足5、四角和屏幕边缘继续使用原裁剪邻域，尺寸上限仍4096×2160。原2px标准、投影ROI、4px投影边缘余量、近裁面回退、完整cut、GPU预算和恢复保护均不变。

算法时间仍O(width×height)，比较临时缓冲从两张Uint32积分图的8×(width+1)×(height+1)降为7×width。这里不包含两张RGBA读回数组、GPU颜色/深度目标、几何和纹理，不能将这一数值当全部内存/显存。

## 测试与可复现基准

全Web461项通过（457+4）。新增10000组随机输入与冻结的旧积分函数逐项比较loss和parentPixels；包括非255红通道、父/子稀疏率、所有窄尺寸组合、四角、全空/全满、最大4096×2160和非法输入。既有独立逐邻域oracle及渲染状态恢复测试继续通过。

web/tools/benchmark_coverage_mask.mjs仅在直接执行时运行，冻结旧函数作为参考，先检查结果一致，预热后两种算法分别12次采样；node tools/benchmark_coverage_mask.mjs --out result.json。固定掩码Node CPU中位数：1280×573约6.432→2.172ms，1920×1080约18.089→6.436ms，4096×2160约77.464→27.064ms。顺序微基准不代表浏览器GPU、冷启动或加载SLA；最大视口CPU仍非硬实时。

1280×573比较临时缓冲5882352→8960字节；4096×2160为70828936→28672字节。分段采样仅qa=1&profile=1开启；默认measure回调直接执行，不改变原返回值、异常或finally状态恢复。

## 精确运行包与边界

旧积分计时基线W10/package manifest30d49d300c191d4c1084fadcae29ca8c6971444d85911dd17840782f707bde2a，viewer58817a72d59ba6a4ba49f6fa76c88224c8582e08b64645cf850a9d6cfed0725f。新扫描线W10/scanline_mode/package manifest70c71b1afa5a7e423944746dd11629a6fe20e7c843da04212708cf396fb6ffc4，viewer8382cc01d7b7e58af96274a3da7da1e1792d41f60ffc37fa25e6f56c8a469d3c。各5840声明文件仅viewer.js变化；沿用同一外部只读Data绑定，无GIS或旧UserData复制，前版本保留。

基线只执行早期近景→道路→总览；新候选单独记录机位序列、分段结果和资源终态，不能把不同路径当严格双轮验收。冷20秒完整性、全区、原始来源深度、8K、满预算视口放大和上传尖峰仍未完成。旧25已同步main ed5fafc；新14固定source5d→0925990等具体授权，后续6文件ec1和本轮改动独立本地，不混入该批准范围。

## 最终实机结果与运维终态

新旧道路相同RTX5080/D3D11、1280×573，采样跨度旧61.689s/新62.009s。两版分别留存37条覆盖日志，末11条道路事件逐项对比root、parent、loss、parentPixels、region、width/height、tolerance全部一致；道路最终3根的id/visible/depth/bytes全部一致（road_pair_comparison.json）。没有归档原始RGBA掩码，不宣称独立GPU深度/纹理来源验收。初始近景停留略不同，未清OS缓存，不是固定冷启动trace。

| 道路实测 | 旧积分 | 扫描线 |
| --- | ---: | ---: |
| CPU比较11次总耗时 | 95.10ms | 33.60ms |
| CPU比较中位数 | 5.70ms | 2.50ms |
| CPU比较最大 | 44.00ms | 8.30ms |
| 整个覆盖检查最大 | 49.50ms | 13.30ms |
| 单次读回最大 | 3.00ms | 4.30ms |
| 单次上传最大 | 64.40ms | 60.90ms |
| 帧间隔最大 | 53.40ms | 53.40ms |

覆盖比较改善不等于整体帧率或加载时间同比改善；上传/读回未因此消除。新候选再完成近景约56.274s（21根/4082613三角形/363draw/held536817528），中景采样快照74.360s（93根，仍在加载，非稳定终态），随后总览。实际路径为早期近景→道路→近景→中景→总览；旧基线没有相同完整路径，不能当严格双轮。中景仅阶段回归，非全场景质量验收。

新候选累计覆盖393、缺口拦截4、恢复6零错误；总览roots/active/retained/coverage均0，held1024，峰536870112字节≤512MiB。基线service53876/session95195已owner204/exit0、reader closed；扫描线service57468/session22171已owner204/exit0、reader closed，保护写0，最终lease/job/waiter0，最终私有--check和原始样本SHA验证通过。总服务时长旧160.953/新321.250秒含停留，不是加载时间。冻结源重建viewer逐字节同。

新手动入口Application/实验入口/地景加载优化_20261020/启动Web覆盖扫描线实验.cmd已生成未代运行；随机回环、独立scanline_mode/manual_runs，owner/Job关闭自己的进程。公网/EXE/用户DLG/业务库未切换、无数据库结构变化。下一步修复满预算视口放大无法分配coverage target的问题；上传峰、外围合理层级、冷20秒/全区/Web严格两轮/原始来源深度/8K仍保留。
