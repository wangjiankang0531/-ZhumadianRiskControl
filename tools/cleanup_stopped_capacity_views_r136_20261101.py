from pathlib import Path
import json,shutil,subprocess,os
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r136';D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101'
J=lambda p:json.loads(p.read_bytes());targets=[]
for n in ['r1','r3','r4']:
 assert J(C/n/'controller-terminal.json')['exitCode']==0 and J(C/n/'duty-browser/browser-terminal.json')['chromeExitCode']==0
 targets.append(C/n/'duty-browser/chrome-profile')
assert J(C/'pool-contract-r3/result.json')['allPassed'];targets.append(C/'pool-contract-r3/Application')
for p in targets:
 resolved=p.resolve();assert resolved.is_relative_to(C.resolve()) and not p.is_symlink() and p.exists()
 # Own paths only; never include _g, database, source, result or protected user roots.
 assert p.name in ['chrome-profile','Application']
query="(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' OR Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('full-controller-r136/') -and $_.ProcessId -ne "+str(os.getpid())+" } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0','OWN_PROCESS_STILL_LIVE'
before=shutil.disk_usage(R).free;rows=[]
for p in targets:
 files=[q for q in p.rglob('*')if q.is_file()];rows.append({'path':p.relative_to(C).as_posix(),'files':len(files),'logicalBytes':sum(q.stat().st_size for q in files),'logicalBytesNotClaimedAsPhysicalRecovery':True})
 shutil.rmtree(p)
result={'allTargetsResolvedUnderOwnAttemptRoot':True,'normalZeroTerminalAndNoLiveProcessVerified':True,'removedOnlyStoppedProfilesAndPassiveContractProgramView':True,'sourceProofsFailuresDownloadsAndOwnDatabasePreserved':True,'logicalHardlinksNotCountedAsPhysicalRecovery':True,'rows':rows,'observedFreeBytesBefore':before,'observedFreeBytesAfter':shutil.disk_usage(R).free,'freeChangeSubjectToConcurrentActivity':True}
(D/'stopped-view-cleanup.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'targets':len(rows),'files':sum(q['files']for q in rows),'observedFreeChange':result['observedFreeBytesAfter']-before}))
