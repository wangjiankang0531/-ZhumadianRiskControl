from pathlib import Path
import ast,datetime,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';D=R/'Document/Deployment/public_test_static_performance_r37_20261103';V=Path(__file__).resolve().parent
stage=json.loads((D/'local-stage-files.json').read_bytes());app=[x for x in stage['application']if x!='deploy/handbook/native_desktop_indicator_and_execution_20261103.md'];assert len(app)==29
engine=['docs/project/静态加载优化R37候选_20261103.md'];out=D/'public-source-r241';assert not out.exists();out.mkdir()
rows=[];syntax={'python':0,'json':0,'node':0}
for role,root,names in [('application',A,app),('engine',E,engine)]:
 for rel in names:
  src=root/rel;raw=src.read_bytes();text=raw.decode('utf-8-sig')
  assert not src.suffix.lower()in['.exe','.dll','.class','.jar','.zip','.png','.db']
  if src.suffix=='.py':ast.parse(text);syntax['python']+=1
  if src.suffix=='.json':json.loads(text);syntax['json']+=1
  if src.suffix=='.mjs':
   q=subprocess.run(['node','--check',str(src)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10);assert q.returncode==0;syntax['node']+=1
  dest=out/role/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  rows.append({'repository':role,'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gitBlobSHA':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
manifest={'revision':'R241-static-performance-fixed-public-source','frozenAt':datetime.datetime.now().astimezone().isoformat(),'stateAtFreeze':'R37 uploaded and server check-only passed; deployment completion receipt not yet obtained.','repositories':{'application':{'name':'wangjiankang0531/-ZhumadianRiskControl','branch':'review/workplace-r19-verified-partial-20261031','soleParent':'b68842becc408c1cc4361d87bccffc5a6bbd65c1'},'engine':{'name':'wangjiankang0531/-XNBYEngine','branch':'review/workplace-r19-verified-progress-20261031','soleParent':'cd8021509ff1d6eee02f800a9de4e117e9402f7d'}},'fileCount':len(rows),'bytes':sum(r['bytes']for r in rows),'files':rows,'syntaxChecks':syntax,'containsSourceInternalPathsAndFixedReleaseMetadataIdentifier':True,'syntheticTransportMarkersAreNotValidAccountsOrTokens':True,'containsActualCredentialsAccountsSessionsBusinessRowsRuntimeDatabaseUUIDAssetsReferenceScreenshotsLogsOrQuarantinedBinaries':False,'newBranchMainChangeOrPrivateAncestryIncluded':False,'cleanPublicCheckoutOneCommandBuildClaimed':False,'fullCloneReady':False}
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();(D/'public-git-sync-r241-manifest.json').write_bytes(raw)
scope=f'''# 固定R241公开源码范围

共{len(rows)}文件、{manifest['bytes']}字节，清单SHA256 {hashlib.sha256(raw).hexdigest()}。应用29文件、引擎1进展摘要；复用原两review分支，唯一父b68842be/cd802150，不新建、不改main/其它分支，不发私有祖先，远端漂移拒绝，逐Blob/闭合树/唯一父/ref回读。

包含本方静态gzip/哈希缓存/IIS协商源码、最终R37严格更新器、构建/完整预检/恢复/实际传输和浏览器验证源及限定证据/体验说明；含内部路径、固定发布ID元数据和无效合成传输标记。不是实际账号/口令/令牌或数据库UUID，不含业务原文、配置、资产、Reference/SDK、截图、原日志、任何EXE/class/Jar/ZIP或held三维改动。公开代码中R37更新器为了固定原R36记录，含静态releaseId；此点在本范围明确披露，不混作运行/数据库UUID。

快照如实记录R37已上传且服务器预检通过，但冻结时尚未取得部署完成回执，真实IIS/外网和登录后业务计时仍待；原13代理通过，360隔离的23测试未执行。原正常停/启/备份/恢复AST保持，不宣称新整文件独立跑过六组件、全南港完成或公开干净检出一键构建。冻结后的实际回执另记，不反改快照。

全部UTF8/逐SHA/Git Blob对象及Python/JSON/Node语法通过。当前仅本地固定，尚未新创建GitHub对象/提交或更新分支。本次固定R37部署批准不含公开Git，旧42文件范围也不同。
'''
(D/'固定公开源码范围说明_r241.md').write_text(scope,encoding='utf-8');(D/'public-source-syntax-checks.json').write_text(json.dumps(syntax,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'fixedFiles':len(rows),'bytes':manifest['bytes'],'manifestSHA256':hashlib.sha256(raw).hexdigest(),'syntax':syntax,'noPublicObjectsOrRefsCreated':True}))
