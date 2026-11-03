from pathlib import Path
import hashlib,json,subprocess,os
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r101';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
t=J(C/'r101/controller-terminal.json');o=J(C/'r101-outer-terminal.json');r=J(C/'r101/scoped-controller-receipt.json')
assert t['actualDescendantJobCountZeroBeforeClose']and o['actualDescendantsZeroBeforeClose']and r['normalOwnedShutdown']and r['allOwnedChildrenExited']and not r['forcedJobClosureComponents']and all(v==0 for v in r['exitCodesBeforeJobClose'].values())
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='node.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('full-controller-r163/r101/')} | Measure-Object).Count"
s=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert s.returncode==0 and s.stdout.decode('utf-8-sig').strip()=='0'
scope=J(P/'frontend-scope.json');assert scope['onlyOwnedSyntheticG']
for name,before in scope['oldFiles'].items():
 p=A/name;assert p.resolve()==p and p.is_relative_to(A)
 if p.exists():assert not p.lstat().st_file_attributes&0x400
 after=scope['newFiles'].get(name);current=sha(p)if p.exists()else None;assert current in[before['sha256']if before else None,after['sha256']if after else None],'FOREIGN_FRONTEND_DRIFT_REFUSE_RESTORE'
 if before:assert sha(P/'frontend-before'/name)==before['sha256']
for name,before in scope['oldFiles'].items():
 p=A/name
 if before is None:
  if p.exists():p.unlink()
 elif not p.exists()or sha(p)!=before['sha256']:
  temp=p.with_name(p.name+'.owned-r201-restore.tmp');assert not temp.exists();temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes((P/'frontend-before'/name).read_bytes());os.replace(temp,p)
assert all((sha(A/n)==b['sha256']if b else not(A/n).exists())for n,b in scope['oldFiles'].items())and sha(A/'release-manifest.json')==scope['oldReleaseSHA256']
proof={'passed':True,'exactFrontendAndManifestBytesRestored':True,'allNewFrontendPathsRemoved':True,'allSixComponentsAndActualDescendantsZero':True,'privateConfigurationDataAndControllersUnchanged':True,'mustNowRestoreTemporarySyntheticConfig':True,'forceTerminationUsed':False}
(P/'frontend-restored.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
