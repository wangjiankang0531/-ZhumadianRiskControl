"""Unify the unsubmitted 135-file snapshot with actual R45 delivery evidence; no network writes."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_source_r45_delivered_r865_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists()
 source=R/'Document/Deployment/public_source_bootstrap_r858_20261104/public-git-sync-r858-manifest.json'
 assert sha(source)=='5e2fc6c8a07c4b33e6d1149a027a16566f3cf9ccd27014cdca8ca92e37c7385f'
 old=J(source);names=[set(),set()]
 for i,t in enumerate(old['targets']):
  for row in t['files']:
   assert sha(Path(row['source']))==row['sha256'];names[i].add(row['path'])
 p=subprocess.run(['git','-C',str(A),'diff-tree','--no-commit-id','--name-only','-r','b9aca822ba7a3ba031ff20323eac6256aab2c64e'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert p.returncode==0;added=p.stdout.decode('utf8').splitlines();assert len(added)==15;names[0].update(added)
 names[1].add('docs/project/R45公网加载实际交付与三维协调_20261104.md')
 proof=J(R/'Document/Deployment/public_test_original_bootstrap_r45_20261104/public-delivery-r864.json');assert proof['passed']and proof['publicR45Deployed']and not proof['publicGitPushed']
 doc='''# 固定R865公开源码范围：R45已实际交付

本清单统一替代尚未执行的31文件旧提案及未外发的135文件准备快照，旧范围不另执行，原固定字节保留。复用原应用review/workplace-r19-verified-partial-20261031和引擎review/workplace-r19-verified-progress-20261031；不新建分支、不改main或其他分支、不发送私有提交祖先。两个唯一父为清单所列已公开当前头，执行前再次只读核对，漂移即停止；逐Blob、完整树、唯一父及最终分支回读。

内容包括原R44 Mapper/工作台样式源码与验证、本轮七份实际编译TS/Vue、完整在线表单与原后端兼容、登录前完整组件延迟与显式分组、静态地址兼容、R45运行更新/运输恢复、真实公网/IIS/浏览器验证工具与限定结果、部署体验及三维协调说明。七份正文与最终完整编译输入SHA一致，保留失败和被替代构建记录，不把语法核验当业务验收。旧“未部署”说明是阶段历史，新R45实际交付说明优先解释当前状态。

R45已从精确R36正常部署，八运输文件逐字回读、196写入/181移除、原六组件正常停启。服务器网关/IIS TLS16项、外网正常证书12项过：主脚本gzip约819234/431938字节、解压SHA相同、哈希一年immutable/HTML no-store。独立匿名首次/再次登录页为1014/139ms和578/156ms、再次9/9及8/8静态命中；仅一次本机受控范围测量，8范围外请求被拦截未分类，非稳定SLA或登录后业务模块/API验收。Chrome原生接管提示超时后已停输入/交还桌面；独立测试浏览器使用自有新档案且正常退出，未接触用户档案。

包含本方代码、内部部署/临时工作区路径、固定构建标识、合成用户名/测试定义及限定结果。排除真实或虚构口令值、实际账号/会话/令牌、运行数据库UUID、业务原始行、数据库、资产、Reference/SDK原档/class/二进制、截图、原始日志及held三维原生改动。三维D60/D61记录已核，部署前既定同步路由实404，三维独立目录/源/数据未覆盖；后续三维必须重新发现R45当前run/ready/nginx/端口，不能用旧j2。没有声称另一会话已回执，没有部署图层同步功能或删除服务器旧版本。

公开仓库仍依赖原SDK、现存编译素材及本地准备元数据；历史/最终构建驱动精确引用内部路径/实际模块图。本范围用于如实审阅与保留本方实际代码，不宣称公开干净检出后一键完整构建。全部南港业务/复杂表单、公网正常登录后的完整页面/API、三维EXE/Web及UE长期目标继续，fullCloneReady=false。

本批没有创建新GitHub内容对象、树、提交或修改分支。R45部署批准明确不含新的公开Git，需要本份固定公开源码范围的单独确认；不含新的服务器部署、桌面接管、腾讯回填或清理。
'''
 D.mkdir();(D/'固定公开源码范围说明.md').write_text(doc,encoding='utf8')
 rel='deploy/handbook/public_r45_delivered_source_scope_r865_20261104.md';assert not(A/rel).exists();(A/rel).write_text(doc,encoding='utf8');names[0].add(rel)
 rel='tools/freeze_public_r45_delivered_r865.py';assert not(A/rel).exists();(A/rel).write_bytes(Path(__file__).read_bytes());names[0].add(rel)
 s=importlib.util.spec_from_file_location('source_scan_r865',V/'freeze_public_bootstrap_scope_r858.py');scan=importlib.util.module_from_spec(s);s.loader.exec_module(scan)
 targets=[];stats=[]
 for i,repo in enumerate([A,E]):
  rows,counts,findings=scan.scan(repo,names[i]);assert not findings
  targets.append({**{k:v for k,v in old['targets'][i].items()if k!='files'},'files':rows});stats.append(counts)
 actual=J(R/'work/canonical-bootstrap-compatible-r841/actual-compiled-source-files.json')
 for pin in old['sevenActualFinalCompilerInputs']:assert sha(A/pin['path'])==pin['sha256']==actual[pin['compilerPath']]['sha256']
 manifest={'revision':'fixed-public-r45-delivered-source-r865','targets':targets,'files':sum(len(t['files'])for t in targets),'bytes':sum(r['bytes']for t in targets for r in t['files']),
  'sevenActualFinalCompilerInputs':old['sevenActualFinalCompilerInputs'],'existingBranchesOnly':True,'uniquePublicParentAndDriftRecheckRequired':True,
  'publicR45Deployed':True,'publicAuthenticatedModulesTimingAccepted':False,'publicCleanCheckoutOneCommandBuildNotClaimed':True,
  'newGitHubObjectsCreated':False,'fullCloneReady':False}
 assert manifest['files']==153
 (D/'public-git-sync-r865-manifest.json').write_bytes(enc(manifest))
 result={'prepared':True,'files':manifest['files'],'bytes':manifest['bytes'],'manifestSHA256':sha(D/'public-git-sync-r865-manifest.json'),'repositoryFiles':[len(t['files'])for t in targets],
  'syntaxTypes':stats,'sevenActualFinalCompilerInputsMatch':True,'JS_TS_Vue_SyntaxPending':True,'publicObjectsCreated':False}
 (D/'prepared-fixed-source-r865.json').write_bytes(enc(result));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
