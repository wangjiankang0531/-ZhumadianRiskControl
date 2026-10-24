# 原管理前端的预适配私有运行组件

当前候选每次启动都从原环境读取管理前端 tar，再调用 Node/Babel 做部署子路径适配。服务器运行不应依赖准备机的前端编译环境。本阶段把既有适配步骤前移到构建阶段：生成一个私有静态 ZIP 和可信清单，运行时仅用 Python 标准库校验并读取，再交给既有静态服务和网关。全部原管理前端资源和业务界面逻辑保留。

## 准备、校验和接线

portable_original_admin_frontend.prepare 只接受固定原归档及可信 Node、Babel parser 和自有适配脚本指纹。它复用现有 tar 内存读取器和部署 AST 配方，只改既有部署元数据，不执行原 JavaScript。先核算空间，输出须为不覆盖原输入的全新目录。1589 个原文件必须完整保留，生成 admin_static.zip 与 admin_runtime.json；不把资源展开到文件夹。ZIP 成员时间和顺序固定，清单不含本机绝对准备路径。

运行 load/verify 要求外部可信清单 SHA、固定来源、明确部署 base 和精确两文件集合。逐项检查清单重复键、路径、大小、SHA、ZIP 成员集合、特殊文件、压缩类型与总展开上限，全部校验后才返回静态文件字典。它不导入 Node/Babel 或原 tar 准备模块，不读取原归档、Reference 或实验收据，不提供登录和业务接口。

```text
python -B tools/portable_original_admin_frontend.py prepare --archive <固定原归档> --node <已验证Node> --parser <已验证Babel parser> --node-sha256 <可信SHA> --parser-sha256 <可信SHA> --recipe-sha256 <自有适配脚本SHA> --recipe <自有脚本> --output <全新私有组件目录> --base /zhumadian/admin
python -I -B tools/portable_original_admin_frontend.py verify --manifest <组件/admin_runtime.json> --manifest-sha256 <构建侧保存的可信SHA>
```

受控启动器新增 --admin-frontend-runtime 与 --admin-frontend-runtime-sha256。参数成对检查及组件完整校验发生在创建实例/持久锁/组件前；选中后使用预加载字节，跳过原 tar 读取和 Node/Babel 调用。原 ArchiveServer 与 Nginx 的静态/API 路由沿用，后台认证和数据逻辑不变。未传新参数仍保留旧启动时适配模式。

## 实际验证

原 tar 13095102 字节，原展开资源 30216262 字节。准备前记录保守最大写入预算 138 MiB 与可用空间，实际静态 ZIP 13481083 字节，部署后展开字节 30217902；只生成一份约 12.9 MiB ZIP 及小型清单，没有复制原环境目录、Node、node_modules、GIS 或数据库。

实际原包和既有 AST 适配后，1589 个文件全部逐项通过 ZIP 往返。隔离 Python -I 只带本标准库工具加载组件通过，无原归档、Node 或 parser。随后对当前 j15 管理静态入口逐个 GET，1589 个 HTTP 200 响应、共 30217902 字节全部与组件资源精确相同；请求显式使用 identity 编码，无认证或业务写入。当前启动器的已准备分支也以真实组件执行，直接使用预加载字节及来源元数据，没有进入旧准备分支。

16 项合成完整性/部署前置/实际错误 CLI 检查通过，涵盖改动内容、缺失成员、额外文件、重复键、ZIP 符号链接、展开预算、不同挂载前缀、构建工具指纹不符及创建实例前拒绝错误。另 23 项平台支持、22 项独立业务、22 项参考运行件（含 5 DTO）通过。合成测试资源不代表原项目界面；真实 1589 HTTP 字节比对单独留证。

## 运行边界与交付

j15 没有重启，仍使用其冻结控制器的旧管理前端准备方式。磁盘源码已完成新选择接线，尚未把新参数用于整套原应用启动；不能把字节一致和单分支预检当作整套服务器独立运行已验。现有 134 MiB 业务组件仍供 JVM 使用，新管理组件保留供下一套候选/实际交付复用，不为每轮测试重复生成。

独立服务器仍需平台归档/JRE/MySQL/Redis/对象存储、其余前端/地图资源、运行目录与持久化配方；原账号登录后的全模块、附件、手机真机、IIS/TLS 和公网同版仍未通过。正式 8767 与公网保持不变。fullCloneReady=false；无数据库字段、索引、状态或归属变化。

原资源包含在私有 ZIP 内，ZIP 和清单只用于授权部署，不加入 Git。Git 仅同步自有组件准备/加载器、启动器接线、合成测试和本说明，不包含原前端资源、原归档、配置、数据库、截图、凭据、私有运行收据或其他未完成修改。
