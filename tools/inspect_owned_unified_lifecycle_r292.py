from pathlib import Path
import hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/unified_update_owned_lifecycle_r292_20261103'
assert not D.exists();D.mkdir()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0','OWN_G_ALREADY_ACTIVE'
old=J(R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle/payload/release-manifest.json')
release=J(A/'release-manifest.json');config=J(A/'private/server-configuration.json')
identity=J(A/'UserData/OriginalServer/installation.json')
deployment=A/'UserData/OriginalDeployment/active-deployment.private.json'
resolved=J(R/'work/r38-unified-full-preflight-r288/resolution.json')
different=[];same=0
for n,pin in {**resolved['programs'],**resolved['controls']}.items():
    target=A/n;source=Path(pin['source'])
    if target.exists()and os.path.samefile(target,source):same+=1;continue
    if target.exists()and target.is_file()and target.stat().st_size==pin['bytes']and sha(target)==pin['sha256']:same+=1;continue
    assert not target.exists()or target.is_file(),'NON_FILE_COLLISION'
    different.append({'path':n,'source':str(source),'sourceSHA256':pin['sha256'],'sourceBytes':pin['bytes'],
      'beforeBytes':target.stat().st_size if target.exists()else None})
report={'inspectionOnly':True,'ownedSyntheticFixtureConfirmed':True,'ownedProcessesReferencingFixture':0,
 'currentOwnReleaseSHA256':sha(A/'release-manifest.json'),
 'releaseIdAlreadyMatchesR36':release.get('releaseId')==old.get('releaseId'),
 'installationReleaseIdAlreadyMatchesR36':identity.get('releaseId')==old.get('releaseId'),
 'installationFieldNames':sorted(identity),'deploymentRecordPresent':deployment.exists(),
 'deploymentFieldNames':sorted(J(deployment))if deployment.exists()else[],
 'configTopLevelKeys':sorted(config),'configHasBusinessArguments':isinstance(config.get('businessArguments'),list),
 'sameProgramOrControllerFiles':same,'differentProgramOrControllerFiles':len(different),
 'estimatedIndependentBaselineCopyBytes':sum(v['sourceBytes']for v in different),
 'estimatedBeforeCodeBackupBytes':sum(v['beforeBytes']or 0 for v in different),
 'exactPathsForOwnCodePreparationOnly':different,
 'databaseOrConfigValuesOrRuntimeUUIDsReturned':False,'servicesOrPublicOrDesktopTouched':False}
(D/'inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items()if k!='exactPathsForOwnCodePreparationOnly'}))
