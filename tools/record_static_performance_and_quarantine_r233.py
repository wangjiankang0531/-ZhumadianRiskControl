"""Record observed results and quarantine findings; never restore or execute samples."""
from pathlib import Path
import hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/static_performance_candidate_r229_20261103';Q=R/'Document/Deployment/test_executable_quarantine_r233_20261103'
assert not Q.exists();Q.mkdir(parents=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def dump(p,x):put(p,enc(x))
r230=json.loads((V/'static-transport-r230/verified-result.json').read_text(encoding='utf-8'))
r231=json.loads((V/'static-transport-r231/verified-result.json').read_text(encoding='utf-8'))
r232=json.loads((V/'static-proxy-boundaries-r232/transport/receipt.json').read_text(encoding='utf-8'))
assert r230['passed'] and r231['passed'] and r232['checks']==13
for mode in ['baseline','candidate']:
 for file in ['exit.json','browser-owned-exit.json','browser-terminal.json']:
  value=json.loads((V/'static-transport-r231'/mode/file).read_text(encoding='utf-8'))
  if file=='exit.json':assert value['processExit']==0 and value['ownedActiveProcesses']==0
  if file=='browser-owned-exit.json':assert value['exitCode']==0 and value['ownedActiveProcesses']==0
  if file=='browser-terminal.json':assert value['exitCode']==0 and value['normalBrowserClose']
baseline=R/'Document/Deployment/native_frame_profile_20261103';receipt=json.loads((baseline/'source-receipt.json').read_text(encoding='utf-8'))['sourceSHA256']
archive=baseline/'source-build-inputs.zip';archiveReceipt=json.loads((baseline/'source-archive.json').read_text(encoding='utf-8'));assert sha(archive.read_bytes())==archiveReceipt['SHA256']
names=['XNBYEngine/tests/src/rhi/test_gpu_frame_timing.cpp','Application/tools/test_native_frame_profile_summary.cpp','Application/native/native_frame_profile.hpp','XNBYEngine/rhi/include/hongtu/rhi/GpuFrameTiming.h']
with zipfile.ZipFile(archive) as z:
 inputPins={n:{'bytes':len(z.read(n)),'sha256':sha(z.read(n))}for n in names}
 assert all(p['sha256']==receipt[n] for n,p in inputPins.items())
scope={'generatedTestTools':2,'screenshotAlerts':3,'sameNativePathReportedTwiceIgnoringWindowsPathCase':True,
 'files':[{'name':'cases.exe','originalPath':str(V/'static-proxy-boundaries-r232/cases.exe'),'source':str(V/'static-proxy-boundaries-r232/cases.cs'),'sourceSHA256':sha((V/'static-proxy-boundaries-r232/cases.cs').read_bytes()),'compiler':'Microsoft .NET C# csc.exe','compilerSignatureVerifiedValid':True,'intendedCases':23,'actualCasesExecuted':False,'launchRejectedWithWinError5':True,'binarySHA256BeforeQuarantineAvailable':False,'requiredByDeployedApplication':False},
 {'name':'ht_frame_timing_tests.exe','originalPath':str(R/'work/native_frame_profile_20261103/regression-build/Release/ht_frame_timing_tests.exe'),'compiler':'Microsoft Visual C++ cl.exe','compilerSignatureVerifiedValid':True,'cmakeTargetSourcesVerified':True,'archivedBuildInputPins':inputPins,'unitBuildExitCode':1,'testDiscoveryOperationNotPermittedRecorded':True,'originalExecutableBinaryNotAvailable':True,'currentHeaderHasLaterNormalTraceFieldChanges':True,'reviewUsedOriginalArchivedHeader':True,'requiredByDeployedApplication':False}],
 'assessment':'Likely false positives based on source and build provenance; no final quarantined-binary verdict.',
 'quarantinedSamplesRestored':False,'trustOrExclusionsChanged':False,'antivirusDisabled':False,'samplesUploadedToThirdParty':False,'desktopOperated':False,'publicRuntime':'R36 unchanged','threeDSourceAssetsAndDedicatedCheckpointChanged':False}
dump(Q/'source-and-build-assessment.json',scope)
dump(D/'actual-static-transport-r230.json',r230);dump(D/'actual-anonymous-browser-r231.json',r231)
dump(D/'proxy-boundaries-r232.json',{'original13RealTransportCasesPassed':True,'gzip23UnitChecksExecuted':False,'reason':'360 quarantined cases.exe; process launch WinError5. No restore or whitelist.'})
report='''# 两种临时测试程序的360隔离核查（2026-11-03）

结论：截图三条告警涉及两种自建测试工具，来源和已审阅源码支持“疑似误报”，不是杀毒厂商已经确认的误报结论。隔离样本未提取，两个EXE的隔离前逐字节身份未核实，不能宣称已完成二进制取证或整机无病毒。

cases.exe：本轮B/S静态压缩测试临时生成。入口仅调用23个gzip协商/静态路径判断断言；编译时包含既有ASP.NET代理类，类含HTTP/WebSocket转发实现，但该测试入口不调用转发入口。微软C#编译器签名有效。生成后启动WinError5，随后原路径无文件，与用户13:04:09隔离截图相符。原13项代理真实传输检查已通过；这23项单独检查没有执行，不能记通过。

ht_frame_timing_tests.exe：补充两图同为work/native_frame_profile_20261103/regression-build/Release下目标，03:29:46和03:30:16为两通道记录。CMake明确编译GPU时间换算和NativeFrameSummary两份GoogleTest源，内容为时钟回绕/数值有效性/均值分位数/1024窗口校验。MSVC编译器签名有效，既有构建日志记录测试发现阶段operation not permitted、退出1；与隔离时间吻合。四份原始输入从已封存源码ZIP只读核SHA，与原source-receipt完全一致。当前临时头文件07:50已增加正常GPU原始计时追踪字段，不能拿它直接冒充03:29构建原稿，本核查采用封存原稿；未改三维源码、资产或另一会话断点。

两个文件都是可重建验证工具，公网R36和日常三维运行不依赖它们。当前不需要从隔离区恢复，保留隔离与防护即可。未更改信任区/排除项，未关闭杀毒，未上传内部源码/样本到任何第三方；未操作桌面。若后续必须取得杀毒厂商正式意见，应另作最小样本范围审阅，再走360官方样本复核；不为完成测试而改名重编、改后缀或绕过隔离。

360官方常见问题说明可疑或疑似误报样本可提交其样本复核入口：https://sd.360.cn/faq.html 。本轮未提交。

性能优化状态：实际Nginx+ASP.NET处理器18种请求各对照通过、原13项传输回归通过、隔离Chrome两入口冷暖登录页通过；这不等于真实IIS/公网登录后业务加载验收。公网仍R36，性能候选尚未发布。
'''
put(Q/'核查说明.md',report.encode())
perf='''# 首页及模块静态加载优化：本地传输和浏览器验证

公网只读基线：两个主JS2624898/2575860字节，CSS869689/868546字节，Accept-Encoding:gzip仍未压缩且no-store。使用精确R36安全836/应急340静态文件只读验证，无业务库/真实账号。

候选同时修正Nginx压缩/成功哈希资源缓存与ASP.NET对静态GET/HEAD的gzip协商及Vary转发，HTML、接口、非哈希资源及错误维持不长期缓存。真实Nginx语法、ASP.NET HttpWebRequest到Nginx的18种请求前后对照通过，解压后的HTML/JS/CSS/API字节相同；JSON原南港标记、合成鉴权/Cookie保持，两个Nginx正常退出且自有后代零。

主JS传输降为819234/806701B（减少68.79%/68.68%），CSS126860/126553B（减少85.41%/85.43%）。独立Chrome固定10Mbps/60ms场景，匿名登录表单冷打开由3308/3265ms变为1289/1219ms，暖打开由3230/3186ms变为250/140ms；暖请求8个静态资源命中磁盘缓存、静态网络体积零，两轮无JS运行时异常。外部alicdn字体在两组同样阻止，此对照不是公网用户完整首次登录/工作台/模块接口加载成绩，不可直接推广为公网提速承诺。

代理原13项大响应、PUT/PATCH/DELETE/HEAD/OPTIONS、拒绝、Range、越界/Host/方法/WebSocket边界回归实际通过。单独23项gzip/路由检查编译后被360隔离，未启动、不计通过、不恢复或加白，详见Deployment/test_executable_quarantine_r233_20261103。已有R230/R231真实gzip与q=0/通配/HEAD/查询串验证结果不因此改写。

实际IIS集成、最终固定更新包完整预检/恢复、真实公网登录后首页及模块计时尚待；公网仍R36，未改变真实Jar、鉴权、数据库、配置、上传、IIS或前端。需继续准备最小静态性能更新并上线前核验，桌面操作仍先交接。
'''
put(D/'本地验证与360隔离说明.md',perf.encode());put(A/'deploy/handbook/static_performance_and_quarantine_r233_20261103.md',(perf+'\n'+report).encode())
proof={'staticTransport':r230,'browser':r231,'quarantine':scope,'publicDeployed':False,'finalPackagePrepared':False,'fullCloneReady':False}
dump(A/'deploy/verification/static_performance_and_quarantine_r233_20261103.json',proof)
put(R/'Document/Engine/project/静态加载优化与临时测试隔离_20261103.md',(perf+'\n'+report).encode())
entry='''## 2026-11-03 R229—R233：静态传输/冷暖登录对照通过，两种临时测试EXE隔离不恢复

精确R36安全836/应急340静态源，真实Nginx+ASP.NET处理器18请求各对照通过、解压内容一致；JS减少68.7%左右/CSS85.4%左右，成功哈希资源缓存，HTML/API/错误不长期缓存。Chrome固定10Mbps/60ms匿名登录冷约3.3→1.2—1.3s、暖约3.2→0.14—0.25s，8静态缓存命中；不是公网登录后业务成绩。原13代理传输回归通过。23单独边界EXE cases.exe启动WinError5被360隔离，未执行不能算通过；用户另两图为同一ht_frame_timing_tests.exe两通道告警，CMake/原封存源码SHA及03:29构建拒绝可对上。源码/生成过程支持疑似误报，未取得隔离二进制不宣称最终鉴定，均为可重建测试工具不需恢复；未改信任/排除/杀毒设置，未上传样本，不绕过隔离。证据Deployment/static_performance_candidate_r229_20261103及test_executable_quarantine_r233_20261103。公网仍R36/性能未发布、桌面未操作；原计划/演练候选待验。完整目标active/fullCloneReady=false，另一三维专属断点、8767/资产和正式18891保持。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
 old=p.read_bytes();assert not old.startswith(entry.encode());put(p,entry.encode()+old)
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
dump(Q/'recording-result.json',{'recorded':True,'restoredOrWhitelisted':False,'newPublicDeploymentOrGit':False})
print(json.dumps({'recorded':True,'twoTestProgramsThreeAlerts':True,'noRestoreOrWhitelist':True,'publicR36Unchanged':True}))
