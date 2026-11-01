"""Materialize exact R23 programs with hardlinks and an owned R114 synthetic dataset."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,os,shutil,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_e/Application';T=R/'Application/tools'
C=R/'work/event_delivery_consistency_20261030/full-controller-r123'
D=R/'Document/Deployment/public_test_unified_r23_20261101'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
assert not A.parent.exists()and not C.exists()
assert shutil.disk_usage(R).free>3*1024**3
assert sha(D/'delivery-manifest.json')=='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
dep=read(R/'work/r23gv-r1/dependency-resolution.json');assert dep['allResolved']and not dep['realPrivateConfigurationRead']and not dep['realSeedOrBusinessDataRead']
A.mkdir(parents=True);C.mkdir();checks={};copied=linked=0
with zipfile.ZipFile(next((D/'delivery').glob('*.zip')))as z:
    assert z.testzip()is None
    payload=json.loads(z.read('payload/payload-manifest.json'));release=json.loads(z.read('payload/release-manifest.json'))
    for rel,row in payload['files'].items():
        if rel.startswith(('seed/mysql/','private/')):continue
        p=PurePosixPath(rel);assert not p.is_absolute()and '..'not in p.parts and '\\'not in rel and ':'not in rel
        dest=A/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if 'payload/'+rel in z.namelist():dest.write_bytes(z.read('payload/'+rel));copied+=dest.stat().st_size
        else:
            source=Path(dep['programs'][rel]['source']);assert sha(source)==row['sha256']and source.stat().st_size==row['bytes']
            assert not source.lstat().st_file_attributes&0x400;os.link(source,dest);linked+=1
        assert sha(dest)==row['sha256']and dest.stat().st_size==row['bytes']
    for rel,digest in release['controllerFiles'].items():
        dest=A/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if 'payload/'+rel in z.namelist():dest.write_bytes(z.read('payload/'+rel))
        elif not dest.exists():
            source=Path(dep['controllers'][rel]['source']);assert sha(source)==digest;dest.write_bytes(source.read_bytes())
        assert sha(dest)==digest
    for name in ['payload-manifest.json','release-manifest.json']:(A/name).write_bytes(z.read('payload/'+name))
overlay=Path('D:/Zqa20261025/Application/payload/callback-overlay/20261026-password-identity')
assert sha(overlay/'manifest.json')=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb'
om=read(overlay/'manifest.json');target=A/'payload/callback-overlay/20261026-password-identity';target.mkdir(parents=True)
(target/'manifest.json').write_bytes((overlay/'manifest.json').read_bytes())
for rel,row in om['files'].items():
    source=overlay/rel;assert sha(source)==row['SHA256'];dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
(A.parent/'own-fixture.json').write_text(json.dumps({'ownedSyntheticFixtureOnly':True,'purpose':'actual-approval-ui-retry-on-isolated-synthetic-dataset','noInstalledPrivateConfigOrSeedRead':True}),encoding='utf-8')
(C/'code-prepared.json').write_text(json.dumps({'exactR23ProgramAnd20ControlFilesVerified':True,'hardlinkedProgramFiles':linked,'newProgramBytesWritten':copied,'onlySyntheticDatabaseWillBeCopied':True}),encoding='utf-8')

print("OWN_APPROVAL_PROGRAMS_READY_NO_USER_PREVIEW_DATA_READ")
