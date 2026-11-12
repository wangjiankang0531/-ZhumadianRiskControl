"""Record bounded local D176 integration evidence without installing a candidate."""
from pathlib import Path
import datetime, hashlib, json, shutil
R=Path('D:/Project/Zhumadian'); A=R/'Application'; E=R/'XNBYEngine'; V=Path(__file__).resolve().parent
D=R/'Document/Deployment/resource_control_integration_r2440_20261112'
S=A/'tools/experimental_source/resource_control_integration_r2440'
P=A/'deploy/verification/resource_control_integration_r2440'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p): return json.loads(p.read_bytes())
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cp(p,q):
 assert p.is_file() and not q.exists(); q.parent.mkdir(parents=True,exist_ok=True)
 with p.open('rb')as r,q.open('xb')as w:shutil.copyfileobj(r,w)
 assert sha(p)==sha(q)
def main():
 assert not D.exists() and not S.exists() and not P.exists()
 F=R/'work/hazard-management-full-r2434'; W=R/'work/resource-scene-control-r2435'; G=R/'work/resource-complete-control-r2438'
 full=j(F/'full-build-result.json'); scene=j(W/'verification.json'); graph=j(G/'independent-graph-verification.json')
 ft=j(V/'hazard-management-full-r2434-outer-terminal.json'); st=j(V/'d176-scene-r2435-outer-terminal.json')
 assert full['passed'] and scene['passed'] and graph['passed']
 assert ft['exitCode']==0 and ft['actualJobDescendantsZero'] and st['rootExitCode']==0 and st['actualJobBeforeClose']==0
 assert not ft['forceTerminationUsed'] and not st['forceTerminationUsed']
 held=sha(A/'native/main.cpp')
 proofs={
  'peer-source-receipt.json':R/'Document/Deployment/resource_gis_browser_received_r2432_20261112/source-receipt.json',
  'full-build-result.json':F/'full-build-result.json','source-restoration.json':F/'source-restoration.json',
  'full-build-outer-terminal.json':V/'hazard-management-full-r2434-outer-terminal.json',
  'scene-verification.json':W/'verification.json','scene-rebuild-receipt.json':W/'products/rebuild-receipt.json',
  'scene-outer-terminal.json':V/'d176-scene-r2435-outer-terminal.json',
  'complete-graph-verification.json':G/'independent-graph-verification.json',
 }
 for name,p in proofs.items():cp(p,D/name);cp(p,P/name)
 recipes=['prepare_d176_merge_r2433.py','build_full_resource_portal_r2434.py','run_full_resource_portal_r2434.py',
  'rebuild_d176_scene_r2435.py','prepare_resource_control_graph_r2438.py','verify_resource_control_graph_r2439.py','record_control_integration_r2440.py']
 for name in recipes:cp(V/name,S/'recipe'/name)
 # Runtime sources are retained for review, not the enormous generated payload/contract or any private proposal.
 for p in (G/'runtime/tools').iterdir():
  if p.is_file()and p.suffix=='.py':cp(p,S/'runtime/tools'/p.name)
 summary={'at':datetime.datetime.now().astimezone().isoformat(),'actualPublicRelease':'R51',
  'actualPublicReleaseSHA256':'b36491663db37033ae2fc450b0209e864d5ebd7b7b7ed1bba7fda6a7e5545323',
  'newLocalCandidateOnly':True,'sourcePeerFilesIndependentlyMatched':26,'completeFrontendFiles':841,
  'actualCompilerInputs':3737,'completeFrontendBytes':17835074,'fixedSceneInputs':319,'fixedSceneSourceBytes':5595971,
  'sceneOutputsMatched':5,'sceneViewerSHA256':scene['outputs']['viewer.js']['sha256'],
  'fullBuildAndSceneOriginalRootsAndJobsNormalZero':True,'completeGraphRows':16227,
  'actualProgramFilesSHARead':15663,'actualProgramLogicalBytes':1445194910,'protectedMetadataRowsNotRead':564,
  'R49QualificationSparseWrites':602,'R49QualificationRemovals':518,'notCurrentPublicIncrementalDeploymentPlan':True,
  'candidateReleaseSHA256':sha(G/'bundle/payload/release-manifest.json'),
  'newPrivateSidecarProposalOnlyNoOldFileOverwrite':True,'privateProposalContentExcludedFromSourceGitAndTransport':True,
  'wholeOriginalApplicationLifecycleAccepted':False,'ordinaryUserPublic250252Accepted':False,
  'D171StrictManagementNullGapConfirmedWithPeer':True,'nextBootstrapOwnedByPeerCandidateOnly':True,
  'serverOrClientInstallOrRegistryOrDatabaseOrGISChanged':False,'publicGitPushed':False,'fullCloneReady':False,
  'proofs':{name:{'bytes':p.stat().st_size,'sha256':sha(p)}for name,p in proofs.items()}}
 put(D/'integration-summary.json',summary);put(P/'integration-summary.json',summary)
 note='''R2440：D176资源管理完整整合候选，公网仍为已交付R51

用户批准的固定R51已正常上线，原服务器健康/数据身份和13项外网检查通过，首验后已即时通知用户。250正常公网首页刷新→敏捷应急指挥→真实地景/企业标牌仍等用户复测；252正规客户端本机激活与正常账号体验未验收。本阶段没有再次更新公网，不把候选开发混入固定R51。

独立核收三维D176固定26份Git/ZIP/工作字节一致后，沿D170既有完整输入语义合并。7个门户输入仅transport相对D170更新；完整原安全端3737实际编译输入生成841文件17,835,074字节。原首页同窗口、头像、表头/统计、危险源保护、原登录及既有业务修正保留；原项目和独立源副本在finally逐字恢复。实际原根exit0、内核Job0，未强杀，峰2,185,383,936B低于3GiB。编译通过不当正常账号浏览器或后端验收。

场景侧从保留的D170/D176固定319源/5,595,971字节重新构建五产物，312 sourcePins/190 mainInputs与依赖逐SHA符合。新viewer SHA7846f1621dda9ae7afee25019ef7f1313ab5fc3656dc7abc919704751d4d990b；其余四产物保留原pin。实际根0/Job0，峰181,506,048B低1GiB，无GIS/runtime复制。receipt的allFiveOutputsByteIdenticalToDeliveredPackage=false表示pinKind=candidate，实际allFiveOutputsMatchPinnedSources=true；不改原证据字段掩饰来源。

完整程序图resource-complete-control-r2438共16227行，44源worker、两份IIS代理及静态元数据、841门户+4保留资源、五场景产物对齐。独立读取15663程序文件/1,445,194,910逻辑字节与602稀疏文件均SHA匹配；564受保护private/seed行只核原元数据，未读业务行或凭据。原完整profile所有函数AST不变，原支持只四已声明函数和新增纯验证器不同。candidate release SHA66aa3dfd93b63efae9b39be299e038a84f729b51c843bfc8a61fc5fd8b336dfe。602写/518移除是R49资格图，不是对当前R51可直接执行的增量发布计划。

新增资源安装允许项采用独立private/spatial-sync-settings.client-resources-r2438.private.json侧文件候选；原R51 private/spatial-sync-settings.private.json及账号权限/其他每项配置保持。新私有提案仅留既有受保护本机目录，未上传、未加入源码/Git/运输，未应用。这样不在停服前改坏旧R51预检/启动/恢复配置；正式候选仍需新固定范围、现场基线与完整生命周期验证。

发现D171入口明确要求management为null，250当前正式登记也是null。直接填新管理字典会被原资格拒绝；原登录自启GIS可用不证明18768资源管理已接通。R2436已向三维共享精确来源，其16:35实际回执已确认本缺口并约定新独立安装候选：分别资格D175 .2十代码管理与原953 GIS，不让管理失败阻塞GIS；管理可在GIS根未配置时修复路径。正规可视安装固定已知旧新Run类型/SHA，未知值拒绝，当前不改250/252 Run/服务。我们负责完整门户/场景/原控制/IIS/恢复与未来公网发布；候选就绪后再定具体激活和验收。

252全量GIS内容核验由三维D177接续。首次审计在OSGB读取前因缺2346份原目录清单而拒，原根1/Job0，不能推断raw OSGB损坏。D177已认领仅补精确44,104,047字节JSON/不覆盖原目录，再使用未改审计器核237453 OSGB。本方已读其接续消息，不重复拷贝或并发扫描；其进行中声明不当完成或实际句柄终态证据。252已预置D174安装包不当已执行；本机激活、真实原用户与冷Windows登录仍待。

本轮不执行未获批准的_h七周期，不启动Java/MySQL/原GIS，不改变安全软件/用户桌面/注册表/公网或任何业务数据。后续只有精确终态、鲜CIM零、无重解析和源SHA全匹配后才清自有319源可重建副本，保留五产物/完整候选/所有源码和失败证据；具体执行另记，不先称已清。服务包装器与真实控制器属于当前运行版本，不能为整理制造退出条件。

文档和本方源码只追加原本地两个review分支，正式HEAD/index/main及held native/main.cpp保留，公开Git仍需新具体固定范围。完整UE效果效率引擎、EXE GIS DLG分层点线面多源空间标牌、Web3D两机协同和单系统天津南港完整B/S目标继续active/fullCloneReady=false，不宣称公开干净检出一键构建或整体完成。
'''
 handbook=A/'deploy/handbook/完整资源控制整合与客户机启动缺口_r2440_20261112.md'
 for p in (handbook,D/'阶段说明.md',E/'docs/project/资源完整整合与客户机启动链_r2440_20261112.md'):
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('x',encoding='utf8')as f:f.write(note)
 for name in('Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md'):
  with(R/name).open('a',encoding='utf8')as f:f.write('\n\n## 2026-11-12 R2440：完整资源候选与客户机启动链核对\n\n'+note)
 C=R/'Document/Coordination';peer=C/'交接消息/驻马店三维核收R2436管理启动缺口与下一独立安装候选约定_20261112.json'
 message={'fromChat':'驻马店3','to':'驻马店三维','at':summary['at'],'stage':'R2440-fixed-full-D176-candidate',
  'actuallyRead':{'path':peer.relative_to(R).as_posix(),'sha256':sha(peer)},
  'D171StrictNullGapAndCandidateOnlyBootstrapOwnershipAgreed':True,'newCandidate':summary,
  'D177AdditiveCatalogAndRawHashOwnedByYouNoDuplicateCopyOrScanByUs':True,
  'publicUnchangedR51':True,'noDesktopOrRegistryOr252Execution':True,'sharedFileNotRealtimeWakeup':True}
 put(C/'交接消息/驻马店3D176完整门户场景图通过并核收启动分工_r2440_20261112.json',message)
 statep=C/'驻马店3_当前协作状态.json';state=j(statep)
 state.update({'at':summary['at'],'latestResourceCompleteCandidateRoot':str(G),'latestResourceCompleteCandidateReleaseSHA256':summary['candidateReleaseSHA256'],
  'latestResourceCandidateFullGraphRows':16227,'latestResourceCandidateActualProgramFilesRead':15663,
  'latestResourceCandidateActualApplicationLifecyclePassed':False,'peerD176SourceFilesIndependentlyMatched':26,
  'ownD176FullPortal3737InputsAndFiveSceneOutputsRebuilt':True,'ownPrivateSidecarProposedOnly':True,
  'D171ManagementNullGapConfirmedAndPeerNewBootstrapCandidateAgreed':True,
  'peerLastRead':peer.name,'ownD177CatalogAndFullGISAuditDelegatedNotDuplicated':True,
  'nextOwnWork':'优先正常公网首页两机验收；新资源完整候选待正规管理启动候选/全原应用周期，不重跑R51部署，不覆盖D177扫描。'})
 statep.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert held==sha(A/'native/main.cpp')
 print(json.dumps({k:v for k,v in summary.items()if k!='proofs'},ensure_ascii=False))
if __name__=='__main__':main()
