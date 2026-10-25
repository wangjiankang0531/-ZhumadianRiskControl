"""Build a small pinned, first-install controller overlay for the sealed server ZIP."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,uuid,zipfile

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['base-archive','base-bootstrap','source-tools','update-tool','output']:p.add_argument('--'+name,type=Path,required=True)
    for name in ['base-archive-sha256','base-bootstrap-sha256','base-manifest-sha256']:p.add_argument('--'+name,required=True)
    a=p.parse_args();archive=a.base_archive.resolve(strict=True);bootstrap=a.base_bootstrap.resolve(strict=True);tools=a.source_tools.resolve(strict=True);out=a.output.resolve()
    if out.exists():raise ValueError('FRESH_SMALL_UPDATE_OUTPUT_REQUIRED')
    with archive.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=a.base_archive_sha256:raise ValueError('SEALED_BASE_ARCHIVE_CHANGED')
    boot=bootstrap.read_bytes()
    if sha(boot)!=a.base_bootstrap_sha256:raise ValueError('BASE_BOOTSTRAP_CHANGED')
    names=['tools/original_project_branding.py','tools/install_original_server_ingress.py','Start_Original_Server.cmd','Deploy_Original_Server.cmd','Rollback_Original_Server.cmd','release-manifest.json']
    with zipfile.ZipFile(archive) as z:old={rel:z.read('Application/'+rel) for rel in names}
    if sha(old['release-manifest.json'])!=a.base_manifest_sha256:raise ValueError('BASE_RELEASE_MANIFEST_CHANGED')
    base=json.loads(old['release-manifest.json']);new={rel:(tools/Path(rel).name).read_bytes() for rel in names[:2]}
    revision=dict(base,controllerFiles=dict(base['controllerFiles']),controllerRevision='20261025-r2',
                  baseIsolatedStartupAndRestartVerified=base['isolatedStartupAndRestartVerified'],isolatedStartupAndRestartVerified=False)
    for rel in names[:2]:
        if sha(old[rel])!=base['controllerFiles'][rel]:raise ValueError('SEALED_BASE_CONTROLLER_CHANGED')
        revision['controllerFiles'][rel]=sha(new[rel])
    new['release-manifest.json']=json.dumps(revision,indent=2).encode('utf-8');new_pin=sha(new['release-manifest.json'])
    for name,tool,extra in [('Start_Original_Server.cmd','serve_original_server_release.py',''),('Deploy_Original_Server.cmd','install_original_server_ingress.py',''),('Rollback_Original_Server.cmd','install_original_server_ingress.py',' --rollback')]:
        new[name]=('@echo off\r\n"%~dp0runtime\\python\\python.exe" -I -B "%~dp0tools\\'+tool+'" --application "%~dp0." --release-manifest-sha256 '+new_pin+extra+'\r\nif errorlevel 1 pause\r\n').encode('ascii')
    spec={'schema':'zhumadian.original.offline-update.v1','updateId':str(uuid.uuid4()),'releaseId':base['releaseId'],
          'baseReleaseManifestSHA256':a.base_manifest_sha256,'updatedReleaseManifestSHA256':new_pin,
          'baseArchiveSHA256':a.base_archive_sha256,'files':{rel:{'before':sha(old[rel]),'after':sha(new[rel]),'bytes':len(new[rel])} for rel in names}}
    out.mkdir(parents=True)
    for rel,raw in new.items():dest=out/'payload'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    manifest_raw=json.dumps(spec,indent=2).encode('utf-8');patch_pin=sha(manifest_raw)
    (out/'update-manifest.json').write_bytes(manifest_raw)
    update=a.update_tool.resolve(strict=True).read_bytes();(out/'apply_original_server_offline_update.py').write_bytes(update);update_pin=sha(update)
    original=boot.decode('ascii');marker="& (Join-Path $application 'runtime\\python\\python.exe')"
    if original.count(marker)!=1:raise ValueError('EXACT_BASE_BOOTSTRAP_COMMAND_REQUIRED')
    prefix=original.split(marker)[0]
    needle="$manifestSha = '"+a.base_manifest_sha256+"'"
    if prefix.count(needle)!=1:raise ValueError('EXACT_BASE_MANIFEST_DECLARATION_REQUIRED')
    prefix=prefix.replace(needle,needle+"\r\n$updatedManifestSha = '"+new_pin+"'")
    needle='$archive = Join-Path $PSScriptRoot $archiveName'
    if prefix.count(needle)!=1:raise ValueError('EXACT_BASE_ARCHIVE_LOCATION_REQUIRED')
    prefix=prefix.replace(needle,"$archive = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'ZhumadianOriginal_Private_20261025') $archiveName")
    needle="if ((Get-FileHash -LiteralPath (Join-Path $application 'release-manifest.json') -Algorithm SHA256).Hash -ine $manifestSha) { throw 'Existing application belongs to a different release.' }"
    if prefix.count(needle)!=1:raise ValueError('EXACT_EXISTING_MANIFEST_GUARD_REQUIRED')
    prefix=prefix.replace(needle,"$installedPin = (Get-FileHash -LiteralPath (Join-Path $application 'release-manifest.json') -Algorithm SHA256).Hash\r\nif ($installedPin -ine $manifestSha -and $installedPin -ine $updatedManifestSha) { throw 'Existing application belongs to a different release.' }")
    tail=r'''$updater = Join-Path $PSScriptRoot 'apply_original_server_offline_update.py'
$patch = Join-Path $PSScriptRoot 'update-manifest.json'
if ((Get-FileHash -LiteralPath $updater -Algorithm SHA256).Hash -ine '__UPDATER_SHA__') { throw 'Offline update tool SHA mismatch.' }
if ((Get-FileHash -LiteralPath $patch -Algorithm SHA256).Hash -ine '__PATCH_SHA__') { throw 'Offline update manifest SHA mismatch.' }
& (Join-Path $application 'runtime\python\python.exe') -I -B $updater --application $application --patch-manifest $patch --patch-sha256 '__PATCH_SHA__'
if ($LASTEXITCODE -ne 0) { throw 'First-install controller update refused or failed. No IIS changes made. Do not repeat; report the error.' }
& (Join-Path $application 'runtime\python\python.exe') -I -B (Join-Path $application 'tools\install_original_server_ingress.py') --application $application --release-manifest-sha256 $updatedManifestSha
if ($LASTEXITCODE -ne 0) { throw 'Original R2 deployment failed. Inspect Application\UserData\OriginalDeployment. Existing IIS is retained or restored.' }
Write-Host 'Original-system R2 ready. External PC/H5, original account and business acceptance remain required.'
'''.replace('__UPDATER_SHA__',update_pin).replace('__PATCH_SHA__',patch_pin)
    (out/'Deploy_Original_20261025_R2.ps1').write_bytes((prefix+tail).replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
    (out/'Deploy_Original_20261025_R2.cmd').write_bytes(b'@echo off\r\n"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -NonInteractive -File "%~dp0Deploy_Original_20261025_R2.ps1"\r\nif errorlevel 1 pause\r\n')
    guard=archive.parent/'web.config';shutil.copyfile(guard,out/'web.config')
    files={f.relative_to(out).as_posix():{'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())} for f in out.rglob('*') if f.is_file()}
    result={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'updateId':spec['updateId'],'releaseId':spec['releaseId'],
            'baseArchiveSHA256':a.base_archive_sha256,'baseArchiveChanged':False,'files':files,
            'totalBytes':sum(v['bytes'] for v in files.values()),'patchManifestSHA256':patch_pin,
            'updatedReleaseManifestSHA256':new_pin,'actualOriginalBackendStarted':False,'publicDeployed':False}
    (out.parent/(out.name+'.build.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
