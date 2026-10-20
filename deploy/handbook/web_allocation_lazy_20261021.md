# Web 原优先级惰性预算试算与严格状态缓存

日期2026-10-21，状态：本机实验改善，完整目标active。承接性能基线e6a4548，实际WebGL设备RTX5080/D3D11；原调度在保存的中景采样中占帧CPU约94.25%，一次最高604.7ms。

## 问题与实现

旧allocationCandidates先对大量候选逐一做完整预算/回退可行性试算，之后才按优先级挑选，即使排名最高的未知代价候选只需元数据，也先为其余候选付出试算成本。source_allocation.js新增chooseFeasibleSourceCandidate：完整验证候选，按完全相同的根覆盖优先/未知代价/收益密度/分数/字典序排序；只沿原赢家顺序检查可行性，找到首个可行候选便停止。未知代价仍只请求元数据。没有截断候选、减少加载区块或改变优先级。仅indexedCutsRequested模式接新路径，默认旧模式保留原过滤及选择。

source_allocation_memo.js只缓存同步只读可行性boolean，包含false；最多4096条、1MiB的UTF8键/上下文加每条64字节保守元数据账目，不宣称这是精确JS heap。上下文过大则不缓存。严格依赖当前visibility snapshot引用、frontier对象引用、精确相机/投影/FOV、视口尺寸、limit/驻留容量/held/staging、visibilityReady/restoreFailed、每root cutVersion/bytes/visible/bundle及实际驻留page目录。请求root/parent/score/cost分键，任何相关变化失效。

缓存仅用于挑选候选的apply=false提示。实际上传仍走原canMakeFamilyRoom(...,true)、恢复共存峰值、SourcePageBudget及begin剩余字节检查；不复用旧执行计划，不降低2倍质量迟滞、完整cut、SHA、租约或2像素覆盖准则。frame_profile增加budget_probe，显示缓存统计，能区分省掉的重复试算与真实上传检查。

## 测试与精确身份

4000组随机候选对照穷举可行性过滤，indexed/legacy两种排序得到同一对象赢家，包含未知代价/0收益/密度和字典序平局；128候选首项可行时只做1次probe。18类相机/可见性/cut/page/预算等状态变化逐项失效；同状态300次false只算1次/299命中；LRU容量与字节上限、超大上下文、异常/异步probe拒绝、非法请求均有测试。全Web450项通过。此处算法对照不是原始地景GPU来源/深度验收。

优化包manifest e58d4a75fd879a74c72cc66719d573383fb9054c9ec1afaf95a58baa0712c668；viewer SHA256 91af41bb7a4d7ae2789cbc198d5fd203d209475765f7f25c449c3eaebc796c65。对照包manifest8c05d4e52861edc153e5ea8bc86efbe4e92373a0bbfa56b5fb67afe7b65f677e，独立不改。新包5840声明文件，只替换viewer.js，不复制GIS/旧UserData。规范未变行行尾后重建产物逐字节同，最终私有Python --check通过。

## 实际性能结果与比较边界

两版均为同一中心350米、同一WebGL设备和性能采样开关，但未清OS缓存，没有锁定相同活动cut，不能给出同画质受控提速或冷20秒SLA。保存的可比时间段：基线frame_interval跨度157202.7ms，优化160270.7ms；根91/80、三角形4078644/4043043，画面细节分配不同，不能只按FPS宣称质量等价。

| 指标 | 基线中景 | 优化中景约160秒快照 |
| --- | ---: | ---: |
| maintain最近256次P95 | 351.7ms | 9.0ms |
| maintain平均 | 200.032ms | 5.312ms |
| maintain最大 | 604.7ms | 300.5ms |
| 帧CPU最近256帧P95 | 176.9ms | 2.5ms |
| 帧间隔最近256帧P95 | 173.2ms | 13.4ms |
| 帧CPU累计>50ms次数 | 503 | 48 |

以上P95是最近窗口，不能当整个阶段所有帧的分位数；全阶段mean/count/max保存在performance_comparison.json，嵌套CPU耗时不相加。优化240299.4ms后续快照调度P95 7.2ms，最大仍300.5ms。近景两版都21根、4082613三角形、363 draw计数、held536817528；调度最大169.1→14.3ms，P95 131.7→4.3ms，但不宣称已证明完整cut逐节点相同。

残留300ms峰说明一批已知不可行候选仍可在一次同步扫描中累计很多独立probe（单probe最大约13.4ms）。下一步应保留全部候选/原顺序，在同一状态下跨帧继续扫描，改变状态就取消重来；不能限制候选数量来掩盖阻塞。当前改动显著降低调度开销，尚未彻底消除长帧。

## 实际回归、回收与运维

优化候选近→中→道路→总览4站，累计44次混合cut提交、405次覆盖检查、6次缺口拦截、6次恢复0错误。道路期间视口缩至764×567（此前1280×573），源包manifest没变，GPU coverage target正确改为3465504字节；道路为2根/最高depth6，不与前版1280道路截图作逐像素/逐根配对。只验证了这次缩小，不冒称满预算放大resize已解决。

返回总览roots/active/retained/coverage0、held1024、textures4/geometries2。细层峰536870112字节，低于512MiB仅800字节；仍非整个浏览器VRAM。服务整会话501.328秒含停留和多机位，不是加载时间；owner204/exit0、reader closed、保护写0，服务构建失败0/最终leases/jobs/waiters0。最后warn/error列表为空。

本机体验入口Application/实验入口/地景加载优化_20261020/启动Web调度优化实验.cmd，未代用户运行；开启qa/profile，右侧性能明细在窄窗CSS下可能隐藏，宽窗可滚到信息栏下方查看。私有Python -I -B，随机回环、每次manual_runs独立，Ctrl+C/关控制台或30分钟owner/Job关闭。原入口与包保留可回滚；正式公网、EXE、业务库不切换，数据库结构未改。

## Git与完整目标

用户批准的旧25已单独push并fetch/tree/25blob核验到main ed5fafcff91e77fa5ba78fb292e3f921184d8ccf，仅source3e8b62d，后续代码未混入。本轮按明确列表本地提交源/测/handbook及两份旧handbook同步状态更正，不含GIS、索引数据、运行包、图片、用户资料、凭据或14held。引擎master末查仍da9898f3054f898924dc1637771eb2947e2d5131，无新提交。

后续跨帧预算扫描、满预算resize/覆盖桥接、冷20秒/全区长稳/Web严格两轮/原始OSGB CPU/GPU来源深度/最细8K仍未完成；UE效果效率、EXE标注、Web业务/IAM、261013、252实机与迁移完整目标active。
