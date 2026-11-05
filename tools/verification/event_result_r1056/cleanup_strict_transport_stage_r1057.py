from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
R=Path('D:/Project/Zhumadian');ROOT=R/'work/ut1057'
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'

def main():
    report=json.loads((D/'verified-transport-r1057.json').read_bytes())
    assert report['passed']and report['exactNineFilesBeforeAndAfterModuleInspection']
    assert ROOT.resolve()==Path('D:/Project/Zhumadian/work/ut1057').resolve()and ROOT!=R
    assert not(D/'transport-stage-cleanup-r1057.json').exists()
    query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/work/ut1057') } | Measure-Object).Count"
    process=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    assert process.returncode==0 and process.stdout.decode('utf-8-sig').strip()=='0'
    rows={}
    archive=D/'delivery/Zhumadian_Event_Write_Results_20261105_R48_R3.zip'
    with zipfile.ZipFile(archive)as zipped:
        for p in ROOT.rglob('*'):
            assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400
            if not p.is_file():continue
            relative=p.relative_to(ROOT);label=relative.parts[0];assert label in {'r45','r47'}
            name=Path(*relative.parts[1:]).as_posix()
            member='variants/'+label+'/update-manifest.json'if name=='update-manifest.json'else name
            raw=zipped.read(member);pin={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            assert p.stat().st_size==pin['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256']
            rows[p]=pin
    before=shutil.disk_usage(R).free
    for p,pin in rows.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'];p.unlink()
    for p in sorted([x for x in ROOT.rglob('*')if x.is_dir()],key=lambda p:len(p.parts),reverse=True):p.rmdir()
    ROOT.rmdir()
    proof={'deletedFiles':len(rows),'logicalBytes':sum(x['bytes']for x in rows.values()),
        'observedFreeBytesDelta':shutil.disk_usage(R).free-before,'exclusivePhysicalAttribution':False,
        'retainedR3ArchiveMatchedEveryRemovedFile':True,'successfulCIMReferencesZero':True,
        'publicOrBusinessDataTouched':False}
    (D/'transport-stage-cleanup-r1057.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))

if __name__=='__main__':main()
