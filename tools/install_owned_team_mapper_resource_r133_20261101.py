from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r133';T=R/'Application/tools'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest()
assert A.resolve()==A.absolute()and not(A.parent/'user-manual-protected.json').exists()and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
terminal=J(C/'r2/controller-terminal.json');receipt=J(C/'r2/scoped-controller-receipt.json');failure=J(C/'r2/team-browser/failure.json')
assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed']
assert receipt['ready']and receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(code==0 for code in receipt['exitCodesBeforeJobClose'].values())
assert failure['stage']=='team-parent-save-with-child'and failure['message']=='TEAM_PARENT_CHILD_SAVE_NOT_CONFIRMED'
assert any(r['path'].endswith('/firstAidTeams/save')and r['httpStatus']==500 and r['businessCode']==100000 for r in failure['http'])
command="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
observed=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert observed.returncode==0 and observed.stdout.decode('utf-8-sig').strip()=='0'
prepared=J(R/'work/event_delivery_consistency_20261030/full-controller-r131/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==prepared['releaseSHA256']
original=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');main='payload/business/application.jar';assert sha(A/main)==original['files'][main]['sha256']
with zipfile.ZipFile(A/main)as z:raw=z.read('xml/FirstAidTeamMembersMapper.xml')
assert len(raw)==2568 and digest(raw)=='2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'
target='payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml';assert target not in original['files']and not(A/target).exists()
payload=copy.deepcopy(original);payload['files'][target]={'bytes':len(raw),'sha256':digest(raw)};payload['nativeTeamMapperResource']={'source':'payload/business/application.jar!/xml/FirstAidTeamMembersMapper.xml','sourceAndInstalledBytesIdentical':True,'defaultMybatisPlusMapperScanPath':'classpath*:/mapper/**/*.xml','originalSQLUnchanged':True}
bodies={target:raw,'payload-manifest.json':enc(payload)};release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);release['nativeTeamMapperCandidate']='R133-original-member-XML-in-default-scan-path';bodies['release-manifest.json']=enc(release)
changes={n:{'before':sha(A/n)if(A/n).exists()else None,'after':digest(body)}for n,body in bodies.items()};out=C/'candidate-install-r1';assert not out.exists();out.mkdir();bundle=out/'bundle'
for name,body in bodies.items():p=bundle/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
spec=importlib.util.spec_from_file_location('own_g_update',A/'tools/original_public_test_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.backup_code(A,out/'backup',changes);m.replace_code(A,bundle,changes)
assert all(sha(A/n)==row['after']for n,row in changes.items())and all(sha(A/n)==pin for n,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(prepared);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),wholeControllerActuallyStarted=False)
for name,value in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'onlyStoppedOwnGChanged':True,'originalR25FrontendUnchanged':True,'originalTeamSQLResourceByteExact':True,'writes':3,'removals':0,'backendJavaJarControlConfigDatabaseSchemaOrPublicChanged':False,'runtimePending':True})]:(out/name).write_bytes(enc(value))
print('OWN_G_ORIGINAL_TEAM_XML_RESTORED_TO_DEFAULT_SCAN_PATH_THREE_PATHS_NO_SQL_OR_JAVA_OR_FRONTEND_EDIT')
