from pathlib import Path
import hashlib,json,subprocess,os
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r106';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
terminal=J(C/'r106/controller-terminal.json');outer=J(C/'r106-outer-terminal.json');started=J(C/'r106/controller-started.json')
assert terminal['pid']==started['pid']and terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and not terminal['forceTerminationUsed']and not outer['forceTerminationUsed']
early=False
receipt=J(C/'r106/scoped-controller-receipt.json');assert receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and not receipt['jobAssignmentFailureComponents']
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='node.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('full-controller-r163/r106/')} | Measure-Object).Count"
s=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert s.returncode==0 and s.stdout.decode('utf-8-sig').strip()=='0'
scope=J(P/'history-runtime-scope.json');stock=J(P/'temporary-synthetic-config-scope.json');assert scope['onlyOwnedSyntheticG'];targets={}
for name,old in scope['oldFiles'].items():
 p=A/name;b=P/'history-before'/name;assert p.resolve()==p and b.resolve()==b and not p.lstat().st_file_attributes&0x400 and sha(b)==old['sha256']
 candidates={old['sha256'],scope['newFiles'][name]['sha256']}
 if name in stock['files']:
  pin=stock['files'][name];original=P/'before'/name;assert sha(original)==pin['beforeSHA256']and old['sha256']==pin['afterSHA256'];candidates.add(pin['beforeSHA256']);targets[name]=original.read_bytes()
 else:targets[name]=b.read_bytes()
 assert sha(p)in candidates,'OWN_HISTORY_FOREIGN_DRIFT_REFUSED'
for name in scope['newPaths']:
 p=A/name;assert p.resolve()==p and p.is_file()and not p.lstat().st_file_attributes&0x400 and sha(p)==scope['newFiles'][name]['sha256'],'NEW_HISTORY_PATH_DRIFT_REFUSED'
for name,raw in targets.items():
 p=A/name
 if p.read_bytes()==raw:continue
 temp=p.with_name(p.name+'.own-r215-restore.tmp');assert not temp.exists();temp.write_bytes(raw);os.replace(temp,p)
for name in scope['newPaths']:(A/name).unlink()
assert all(not(A/name).exists()for name in scope['newPaths'])
assert all((A/n).read_bytes()==b for n,b in targets.items())and all(sha(A/n)==pin['beforeSHA256']for n,pin in stock['files'].items())
proof={'passed':True,'exactOriginalBytesRestored':True,'originalObservationJarAndFakeConfigurationAndManifestBytesRestored':True,'allActualDescendantsZero':True,'earlyCallbackPreflightRejectedBeforeOwnerOrRunAllocation':early,'businessDatabaseOrHistoryRowsRewritten':False,'forceTerminationUsed':False,'formalOrPublicOrR34Operated':False}
for name in ['configuration-restored.json','history-runtime-restored.json']:(P/name).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
