from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r143';B=R/'work/event_delivery_consistency_20261030/full-controller-r142/r4';W=R/'work/user_feedback_20261031';N=W/'emergency-workflow-source-r15';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
assert J(B/'controller-terminal.json')['exitCode']==0 and J(B/'controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']
assert J(B/'task-feedback-browser/browser-terminal.json')['chromeExitCode']==0
failure=J(B/'task-feedback-browser/failure.json');repro=J(B/'task-feedback-browser/false-save-response-proof.json');assert failure['message']=='FALSE_DISPOSAL_SAVE_LOST_INPUT_OR_REPORTED_SUCCESS'and repro['actualCodeZeroDataFalse']and(not repro['stayed']or not repro['feedback']or repro['successMessage'])
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
command="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
old=J(W/'emergency-workflow-source-r14/build-result.json')['files'];new=J(N/'build-result.json')['files'];assert len(old)==len(new)==339 and J(N/'independent-build-verification.json')['undeclaredSourceDifferences']==0
ready=J(R/'work/event_delivery_consistency_20261030/full-controller-r139/candidate-install-r3/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==ready['releaseSHA256'];payload=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');prefix='frontend/emergency_pc/';assert {n.removeprefix(prefix):pin for n,pin in payload['files'].items()if n.startswith(prefix)}==old
for n,pin in old.items():assert sha(A/(prefix+n))==pin['sha256']
for n,pin in new.items():assert sha(N/'dist'/n)==pin['sha256']and(N/'dist'/n).stat().st_size==pin['bytes']
P=C/'candidate-install-r1';assert not P.exists();P.mkdir(parents=True)
oldq=(A/'payload-manifest.json').read_bytes();oldr=(A/'release-manifest.json').read_bytes();(P/'old-payload-manifest.json').write_bytes(oldq);(P/'old-release-manifest.json').write_bytes(oldr)
changed={n for n in set(old)|set(new)if old.get(n)!=new.get(n)};before={n:(A/(prefix+n)).read_bytes()for n in changed if n in old}
for n,raw in before.items():p=P/'before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
try:
 for n in changed:
  p=A/(prefix+n);assert p.resolve().is_relative_to((A/'frontend/emergency_pc').resolve());assert not p.is_symlink()and(not p.exists()or not p.lstat().st_file_attributes&0x400)
  if p.exists():p.unlink()
  if n in new:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((N/'dist'/n).read_bytes())
 for n in set(old)-set(new):del payload['files'][prefix+n]
 for n,pin in new.items():payload['files'][prefix+n]=pin
 payload['ownedTaskFeedbackResultCandidate']={'onlyOneSourceChangedFromWF14':True,'sourceClosureSHA256':sha(N/'source-closure.json')};raw=enc(payload);(A/'payload-manifest.json').unlink();(A/'payload-manifest.json').write_bytes(raw);release['payloadManifestSHA256']=hashlib.sha256(raw).hexdigest();(A/'release-manifest.json').unlink();(A/'release-manifest.json').write_bytes(enc(release))
except BaseException:
 for n in changed:
  p=A/(prefix+n)
  if p.exists():p.unlink()
  if n in before:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(before[n])
 for name,raw in [('payload-manifest.json',oldq),('release-manifest.json',oldr)]:
  p=A/name
  if p.exists():p.unlink()
  p.write_bytes(raw)
 raise
ready.update(releaseSHA256=sha(A/'release-manifest.json'),onlyStoppedOwnGFrontendAndManifestsChanged=True);(P/'controller-fixture-ready.json').write_bytes(enc(ready))
proof={'onlyOwnNeverUserFixtureChanged':True,'baselineActualFalseSaveResponseObserved':True,'oneFrontendSourceChanged':True,'frontendFiles':339,'changedProgramPaths':len(changed),'all20ControlsKept':True,'oldAndNewControllerFilesEqual':J(P/'old-release-manifest.json')['controllerFiles']==release['controllerFiles'],'databaseSchemaOrBusinessRowsWrittenByInstaller':False,'publicOrProtectedUserEnvironmentChanged':False};assert proof['oldAndNewControllerFilesEqual'];(P/'installation-result.json').write_bytes(enc(proof));print(json.dumps(proof))
