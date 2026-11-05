from pathlib import Path
import json,hashlib,datetime
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/ledger_original_ui_r940_20261104'
J=lambda p:json.loads(p.read_bytes())
rows=[]
for n in [941,946,948]:
 p=R/f'work/ledgerfull-r{n}/verified-ledger-ui-r{n}.json';s=J(p);assert not s['passed'] and s['codeRestored'] and s['privateConfigurationUnchanged'] and s['originalCurrentPointerRestored']
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values()) for t in s['terminals'])
 browser=J(R/f'work/ledger-browser-r{n}/first-start/result.json');assert J(R/f'work/ledger-browser-r{n}/first-start/browser-terminal.json')['normalBrowserClosed']
 rows.append({'revision':n,'passed':False,'failedStage':browser['stage'],'type':browser['type'],'cases':browser['cases'],'generationRequests':browser['generationRequests'],'normalSixComponentAndBrowserExitVerified':True,'codePrivateConfigurationAndPointerRestored':True})
assert rows[0]['generationRequests']==rows[1]['generationRequests']==0 and rows[2]['generationRequests']==1
proof=J(V/'ledger_root_r948/route-deduplication-proof-r948.json');assert proof['passed']
out={'at':datetime.datetime.now().astimezone().isoformat(),'attempts':rows,'routeCause':'own synthetic fixture duplicated existing root path; original converter skips second whole branch','actualCompiledRouteConversionReproduced':True,'onlyOneOwnMetadataPathCorrected':True,'originalAuthRouterAndProductUnchanged':True,'actualNormalNativeLedgerButtonGeneratedOnce':True,'cancelGeneratedNothing':True,'actualDetailPDFCanvasRendered':True,'originalDownloadDOMClickTimedOutAndCauseStillUnderTest':True,'nextR950ReusesOnlySameRecordAndPDFReadOnly':True,'nextR950TerminalOrPassedNotYetClaimed':True,'publicR47PreflightResultStillNotReceived':True,'publicOrDesktopUsed':False,'fullCloneReady':False}
p=D/'partial-ledger-r951.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note='''# 原台账督办 UI 联测阶段记录 R951

完整R47候选在自有G原六组件/原鉴权与普通非管理员登录下运行。R941/R946先后在台账路由404处失败；两轮登录/CurrentUser成功、业务创建和督办请求均为零。实测CurrentUser菜单显示本轮新增测试根与既有根重复`/hiddenInvestigate`；从实际编译前端提取原路由转换函数执行，证实会跳过第二个同路径整分支。R948只将本轮新增合成根的一项路径改为唯一值；不修改原路由/鉴权代码、不改变账号角色、其他既有元数据和表结构。

纠正后R948原台账搜索、取消督办零生成、确认一次原addPdf、成功后按钮禁用和原详情PDF canvas渲染共5项通过。只创建一条明确标记的本地合成台账和一份督办PDF，精确实体/日志/操作者和文件SHA已保存在私有journal，后续不得重建或重发督办。总测试仍false：脚本DOM点击原下载按钮后未观察到下载事件，未直接归因为产品缺陷。R950已准备并开始只读续验同一记录/PDF，改为实际浏览器输入点击可见按钮；尚未宣称终态或通过。

R941/R946/R948的原六组件和控制器均正常0、真实Job零，浏览器正常关闭；本轮各自代码/私有配置/运行指针前像均已恢复。失败和已提交的自有元数据/台账/PDF/journal均保留，不重放未知提交。本轮未修改数据库字段、索引、状态模型或业务归属规则，不需要生成新的物理结构；仅隔离测试元数据和正常原业务操作。公网R47只完成上传回读、预检结果仍待；不操作桌面或公网业务、不将本轮新源码自动扩入已完成的193文件公开范围。完整南港/真实IIS及角色验收仍待。
'''
p=D/'原台账督办联测阶段记录_r951.md';assert not p.exists();p.write_text(note,encoding='utf8')
print(json.dumps({'recorded':True,'attempts':3,'actualGeneratedOnceAndCanvasVerified':True,'downloadStillUnderTest':True}))
