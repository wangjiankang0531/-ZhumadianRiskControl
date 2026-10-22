# 风险分析单元：原Excel功能链实现与验收（W68）

日期：2026-10-22。完整天津原站界面/功能复刻、驻马店EXE/三维/UE效率目标继续active，本阶段仅证明风险单元Excel子链，不是全模块或全项目完成。

## 原资料依据与实现

已读 RiskLevelController、RiskLevel、RiskLevelService/Impl及ExcelUtil：首个sheet、六列为部门名称/负责人/分析对象/分析单元/风险等级/坐标，模板sheet名称为sheet。原ExcelUtil每3000条saveBatch，原导出fastWrite建议10000条内；候选保留首sheet、六字段和导入新增语义，并增加目录校验、原子事务、行号错误、审计和重复请求控制。未把CSV当Excel实现，未调用原天津服务或写原站数据。

原 ImportExcel 专用对话框和三个按钮仍使用；API接真实multipart与xlsx字节。支持真实xls、xlsx，表头按名称映射（允许调序），空行跳过。风险等级可用合法编码或唯一名称；负责人须启用且属于对应部门，名字重复不猜测。Excel保存公式仅读缓存值、不重算，缺少缓存或无效值报错。导出把数据写成文本单元格以保留字面值，输出合法xlsx，不生成HTML伪Excel。

一次导入先预校验全部行，再用同一BEGIN IMMEDIATE事务写每条快照、create审计、回执和pending包；任意行失败整批回滚。请求键绑定完整文件SHA/全部行摘要，不能在重试时改变最后一行或数量。审计可选importBatch保存批次id、sourceSHA256、rowNumber、rowCount、batchDigest；不存原文件字节，不声称已完成原件归档。原四表DDL/schema1保持，正式schema4、workflow2及风险SQLite DDL五项生成物SHA不变。

Excel只有原六列，不含记录ID、revision或坐标系；导入总是新记录，坐标系明确待核实，不能当作数据库恢复或在地图正式定位的证明。正式备份保存四表全部字段、历史和关系。

## 实际验收

- 54项风险领域/真实Excel/HTTP测试通过，覆盖xls/xlsx、表头/调序/空行、缓存值、重复批次、改变尾行/数量、逐行报错、整批回滚、当前范围/权限、模板与筛选全部导出、格式/容量边界及在线备份恢复。此前39项R2回归为W67历史，本阶段不冒称重新运行。
- 全部原动态组件重新构建通过，5005模块；最终41.21秒是编译时间，不是页面加载性能。全新配方生成1243候选源码SHA逐项一致。53原直接依赖+原冻结npm锁继续使用；Excel运行4轮包及测试xlwt单独固定哈希，安装只进私有候选目录，无全局pip更新。
- 浏览器通过原上传控件实际导入xlsx两行、xls一行，连同W67复制来的1条合成数据，当前4记录。审计/回执/outbox各6条（原记录3版本+新3条）。错误负责人文件未写入任何一行；改进后的原对话框持续显示“第3行：部门责任人名称无法唯一确定，请重新选择”，可修正后重传。
- 通过原按钮实际下载到浏览器文件目录的三个xlsx均重新打开核对：空模板0行、筛选3行、全部4行，sheet及六列表头/字段值一致；路径、SHA、字节保存在browser_downloads.json。独立活动HTTP服务也验证同三种输出、Content-Type/Disposition/Length。不是只验证按钮点击或仅在API脚本保存文件。
- 实际浏览器导入后的online backup复制到新库，四表逐行内容、导入元数据、逻辑删除回归、integrity/FK通过。旧候选、业务库、地景和图层没有被升级或覆盖。
- 浏览器保留3条预期无效文件对应的错误日志，Element Upload源码handleError明确console.error(err)；不把它们抹除或声称console0。当前证据不能据此宣称所有JS/网络负载场景已无错误。

## 运行、限制与后续

本机入口 http://localhost:60799/safety/hiddenInvestigate/riskAnalysisUnit ，IAB13已登录并保留。当前进程、创建时间与3600秒上限见runtime_receipt.json；约一小时后自动停。新候选用localhost隔离旧127测试Cookie，只绑定127.0.0.1；独立数据库在Application/work/replica_excel_20261022。两个早期限时候选已用同句柄确认exit0后才重建。期间第一次浏览器download事件等待异常挂起并超时重置；故障原样记录browser_wait_incident.json，后改为显式超时的异步检查后已取得实际保存文件，不将最初失败记作成功。后续禁止无界await下载事件。

单文件小于100MiB、单次最多10000数据行/64列，xlsx展开总量256MiB/单项64MiB；同时最多1个解析任务，超额429。这些是已实现的候选边界，100MiB吞吐、极端文件负载和IIS上传配置尚未实机验收。MySQL/Linux/Apache及正式身份、组织管理、上级网络投递仍未完成；pending不是送达。不得拿本机小文件通过声称公网100MiB已验收。

地图选点/完整新增链仍未通过。原Map组件仍有天津中心和瓦片路径，下一阶段必须接驻马店真实底图/坐标映射，不能把旧中心下选出的经纬度当驻马店定位验收。其它检查内容/清单/计划任务/隐患、巡检、八类票及审批、应急、监测、大屏和完整手机端仍按630行矩阵推进。新矩阵仅4条标部分验证、0条完整通过；W66原始矩阵保留。

本轮未切公网入口、未启动原生/ETW、未改安全设置；14held SHA全同。引擎远端8966e32b与本地b89578af仍同树e02070b58d27067f82742bbb1de98f573ebaaf06，没有新内容需要merge。上轮授权14文件已push并核验main=d6ce00bd；本轮Excel新源码另批，不混入该授权镜像，后续Git结果另看本E回执。

## 运维与资料

配方tools/prepare_replica_excel_components.py在全新目录调用原组件基线配方并适配Excel；引用本地Reference，不把原参考源码推送。依赖用deploy/reference_components/excel_requirements.txt的require-hashes锁安装到私有目录，xls测试生成器锁另列excel_test_requirements.txt。构建仍有旧库弃用和大块JS提示，不称性能优化完成。

设计、实现、验收及运维证据位于Document/Deployment/replica_excel_20261022：verification、live_acceptance、browser_downloads、54测试日志、构建日志、数据库生成回执、PNG、空模板及两份实际导出。数据库配套见Document/Database/风险分析单元库概念模型、物理模型、维护说明。候选原数据和配置禁止放静态根或上传Git。

解析依据：[openpyxl官方读取接口](https://openpyxl.readthedocs.io/en/3.1/api/openpyxl.reader.excel.html)、[xlrd官方接口](https://xlrd.readthedocs.io/en/latest/api.html)。所用版本以本地固定哈希依赖锁为准，不以搜索结果代替运行验收。
