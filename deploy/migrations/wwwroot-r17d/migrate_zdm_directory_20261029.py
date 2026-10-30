"""Pinned directory migration steps. Only the PowerShell coordinator moves directories."""
from pathlib import Path
import argparse,ctypes,datetime,hashlib,http.client,importlib.util,json,os,shutil,socket,ssl,subprocess,sys,time,xml.etree.ElementTree as ET

OLD=Path('C:/Zdm/Application')
NEW=Path('C:/inetpub/wwwroot/Zhumadian/Application')
OLDIIS=Path('C:/FTP_Root/Zhumadian/ZhumadianBusiness_0.8.7_public_1/iis')
STAGE=Path('C:/FTP_Root/Zhumadian/Zhumadian_Directory_Migration_20261030_R17D')
BACKUP='UserData/OriginalDirectoryMigration/20261030_r17d'
STATUS=STAGE/'migration-status.json'
PROTECTED=['UserData/OriginalServer/database','UserData/OriginalServer/store-data','UserData/TianjinOriginalPlatform/files','private']
POINTERS=['UserData/OriginalDeployment/active-deployment.private.json','UserData/OriginalPublicUpdates/latest.json','UserData/OriginalPublicUpdates/pending.json']
REPORTS=['transaction-bean-observation.json','work-services-transaction-observation.json','own-finding-observer-ready.json','training-transaction-observation.json','work-safety-batch-observation.json','emergency-team-transaction-observation.json','event-disposal-transaction-observation.json','emergency-exercise-transaction-observation.json']
HIDDEN=['App_Code','App_Data','App_GlobalResources','App_LocalResources','App_WebReferences','App_Browsers','bin','web.config','private','UserData','runtime','payload','seed','tools','deploy','frontend','release-manifest.json','payload-manifest.json']

def need(condition,code):
    if not condition:raise ValueError(code)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def regular(path):
    path=Path(path).absolute()
    for p in [*reversed(path.parents),path]:
        if p.exists() or p.is_symlink():need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'REPARSE_PATH_REFUSED')
    return path

def read(path):
    path=regular(path);need(path.stat().st_size<8*1024**2,'BOUNDED_METADATA_REQUIRED');return json.loads(path.read_bytes())

def write(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();path=regular(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name('.migration-'+path.name+'.tmp');need(not temp.exists(),'NO_PENDING_METADATA_WRITE');temp.write_bytes(raw);os.replace(temp,path)

def status(phase,**extra):
    old=read(STATUS) if STATUS.exists() else {'schema':'xnby.server-directory-migration.status.v1'}
    if old.get('migrationRevision')!='R17d':old={'schema':'xnby.server-directory-migration.status.v1','migrationRevision':'R17d','ready':False}
    if not phase.startswith('STOPPED_'):
        for key in ['failureType','failureCode','manualRecoveryRequired']:old.pop(key,None)
    old.update(phase=phase,at=datetime.datetime.now().astimezone().isoformat(),sourceSHA256=sha(Path(__file__)),manifestSHA256=sha(STAGE/'migration-manifest.json'),**extra);write(STATUS,old)
    with (STAGE/'migration-phase-history.jsonl').open('a',encoding='utf-8') as history:history.write(json.dumps(old,ensure_ascii=False)+'\n')
    print(json.dumps({'phase':phase,**extra}),flush=True)

def updater(app,baseline=False):
    source=app/BACKUP/'before/tools/original_public_test_update.py' if baseline else app/'tools/original_public_test_update.py'
    sys.path.insert(0,str(app/'tools'));spec=importlib.util.spec_from_file_location('migration_owned_updater',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def identity(app):
    install=read(app/'UserData/OriginalServer/installation.json')
    return {'databaseUUID':install['databaseUUID'],'installationSHA256':sha(app/'UserData/OriginalServer/installation.json'),'platformIdentitySHA256':sha(app/'UserData/TianjinOriginalPlatform/identity.json')}

def metadata_tree(root):
    regular(root);files=[];total=0
    for folder,dirs,names in os.walk(root,followlinks=False):
        regular(Path(folder))
        for name in dirs:regular(Path(folder)/name)
        for name in sorted(names):
            p=regular(Path(folder)/name);s=p.stat();need(p.is_file(),'REGULAR_DATA_FILES_REQUIRED');files.append((p.relative_to(root).as_posix(),s.st_size,s.st_mtime_ns,s.st_ino));total+=s.st_size
    h=hashlib.sha256(json.dumps(sorted(files),separators=(',',':')).encode()).hexdigest();s=root.stat()
    return {'files':len(files),'logicalBytes':total,'metadataSHA256':h,'directoryFileID':s.st_ino,'volumeID':s.st_dev}

def mappings():
    exe=str(Path(os.environ['SystemRoot'])/'System32/inetsrv/appcmd.exe');p=subprocess.run([exe,'list','vdir','/xml'],capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);need(p.returncode==0,'IIS_MAPPING_READ_FAILED')
    return [{k:n.get(k) for k in ['VDIR.NAME','APP.NAME','path','physicalPath']} for n in ET.fromstring(p.stdout)]

def mapping_state(expected):
    rows=mappings();own=[x for x in rows if x['VDIR.NAME']==expected['VDIR.NAME']];need(len(own)==1,'EXACT_IIS_ENTRY_REQUIRED');other=[x for x in rows if x['VDIR.NAME']!=expected['VDIR.NAME']]
    return own[0],{'count':len(other),'SHA256':hashlib.sha256(json.dumps(other,sort_keys=True).encode()).hexdigest()}

def set_mapping(plan,target):
    current,other=mapping_state(plan['iisMapping']);need(other==plan['otherMappings'],'OTHER_IIS_MAPPINGS_DRIFT')
    need(Path(current['physicalPath']) in (OLDIIS,NEW/'iis'),'OWN_IIS_MAPPING_DRIFT')
    if Path(current['physicalPath'])!=target:
        exe=str(Path(os.environ['SystemRoot'])/'System32/inetsrv/appcmd.exe');p=subprocess.run([exe,'set','vdir',plan['iisMapping']['VDIR.NAME'],'/physicalPath:'+str(target)],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);need(p.returncode==0,'OWN_IIS_MAPPING_CHANGE_FAILED')
    current,other=mapping_state(plan['iisMapping']);need(Path(current['physicalPath'])==target and other==plan['otherMappings'],'IIS_MAPPING_VERIFY_FAILED')

def all_root_images(app):
    command="[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; @(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -and $_.ExecutablePath.StartsWith('"+str(app)+"\\',[StringComparison]::OrdinalIgnoreCase)} | Select-Object ProcessId,ParentProcessId,ExecutablePath) | ConvertTo-Json -Compress"
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW);need(p.returncode==0,'ROOT_PROCESS_QUERY_FAILED')
    value=json.loads(p.stdout.decode('utf-8-sig')) if p.stdout.strip() else [];return value if isinstance(value,list) else [value]

def verify_owned_images(app,row,images,inspector_pid):
    roles={'controller':'runtime/python/python.exe','store':'runtime/minio/minio.exe','mysql':'runtime/mysql/bin/mysqld.exe','redis':'runtime/redis/redis-server.exe','platform':'runtime/jdk8/bin/java.exe','business':'runtime/jdk17/bin/java.exe','gateway':'runtime/nginx/nginx.exe'}
    declared=dict(row['children'],controller=row['controllerPID']);observed={x['ProcessId']:x for x in images if x['ProcessId']!=inspector_pid}
    need(set(declared)==set(roles) and len(set(declared.values()))==7,'EXACT_REGISTERED_COMPONENTS_REQUIRED')
    for role,pid in declared.items():
        need(pid in observed and Path(observed[pid]['ExecutablePath'])==app/roles[role],'DECLARED_COMPONENT_IMAGE_MISMATCH')
        if role!='controller':need(observed[pid]['ParentProcessId']==row['controllerPID'],'COMPONENT_PARENT_OWNERSHIP_MISMATCH')
    extra=[x for pid,x in observed.items() if pid not in declared.values()]
    # The pinned gateway recipe explicitly uses master_process on and worker_processes 1.
    need(len(extra)==1 and extra[0]['ParentProcessId']==row['children']['gateway'] and Path(extra[0]['ExecutablePath'])==app/'runtime/nginx/nginx.exe','UNKNOWN_ROOT_PROCESS_PRESERVED')
    return {'registeredComponents':7,'ownedGatewayWorkers':1,'totalImages':len(observed)}

def check_package(pin):
    need(os.name=='nt' and Path(__file__).resolve().parent==STAGE,'EXACT_SERVER_STAGE_REQUIRED');regular(STAGE);need(sha(STAGE/'migration-manifest.json')==pin,'MIGRATION_MANIFEST_PIN_REQUIRED');plan=read(STAGE/'migration-manifest.json')
    for name,row in plan['stageFiles'].items():
        path=regular(STAGE/name);need(path.stat().st_size==row['bytes'] and sha(path)==row['SHA256'],'STAGED_SOURCE_DRIFT')
    return plan

def validate_old(plan):
    regular(OLD);regular(NEW);regular(OLDIIS);need(sha(OLD/'release-manifest.json')==plan['oldReleaseSHA256'],'EXACT_R16_REQUIRED')
    need(set(p.name for p in OLD.parent.iterdir())=={'Application'},'UNKNOWN_ZDM_CONTENT_PRESERVED')
    need(not NEW.exists() or NEW.is_dir() and not any(NEW.iterdir()),'TARGET_MUST_BE_ABSENT_OR_EMPTY')
    need(not NEW.parent.exists() or not any(NEW.parent.iterdir()) or set(p.name for p in NEW.parent.iterdir())=={'Application'},'PROJECT_CONTAINER_MUST_BE_EMPTY')
    need(not (OLD/BACKUP).exists(),'MIGRATION_NOT_REPEATED')
    release=read(OLD/'release-manifest.json');need(sha(OLD/'payload-manifest.json')==release['payloadManifestSHA256']==plan['payloadManifestSHA256'],'PAYLOAD_MANIFEST_UNCHANGED_REQUIRED')
    for name,pin in release['controllerFiles'].items():need(sha(regular(OLD/name))==pin,'INSTALLED_CONTROLLER_DRIFT')
    for name,row in plan['replacements'].items():need(sha(regular(OLD/name))==row['before'],'ALL_MIGRATION_PREIMAGES_REQUIRED_BEFORE_STOP')
    for name,pin in plan['iisFiles'].items():need(sha(OLDIIS/name)==pin,'IIS_FILE_DRIFT')
    current,other=mapping_state(plan['iisMapping']);need(current==plan['iisMapping'] and other==plan['otherMappings'],'IIS_PREFLIGHT_DRIFT')
    module=updater(OLD);row=module.owned_ready(OLD,plan['oldReleaseSHA256']);module.health(OLD,row)
    image_summary=verify_owned_images(OLD,row,all_root_images(OLD),os.getpid())
    need(len(str(NEW/'UserData/TianjinOriginalPlatform/t9999'))<=80,'REAL_JDK_TEMP_LIMIT_PRESERVED')
    files=0;maximum=0
    for folder,dirs,names in os.walk(OLD,followlinks=False):
        regular(Path(folder))
        for name in dirs:regular(Path(folder)/name)
        for name in names:regular(Path(folder)/name);files+=1;maximum=max(maximum,len(str(NEW/(Path(folder)/name).relative_to(OLD))))
    sys.path.insert(0,str(OLD/'tools'));import install_original_server_ingress as ingress
    info={};address=ingress.preflight(OLD,OLDIIS,info)
    return row,{'identity':identity(OLD),'existingFiles':files,'maximumMovedFilePathCharacters':maximum,'httpsAddress':address,'oldControllerPID':row['controllerPID'],'oldChildren':row['children'],'oldRun':row['run'],'ownedImageSummary':image_summary}

def prepare_retry(plan):
    need(sha(OLD/'release-manifest.json')==plan['oldReleaseSHA256'],'RESTORED_R16_REQUIRED')
    module=updater(OLD);row=module.owned_ready(OLD,plan['oldReleaseSHA256']);module.health(OLD,row)
    current,other=mapping_state(plan['iisMapping']);need(current==plan['iisMapping'] and other==plan['otherMappings'],'ORIGINAL_IIS_STILL_ACTIVE_REQUIRED')
    previous=regular(OLD/'UserData/OriginalDirectoryMigration/20261029_r17c');need(previous.is_dir(),'OWN_FAILED_ATTEMPT_REQUIRED')
    root_config=regular(OLD/'web.config');iis=regular(OLD/'iis');archive=previous/'created-during-failed-attempt';need(not archive.exists(),'FAILED_ARTIFACTS_NOT_ALREADY_ARCHIVED')
    need(sha(root_config)==sha(STAGE/'payload/web.config'),'OWN_GENERATED_ROOT_CONFIG_REQUIRED')
    actual={p.relative_to(iis).as_posix() for p in iis.rglob('*') if p.is_file()};need(actual=={'web.config','App_Code/XnbyReferenceProxy.cs'},'NO_UNKNOWN_GENERATED_IIS_CONTENT')
    need(sha(iis/'App_Code/XnbyReferenceProxy.cs')==plan['iisFiles']['App_Code/XnbyReferenceProxy.cs'],'OWN_GENERATED_IIS_CODE_REQUIRED')
    need((iis/'web.config').read_bytes()==protect_iis((OLDIIS/'web.config').read_bytes()),'OWN_GENERATED_IIS_CONFIGURATION_REQUIRED')
    archive.mkdir();os.rename(root_config,archive/'web.config');os.rename(iis,archive/'iis')
    status('FAILED_ATTEMPT_ARTIFACTS_ARCHIVED',currentWebsiteKeptRunning=True,currentControllerPID=row['controllerPID'])

def stop_old(plan):
    row,details=validate_old(plan);root=OLD/BACKUP;root.mkdir(parents=True)
    for name in [*plan['replacements'],*POINTERS]:
        path=regular(OLD/name);dest=root/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    for name in plan['iisFiles']:
        dest=root/'original-iis'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLDIIS/name,dest)
    details['oldAppFileID']=OLD.stat().st_ino;write(root/'before-metadata.json',details)
    status('NORMAL_SHUTDOWN_REQUESTED',oldReleaseSHA256=plan['oldReleaseSHA256'],servicesChanged=True,ready=False)
    final=updater(OLD).normal_stop(OLD,plan['oldReleaseSHA256'],row)
    need(not [x for x in all_root_images(OLD) if x['ProcessId']!=os.getpid()],'OLD_ROOT_STILL_IN_USE')
    snapshots={name:metadata_tree(OLD/name) for name in PROTECTED};write(root/'protected-after-stop.json',snapshots)
    status('OLD_NORMAL_SHUTDOWN_COMPLETE',oldNormalShutdownCompleted=True,sixNormalZeroExitCodes=all(x==0 for x in final['exitCodesBeforeJobClose'].values()))

def compare_reports(old_root,new_root):
    skip={'PID','run','ownerIdSHA256'}
    for name in REPORTS:
        before=read(old_root/name);after=read(new_root/name)
        need({k:v for k,v in before.items() if k not in skip}=={k:v for k,v in after.items() if k not in skip},'READINESS_SEMANTICS_CHANGED')

def protect_iis(config):
    root=ET.fromstring(config);server=root.find('system.webServer');need(server is not None,'IIS_SERVER_SECTION_REQUIRED')
    security=server.find('security')
    if security is None:security=ET.SubElement(server,'security')
    filtering=security.find('requestFiltering')
    if filtering is None:filtering=ET.SubElement(security,'requestFiltering')
    hidden=filtering.find('hiddenSegments')
    if hidden is None:hidden=ET.SubElement(filtering,'hiddenSegments')
    hidden.clear();ET.SubElement(hidden,'clear')
    for name in HIDDEN:ET.SubElement(hidden,'add',segment=name)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def private_path_head(address,path):
    # Never read a response body when testing paths that would contain private data.
    raw=socket.create_connection((address,443),timeout=12)
    secure=ssl.create_default_context().wrap_socket(raw,server_hostname='www.joinlinksmart.com')
    client=http.client.HTTPConnection('www.joinlinksmart.com',timeout=12);client.sock=secure
    try:
        client.request('HEAD',path,headers={'Host':'www.joinlinksmart.com','Connection':'close'})
        return client.getresponse().status
    finally:client.close()

def rebase_active(value):
    if isinstance(value,dict):return {k:rebase_active(v) for k,v in value.items()}
    if isinstance(value,list):return [rebase_active(v) for v in value]
    if isinstance(value,str):
        for old,new in [(str(OLD),str(NEW)),(OLD.as_posix(),NEW.as_posix())]:
            if value==old or value.startswith(old+'\\') or value.startswith(old+'/'):return new+value[len(old):]
    return value

def apply_new(plan):
    need(NEW.exists() and not OLD.exists(),'ONE_MOVED_ROOT_REQUIRED');root=NEW/BACKUP;details=read(root/'before-metadata.json')
    need(NEW.stat().st_ino==details['oldAppFileID'],'SAME_VOLUME_DIRECTORY_MOVE_REQUIRED')
    snapshots={name:metadata_tree(NEW/name) for name in PROTECTED};need(snapshots==read(root/'protected-after-stop.json'),'PROTECTED_FILE_IDENTITIES_OR_METADATA_CHANGED_DURING_MOVE')
    write(root/'protected-after-move.json',snapshots);status('MOVED_DATA_IDENTITIES_VERIFIED',protectedTreesPreserved=True,sameVolumeRename=True)
    for name,row in plan['replacements'].items():
        need(sha(regular(NEW/name))==row['before'],'CODE_CHANGED_BEFORE_MIGRATION_PATCH');source=STAGE/'payload'/name;need(sha(source)==row['after'],'NEW_SOURCE_PIN_REQUIRED');shutil.copyfile(source,NEW/name)
    need(not (NEW/'web.config').exists() and not (NEW/'iis').exists(),'NO_EXISTING_WEBROOT_OVERWRITE')
    shutil.copyfile(STAGE/'payload/web.config',NEW/'web.config');(NEW/'iis/App_Code').mkdir(parents=True)
    old_iis_config=(root/'original-iis/web.config').read_bytes();new_iis_config=protect_iis(old_iis_config)
    (NEW/'iis/web.config').write_bytes(new_iis_config);shutil.copyfile(root/'original-iis/App_Code/XnbyReferenceProxy.cs',NEW/'iis/App_Code/XnbyReferenceProxy.cs')
    for name in POINTERS:write(NEW/name,rebase_active(read(NEW/name)))
    module=updater(NEW);status('STARTING_NEW_ROOT',newReleaseSHA256=plan['newReleaseSHA256'])
    row=module.launch(NEW,plan['newReleaseSHA256'],root);module.health(NEW,row)
    need(identity(NEW)==details['identity'],'INSTALLATION_OR_DATABASE_IDENTITY_CHANGED')
    old_run=NEW/Path(details['oldRun']).relative_to(OLD);compare_reports(old_run/'b',Path(row['run'])/'b')
    # Prepare the new IIS rollback transaction locally; its private key never leaves the server.
    rollback=root/'iis-backup';rollback.mkdir()
    for name in plan['iisFiles']:
        dest=rollback/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'original-iis'/name,dest)
    write(rollback/'transaction.private.json',{'schema':'zhumadian.original.iis.transaction.v1','root':str(NEW/'iis'),'before':plan['iisFiles'],'after':{name:sha(NEW/'iis'/name) for name in plan['iisFiles']},'applied':True,'rolledBack':False,'oldBackendOrDatabaseChanged':False})
    active=read(NEW/POINTERS[0]);active.update(backup=str(rollback),controllerPID=row['controllerPID'],run=row['run']);write(NEW/POINTERS[0],active)
    set_mapping(plan,NEW/'iis');status('IIS_MAPPING_SWITCHED',newControllerPID=row['controllerPID'])
    import install_original_server_ingress as ingress
    tls=[]
    for path in ['/zhumadian/home','/zhumadian/emergency/','/zhumadian/h5/','/zhumadian/project-icon-20261025.svg','/zhumadian/api/jnpf/oauth/getLoginConfig']:
        code,body=ingress.tls_local(details['httpsAddress'],path);need(code==200,'MIGRATED_SERVER_TLS_FAILED')
        if path.endswith('getLoginConfig'):need(json.loads(body).get('code')==200,'MIGRATED_LOGIN_CONFIGURATION_FAILED')
        tls.append({'path':path,'status':code,'bytes':len(body),'bodySHA256':hashlib.sha256(body).hexdigest()})
    blocked=[]
    for path in ['/zhumadian/private/server-configuration.json','/zhumadian/UserData/OriginalServer/installation.json','/zhumadian/runtime/python/python.exe','/zhumadian/release-manifest.json','/zhumadian/payload-manifest.json']:
        code=private_path_head(details['httpsAddress'],path);need(code in (403,404),'PRIVATE_PATH_NOT_BLOCKED');blocked.append({'path':path,'status':code,'method':'HEAD','bodyRead':False})
    latest={'schema':'zhumadian.public-test-update.receipt.v1','updateId':'20261030-R17d-directory-migration','oldReleaseSHA256':plan['oldReleaseSHA256'],'newReleaseSHA256':plan['newReleaseSHA256'],'callbackOverlay':'payload/callback-overlay/20261026-password-identity/manifest.json','callbackOverlaySHA256':plan['callbackOverlaySHA256'],'databaseUUID':row['databaseUUID'],'attempt':str(root),'directoryMigration':True,'ready':True,'controllerPID':row['controllerPID'],'run':row['run'],'serverLocalTLSVerified':True,'userNormalLoginPending':True}
    write(NEW/POINTERS[1],latest);write(NEW/POINTERS[2],dict(latest,completed=True))
    status('NEW_ROOT_READY_EXTERNAL_VERIFICATION_PENDING',ready=True,newReleaseSHA256=plan['newReleaseSHA256'],newApplication=str(NEW),newIISRoot=str(NEW/'iis'),controllerPID=row['controllerPID'],children=row['children'],run=row['run'],databaseUUID=row['databaseUUID'],installationIdentityPreserved=True,eightReadinessReportsSemanticsPreserved=True,otherElevenIISMappingsPreserved=True,serverLocalTLS=tls,blockedPrivatePaths=blocked,oldZdmRemoved=False)

def rollback_stop(plan):
    root=NEW/BACKUP;module=updater(NEW,True);row=read(NEW/'UserData/OriginalServer/current-run.json')
    if module.process_owned(row.get('controllerPID'),NEW,plan['newReleaseSHA256']):module.normal_stop(NEW,plan['newReleaseSHA256'],row)
    need(not [x for x in all_root_images(NEW) if x['ProcessId']!=os.getpid()],'NEW_ROOT_PROCESS_RETAINED_NO_MOVE')
    launch=root/'launch-state.json'
    if launch.exists():
        record=read(launch);matches=[]
        for p in (NEW/'UserData/OriginalServer/runs').glob('j*/receipt.json'):
            value=read(p)
            if value.get('controllerPID')==record['controllerPID']:matches.append(value)
        need(len(matches)==1 and matches[0].get('allOwnedChildrenExited') is True,'EXACT_FAILED_LAUNCH_FULLY_EXITED_REQUIRED')
        receipt=matches[0]
        if receipt.get('exitCodesBeforeJobClose',{}).get('mysql')!=0:
            # Only the pinned new controller records this flag before any database Popen.
            need(receipt.get('databaseStartRequested') is False and set(receipt.get('children',{}))<= {'store'},'CLEAN_DATABASE_SHUTDOWN_REQUIRED_FOR_RECOVERY')
            need(not (Path(receipt['run'])/'mysql-client.private.cnf').exists(),'PRE_DATABASE_START_MARKER_MUST_BE_ABSENT')
            expected=read(root/'protected-after-move.json')['UserData/OriginalServer/database']
            need(metadata_tree(NEW/'UserData/OriginalServer/database')==expected,'UNSTARTED_DATABASE_FILE_IDENTITIES_AND_METADATA_MUST_MATCH')
            need(sha(NEW/'release-manifest.json') in (plan['oldReleaseSHA256'],plan['newReleaseSHA256']),'KNOWN_PINNED_RELEASE_REQUIRED_FOR_PRE_DATABASE_RECOVERY')

    set_mapping(plan,OLDIIS)
    # Validate every replacement and preimage before any restoration write.
    for name,row in plan['replacements'].items():
        path=NEW/name;need(sha(path) in (row['before'],row['after']),'NO_UNRELATED_CODE_OVERWRITE');need(sha(root/'before'/name)==row['before'],'BACKUP_PIN_REQUIRED')
    for name in plan['replacements']:shutil.copyfile(root/'before'/name,NEW/name)
    for name in POINTERS:shutil.copyfile(root/'before'/name,NEW/name)
    status('SAFE_TO_MOVE_BACK',newOwnedProcessesGone=True)

def restart_old(plan):
    root=OLD/BACKUP;module=updater(OLD);need(sha(OLD/'release-manifest.json')==plan['oldReleaseSHA256'],'OLD_RELEASE_RESTORED_REQUIRED')
    row=module.launch(OLD,plan['oldReleaseSHA256'],root);module.health(OLD,row);module.refresh_deployment_owner(OLD,row)
    latest=read(OLD/POINTERS[1]);latest.update(controllerPID=row['controllerPID'],run=row['run'],ready=True);write(OLD/POINTERS[1],latest)
    status('OLD_ROOT_RECOVERED',ready=True,restoredReleaseSHA256=plan['oldReleaseSHA256'],controllerPID=row['controllerPID'])

def verify_new(plan):
    need(not OLD.exists(),'OLD_APPLICATION_REMAINS');need(sha(NEW/'release-manifest.json')==plan['newReleaseSHA256'],'EXACT_MIGRATED_RELEASE_REQUIRED');module=updater(NEW);row=module.owned_ready(NEW,plan['newReleaseSHA256']);module.health(NEW,row)
    current,other=mapping_state(plan['iisMapping']);need(Path(current['physicalPath'])==NEW/'iis' and other==plan['otherMappings'],'NEW_MAPPING_REQUIRED');need(identity(NEW)==read(NEW/BACKUP/'before-metadata.json')['identity'],'PRESERVED_DATA_IDENTITY_REQUIRED')
    image_summary=verify_owned_images(NEW,row,all_root_images(NEW),os.getpid());need(not all_root_images(OLD),'OLD_ROOT_PROCESS_REMAINS')
    status('NEW_ROOT_VERIFIED',ready=True,controllerPID=row['controllerPID'],run=row['run'],sevenRegisteredImagesAndOwnedGatewayWorkerFromNewRoot=True,ownedImageSummary=image_summary)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare-retry','preflight','stop-old','activate-new','rollback-stop','restart-old','verify-new','confirm-clean']);parser.add_argument('--manifest-sha256',required=True);a=parser.parse_args();plan=check_package(a.manifest_sha256)
    try:
        if a.mode=='prepare-retry':prepare_retry(plan)
        elif a.mode=='preflight':
            _,info=validate_old(plan);status('CHECK_ONLY_PASSED',**info,servicesChanged=False)
        elif a.mode=='stop-old':stop_old(plan)
        elif a.mode=='activate-new':apply_new(plan)
        elif a.mode=='rollback-stop':rollback_stop(plan)
        elif a.mode=='restart-old':restart_old(plan)
        elif a.mode=='verify-new':verify_new(plan)
        elif a.mode=='confirm-clean':
            verify_new(plan);need(not OLD.parent.exists(),'OLD_ZDM_NOT_REMOVED');status('COMPLETE',ready=True,oldZdmRemoved=True)
    except Exception as error:
        code=str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else type(error).__name__
        status('STOPPED_'+a.mode.upper().replace('-','_'),ready=False,failureType=type(error).__name__,failureCode=code,manualRecoveryRequired=a.mode!='preflight');raise SystemExit(1)

if __name__=='__main__':main()
