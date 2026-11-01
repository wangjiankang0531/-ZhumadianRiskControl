"""Install only verified WF13 program bytes into the stopped never-user-delivered synthetic _g."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r135';F=R/'work/user_feedback_20261031/emergency-workflow-source-r13'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest()
assert A.resolve()==A.absolute()and not(A.parent/'user-manual-protected.json').exists()and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
assert J(F/'independent-build-verification.json')['allBuildBytesAndSourcePinsVerified']
terminal=J(C/'r8/controller-terminal.json');receipt=J(C/'r8/scoped-controller-receipt.json');assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed'];assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(c==0 for c in receipt['exitCodesBeforeJobClose'].values())and J(C/'r8/duty-browser/browser-terminal.json')['chromeExitCode']==0
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
observed=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert observed.returncode==0 and observed.stdout.decode('utf-8-sig').strip()=='0','OWN_G_PROCESS_STILL_PRESENT'
oldPrepared=J(R/'work/event_delivery_consistency_20261030/full-controller-r134/candidate-install-r1/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==oldPrepared['releaseSHA256']
oldq=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');assert sha(A/'payload-manifest.json')==release['payloadManifestSHA256']
prefix='frontend/emergency_pc/';b=J(F/'build-result.json');q=copy.deepcopy(oldq);q['files']={n:v for n,v in oldq['files'].items()if not n.startswith(prefix)};q['files'].update({prefix+n:copy.deepcopy(pin)for n,pin in b['files'].items()})
changes={};bodies={}
for name in set(oldq['files'])|set(q['files']):
    if not name.startswith(prefix):assert oldq['files'].get(name)==q['files'].get(name);continue
    old=oldq['files'].get(name);new=q['files'].get(name)
    if old==new:assert sha(A/name)==old['sha256'];continue
    if old:assert sha(A/name)==old['sha256']
    else:assert not(A/name).exists()
    if new:
        raw=(F/'dist'/name.removeprefix(prefix)).read_bytes();assert len(raw)==new['bytes']and digest(raw)==new['sha256'];bodies[name]=raw
    changes[name]={'before':old['sha256']if old else None,'after':new['sha256']if new else None}
bodies['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);release['publicTestRevision']='owned-R135-WF13-native-duty-picker-only';release['publicAccepted']=False;bodies['release-manifest.json']=enc(release)
for name in ['payload-manifest.json','release-manifest.json']:changes[name]={'before':sha(A/name),'after':digest(bodies[name])}
assert len(q['files'])==len(oldq['files'])and len(b['files'])==339 and sum(map(len,bodies.values()))<32*1024**2 and shutil.disk_usage(R).free>1024**3
out=C/'candidate-install-r1';assert not out.exists();out.mkdir();bundle=out/'bundle'
for name,raw in bodies.items():p=bundle/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
spec=importlib.util.spec_from_file_location('verified_r26_owned_update',A/'tools/original_public_test_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.backup_code(A,out/'backup',changes)
try:m.replace_code(A,bundle,changes)
except BaseException:m.restore_code(A,out/'backup',changes);raise
assert all((sha(A/n)==pin['after']if pin['after']else not(A/n).exists())for n,pin in changes.items())and all(sha(A/n)==pin for n,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(oldPrepared);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),wholeControllerActuallyStarted=False)
for name,obj in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'onlyStoppedOwnedGFrontendAndTwoManifestsChanged':True,'writes':len(bodies),'oldFrontendRemoved':sum(p['after']is None for p in changes.values()),'backendControllersPrivateDatabaseSchemasAndPublicKept':True,'actualNativeCandidateFlowPending':True})]:(out/name).write_bytes(enc(obj))
print('OWN_G_VERIFIED_WF13_DUTY_PICKER_ONLY_FRONTEND_INSTALLED_NO_DATA_OR_SCHEMA_CHANGE')
