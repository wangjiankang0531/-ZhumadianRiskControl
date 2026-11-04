"""Retain measured public bottlenecks and verified local lossless candidate; local Git only."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,subprocess,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine'
S=V/'performance-assets-r893';C=S/'candidate-r900';W=R/'work/ha902'
D=R/'Document/Deployment/home_transfer_candidate_r903_20261104';assert not D.exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
built=J(S/'lossless-candidate-r900.json');test=J(W/'gateway-result.json');browser=J(W/'browser-r896/result.json')
assert built['passed'] and built['image']['originalICCProfilePreserved'] and built['image']['rgbaPixelsIdentical']
assert test['passed'] and test['browserPassed'] and len(test['renderComparisons'])==3 and all(c['allPixelsIdentical'] for c in test['renderComparisons'])
assert browser['passed'] and len(browser['rows'])==6 and browser['fixtureDOM'] and not browser['originalSDKAccepted']
assert test['normalOwnNginxQuitRequested'] and all(t['exitCode']==0 and t['actualJobDescendantsZero'] and not t['forceTerminationUsed']for t in test['terminals'].values())
assert all(sha(C/n)==p['sha256'] and (C/n).stat().st_size==p['bytes']for n,p in built['files'].items())
current=[r for r in browser['requests']if r['phase'].startswith('candidate-')]
assert not any(r['path'].endswith('.ttf')or'background-BHYqFd8n.png'in r['path']for r in current)
for suffix in ['.webp','.woff2']:
    rows=[r for r in current if r['path'].endswith(suffix)]
    assert len(rows)==3 and not rows[0]['cached'] and all(r['cached']for r in rows[1:])
    assert all(r['cacheControl']=='public, max-age=31536000, immutable' and r['status']==200 for r in rows)
sources=['build_home_transfer_assets_r894.py','verify_lossless_home_assets_r896.mjs','run_home_asset_gateway_r896.py','record_home_transfer_candidate_r903.py']
for n in sources:
    if n.endswith('.py'):ast.parse((V/n).read_bytes(),filename=n)
assert subprocess.run(['node','--check',str(V/'verify_lossless_home_assets_r896.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
measured={'schema':'xnby.public-authenticated-manual-network-observations.v1','source':'observed native Computer Use screenshots of local user Chrome; no HAR/response/cookie export',
 'browserZoomPercent':90,'devToolsDocked':True,'networkThrottling':'No throttling','singleSamplePerCondition':True,
 'homepageCacheDisabled':{'requestsFinishSeconds':12.95,'DOMContentLoadedSeconds':1.93,'loadEventSeconds':1.93,'transferredApproxMB':8.0,'backgroundDisplayedKB':4864,'backgroundSeconds':9.84,'fontDisplayedKB':1419,'fontSeconds':5.50},
 'homepageCacheEnabled':{'requestsFinishSeconds':5.67,'DOMContentLoadedSeconds':2.61,'loadEventSeconds':2.61,'transferredApproxMB':1.6,'mainScriptAndMostImagesHitMemoryCache':True,'fontDisplayedKB':1416,'fontSeconds':2.42},
 'emergencyHomeExistingCache':{'requestsFinishSeconds':1.62,'DOMContentLoadedMs':772,'loadEventMs':787,'currentUserMs':423,'mainScriptsHitDiskCache':True,'favicon404Observed':True},
 'eventListFirstEntry':{'listAPISeconds':1.28,'dictionaryAPIsMs':[368,364,364],'smallChunkObservedRangeMs':[677,1130],'businessListReadOnly':True},
 'responsePageNotAcceptedBecauseComputerUseURLConfidenceStop':True,'desktopReturned':True,'cacheEnabledLeftForNormalBrowsing':True,
 'DOMLoadNotEquivalentToInteractiveOrAllRequestsFinished':True,'productionBusinessWrites':0,'rawUserNameBusinessRowsHeadersOrTokensRetained':False}
faults=[{'stage':'R894','finding':'Initial font verifier incorrectly required the mandatory WOFF2 head flag to be byte-identical; exact bit11/checksum normalization now checked against W3C.'},
 {'stage':'R895/R899','finding':'Image decoded RGBA matched but original ICC metadata had been dropped; browser colors differed. Final candidate retains original ICC and EXIF.'},
 {'stage':'R896','finding':'Nginx preflight refused missing owned logs/temp parents before server launch.'},
 {'stage':'R897/R898','finding':'Probe read an existing but empty PID file too early; normal -s quit later succeeded, fresh process references zero. Original Job handles were no longer held; no actual-Job-zero claim for these two recovery runs.'},
 {'stage':'R899','finding':'Fetch interception altered cache behavior and FontFaceSet.load explicitly fetched an unused old face; original candidate acceptance rejected.'},
 {'stage':'R900','finding':'Overbroad test-only DNS rule refused loopback navigation; browser/Nginx exited normally.'},
 {'stage':'R901','finding':'FontFaceSet.check covered an unused overlapping original face; test now observes the loaded face actually used by layout.'}]
proof={'schema':'xnby.home-transfer-candidate.v1','recordedAt':datetime.datetime.now().astimezone().isoformat(),'previousGoalTurnClassification':'progress',
 'previousTurnEvidence':'normal task feedback chain independently accepted and public authenticated Network observations changed next action',
 'publicMeasurement':measured,'candidate':built,'gatewayAndRender':test,'failuresPreserved':faults,
 'fourFileCandidateOnly':True,'candidateFiles':built['files'],'payloadLogicalBytes':sum(p['bytes'] for p in built['files'].values()),
 'fullOriginalApplicationAndSDKCandidateAcceptance':False,'fullReleaseManifestAndSparseTransportPrepared':False,'publicDeployed':False,'publicGitPushed':False,
 'lastKnownPublicRelease':'R45','actualPublicOwnerAndReleaseMustBeRefreshedBeforeNextDeployment':True,
 'sourceReviewPins':{n:sha(V/n)for n in sources},'fullCloneReady':False}
text='''# 首页背景、字体与加载优化候选：R903阶段记录

本阶段已形成4文件静态候选并通过实际Nginx/浏览器呈现验证，尚未接入完整原SDK应用测试，也未打包或部署公网。完整引擎UE效果/效率、EXE GIS点线面图层/多源空间标牌、Web3D和单系统南港B/S目标继续active。

## 本机Chrome的真实公网观察

原生工具先未发现Chrome，用户说明本机后重新观察到了新窗口，核实已登录首页才操作。Chrome缩放90%、开发者工具停靠右侧、No throttling；初始Disable cache已勾选。禁用缓存刷新：Network Finish12.95s、DCL/Load1.93s，背景约4.86MB/9.84s，字体约1.42MB/5.50s。取消禁用缓存后刷新：Finish5.67s、DCL/Load2.61s，主脚本和多数图片已缓存，字体仍传输约1.42MB/2.42s。每条件单样本，Finish、Load和可交互不是同一指标，不能当稳定均值或直接相加。

应急首页已有缓存：DCL772ms、Load787ms、Finish1.62s，身份接口423ms，脚本磁盘缓存命中；仍观察到favicon.ico 404。应急事件列表首进：列表接口1.28s、三字典接口约364—368ms，多份小块约677—1130ms。未复制姓名或业务行、令牌/账号/响应原文；未提交业务。继续应急响应时工具因URL识别置信度自动停止并交还桌面，未把该页计为通过。停止时正常缓存开启，DevTools尚未关闭。

随后匿名正常TLS HEAD核字体返回no-store、背景返回一年immutable，确认旧TTF未被当前静态缓存规则覆盖。当前R45脚本压缩缓存仍生效，不代表全部页面优化完成。

## 本地候选及已通过的范围

原3840×2160背景PNG4,854,984B→WebP2,591,292B；所有RGBA像素、原ICC和EXIF保留。原完整字体TTF1,414,784B→WOFF2 745,328B，保留7194字形、全部字符映射和字形顺序。原11表逐字核对，仅按WOFF2规范允许head校验和与强制bit11变化；未做字符裁剪。字体使用font-display:swap。

只向精确R45首页HTML增加一个样式链接，新增带内容哈希的CSS/WebP/WOFF2三资源。原JS、原CSS、菜单、鉴权、数据库和三维源码未修改；旧资源保留供其他页面引用。源文件与候选逐SHA固定。

独立回环端口使用原Nginx程序及实际R45静态处理源码；页面为明确的静态DOM夹具，原编译CSS保持，非业务/SDK替身验收。原图/原字体与候选在1366×768、1920×1080、3840×2160三种分辨率渲染逐像素一致；实际MIME为image/webp、font/woff2，成功响应一年immutable，后两次导航命中缓存。候选不再请求旧大PNG/TTF。浏览器、Node/Nginx包装进程均正常0，两个真实Job后代0，不强杀。

初版丢ICC导致色差、测试主动加载未使用字体、请求拦截影响缓存、空PID过早读取等失败均保留。R897/R898在父验证器已退出后才正常停自有Nginx，只有正常quit和后续零进程引用证据，不补造已丢失Job句柄的零后代证明；R899—R902的实际终态另有保存。R903不把这些失败改成全部通过。

## 下一步与发布边界

先在完整原应用中用合成普通角色验证登录、首页/模块导航、实际资源请求和正常退出，完成版本/文件清单与恢复验证，再准备固定公网更新。发布前重新发现实际公网归属/版本、三维路由和文件差异，不套旧R45或j2的进程状态；本轮没有公网变更或三维接入发布。字典请求、小脚本首进和列表API继续分别测量，不对登录态或业务列表设置公共缓存。

本记录和源码只追加原本地审阅分支，未包含在已批准的153文件公开范围内，没有新公开push。不宣称完整南港模板/全部B/S验收，亦不宣称公开干净检出一键构建。当前候选依赖既有固定输入及隔离的Pillow13.0.0/fontTools4.68.0/Brotli1.2.1，轮子来自PyPI，逐SHA记录，未全局安装。原pip下载等待后已取消；没有恢复或信任360隔离文件、没有新原生EXE构建。

参考：[WOFF2规范](https://www.w3.org/TR/WOFF2/)、[fontTools WOFF2接口](https://fonttools.readthedocs.io/en/stable/ttLib/woff2.html)、[Pillow格式说明](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)。
'''
D.mkdir();(D/'candidate-and-observations.json').write_bytes(enc(proof));(D/'公网实测与首页资源候选.md').write_text(text,encoding='utf8')
for name,path in [('lossless-candidate-r900.json',S/'lossless-candidate-r900.json'),('actual-gateway-render-r902.json',W/'gateway-result.json'),('dependency-receipt.json',S/'dependency-receipt.json')]:
    (D/name).write_bytes(path.read_bytes())
files=[]
for n in sources:
    rel='tools/'+n;p=A/rel;assert not p.exists();p.write_bytes((V/n).read_bytes());files.append(rel)
for rel,raw in {'deploy/verification/home_transfer_candidate_r903_20261104.json':enc(proof),'deploy/handbook/home_transfer_candidate_r903_20261104.md':text.encode('utf8')}.items():
    p=A/rel;assert not p.exists();p.write_bytes(raw);files.append(rel)
header='## 2026-11-04 R903：首页真实网络耗时已取得；无损资源三分辨率/实际缓存通过\n\n'
body='本机原生Chrome实际登录：首页禁用缓存Finish12.95s，正常缓存5.67s；旧背景4.86MB/9.84s、TTF1.42MB/5.50s，暖TTF仍2.42s；应急首页Load787ms/Finish1.62s，事件列表API1.28s。单样本/DevTools停靠/非统一交互时间；响应页URL策略结束未验，正常缓存开启且桌面已交还。匿名HEAD确认TTF no-store。新候选只HTML+CSS/WebP/完整WOFF2四文件，背景4854984→2591292B、字体1414784→745328B；7194字形/全映射保持，ICC/EXIF保留。实际原Nginx缓存/MIME与1366/1920/3840像素全同，候选零旧大图/TTF；最终浏览器/Node/Nginx0/真实Job零。明确静态DOM夹具，非完整原SDK/公网验收。保全部失败和两次早读空PID后的正常quit，非全部历史正常。下一完整应用普通角色/正常生命周期及固定运输恢复；最新回调仍after-submit-r889/441a3970，不重发业务。只原本地Git，无新公网/公开push/三维改动。完整UE/EXE GIS图层多源标牌/Web3D/单系统南港active/fullCloneReady=false。\n\n'
rel='docs/project/首页网络实测与无损候选_20261104_r903.md';assert not(E/rel).exists();(E/rel).write_bytes((header+body).encode('utf8'))
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
    p.write_bytes((header+body).encode('utf8')+p.read_bytes())
with(R/'Document/Engine/showcase_demo_completion.md').open('ab')as f:f.write(('\n'+header+body).encode('utf8'))
spec=importlib.util.spec_from_file_location('local_r903',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.commit(A,'977a2b536c30573d15453abcf33d925813a57752','review/workplace-r19-live-local-20261031',files,'app-r903',message_override='perf: prepare pixel-identical cached navigation image and complete WOFF2 font',update_existing=True)
e=h.commit(E,'fbb841cf9c1b815bf9d5ba75fb31848063e3d291','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r903',message_override='docs: retain public authenticated bottlenecks and lossless candidate acceptance limits',update_existing=True)
(D/'local-review-git-r903.json').write_bytes(enc({'application':a,'engine':e,'publicPushed':False}))
print(json.dumps({'passed':True,'application':a,'engine':e,'publicDeployed':False,'fullOriginalSDKCandidatePending':True}))
