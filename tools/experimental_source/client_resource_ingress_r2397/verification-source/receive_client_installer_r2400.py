"""Independently receive D174; do not display UI or perform installation."""
from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
O=V/'client-installer-receipt-r2400'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    source=A/'tools/experimental_source/client_installer_gui_20261112'
    archive=R/'Document/Deployment/client_installer_gui_20261112/source.zip'
    assert sha(archive)=='ec16b0e95743970e49ef869201bf0420ad3a79287439725cbf9131badb61b6be'
    with zipfile.ZipFile(archive)as z:
        names=z.namelist();assert len(names)==17 and len(set(names))==17
        assert {p.relative_to(A).as_posix()for p in source.rglob('*')if p.is_file()}==set(names)
        for name in names:
            data=z.read(name);assert data==(A/name).read_bytes()
            p=subprocess.Popen(['git','-C',str(A),'show','762693df14d726cf6dc0881ea7ff8eb453064a4c:'+name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            out,err=p.communicate();assert p.returncode==0 and out==data
            if name.endswith('.py'):ast.parse(data)
            if name.endswith('.json'):json.loads(data)
    transport=R/'Document/Deployment/client_installer_gui_20261112/thin-delivery-map.json'
    assert sha(transport)=='346daae7d13284874fe7f57e91ffba67437f01adcad132bf7981cb5495b7a964'
    mappings=json.loads(transport.read_bytes());summaries=[]
    for machine in ['client-250','client-252']:
        folder=A/'Packages/ClientInstallerCandidate_20261112'/machine;rows=mappings[machine]['files']
        assert len(rows)==10 and {p.relative_to(folder).as_posix()for p in folder.rglob('*')if p.is_file()}==set(rows)
        for name,row in rows.items():assert (folder/name).stat().st_size==row['bytes']and sha(folder/name)==row['sha256']
        manifest=json.loads((folder/'client-installer-install.json').read_bytes());assert len(manifest['files'])==8
        for name,row in manifest['files'].items():assert rows[name]==row
        payload=folder/'payload/ClientLogin';old=A/'Packages/ClientLoginBootstrapCandidate_20261112'/machine
        assert {p.relative_to(payload).as_posix()for p in payload.rglob('*')if p.is_file()}=={'client-login-install.json','registration.json','code/entry.py','code/bootstrap_core.py'}
        for p in payload.rglob('*'):
            if p.is_file():assert p.read_bytes()==(old/p.relative_to(payload)).read_bytes()
        shortcut=folder/'驻马店客户机安装.lnk'
        ps="$ErrorActionPreference='Stop';$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('"+str(shortcut).replace("'","''")+"');[pscustomobject]@{target=$s.TargetPath;arguments=$s.Arguments;directory=$s.WorkingDirectory}|ConvertTo-Json -Compress"
        p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        out,err=p.communicate();assert p.returncode==0
        meta=json.loads(out.decode('utf-8-sig'));expected_root='D:/Project/Zhumadian'if machine=='client-250'else'F:/XNBY/Zhumadian'
        install='Application/Packages/ClientGISSettingsCandidate_20261107'if machine=='client-250'else'Application/ClientGIS'
        assert meta['target'].replace('\\','/').casefold()==(expected_root+'/'+install+'/runtime/python/pythonw.exe').casefold()
        assert meta['arguments'].replace('\\','/')=='-I -B "'+expected_root+'/Application/ClientInstaller/code/entry.py"'
        assert 'cmd.exe'not in meta['target'].casefold()and 'powershell'not in meta['target'].casefold()
        summaries.append({'machine':machine,'files':10,'bytes':sum(r['bytes']for r in rows.values()),'allFileSHA256Matched':True,'innerD171PayloadUnchanged':True,'shortcutMetadataExactNoShell':True})
    result={'passed':True,'source17GitZipWorkingByteMatched':True,'twoThinTransportMapsAnd20FileSHA256Matched':True,
        'machines':summaries,'shortcutOnlyReadNotRun':True,'noUIRegistryInstallOr252Execution':True,
        'peer23CasesAndNativeUIPreviewNotRerun':True}
    (O/'verification.json').write_text(json.dumps(result,indent=2)+'\n','utf-8');print(json.dumps(result))


if __name__=='__main__':main()
