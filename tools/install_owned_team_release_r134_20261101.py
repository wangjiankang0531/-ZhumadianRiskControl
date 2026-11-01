from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r134';W=R/'work/user_feedback_20261031';S=W/'r26-team-native-candidate-r1';T=R/'Application/tools'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest()
assert A.resolve()==A.absolute()and not(A.parent/'user-manual-protected.json').exists()and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
assert J(R/'work/r26gv-r1/full-preflight-result.json')['allPassed']
for name,count in [('r26-inherited-updater-contract-r1',123),('r26-workflow-contract-r1',34),('r26-material-contract-r1',57),('r26-team-contract-r1',46)]:
 proof=J(W/name/'result.json');assert proof['allPassed']and proof['checks']==count and proof['sourceSHA256']==sha(T/'original_public_test_update_r26_20261101.py')
previous=R/'work/event_delivery_consistency_20261030/full-controller-r133';assert J(previous/'r8/result.json')['allPassed']and J(previous/'r8/team-browser/result.json')['passed']
terminal=J(previous/'r8/controller-terminal.json');receipt=J(previous/'r8/scoped-controller-receipt.json');assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed'];assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(code==0 for code in receipt['exitCodesBeforeJobClose'].values())
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
observed=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert observed.returncode==0 and observed.stdout.decode('utf-8-sig').strip()=='0','OWN_G_PROCESS_STILL_PRESENT'
oldPrepared=J(previous/'candidate-install-r2/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==oldPrepared['releaseSHA256']
owned=J(A/'payload-manifest.json');q=J(S/'bundle/payload/payload-manifest.json');assert [name for name in set(owned['files'])|set(q['files'])if owned['files'].get(name)!=q['files'].get(name)]==['private/server-configuration.json']
q['files']['private/server-configuration.json']=copy.deepcopy(owned['files']['private/server-configuration.json']);assert owned['files']==q['files']
release=J(S/'bundle/payload/release-manifest.json');bodies={'tools/original_public_test_update.py':(T/'original_public_test_update_r26_20261101.py').read_bytes(),'payload-manifest.json':enc(q)};release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(release)
changes={name:{'before':sha(A/name),'after':digest(raw)}for name,raw in bodies.items()};out=C/'candidate-install-r1';assert not out.exists();out.mkdir(parents=True);bundle=out/'bundle'
for name,raw in bodies.items():p=bundle/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
spec=importlib.util.spec_from_file_location('verified_r26_owned_install',T/'original_public_test_update_r26_20261101.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.backup_code(A,out/'backup',changes);m.replace_code(A,bundle,changes)
assert all(sha(A/name)==row['after']for name,row in changes.items())and all(sha(A/name)==pin for name,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(oldPrepared);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),updaterSHA256=sha(A/'tools/original_public_test_update.py'),wholeControllerActuallyStarted=False)
for name,obj in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'onlyStoppedOwnedGControlAndTwoManifestsChanged':True,'writes':3,'publicR26ProgramRowsExceptSyntheticPrivateMatch':True,'dataOrSchemaOrPublicChanged':False,'newUpdaterActualLifecyclePending':True})]:(out/name).write_bytes(enc(obj))
print('OWN_G_VERIFIED_R26_UPDATER_AND_TWO_MANIFESTS_INSTALLED_NO_DATA_OR_SCHEMA_CHANGE')
