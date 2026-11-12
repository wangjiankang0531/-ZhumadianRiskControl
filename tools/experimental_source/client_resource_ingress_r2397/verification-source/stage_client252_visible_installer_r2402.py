"""Stage ten fixed normal GUI installer files on the user-confirmed 252 share.

No shortcut execution, remote process creation, registry write, or GIS change.
Canonical target must be new; a complete identical existing target is read-only.
"""
from pathlib import Path
import datetime,hashlib,json,os

R=Path('D:/Project/Zhumadian');V=Path(__file__).parent
BASE=Path(r'\\192.168.250.252\Fofme\XNBY\Zhumadian')
TARGET=BASE/'Application/ClientInstaller'
SOURCE=R/'Application/Packages/ClientInstallerCandidate_20261112/client-252'
D=R/'Document/Deployment/client252_visible_installer_r2402_20261112'


def need(value,code):
    if not value:raise ValueError(code)
def plain(path):
    p=Path(path).absolute();need(p.is_absolute()and '..'not in p.parts,'EXACT_ABSOLUTE_PATH_REQUIRED')
    for item in [p,*p.parents]:
        if item.exists():need(not item.is_symlink()and not(getattr(item.lstat(),'st_file_attributes',0)&1024),'REPARSE_REFUSED')
    return p
def sha(path):
    with plain(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
    with(D/name).open('x',encoding='utf-8')as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    need(os.name=='nt'and not D.exists(),'FRESH_WINDOWS_STAGE_RECEIPT_REQUIRED')
    receiver=json.loads((V/'client-installer-receipt-r2400/verification.json').read_bytes());need(receiver['passed'],'INDEPENDENT_FIXED_SOURCE_RECEIPT_REQUIRED')
    mapping=R/'Document/Deployment/client_installer_gui_20261112/thin-delivery-map.json'
    need(sha(mapping)=='346daae7d13284874fe7f57e91ffba67437f01adcad132bf7981cb5495b7a964','EXACT_D174_TRANSPORT_MAP_REQUIRED')
    value=json.loads(mapping.read_bytes())['client-252'];rows=value['files']
    need(value['canonicalTarget']=='F:/XNBY/Zhumadian/Application/ClientInstaller'and len(rows)==10 and sum(r['bytes']for r in rows.values())==37966,'EXACT_252_TEN_FILE_SCOPE_REQUIRED')
    need(plain(BASE).is_dir()and plain(BASE/'Application/ClientGIS').is_dir(),'EXISTING_STABLE_252_INSTALLATION_REQUIRED')
    need(sha(BASE/'Application/ClientGIS/client-gis-install.json')=='26342711ce4091661d71893ce43a1e0431417117ba9f9d522d3ce8ea738cac72','PREVIOUS_QUALIFIED_252_PROGRAMME_REQUIRED')
    for name,row in rows.items():need((SOURCE/name).stat().st_size==row['bytes']and sha(SOURCE/name)==row['sha256'],'FIXED_SOURCE_FILE_CHANGED')
    protected=[BASE/'Config/client-workspace.json',BASE/'Application/ClientGIS/client-gis-install.json',BASE/'Assets/3DGIS/驻马店园区/metadata.xml']
    before=[sha(p)for p in protected]
    D.mkdir()
    scope={'schema':'xnby.client252.visible-installer-stage.v1','source':SOURCE.as_posix(),'targetShare':str(TARGET),
       'canonicalMachineTarget':value['canonicalTarget'],'files':rows,'fileCount':10,'bytes':37966,
       'registryProcessExecutionOrGISMutationIncluded':False,'priorExplicitUserShare':r'\\192.168.250.252\Fofme\XNBY'}
    save('fixed-scope.json',scope)
    existed=plain(TARGET).exists();copied=[]
    if not existed:
        need(TARGET.parent==plain(BASE/'Application'),'CANONICAL_APPLICATION_TARGET_REQUIRED')
        TARGET.mkdir()
        # Entry shortcut is last. No runnable normal entry appears before all code.
        names=[n for n in rows if n not in ('client-installer-install.json','驻马店客户机安装.lnk')]+['client-installer-install.json','驻马店客户机安装.lnk']
        for name in names:
            target=plain(TARGET/name);need(target.is_relative_to(TARGET),'TARGET_SCOPE_ESCAPE_REFUSED')
            target.parent.mkdir(parents=True,exist_ok=True)
            with plain(SOURCE/name).open('rb')as src,target.open('xb')as dst:
                while True:
                    block=src.read(1024*1024)
                    if not block:break
                    dst.write(block)
            need(target.stat().st_size==rows[name]['bytes']and sha(target)==rows[name]['sha256'],'TARGET_FILE_COPY_NOT_ACCEPTED_NO_RETRY')
            copied.append(name)
    actual={p.relative_to(TARGET).as_posix()for p in TARGET.rglob('*')if p.is_file()}
    need(actual==set(rows),'UNKNOWN_EXISTING_INSTALLER_CONTENT_NO_OVERWRITE')
    for name,row in rows.items():need((plain(TARGET/name)).stat().st_size==row['bytes']and sha(TARGET/name)==row['sha256'],'REMOTE_TEN_FILE_READBACK_FAILED')
    need(before==[sha(p)for p in protected],'EXISTING_252_GIS_PROGRAM_CONFIG_OR_METADATA_CHANGED')
    result={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'copiedFiles':len(copied),
        'copiedBytes':sum(rows[n]['bytes']for n in copied),'completeTenFileSHA256ReadbackMatched':True,
        'existingIdenticalVersionReadOnlyReused':existed,'existing252GISConfigProgrammeMetadataByteUnchanged':True,
        'shortcutExecutedOrUIOpened':False,'remoteProcessOrRegistryNotOperated':True,
        'actual252LocalProgrammeQualificationInstallAndGISStartupStillPending':True,
        'mustOpenShortcutOn252Not250UNC':True,'publicR51StillNotUploadedOrDeployed':True}
    save('verification.json',result);print(json.dumps(result))


if __name__=='__main__':main()
