"""Retire only verified G-test code copies after exact restoration and Job zero."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

R=Path('D:/Project/Zhumadian');G=R/'_g/Application';W=R/'work/ua1049'
D=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'
V=Path(__file__).resolve().parent
R3=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'

def sha(p):
    with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def plain(p):
    p=p.absolute();assert p.is_relative_to(R)and p!=R
    for item in [p,*p.parents]:
        assert not item.is_symlink()
        if item.exists():assert not item.lstat().st_file_attributes&0x400
    return p

def main():
    assert read(W/'verified-real-apply-r1049.json')['passed']
    assert read(W/'actual-parent-terminal-r1053.json')['actualJobDescendantsZero']
    assert read(W/'actual-parent-terminal-r1049.json')['actualJobDescendantsZero']
    assert read(D/'independent-restoration-r1054.json')['successfulCIMOwnedGReferences']==0
    assert read(R3/'verified-transport-r1052.json')['passed']
    assert not(D/'cleanup-r1055.json').exists()
    plan=read(W/'prepared-plan.private.json')
    assert all(pin(G/name)==row['before']for name,row in plan['mutations'].items())
    assert all(pin(G/name)==row for name,row in plan['protectedPins'].items())
    query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/work/ut1052') } | Measure-Object).Count"
    proc=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    assert proc.returncode==0 and proc.stdout.decode('utf-8-sig').strip()=='0','SUCCESSFUL_ZERO_REFERENCE_PROOF_REQUIRED'
    candidates={};directories=[]
    def add(path,expected,retained):
        path=plain(path);assert pin(path)==expected
        assert str(path)not in candidates
        candidates[str(path)]={'bytes':expected['bytes'],'sha256':expected['sha256'],'retainedProof':retained}
    def tree(root,callback):
        root=plain(root);assert root.is_dir()
        for path in root.rglob('*'):
            plain(path)
            if path.is_file():callback(path)
        directories.append(root)
    # The outer before image is redundant with the independently restored G files.
    assert read(W/'base-before/journal.json')['phase']=='restored'
    def outer_before(path):
        name=path.relative_to(W/'base-before/before').as_posix();row=plan['mutations'][name]['before']
        assert row is not None and pin(G/name)==row
        add(path,row,str(G/name))
    tree(W/'base-before/before',outer_before)
    resolution=read(V/'r48-file-source-resolution-r1007.private.json')
    old_sources=resolution['bases']['r45']['programs']
    allowed_new={s['newReleaseSHA256']for s in plan['scenarios']}
    retired_attempts=[]
    for attempt in (G/'UserData/OriginalPublicUpdates').iterdir():
        if not attempt.is_dir()or not(attempt/'result.json').is_file():continue
        result=read(attempt/'result.json')
        if result.get('updateId')!='20261105-r48-event-results-from-r45'or result.get('newReleaseSHA256')not in allowed_new:continue
        assert re.fullmatch('[0-9a-f]{32}',attempt.name)
        assert (attempt/'rollback-result.json').exists()or(attempt/'recovery-result.json').exists()
        changes=read(attempt/'changes.json')
        def inner_before(path):
            name=path.relative_to(attempt/'before').as_posix();expected=changes[name]['before'];assert expected
            source=W/'old'/name if name in ['release-manifest.json','payload-manifest.json']else Path(old_sources[name]['source'])
            retained=pin(source);assert retained and retained['sha256']==expected
            add(path,retained,str(source))
        tree(attempt/'before',inner_before);retired_attempts.append(str(attempt))
    assert len(retired_attempts)==2
    # Code stages are exactly reconstructible from pinned sources. Keep their
    # metadata and the original failures instead of erasing the test history.
    for scenario in plan['scenarios']:
        bundle=Path(scenario['bundle']);manifest=read(bundle/'update-manifest.json')
        for name,row in manifest['files'].items():
            if name in ['release-manifest.json','payload-manifest.json']:continue
            path=bundle/'payload'/name
            if name=='tools/original_public_test_update.py':source=Path(scenario['runtimeSource'])
            elif name=='tools/original_public_test_base_r46.py':source=Path(scenario['runtimeSource']).with_name('original_public_test_base_r46.py')
            else:source=Path(resolution['newSources'][name]['source'])
            expected={'bytes':row['bytes'],'sha256':row['SHA256']};assert pin(source)==expected
            add(path,expected,str(source))
        directories.append(bundle/'payload')
    # The transport extractor stages have a complete retained, approved-later
    # candidate ZIP; compare the exact selected member for every file.
    archive=R3/'delivery/Zhumadian_Event_Write_Results_20261105_R48_R3.zip'
    with zipfile.ZipFile(archive)as zipped:
        for label in ['r45','r47']:
            root=R/'work/ut1052'/label
            def extracted(path):
                name=path.relative_to(root).as_posix()
                origin='variants/'+label+'/update-manifest.json'if name=='update-manifest.json'else name
                raw=zipped.read(origin);expected={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
                add(path,expected,str(archive)+'::'+origin)
            tree(root,extracted)
    logical=sum(row['bytes']for row in candidates.values());free_before=shutil.disk_usage(R).free
    scope={'schema':'xnby.owned-test-retirement-scope.v1','files':candidates,'logicalBytes':logical,
        'protectedDatabaseGISDLGSourceAndCurrentCandidateUntouched':True,'publicServerDeletion':False}
    (V/'cleanup-real-apply-scope-r1055.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,row in candidates.items():
        path=plain(Path(name));assert pin(path)=={'bytes':row['bytes'],'sha256':row['sha256']};path.unlink()
    for root in directories:
        for path in sorted([p for p in root.rglob('*')if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
            plain(path)
            if not any(path.iterdir()):path.rmdir()
        if not any(root.iterdir()):root.rmdir()
    ut=R/'work/ut1052'
    if ut.exists()and not any(ut.iterdir()):ut.rmdir()
    assert all(not Path(name).exists()for name in candidates)
    assert all(pin(G/name)==row['before']for name,row in plan['mutations'].items())
    assert all(pin(G/name)==row for name,row in plan['protectedPins'].items())
    report={'deletedFiles':len(candidates),'logicalBytes':logical,'observedFreeBytesDelta':shutil.disk_usage(R).free-free_before,
        'exclusivePhysicalAttribution':False,'bothActualJobsPreviouslyProvenZero':True,'successfulFreshCIMZero':True,
        'originalGCodeAndProtectedPinsKept':True,'metadataFailuresSourceLogsAndR3CandidateKept':True,
        'testBeforeCopiesRetiredSoOldTestRollbackEntryNotPromised':True,'serverVersionsDeleted':False}
    (D/'cleanup-r1055.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
