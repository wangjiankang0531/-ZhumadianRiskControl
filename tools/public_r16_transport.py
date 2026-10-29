"""Pinned R16 transport template. Bind the exact R15 variant and new release before delivery.



No execution-policy or system security change. Only the declared owned server.

"""

from pathlib import Path,PurePosixPath

import datetime,hashlib,importlib.util,json,os,sys,uuid,zipfile



VARIANTS = {}

NEW_RELEASE_SHA256 = ''



def require(value,code):

    if not value:raise ValueError(code)

def sha(path):

    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def regular(path):

    for q in [*reversed(path.parents),path]:

        if q.exists() or q.is_symlink():require(not q.is_symlink() and not getattr(q.lstat(),'st_file_attributes',0)&0x400,'REDIRECTED_PATH_REFUSED')

    return path

def select_variant(app,args):

    require(len(VARIANTS)==1 and len(NEW_RELEASE_SHA256)==64,'BOUND_R16_PINS_REQUIRED')

    require(args in ([],['--check-only'],['--recover-pending'],['--rollback-latest']),'EXACT_UPDATE_MODE_REQUIRED')

    if args in (['--recover-pending'],['--rollback-latest']):

        record='latest.json' if args==['--rollback-latest'] else 'pending.json'

        path=regular(app/'UserData/OriginalPublicUpdates'/record)

        require(path.is_file() and path.stat().st_size<=2*1024**2,'OWN_R16_PENDING_RECORD_REQUIRED')

        value=json.loads(path.read_bytes())

        require(value.get('newReleaseSHA256')==NEW_RELEASE_SHA256

                and value.get('updateId') in {v['updateId'] for v in VARIANTS.values()},'ONLY_THIS_R16_RECOVERY_OR_ROLLBACK_ALLOWED')

        # The single archive carries its exact pinned composed updater bytes; recovery uses its own pinned pending record.

        return next(iter(VARIANTS.values()))

    pin=sha(regular(app/'release-manifest.json'))

    require(pin in VARIANTS,'UNKNOWN_OR_ALREADY_UPDATED_RELEASE_NO_FILES_CHANGED')

    return VARIANTS[pin]

def main():

    app=Path('C:/Zdm/Application');root=regular(Path(__file__).absolute().parent);args=sys.argv[1:]

    require(os.name=='nt' and regular(app).resolve(strict=True)==app,'EXACT_SERVER_REQUIRED')

    selected=select_variant(app,args);archive=regular(root/selected['archive']);manifest_pin=selected['manifestSHA256']

    require(sha(archive)==selected['archiveSHA256'],'TRANSPORT_ZIP_SHA256_MISMATCH')

    stage=regular(app/'UserData/OriginalPublicUpdates/staging'/uuid.uuid4().hex)

    with zipfile.ZipFile(archive) as z:

        entries=z.infolist();names=[v.filename for v in entries]

        require(len(entries)<=1100 and len(names)==len(set(names)) and sum(v.file_size for v in entries)<=40*1024**2,'SPARSE_TRANSPORT_BOUND_EXCEEDED')

        raw=z.read('update-manifest.json');require(hashlib.sha256(raw).hexdigest()==manifest_pin,'UPDATE_MANIFEST_SHA256_MISMATCH');plan=json.loads(raw)

        require(plan['newReleaseSHA256']==NEW_RELEASE_SHA256 and plan['updateId']==selected['updateId'],'EXACT_R16_PLAN_REQUIRED')

        require(set(names)=={'update-manifest.json','web.config'}|{'payload/'+v for v in plan['files']},'EXACT_TRANSPORT_MEMBERS_REQUIRED')

        stage.mkdir(parents=True)

        for info in entries:

            rel=PurePosixPath(info.filename)

            require(str(rel)==info.filename and not rel.is_absolute() and all(v not in ('.','..') and ':' not in v and '\\' not in v and not v.endswith((' ','.')) for v in rel.parts),'TRANSPORT_PATH_REJECTED')

            require(not info.is_dir() and ((info.external_attr>>16)&0o170000)!=0o120000,'TRANSPORT_REGULAR_FILE_REQUIRED')

            target=regular(stage.joinpath(*rel.parts));target.parent.mkdir(parents=True,exist_ok=True)

            with target.open('xb') as out,z.open(info) as inp:

                while True:

                    block=inp.read(65536)

                    if not block:break

                    out.write(block)

    helper=stage/'payload/tools/original_public_test_update.py'

    require(sha(helper)==plan['files']['tools/original_public_test_update.py']['SHA256'],'UPDATER_PIN_MISMATCH')

    spec=importlib.util.spec_from_file_location('pinned_public_r16_update',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

    if args==['--check-only']:

        checked,old,_=module.load_bundle(app,stage,manifest_pin);current=module.owned_ready(app,old);module.ingress_preflight(app,checked,{});module.health(app,current)

        module.write_json(root/'preflight-status.json',{'state':'CHECK_ONLY_PASSED','oldReleaseSHA256':old,'newReleaseSHA256':NEW_RELEASE_SHA256,'selectedArchive':selected['archive'],'controllerPID':current['controllerPID'],'servicesChanged':False})

        print('R16_SPARSE_FILES_BASE_HTTPS_AND_CURRENT_SERVICES_VERIFIED; NO_SERVICE_CHANGED',flush=True)

        return

    sys.argv=[str(helper),'--application',str(app)]+(args if args else ['--apply',str(stage),'--manifest-sha256',manifest_pin])

    status_path=regular(root/'deployment-status.json');operation='apply' if not args else ('recover' if args==['--recover-pending'] else 'rollback')

    status={'updateId':plan['updateId'],'operation':operation,'state':'UPDATER_RUNNING','archiveSHA256':selected['archiveSHA256'],'selectedArchive':selected['archive'],'publicAccepted':False};module.write_json(status_path,status)

    try:

        module.main();installed=sha(app/'release-manifest.json');current=module.owned_ready(app,installed);status.update(state='SERVER_STEP_COMPLETED_EXTERNAL_VERIFICATION_PENDING',installedReleaseSHA256=installed,currentControllerPID=current['controllerPID'],currentRun=current['run'],ready=True)

    except BaseException as error:

        status.update(state='STOPPED_INSPECT_SERVER_RESULT',failureType=type(error).__name__);raise

    finally:

        pending=app/'UserData/OriginalPublicUpdates/pending.json'

        if pending.is_file():

            value=json.loads(pending.read_bytes())

            if value.get('newReleaseSHA256')==NEW_RELEASE_SHA256:

                for key in ['ready','codeApplied','oldNormalShutdownCompleted','manualRecoveryRequired','failureType','newReleaseSHA256','serverLocalTLSVerified','userNormalLoginPending','recovered']:

                    if key in value and (operation=='apply' or key not in ('ready','newReleaseSHA256')):status[key]=value[key]

        if status['state']=='STOPPED_INSPECT_SERVER_RESULT':status['ready']=False

        status['recordedAt']=datetime.datetime.now().astimezone().isoformat();module.write_json(status_path,status)

if __name__=='__main__':main()

