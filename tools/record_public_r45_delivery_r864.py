"""Record actual approved R45 deployment, public static/browser proof and coordination boundaries."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_original_bootstrap_r45_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not(D/'public-delivery-r864.json').exists()
 assert sha(D/'delivery-manifest.json')=='1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876'
 remote=V/'r45-ftp-readback-r861';deploy=J(remote/'r45-scoped-result.json');server=J(remote/'server-static-performance-result.json')
 assert deploy['phase']=='deploy-complete'and deploy['selectedBase']=='r36'and deploy['serverLocalGatewayAndIISTLSStaticPassed']
 assert deploy['newReleaseSHA256']=='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
 assert deploy['updaterSHA256']=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
 assert not deploy['credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded']
 assert server['passed']and len(server['checks'])==16
 external=J(V/'public-r45-static-r862/verified-result.json');assert external['passed']and len(external['rows'])==12 and external['actualExternalHTTPS']
 browserRoot=V/'public-login-browser-r863';browser=J(browserRoot/'browser-results.json');terminal=J(browserRoot/'actual-job-terminal.json');bt=J(browserRoot/'browser-terminal.json')
 assert browser['completed']and not browser['errors']and len(browser['rows'])==4 and not browser['credentialsEntered']
 assert terminal['driverExitCode']==0 and terminal['actualJobDescendantsZero']and terminal['budgetMetricsBeforeClose']['activeProcesses']==0
 assert bt['normalBrowserCloseRequested']and bt['exitCode']==0 and not bt['forceKill']
 assert [r['cachedStaticResources']for r in browser['rows']]==[0,9,0,8]
 assert all(not r['failedStaticResources']for r in browser['rows'])
 helper=load('public_r45_owned_cleanup_r864',V/'record_research_task_ui_r812.py')
 helper.fixed();held=sha(A/'native/main.cpp')
 root=browserRoot/'browser-profile';files=helper.scan(root,browserRoot);before=shutil.disk_usage(root).free;shutil.rmtree(root)
 cleanup={'passed':True,'path':str(root),'files':len(files),'logicalBytes':sum(files.values()),'observedVolumeFreeDeltaBytes':shutil.disk_usage(browserRoot).free-before,'volumeDeltaNotExclusive':True,'normalChromeDriverAndActualJobExitedBeforeRemoval':True,'userProfileOrBusinessDataRemoved':False}
 proof={'passed':True,'publicR45Deployed':True,'exactOldBase':'R36','fixedManifestSHA256':sha(D/'delivery-manifest.json'),'newReleaseSHA256':deploy['newReleaseSHA256'],
  'serverGatewayAndIISTLSChecks':16,'actualExternalStaticHTTPSChecks':12,'actualAnonymousColdWarmNavigations':4,
  'publicNormalAuthenticatedUserTimingAccepted':False,'nativeChromeApprovalTimedOutAndDesktopInputStopped':True,'desktopReturnedToUser':True,
  'preDeploySpatialSyncRouteStatus':404,'spatialSyncDeploymentOrNewRouteAddedByThisStage':False,'serverOldVersionDeletionPerformed':False,'publicGitPushed':False,'fullCloneReady':False}
 doc='''# R45公网实际交付与加载体验说明

R45已从精确R36正常部署完成。固定8文件、2,333,477字节，运输清单SHA256为1c89579f0155c64ea7660114b7135371f726d5da2e10bfb356fe6abd687c9876；实际发布清单SHA256为3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd。用户明确批准本包并将脚本执行改为代理承担；通过服务器资源管理器仅各运行一次固定Check_Only和Deploy，未向命令窗口输入命令。Check_Only精确R36、原Mapper和预算/就绪/文件通过后才Deploy；原六组件正常停启，未手动恢复或强杀。全部八文件先独立二进制回读、逐字/SHA匹配。196写入、181退役前端移除均按固定清单；数据库、上传、鉴权和IIS映射保持。

## 已核实的公网效果

服务器原网关与实际IIS TLS共16项通过；本机从外网连接已知公网IP并正常验证www.joinlinksmart.com证书的12项独立检查也通过，不是只测本地候选。安全端主JS实际2624898→819234字节，外网gzip请求0.7121秒；应急新主JS1320116→431938字节，外网gzip请求0.4534秒。与部署前应急主脚本2575860字节不同，包含已验证登录前组件延迟/分组及静态地址兼容。gzip与显式拒绝gzip的identity均解码同SHA；两主CSS gzip分别126860和126154字节。静态哈希资源Cache-Control为public, max-age=31536000, immutable，Vary:Accept-Encoding；HTML仍no-store，并引用本轮正确资源。没有给登录/业务API设置长期缓存。

独立新Chrome档案、1360×900、缓存开启/不限速、匿名登录页受控首次/再次导航4轮通过：安全端登录可见1014/139毫秒，应急578/156毫秒；再次9/9及8/8静态资源命中缓存，静态CDP传输0字节，静态失败0、页面异常0。首次静态CDP传输约1135122/744962字节。保留原受控同项目GET/HEAD范围，8次项目外/范围外请求被拦截且未分类；这是受控匿名页面一次对照，不是所有用户网络的稳定SLA、完整浏览器全部请求或登录后模块/API提速证明。1GiB非终止Job峰值约451788800字节；Chrome/Node均0，实际后代零，随后只清本轮独立profile。

## 可以怎样体验

在https://www.joinlinksmart.com/zhumadian/正常重新打开或刷新一次，加载新HTML和静态策略；正常登录后进入你常用的“敏捷应急管理”“应急处置”等入口，比较首次进入和再次返回同一页面的等待。正常刷新即可，不要用持续强制绕缓存的方式评估再次加载。先核原数据列表是否可读，再检查本人发起/待办/已办详情、刷新和正常退出。两综合入口与六快捷入口仍按同一系统对待，不重复计算功能。

本轮原生Chrome应用授权提示超时，立即停止接管并明确交还桌面；没有通过其他方法读取用户Chrome档案、Cookie或令牌。后台独立匿名浏览器测量已完成，但公网正常登录后首页、业务列表、详情、统计API和多节点全流程仍待本轮验收，不能以匿名登录数字宣布全模块速度问题解决。已有本地原发布后端13项正常角色兼容证明保留；全部南港业务/复杂表单尚未完成。

## 与驻马店三维会话的协调

已读取该会话近期记录及D60/D61共享部署资料：图层同步只读预检报告为精确R36，路由尚未安装，后续21项运行身份工具为本地验证，未记录公网部署；近期会话尾部工作是本地场景低视角加载。当前工具没有跨会话发送接口，没有声称另一会话已回执。部署前R45现场再确认精确R36，既定/zhumadian/api/spatial-sync/v1/project/layers外网只读请求404。首次沙箱DNS/Schannel失败保留，正常权限请求正常TLS并404，不跳过证书检查。

R45仅写自己独立FTP目录，没有覆盖三维的Zhumadian_LayerSync_Check_20261104；三维源文件、GIS/DLG/用户工程、本地3D服务及其独立后台未改。本包不是三维图层同步部署。R45正常重启会使旧j2/PID/端口和ready/nginx前像过期；三维会话将来接入路由时必须重新读取当前运行身份、网关配置和SHA，以最新R45为基线条件更新，不能套用旧j2。详同级“三维会话发布协调_R45.md”。未删除服务器旧版本。

## 文档与Git

本说明是实际部署后的新记录；此前固定候选和135文件公开范围中的“未部署”是其制备时快照，保留原字节，用本说明补充，不伪改历史。源码、结果和体验说明追加原本地分支，公开Git尚未推送；将按统一新固定范围复用原两个公开分支，不发送私有祖先，不改main。完整UE效果效率引擎、EXE GIS/DLG分层点线面与多源标牌、Web3D和一套南港B/S复刻目标继续，fullCloneReady=false。
'''
 coordinate='''# 三维会话发布协调：R45已完成

驻马店3本轮已按用户批准，从精确R36更新到R45。新release-manifest SHA256：3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd；应用C:/inetpub/wwwroot/Zhumadian/Application，IIS映射不变，网关固定18892。原六组件已正常重启，旧j2、旧PID/平台业务动态端口、旧current-ready/nginx SHA不再作为当前证明。

部署前已核三维D60/D61：图层同步路由尚未部署；实际公网既定路由GET404，R45精确原文件及就绪预检通过。没有修改或执行三维的服务器检查目录，没有覆盖图层同步源、配置、数据、GIS/DLG或本地3D体验。当前无证据表明图层同步路由已安装，不能把R45当该功能交付。

三维后续部署请重新只读发现current-run/ready/release/nginx及真实进程/端口归属，基于当前R45准备精确配置差异和条件恢复，不套旧j2/旧配置前像或旧R36启动器。B/S后续也须保护届时已实际落地的三维路由，遇未知网关修改先核对，不按主版本号猜测。此说明记录本会话动作，不是另一会话已确认的回执。
'''
 artifacts={'upload-readback-r861.json':J(V/'r45-ftp-readback-verified-r861.json'),'deployment-result-r861.json':deploy,'server-static-r861.json':server,'external-static-r862.json':external,'anonymous-browser-r863.json':browser,'browser-terminal-r863.json':terminal,'cleanup-r864.json':cleanup,'delivery-r864.json':proof}
 (D/'public-delivery-r864.json').write_bytes(enc(proof));(D/'R45公网实际交付与加载体验.md').write_text(doc,encoding='utf8');(D/'三维会话发布协调_R45.md').write_text(coordinate,encoding='utf8')
 changed=[]
 for name,value in artifacts.items():
  (D/('actual-'+name)).write_bytes(enc(value));rel='deploy/verification/public-r45/'+name;p=A/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(enc(value));changed.append(rel)
 for rel,raw in {'deploy/handbook/public_r45_delivery_20261104.md':doc.encode('utf8'),'deploy/handbook/public_r45_3d_coordination_20261104.md':coordinate.encode('utf8')}.items():
  p=A/rel;assert not p.exists();p.write_bytes(raw);changed.append(rel)
 for name in ['verify_public_r45_static_r862.py','prepare_public_browser_r863.py','measure_public_login_browser_r863.mjs','run_public_browser_r863.py',Path(__file__).name]:
  p=A/'tools'/name;assert not p.exists();p.write_bytes((V/name).read_bytes());changed.append('tools/'+name)
 header='## 2026-11-04 R861—R864：固定R45从精确R36公网部署，实际压缩缓存及匿名冷暖通过\n\n'
 body='用户明确批准并改由代理执行固定脚本；原生RDP/FTP仅独立目录/八文件回读同SHA，CheckOnly过后一次Deploy，原六组件正常停启，R45最终3b125178。服务器网关/IIS TLS16、外网正常证书12项过：安全JS819234B/0.7121秒，应急新JS431938B/0.4534秒，gzip/identity同SHA、哈希一年immutable/HTML no-store。独立匿名登录安全1014/139ms、应急578/156ms，再次静态9/9、8/8命中/CDP0；8范围外拦截未分类/非全部真实页面，登录后模块/API仍待。1GiB Job峰451788800B、Chrome Node0/Job零后清自有profile。Chrome原生应用授权超时已停输入/交还桌面，不访问用户会话。三维D60/D61和近期尾部核无同步部署，部署前路由实404，独立检查目录/源/图层/GIS/DLG/本地体验保持；三维后续要以新R45重新发现run/ready/nginx/端口，不套旧j2。保留沙箱DNS/Schannel与早期传输未终态比较拒绝，未跳TLS或重启传输。服务器未删旧版/公开Git未推送，原135固定快照保留将另合实际交付新范围；完整长期目标active/fullCloneReady=false。\n\n'
 for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
  p.write_bytes((header+body).encode('utf8')+p.read_bytes())
 with(R/'Document/Engine/showcase_demo_completion.md').open('a',encoding='utf8')as out:out.write('\n'+header+body)
 specific='docs/project/R45公网加载实际交付与三维协调_20261104.md';assert not(E/specific).exists();(E/specific).write_text(header+body,encoding='utf8')
 commit=load('public_r45_local_r864',V/'commit_r18_local_review.py')
 app=commit.commit(A,'4fbd56a21424bb1c32f980f065a4b46266234e96','review/workplace-r19-live-local-20261031',changed,'app-r864',message_override='release: record actual R45 deployment, HTTPS compression/cache and isolated browser timing',update_existing=True)
 engine=commit.commit(E,'dbfed80b9a02fc56b9566bfe520825633dae978c','review/workplace-r19-live-progress-local-20261031',[specific,'docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/showcase_demo_completion.md'],'engine-r864',message_override='docs: record public R45 delivery and fresh gateway baseline for 3D coordination',update_existing=True)
 helper.fixed();assert sha(A/'native/main.cpp')==held
 receipt={'application':app,'engine':engine,'publicR45Deployed':True,'publicGitPushed':False,'desktopReturned':True,'fullCloneReady':False}
 (D/'local-review-git-r864.json').write_bytes(enc(receipt));print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
