"""Freeze explicit public-source proposal only; do not create GitHub objects or push refs."""
from pathlib import Path,PurePosixPath
import ast,collections,hashlib,importlib.util,json,re,subprocess,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_source_bootstrap_r858_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PARENTS=['1f936ec0ac6cbd7574a7f5b49b3115b5ccdb48fa','22ff2cad89d05678b90d41601ba7d4323990f7d6']

def git(repo,args):
 p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert p.returncode==0,'READ_ONLY_GIT_FAILED';return p.stdout

def inventory():
 oldPath=R/'Document/Deployment/public_test_mapper_chart_r44_20261104/public-git-sync-r577-manifest.json'
 assert sha(oldPath)=='385715bcd986bbe68315b6fe47e22ec5e32907bdfabbe0e63f5141f02b4c1524'
 old=J(oldPath);names=[set(),set()]
 for i,target in enumerate(old['targets']):
  assert target['expectedParent']==PARENTS[i]
  for row in target['files']:
   assert sha(Path(row['source']))==row['sha256']
   names[i].add(row['path'])
 for commit in ['2ebe25737ce0f7913ab3791b801b9a99d74702df','d644603e59055969257b789863662f42e1c983dc','43341fc36957259aea003ed28e83d2f16db02777']:
  names[0].update(git(A,['diff-tree','--no-commit-id','--name-only','-r',commit]).decode('utf8').splitlines())
 names[0].update((p.relative_to(A).as_posix()for p in(A/'source-review/original-online-integration-r481').rglob('*')if p.is_file()))
 names[0].add('tools/original_online_workflow_integration_r483.py')
 names[1].update(['docs/project/R45原后端加载兼容固定候选进展_20261104.md','docs/project/公网IIS只读复核与加载未验收_20261104.md'])
 inputs=J(R/'work/canonical-bootstrap-compatible-r841/actual-compiled-source-files.json')
 sourceProof=[]
 for folder in ['authenticated-bootstrap-r817','original-online-integration-r481']:
  for p in(A/'source-review'/folder).rglob('*'):
   if not p.is_file():continue
   relative=p.relative_to(A/'source-review'/folder).as_posix()
   assert inputs[relative]=={'bytes':p.stat().st_size,'sha256':sha(p)}
   assert p.relative_to(A).as_posix()in names[0]
   sourceProof.append({'path':p.relative_to(A).as_posix(),'compilerPath':relative,'sha256':sha(p)})
 assert len(sourceProof)==7
 return names,sourceProof

def scan(repo,names):
 result=[];counts=collections.Counter();findings=[]
 for name in sorted(names):
  q=PurePosixPath(name);assert not q.is_absolute()and '..'not in q.parts and q.as_posix()==name
  assert q.parts[0]in {'tools','source-review','deploy','docs'}
  assert not any(x.lower()in {'private','assets','reference','node_modules','userdata','native','logs'}for x in q.parts)
  p=repo/name;raw=p.read_bytes();text=raw.decode('utf8');ext=p.suffix.lower()
  assert ext in {'.py','.mjs','.ts','.vue','.md','.json','.cmd','.config'}and b'\0'not in raw
  assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ajb-[a-z]{2,}|[A-Za-z0-9_-]{35,}\.[A-Za-z0-9_-]{35,}\.[A-Za-z0-9_-]{25,}',text),'POTENTIAL_REAL_CREDENTIAL_OR_TOKEN_REFUSED'
  # Flag literal credential assignments for inspection without returning their values.
  for lineno,line in enumerate(text.splitlines(),1):
   if re.search(r'''(?i)["']?(?:password|passwd|pwd|access_token|refresh_token)["']?\s*[:=]\s*["'][^"']+["']''',line):
    findings.append({'path':name,'line':lineno,'kind':'literal-credential-like-assignment-review-required'})
  if ext=='.py':ast.parse(raw,filename=name)
  if ext=='.json':json.loads(raw)
  if ext=='.config':ET.fromstring(raw)
  if ext=='.cmd':assert text.lower().startswith('@echo off')and 'python.exe" -I -B 'in text
  counts[ext]+=1
  blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  result.append({'path':name,'source':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gitBlobSHA1':blob})
 allPaths={row['path']for row in result};assert len(allPaths)==len(result)
 for path in allPaths:assert not any(str(p)in allPaths for p in PurePosixPath(path).parents if str(p)!='.')
 return result,dict(counts),findings

def main():
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
 names,sourceProof=inventory();rows=[];stats=[];flags=[]
 for repo,n in zip([A,E],names):
  r,c,f=scan(repo,n);rows.append(r);stats.append(c);flags.extend(f)
 if not args.freeze:
  report={'inventoryFiles':[len(x)for x in rows],'inventoryBytes':sum(x['bytes']for group in rows for x in group),'syntaxTypes':stats,'sevenFinalCompilerInputsMatch':True,'credentialLikeLinesRequiringInspection':flags,'scopePaths':[[r['path']for r in group]for group in rows]}
  (V/'public-bootstrap-preparation-r858.json').write_bytes(enc(report));print(json.dumps({k:v for k,v in report.items()if k!='scopePaths'},ensure_ascii=False));return
 assert not flags,'INSPECT_LITERAL_CREDENTIAL_FINDINGS_BEFORE_FREEZE'
 assert not D.exists();D.mkdir()
 doc='''# R858固定公开源码范围说明

本次只整理公开Git同步范围，不操作桌面或服务器。复用应用review/workplace-r19-verified-partial-20261031和引擎review/workplace-r19-verified-progress-20261031，不建分支，不改main/其他分支，不发送私有提交祖先。公开当前头已通过连接器只读核对，执行时须再次核对，漂移即停止；每仓新提交只有清单指定公开头这一父提交，发布后逐Blob、闭合树、唯一父和最终ref回读。

包括原未答R44的31文件、本轮完整在线表单/组件延迟与分组/静态地址兼容源码、构建和实际验证工具、原后端兼容R45更新器/运输恢复源码、公开静态GET实测及IIS只读观察和部署验收说明；重复路径只计一次。R44旧说明为历史候选快照，由最新R45和IIS实测说明明确补证。本提案统一替代未答31文件提案，旧提案不另执行，旧固定字节保留。

七份最终TS/Vue正文逐SHA匹配实际完整R841编译输入。R45本地真实原后端13项UI、10实际网关GET、两基线完整代码正常和第4写恢复、22拒绝/17运输检查通过，R45仍未上传部署。R856公网两脚本实际仍identity/no-store，IIS只读核查正确映射/托管代理、静态压缩勾选、动态缺组件，不认定唯一根因。独立本地源码审阅、语法检查和固定清单不替代全南港业务、全部表单、实际IIS/TLS/冷暖导航/API验收。

包含本方代码、内部部署及临时工作区路径、固定构建标识、合成测试用户名/定义、运行阶段与哈希等限定结果。排除真实或虚构口令值、实际账号/会话/令牌、运行数据库UUID、实际业务原始行、数据库/资产、Reference/SDK原档/class/二进制、截图、原始日志和另一三维会话held原生代码。小型JSON均为限定测试摘要/清单，不是原业务导出。

源码与实际来源对应，但公开仓库仍依赖未公开原SDK、现存完整编译素材、安装环境和本地准备元数据。部分历史/最终驱动精确引用原内部路径或模块图；它们按实测来源保留，不伪称公开干净检出后一键完整构建。历史失败/被替代构建保留为阶段证据，不将语法通过算作业务验收。运行身份/私有配置值未包含。

本轮未创建新GitHub Blob/树/提交或更新分支。仍需对新的固定公开清单范围明确确认；此范围不替代R45部署/桌面交接答复，也不含腾讯回填或服务器清理。完整UE效果效率引擎、EXE GIS/DLG点线面图层与多源空间标牌、Web3D和一套南港B/S复刻目标保持，fullCloneReady=false。
'''
 (D/'固定公开源码范围说明.md').write_text(doc,encoding='utf8')
 rel='deploy/handbook/public_source_bootstrap_scope_r858_20261104.md';assert not(A/rel).exists();(A/rel).write_text(doc,encoding='utf8');names[0].add(rel)
 rel='tools/freeze_public_bootstrap_scope_r858.py';assert not(A/rel).exists();(A/rel).write_bytes(Path(__file__).read_bytes());names[0].add(rel)
 rows=[];stats=[]
 for repo,n in zip([A,E],names):
  r,c,f=scan(repo,n);assert not f;rows.append(r);stats.append(c)
 targets=[{'repository':repo,'branch':branch,'expectedParent':parent,'files':files}for repo,branch,parent,files in zip(
  ['wangjiankang0531/-ZhumadianRiskControl','wangjiankang0531/-XNBYEngine'],
  ['review/workplace-r19-verified-partial-20261031','review/workplace-r19-verified-progress-20261031'],PARENTS,rows)]
 manifest={'revision':'fixed-original-backend-bootstrap-public-source-r858','targets':targets,
  'files':sum(len(x)for x in rows),'bytes':sum(r['bytes']for group in rows for r in group),
  'existingBranchesOnly':True,'uniquePublicParentAndDriftRecheckRequired':True,'sevenActualFinalCompilerInputs':sourceProof,
  'publicR45Deployed':False,'newGitHubObjectsCreated':False,'publicCleanCheckoutOneCommandBuildNotClaimed':True,'fullCloneReady':False}
 (D/'public-git-sync-r858-manifest.json').write_bytes(enc(manifest))
 (D/'prepared-source-validation-r858.json').write_bytes(enc({'passed':True,'syntaxTypes':stats,'UTF8BytePinsAndGitBlobSHA1':True,'sevenActualFinalCompilerInputsMatch':True,'credentialLikeLiteralFindings':[],'wholeRemoteTreeNotYetCreatedOrVerified':True,'JS_TS_Vue_SyntaxStillPending':True}))
 print(json.dumps({'files':manifest['files'],'bytes':manifest['bytes'],'manifestSHA256':sha(D/'public-git-sync-r858-manifest.json'),'countsByRepository':[len(x)for x in rows]},ensure_ascii=False))
if __name__=='__main__':main()
