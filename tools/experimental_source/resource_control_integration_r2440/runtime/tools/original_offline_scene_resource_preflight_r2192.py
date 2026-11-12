"""Run the original spatial/models preflight for the client-offline role against a private, pinned code view.

The live installation is read only. A gated, owned Python child validates the
actual original resources; it never starts services, edits accounts or emits
private settings. Every temporary code link is retired only after Job zero.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, traceback

PRIVATE_ACL_SHA='bb1a0c0fac7053efec1fde8020cc344bb158a9ab08674b40e68701f442e3f2dd'
GATE=b'XNBY_OWN_RESOURCE_PREFLIGHT_R2192\n'

def need(ok,code):
    if not ok:raise ValueError(code)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def plain(path):
    path=Path(path).absolute();need('..'not in path.parts and path.resolve()==path,'SCENE_RESOURCE_CANONICAL_PATH_REQUIRED')
    for p in [path,*path.parents]:
        need(not p.is_symlink() and not p.is_junction() and (not p.exists() or not p.lstat().st_file_attributes&0x400),
             'SCENE_RESOURCE_REPARSE_REFUSED')
    return path

def child(root,release_sha,port):
    root=plain(root);release_path=root/'release-manifest.json'
    need(sha(release_path)==release_sha,'SCENE_RESOURCE_CHILD_RELEASE_PIN_REQUIRED')
    release=json.loads(release_path.read_bytes())
    helper=root/'tools/original_spatial_sync_release_support.py'
    need(sha(helper)==release['controllerFiles']['tools/original_spatial_sync_release_support.py'],
         'SCENE_RESOURCE_ORIGINAL_HELPER_PIN_REQUIRED')
    sys.path.insert(0,str(root/'tools'))
    from original_spatial_sync_release_support import preflight as original_preflight
    value=original_preflight(root,release,gateway_port=port)
    need(value is not None and value['localGIS']is not None and 'fineSource'not in release,'SCENE_RESOURCE_CLIENT_OFFLINE_ROLE_REQUIRED')
    need(value['sceneModels']is not None and value['sceneLibrary']is not None,'SCENE_RESOURCE_BOTH_LIBRARIES_REQUIRED')
    need(not any(name.startswith('original_fine')for name in sys.modules),'SCENE_RESOURCE_NO_SERVER_GIS_IMPORT_ALLOWED')
    models=sum(row['route'].endswith('.glb')for row in value['sceneRows'])
    need(1<=models<=64,'SCENE_RESOURCE_MODELS_REQUIRED')
    return {'passed':True,'clientGISExcludedFromServerLifecycle':True,'originalSpatialPreflightExecuted':True,
            'sceneRoutes':len(value['sceneRows']),'modelAssetPinsVerified':models,
            'modelStorageConfigured':True,'namedSceneLibraryConfigured':True,
            'serviceProcessesStarted':0,'originalResourcesReferencedNotCopied':True,'settingsOrIdentityValuesReturned':False}

def preflight(m,app,bundle,plan,release):
    app=plain(app);bundle=plain(bundle)
    descriptor=release['spatialSync'];settings=m.check_file(app,descriptor['settingsPath'],descriptor['settingsSHA256'])
    need(settings.stat().st_size<=32768,'SCENE_RESOURCE_BOUNDED_PRIVATE_SETTINGS_REQUIRED')
    def pairs(items):
        result={}
        for k,v in items:
            need(k not in result,'SCENE_RESOURCE_DUPLICATE_PRIVATE_FIELD');result[k]=v
        return result
    value=json.loads(settings.read_bytes(),object_pairs_hook=pairs)
    # The shadow's directory differs from the installed root. Retain the
    # original installed-root data separation policy before constructing it.
    for key in ['dataRoot','projectFilesRoot','sceneProjectsRoot','sceneModelsRoot']:
        if key in value:
            p=plain(value[key]);need(not p.is_relative_to(app) and not app.is_relative_to(p),
                                     'SCENE_RESOURCE_DATA_MUST_REMAIN_OUTSIDE_INSTALLED_APPLICATION')

    release_path=m.check_file(bundle/'payload','release-manifest.json',plan['newReleaseSHA256'])
    payload=json.loads(m.check_file(bundle/'payload','payload-manifest.json',plan['newPayloadManifestSHA256']).read_bytes())
    selected={n for n in release['controllerFiles'] if n.startswith('extensions/') or n.startswith('tools/') and n.endswith(('.py','.json'))}
    static=release['sceneStatic'];sm=m.check_file(bundle/'payload' if static['manifestPath'] in plan['files'] else app,
                                                static['manifestPath'],static['manifestSHA256'])
    static_rows=json.loads(sm.read_bytes())['files'];selected.add(static['manifestPath'])
    selected.update(str(Path(static['manifestPath']).parent/Path(n)).replace('\\','/') for n in static_rows)
    selected.add(descriptor['settingsPath'])
    source_pins={}
    for name in selected:
        if name==descriptor['settingsPath']:source_pins[name]=settings
        else:
            row=payload['files'].get(name)
            pin=row['sha256'] if row else release['controllerFiles'][name]
            source_pins[name]=m.check_file(bundle/'payload' if name in plan['files'] else app,name,pin)
    executable=m.check_file(app,'runtime/python/python.exe',payload['files']['runtime/python/python.exe']['sha256'])
    jobs_path=m.check_file(app,'tools/original_server_windows_job.py',release['controllerFiles']['tools/original_server_windows_job.py'])
    spec=importlib.util.spec_from_file_location('scene_resource_owned_jobs_r2192',jobs_path)
    jobs=importlib.util.module_from_spec(spec);spec.loader.exec_module(jobs)
    root=plain(tempfile.mkdtemp(prefix='pf-',dir=bundle));need(root.parent==bundle,'SCENE_RESOURCE_OWN_TEMP_ROOT_REQUIRED')
    process=None;job=None;terminal=False;closed=False
    try:
        acl_source=source_pins['tools/original_private_directory_r2191.py']
        need(sha(acl_source)==PRIVATE_ACL_SHA,'SCENE_RESOURCE_EXACT_PRIVATE_ACL_HELPER_REQUIRED')
        acl_spec=importlib.util.spec_from_file_location('scene_private_view_acl_r1977',acl_source)
        acl_module=importlib.util.module_from_spec(acl_spec);acl_spec.loader.exec_module(acl_module)
        acl=acl_module.private_directory(root)
        need(acl=={'protectedDACL':True,'onlySystemAndAdministratorsFullControl':True},
             'SCENE_RESOURCE_PRIVATE_VIEW_DACL_REQUIRED_BEFORE_FILES')
        for name,source in source_pins.items():
            if name==descriptor['settingsPath']:continue
            target=plain(root/name);target.parent.mkdir(parents=True,exist_ok=True);need(not target.exists(),'SCENE_RESOURCE_FRESH_VIEW_REQUIRED')
            os.link(source,target)
        stage_value=copy.deepcopy(value);rebased=0
        for key in ['sceneModelCatalog','sceneModelsCatalog']:
            if key in stage_value and plain(stage_value[key]).is_relative_to(app):
                name=plain(stage_value[key]).relative_to(app).as_posix()
                need(name in selected and name.startswith('frontend/scene/'),
                     'SCENE_RESOURCE_ONLY_PINNED_STATIC_CATALOG_REBASE_ALLOWED')
                expected=stage_value['sceneModelCatalogSHA256' if key=='sceneModelCatalog' else 'sceneModelsCatalogSHA256']
                need(sha(root/name)==expected,'SCENE_RESOURCE_STAGED_CATALOG_SOURCE_CHANGED')
                stage_value[key]=str(root/name);rebased+=1
        raw=(json.dumps(stage_value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
        target=plain(root/descriptor['settingsPath']);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        stage_release=copy.deepcopy(release);stage_release['spatialSync']['settingsSHA256']=hashlib.sha256(raw).hexdigest()
        stage_raw=(json.dumps(stage_release,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
        (root/'release-manifest.json').write_bytes(stage_raw);stage_sha=hashlib.sha256(stage_raw).hexdigest()
        stage_value.clear();value.clear();stage_release.clear();raw=b'';stage_raw=b''
        bootstrap="import runpy,sys;assert sys.stdin.buffer.readline(128)==b'XNBY_OWN_RESOURCE_PREFLIGHT_R2192\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
        command=[str(executable),'-I','-B','-c',bootstrap,str(Path(__file__).absolute()),'--child',str(root),stage_sha,str(plan['gatewayPort'])]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 cwd=root,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        try:job=jobs.OwnedWindowsJob(process)
        except BaseException:
            process.stdin.write(b'cancel\n');process.stdin.close()
            while process.poll() is None:
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
            terminal=True;raise
        raw=GATE;first=True
        while True:
            try:out,err=process.communicate(input=raw if first else None,timeout=15);break
            except subprocess.TimeoutExpired:first=False;raw=b''
        need(len(out)<=65536 and len(err)<=65536,'SCENE_RESOURCE_BOUNDED_CHILD_OUTPUT_REQUIRED')
        while job.active_processes():
            # The original Job has no force-on-close semantics. Keep observing
            # these exact handles instead of closing it on a timeout.
            __import__('time').sleep(.1)
        terminal=True;job.close();closed=True
        result=json.loads(out)
        if process.returncode!=0 or result.get('passed') is not True:
            error=ValueError('SCENE_RESOURCE_ORIGINAL_PREFLIGHT_FAILED:'+str(result.get('closedCode') or 'NO_CLOSED_CODE'))
            error.diagnosis={k:result.get(k) for k in ['type','closedCode','frames','missingModule']};raise error
        return dict(result,actualChildExitCode=process.returncode,actualJobZero=True,
                    stageCodeFiles=len(source_pins),privateViewRemovedAfterJobZero=True,
                    originalSettingsPinVerified=True,immutableCatalogPathsRebasedForPrivateView=rebased,
                    dataRootsAndAccessSemanticsUnchanged=True,privateViewDACLProtectedBeforeFiles=True)
    finally:
        if process is None or terminal and (job is None or closed):
            plain(root)
            for directory,dirs,names in os.walk(root,followlinks=False):
                for name in dirs+names:plain(Path(directory)/name)
            shutil.rmtree(root);need(not root.exists(),'SCENE_RESOURCE_PRIVATE_VIEW_CLEANUP_REQUIRED')

if __name__=='__main__':
    try:
        need(len(sys.argv)==5 and sys.argv[1]=='--child','SCENE_RESOURCE_CHILD_ARGUMENTS_REQUIRED')
        result=child(Path(sys.argv[2]),sys.argv[3],int(sys.argv[4]));print(json.dumps(result));raise SystemExit(0)
    except Exception as error:
        code=str(error);closed=code if re.fullmatch('[A-Z0-9_:/.-]{1,200}',code) else None
        frames=[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)]
        missing=getattr(error,'name',None);missing=missing if isinstance(missing,str) and re.fullmatch('[A-Za-z0-9_.]{1,100}',missing) else None
        print(json.dumps({'passed':False,'type':type(error).__name__,'closedCode':closed,'frames':frames,'missingModule':missing,'settingsOrIdentityValuesReturned':False}));raise SystemExit(1)
