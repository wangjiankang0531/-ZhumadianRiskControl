from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r136';D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
assert not(A.parent/'user-manual-protected.json').exists()and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
assert J(C/'r1/result.json')['allPassed']and J(C/'r1/controller-terminal.json')['exitCode']==0 and J(C/'r1/duty-browser/browser-terminal.json')['chromeExitCode']==0
assert J(D/'pool-policy-binding-verification.json')['actualBinding']['mappedMaximum']==4
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0','OWN_G_STILL_LIVE'
old=J(R/'work/event_delivery_consistency_20261030/full-controller-r135/candidate-install-r2/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==old['releaseSHA256'];release=J(A/'release-manifest.json');pins=J(D/'runtime-candidate-source-pins.json')['twoControllerSources'];bodies={}
for name,pin in pins.items():
    assert sha(A/name)==release['controllerFiles'][name]==pin['beforeSHA256'];raw=(T/'connection-budget-r136'/Path(name).name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin['afterSHA256'];bodies[name]=raw;release['controllerFiles'][name]=pin['afterSHA256']
release['publicTestRevision']='owned-R136-matched-pool-family-and-budget';release['runtimeConnectionPoolPolicy']={'revision':'pool-family-budget-v1','mysqlMinimum':24,'mysqlMaximum':256,'reservedConnections':12,'maximumSinglePool':128};bodies['release-manifest.json']=enc(release)
changes={n:{'before':sha(A/n),'after':hashlib.sha256(raw).hexdigest()}for n,raw in bodies.items()};out=C/'candidate-install-r1';assert not out.exists();out.mkdir();bundle=out/'bundle'
for n,raw in bodies.items():p=bundle/'payload'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
spec=importlib.util.spec_from_file_location('owned_exact_update',A/'tools/original_public_test_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.backup_code(A,out/'backup',changes)
try:m.replace_code(A,bundle,changes)
except BaseException:m.restore_code(A,out/'backup',changes);raise
assert all(sha(A/n)==p['after']for n,p in changes.items())and all(sha(A/n)==pin for n,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(old);prepared.update(controllerSHA256=sha(A/'tools/serve_original_server_release.py'),releaseSHA256=sha(A/'release-manifest.json'),wholeControllerActuallyStarted=False)
for n,o in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'writes':3,'onlyTwoControllerSourcesAndReleaseManifestChanged':True,'privateConfigurationPayloadManifestJarsDatabaseOrSchemaChanged':False,'actualRuntimePending':True})]:(out/n).write_bytes(enc(o))
print('OWN_G_POOL_POLICY_CANDIDATE_INSTALLED_THREE_PROGRAM_PATHS_NO_CONFIG_OR_DATA_CHANGE')
