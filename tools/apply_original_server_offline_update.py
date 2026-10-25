"""Apply a pinned controller delta before the original server is initialized.

No service start/stop, database opening, IIS edit, credential read, or OS change.
An initialized installation is refused; an identical applied update is a no-op.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,uuid

CONTROLLERS=('tools/original_project_branding.py','tools/install_original_server_ingress.py')
FILES=(*CONTROLLERS,'Start_Original_Server.cmd','Deploy_Original_Server.cmd','Rollback_Original_Server.cmd','release-manifest.json')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path):
    p=Path(path)
    for q in [p,*p.parents]:
        if q.is_symlink() or q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400:raise ValueError('UPDATE_PATH_REDIRECTION_REJECTED')
    return p
def bounded(path):
    p=regular(path)
    if not p.is_file() or p.stat().st_size>2*1024**2:raise ValueError('BOUNDED_REGULAR_UPDATE_FILE_REQUIRED')
    return p.read_bytes()
def atomic(path,raw):
    p=regular(path);tmp=p.with_name(p.name+'.'+str(uuid.uuid4())+'.pending')
    try:
        with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if tmp.exists():tmp.unlink()
def apply_update(application,patch_manifest,patch_sha):
    app=regular(Path(application).absolute());manifest_path=regular(Path(patch_manifest).absolute())
    if app.resolve(strict=True)!=app or app.name!='Application':raise ValueError('EXPLICIT_REGULAR_APPLICATION_REQUIRED')
    raw=bounded(manifest_path)
    if sha(raw)!=patch_sha:raise ValueError('OFFLINE_UPDATE_MANIFEST_CHANGED')
    spec=json.loads(raw)
    if spec['schema']!='zhumadian.original.offline-update.v1' or set(spec['files'])!=set(FILES):raise ValueError('EXACT_CONTROLLER_DELTA_REQUIRED')
    if str(uuid.UUID(spec['updateId']))!=spec['updateId']:raise ValueError('UPDATE_UUID_REQUIRED')
    base_path=app/'release-manifest.json';current=bounded(base_path)
    new={}
    for rel in FILES:
        row=spec['files'][rel];body=bounded(manifest_path.parent/'payload'/rel)
        if len(body)!=row['bytes'] or sha(body)!=row['after']:raise ValueError('OFFLINE_UPDATE_PAYLOAD_CHANGED')
        new[rel]=body
    revision=json.loads(new['release-manifest.json'])
    if sha(new['release-manifest.json'])!=spec['updatedReleaseManifestSHA256'] or revision['releaseId']!=spec['releaseId']:
        raise ValueError('UPDATE_RELEASE_IDENTITY_CHANGED')
    if sha(current)==spec['updatedReleaseManifestSHA256']:
        if any(sha(bounded(app/rel))!=spec['files'][rel]['after'] for rel in FILES):raise ValueError('APPLIED_UPDATE_CONTROLLER_DRIFT')
        return {'alreadyApplied':True,'updateId':spec['updateId'],'runtimeStarted':False,'iisChanged':False,'dataChanged':False}
    if sha(current)!=spec['baseReleaseManifestSHA256']:raise ValueError('EXACT_BASE_RELEASE_REQUIRED')
    base=json.loads(current)
    if (base['schema']!=revision['schema'] or base['releaseId']!=spec['releaseId'] or
        base['payloadManifestSHA256']!=revision['payloadManifestSHA256'] or
        set(base['controllerFiles'])!=set(revision['controllerFiles'])):raise ValueError('BASE_PAYLOAD_IDENTITY_CHANGED')
    for rel,pin in base['controllerFiles'].items():
        if sha(bounded(app/rel))!=pin:raise ValueError('BASE_CONTROLLER_DRIFT')
        if rel not in CONTROLLERS and revision['controllerFiles'][rel]!=pin:raise ValueError('UNEXPECTED_CONTROLLER_DELTA')
    if any(revision['controllerFiles'][rel]!=spec['files'][rel]['after'] for rel in CONTROLLERS):raise ValueError('NEW_CONTROLLER_PINS_REQUIRED')
    old={rel:bounded(app/rel) for rel in FILES}
    if any(sha(old[rel])!=spec['files'][rel]['before'] for rel in FILES):raise ValueError('BASE_UPDATE_FILE_DRIFT')
    # Reserve the same byte lock used by the server controller. A concurrent
    # first start cannot proceed past its ownership lock while files change.
    data=regular(app/'UserData/OriginalServer')
    data.mkdir(parents=True,exist_ok=True)
    allowed={'server-owner.lock','offline-update.private.json'}
    if any(p.name not in allowed for p in data.iterdir()):raise ValueError('INITIALIZED_SERVER_UPDATE_REFUSED')
    guard=data/'offline-update.private.json'
    reservation={'schema':'zhumadian.original.offline-update.reservation.v1','updateId':spec['updateId'],'patchSHA256':patch_sha}
    import msvcrt
    lock=regular(data/'server-owner.lock').open('a+b')
    try:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        if any(p.name not in allowed for p in data.iterdir()):raise ValueError('INITIALIZED_SERVER_UPDATE_REFUSED')
        # A pinned successor may replace only the exact known completed base
        # reservation. This check runs under the same controller ownership lock.
        if guard.exists():
            observed=json.loads(bounded(guard))
            if observed!=reservation:
                prior=spec.get('previousReservation')
                approved=(isinstance(prior,dict) and set(prior)==set(reservation) and prior==observed and
                          prior.get('schema')==reservation['schema'] and prior.get('updateId')!=spec['updateId'] and
                          isinstance(prior.get('updateId'),str) and re.fullmatch('[0-9a-f-]{36}',prior['updateId']) and
                          str(uuid.UUID(prior['updateId']))==prior['updateId'] and
                          isinstance(prior.get('patchSHA256'),str) and re.fullmatch('[0-9a-f]{64}',prior['patchSHA256']))
                if not approved:raise ValueError('OTHER_OFFLINE_UPDATE_RESERVATION')
        atomic(guard,json.dumps(reservation,indent=2).encode('ascii'))
        backup=regular(app/'UserData/OriginalOfflineUpdate'/str(uuid.uuid4()));backup.mkdir(parents=True)
        for rel,body in old.items():p=backup/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
        report={'schema':'zhumadian.original.offline-update.result.v1','updateId':spec['updateId'],
                'applied':False,'rolledBack':False,'runtimeStarted':False,'iisChanged':False,'databaseOpened':False,
                'recordedAt':datetime.datetime.now().astimezone().isoformat(),'files':list(FILES)}
        try:
            for rel in FILES:
                if sha(bounded(app/rel))!=spec['files'][rel]['before']:raise ValueError('BASE_CHANGED_DURING_UPDATE')
            for rel in FILES:atomic(app/rel,new[rel])
            if any(sha(bounded(app/rel))!=spec['files'][rel]['after'] for rel in FILES):raise ValueError('UPDATE_READBACK_CHANGED')
            report['applied']=True
        except BaseException:
            for rel in FILES:
                if sha(bounded(app/rel)) not in (spec['files'][rel]['before'],spec['files'][rel]['after']):
                    report['concurrentEditDetected']=True;raise
            for rel in reversed(FILES):atomic(app/rel,old[rel])
            report['rolledBack']=True;raise
        finally:atomic(backup/'result.json',json.dumps(report,indent=2).encode('utf-8'))
        return dict(report,backup=str(backup),updatedReleaseManifestSHA256=spec['updatedReleaseManifestSHA256'])
    finally:
        # Closing releases only this process's byte lock, including on failure.
        lock.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--application',type=Path,required=True)
    p.add_argument('--patch-manifest',type=Path,required=True);p.add_argument('--patch-sha256',required=True);a=p.parse_args()
    print(json.dumps(apply_update(a.application,a.patch_manifest,a.patch_sha256),indent=2))
if __name__=='__main__':main()
