from pathlib import Path
import json,hashlib,subprocess,os,sys
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r127';D=R/'Document/Deployment/original_mapper_registration_r257_20261103';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=J(C/'r127/scoped-controller-receipt.json');outer=J(C/'r127-outer-terminal.json');terminal=J(C/'r127/controller-terminal.json')
assert receipt['failureStageMessage']=='OWN_COMPONENT_EXITED:business'and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and not receipt['jobAssignmentFailureComponents']and receipt['exitCodesBeforeJobClose']=={'store':0,'mysql':0,'redis':0,'platform':0,'business':1}
assert outer['actualDescendantsZeroBeforeClose']and terminal['actualDescendantJobCountZeroBeforeClose']and not outer['forceTerminationUsed']and not terminal['forceTerminationUsed']
diag=J(D/'startup-failure-diagnostic.json');assert any('OWN_MAPPER_OBSERVATION_FAILED'in x['uppercaseExceptionCodes']and any('R257.java:31)'in f for f in x['ownObserverFrames'])for x in diag['diagnostics'])
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
scope=J(P/'mapper-observer-scope.json');assert scope['onlyOwnedStoppedSyntheticFixture']and scope['observerOnlyOrCandidateSetting']=='r127'
for n,pin in scope['newFiles'].items():assert(A/n).resolve()==A/n and sha(A/n)==pin['sha256']and not(A/n).lstat().st_file_attributes&0x400
for n,pin in scope['oldFiles'].items():assert sha(P/'mapper-observer-before'/n)==pin['sha256']
for n in scope['newPaths']:(A/n).unlink()
for n in scope['oldFiles']:
 p=A/n;tmp=p.with_name(p.name+'.own-r259-recovery.tmp');assert not tmp.exists();tmp.write_bytes((P/'mapper-observer-before'/n).read_bytes());os.replace(tmp,p)
assert all(sha(A/n)==pin['sha256']for n,pin in scope['oldFiles'].items())
proof={'passed':True,'allActualDescendantsZeroBeforeRestore':True,'observerAssertionFailed':True,'businessNormalStartupClaimed':False,'onlyOwnListenerJarAndConfigManifestBytesRestored':True,'dataOrSchemaRewrittenByRestore':False}
(P/'mapper-observer-restored.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
r=subprocess.run([sys.executable,str(R/'Application/tools/restore_production_history_runtime_r257_baseline.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and json.loads(r.stdout)['passed']
original=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256'];assert sha(A/'release-manifest.json')==original
(D/'failed-observation-recovery-r259.json').write_text(json.dumps({**proof,'historyAndSyntheticConfigurationRestoredExactBytes':True,'originalReleaseRestored':True,'original398ComparisonReached':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'recovered':True,'originalReleaseRestored':True,'actualRegistrationNotYetVerified':True}))
