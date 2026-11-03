# 原平台审批前加签独立意见维护边界（2026-11-03）

原flow_task_operator_record的DDL/索引/实体/Mapper及状态枚举保持；10是原审批前加签状态，不新增表、字段、索引或状态码。原模型源deploy/database/original_platform_http_fixture_models.json与实际398表前后快照为物理模型依据。本轮无产品DDL，不运行SQLite生成器改写原平台模型。

独立意见只在原freeApprover、原DSTransactional和原Mapper同连接内复制。保留原task/actor/opinion/节点名称和Java Date经原JDBC转换后的handleTime/creatorTime，工作项引用置空以排除活动待办唯一查询；原时间缺失则整体回滚。没有新数据源/连接池或账号角色变更，开关/初始化器只在启动内存注入。

真实Mapper十项（含8小时SQL时区差异、SIMPLE/BATCH、真实SQL故障与缺时间拒绝）与2次正常SQL停启通过；真实原服务独立模块的后加签7阶段、前加签8阶段通过。仅对一个精确自有合成流程临时注入SQL故障，八表指纹完全不变，UI输入保留，移除精确触发器后一次成功重试及后续审批通过。触发器已清，是测试范围，非产品DDL。两次正常重启只回看同一已完成实例，意见/时间/附件保持；原398模型不变，六组件正常退出/实际后代零后恢复临时文件。

公网R35只修个人流程路由，后端候选R36尚未部署。修正保证以后加签独立留痕，既有已覆盖意见不编造或批量回填。真实南港全部模板/并行权限/通知及整模块验收仍待，fullCloneReady=false。
