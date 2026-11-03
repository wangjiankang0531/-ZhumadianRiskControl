from pathlib import Path
import ast,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent;D=R/'Document/Deployment/public_test_static_performance_r37_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
prep=J(D/'preparation-result.json');assert J(D/'independent-fixed-delivery-verification.json')['passed']and J(D/'full-program-preflight.json')['allPassed']
validation=A/'tools/frontend/static_performance_r229/validation';validation.mkdir(exist_ok=True)
sources=['measure_public_initial_resources_r228.py','verify_static_transport_r230.py','measure_static_browser_r231.mjs','prepare_static_browser_r231.py','verify_static_transport_r231.py','verify_static_proxy_boundaries_r232.py']
staged=[]
for name in sources:
 p=validation/name;assert not p.exists();put(p,(V/name).read_bytes());staged.append(p.relative_to(A).as_posix())
for name in ['prepare_static_performance_updater_r234.py','prepare_static_performance_sparse_r235.py','verify_static_performance_full_program_r236.py','build_static_performance_delivery_r237.py','verify_static_delivery_r238.py','record_static_performance_candidate_r239.py']:
 p=T/name;assert not p.exists();put(p,(V/name).read_bytes());ast.parse(p.read_bytes());staged.append(p.relative_to(A).as_posix())
staged.extend(['tools/original_project_branding_r229.py','tools/frontend/static_performance_r229/XnbyReferenceProxy.cs','tools/prepare_static_performance_r229.py','tools/original_public_test_update_r37_static_20261103.py'])
proofs={
 'public_static_baseline_r228_20261103.json':R/'Document/Deployment/initial_load_performance_r228_20261103/public-static-baseline.json',
 'static_transport_r230_20261103.json':R/'Document/Deployment/static_performance_candidate_r229_20261103/actual-static-transport-r230.json',
 'static_anonymous_browser_r231_20261103.json':R/'Document/Deployment/static_performance_candidate_r229_20261103/actual-anonymous-browser-r231.json',
 'static_quarantined_test_limit_r232_20261103.json':R/'Document/Deployment/static_performance_candidate_r229_20261103/proxy-boundaries-r232.json',
 'static_r37_updater_preparation_20261103.json':D/'updater-preparation.json',
 'static_r37_composition_recovery_20261103.json':D/'composition-and-recovery.json',
 'static_r37_composition_negative_cases_20261103.json':D/'composition-negative-cases.json',
 'static_r37_full_program_preflight_20261103.json':D/'full-program-preflight.json',
 'static_r37_fixed_delivery_verification_20261103.json':D/'independent-fixed-delivery-verification.json',
 'static_r37_response_checker_cases_20261103.json':D/'response-checker-cases.json',
 'static_r37_fixed_delivery_manifest_20261103.json':D/'delivery-manifest.json',
}
for name,p in proofs.items():
 target=A/'deploy/verification'/name;assert not target.exists();put(target,p.read_bytes());json.loads(target.read_bytes());staged.append(target.relative_to(A).as_posix())
manifest=J(D/'delivery-manifest.json')
text=f'''# R37 首页及模块静态加载优化固定候选

截至本记录，公网仍R36，R37未上传/安装，桌面未接管。性能优先不改变完整南港B/S复刻目标；预案/演练原映射和14源码候选仍独立待验，不夹入本包。

## 改动与范围

两个入口及其哈希命名静态JS/CSS/图片/字体启用gzip协商与长期缓存；ASP.NET仅向静态GET/HEAD转发可接受的gzip并保留编码字节及Vary。HTML保持no-store，业务接口不增加长期缓存。只替换六路径：tools/original_project_branding.py、deploy/iis_original/App_Code/XnbyReferenceProxy.cs、iis/App_Code/XnbyReferenceProxy.cs、tools/original_public_test_update.py、payload-manifest.json（原字节）及release-manifest.json。实际IIS代理源码从此加入固定控制清单；IIS站点映射/配置和其余站点保持。

全部业务Jar/类、两前端836+340原文件、鉴权/原生会话/异步/任务物资队伍/独立历史意见、真实配置、数据库、上传及11份就绪保持。正常停启原六组件，失败仅按本次updateId和前后SHA/新备份恢复，进程退出归属不明停止、不强杀。不自动写公网测试业务或读取凭据/令牌/账号会话表/业务行/原日志。

## 已取得证据

精确R36静态源核SHA；真实Nginx+ASP.NET处理器每组18请求对照，解压后内容一致。主JS2624898→819234B、2575860→806701B，CSS869689→126860B、868546→126553B。固定10Mbps/60ms的独立Chrome匿名登录冷约3.3→1.2—1.3s、暖约3.2→0.14—0.25s，八静态缓存命中、无JS运行时异常。两组同样阻止外部alicdn字体；这些不是公网登录后工作台/模块/业务API的实测承诺。

原代理13项真实传输回归通过。独立23项gzip/路由断言EXE被360隔离、未执行、不计通过、不恢复/加白；原R230/R231实际压缩、q=0及冷暖证据保持。31组合拒绝、8文件正常/故障恢复、无关IIS漂移拒绝；完整15557程序和保留依赖/21旧22新控制、原预算及六项完整预检通过。最终包装器真实解包和预算先于服务的顺序通过，身份/健康为明确测试替身，完整load_bundle另已真实执行；28响应校验器合成样例通过。原正常停/启/备份/替换/恢复函数AST与已实际六组件运行的R36完全相同，apply_update仅增加准确IIS文件变更回执赋值；不宣称新更新器整文件另跑过六组件生命周期。

## 固定发布与后续核验

8运输文件、{prep['transportBytes']}字节，清单SHA256 {prep['manifestSHA256']}。目标FTP /Zhumadian/Zhumadian_Static_Performance_20261103_R37/，应用C:/inetpub/wwwroot/Zhumadian/Application。新release {manifest['newReleaseSHA256']}；新updater {manifest['newUpdaterSHA256']}。仅精确R36预检通过后执行。真实公网身份/11就绪/预算、实际IIS集成、外网TLS与正常登录后首页/模块计时仍待；安装器额外核Nginx及真实本机IIS TLS的gzip、q=0、缓存头、四资源解压SHA及两HTML no-store。

上线后同一浏览器先正常打开首页和模块，再正常刷新/再次进入比较；暖缓存测试不要用强制刷新。新前端版本依靠编译哈希更新；将来若修改同一哈希资源上的品牌替换规则，必须同步更新资源版本URL并核新版本，不能只在旧immutable地址下改响应内容。原HTML不长缓存以便发现新版本。

若公网完整核验通过，再按用户“只留最新”要求核精确旧清单、已停无引用/无重解析，清退役R36运输包和本轮旧代码副本，保留全部数据/上传/配置。桌面操作先交接，焦点变化即停。此固定候选不含新的公开Git或腾讯回填。

## 源码与结论边界

validation目录为实际执行源的归档，运行时应复制到独立新工作目录并按先后顺序执行，不在源码目录盲目重跑；历史路径/失败和自有临时目录记录保留。完整公开干净检出一键构建及全南港功能验收尚未完成，fullCloneReady=false。不会把被360隔离的测试EXE、实际配置/数据库/资产/Reference/截图/原日志或held三维改动打包外发。
'''
put(D/'固定候选说明.md',text.encode());target=A/'deploy/handbook/static_performance_r37_candidate_20261103.md';put(target,text.encode());staged.append(target.relative_to(A).as_posix())
eng='''# R37静态加载优化候选进展（2026-11-03）

一套系统的综合入口/快捷入口共用静态交付：已固定gzip及哈希资源缓存、IIS代理协商候选。原业务/前端/鉴权/历史意见/数据保持，六安装路径零移除；31组合拒绝/8恢复/15557完整程序预检、真实Nginx+ASP.NET每组18请求、Chrome两入口匿名冷暖通过。控制10Mbps/60ms冷约3.3→1.2—1.3s、暖约3.2→0.14—0.25s，不等于公网登录后业务成绩。原13代理传输通过；23单独测试EXE隔离未运行，不恢复或加白。

公网仍R36，R37未部署，真实IIS及外网正常登录/工作台模块计时待验。新更新器原停/启/备份/恢复函数AST保持，未独立重跑整文件六组件。预案映射/14源码候选独立待验。完整UE效果效率引擎/EXE GIS DLG标绘图层与旗杆多源标牌/Web3D/全南港B/S目标active/fullCloneReady=false；单系统去重业务分母仍待闭合，旧60/75估值不恢复。另一三维专属断点、8767、资产和正式18891保持。
'''
put(R/'Document/Engine/project/静态加载优化R37候选_20261103.md',eng.encode())
entry='''## 2026-11-03 R234—R239：静态性能R37固定六路径候选，完整预检/恢复通过待桌面交接

固定8文件573275B/manifest1bf56d75d5edb8b12dd82831ea863fde1e03dfaefa8ef2b37f5f471575baa1b4，R36→R37仅六静态控制/清单路径、零前端/后端/数据改动，实际IIS代理源码加入22控制。31拒绝/8恢复/15557完整程序、真实包装器预算先于服务及28响应校验器样例通过；原13代理与R230/R231真实压缩和匿名冷暖证据保持，隔离23测试不计通过。原停启/备份/替换/恢复函数AST保持，apply仅增加IIS文件回执；新整文件未独立六组件生命周期，真实公网IIS/TLS/正常登录后业务耗时待验。公网仍R36，未上传/桌面未接管；候选含安装后真实Nginx与IIS TLS编码/缓存/解压SHA核验。后台准备源码/说明，旧42公开完成不覆盖本新范围。完整目标active/fullCloneReady=false，原预案/演练候选待验，另一三维专属断点、8767/资产/正式18891保持。详Deployment/public_test_static_performance_r37_20261103。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
put(D/'local-stage-files.json',enc({'application':staged,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/project/静态加载优化R37候选_20261103.md','docs/showcase_demo_completion.md']}));print(json.dumps({'recorded':True,'applicationFiles':len(staged),'engineFiles':4,'newPublicOrDesktopOperation':False}))
