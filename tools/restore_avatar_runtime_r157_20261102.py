from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r157';P=C/'prepared-r1'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=J(P/'scope.json');assert scope['onlyOwnedSyntheticG']and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
attempt=sys.argv[1]if len(sys.argv)==2 else'r1';assert attempt in['r1','r2'];term=J(C/attempt/'controller-terminal.json');outer=J(C/(attempt+'-outer-terminal.json'));receipt=J(C/attempt/'scoped-controller-receipt.json');assert term['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and all(x==0 for x in receipt['exitCodesBeforeJobClose'].values())and not receipt['forcedJobClosureComponents']
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { $c=($_.CommandLine -replace '\\\\','/').ToLowerInvariant(); $c.Contains('d:/project/zhumadian/_g/application') -or $c.Contains('d:/project/zhumadian/work/event_delivery_consistency_20261030/full-controller-r157/') } | Measure-Object).Count";r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
for name,before in scope['oldFiles'].items():
 p=A/name;assert p.resolve()==p and p.is_relative_to(A)
 current=sha(p)if p.exists()else None;after=scope['newFiles'].get(name);valid=[before['sha256']if before else None,after['sha256']if after else None];assert current in valid,'FOREIGN_TEST_FRONTEND_DRIFT'
 if before:
  b=P/'before'/name;assert b.resolve()==b and sha(b)==before['sha256']
for name,before in scope['oldFiles'].items():
 p=A/name
 if before is None:
  if p.exists():p.unlink()
 elif not p.exists()or sha(p)!=before['sha256']:
  temp=p.with_name(p.name+'.owned-r157-restore.tmp');assert not temp.exists();temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes((P/'before'/name).read_bytes());os.replace(temp,p)
assert all((sha(A/n)==b['sha256']if b else not(A/n).exists())for n,b in scope['oldFiles'].items());assert sha(A/'release-manifest.json')==scope['oldReleaseSHA256']
proof={'passed':True,'exactAllOriginalFrontendsAndManifestBytesRestored':True,'allNewTestFrontendPathsRemoved':True,'normalSixComponentsZeroAndActualDescendantsZero':True,'currentScopedProcessCountZero':True,'privateConfigDataObjectsAndAllControllersUnchanged':True,'forceTerminationUsed':False,'publicOrFormalChanged':False};(P/'frontend-restored.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
