# 2026-10-24 演示入口发布与双机验收

记录时间：2026-10-24T13:39:24+08:00。用户要求16:00演示，优先更新既有公网项目测试版，并使250、252分别进入本机三维应急一张图。天津南港原前端、原后台、原测试数据与全部内部操作严格复刻仍未达成，本次不是该阶段验收。

## 实现与发布范围

公网入口为 https://www.joinlinksmart.com/zhumadian/ ，版本仍为0.9.0 / referenceRevision 20261022-r2，新增presentationRevision为20261024-demo1。首页显示今日演示日期；电脑业务工作台增加“敏捷应急指挥”，与首页相同，打开 http://127.0.0.1:8767/?topic=emergency&mode=command 。该地址在点击者自己的电脑解析，不固定为250或252的局域网地址。链接使用新标签和noopener noreferrer，不携带公网登录会话、CSRF或口令。

三个HTML页面为JS/CSS追加同版查询参数。实际发布仅web/dist下reference-demo.html、reference-demo.js、business.html、mobile.html、business.js及package_manifest.json。未改后端、业务数据库或IIS配置，未重启后端。

13:21已发布，原文件先备份到服务器 /Zhumadian/ZhumadianBusiness_0.9.0_public_1/logs/demo_20261024_132103 。六个旧文件与服务器备份读回一致；五个新文件分别完成服务器读回SHA与真实HTTPS读取SHA比对，公网根页面等于候选HTML，业务汇总API可读。新manifest SHA为beb1f6ed18585de078e514733bb061419aff28b118426519dcc6bad51b30fbbd。完整本地收据位于Application/work/demo_20261024/publication_receipt.json，备份在server_before和server_backup_verified；其中私有日志不入Git。

## 250本机实现与数据保留

原8767选择器0.9.7只读取到2个用户标注。保留其冻结版本与active_release.json，未就地修改。独立演示目录为Application/work/demo_20261024/local_scene，固定源码运行清单身份f6a5758586635b70025773c3e40083e0c51c7bc01cc02db74cf491233dd7293a。

先在8768启动自有独立候选，验证14家企业与原有2标注共16个、原生只读读取器启动和请求成功。退出协议实际返回204，初始控制器错误断言200导致记录中断；原生候选已正常退出0，核验所有者日志及进程终态后才继续切换，未重复发送退出请求。该诊断失误和首次记录保留。随后严格核验旧PID、启动时间、完整命令和8767监听归属，只停止该旧场景，再于8767启动已验证候选。演示服务现保持运行，不设置自动重启或系统服务。

5840个固定SHA运行资源通过硬链接复用约774.61MiB逻辑内容，payloadBytesCopied=0。原GIS只读引用Assets/3DGIS下现存Data，没有复制GIS或252原环境。新增仅独立UserData、少量清单、日志和截图。不得把硬链接目录属性再次累计为真实新增空间，也不得演示前清理该运行目录。

原Assets/DLG/驻马店图层.json的2标注完整并入独立演示图层，原文件SHA a8472f1a89d67f7e37cd932bce571d8a6a766fec8d96550c956900e05f47b1f3 不变；原图层业务库SHA e6951c261cf1ff50fc7aacebdc3f0e3c6923d7ad6616ffa7bd4db77b5dd963a1 不变，已有在线SQLite备份并通过完整性核验。新演示图层保存在其独立UserData，不自动回写原业务库或用户DLG。

## 实际验收

- 现有reference_home和reference_deployment共9项测试通过；本轮未增加镜像实现的低价值测试。
- 250从公网电脑业务菜单点击后进入本机8767；实际渲染敏捷应急指挥，14企业、全部16标注。点击近景，原生读取器starts=1、alive=true、failed=false，store.failures=0，protectedWrites=0。截图已保存，不将FPS截图作为性能基准。
- 252通过UU观察，刷新公网首页并实际点击“敏捷应急指挥”，新标签进入252自己的127.0.0.1:8767，同样显示14企业、16总标注，点击近景后看到三维细层。未修改252原环境或复制原数据库。
- 公网1280 CSS像素电脑首页、312/390 CSS像素手机业务页可用；手机隐患列表与已闭环测试记录详情/整改/复核/历史可读，与电脑同一测试业务库。QA只读取既有测试记录，没有新增、审批或删除公网业务数据。浏览器临时视口已恢复，临时测试标签已关闭，留下公网首页与250正式场景。
- 原20秒外围角落全部清晰的质量要求仍未验收通过，不宣称此次入口更新解决了该问题。

14家企业来自既有发布文件快照，点位为资料估算、厂界待核实；演练、通讯席位与预案图表明确标注模拟。当前公网为既有项目测试业务后台，并非已完成天津原平台移植；原JNPF登录/工作流与全部PC/手机操作对版仍需继续验证。

## 演示步骤与运行维护

在250或252打开公网地址，使用既有账号登录，点击首页左侧“敏捷应急指挥”；将进入各自本机服务。可用“总览”“斜视”“近景”和企业标牌进行查看。电脑业务工作台侧栏也有同名入口；手机业务端为mobile.html。演示前保持两机开机及本机8767服务运行，不重启服务或清理运行资源；没有新要求安装APK。

250新运行目录的runtime/python/python.exe以-I -B运行application/tools/portable_web_entry.py，参数为--package该目录 --port 8767 --no-browser。手动恢复前先查询端口与/api/runtime/status并核对清单身份，已有同身份服务可直接使用；不同服务占用时停止恢复操作，不终止未知进程。当前启动和所有者记录保存在Application/work/demo_20261024/scene_presentation.json及独立UserData/Run，所有者凭据不入Git。

公网回滚：先核对发布收据，仅把服务器备份中的上述五个dist文件和manifest恢复原位，再按备份SHA读回并检查公网页面及API。不改数据库、不重启后端。250回滚：先按所有者协议正常关闭本次自有演示服务并核验退出，再使用原active_release.json选择器启动原0.9.7，端口8767；不能同时启动两套。原选择器与原用户数据均未改动，回滚后原版只含2标注的既有行为仍存在。252本次未替换运行包。

## 源码同步与持续目标

本轮源码载荷精确为5个Web源码与本handbook，共6文件。运行包、GIS、截图、数据库、Reference原源码、私有日志、所有者凭据和原14项held均不入Git。远端main发布前基线为7e1bee883695c036d673ede2afc034aa2785be55；具体同步结果另存本地source_mirror.json。引擎远端8966e32b370a10b1e8f5d4fba512f42f439c2451与本地已集成树相同，无新引擎代码待合并。

长期UE级引擎、驻马店EXE/网页点线面图层、迁移归档仍active。本轮仅完成演示入口发布和双机打开验证，fullCloneReady=false。完整原环境复刻完成后再通知用户正式复核。
