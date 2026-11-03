from pathlib import Path
import ast,copy,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
W=R/'work/user_feedback_20261031';O=W/'r38-unified-original-mappers-r2'
D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2';D1=R/'Document/Deployment/public_test_unified_mappers_r38_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
full=J(D/'full-program-preflight.json');tx=J(D/'composition-and-recovery.json');gate=J(R/'Document/Deployment/original_mapper_install_preflight_r285_20261103/verified-cases-r287.json')
source=T/'original_public_test_update_r38_mapper_preflight_r286.py'
assert full['allPassed']and tx['passed']and gate['passed']
assert full['newUpdaterSHA256']==tx['updaterSHA256']==gate['candidateSourceSHA256']==sha(source)
delivery=D/'delivery';assert not delivery.exists();delivery.mkdir()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
plan=J(O/'bundle/update-manifest.json')
archive=delivery/'Zhumadian_Unified_Original_Mappers_20261103_R38_R2.zip'
deny=(D1/'delivery/web.config').read_bytes()
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
    z.writestr('web.config',deny);z.writestr('update-manifest.json',(O/'bundle/update-manifest.json').read_bytes())
    for name,pin in plan['files'].items():
        raw=(O/'bundle/payload'/name).read_bytes();assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'];z.writestr('payload/'+name,raw)
wrapper=(D1/'delivery/deploy_unified_mappers_r38.py').read_text(encoding='utf-8')
tree=ast.parse(wrapper);assign={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
values={'ARCHIVE_SHA':sha(archive),'MANIFEST_SHA':sha(O/'bundle/update-manifest.json'),'NEW':plan['newReleaseSHA256'],
        'UPDATE':plan['updateId'],'UPDATER_SHA':sha(source)}
lines=wrapper.splitlines(keepends=True)
for key,value in values.items():
    n=assign[key];assert n.lineno==n.end_lineno;lines[n.lineno-1]=key+'='+repr(value)+'\n'
wrapper=''.join(lines).replace('Zhumadian_Unified_Original_Mappers_20261103_R38.zip',archive.name)
ast.parse(wrapper);put(delivery/'deploy_unified_mappers_r38.py',wrapper.replace('\r\n','\n').replace('\n','\r\n').encode())
put(delivery/'r38_update_runtime.py',source.read_bytes());put(delivery/'web.config',deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
    put(delivery/(label+'_Unified_Mappers_R38_R2.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_unified_mappers_r38.py" '+flag+'\r\n').encode('ascii'))
md=copy.deepcopy(J(D1/'delivery-manifest.json'));md.update(
    revision='R38-r2-unified-original-mappers-install-snapshot',
    targetFTP='/Zhumadian/Zhumadian_Unified_Original_Mappers_20261103_R38_R2/',
    files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in delivery.iterdir()},
    newReleaseSHA256=plan['newReleaseSHA256'],newUpdaterSHA256=sha(source),updateManifestSHA256=sha(O/'bundle/update-manifest.json'),
    sameSnapshotMapperValidationInsideApplyUpdate=True,mapperInstallPreflightChecks=gate['checks'],
    actualApplyUpdatePreStopPathsWithExplicitSpiesPassed=True,
    priorUnpublishedR38ManifestWithdrawn=sha(D1/'delivery-manifest.json'))
md.pop('allLifecycleFunctionsASTRetainedFromR37')
md['normalStopLaunchBackupReplaceRestoreRecoveryFunctionsASTRetainedFromR37']=True
put(D/'delivery-manifest.json',enc(md));put(delivery/'delivery-manifest.json',enc(md))
proof={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),
 'manifestSHA256':sha(D/'delivery-manifest.json'),'writes':len(plan['files']),'removals':len(plan['removedFrontendFiles']),
 'publicUploadedOrInstalled':False,'newPublicGitIncluded':False,'previousR38Withdrawn':True}
put(D/'preparation-result.json',enc(proof))
s=(T/'verify_unified_delivery_r280.py').read_text(encoding='utf-8').replace('public_test_unified_mappers_r38_20261103','public_test_unified_mappers_r38_20261103_r2').replace('r38-unified-full-preflight-r275','r38-unified-full-preflight-r288').replace('r38-unified-original-mappers-r1','r38-unified-original-mappers-r2')
ast.parse(s);out=V/'verify_unified_snapshot_delivery_r289.py';assert not out.exists();out.write_text(s,encoding='utf-8')
print(json.dumps(proof))
