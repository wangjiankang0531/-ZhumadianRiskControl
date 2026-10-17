# 驻马店高新开发区重大风险防控

Windows 场景标注编辑器与浏览器三维查看器，依赖信能本源 XNBYEngine。
当前可体验版本：EXE 0.9.6、网页 0.8.0，业务 API 0.3。
应用最新需求基线为完整工作目录 Document/Require/需求说明书261013.docx；研发顺序及条款追溯见 Document/Design/驻马店新版需求理解与研发调整261013.md。真实业务系统、登录权限、公网上线与长期 UE 对标仍在推进。

## 两个源码仓库的目录

仓库名称带有前导横线，检出时请明确指定本地目录名，使应用 CMake 能找到同级引擎：

```text
git clone https://github.com/wangjiankang0531/-XNBYEngine.git XNBYEngine
git clone https://github.com/wangjiankang0531/-ZhumadianRiskControl.git Application
```

完整工作目录布局：XNBYEngine、Application、Assets、Document、Backup 为同级目录。
本仓库包含 native/、web/、services/、shared/、tools/ 与可再生配置；GIS、三维模型、用户 DLG、台账、运行时和文档不上传 Git。
源码检出后需要另外准备实际 Assets 和运行时，不能直接把源码仓库视为可运行发布包。

## 本地体验与构建

已有完整本地项目时，从根目录或 Application 双击 run_editor.cmd / run_web.cmd。
EXE 标注保存到 ../Assets/DLG。网页本地地址 http://127.0.0.1:8767/，三维区域配图层菜单和信息面板。

native/ 是 EXE 源码，web/ 是 WebGL2 源码，tools/ 包含数据服务、转换及验证工具。
用 CMake 配置 Application 并构建 xnby_zmd_editor；当前 Windows 构建需要 MSVC、Windows SDK、Vulkan 与引擎 vcpkg 清单中的依赖。
本机 build_local.cmd 用现有机器依赖路径，不入 Git；其它机器需要按实际依赖位置配置 CMake。

网页从 web/ 执行 npm ci、npm test、npm run build，依赖由 package-lock.json 固定。
构建输出 web/dist。运行只读服务 tools/landscape_web_server.py 时需要完整地景、派生模型与转换运行时。

## 已实现的交互

EXE 按显示器工作区与 DPI 最大化启动；顶部按钮/F9 显隐面板，支持左右停靠、拖动头部到边缘吸附、滚动和视口缩放。
点图标、线型/宽度/颜色/透明度、封闭区域与填充、文字标牌和分组图层可编辑并保存。
0.9.2 支持空间标注的对象类别、业务编号、所属企业编号和来源系统登记；应用/解除支持撤销重做，锁定及非法输入受保护。

网页支持图层开关、整层定位、画面点线面选择、搜索/类型筛选及窄屏详情抽屉。
0.6增加园区画像、监测预警、封闭管理、敏捷应急、能源五张图入口，按空间目录或已有业务引用分类；支持22类空间对象及多专题归属。xnby.spatial.catalog.v1以空间编号和图层指纹防止错配，固定只读发布路径为Assets/Spatial/spatial_catalog.json。
页面计数来自实际加载的空间对象，非业务统计。API 0.2 与网页 0.7 已完成签名访问令牌、服务端企业权限、OAuth2/PKCE 登录适配和受控数据读取的独立验收；真实身份/业务系统和正式云渲染仍待接入。
0.5 支持各图层、倾斜摄影和卫片底景的浏览透明度（0% 不透明，100% 完全透明）；文字、轮廓、填充和选中反馈同步淡化，完全透明的图层不拦截场景拾取。
浏览透明度与编辑端保存的不透明度相乘，只影响当前浏览；恢复按钮回到原始样式，成功读取另一图层文件重置图层浏览设置。
启动自动读取、手动打开和并发读取按最新选择生效，旧读取完成不会覆盖新选择；错误图层保留当前文件及浏览设置。
0.4 可导入 xnby.business.records.v1 JSON 台账快照，按来源系统/类别/编号对应记录，查询属性、时间与数据状态。
缺失、企业冲突、过时、未来时间与重复记录有明确处理；导入失败保留之前台账，清除台账保留空间关联。
文件台账标识为非实时数据；格式及发布约定放在完整工作目录的 ../Document/Design。
正式业务台账尚未收到，独立验收文件不能作为真实监管数据。

## 验证与边界

EXE 自身 --editor-shell-probe 验证八个真实窗口/Vulkan 状态；--editor-business-probe 验证关联编辑、撤销、保护与保存重开。
工具入口：tools/verify_editor_shell.py、tools/verify_business_references.py，使用独立测试图层副本。
网页 120 项单元测试、63 项 API/网关/合成 OAuth HTTP 测试及既有六项只读文件路由测试和浏览器导入/选择/错误状态验证通过。
证据分别位于 ../Document/Deployment/editor_shell_20261012、business_binding_20261013、business_records_20261013、web_opacity_20261013、portal_20261013。
鼠标外部输入自动化受 Windows 限制，拖动手感与跨物理显示器 DPI 仍需人工体验。
本地 HTTP 服务不是正式上线部署；部署需要 HTTPS、鉴权、数据权限和真实接口验收。

## R1 API 0.2 / 网页 0.7 阶段入口

services/ 提供标准空间对象与业务查询 API；配置、身份与企业权限协议见 services/README.md。shared/spatial_types.json 是网页/API 共用类别与专题定义。
双击 verify_business_api.cmd 查看临时 QA 数据的实际 HTTP 企业隔离验收；run_business_api.cmd 需要另行提供 Assets/Configuration/api.json、可信公钥及主体授权。
双击 run_api_web_qa.cmd 在 8790 体验合成 A/B/公共账号权限、图层显隐和到期清空；认证适配与配置见 services/PORTAL.md。该页面没有生产身份鉴别能力，不采集密码，不能公开作为正式登录。run_web.cmd 的 8767 保留原有本地图层入口。真实统一身份暂未提供，按用户要求先完成接口与独立验收；正式 HTTPS、真实数据接口以及需求的全量性能/长稳验收继续推进。

## 2026-10-14 航拍清晰度修复

0.9.3 / 网页0.7.1修复原纹理被压缩尺寸、中心升级等待及包围盒抢占。保留原始纹理像素，以纹理/几何屏幕质量和真实源表面确定中心目标，优先完整细化。总细层512MiB、单批32MiB。实际EXE和网页达到中心第五层，网页滚轮推进、八状态窗口及125网页/7纹理源审计/12HTTP/4实际C++决策验证通过。证据完整工作目录Document/Deployment/lod_quality_20261014。

整根前沿的第六层及部分周边仍受预算限制，下一步完善局部源子节点/兄弟族事务及纹理分页。此次增量不能替代全视野最高精度、正式性能或UE总体效果验收。


2026-10-14 局部源节点族加载准备：新增真实OSGB完整兄弟族转换、每节点精确索引/实际包围盒、只读HTTP加载与独立验收工具 verify_local_lod_family.cmd。真实Tile141第五层28节点到局部第六层31节点的完整cut、文件哈希及并发预算通过验证。引擎加入全部上传就绪后提交、取消及陈旧回调保护。局部族还未接入EXE/网页显示和拾取，默认视觉体验仍为EXE0.9.3/网页0.7.1。下一步先完成两端资源共享、绘制和拾取使用同一可见cut，再进行极近景/周边/冷转换验收。说明：../Document/Deployment/lod_family_20261014/阶段说明与独立验收.md。


2026-10-15 局部LOD实际接入完成：EXE0.9.4/网页0.7.2逐完整源节点族细化，精确屏蔽父索引并使用同一可见cut拾取，退远回退/取消。真实第七层、同相机整根第五层对照、八站往返和八状态窗口、134网页/63接口/19数据回归通过。体验与限制见../Document/Deployment/lod_family_runtime_20261014/体验与验收.md。周边视野调度、缓存/冷加载/正式性能继续优化。


## 2026-10-15 网页 0.8 / API 0.3

三维采用驻马店本地资源、中间地景与两侧水晶仪表面板；MIS统一深蓝导航、浅色工作区、卡片/表格/表单。8767/portal.html#workbench为业务工作台。用户原始DLG保持不变，图层数据库位于Assets/BusinessData/xnby_business.sqlite；网页读取时把EXE保存的完整JSON导入SQLite并保留版本与点线面索引。目前为单向编辑端发布桥接，尚无多编辑端数据库合并写入。

运行根目录“体验重点问题闭环.cmd”或Application/run_focus_qa.cmd，在8790/portal.html#hidden-danger体验模拟A/B企业。种子10条重点问题，用户体验新增修改保存在Application/work/focus_qa/focus.sqlite；账号不采集密码，限本机合成验收。支持重点登记、六项企业反馈、园区跟踪、复查、归档及重新关注；企业反馈不等于园区复查通过。普通企业一般隐患台账和复杂审批不由此模块接管。

数据库结构v2共7表，概念/物理模型及维护说明在完整工作目录Document/Database。tools/generate_database_docs.py --publish-source生成真实SQLite结构、目标MySQL DDL和指纹；services.database_transfer提供一致备份、恢复及MySQL数据脚本。MySQL运行时驱动和真实导入、Linux/Apache实际部署尚待实施。当前HTTP由Python标准库提供，非IIS。deploy/apache-zhumadian.conf.example为HTTPS反向代理模板，不能直接视为上线配置。

本阶段验证：153网页测试，89真实HTTP/SQLite/权限/恢复测试，8文件发布HTTP，20缓存检查分别在源码和体验包便携运行时通过；浏览器实际1280×720验证默认端口三维中心7层、原2标注及模拟登记到归档。移动尺寸尚未实际验收。证据位于Document/Deployment/focus_database_crystal_20261015。EXE0.9.6未重新编译，原始DLG字节保持。
