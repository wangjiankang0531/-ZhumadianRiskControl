# 原天津前端部署构建与本地联调入口

本轮修复构建环境遗漏API地址的问题，不修改Reference业务源码，不提供仿造后台。

## 已确认的问题和最终行为

此前安全PC使用source-check构建模式，未加载.env.production的VITE_API_URL；原产物有28处undefined/serv、2处undefined/jnpf，原API前缀出现0次。Vite实际loadEnv也确认source-check地址缺失、production为/tianjinrisk/api。早期构建只能证明编译，不可作为可运行入口。

build_original_frontend.py使用原锁定依赖和原Vite/uni入口，仅按进程设置部署变量，在独立输出构建。security_pc、emergency_pc分别明确VITE_API_URL与VITE_APP_BASE_PATH，移动端同时设置请求base、代理前缀、附件getProxy前缀和公共资源base。三套产物中undefined/serv和undefined/jnpf均为0，原API前缀出现31/8/3次。

原外层网关为/tianjinrisk/，内层代理为/emergency/、/h5/、/map/与/api。移动Reference默认资源base为/h5/且代理/api；本候选H5部署base为/tianjinrisk/h5/，API/附件统一/tianjinrisk/api。保持原原生业务组件、接口后缀、鉴权及上传拦截器，不改写为自制手机页面。

使用replica-deploy构建模式，显式保留移动生产配置的去console/关闭sourcemap设置，NODE_ENV为production；此模式不自动打开原构建配置中的production统计图浏览器窗口。源配置和锁文件不改。部署变量不是原测试数据；最终视觉与业务一致性仍需真实原后台验证。

## 构建命令

```powershell
python -B -X utf8 tools/build_original_frontend.py --kind security_pc --project <原安全PC构建项目> --source-manifest <私有原源码SHA清单> --node <显式Node可执行文件> --output <全新独立输出>
python -B -X utf8 tools/build_original_frontend.py --kind emergency_pc --project <原应急PC构建项目> --source-manifest <同上> --node <同上> --output <全新独立输出>
python -B -X utf8 tools/build_original_frontend.py --kind mobile --project <既有依赖的独立移动构建副本> --source-project <只读原移动源码> --source-manifest <同上> --node <同上> --output <全新独立输出>
```

清单结构使用prepare_tianjin_original_sources的projects/files路径与SHA。所有原输入构建前后逐SHA验证；排除node_modules等构建目录，未知.env.local和其它新增输入拒绝。移动UniManifest原插件会改写独立构建副本src/manifest.json的h5.router.base；只有这一字段精确等于所配部署base且其它输入不变才保存生成快照、恢复原字节，拒绝忽略额外变化。原移动源码和Reference不写。

构建不运行npm安装脚本，不安装新依赖，不连接数据库，不启动原Spring应用，不部署公网。输出必须不存在且与输入目录不重叠。编译失败、原输入变化或产物错误API地址都保留日志并停止，不能覆盖旧候选冒充成功。

## 本地入口及协议边界

prepare_original_frontend_gateway.py生成仅绑定127.0.0.1的Nginx配置，静态目录和共享瓦片只引用，不复制资源。Nginx运行时由操作者显式提供、单独校验，不随源码提交。Windows版仅用于本地联调，不据此证明公网性能或生产可用。

原/api/jnpf/转发到本机平台/api/，原/api/serv/转发到本机业务/，原/api/serv/websocket/转发到本机业务/websocket/，保留查询、表单、鉴权头、Cookie、错误正文、二进制下载及WebSocket。真实后台未配置时返回503；未知API返回404，不能以SPA或伪造业务JSON代替。

四套本地静态入口为/tianjinrisk/、/tianjinrisk/emergency/、/tianjinrisk/h5/及/reference-bigscreen/。最后一个仅为显式本地QA挂载；现场原门户应急指挥链接使用本机18080端口的独立桌面组件，不能将此QA地址当成已接通的原门户目标；/zhumadian/也仅为本地重定向，公网子路径映射仍待实际部署验证。共享地图同时挂载/tianjinrisk/map/和/tianjinrisk/api/map/。非静态深层路由回原index，缺失静态文件及瓦片返回404。

默认不配置业务/平台上游；如配置必须同时给出两个本机端口，不能代理回网关自身。后台配置隔离、原库恢复、用户权限和真实业务仍单独验收。日志不记请求查询串或认证头；独立目录的主进程/工作进程均须在测试后正常退出，验证端口关闭。原共享服务、公网入口和用户业务库不重启。

## 验证

```powershell
python -B -X utf8 -m unittest discover -s tools -p test_original_frontend_deployment.py -v
python -B -X utf8 tools/test_original_frontend_gateway_runtime.py --runtime <已核验Nginx目录> --runtime-sha256 <nginx.exe的SHA256> --output <新证据目录> --security-pc <安全产物dist> --emergency-pc <应急dist> --mobile <H5产物dist> --bigscreen <大屏产物> --tiles <共享地图目录>
```

7项构建/路径/输入和限定恢复测试通过。真实Nginx HTTP逐文件校验835安全PC、204应急PC、191手机H5、376大屏共1606文件，原静态字节共151026677；两条共享瓦片路径通过。协议夹具只在测试期间开自有回环服务，覆盖URI/query、表单POST、鉴权/Cookie、206下载及range/content-disposition、原错误状态正文与WebSocket双向帧；不是业务实现或真实原账户测试。

早期本地前缀缺logs/temp父目录的配置失败、单进程模式无法优雅退出的失败均保留，未冒充通过。最终使用标准主/工作进程模式，配置通过、正常退出且两测试端口关闭。第一阶段仍缺隔离原库、原平台/原后端联调和完整电脑/手机操作对版，公网未发布新版。

依据：[Vite环境变量优先级](https://vite.dev/guide/env-and-mode.html)、[Nginx Windows运行与管理](https://nginx.org/en/docs/windows.html)、[官方签名公钥](https://nginx.org/en/pgp_keys.html)。原网关配置及原Reference留私有目录，不复制进Git。数据库模型没有变化。

原完整性CLI已修正Windows目录链接可能落在Path.walk文件名列表的识别差异，仍只排除原有明确的构建目录名称；实际对Reference及六套副本7566输入逐SHA校验全部通过，不将目录链接误计成业务源码，也不跳过其它文件。

## 原门户实测后的入口修正

原门户应急管理菜单链接没有末尾斜杠，先前静态root/rewrite配置会将它落入安全PC。网关为应急、H5、本地QA大屏的裸挂载地址明确返回301到各自带斜杠的入口，保留查询串。四套应用带斜杠根地址明确返回各自index.html，避免rewrite后目录index模块内部跳转到/index.html、再匹配站点默认404。

真实HTTP回归覆盖三个裸挂载×有无查询串共六项重定向、四个根入口、四个深层路由、1606个静态文件SHA、共享地图与七组透传协议。首轮回归确实发现根入口404，保留失败日志；其失败收尾原先只终止主进程、留下一个自有worker，已核验PID/父PID/专用运行时路径后单独关闭，测试finally已改正常quit整个自有进程组。修正后的第二轮全部通过，两个测试端口关闭，未遗留Nginx进程。该回归没有启动原后台或连接原库，不能当作完整业务验收。

本轮只改自有网关、运行回归和本说明三个文件；此前待审11文件镜像仍保持原提交，不将后续修改加入其既有确认范围。Reference原业务源码、原数据库和原站配置未改。原门户实际二维码指向独立端口的/h5入口，与参考包图片不同；二维码本身和实际内网地址仅在私有验收资料保留，不随本源码提交。手机统一子路径部署的鉴权和真实业务仍需独立验证。
