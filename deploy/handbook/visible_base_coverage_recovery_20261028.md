# 可见缺区完整根恢复实验

本阶段为显式 QA coverageRecovery=1 实验，默认关闭，未部署公网或替换8767。fullCloneReady=false，整体目标继续进行。新增的是“补回当前可见、尚未加载的完整根区块”策略。它与普通细节请求有明确区别：普通细化保留损失两倍小于收益门槛；覆盖恢复允许按估计损失/释放字节贪心选择完整父页退粗，以覆盖优先。不是全部质量门槛保持不变，不能据覆盖补齐宣称整体画质不降。

请求必须具有真实正收益、当前相机及切面匹配、(0,1]可见基础权重、已验证完整源能力，root 1..2346且未常驻、parent为空。覆盖路径禁止rootPriority和整根驱逐；保持全部已有根。每次恢复共存峰值与最终incoming及余量都需满足既有2GiB源资源预算、页完整性、源SHA及原子切换。相机/epoch/展示方式变化取消；失败保留最后完整中间切面，不重试原生读取器。profile记录覆盖plans/steps/peak/last；startup witness尚无此新统计。
同 CSS1920×776、350米机位，关闭组稳定返回173根、基础粗层1193像素、左右上角610/271；其近景快照并非充分稳定证据，不能冒称严格相同近景终态A/B。启用组初始184根，两次新鲜快照切面/held一致。恢复前台后帧间隔中位13.3ms；恢复的新标签默认1920×720状态另存、不混入对照，临时视口调整回1920×776后重新加载。

本次近景仍在细化时返回中景（23根/pending family），测试的是进行中取消与返回恢复，不是近景完成后的严格往返。返回稳定184根，基础0像素，角[0, 0]，覆盖恢复9个计划/9步；连续两份fresh报告pending空、扫描完成且candidate空、切面/held相同。与首次根ID集合相同=True，完整切面相同=False，held相同=False。returned held=2118129525B，峰2130048885B < 2147483648B；这是源资源账，不是总显存。全幅代理超阈823863仍不能当整体画质通过；独立来源ID诊断原样见phase-result，误差不忽略。

11项新增策略测试；本地/独立闭包/干净审查树各898项Web全过。审查树88项读取器及13项图层/纹理发布Python检查通过；均纯Python/合成夹具，不运行被隔离EXE。首次审查导出曾因Git中文路径引用失败，改用ls-tree -z保留失败记录后完成。没有原生重试、360放行、GIS拷贝或业务库改动。

首次全幅代理超阈676694、独立来源ID差34；本次返回代理691390、来源ID差37，局部细节退让与未通过的独立校验明确保留，不以补覆盖冒称全面清晰。20秒全幅清晰、近景完全稳定后的重复往返、全园区质量、屋面细节及独立来源ID仍需验收，未宣布彻底解决。旧实验标签被关闭使原GPU状态丢失，原观察保留，未用服务重启掩盖；本轮始终原PID42156/51061。
候选Application/Packages/candidates/WebCoverageRecovery_20261028_Experimental，37文件/1727501B，只读引用已有GIS、0.9.7、索引、纹理与图层，不复制地景。状态Application/UserData/WebCoverageRecovery_20261028/web-service.json；端口/PID以该自有状态为准，控制密钥不归档。当前51061/PID42156。回退可用仍运行的57021父候选，不重启18891/8767/公网R5或252。

体验入口：http://127.0.0.1:51061/?qa=1&levelIndex=1&regionResidual=1&coverageSeed=strict&visibilityGrid=160&recoveryHeadroom=adaptive&completion=coverage&coverageRecovery=1&topic=emergency&inspect=-317,-1988,43&height=350 。普通用户入口无该参数，默认策略不变。验收加profile=1&profileMode=manual&denseAudit=manual&denseReference=1，诊断只在稳定后手动执行；不能将诊断耗时混入20秒加载。先查看性能明细，再刷新并读取新generation，pending空仍须扫描done/candidate空及第二份切面/held一致。

仅自有临时执行目录和命名脚本可在逐文件SHA归档验证后清理，保留活动候选、状态和共享资源。正式HEAD/index、27受保护文件、5194源/索引/图层校验均保持。Git只准备精确自有源码/测试/handbook镜像，以aee1fdd9为父，不向main写入，不包含Reference、资源、库、运行包、凭据或旧held修改。新载荷外发状态单独记录，不把本地检查点称已推送。
