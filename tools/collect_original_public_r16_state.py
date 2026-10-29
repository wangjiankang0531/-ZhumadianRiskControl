"""Bound R16 metadata collector template; never reads auth, business rows or original logs."""

from pathlib import Path

import ctypes,datetime,hashlib,json,os,shutil,sys,urllib.request,zipfile



APP=Path('C:/Zdm/Application')

DELIVERY=Path('C:/FTP_Root/Zhumadian/Zhumadian_Update_20261029_R16')

RELEASE_PINS = {}

NEW_RELEASE_SHA256 = ''



def sha(raw):return hashlib.sha256(raw).hexdigest()

def read_json(path,limit=4*1024*1024):

    for parent in [path,*path.parents]:

        if parent.is_symlink() or parent.exists() and getattr(parent.lstat(),'st_file_attributes',0)&0x400:raise ValueError('REGULAR_METADATA_FILE_REQUIRED')

    if path.stat().st_size>limit:raise ValueError('METADATA_BOUND')

    with path.open('rb') as stream:raw=stream.read(limit+1)

    if len(raw)>limit:raise ValueError('METADATA_BOUND')

    return raw,json.loads(raw.decode('utf-8-sig'))

def image(pid):

    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)]

    handle=kernel.OpenProcess(0x1000,False,int(pid))

    if not handle:return {'pid':pid,'live':False,'winError':ctypes.get_last_error()}

    try:

        name=ctypes.create_unicode_buffer(32768);size=ctypes.c_ulong(len(name));ok=kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size));return {'pid':pid,'live':bool(ok),'image':name.value if ok else None}

    finally:kernel.CloseHandle(handle)

def main():

    if sys.argv[1:] not in ([],['--after']):raise ValueError('EXACT_METADATA_MODE_REQUIRED')

    after=sys.argv[1:]==['--after'];output=DELIVERY/('public-state-after-r16-20261029.zip' if after else 'public-state-before-r16-20261029.zip')

    if len(RELEASE_PINS)!=2 or len(NEW_RELEASE_SHA256)!=64:raise ValueError('BOUND_R16_PINS_REQUIRED')

    if os.name!='nt' or not APP.is_dir() or not DELIVERY.is_dir() or output.exists():raise ValueError('EXACT_EXISTING_SERVER_AND_FRESH_OUTPUT_REQUIRED')

    for path in [APP,DELIVERY,DELIVERY/'web.config']:

        for parent in [path,*path.parents]:

            if parent.is_symlink() or parent.exists() and getattr(parent.lstat(),'st_file_attributes',0)&0x400:raise ValueError('REGULAR_SERVER_PATH_REQUIRED')

    if sha((DELIVERY/'web.config').read_bytes())!='fcc83fda7178f4b237121ebaf34992ec93092be3485aef71ccc86a3184d1b819':raise ValueError('EXACT_DENY_ALL_CONFIG_REQUIRED')

    release_raw,release=read_json(APP/'release-manifest.json');payload_raw,payload=read_json(APP/'payload-manifest.json');pin=sha(release_raw)

    if pin not in RELEASE_PINS or (after and pin!=NEW_RELEASE_SHA256) or (not after and pin==NEW_RELEASE_SHA256):raise ValueError('EXACT_R15_BEFORE_OR_R16_AFTER_REQUIRED')

    if release['payloadManifestSHA256']!=sha(payload_raw):raise ValueError('INSTALLED_PAYLOAD_MANIFEST_MISMATCH')

    expected=RELEASE_PINS[pin];code_pins={}

    for relative,key in [('tools/original_public_test_update.py','updaterSHA256'),('payload/business/run-template/classes/META-INF/spring.factories','factoriesSHA256')]:

        path=APP/relative

        if not path.is_file() or path.stat().st_size>512*1024 or path.is_symlink() or sha(path.read_bytes())!=expected[key]:raise ValueError('EXACT_DECLARED_SERVER_CODE_REQUIRED')

        code_pins[relative]=expected[key]

    _,run=read_json(APP/'UserData/OriginalServer/current-run.json',65536)

    result={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'collectorSourceSHA256':sha(Path(__file__).read_bytes()),'releaseSHA256':pin,'payloadManifestSHA256':sha(payload_raw),'run':{k:run[k] for k in ['controllerPID','run','gatewayPort','startedAt','persistent','ready','children','databaseUUID'] if k in run},'processes':{'controller':image(run['controllerPID'])},'businessDataCredentialsOrSessionsRead':False,'originalLogsRead':False,'servicesChanged':False,'exactCodePins':code_pins,'freeBytes':shutil.disk_usage(APP).free,'runtimeReports':{}}

    if len(run.get('children',{}))!=6:raise ValueError('EXACT_SIX_CHILD_METADATA_REQUIRED')

    for key,pid in run['children'].items():result['processes'][key]=image(pid)

    run_root=Path(run['run'])

    if run_root.parent!=APP/'UserData/OriginalServer/runs' or not run_root.name.startswith('j') or not run_root.name[1:].isdigit() or run_root.resolve(strict=True)!=run_root:raise ValueError('EXACT_OWN_RUN_LAYOUT_REQUIRED')

    if set(run['children'])!={'store','mysql','redis','platform','business','gateway'} or any(type(v) is not int or v<1 for v in [run['controllerPID'],*run['children'].values()]):raise ValueError('EXACT_OWN_PROCESS_METADATA_REQUIRED')

    root=run_root/'b'

    reports=['transaction-bean-observation.json','work-services-transaction-observation.json','own-finding-observer-ready.json','training-transaction-observation.json','work-safety-batch-observation.json','emergency-team-transaction-observation.json']
    if after:reports+=['event-disposal-transaction-observation.json','emergency-exercise-transaction-observation.json']
    for name in reports:

        path=root/name;result['runtimeReports'][name]=read_json(path,65536)[1] if path.is_file() else None

    result['serverCodePins']={}

    for name in ['tools/install_original_server_ingress.py','tools/original_iis_cutover.py']:

        p=APP/name;result['serverCodePins'][name]={'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} if p.is_file() and not p.is_symlink() else None

    status=DELIVERY/'deployment-status.json'

    if status.is_file():

        _,value=read_json(status,65536);result['previousDeployment']={k:value[k] for k in ['updateId','operation','state','ready','codeApplied','oldNormalShutdownCompleted','manualRecoveryRequired','failureType','newReleaseSHA256','installedReleaseSHA256','currentControllerPID','currentRun','recordedAt'] if k in value}

    latest=APP/'UserData/OriginalPublicUpdates/latest.json'

    if latest.is_file():

        _,value=read_json(latest,65536);result['latestUpdate']={k:value[k] for k in ['updateId','oldReleaseSHA256','newReleaseSHA256','ready','rolledBack','controllerPID','run','databaseUUID','serverLocalTLSVerified','userNormalLoginPending'] if k in value}

    try:

        with urllib.request.urlopen('https://www.joinlinksmart.com/zhumadian/',timeout=10) as response:

            body=response.read(1024*1024+1);result['publicHTTPS']={'status':response.status,'bytes':len(body),'bodySHA256':sha(body),'TLSVerificationDisabled':False}

    except Exception as error:result['publicHTTPS']={'errorType':type(error).__name__,'TLSVerificationDisabled':False}

    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as archive:

        for name,body in [('release-manifest.json',release_raw),('payload-manifest.json',payload_raw),('state.json',raw)]:archive.writestr(name,body)

    print(json.dumps({'output':str(output),'bytes':output.stat().st_size,'SHA256':sha(output.read_bytes()),'releaseSHA256':pin,'liveProcesses':sum(1 for v in result['processes'].values() if v['live']),'servicesChanged':False}))

if __name__=='__main__':main()

