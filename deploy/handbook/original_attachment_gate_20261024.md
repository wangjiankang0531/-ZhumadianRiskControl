# 原附件引用与失败语义验收门槛（2026-10-24）

记录时间：2026-10-24T19:17:50.565570+08:00。本阶段完成封存导出中13个指定表、15个附件字段的只读引用统计，以及未修改原附件类的错误语义实测。它没有恢复对象或验证正常上传，不是完整复刻交付。原联合候选继续运行，公网未切换。

## 原数据中的引用和资源缺口

使用固定封存manifest cdac2c99a5d43a4daabea7bf547d7ea9fbda8b2a4a3b491f98b95a5fcfc76b5d，压缩载荷前后SHA、长度和修改时间一致；两库全流未压缩SHA分别5814f66415248c1df04959c81598dbf190f55333ded982e36d0c05dc4aa8ce80、d62023a4c7c175cec7007161d4e9dffc7db51f45c285c8911518a3805e50098d，与恢复基线一致。流式处理约600 MiB原始流，不写原始行副本，不连接源数据库。

白名单来自实际schema；只解码指定附件字段，不解码用户、个人照片、指纹、签名字段。全流校验仍会读取其编码字节；不能称完全未读该库的相关字节。结构化JSON、空值、未知结构和不支持路径分别统计，输出只有计数与SHA，不写原URL、文件名、桶名或业务行。白名单不覆盖全部业务表及动态表单内容，因此referenceScopeComplete=false。

| 表 | 字段 | 非空行 | 分隔后的引用次数 |
| --- | --- | ---: | ---: |
| base_file | file_url | 6 | 6 |
| event_disposal_record | attachments | 17 | 18 |
| event_info | file_url | 10 | 10 |
| inspection_issue | attachment | 5 | 7 |
| inspection_issue | result_attachment | 2 | 2 |
| safety_manage_file | file_address | 7 | 7 |
| work_supervise | file_url | 11 | 13 |

共58个非空字段行、63个不同引用，其中62个是原sys-file对象路径，另1个是未解释的文件标记，不能擅自当有效对象。62个路径只有1个桶名称指纹。Y盘现有MinIO data快照顶层业务目录0、对应桶目录匹配0；只看顶层名称，没有打开.minio.sys或对象正文。该观察不证明原在线对象存储为空或永久丢失，不能把数据库恢复称附件恢复。

## 原表单分隔规则与首轮修正

应急处置attachments、事件fileUrl和作业监督fileUrl由原页面逗号拼接/拆分；巡检attachment/resultAttachment由原页面分号拆分。original_form_contracts.json记录5个原源码文件SHA及精确标记命中，不复制源码。首轮r1将多附件整个字符串当单引用，58项统计不采用；核对原源码后r2/r3按字段显式分隔得到63，不对任意URL查询参数或JSON URL盲目按逗号拆分。r1证据保留，不能把58项旧值当最终验收结果。

14项Python测试覆盖JSON/原分隔、多附件去重、未知结构、字段宽度、非法编码、结构限额、哈希不符、缺字段拒绝、只比顶层桶名及结果不泄露原引用。真实导出检查的表行数与manifest一致；这证明本次指定范围的统计，不证明对象存在或可下载。

## 原类错误语义的实际测试

从既有只读flat application.jar加载原MinioConfig、MinioUtil、SysFileServiceImpl，3个class SHA与固定清单相同，原flat SHA c4637e950664ff2ee26746b80366ca12e8c1f36f69288d35e126871f9afe30ae、219个依赖逐一核验。没有改原class，没有启动原Spring Application，没有连接数据库或原对象存储。

自有HTTP故障夹具只在127.0.0.1随机端口返回503/XML，不是MinIO或替代对象存储。使用原MinioClient和原服务、合成小文件和自有随机凭据；未修改既有Java17进程边界Jar SHA3f5b36ef4a48714a0424b7470d7a1aecf7bd1beb385a4843fd08adc02bd16bb9，仅允许该自有端口和本轮目录。19项实测检查通过，4次实际HTTP请求、0次PUT，夹具进程自然退出0：

- 普通上传与PDF上传均在没有对象PUT的情况下返回原Response.SUCCESS和文件URL。
- 原Base64下载在失败时返回null。
- 原下载捕获异常，未设置Servlet错误状态、未请求输出流；该直接服务观察不是完整HTTP控制器返回状态测试。
- 三原类实际来自固定flat jar，原类未替换、边界仍在、自有哨兵内容不变。

这验证的是原失败行为及验收误判风险，fileServiceSuccessVerified=false。原上传辅助方法捕获错误后返回null，上层忽略这个返回值；第一阶段保留原逻辑，不把此处改成自有模拟后端，也不静默修复原业务行为来宣称严格同版。首轮仅自有夹具Proxy导入歧义导致编译失败，未进入原类；修正后r2/r3通过，失败留存。

## 后续正常链路的验收要求

后续需从原在线环境确定有效对象存储版本、对象位置及历史附件资源，按用户既有授权只读取得需要的附件；不把Y目录快照等同在线状态，不用未核验或窄协议模拟服务冒充原MinIO。部署独立真实存储后，在自有桶中用合成文件验证原上传、返回地址、按原前端前缀取回、长度/SHA一致；覆盖PDF/图片/普通附件与原组件预览，并保留原账户权限和失败语义。只出现提示成功、应用成功码或空HTTP200均不能通过附件验收。已有历史引用需逐个核对实际资源，未知标记要按原模块解释，不擅自替换数据库字段。

手机原uni拦截器会在uploadFile上补应用API前缀，编译文本中/serv/sys-file/upload不是漏前缀的直接证据；不能再把VITE_UPLOAD_BASEURL改成带同一前缀导致重复。当前未改H5、网关和运行配置，未发真实业务上传。

## 运行、资源、文档和源码

当前own-j6/45088和尺寸预览98418仍活，原电脑端18891与预览18892实际HTTP200，租约截至19:46:36；终态以新receipt及退出码为准。正式8767 starts1/alive=true/failed=false、加载失败0、保护写入0，14held SHA未变，252/公网未操作。待原账号登录后继续CurrentUser/角色菜单及模块操作验收；账号密码、验证码、JWT不由本轮自动化提交。

新增自有源码为audit_original_attachment_references.py、test_audit_original_attachment_references.py、verify_original_file_failure.py、java/OriginalFileFailureFixture.java及本handbook共5文件；只同步这些自有源码/说明。原工程/原class/JAR/数据/附件/运行包/截图/凭据/生成结果不入Git。无新整库、GIS或原JAR副本；本轮只生成小型源码、class及记录，未做MinIO安装或大包下载。

完整UE级引擎、EXE点线面图层、网页3D、驻马店迁移归档及天津完整复刻目标仍active。20秒外围清晰、完整认证/流程、文件存储及公网同版未通过；本阶段不发布候选、不标目标完成。
