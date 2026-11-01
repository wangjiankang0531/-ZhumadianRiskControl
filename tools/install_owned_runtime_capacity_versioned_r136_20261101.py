from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess
R=Path('D:/Project/Zhumadian'); A=R/'_g/Application'; T=R/'Application/tools'; C=R/'work/event_delivery_consistency_20261030/full-controller-r136'; D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101'
J=lambda p:json.loads(p.read_bytes()); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
assert not(A.parent/'user-manual-protected.json').exists() and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
assert J(C/'r2/controller-terminal.json')['exitCode']==0 and J(C/'pool-contract-r3/result.json')['allPassed']
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0'
old=J(C/'candidate-install-r1/controller-fixture-ready.json'); assert sha(A/'release-manifest.json')==old['releaseSHA256']
assert sha(A/'tools/original_public_test_update.py')==old['updaterSHA256']
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
before=module('before_updater',A/'tools/original_public_test_update.py');after=module('after_updater',T/'original_public_test_update_r27_20261101.py')
assert sha(T/'original_public_test_update_r27_20261101.py')==J(C/'pool-contract-r3/result.json')['sourceSHA256']
release=J(A/'release-manifest.json');release[after.R24_WORKFLOW_FIELD]=after.R27_POOL_WORKFLOW_CONTRACT
release['controllerFiles']['tools/original_public_test_update.py']=sha(T/'original_public_test_update_r27_20261101.py')
assert after.runtime_pool_declared(release) is not None
bodies={'tools/original_public_test_update.py':(T/'original_public_test_update_r27_20261101.py').read_bytes(),'release-manifest.json':enc(release)}
changes={n:{'before':sha(A/n),'after':hashlib.sha256(v).hexdigest()}for n,v in bodies.items()};out=C/'candidate-install-r2';assert not out.exists();out.mkdir();bundle=out/'bundle'
for n,v in bodies.items():p=bundle/'payload'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
before.backup_code(A,out/'backup',changes)
try:before.replace_code(A,bundle,changes)
except BaseException:before.restore_code(A,out/'backup',changes);raise
assert all(sha(A/n)==p['after']for n,p in changes.items()) and all(sha(A/n)==v for n,v in release['controllerFiles'].items())
prepared=copy.deepcopy(old);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),updaterSHA256=sha(A/'tools/original_public_test_update.py'),wholeControllerActuallyStarted=False)
for n,o in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'writes':2,'onlyVersionedUpdaterAndReleaseManifestChanged':True,'privateConfigurationPayloadManifestJarsDatabaseOrSchemaChanged':False,'actualRuntimePending':True})]:(out/n).write_bytes(enc(o))
print('OWN_G_VERSIONED_UPDATER_INSTALLED_TWO_PATHS_NO_CONFIG_OR_DATA_CHANGE')
