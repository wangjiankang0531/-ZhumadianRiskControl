"""Record an actual anonymous HTTPS recheck separately from logged-in navigation acceptance."""
from pathlib import Path
import datetime, hashlib, importlib.util, json
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine'
D=R/'Document/Deployment/original_feedback_verified_r891_20261104'
proof=json.loads((V/'public-readonly-static-r892.json').read_bytes())
assert proof['anonymousOnly'] and proof['normalTLSVerification']
expected=[('/zhumadian/',819234,2624898,'3fda69730a678c07a2c83117eae03796f9fd3ef5d34a5928cc578a8c957806df'),('/zhumadian/emergency/',431938,1320116,'8a7dc8a8e80dae2c8001d39676e33749c28bfa49b99f80379f2be94e9302a11f')]
for d,(route,wire,decoded,sha) in zip(proof['results'],expected,strict=True):
    assert d['route']==route and d['htmlStatus']==d['scriptStatus']==200 and d['htmlCacheControl']=='no-store'
    assert d['encoding']=='gzip' and d['cacheControl']=='public, max-age=31536000, immutable' and d['vary']=='Accept-Encoding'
    assert d['wireBytes']==wire and d['decodedBytes']==decoded and d['decodedSHA256']==sha
    assert d['finalOriginMatched'] and not d['authCookiesSent'] and not d['loggedInNavigationOrAPITiming']
proof['recordedAt']=datetime.datetime.now().astimezone().isoformat()
proof['singleSamplePerEntryNotStatisticalLatencyBenchmark']=True
raw=(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode('utf8')
name='anonymous-static-recheck-r892.json'; assert not(D/name).exists(); (D/name).write_bytes(raw)
text='''# 公网静态优化当前复核（R892）

使用正常TLS验证、无Cookie/账号的只读HTTPS，分别从当前两个入口HTML解析实际主脚本，再以Accept-Encoding:gzip读取。两入口HTML HTTP200/no-store；两实际脚本HTTP200/gzip/Vary:Accept-Encoding/一年immutable，解压SHA与已核R45交付一致。无部署、配置或业务写入。

安全端脚本2,624,898→819,234字节，本次完整读取545ms；应急端1,320,116→431,938字节，315ms。HTML单次读取分别779ms/46ms。每项只有一个观察样本，包含客户端网络/连接开销，不是统计基准、服务器处理耗时或页面可交互时间；脚本时间与HTML时间也不可直接当完整页面耗时相加。

当前静态优化确实生效，不能因此宣称首页和所有功能页面已经优化完成。正常登录后导航、图表/列表及业务接口仍待测；本机窗口和进程检查均未见Chrome，没有发送桌面输入或转向其他软件。待用户明确实际浏览器所在环境后继续正常页面只读检查，不通过访问浏览器配置/会话令牌来绕开缺少目标窗口的问题。

任务反馈、主管审批和正常重启链的R891独立验收保持，不等价于公网性能验收。完整单系统南港复刻、真实模板/附件/通知及UE引擎、GIS编辑/标牌/Web3D长期目标继续，fullCloneReady=false。本记录只同步原本地审阅分支，未纳入已批准的153文件公开范围，无新公开推送。
'''
(D/'公网静态复核与待测项_R892.md').write_text(text,encoding='utf8')
files=[]
for rel,value in {'tools/record_static_recheck_r892.py':Path(__file__).read_bytes(),'deploy/verification/anonymous_static_recheck_r892_20261104.json':raw,'deploy/handbook/anonymous_static_recheck_r892_20261104.md':text.encode('utf8')}.items():
    p=A/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value);files.append(rel)
spec=importlib.util.spec_from_file_location('local_r892',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.commit(A,'99503f659c63021e54ed6992b0eae4e682b13b03','review/workplace-r19-live-local-20261031',files,'app-r892',message_override='docs: record live public gzip cache recheck without claiming authenticated timing',update_existing=True)
(D/'local-review-git-r892.json').write_text(json.dumps({'application':a,'publicPushed':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'application':a,'normalAuthenticatedTimingCollected':False}))
