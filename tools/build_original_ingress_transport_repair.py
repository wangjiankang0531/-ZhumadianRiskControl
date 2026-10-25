"""Build a pinned controller-only successor for the installed, uninitialized predecessor."""
from pathlib import Path
import argparse, hashlib, json, uuid

def sha(raw): return hashlib.sha256(raw).hexdigest()

def build(base_update, base_pin, source_tools, output, repair_label='R3'):
    revisions={'R3':'20261025-r3-transport','R4':'20261025-r4-303-preflight'}
    if repair_label not in revisions: raise ValueError('KNOWN_REPAIR_LABEL_REQUIRED')
    base_update=Path(base_update).resolve(strict=True);source_tools=Path(source_tools).resolve(strict=True)
    output=Path(output).absolute()
    if output.exists(): raise ValueError('FRESH_REPAIR_DIRECTORY_REQUIRED')
    raw=(base_update/'update-manifest.json').read_bytes()
    if sha(raw)!=base_pin: raise ValueError('PINNED_PREDECESSOR_UPDATE_REQUIRED')
    base_spec=json.loads(raw)
    files=['tools/original_project_branding.py','tools/install_original_server_ingress.py',
           'Start_Original_Server.cmd','Deploy_Original_Server.cmd','Rollback_Original_Server.cmd','release-manifest.json']
    if set(base_spec['files'])!=set(files): raise ValueError('EXACT_PREDECESSOR_FILE_SET_REQUIRED')
    before={rel:(base_update/'payload'/rel).read_bytes() for rel in files}
    for rel,body in before.items():
        row=base_spec['files'][rel]
        if sha(body)!=row['after'] or len(body)!=row['bytes']: raise ValueError('PREDECESSOR_PAYLOAD_CHANGED')
    base=json.loads(before['release-manifest.json'])
    if sha(before['release-manifest.json'])!=base_spec['updatedReleaseManifestSHA256']:raise ValueError('PREDECESSOR_RELEASE_MANIFEST_CHANGED')
    revised=dict(base,controllerFiles=dict(base['controllerFiles']),controllerRevision=revisions[repair_label],isolatedStartupAndRestartVerified=False)
    after={files[0]:before[files[0]],files[1]:(source_tools/'install_original_server_ingress.py').read_bytes()}
    revised['controllerFiles'][files[1]]=sha(after[files[1]])
    after['release-manifest.json']=json.dumps(revised,indent=2).encode('utf-8')
    updated_pin=sha(after['release-manifest.json'])
    for name,tool,extra in [('Start_Original_Server.cmd','serve_original_server_release.py',''),('Deploy_Original_Server.cmd','install_original_server_ingress.py',''),('Rollback_Original_Server.cmd','install_original_server_ingress.py',' --rollback')]:
        after[name]=('@echo off\r\n"%~dp0runtime\\python\\python.exe" -I -B "%~dp0tools\\'+tool+'" --application "%~dp0." --release-manifest-sha256 '+updated_pin+extra+'\r\nif errorlevel 1 pause\r\n').encode('ascii')
    spec={'schema':'zhumadian.original.offline-update.v1','updateId':str(uuid.uuid4()),'releaseId':base['releaseId'],
          'baseReleaseManifestSHA256':sha(before['release-manifest.json']),'updatedReleaseManifestSHA256':updated_pin,
          'previousReservation':{'schema':'zhumadian.original.offline-update.reservation.v1','updateId':base_spec['updateId'],'patchSHA256':base_pin},
          'files':{rel:{'before':sha(before[rel]),'after':sha(after[rel]),'bytes':len(after[rel])} for rel in files}}
    patch=json.dumps(spec,indent=2).encode();patch_pin=sha(patch)
    updater=(source_tools/'apply_original_server_offline_update.py').read_bytes();updater_pin=sha(updater)
    entry=r'''"""Apply only the exact pinned successor, then invoke the existing guarded installer."""
from pathlib import Path
import hashlib,subprocess,sys
APP=Path('C:/Zdm/Application')
PATCH_SHA='__PATCH_SHA__'
UPDATER_SHA='__UPDATER_SHA__'
BASE_SHA='__BASE_SHA__'
UPDATED_SHA='__UPDATED_SHA__'
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    folder=Path(__file__).resolve().parent
    for root in (APP,folder):
        for part in (root,*root.parents):
            if part.is_symlink() or part.exists() and getattr(part.lstat(),'st_file_attributes',0)&0x400:
                raise ValueError('REGULAR_REPAIR_PATH_REQUIRED')
    if digest(APP/'release-manifest.json') not in (BASE_SHA,UPDATED_SHA):raise ValueError('EXACT_INSTALLED_PREDECESSOR_OR_SUCCESSOR_REQUIRED')
    updater=folder/'apply_original_server_offline_update.py';manifest=folder/'update-manifest.json'
    if digest(updater)!=UPDATER_SHA or digest(manifest)!=PATCH_SHA:raise ValueError('REPAIR_TOOL_OR_MANIFEST_CHANGED')
    print('REPAIR 1/2: verifying and applying the pinned offline controller update',flush=True)
    subprocess.run([sys.executable,'-I','-B',str(updater),'--application',str(APP),'--patch-manifest',str(manifest),'--patch-sha256',PATCH_SHA],check=True)
    if digest(APP/'release-manifest.json')!=UPDATED_SHA:raise ValueError('REPAIR_READBACK_FAILED')
    print('REPAIR 2/2: starting deployment preflight; watch the phase messages',flush=True)
    subprocess.run([sys.executable,'-I','-B',str(APP/'tools/install_original_server_ingress.py'),'--application',str(APP),'--release-manifest-sha256',UPDATED_SHA],check=True)
    print('__REPAIR_LABEL__ deployment completed; external PC/H5 and business acceptance remain required',flush=True)
if __name__=='__main__':main()
'''
    for token,value in [('__PATCH_SHA__',patch_pin),('__UPDATER_SHA__',updater_pin),('__BASE_SHA__',spec['baseReleaseManifestSHA256']),('__UPDATED_SHA__',updated_pin),('__REPAIR_LABEL__',repair_label)]:entry=entry.replace(token,value)
    output.mkdir(parents=True)
    for rel,body in after.items():p=output/'payload'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    (output/'apply_original_server_offline_update.py').write_bytes(updater)
    (output/'update-manifest.json').write_bytes(patch)
    (output/('Deploy_Original_20261025_'+repair_label+'.py')).write_text(entry,encoding='ascii',newline='\n')
    (output/('Deploy_Original_20261025_'+repair_label+'.cmd')).write_bytes(('@echo off\r\n"C:\\Zdm\\Application\\runtime\\python\\python.exe" -I -B "%~dp0Deploy_Original_20261025_'+repair_label+'.py"\r\nif errorlevel 1 pause\r\n').encode('ascii'))
    guard=(base_update/'web.config').read_bytes()
    if sha(guard)!='6c56d8b841a526e5ace90fd504758026794ca0464e7b1568d48eeaac9ef357e7':raise ValueError('DENY_HTTP_GUARD_CHANGED')
    (output/'web.config').write_bytes(guard)
    result={'updateId':spec['updateId'],'baseReleaseManifestSHA256':spec['baseReleaseManifestSHA256'],
            'updatedReleaseManifestSHA256':updated_pin,'patchManifestSHA256':patch_pin,
            'files':{p.relative_to(output).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in output.rglob('*') if p.is_file()},
            'originalBackendStarted':False,'publicDeployed':False}
    result['totalBytes']=sum(row['bytes'] for row in result['files'].values())
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['base-update','source-tools','output']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--base-update-manifest-sha256',required=True);parser.add_argument('--repair-label',choices=['R3','R4'],default='R3');args=parser.parse_args()
    result=build(args.base_update,args.base_update_manifest_sha256,args.source_tools,args.output,args.repair_label)
    args.output.with_name(args.output.name+'.build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
