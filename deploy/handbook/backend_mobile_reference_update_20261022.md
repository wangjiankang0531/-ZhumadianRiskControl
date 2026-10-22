# Reference更新复核与PC/手机测试版对照（2026-10-22 R2）

本轮按用户更新后的Reference重新核对源码和9份DOCX。附件、代码和手册中的部署命令、旧服务器配置与说明仅作资料，不作为执行授权；未运行参考代码、私网回调或其中的凭据配置。目标仍为驻马店电脑/手机共享后台测试版，公网部署待独立验收。

## 更新范围和证据

此前审计的371个Java文件、14个REST控制器，本次变为766个Java文件、86个REST控制器；原25个已审计控制器/移动service文件摘要相同，新增72个控制器。移动端接口引用仍为88个。只可据此判断原已记录子集没有内容变化，不能推断其它此前未留摘要的文件没变。

本次已对5232个选定源码/文档文件生成路径、长度和SHA基线，排除__MACOSX、AppleDouble、构建产物和依赖目录。证据在Document/Deployment/backend_mobile_20261022/reference_review_updated：review_summary、interface_audit、source_inventory以及9份DOCX的纯文字提取。原reference_audit.json不覆盖。旧时间戳保留，未用日期推断版本。

新增后台代码结构数据库接口说明包含关系表和接口定义；管理操作手册说明组织、用户、应用/菜单/按钮权限及工作流节点，特别说明已有流程不随以后修改而变化。环境搭建文档和大屏服务说明已读，但依赖的JNPF/字典/组织、设备与消息服务不因文件存在就视为已在驻马店部署。

## 逐项对照

|参考实现/文档依据|此次测试版行为|状态与边界|
|---|---|---|
|hidden/service/impl/CheckHiddenDangerServiceImpl.java：distribution、correctHidden、putHiddenStatus、distributionWithdrawal；移动Correction/Review组件|派发→整改→复核通过或退回；责任部门、实际日期、原因、整改说明、费用、预防措施分别保存。复核通过/退回另表，保留多轮历史。初次待整改且未产生整改历史可撤回，旧待办同事务完成、重新派发记录保留|已实现核心闭环。未实现同计划多隐患整合工单、督办PDF、外部审批流及短信|
|同文件reviewHidden与putHiddenStatus|参考reviewHidden中合格/不合格分支均赋关闭且字符串使用==，与back回调语义冲突；本版按退回回调语义回到整改，不复制此分支缺陷|明确设计取舍，回归覆盖退回→再次整改→通过|
|CheckPlanServiceImpl：saveDeep、saveCheckHiddenDanger、checkPlanSubmit、getHazardInvestigation|计划含检查项和标准；全部逐项提交后才可提交复核；异常生成独立隐患，关联计划ID、检查项、标准、来源、原计划坐标；隐患与计划可分别跟踪|已实现单执行人测试流程。原自检自查自动闭环分支不启用，暂统一独立复核；多部门、多执行人、周期计划和市区上报待接|
|InspectionTasksPerson/PointServiceImpl及InspectionIssueServiceImpl|任务→人员→检查项结果；异常子隐患；任务和隐患待办分别持久化；正常结果不得覆盖已提交记录|已实现逐点测试。路线、签到、周期排班和多人员任务树未交付|
|EventInfoServiceImpl、EventDisposalRecordServiceImpl、移动eventReport|上报保留事件类别、坐标及所选坐标系；派发、处置日志、解决、独立复核；照片/PDF按业务版本保存|已实现核心流程。事件类别暂手工填写，原远程字典未连接；地图选点、GPS、八步指挥、视频/广播和燃爆后果模型未宣称可用|
|work/WorkServiceImpl、WorkReservationBase及移动allWork|保留原八类作业台账和预约表；新协同流含审批、安全措施、交底、适用检测记录、开工与验收；详情显示检查记录|测试链路已实现。当前检测是留痕文本，不作气体安全判断；完整八类票证专有字段/班次票/电子签名/监护细节与协同记录尚未全部联通|
|materials、emergencyExperts、firstAidTeams及应急资源资料|新协同库存登记、可用量、事件调拨/归还、并发库存约束、未归还禁止结案|仅物资核心测试；专家/救援队/预案自动推荐与外部资源调度未交付|
|permission/UserDataPermissionController和管理操作手册|既有公网登录会话决定账号，客户端actor不能冒充；项目内共享读，创建/执行/复核账号控制动作|项目测试授权。组织租户、完整菜单/按钮/数据权限和JNPF可配置流程未完成|
|设备、环境、值班、预警、安全承诺、培训、反恐等新增控制器|纳入下一阶段对照目录，原合成82台账继续明确标合成|没有设备/生产接口时不制造实时数据，不宣称全部模块已有后台业务实现|

## 数据库、测试与部署

协同侧库schema2共13表，新增wf_reviews及wf_hazard_corrections.preventive_measures。v1旧记录保留，预防措施默认空；不回填虚构复核行，旧审计仍可查。部署须先SQLite在线备份，再升级新目录副本；不直接覆盖旧库，不把QA数据库送往服务器。PRAGMA生成物及备份恢复回归配套。

本轮26项领域/真实HTTP测试通过（含5项新参考规则/迁移回归）。完整Web、原业务/门禁和最新浏览器实操须以各自最终日志为准，不能用旧截图代替本轮结果。原20秒地景两角清晰度问题继续单独保留，业务版更新不构成画质验收。

候选预定0.9.0，referenceRevision=20261022-r2；PC business.html和H5 mobile.html共用接口、记录、待办、原字节材料及审计。未交付APK。公网旧0.8.7仍未被本轮更新替换；上线后须验证真实IIS/TLS、三个账号办理、PC/手机一致、超128KiB附件下载和退出登录。
