# 原管理平台持久文件接入与跨原应用重启验收（2026-10-24）

记录时间：2026-10-24T21:06:04.818363+08:00。原管理平台已经实际接入持久文件目录，原13个逻辑目录Bean与两提供器绑定均通过。前一原应用进程上传的108字节合成文件，在该进程正常关闭、完整新原应用启动后，由原 FileUploadUtils 方法找回，再通过原控制器及正确既有网关返回HTTP200、完整字节/SHA一致。最后以原方法仅删除该合成文件及自有标记。认证HTTP上传、页面操作与完整天津复刻仍未验收，公网没有替换。

## 目录、身份与启动范围

固定数据根为Application/UserData/TianjinOriginalPlatform，files存原平台本地文件，runs/jN存每个自有进程的配置、日志与观察文件。identity.json / identity.properties保留同一自有数据身份，owner.lock以Windows字节锁排斥并发拥有者；已有数据目录没有已知身份时拒绝接管，不把它当空目录重置。身份/文件目录拒绝重解析点，单次运行目录必须新建。固定数据目录是用户数据，不能在退出或清理缓存时删除。

Python锁模块在运行前核对布局及身份，Java启动器再核对实际目录、同一拥有者、files目录和准确3端口：自己的MySQL、Redis、对象存储。平台的原两端口模式不改；新平台模式只在--platform-storage显式开启，且要求已有自有对象存储及原业务语义模式。新Java启动器保留原JarLauncher、依赖顺序及既有资源缓存类，仅以明确数据根作为受约束写入范围；它覆盖该项目自己的files及runs，不是仅当前run。原Java8边界Jar SHA799d1289保持不变，没有目录链接绕过或Windows安全设置变更。这是已知原代码的进程内集成约束，不是对恶意代码的操作系统沙箱。

新增精确忽略规则/UserData/TianjinOriginalPlatform/，实际身份文件check-ignore命中；数据、配置、自有连接与截图都不入Git。Java17业务继续准确4端口，原业务类和边界Jar不改。

## 原配置与原路径方法

使用上一阶段已核验的原提供器overlay，恢复local-plus默认、同时启用原MinIO、保留13个相对逻辑目录及原提供器/桶身份。只替换本地物理根、自有回环地址及自有凭据；原物理根和原存储凭据不复制。配置源仍是固定原JAR声明的test配置，这不证明252当前内存有效配置一致。

真实ApplicationReady观察器从原Spring容器取得FileStorageProperties / FileStorageService / LocalPathConfig，逐项比较13目录字段、local-plus选择/物理根和MinIO启用/地址/凭据/桶绑定。探针路径调用原FilePathUtil.getFilePath("annex")，不自行给原配置规定目录尾斜杠；原方法会在配置值后加分隔符。随后调用原FileUploadUtils.uploadFile与downloadFileByte，不提供新HTTP诊断端点、不修改原认证或伪造JWT。

## 两次真实原应用之间的文件保留

own-j9原两main返回且13目录/两提供器绑定及108字节上传和原下载回读实际通过；随后自有HTTP探针误写/zhumadian/api/file/...，实际既有路由是/zhumadian/api/jnpf/file/...，Nginx返回404，该运行仍记failed=true。六组件均自然0、两个ContextClosed、静态资源关闭且平台数据锁释放；该探针保留，原文件和数据库没有为修复重新复制。

own-j10使用显式--platform-files-recover。恢复前要求上一原main已返回并正常退出0/ContextClosed/锁释放，核对准确前运行目录、原观察passed/13目录/原方法回读及同拥有者的探针标记；上一failed和HTTP未通过事实写入本轮platformFileRecoveryBasis，不篡改旧收据。新原Spring容器使用相同数据身份/目录，原方法按上一文件名/原目录找到内容并比对随机拥有者及SHA。

通过正确原路径/zhumadian/api/jnpf/file/Image/annex/原文件名 GET，HTTP200、108字节，SHA ee78d68818e1ce341cff8e0f5fabf7efea5b2c07b1348e2539d7251665bde649。该路由使用原UtilsController/原FileDownloadUtil输出文件流；这是文本合成探针的字节回读，不证明图片/PDF渲染或用户预览UI。实际没有发送Authorization、JWT或验证码。

网关回读后，控制器只写本轮自有清理请求；原Spring工作线程再次核对标记和完整内容，调用原deleteFileByPathAndFileName，确认准确文件不存在后删除自有标记并原子发布清理收据。没有删除其它文件或目录。当前dataRoot身份/文件根保留，当前实例用户后续上传应继续放入该固定files目录。完整用户附件与业务库的一致性备份恢复演练仍待。

## 原文件记录服务的边界

固定原包中FileDetailService.record/delete直接返回true，getByUrl/getFileDetail/getFileList直接返回null，字节码检查记录在原管理平台存储审计目录。本轮保留原实现，不补造保存记录，也不将成功返回当数据库元数据落库证据。观察结果明确originalFileRecorderDatabasePersistenceVerified=false。业务表单自己的附件关联保存、原账号权限和角色流程仍需后续真实操作验证。业务数据库字段、索引、状态和归属没有改动，不新增数据库模型。

## 真实失败与通过范围

own-j8在实际两main/配置绑定后，因自有观察器错误要求原配置尾斜杠失败；未创建平台探针，六组件自然0/锁释放。修正为调用原FilePathUtil后own-j9实际文件方法通过，但HTTP探针前缀错误404仍失败。两个失败都保留，不记为全通过。own-j10才通过跨进程原方法与原HTTP正确路径。

独立夹具10项身份/锁生命周期与30项实际Java8目录/端口范围通过：同身份文件跨拥有者重开保持、并发拥有者在运行目录创建前被拒绝；准确3个自有TCP端口可连，额外/重复/外网/带认证或路径参数端点拒绝，当前运行与固定files可写、目录外写/额外端口/DNS/替换边界被拒绝。最终夹具使用隔离的Application布局，不绕过当前真实数据锁。两个关键启动class与实际运行字节一致；原观察器class在真实前后两次原应用中相同。13项既有平台门槛/共享Redis回归通过，两个非法新参数组合在创建运行目录前拒绝，CLI帮助通过。当前冻结控制器与源文件一致。

业务后台的原14绑定/2内部URL/2原JDBC时区、共享原Redis及可写计数继续通过；它的原Spring MinIO六字段与69字节原网关回读也继续通过，自己的S3探针单对象删后HEAD404，其它对象/桶不动。本轮没有以这些证据替代管理平台108字节的独立证据。

## 入口、浏览器和运维

当前唯一后台句柄81203、手机预览68608，均已实际就绪且继续运行，预计到2026-10-24T23:00:14.845670+08:00。原电脑入口http://127.0.0.1:18891/zhumadian/home，H5 /zhumadian/h5/，管理端 /zhumadian/admin/，尺寸预览http://127.0.0.1:18892/。四入口HTTP200，实际Chrome新页3077/3080显示原电脑/H5登录界面；iframe实测390×844、scroll宽390，无横向溢出。手机截图仍包含尺寸预览外壳，不能称真机/登录后页面；截图已实际查看。旧表单未重载，全浏览器viewport未更改，没有提交账号、密码或验证码。H5初始登录过期提示仍是原行为，不隐去后称页面无异常。

正常结束只写本轮own-j10/stop，由控制器先退出网关/原后台，再签名停MinIO并关Redis/MySQL，最后释放平台文件锁，保留两个UserData目录。当前own-j10完整租约自然结束尚未观察，不能借上轮/夹具退出0称它已通过关闭。若异常要查看当前句柄和当前收据，不能因观测超时重复启动。own-j7/66987、旧预览64399、own-j8/79640和own-j9/27180均已终态，不再poll。

正式8767仍starts1/alive=true/failed=false、加载失败0/保护写入0；公网仍R2、252原环境不操作。共享Y盘原JAR只读，既有恢复MySQL及151MB MinIO复用，无新整库/GIS/原JAR或SDK副本。

## 交付与后续

本轮9文件为.gitignore、平台文件owner/范围验证器、准确Scope、新原平台启动器、范围夹具、真实原Spring文件观察器、联合控制器及本handbook。仅这些自有源码/说明同步Git，不包含Reference原工程/依赖/class、前端资源包、数据库/附件、配置/自有密钥、截图或旧held。14held SHA保持。

还需原账号HTTP上传与业务关联保存、PC/H5附件操作与图片/PDF预览、原有效配置和历史对象恢复、角色/全模块/工作流、手机真机及公网同版。3角色差异、9孤立初始化记录/4缺失定义、历史62业务对象和未知标记仍待，不能把文件传输验收缩成完整复刻。UE级引擎、EXE点线面图层、网页3D、迁移归档及天津严格复刻目标继续active，fullCloneReady=false。
