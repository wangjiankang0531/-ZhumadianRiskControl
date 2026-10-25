> 当前版本说明（2026-10-25）：当前设计已更新为[2026-10-25 R4测试版设计说明](current_test_release_design_20261025.md)。公网已切换到原系统独立后台，双机三维入口已实际验证；完整业务对版仍待验收。以下保留既往实现边界和实验记录，不将早期模拟后台或未发布候选当当前版本。

# 驻马店本地三维、图层发布与预案附件实现说明

更新：2026-10-20T13:46:19.253776+08:00。本说明对应阶段代码与验收边界，配合数据库自动生成模型使用。

## 模块职责

- tools/portable_web_entry.py：使用包内Python，先核对包与绑定，再启动自己的loopback8767服务；不接管已有端口，无自动重启。
- tools/portable_source_runtime.py：只读原始地景接口、Windows Job归属、运行身份就绪、已有LayerRepository图层发布衔接。原数据转换关闭，保护写入计数需实际核对。
- native项目保存流程：另存为保存独立用户副本，新建在UserData/Projects独占目录创建默认层，发布为按SHA命名的不可变快照与原子current指针。网页和SQLite读取同一原字节。
- services/reference_plan_materials.py：独立模拟预案附件的载荷、版本引用和评审引用；services/reference_plans.py负责版本、评审和发布事务。
- web/src/reference-plan-materials.js与reference-plan-form.js：草稿上传/解除关联、历史与评审附件下载；不提供内嵌文件执行。
- tools/serve_reference_public.py继承同一业务处理器，在读取前要求登录，在写入前要求同源与既有token；本轮新增专门公网附件回归验证未登录/错误源/缺token/退出失效。

## 数据边界与状态

正式问题/DLG/气体业务schema v4、14表保持。模拟业务schema v3、9表，附件新增demo_plan_materials、demo_plan_version_materials、demo_plan_review_materials三张关系表。详情含材料元数据，载荷以原始BLOB存储；当前版本与评审分别引用同一不可变载荷。

草稿可上传/移除关联；发布后不能修改附件。修订创建新版本并复制引用；新版本发布前旧版本仍有效，发布后旧版转历史。每次写入以记录revision CAS和BEGIN IMMEDIATE提交，材料及审计同事务。评审快照保留form+materials规范字节和SHA；旧v2评审字节保持，不重算旧摘要。

单份2MiB、版本8份、每预案含历史32份/32MiB。解除关联只删草稿关系，原载荷与既有评审引用保留，容量仍计入历史。下载必须属于指定预案/版本或评审，重新验证字节数及SHA；无关联404、完整性失败503，响应强制attachment/octet-stream、nosniff/no-store。

## 迁移与验证

v0/v1/v2模拟库在新副本中增量到v3，旧记录和评审原文保留。模型由tools/generate_reference_demo_docs.py读取实际SQLite产生；本轮两次生成逐文件一致，并修正MySQL脚本头部版本号为v3。正式模型另由tools/generate_database_docs.py生成，正式发布源manifest和v4 SQL字节保持。

真实上传PDF的在线备份中完成V1评审发布、V2移除引用并发布；旧版和旧评审仍下载原610字节PDF，V2请求返回404。恢复九表逐行同、全部BLOB摘要同、外键0。候选包私有Python复核恢复记录revision10/有效V2和旧附件，包内摘要未变。MySQL/Apache仅有适配准备和DDL，未做环境实机验收。

## 本轮实际结果与未完成项

54后端/接口检查、391网页检查通过；本机真实新建/保存/另存为/重开与快照/HTTP/SQLite一致通过；252两个公网本地入口画面通过。252完整包身份/Data绑定、全区长稳、点线面全部样式的手动覆盖仍待。0.8.10候选没有因本轮代码同步而自动部署公网。
