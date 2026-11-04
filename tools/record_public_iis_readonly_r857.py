"""Record this authorized read-only IIS check and anonymous static GETs; local Git only."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine'
D=R/'Document/Deployment/public_iis_readonly_r857_20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')

def main():
 assert not D.exists()
 p=json.loads((V/'public-performance-recheck-r856/result.json').read_bytes())
 assert p['completed'] and p['anonymousOnly'] and p['requests']==6 and not p['publicChanged']
 assert all(x['httpStatus']==200 for x in p['rows'])
 scripts=[x for x in p['rows']if x['label'].endswith('-js')]
 assert len(scripts)==4 and all(x['headers']['Content-Encoding']is None and x['headers']['Cache-Control']=='no-store'for x in scripts)
 r45=R/'Document/Deployment/public_test_original_bootstrap_r45_20261104'
 assert sha(r45/'delivery-manifest.json')=='1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876'
 assert json.loads((r45/'verified-stage-r855.json').read_bytes())['passed']
 held=sha(A/'native/main.cpp');D.mkdir()
 observation={'observedAtLocal':datetime.datetime.now().astimezone().isoformat(),
  'userAuthorizedReadOnlyHandoff':True,'method':'native Computer Use @oai/sky returned unique public RDP window',
  'applicationPath':'C:/inetpub/wwwroot/Zhumadian/Application/iis',
  'handler':{'name':'XnbyOriginalProject','path':'*','type':'XnbyReferenceProxy','enabled':True,'local':True},
  'staticCompressionCheckboxChecked':True,'dynamicCompressionCheckboxDisabled':True,
  'dynamicCompressionMissingComponentWarningVisible':True,
  'customHeadersVisible':[{'name':'X-Powered-By','value':'ASP.NET','inherited':True}],
  'keepAliveChecked':True,'expireWebContentChecked':False,
  'basicSettingsAndCommonHeadersDialogsCancelled':True,'configurationApplied':False,
  'publicDeployOrStopStartOrBusinessWrite':False,'desktopReturnedToUser':True,
  'exactServerReleaseOrProxyFileSHARead':False,'uniqueRootCauseClaimed':False}
 (D/'iis-observation.json').write_bytes(enc(observation))
 (D/'public-static-get-r856.json').write_bytes(enc(p))
 (D/'recorder-r855-first-attempt.json').write_bytes(enc({'failed':True,'type':'UnicodeDecodeError',
  'stage':'process_reference_output_decode_before_cleanup_or_project_writes',
  'correction':'explicit UTF8 PowerShell stdout; no process command line persisted',
  'subsequentR855Completed':True}))
 doc='''# 公网加载优化只读核查：仍未完成验收

2026-11-04，用户明确交接只读后，用原生Computer Use查看已打开的101.201.65.94远程桌面，未部署、停服或保存配置，结束后已交还鼠标键盘。

IIS驻马店应用指向C:/inetpub/wwwroot/Zhumadian/Application/iis；本地XnbyOriginalProject以路径*交给XnbyReferenceProxy，状态已启用。静态压缩勾选，动态压缩灰色并有缺组件提示。可见自定义响应头仅继承X-Powered-By:ASP.NET；保持HTTP连接勾选，内容过期选项未勾选。两设置对话框都取消退出。没有读服务器精确发布清单或代理源码SHA，不能由界面推断精确版本，也不能将未压缩唯一归因动态压缩模块缺失。

桌面交还后，在后台发出6次匿名HTTPS GET，正常校验证书，不发送Cookie/认证、额外no-cache头或业务请求；仅保存公开静态响应的状态、大小、耗时和SHA。两HTML当场解析入口，不猜版本。安全端主脚本2,624,898字节，首次2.7493秒、重复3.7952秒；应急主脚本2,575,860字节，首次6.0860秒、重复6.3914秒。四次均HTTP200、无Content-Encoding、Cache-Control:no-store、无ETag/Vary，重复仍完整下载且SHA相同。首页HTML本次1.9409秒，应急HTML0.0779秒。网络有波动，以上不是整页可操作、浏览器暖缓存或登录后API耗时，不相加推算页面总时长。

因此公网关键静态压缩和可复用缓存仍没有验收通过。当前映射是托管代理，IIS静态压缩勾选不等于最终代理响应已压缩；下一要核实际代理/网关的响应，而不是直接给整个站点或业务接口设置长期缓存。带哈希静态JS/CSS才使用长期缓存；HTML入口与登录状态/业务API保持各自更新和鉴权策略。

固定R45现已完成本地真实原发布后端兼容、13项正常页面、10次实际网关GET、两基线完整代码正常/故障恢复和17项运输验证。8文件2,333,477字节，清单SHA256：1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876；目录Document/Deployment/public_test_original_bootstrap_r45_20261104。安全端网关gzip约0.82MB，应急新主脚本gzip约0.43MB，均解压SHA相同；这是本地候选证据，不能当公网效果。R45尚未上传或部署，新公网执行不在此次只读交接内。上线后必须按实际HTTPS压缩/缓存，再进行首次/再次导航与关键登录后接口测量。

本轮后台整理首次在任何清理或项目写入前因PowerShell进程输出编码拒绝；仅将输出显式固定UTF8后正常完成。失败保留，不存原始进程命令行。源码、证据与说明只追加原本地Git分支，未公开推送。完整南港复刻与长期UE引擎、EXE GIS图层/多源标牌和Web3D目标继续，fullCloneReady=false。
'''
 (D/'公网IIS与加载实测核查.md').write_text(doc,encoding='utf8')
 changes={'deploy/handbook/public_iis_performance_recheck_r857_20261104.md':doc.encode('utf8'),
  'deploy/verification/public_iis_readonly_r857.json':enc(observation),
  'deploy/verification/public_static_get_r856.json':enc(p),
  'tools/measure_public_performance_recheck_r856.py':(V/'measure_public_performance_recheck_r856.py').read_bytes(),
  'tools/record_public_iis_readonly_r857.py':Path(__file__).read_bytes()}
 for rel,raw in changes.items():
  dest=A/rel;assert not dest.exists();dest.write_bytes(raw)
 title='## 2026-11-04 R856—R857：用户交接后IIS只读复核，公网脚本仍identity/no-store\n\n'
 text='实际映射及XnbyReferenceProxy路径*保持；静态压缩勾选/动态缺组件，未读精确服务器SHA，不认唯一根因；全部设置取消，已交还桌面。后台6公开GET均200，安全JS2624898B约2.75/3.80秒、应急2575860B约6.09/6.39秒，均无编码/no-store/无ETag或Vary，重复完整；非整页或登录API验收。R45已固定本地通过、8文件2333477B/1c89579f，未上传部署，此次只读不覆盖发布。仅原本地Git，无公开推送/服务器写/业务写/腾讯写，完整长期目标active/fullCloneReady=false。\n\n'
 rel='docs/project/公网IIS只读复核与加载未验收_20261104.md';assert not(E/rel).exists();(E/rel).write_text(title+text,encoding='utf8')
 for path in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md']:
  raw=path.read_bytes();path.write_bytes((title+text).encode('utf8')+raw)
 spec=importlib.util.spec_from_file_location('local_r857',V/'commit_r18_local_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 app=m.commit(A,'d644603e59055969257b789863662f42e1c983dc','review/workplace-r19-live-local-20261031',list(changes),'app-r857',message_override='docs: record authorized read-only IIS check and actual uncompressed public static responses',update_existing=True)
 engine=m.commit(E,'ce57a6630a33e0ad68fab5931893c90c23e26b65','review/workplace-r19-live-progress-local-20261031',[rel,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md'],'engine-r857',message_override='docs: retain public performance gap after read-only IIS verification',update_existing=True)
 assert sha(A/'native/main.cpp')==held
 receipt={'application':app,'engine':engine,'publicPushed':False,'desktopReturned':True,'publicChanged':False}
 (D/'local-review-git-r857.json').write_bytes(enc(receipt));print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
