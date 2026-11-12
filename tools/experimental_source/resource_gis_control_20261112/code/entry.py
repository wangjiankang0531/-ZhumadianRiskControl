"""Independent resource manager: qualify all new code and original GIS dependency."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

CODE_FILES={'entry.py','resource_grants.py','resource_settings.py','resource_reports.py','resource_service.py','resource_http.py','verify_offline_gis.py','qualified_settings.py','resource_agent.py','registered_gis.py'}
SHA = re.compile(r'[0-9a-f]{64}')

def require(value, code):
    if not value: raise ValueError(code)

def plain(path, *, directory=None):
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'NORMALIZED_ABSOLUTE_PATH_REQUIRED')
    for part in (*reversed(path.parents),path):
        if part.exists() or part.is_symlink():
            stat=part.lstat()
            require(not part.is_symlink() and not (getattr(stat,'st_file_attributes',0)&0x400),'REPARSE_PATH_REFUSED')
    if directory is not None: require(path.is_dir() if directory else path.is_file(),'ORDINARY_PATH_KIND_REQUIRED')
    return path

def digest(path):
    h=hashlib.sha256()
    with plain(path,directory=False).open('rb') as f:
        while chunk:=f.read(1048576):h.update(chunk)
    return h.hexdigest()

def document(path, limit):
    def unique(rows):
        result={}
        for key,value in rows:
            require(key not in result,'DUPLICATE_JSON_FIELD');result[key]=value
        return result
    with plain(path,directory=False).open('rb') as f:raw=f.read(limit+1)
    require(len(raw)<=limit,'BOUNDED_JSON_REQUIRED')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique)

def relative(root,name):
    require(isinstance(name,str) and 0<len(name)<500 and '\\' not in name and ':' not in name and
        all(s and s not in ('.','..') and not s.endswith((' ','.')) for s in name.split('/')),'NORMALIZED_RELATIVE_PATH_REQUIRED')
    return plain(root.joinpath(*name.split('/')))

def verify_rows(root,rows):
    require(isinstance(rows,dict) and 1<=len(rows)<=12000,'BOUNDED_PROGRAM_MANIFEST_REQUIRED')
    for name,pin in rows.items():
        require(isinstance(pin,dict) and set(pin)=={'bytes','sha256'} and type(pin['bytes']) is int and
            0<=pin['bytes']<=512*1048576 and isinstance(pin['sha256'],str) and SHA.fullmatch(pin['sha256']),'FILE_PIN_REQUIRED')
        file=relative(root,name)
        require(file.is_file() and file.stat().st_size==pin['bytes'] and digest(file)==pin['sha256'],'PROGRAM_CHANGED:'+name)

def qualify(folder):
    folder=plain(folder,directory=True)
    manifest=document(folder/'client-resources-install.json',1048576)
    require(isinstance(manifest,dict) and set(manifest)=={'schema','version','files'} and
        manifest['schema']=='xnby.client-resources.install.v1' and manifest['version']=='client-resources.20261112.2','EXACT_BOOTSTRAP_INSTALL_REQUIRED')
    require(set(manifest['files'])=={'code/'+name for name in CODE_FILES}|{'registration.json'},'EXACT_BOOTSTRAP_FILES_REQUIRED')
    verify_rows(folder,manifest['files'])
    actual={f.relative_to(folder).as_posix() for f in (folder/'code').rglob('*') if f.is_file()}
    require(actual=={'code/'+name for name in CODE_FILES},'UNDECLARED_BOOTSTRAP_CODE')
    for f in (folder/'code').rglob('*'):plain(f)
    reg=document(folder/'registration.json',32768)
    require(isinstance(reg,dict) and set(reg)=={'schema','baseRoot','installationRelative','configurationRelative','GISInstallSHA256'} and
        reg['schema']=='xnby.client-resources.registration.v1','EXACT_BOOTSTRAP_REGISTRATION_REQUIRED')
    require(isinstance(reg['GISInstallSHA256'],str) and SHA.fullmatch(reg['GISInstallSHA256']),'PINNED_GIS_INSTALL_REQUIRED')
    require(isinstance(reg['baseRoot'],str) and re.match(r'^[A-Za-z]:[\\/]',reg['baseRoot']) and not reg['baseRoot'].startswith(('\\','//')), 'LOCAL_DRIVE_PROJECT_REQUIRED')
    base=plain(reg['baseRoot'],directory=True)
    require(base.name.casefold()=='zhumadian','FIXED_PROJECT_ROOT_REQUIRED')
    install=relative(base,reg['installationRelative']); config=relative(base,reg['configurationRelative'])
    require(reg['installationRelative'] in ('Application/Packages/ClientGISSettingsCandidate_20261107','Application/ClientGIS') and
        reg['configurationRelative'] in ('Application/private/client-workspace.json','Config/client-workspace.json'),'REGISTERED_CLIENT_LAYOUT_REQUIRED')
    require(digest(install/'client-gis-install.json')==reg['GISInstallSHA256'],'REGISTERED_GIS_MANIFEST_CHANGED')
    dep=document(install/'client-gis-install.json',4*1048576)
    require(isinstance(dep,dict) and dep.get('schema')=='xnby.client-gis.install.v1','QUALIFIED_GIS_PROGRAM_REQUIRED')
    verify_rows(install,dep['files'])
    require(sys.dont_write_bytecode and sys.flags.isolated==1 and tuple(sys.version_info[:2])==(3,12) and
        any(os.path.samefile(sys.executable,install/name) for name in ('runtime/python/python.exe','runtime/python/pythonw.exe')),
        'USE_REGISTERED_ISOLATED_PYTHON')
    return {'folder':folder,'manifestSHA256':digest(folder/'client-resources-install.json'),'installation':install,'configuration':plain(config),'registration':reg,'programFiles':len(dep['files'])}


def main():
    require(len(sys.argv)==2 and sys.argv[1] in ('check','start','serve','status','stop','recover'),'EXPLICIT_RESOURCE_AGENT_COMMAND_REQUIRED')
    trusted=qualify(Path(__file__).absolute().parent.parent)
    sys.path[:0]=[str(trusted['folder']/'code'),str(trusted['installation']/'code'),str(trusted['installation']/'provider/tools')]
    from client_manifest import load_installation
    trusted['dependency']=load_installation(trusted['installation'])
    from resource_agent import command
    return command(trusted,sys.argv[1])

if __name__=='__main__':
    try:
        result=main();code=2 if result.get('observationExpired') else 0
    except Exception as error:
        result={'passed':False,'code':str(error),'forceTerminationUsed':False};code=1
    if sys.stdout is not None:
        if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(result,ensure_ascii=True),flush=True)
    raise SystemExit(code)
