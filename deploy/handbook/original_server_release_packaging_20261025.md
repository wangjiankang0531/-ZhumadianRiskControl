# 原系统独立测试包、IIS切换与回滚

本包用于把当前天津原前后端及恢复测试数据，以“驻马店重大风险防控”名称部署到既有站点。不是旧R2上的静态页面替换；电脑、H5、应急管理和管理平台复用原工程及原后台，登录加密、角色与业务编码保留。完整业务复刻仍未验收。

## 固定载荷与实际范围

发布ID e5385db1-3ca6-4399-9ae5-64dc3e442b27。原输入15950文件、2126305460字节；最终ZIP15970项、1050340997字节，SHA256为0a9174d21fc9815697f57ac49fbef7e75bee09ac4cbcb9508a1e0f2663564f8e。release-manifest.json的SHA256为cb4587d6158b6392315f1941996161a2796cf1104de9759ce447c57e94a4d57a。

包含私有原SDK、原前端及已从逻辑导出恢复的本方关闭库种子；不是252原物理库。没有全量驻马店GIS、Reference目录或Y盘镜像。包内Python/Java/MySQL/Redis/MinIO/Nginx，不需要运行时访问250/252或Y盘。地景仍在点击者自己的8767，由原首页“敏捷应急指挥”打开http://127.0.0.1:8767/?topic=emergency&mode=command，不转发公网登录令牌；手机二维码已指向https://www.joinlinksmart.com/zhumadian/h5/。

包包含原测试数据及私有配置，禁止入Git、放在可匿名下载目录或经明文互联网传输。上传前先给独立传输目录放置本轮web.config：清空HTTP处理器并拒绝所有扩展。使用现有加密传输会话；若现有FTP未加密，改用已登录RDP的加密文件传输，不改变客户端安全设置。该目录不与旧IIS根目录重叠。

## 实际独立启动与重启

以D:/Zqa20261025/Application全量解压验证，实际包内Python启动，原j18和8767保留。首次j1与同一数据重启j2均真实ready，平台/业务上下文关闭、MinIO/MySQL/Redis/平台/业务/Nginx六组件全部自然退出0；强制Job收尾列表为空，数据库与平台文件身份保持，没有重新初始化数据库。CIM末查无该QA根进程残留。

电脑、H5、应急、admin、SVG、二维码、getLoginConfig和CurrentUser八项实际HTTP检查。前七项200，登录配置业务码200；未登录CurrentUser业务码600，未绕过原认证。图标598字节/SHA509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d，二维码934字节/SHA0779e151fd7884029b7533a39bfc972c14af17c1b63f26fc67d2fd313b0c9be2。

15965个载荷和控制器文件逐SHA验证，读取CRC通过；两个清单及三个启动CMD额外核验，ZIP无重复条目。核心后台控制源码14文件中的原12文件与两轮实机完全相同；后加两个文件仅为发布/回滚工具。没有将该事实外推成服务器IIS、登录后全模块或全部WebSocket业务已通过。

## 归属与生命周期

新控制器显式persistent，默认无12小时退出；QA时长只限制测试控制器ready后的观察，不放宽后端归属。首装把已核验种子移动到安装私有UserData，生成独立MySQL UUID，后续按安装身份保留可写库，不再比较用户已写库与初始种子SHA。平台文件继续使用既有独占owner与每轮新run目录。

每个新子进程都绑定自己的Windows Job，异常owner退出仅收回自有子进程，正常停止优先Spring上下文、Redis NOSAVE、MySQL管理命令与MinIO认证停止。Job收尾可能返回0，因此单独记录强制收尾清单，不能把强制0解释为自然退出。日志每组件保留尾部1MiB。当前未验证服务器OS重启自动恢复或长期运行，不声称已安装系统服务。

## 操作与回滚

受保护传输目录名ZhumadianOriginal_Private_20261025，含ZIP、web.config、Deploy_Original_20261025.cmd及PS1。服务器在该目录运行CMD一次；脚本先验证既有IIS根、C盘至少12GiB、.NET4.5和IIS WebSocket已安装。缺条件即停止，不自动安装角色、不修改安全设置或执行策略。ZIP SHA与全部解压路径先验证，独立临时目录解压后移动到固定C:/Zdm/Application，不覆盖其它现存版本。

新后台只监听回环18892及私有随机基础端口。真实ready和接口检查通过后，编译新IIS适配器、备份既有两个IIS文件，再短时维护切换；本机TLS严格验证证书和既有域名，失败恢复原字节。旧18874后端与旧库不重启、不迁移或修改。新测试库独立保留。现有IIS根固定C:/FTP_Root/Zhumadian/ZhumadianBusiness_0.8.7_public_1/iis。

发布工具在自己UserData/OriginalDeployment保存事务、原文件及私有配置，回滚时比较当前新文件SHA，拒绝覆盖其它操作者修改或已变备份。Rollback_Original_Server.cmd只恢复自己的事务并向归属核对的自有新后台请求正常停止；原测试数据保留。六项实际文件夹具覆盖成功/回滚、探针失败、用户维护文件、并发修改、备份变更及重复事务。五项控制器测试和十二项参数检查通过；首版Job夹具把强制0误当失败，已据实际修正并保留记录。

服务器启动需按受控正常方式执行，GUI自动化不执行命令或脚本；完整包上传完成后再交用户一次点击。上传完成不等于发布完成，服务器本机TLS通过也不等于外网电脑/H5与原账号登录验收。

## 仍待验收

当前公网尚未切换。服务器IIS及WebSocket真实运行、外网访问、原账号电脑/H5登录、所有模块/角色/审批写入/历史附件、252同版与20秒外围三维质量未验收，fullCloneReady=false。当前j18仍是250的原12小时测试版，不因新包完成而重启。数据库字段/索引/状态结构未改，不重建模型。所有原14held修改保持；SDK、库、原数据、运行包、截图和凭据不得同步Git。

证据目录Document/Deployment/original_server_release_20261025：两轮独立收据、匿名HTTP对照、final-archive-verification.json、final-release.json和三个新工具测试日志。冻结清单与ZIP只在Application/work/original_server_release_preparation_20261025私有保存。
