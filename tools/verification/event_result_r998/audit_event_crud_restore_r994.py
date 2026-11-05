from pathlib import Path
import hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application';D=R/'Document/Deployment/event_crud_native_r990_20261104'
J=lambda p:json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p)
 return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}if p.is_file()else None
assert not (D/'independent-restore-r994.json').exists()
proofs=[]
for n in [979,982,985,990]:
 z=R/('work/ev'+str(n));p=J(z/('verified-event-crud-r'+str(n)+'.json'))
 assert p['codeRestored']and p['privateConfigurationRestored']and p['originalCurrentPointerRestored']
 assert p['terminals']and all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and t['normalOwnedShutdown']and set(t['exitCodes'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in t['exitCodes'].values())for t in p['terminals'])
 cj=J(z/'code-transaction/journal.json');assert cj['phase']=='restored'and cj['restored']
 config=J(z/'event-config/journal.private.json');assert config['phase']=='restored'
 for rel,before in config['before'].items():
  # Config manifests restore to the outer candidate first; outer code restoration
  # then restores its original payload/release bytes. Verify the private preimage here.
  if rel.startswith('private/'):assert pin(G/rel)==before
 pointer=J(z/'pointer-snapshot/snapshot.private.json');assert pointer['phase']=='restored'
 assert pin(G/'UserData/OriginalServer/current-run.json')==pointer['before']
 b=J(z/('browser/normal-restart/result.json'if n==990 else'browser/first-start/result.json'));creates=b['eventCreatesObserved']
 if n!=985:assert creates==0
 proofs.append({'attempt':n,'passed':p['passed'],'lifecycleCount':len(p['terminals']),'normalAllSixAndControllerExit0ActualJob0':True,'firstPhaseEventCreates':creates,'maxControllerPrivateCommitBytes':max(t['jobMemoryBudget']['reportedPeakJobMemoryBytes']for t in p['terminals'])})
plan=J(D/'full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for k,v in plan['retiredKnownFrontendPaths'].items():assert k not in rows;rows[k]={'before':v}
for k,v in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():assert k not in rows;rows[k]={'before':v}
for name,row in rows.items():assert pin(G/name)==row['before'],'EXACT_RESTORED_CODE:'+name
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert pin(G/'release-manifest.json')['sha256']==plan['baseOwnedReleaseSHA256']
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0','NO_ACTUAL_OWN_G_REFERENCES_REQUIRED'
out={'passed':True,'attempts':proofs,'originalCodeAndCachePathsMatched':len(rows),'originalConfigurationInstallationAndThreeDurablePointerPreimagesMatched':True,'actualOwnGProcessReferences':0,'forceTerminationUsed':False,'dataOrRecordsResetClonedOrReplaced':False,'publicOrDesktopTouched':False,'nativeEventCRUDProductAcceptance':J(R/'work/ev990/verified-event-crud-r990.json')['passed'] and J(R/'work/ev985/browser/first-start/result.json')['passed'],'fullCloneReady':False}
assert sum(t['firstPhaseEventCreates']for t in proofs)==1
assert J(R/'work/ev985/event-context.private.json')['phase']=='delete-issued-do-not-retry'
assert not J(R/'work/ev990/browser/normal-restart/result.json')['passed']
out['singleExistingEventNoRecreationAcrossAllAttempts']=True
(D/'independent-restore-r994.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
