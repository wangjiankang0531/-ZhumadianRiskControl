"""Independent completed-handle, restored-preimage and scoped CIM audit."""
from pathlib import Path
import datetime,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application'
J=lambda p:json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p)
 if not p.is_file():return None
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'bytes':p.stat().st_size,'sha256':h}
OUT=R/'Document/Deployment/event_r2_native_r1021_20261105/independent-restoration-r1023.json'
assert not OUT.exists()
z=R/'work/ev1021';proof=J(z/'verified-event-crud-r1021.json')
assert proof['passed']and proof['codeRestored']and proof['privateConfigurationRestored']and proof['originalCurrentPointerRestored']
assert len(proof['terminals'])==1
for t in proof['terminals']:
 assert t['controllerExitCode']==0 and t['actualJobDescendantsZero']and t['normalOwnedShutdown']and not t['forceTerminationUsed']
 assert set(t['exitCodes'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in t['exitCodes'].values())
assert proof['actualR2CandidatePreflights']==[
 {'transportedModule':False,'actualPoolMapperInitializerAndFileChecks':True},
 {'transportedModule':True,'actualPoolMapperInitializerAndFileChecks':True}]
ui=J(z/'browser/normal-restart/result.json')
assert ui['passed']and not ui['APIsMocked']and ui['eventCreatesObserved']==0
assert all(c['passed']for c in ui['cases'])and len(ui['cases'])==8
pointer=J(z/'pointer-snapshot/snapshot.private.json');config=J(z/'event-config/journal.private.json')
assert pointer['phase']=='restored'and pin(G/'UserData/OriginalServer/current-run.json')==pointer['before']
assert config['phase']=='restored'and pin(G/'private/server-configuration.json')==config['before']['private/server-configuration.json']
assert J(z/'code-transaction/journal.json')['phase']=='restored'
plan=J(R/'Document/Deployment/event_r2_native_r1021_20261105/full-source-and-restore-plan.private.json')
rows=dict(plan['mutations'])
for n,p in plan['retiredKnownFrontendPaths'].items():rows[n]={'before':p}
for n,p in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():rows[n]={'before':p}
assert all(pin(G/n)==row['before']for n,row in rows.items())
assert pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert pin(G/'release-manifest.json')['sha256']==plan['baseOwnedReleaseSHA256']
assert J(R/'work/ev1004/event-context.private.json')['phase']=='delete-and-false-save-verified'
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0','REAL_SUCCESSFUL_CIM_REQUIRED'
out={'passed':True,'at':datetime.datetime.now().astimezone().isoformat(),
 'actualR2UnmockedPoolMapperInitializerAndFilePreflights':2,'actualR2NormalSixComponentLifecycles':1,
 'controllerAndAllSixExit0BeforeJobClose':True,'actualJobDescendantsZero':True,'currentScopedElevatedCIMSucceededAndReferencesZero':True,
 'currentOriginalCodeAndCachePreimagesMatched':len(rows),'originalPrivateConfigurationInstallationAndDurablePointerRestored':True,
 'normalNonadminOriginalUIReadOnlyChecks':len(ui['cases']),'APIsMocked':False,'newBusinessWrites':0,
 'samePreviouslyDeletedRepairValidationRecordNotRecreated':True,'R1NativeUIFunctionalProofRetainedButNotCountedAsFreshR2CRUD':True,
 'actualSparseServiceUpdateIISTLSOrPublicAcceptance':False,'fullCloneReady':False}
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
