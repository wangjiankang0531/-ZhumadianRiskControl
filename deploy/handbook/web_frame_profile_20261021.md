批准后接续更新：此前待批25文件已单独同步并远端核验到main ed5fafcff91e77fa5ba78fb292e3f921184d8ccf（仅source3e8b62d）。下面保留该实验当时记录；最新调度改动及同步状态见web_allocation_lazy_20261021.md，不把新代码混入旧批准。

# Web 分段性能采样与中景调度基线

日期2026-10-21。完整目标active，本轮是诊断基线，不宣称卡顿已解决。qa=1&profile=1才启用；正式默认页面不显示诊断，不读取计时器/设备扩展或创建GPU查询。

## 实现与测量口径

frame_profile.js固定15个阶段，每阶段最多256样本，保存全阶段count/total/max和最近窗口P50/P95。sync finally计时保持返回/异常；异步source_load_wait和source_model_wait是含等待的总历时，不能当CPU时间。细分主帧orbit/render_submit/annotations/maintain，原始页JSON/几何/加载后几何校验、上传和覆盖检查。

实际设备从当前WebGL context的debug renderer扩展读取，不能用系统适配器列表代替。EXT_disjoint_timer_query_webgl2可用时异步读取主场景GPU时间，最多8个在途query，结果尚未ready不会等待；disjoint丢弃、错误/不支持继续渲染，pagehide清理查询。它只测主场景，不包括上传/覆盖等所有GPU工作。scene draw计数可能被同帧后续诊断pass刷新，不能把它当完整帧所有GPU工作量。

右侧“性能采样（验收模式）”和可展开JSON是用户可见观察面，自动化只读该UI/console，不读取私有运行对象。QA近/中/远/道路按钮切换会重置阶段统计；原总览按钮不重置，需按具体phase判断窗口。8项新增测试覆盖关闭透明、有界统计、异常、GPU队列/分配/查询失败/清理和实际context设备；全Web441项通过。

## 实际基线

实测manifest8c05d4e52861edc153e5ea8bc86efbe4e92373a0bbfa56b5fb67afe7b65f677e，viewer f6338cdd9f6c069c90b42857e399b989a72362eaf59d3f1964954c761f384de3；独立5840文件包，只改viewer.js。未变行原行尾恢复后重建viewer逐字节同，未换包冒用GPU结果。

当前WebGL实际设备ANGLE/NVIDIA GeForce RTX5080/Direct3D11，GPU查询supported、无error/disjoint/dropped。近100米→中350米→总览三阶段。未清OS缓存，停留时长不同，不作冷启动、跨版本精确FPS基准或地景质量两轮验收。

保存的中景快照：91根、约4078644三角形；maintain613次，总122619.700ms，最大604.700ms，最近P95 351.700ms；主帧CPU总130102.800ms，约94.25%是maintain嵌套耗时（两者不能相加）。最近帧CPU P95 176.900ms、帧间隔P95 173.200ms；render_submit最大3.100ms，annotations最大1.800ms；单页上传最大11.900ms，区域coverage最大21.700ms。主场景GPU最近P95约33.319ms，测量不覆盖全部GPU工作。指向调度是这段采样的主要CPU瓶颈，不宣称所有场景/所有卡顿都同因。

代码核对发现allocationCandidates对大量候选先逐个执行canMakeFamilyRoom，内部完整预算/恢复试算，然后才排序挑选。相同相机/cut下会重复试算。这是后续按原排序惰性可行性检查及严格状态缓存的具体优化对象；实际上传前必须fresh重新验证，2倍质量迟滞、完整cut/SHA/租约/GPU预算不放松。

总览回roots0/held1024，服务owner204/exit0、reader closed、保护写0；整会话368秒含空闲，不是加载时间。证据baseline_analysis.json及每机位完整JSON/截图。原console滚动日志不当完整逐帧trace；单机位快照保留全阶段累计及最近窗口。

## 体验与Git

本机入口Application/实验入口/地景加载优化_20261020/启动Web性能采样实验.cmd，未代运行；右侧下方展开详情，必要时滚动信息栏。私有Python -I -B、随机回环、独立manual_runs、Ctrl+C/关控制台或30分钟owner/Job关闭。正式页面/公网/EXE/业务库未切换，不复制GIS和旧UserData。无数据库结构变更。

本轮5个纯源/测/handbook精确本地提交：frame_profile.js、viewer.js、prepared_source_page.js、frame_profile.test.mjs及本说明，冻结SHA；原14held保持。旧25待批载荷仍source3e8b62d→ed5fafc，不混入后续新源码，不绕过自动审批拒绝。

后续继续实际调度优化、满预算resize/覆盖桥接、冷20秒/全区长稳/Web严格两轮/原始OSGB来源深度/8K；UE、EXE、Web业务/IAM、261013、252实机和迁移完整目标active。
