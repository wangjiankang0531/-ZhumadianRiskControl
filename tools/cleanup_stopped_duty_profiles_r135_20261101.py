from pathlib import Path
import datetime,json,re,shutil,subprocess
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r135';D=R/'Document/Deployment/emergency_duty_native_r135_20261101'
assert C.resolve()==C.absolute()and not(R/'_g/user-manual-protected.json').exists()
cmd="$ErrorActionPreference='Stop';(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\"|Where-Object{($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/work/event_delivery_consistency_20261030/full-controller-r135/') -and ($_.CommandLine -replace '\\\\','/').Contains('/chrome-profile')}|Measure-Object).Count"
observed=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert observed.returncode==0 and observed.stdout.decode('utf-8-sig').strip()=='0','OWN_DUTY_CHROME_STILL_LIVE_OR_OBSERVATION_FAILED'
targets=[]
for p in sorted(C.iterdir()):
    if not p.is_dir()or not re.fullmatch(r'r(?:[1-9]|10|11)',p.name):continue
    target=p/'duty-browser/chrome-profile'
    if not target.exists():continue
    browser=json.loads((p/'duty-browser/browser-terminal.json').read_bytes());controller=json.loads((p/'controller-terminal.json').read_bytes());receipt=json.loads((p/'scoped-controller-receipt.json').read_bytes())
    assert browser['chromeExitCode']==0 and not browser['forceTerminationUsed']and controller['exitCode']==0 and controller['actualDescendantJobCountZeroBeforeClose']and receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']
    resolved=target.resolve();assert resolved.is_relative_to(C.resolve())and resolved==target.absolute()and target.name=='chrome-profile'
    for node in [target,*target.rglob('*')]:assert not node.is_symlink()and not getattr(node.lstat(),'st_file_attributes',0)&0x400
    files=[node for node in target.rglob('*')if node.is_file()];targets.append({'attempt':p.name,'target':str(target),'files':len(files),'logicalBytes':sum(n.stat().st_size for n in files)})
before=shutil.disk_usage(R).free
for row in targets:shutil.rmtree(row['target']);assert not Path(row['target']).exists()
after=shutil.disk_usage(R).free
result={'at':datetime.datetime.now().astimezone().isoformat(),'onlyOwnedNormallyStoppedChromeProfilesRemoved':True,'profiles':len(targets),'files':sum(r['files']for r in targets),'logicalBytes':sum(r['logicalBytes']for r in targets),'observedDiskFreeIncrease':after-before,'diskFreeObservationMayIncludeConcurrentActivity':True,'allSourcesFailuresProofsDownloadsAndSyntheticDatabasesKept':True,'publicDesktopFormalOrProtectedUserRootsTouched':False,'targets':targets}
(D/'stopped-profile-cleanup.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k!='targets'}))
