from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';W=R/'work/user_feedback_20261031/plan-exercise-retained-r221';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r110'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert J(W/'full-build-result.json')['passed']and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert P.exists()and not(P/'frontend-scope.json').exists()and not(C/'r110').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
baseline=J(P/'controller-fixture-ready.json');assert sha(A/'release-manifest.json')==baseline['releaseSHA256']
q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');old={n:p for n,p in q['files'].items()if n.startswith('frontend/emergency_pc/')};new={'frontend/emergency_pc/'+n:p for n,p in J(W/'full-build-result.json')['compiledFiles'].items()};assert len(old)==339 and len(new)==341
for name,pin in old.items():assert (A/name).stat().st_size==pin['bytes']and sha(A/name)==pin['sha256']
before={}
for n in sorted(set(old)|set(new)|{'payload-manifest.json','release-manifest.json'}):
 p=A/n;assert p.resolve()==p
 if p.exists():
  assert p.is_file()and not p.lstat().st_file_attributes&0x400;raw=p.read_bytes();b=P/'frontend-before'/n;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(raw);before[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 else:before[n]=None
q['files']={n:p for n,p in q['files'].items()if n not in old};q['files'].update(new);qraw=enc(q);release['payloadManifestSHA256']=hashlib.sha256(qraw).hexdigest();rraw=enc(release)
after={**new,'payload-manifest.json':{'bytes':len(qraw),'sha256':hashlib.sha256(qraw).hexdigest()},'release-manifest.json':{'bytes':len(rraw),'sha256':hashlib.sha256(rraw).hexdigest()}}
scope={'onlyOwnedSyntheticG':True,'oldFiles':before,'newFiles':after,'oldReleaseSHA256':baseline['releaseSHA256'],'mustRestoreAfterActualDescendantsZero':True,'configurationDataObjectsAndControllersChanged':False}
(P/'frontend-scope.json').write_bytes(enc(scope))
for n in old.keys()-new.keys():(A/n).unlink()
for n,pin in new.items():
 if old.get(n)==pin:continue
 raw=(W/'dist'/n.split('/',2)[2]).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin['sha256'];p=A/n;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():p.unlink()
 p.write_bytes(raw)
for n,raw in [('payload-manifest.json',qraw),('release-manifest.json',rraw)]:p=A/n;p.unlink();p.write_bytes(raw)
assert all(sha(A/n)==pin['sha256']for n,pin in after.items())
baseline['releaseSHA256']=sha(A/'release-manifest.json');baseline['temporaryPendingVisibilityFrontendOnly']=True
(P/'controller-fixture-ready.json').write_bytes(enc(baseline))
print(json.dumps({'prepared':True,'candidateFrontendFiles':341,'onlyOwnedSyntheticG':True,'allControllersAndPrivateConfigKept':True,'mustRestoreFrontendThenTemporaryConfig':True}))
