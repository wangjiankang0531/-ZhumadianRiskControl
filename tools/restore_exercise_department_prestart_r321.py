from pathlib import Path
import hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r139'
D=R/'Document/Deployment/native_plan_delete_roundtrip_r320_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(C/'r139').exists(),'NOT_AN_EARLY_PREALLOCATION_REFUSAL'
outer=J(C/'r139-outer-terminal.json');assert outer['exitCode']==1 and outer['actualDescendantsZeroBeforeClose']and not outer['forceTerminationUsed']
trace=(C/'r139-outer.private.log').read_text(encoding='utf-8')
assert 'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in trace
source=(R/'Application/tools/verify_full_controller_plan_delete_r320.py').read_text(encoding='utf-8').splitlines()
assert any('OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY' in line for line in source)
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='node.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or $_.CommandLine.Contains('verify_full_controller_plan_delete_r320.py') -or $_.CommandLine.Contains('run_native_plan_delete_r320.py') } | Measure-Object).Count"
s=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert s.returncode==0 and s.stdout.decode('utf-8-sig').strip()=='0','OWN_PRESTART_PROCESS_STILL_ACTIVE'

view={};original={}
def raw(name):
    p=A/name
    assert '..'not in Path(name).parts and not name.startswith(('Assets/','UserData/','Reference/','seed/'))
    for q in [p,*p.parents]:
        if q==A.parent:break
        if q.exists():assert not q.is_symlink()and not getattr(q.lstat(),'st_file_attributes',0)&0x400
    if name not in view:view[name]=p.read_bytes()if p.exists()else None;original[name]=view[name]
    return view[name]
def pin(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}if data is not None else None
def layer(label,scope,backup):
    expected={n:scope['newFiles'].get(n)for n in set(scope['oldFiles'])|set(scope['newFiles'])}
    for name,value in expected.items():assert pin(raw(name))==value,'FOREIGN_DRIFT_BEFORE_RESTORE_'+label+':'+name
    for name,value in scope['oldFiles'].items():
        before=P/backup/name
        if value is None:view[name]=None
        else:
            data=before.read_bytes();assert pin(data)==value;view[name]=data
    for name in scope.get('newPaths',[]):assert name not in scope['oldFiles'];view[name]=None

frontend=J(P/'frontend-scope.json');assert frontend['onlyOwnedSyntheticG'];layer('frontend',frontend,'frontend-before')
observer=J(P/'mapper-observer-scope.json');assert observer['onlyOwnedStoppedSyntheticFixture'];layer('observer',observer,'mapper-observer-before')
product=J(P/'mapper-product-scope.json');assert product['onlyOwnedStoppedSyntheticFixture'];layer('product',product,'mapper-product-before')
history=J(P/'history-runtime-scope.json');assert history['onlyOwnedSyntheticG'];layer('history',history,'history-before')
serial=J(P/'temporary-synthetic-config-scope.json');assert serial['onlyOwnedG']
for name,pins in serial['files'].items():
    assert pin(raw(name))['sha256']==pins['afterSHA256'];before=(P/'before'/name).read_bytes();assert hashlib.sha256(before).hexdigest()==pins['beforeSHA256'];view[name]=before
assert hashlib.sha256(view['release-manifest.json']).hexdigest()=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
for name,data in view.items():assert raw(name)==data  # all virtual layers fully validated before writes
# Verify the actual tree has not changed while the complete unwind was checked.
for name,data in original.items():assert (A/name).read_bytes()==data if data is not None else not(A/name).exists()
names=sorted(view,key=lambda n:(n=='release-manifest.json',n))
for name in names:
    data=view[name];p=A/name
    if data is None:
        if p.exists():p.unlink()
    elif original[name]!=data:
        tmp=p.with_name(p.name+'.own-r300-prestart-restore.tmp');assert not tmp.exists();tmp.write_bytes(data);os.replace(tmp,p)
assert all((A/name).read_bytes()==data if data is not None else not(A/name).exists()for name,data in view.items())
assert sha(A/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
proof={'passed':True,'attempt':'r139','refusalBeforeTestRootOrControllerAllocation':True,
 'declaredAvailableMemoryMinimumGiB':4,'exactAvailableMemoryAtRefusalNotCaptured':True,
 'actualDescendantsZeroAndCurrentProcessAbsenceVerified':True,
 'normalSixComponentReceiptsFabricated':False,'virtualLayerPinsAndAllPreimagesCheckedBeforeWrites':True,
 'restoredLayers':['frontend','observer','product','history','synthetic-flow-configuration'],
 'restoredPathStates':len(view),'originalGCodeAndFakeConfigurationAndManifestsRestored':True,
 'newBusinessBrowserCasesExecuted':0,'candidateBusinessAccepted':False,
 'databaseOrPublicOrFormalOrSceneOrDesktopChanged':False,'forceTerminationUsed':False}
(D/'prestart-refusal-and-restore-r300.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
