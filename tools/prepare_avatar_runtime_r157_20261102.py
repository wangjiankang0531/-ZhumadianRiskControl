from pathlib import Path
import copy,hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';W=R/'work/user_feedback_20261031/avatar-full-r157';C=R/'work/event_delivery_consistency_20261030/full-controller-r157';P=C/'prepared-r1'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert J(W/'independent-full-build-verification.json')['passed'];assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
baseline=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==baseline['releaseSHA256'];assert not P.exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count";r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');old={n:p for n,p in q['files'].items()if n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))};new={};roots={'security_pc':W/'security_pc/build/dist','emergency_pc':W/'emergency_pc/dist'}
assert len(old)==1175
for name,pin in old.items():assert (A/name).stat().st_size==pin['bytes']and sha(A/name)==pin['sha256']
for role,root in roots.items():
 for p in root.rglob('*'):
  if not p.is_file():continue
  n='frontend/'+role+'/'+p.relative_to(root).as_posix();new[n]={'bytes':p.stat().st_size,'sha256':sha(p)}
assert len(new)==1175
P.mkdir(parents=True);paths=set(old)|set(new)|{'payload-manifest.json','release-manifest.json'};before={}
for n in sorted(paths):
 p=A/n;assert p.resolve()==p
 if p.exists():
  assert p.is_file()and not p.is_symlink()and not p.lstat().st_file_attributes&0x400;raw=p.read_bytes();b=P/'before'/n;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(raw);before[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 else:before[n]=None
q['files']={n:p for n,p in q['files'].items()if n not in old};q['files'].update(new);qraw=enc(q);release['payloadManifestSHA256']=hashlib.sha256(qraw).hexdigest();rraw=enc(release)
after=dict(new);after.update({'payload-manifest.json':{'bytes':len(qraw),'sha256':hashlib.sha256(qraw).hexdigest()},'release-manifest.json':{'bytes':len(rraw),'sha256':hashlib.sha256(rraw).hexdigest()}})
scope={'onlyOwnedSyntheticG':True,'oldFiles':before,'newFiles':after,'oldReleaseSHA256':baseline['releaseSHA256'],'mustRestoreAfterActualDescendantsZero':True,'configurationDataObjectsAndControllersChanged':False};(P/'scope.json').write_bytes(enc(scope))
for n in old.keys()-new.keys():(A/n).unlink()
for n,pin in new.items():
 if n in old and old[n]==pin:continue
 role=n.split('/')[1];raw=(roots[role]/n.split('/',2)[2]).read_bytes();target=A/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():target.unlink()
 target.write_bytes(raw)
for n,raw in [('payload-manifest.json',qraw),('release-manifest.json',rraw)]:
 p=A/n;p.unlink();p.write_bytes(raw)
assert all(sha(A/n)==p['sha256']for n,p in after.items());baseline.update(releaseSHA256=sha(A/'release-manifest.json'),temporaryOwnAvatarFullFrontendOnly=True);(P/'controller-fixture-ready.json').write_bytes(enc(baseline));(P/'own-serial-definition.json').write_bytes((R/'work/event_delivery_consistency_20261030/full-controller-r154/closed-readback-r1/own-serial-definition.json').read_bytes())
print(json.dumps({'onlyOwnCandidateFrontendsPrepared':True,'frontendFiles':len(new),'configurationDatabaseAndAll20ControlsKept':True,'mustRestore':True}))
