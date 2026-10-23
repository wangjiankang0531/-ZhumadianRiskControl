# 天津南港原项目严格复刻：构建与采集运行说明

用户2026-10-23最新要求：第一阶段前端、后台和测试数据严格仿制天津南港原项目，达成后通知整体复核。先保留原标识、原页面、菜单、模块操作及业务处理；驻马店定制在原版复核后继续。本说明记录构建准备，不声明第一阶段已完成。

## 原工程与完整性

Reference中的安全管控PC、应急管理PC、原移动端、原大屏、cloud-endanger Java、大屏Java六套工程完整复制到Application/work/tianjin_native_20261023。共7566个原文件；业务源码、配置、静态图和移动二维码均保留。仅排除node_modules、dist、target、版本控制目录和Apple元数据目录等非源码构建目录。原安全首页第三卡是“浏览器扫码”，当前公网自行改造的园区三维卡不符合本阶段基线。

使用tools/prepare_tianjin_original_sources.py准备新的独立副本，或只读核对现有副本：

```powershell
python -B -X utf8 tools/prepare_tianjin_original_sources.py --reference D:/Project/Zhumadian/Reference --output D:/Project/Zhumadian/Application/work/tianjin_native_20261023 --manifest D:/Project/Zhumadian/Document/Deployment/tianjin_native_replica_20261023/native_source_verification.json --verify-only
```

清单必须使用新文件名；复制模式要求全新输出，拒绝覆盖、路径重叠或原始文件差异。工具仅复制/校验，不执行参考资料中的命令、包脚本、不启动服务、不访问数据库。原Source、测试数据、会话、运行包或凭据不因该工具自动上传Git。

## 已验证的原构建

安全PC原vite.config.ts完整构建成功，835产物；应急PC原vite.config.ts完整构建成功，204产物。两者使用独立native-build-phase1目录及source-check模式，业务源码未改。应急FullCalendar5包锁定6.1.17、moment2.30.1，均来自原pnpm锁文件，额外依赖安装在独立目录，不修改既有缓存。

原移动端使用pnpm9.15.9读取原lockfile9，frozen-lockfile、ignore-scripts。原package含Darwin平台二进制，使用force保留其原声明；没有删除依赖或改写package/锁文件。忽略安装脚本以避免原prepare中的git init/husky副作用。完整依赖安装成功，随后在另一份构建副本按原uni build命令生产编译H5，191产物，15.703秒成功；原301输入和构建副本输入均未变化，保留原首页与全部原路由，未换成联调导航。原图标/字体/接口仍按原实现；尚未运行真实页面与后台对照。

原业务Jar768个应用类的major为61。Java17从[微软官方OpenJDK下载页](https://learn.microsoft.com/en-us/java/openjdk/download)所列Windows ZIP取得，官方SHA-256为3d9006956fc8af5601cd24ffc4f468bef48279c7ebd8171b9bdf90d0aabfbf1f。整包响应长期未落盘后，验证官方CDN的HEAD200/Range206，主动停掉仅本轮自有下载，保留partial；改用有界分段组装，再核官方SHA才解压、验证版本。没有改系统PATH、注册表或运行后台。

原Java766源码使用原运行包自带220依赖，显式JAR类路径编译成功，生成768个Java17类，7.422秒。第一次通配类路径参数未使依赖生效，其失败日志和回执保留；仅修正编译命令，未修业务源码。此为完整源码编译检查，尚非Maven完整打包、后台启动、数据库接通或业务/权限验收。

构建、依赖与摘要回执在Document/Deployment/tianjin_native_replica_20261023。全局浏览器库过旧、SCSS弃用、较大chunk等原工具警告保留；不以修改业务源码或升级依赖来掩盖差异。原大屏Vue2已独立按原package-lock v1完成1392包安装，ignore-scripts，141.969秒；原package/锁文件和全部766输入未变化。原vue.config.js生产构建成功，13.672秒、376产物；仅本次构建进程设置NODE_OPTIONS=--openssl-legacy-provider供原webpack4使用，不改系统设置或业务逻辑。至此四套原前端均构建通过；大屏Java是独立SpringBoot2/Java8工程，仍需按原依赖准备，不能混用Vue3环境或业务Java17后台替代。

## 原测试数据采集与对照

用户指定并授权：通过已启动的UU远程遍历原天津网页自行采集。不得再次要求用户找SQL备份替代这一方式。按实际账号可见菜单建立目录，逐页保存列表全部分页、筛选总数、详情子表、字段/状态、真实上下游ID关系、可见附件和历史，记录URL、角色、时间、范围及完整性。保持原站只读；新增、修改、删除、审批和其它写操作在私有复刻环境验证。采集数据不进Git或公共静态目录，凭据/会话不写明文文档。

original_contract_inventory.json记录原前端源码组件和84个业务Controller中的763个注解映射候选，以及移交Word1438个表格；它们只是待核对来源，不是现场菜单或完整接口验证。必须用UU实际遍历校准，不能把组件数当菜单数或完整验收率，不能把文档表格默认为全部DDL。

当前Windows工具在创建kernel assets阶段报系统找不到指定路径，重置后仍失败；UU已启动不等于工具已能操作，实际采集尚未开始。已请用户重开Codex恢复操作工具，保持UU及原站登录。遵循Computer Use支持的node_repl/@oai/sky窗口接口，不自造协议或用Shell/UIA绕过。

## 启动与部署门槛

启动原Java前，须根据移交资料和原站采集恢复本机私有MySQL/Redis/Nacos/JNPF等实际依赖，配置明确指向本机测试资源。不得直接运行带原环境配置的Jar，避免原定时任务或回调写入原业务环境；不以简化接口/伪造成功替代缺失配套。原运行包和Mapper资源不覆盖，当前既有服务/数据库/GIS/用户DLG不改。

第一阶段必须完成四套原前端、原后台及依赖、原数据导入、真实菜单与模块内操作、图片/附件/Excel/文书、身份与流程、相同视口视觉和跨端数据对照，并部署用户可访问的整体候选，再通知用户复核。当前公网未更新，本地构建成功不构成对版完成。

本轮自建巡检实验已按用户纠正封存，不能恢复为本阶段后台路线。六份连续性文件、原版设计基线和采集/验收清单持续更新。长期UE引擎、驻马店EXE标注图层、网页地景质量及迁移归档目标仍保留，旧cwd仍在使用，不得删除。

## 原Java后台离线重建（原业务不改）

tools/rebuild_tianjin_original_business_jar.py从显式SHA锁定的原cloud-endanger运行包取得220个原依赖，使用显式Java17 JDK重编译766个原Java源码，生成与原包类名集合一致的768个类，再将应用类放回保留原Boot加载器、原依赖和97个资源文件的候选Jar。97个原源码资源（包括bootstrap与Mapper）与原运行包均逐字节一致；任何资源集合/字节差异、签名、重复条目、不压缩嵌套库不满足要求时停止，不能忽略差异冒充原基线构建。输出必须为全新且与原源码树分离的目录，失败输出和日志保留。

此为使用原运行包依赖的离线重建，不是Maven完整打包或在线业务验收。原Jar以及Reference不修改；候选Jar含原环境配置，仅留本地私有工作目录，不进Git或公网静态目录。后续业务启动必须先将依赖与配置隔离到本机测试资源。

```powershell
python -B -X utf8 tools/rebuild_tianjin_original_business_jar.py --source <原源码副本> --runtime-jar <移交原Jar> --runtime-sha256 b48adb8d966fa55656757d182cdd6b64c409d151c3e30ee3cbc5ef0cb86e68d8 --java-home <独立JDK17目录> --output <全新D盘构建目录>
```

在构建目录receipt.json记录原Jar、输入源码及依赖SHA、应用类数和所有非应用类条目保留事实，不记录配置值。候选运行包SHA和两次独立构建对比另见Document/Deployment/tianjin_native_replica_20261023/original_business_rebuild_git_receipt.json。

加载器验证仅执行原标准layertools的list命令。先枚举所有嵌套库的JarMode注册，只有原LayerToolsJarMode；Spring Boot 3.1.5[官方Launcher源码](https://raw.githubusercontent.com/spring-projects/spring-boot/v3.1.5/spring-boot-project/spring-boot-tools/spring-boot-loader/src/main/java/org/springframework/boot/loader/Launcher.java)确认设置jarmode后选择JarModeLauncher，未进入应用主类。实际返回dependencies、spring-boot-loader、snapshot-dependencies、application四层，不能将此描述为后台服务启动或数据库联通。原自动任务仍待私有依赖和测试数据齐备后逐项验证。

## 双后台构建选项校准与当前限制

原业务后台与原大屏后台的应用类均没有MethodParameters，保留局部变量调试信息。初版重建命令使用-parameters、缺少完整-g信息，其88d88343候选仅作为历史可复现检查保留，不能作为与原包一致的证明。已根据原Maven编译配置、[3.11.0官方参数默认值](https://maven.apache.org/plugins-archives/maven-compiler-plugin-3.11.0/compile-mojo.html)和实际原class元数据，改为-g并去除-parameters；原业务后台仍使用原Java17和220原依赖。768类中723类字节与原包一致，45类仍不同；已离线做javap比较，其中BaseFile示例差异涉及字符串拼接的String.valueOf生成方式，不能据此断言全部差异均为编译器造成。所有差异路径和摘要见original_business_class_difference_audit.json，未通过业务/注解/原站对版。

工具新增显式--java-release 8、--artifact-name支持独立大屏后台，拒绝JDK版本/原包class major不一致。大屏原运行包SHA为97c2f1662a3a4494f01da4c2e83d7fa960e6832bda870e90424ffbaddf667cca，26原源码、27应用类、73原依赖、3个原配置资源，以原Java8和原Lombok1.18.2构建，不混用业务后台Java17或升级处理器。

JDK8使用Azul官方元数据及官方CDN ZIP，SHA-256 510d00a6814ee576205cdfec7efd0c9f93b066b34bf3f841b8854594dc97476b校验后才解压、执行版本检查。独立D盘目录，不改全局PATH/注册表。Adoptium API403、GitHub范围请求TLS超时和普通整包下载的partial保留；仅主动停止本轮自有下载进程后，按已实测206协议有界分段下载。Azul API标注大小108696000，实际Content-Range与ZIP为108695886，完整官方SHA一致。

大屏首次javac.exe -version在创建进程时报WinError32，未建立构建输出目录；独占读取探测也失败。该探测原PowerShell未设置终止错误而输出过无效true字段，已明确作废，不当作占用解除证据。没有关闭其它进程或修改安全设置。后续显式--java8-tools-main使用同一JDK的java.exe、lib/tools.jar调用同一个com.sun.tools.javac.Main编译器，javac版本1.8.0_504，26源码实际编译/封装通过；没有重试受锁javac.exe，也不声称其文件占用已解除。

第二次构建从精确Git镜像提取本工具，业务Java17与大屏Java8各自重建并逐Jar字节比较。两套原标准layertools清单检查不进入应用主类；这不是完整Maven构建、依赖平台运行、数据库连接或原站业务对照验收。所有运行包、原Reference源码和配置值留私有本地目录，不进Git；新载荷仅重建工具和本说明。

## 原数据库结构文档核对与采集缺口

tools/inspect_tianjin_original_database_schema.py只读解析原Word中表头明确为“#、字段、名称、数据类型、主键、非空、默认值、备注说明”的102张结构表，1496字段。其余1438总表格中的参数/响应表不混作数据库表。工具不执行文档指令，不执行SQL，不生成建库脚本、不创建库、不导入测试记录。

当前原Java源码显式@TableName候选112个（先去注释），对应111个不同表名；101个与文档一致。缺少base_organize、base_user、base_user_relation、dept_path、flow_task、safety_inspection、safety_inspection_accompaniment、user_data_permission、warning_log、warning_set的文档结构。文档另有safety_administrative_permit_documents未对应显式注解，不能据此认定未使用。源码正则盘点不宣称有效ORM字段/继承映射已验证。

13个带引号CURRENT_TIMESTAMP默认值按原文保留，尚需原库核实，不自动当作表达式或字符串。索引/外键、字符集/排序规则/引擎、服务端版本和实际记录均未核验。结构稿不是完整原库或已运行后台；不把缺口用自造模型/数据填补。

私有产物在Document/Database/tianjin_original_from_handover_20261023：概念实体目录、文档物理字段表、结构JSON、覆盖/缺口JSON、维护说明。原WordSHA为c8e8b60867bc813079bd0dab621f7c693a0a6c2bab4fed4ddbed6c96688f9591，Java输入SHA也入清单。两次独立生成物逐字节对比；运行输出必须为全新私有目录，错误原文SHA在写输出前拒绝，既有目录拒绝覆盖。结构数据、后续原站快照和凭据不随工具上传Git，旧数据库与既有模型未变；没有发生数据库字段、索引、状态或归属迁移。

数据仍按用户指定通过UU遍历采集，不要求用户重找SQL。当前Windows工具报failed to write kernel assets / os error3，官方排障资料未提供此特定错误的确定修复；本机临时目录存在、主进程仍为9:30启动，日志未提供具体缺失路径。受支持的浏览器连接没有原站标签，本轮直接打开原URL也已实测ERR_EMPTY_RESPONSE；仅关闭本轮自建错误标签，没有改原站。没有禁用沙箱、修改ACL或安全设置，没有操作UU窗口或采到数据。需恢复Windows操作工具后续接采集。

### UU原站实际采集恢复与当前范围（2026-10-23 16:30，整体active）

Windows node_repl/@oai/sky现已实际可用，并已通过UU进入天津原站已登录页面；此前kernel assets/os error3为历史阻塞，已解除，不再要求用户重开工具或重找SQL。只读取得CurrentUser实际11根菜单/69菜单节点/79权限条目、组织树、风险等级字典；风险单元100+13条按原ID去重113/113通过，并取得1条原详情样本。检查内容100+100+66行虽然合计266，但仅219不同ID、47重复/47缺口，不能称全量；原Controller仅按createdAt降序，无同值稳定次序，与观察一致，但未证明所有重复成因。下一步使用原UI部门/级别/单元筛选分组补采并验证ID并集。全部266条检查记录riskLevelId均为空，不推造外键关联。

所有原响应与元数据留Application/work/tianjin_native_20261023/captured_reference_20261023；16份收据已核验，Windows文本写入的CRLF使原收据逻辑文本SHA与磁盘SHA不同，检查点同时保存两者，原件未改。CurrentUser默认密码字段已移除且未输出值；保存助手已加强认证字段过滤。原导出已点击一次，Copy response不是可解析JSON，保存助手在落盘前拒绝；导出文件内容/完整性尚未验，不计导出成功。HAR只含请求元数据、没有响应正文，不能当已采业务数据。原界面截图/菜单对源码矩阵及uu_capture_checkpoint_20261023.json私有封存，不进Git/公网目录。

用户再次明确Reference内是天津项目源码，继续直接使用四套原前端与两套原Java工程作为主体，UU用于核对原菜单、权限、模块内操作与测试数据。未启动原后台、未建库导入、未完成全模块对版或公网部署，第一阶段未完成；不回到自建Python兼容后台/合成数据路线。原站无新增/修改/删除/审批，未自动化登录；held14/旧服务/GIS/用户业务库保持。长期UE/EXE/网页/迁移归档目标保留active。

### 原源码严格复刻：分组补采与业务关联核验（2026-10-23 17:00，整体 active）

继续以 Reference 四套原前端、两套原 Java 工程为主体。通过 UU 原站只读 UI 按风险等级分组，已补齐检查内容原分页遗漏的 47 个 ID：当前 266 个不同 ID 对应原总数 266，重大20、较大11、一般99、低风险136；重复记录字段冲突0。旧三页219个不同ID/47重复的证据保留为历史，不改写原响应；全部266个当前检查项 riskLevelId 为空，不构造风险单元外键。

原排查清单列表12/12、详情12/12，432条子项引用涉及254个不同检查项，均命中当前266项。原排查计划列表14/14、详情14/14，323条计划检查项明细；其中20条引用涉及5个当前检查列表未出现的原 itemId，保留原计划快照和原ID，关联原因未核实，不补造当前检查项。任务列表两页100+45按ID核验145/145，取得1条已排查详情、58个检查项；其余144条详情、隐患/附件/审批流和其他模块仍待采集核对，不能称全模块完成。

已验证原 Chrome Network 的“导出HAR”文件包含响应正文：022/023/024分别保留51/33/38个原JSON响应。此前“Copy all listed as HAR”元数据文件仍无正文，两种保存方式明确区分；业务Excel导出仍未验收。保存前过滤认证头、cookie和凭据字段，原站无新增/编辑/删除/提交/审批。原响应、截图、ID及原站数据仅在私有 work 和 Deployment 证据目录，不进 Git 或公网目录。

025_original_data_bundle.json已按原ID整合风险单元113、当前检查内容266、清单12详情、计划14详情、任务145列表及1详情；SHA-256 b2259fcfcd2bf5e885db35bf7299d3393d0b017f43f745681f0c1fa3fa12996a。它是原响应整理包，未建库、未导入数据库、未启动原应用后台。后续先补任务/隐患和其他原模块，再恢复隔离的原平台配套与数据库，逐项验证原组件和原Java逻辑；第一阶段和公网部署仍未完成，未通知用户复核通过。长期引擎UE/EXE/网页/迁移目标保持 active。

### 原测试机配套资料新线索（2026-10-23 17:07）

通过UU已打开的F:/TJZY项目目录只读确认home/tool下有mysql、nacos、redis、minio、nginx及docker-compose.yml；mysql/data含jnpf、nacos、tj_endanger。tj_endanger内可见108个物理文件，包括check_items.ibd、check_plan_items.ibd、check_plan_schedule.ibd等，界面显示文件修改时点为2025-11，不能据此认定与当前网页完全一致或为一致性备份。未运行脚本、未启动/停止服务、未读取密钥或密码值。该目录目前仅在远端观察到，本地尚未收到，也未验证恢复成功。

UU工具-文件传输明确提示“远程协助不支持文件传输”。已通过异步问题请用户用可用传输方式复制远端F:/TJZY/home/tool及home/tjng到本机Reference/原环境配套_20261023，原文件保留；不是要求用户重新寻找SQL。等待复制期间继续网页采集及原源码核对。收到后先清点、校验和封存只读原件，再在独立副本验证版本与恢复，不对原目录执行数据库程序。此线索优先于此前“本地未找到配套资料”的历史描述；配套运行和第一阶段仍未完成。

### 原隐患台账采集核验（2026-10-23）

继续以Reference原工程为主体，原站台账16个不同ID/总数16，15个详情成功、1个原HTTP500失败；失败保留，不补造记录。隐患来源分别含排查、巡检、随手拍，原表单分支保持。
原待审批工单详情取得，但流程详情原HTTP404，默认灰色流程图和空流转记录不计真实审批数据。原代理与流程路由尚待配套恢复后核验，未凭猜测改写原源码。
私有原始响应、原ID、截图和脱敏收据封存并按SHA核验，均不纳入Git或公网；业务附件和完整流程未验收。原后台及数据库未联调，第一阶段未完成。

### 原上级检查与巡检模块采集核验（2026-10-23）

通过UU原查询取得当前视图上级检查1、专项任务0、班组6、巡检点32、线路8、巡检计划40、问题14条列表；不同ID与原total一致。上级检查1详情、班组6详情已齐，其余详情部分采集，不计完整模块通过。
原线路61次点位引用、原任务312次点位引用命中当前32点；19条历史任务引用8个当前班组列表缺席ID，保留历史关系待核，不补造记录。原线路图附件预览失败另记，地图点位和附件分别验收。
31个查询响应及原ID整理包、截图、SHA收据留本地私有目录，不进Git或公网。继续补齐详情子表和原配套联调，严格复刻第一阶段未完成。

### 原共享依赖及工作台审批核对（2026-10-24）

自有通用类路径工具通过8项测试；从共享原运行包直接核验768个源码重建业务类、97个原资源和16个平台顶层类全部通过，不复制大JAR，不启动原Spring应用或数据库。类路径成功不等于业务兼容或完整复刻通过。
原工作台实测巡检总计201与问题类型合计14对应不同SQL口径，保留原计算方式。原JNPF、业务统一响应和直接DTO响应分别按原契约核验，不能统一改造成仿造接口。
当前账号原已办列表23条不同ID涉及15个流程实例，保留每条审批历史；1个原详情包含3节点、8条操作记录，审批记录、流程图及流程状态实际显示。以前原隐患详情404仍单独保留，不能将本次成功当作其修复。
原响应、原ID、截图和SHA收据仅存私有证据目录，不入Git或公网。隔离原库、完整PC/手机操作及测试数据复刻仍未完成，第一阶段和公网新版未验收。
