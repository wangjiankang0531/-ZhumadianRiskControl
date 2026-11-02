from pathlib import Path,PurePosixPath
import hashlib,importlib.util,json,os,re,sys,uuid,zipfile
APP=Path('C:/inetpub/wwwroot/Zhumadian/Application')
ARCHIVE_SHA='1e2f701c32ff0a1645daee21ef3ecc1b15df7cdf257dd7c3169ebdb0434f8b6c'
MANIFEST_SHA='b3e9bdb2dddd48322a7fbe250771f29501e051dfffaafabd55274ed2ffb88236'
OLD='19ff463fce665b146975e238451725f063c772260485df72c6bbfd2da6c384d1'
NEW='bd3da492c0f226c62bf00e2e416521bd860d8d4c748fe8b34b1537d69854f1ea'
UPDATE='20261102-R32-two-portal-avatar-from-exact-R31'
UPDATER_SHA='97139494d048254cfa559d58eb5125a00ff370c3422acebe59a216e7a37fe6f3'
OLD_UPDATER_SHA='477cd84dbce633623db7d31d6bf1504455cbcfa114f44c53f4c5d751a00d64ac'
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def regular(path):
    path=Path(path).absolute()
    for p in [*reversed(path.parents),path]:
        if p.exists()or p.is_symlink():
            need(not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'REDIRECTED_PATH_REFUSED')
    return path
def recovery_guard(report):
    need(report.get('updateId')==UPDATE,'ONLY_THIS_UPDATE')
    need(report.get('oldReleaseSHA256')==OLD,'ONLY_THIS_OLD_RELEASE')
    need(report.get('newReleaseSHA256')==NEW,'ONLY_THIS_NEW_RELEASE')
    need(Path(report['attempt']).absolute().parent==APP/'UserData/OriginalPublicUpdates','ONLY_OWN_BACKUP_PARENT')
def main():
    sys.dont_write_bytecode=True
    need(os.name=='nt'and regular(APP).resolve(strict=True)==APP,'EXACT_SERVER')
    mode=sys.argv[1:]
    need(mode in ([],['--check-only'],['--recover-this-update']),'ONLY_SCOPED_MODES')
    root=regular(Path(__file__).absolute().parent)
    installed=regular(APP/'tools/original_public_test_update.py')
    need(sha(installed) in (OLD_UPDATER_SHA,UPDATER_SHA),'EXACT_OLD_OR_THIS_UPDATE_UPDATER')
    source=regular(root/'r32_update_runtime.py')
    need(sha(source)==UPDATER_SHA,'EXACT_FIXED_R32_UPDATE_RUNTIME')
    sys.path.insert(0,str(APP/'tools'))
    spec=importlib.util.spec_from_file_location('fixed_r32_updater',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if mode==['--recover-this-update']:
        pending=m.read(regular(APP/'UserData/OriginalPublicUpdates/pending.json'))
        if pending.get('updateId')==UPDATE and pending.get('failureType')and not pending.get('ready'):
            recovery_guard(pending);m.recover_pending(APP)
        else:
            latest=m.read(regular(APP/'UserData/OriginalPublicUpdates/latest.json'))
            recovery_guard(latest)
            need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_ROLLBACK')
            m.rollback_latest(APP)
        return
    archive=regular(root/'Zhumadian_Avatar_Two_Portals_20261102_R32.zip')
    need(sha(archive)==ARCHIVE_SHA,'EXACT_FIXED_ARCHIVE')
    stage=regular(APP/'UserData/OriginalPublicUpdates/staging'/uuid.uuid4().hex)
    with zipfile.ZipFile(archive)as z:
        entries=z.infolist();names=[v.filename for v in entries]
        need(len(entries)<=1100 and len(names)==len(set(names))and sum(v.file_size for v in entries)<=40*1024**2,'CLOSED_TRANSPORT_BOUNDS')
        raw=z.read('update-manifest.json')
        need(hashlib.sha256(raw).hexdigest()==MANIFEST_SHA,'FIXED_UPDATE_MANIFEST')
        plan=json.loads(raw)
        need(plan['updateId']==UPDATE and plan['newReleaseSHA256']==NEW,'FIXED_UPDATE_IDENTITY')
        need(set(names)=={'update-manifest.json','web.config'}|{'payload/'+v for v in plan['files']},'EXACT_CLOSED_MEMBERS')
        for info in entries:
            rel=PurePosixPath(info.filename)
            need(str(rel)==info.filename and not rel.is_absolute()and all(p not in ('.','..')and not re.search(r'[\\:\x00-\x1f]',p)and not p.endswith((' ','.'))for p in rel.parts),'EXACT_RELATIVE_MEMBER')
            need(not info.is_dir()and ((info.external_attr>>16)&0o170000)!=0o120000,'REGULAR_MEMBERS')
        stage.mkdir(parents=True)
        for info in entries:
            dest=regular(stage.joinpath(*PurePosixPath(info.filename).parts));dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb')as target,z.open(info)as stream:
                while True:
                    chunk=stream.read(65536)
                    if not chunk:break
                    target.write(chunk)
    checked,old,changes=m.load_bundle(APP,stage,MANIFEST_SHA)
    need(old==OLD and checked['newReleaseSHA256']==NEW,'EXACT_R31_BASE')
    candidate_pool=m.candidate_runtime_pool_preflight(APP,stage,checked)
    need(candidate_pool is not None,'EXACT_CANDIDATE_POOL_PREFLIGHT_REQUIRED')
    print('R32_CANDIDATE_POOL_LAYOUT_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)
    row=m.owned_ready(APP,old);m.health(APP,row)
    if mode==['--check-only']:
        print('R32_PREFLIGHT_PASSED_EXACT_R31_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return
    m.apply_update(APP,stage,MANIFEST_SHA)
    print('R32_APPLY_COMPLETED_EXTERNAL_HTTPS_AND_USER_LAYOUT_PENDING',flush=True)
if __name__=='__main__':main()
