from pathlib import Path,PurePosixPath
import hashlib,importlib.util,json,os,re,sys,uuid,zipfile
APP=Path('C:/inetpub/wwwroot/Zhumadian/Application')
ARCHIVE_SHA='a309e661cd4b46525faa0f54e20c14efcfe7944d78cb0325f0cb3d226acd6389'
ARCHIVE_NAME='Zhumadian_Original_Bootstrap_20261104_R45.zip'
NEW='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
UPDATER_SHA='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
BASES={'daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853': {'label': 'r36', 'updateId': '20261104-r45-original-bootstrap-from-r36', 'manifestSHA256': '4366043e640634b72b2fb8f59c53335012bf5bff8c75f4a3bd8563829e002d84', 'oldUpdaterSHA256': '67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca'}, '909b64aa1315b8764b169c9874b8f52f903268b59c67adbf7b3799e85e29448c': {'label': 'r37', 'updateId': '20261104-r45-original-bootstrap-from-r37', 'manifestSHA256': '8718fca7fcad4ce225c71a45e9c34f513d1447880ac22396a76a0b596669e98b', 'oldUpdaterSHA256': '52daac9f348be6622592920240794a1ba701d46683fa6b7c3e0cb34da47fcf62'}}
STATIC_EXPECTED={'/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js': {'decodedBytes': 2624898, 'decodedSHA256': '3fda69730a678c07a2c83117eae03796f9fd3ef5d34a5928cc578a8c957806df'}, '/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css': {'decodedBytes': 869689, 'decodedSHA256': '4672b6a197d7ab95683739a1dd1677b19dd0c117815f4bcfdec4244de5cd1b66'}, '/zhumadian/branding-20261025/assets/css/xnby-workplace-period-736f7b07dd2c.css': {'decodedBytes': 1915, 'decodedSHA256': '736f7b07dd2cebca59b613be97ac0288bde3ca01b54416d7a680f0ce97da68a3'}, '/zhumadian/emergency/branding-20261025/assets/js/wf-index-C_ZP3Pto.js': {'decodedBytes': 1320116, 'decodedSHA256': '8a7dc8a8e80dae2c8001d39676e33749c28bfa49b99f80379f2be94e9302a11f'}, '/zhumadian/emergency/branding-20261025/assets/css/index-CRXrVYsv.css': {'decodedBytes': 867418, 'decodedSHA256': '4b34f117d0aaf505554964a852715bd15f8bcc2533abce3856ef8c1ae18380fb'}}

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

def validate_static_response(path,encoding,status,headers,body):
    import gzip,io
    need(status==200 and len(body)<=4*1024*1024,'STATIC_HTTP_STATUS_OR_BOUND')
    need(headers.get('cache-control')=='public, max-age=31536000, immutable','STATIC_HASH_CACHE_POLICY')
    expected=STATIC_EXPECTED[path]
    if encoding=='gzip':
        need(headers.get('content-encoding')=='gzip' and 'accept-encoding' in [v.strip().lower()for v in headers.get('vary','').split(',')],'STATIC_GZIP_AND_VARY')
        with gzip.GzipFile(fileobj=io.BytesIO(body))as stream:decoded=stream.read(4*1024*1024+1)
    else:
        need(not headers.get('content-encoding'),'STATIC_EXPLICIT_ZERO_MUST_REMAIN_IDENTITY');decoded=body
    need(len(decoded)==expected['decodedBytes']and hashlib.sha256(decoded).hexdigest()==expected['decodedSHA256'],'STATIC_DECODED_CONTENT_IDENTITY')
    return {'status':status,'wireBytes':len(body),'decodedBytes':len(decoded),'gzip':encoding=='gzip','hashCacheVerified':True,'decodedContentMatched':True}

def verify_static_gateway_and_iis(m,root,checked):
    import http.client,socket,ssl
    # A new exact proxy pin is used only after apply_update has completed normally.
    changed=dict(checked);changed['iisProxySHA256']=m.R37_STATIC_CONTRACT['files']['iis/App_Code/XnbyReferenceProxy.cs']['sha256']
    ingress,address=m.ingress_preflight(APP,changed,{})
    def fetch(channel,path,accept):
        if channel=='gateway':c=http.client.HTTPConnection('127.0.0.1',18892,timeout=20)
        else:
            secure=ssl.create_default_context().wrap_socket(socket.create_connection((address,443),timeout=20),server_hostname='www.joinlinksmart.com')
            c=http.client.HTTPConnection('www.joinlinksmart.com',timeout=20);c.sock=secure
        try:
            c.request('GET',path,headers={'Host':'www.joinlinksmart.com','Accept-Encoding':accept,'Connection':'close'});r=c.getresponse();b=r.read(4*1024*1024+1)
            need(len(b)<=4*1024*1024,'STATIC_RESPONSE_BOUND')
            return r.status,{k.lower():v for k,v in r.getheaders()},b
        finally:c.close()
    rows=[]
    for channel in ['gateway','iis-tls']:
        for path in STATIC_EXPECTED:
            code,headers,body=fetch(channel,path,'gzip');r=validate_static_response(path,'gzip',code,headers,body);r.update(channel=channel,resource=path);rows.append(r)
        path=next(iter(STATIC_EXPECTED));code,headers,body=fetch(channel,path,'gzip;q=0, *;q=1');r=validate_static_response(path,'identity',code,headers,body);r.update(channel=channel,explicitGzipZero=True);rows.append(r)
        for path in ['/zhumadian/home','/zhumadian/emergency/home/index']:
            code,headers,body=fetch(channel,path,'identity');need(code==200 and 'no-store'in headers.get('cache-control',''),'HTML_ENTRY_MUST_NOT_BE_LONG_CACHED');rows.append({'channel':channel,'resource':path,'status':code,'htmlNoStoreVerified':True})
            if path=='/zhumadian/home':need(b'/zhumadian/branding-20261025/assets/css/xnby-workplace-period-736f7b07dd2c.css' in body and b'data-xnby-workplace-period="20261104-r564"' in body,'EXACT_WORKPLACE_STYLE_LINK_REQUIRED')
    result={'passed':True,'checks':rows,'realGatewayAndLocalIISTLS':True,'businessRecordsOrCredentialsRead':False,'publicExternalOrAuthenticatedTimingAccepted':False}
    m.write_json(root/'server-static-performance-result.json',result)
    print('R45_STATIC_GZIP_CACHE_HTML_AND_DECODED_BYTES_PASSED_GATEWAY_AND_IIS_TLS',flush=True)

def verify_candidate_mapper_configuration(app):
    # Read only in memory; never return setting values or credentials.
    cfg=json.loads(regular(app/'private/server-configuration.json').read_bytes())
    business=cfg['configuration']['business'];need(isinstance(business,dict),'MAPPER_CONFIGURATION_SHAPE_REQUIRED')
    def mapper_key(key):return re.fullmatch(r'mybatisplusmapperlocations(?:\[[0-9]+\])?',re.sub(r'[-_.]','',key).lower())is not None
    explicit=[value for key,value in business.items()if mapper_key(key)]
    explicit.extend(value for key,value in os.environ.items()if mapper_key(key))
    for argument in cfg.get('businessArguments',[]):
        if argument.startswith('-D')or argument.startswith('--'):
            key,separator,value=argument[2:].partition('=')
            if mapper_key(key):need(separator=='=','EXPLICIT_MAPPER_ARGUMENT_VALUE_REQUIRED');explicit.append(value)
    need(not explicit or all(isinstance(value,str)and value in ('classpath*:/xml/**/*.xml','classpath*:xml/**/*Mapper.xml')for value in explicit),'EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN')
    return {'passed':True,'defaultWillApply':not explicit,'explicitOriginalPatternRetained':bool(explicit),'settingValuesOrCredentialsReturned':False}


def select_installed_base(app):
    installed=sha(regular(app/'release-manifest.json'))
    need(installed in BASES,'ONLY_EXACT_R36_OR_R37_BASE')
    base=BASES[installed]
    need(sha(regular(app/'tools/original_public_test_update.py'))==base['oldUpdaterSHA256'],'EXACT_SELECTED_BASE_UPDATER_REQUIRED')
    return installed,base

def recovery_guard(report):
    old=report.get('oldReleaseSHA256');need(old in BASES,'ONLY_THIS_OLD_RELEASE')
    base=BASES[old]
    need(report.get('updateId')==base['updateId'],'ONLY_THIS_UPDATE')
    need(report.get('newReleaseSHA256')==NEW,'ONLY_THIS_NEW_RELEASE')
    attempt=regular(Path(report['attempt']).absolute())
    need(attempt.parent==APP/'UserData/OriginalPublicUpdates'and re.fullmatch('[0-9a-f]{32}',attempt.name)is not None,'ONLY_OWN_BACKUP_PARENT_AND_ID')
    return base

def validate_archive(z,base):
    entries=z.infolist();names=[v.filename for v in entries]
    need(len(entries)<=512 and len(names)==len(set(names))and sum(v.file_size for v in entries)<=40*1024**2,'CLOSED_TRANSPORT_BOUNDS')
    need(all(not v.is_dir()and not(v.flag_bits&1)and ((v.external_attr>>16)&0o170000)!=0o120000 for v in entries),'REGULAR_UNENCRYPTED_MEMBERS')
    for info in entries:
        rel=PurePosixPath(info.filename)
        need(str(rel)==info.filename and not rel.is_absolute()and all(p not in ('.','..')and not re.search(r'[\\:\x00-\x1f]',p)and not p.endswith((' ','.'))for p in rel.parts),'EXACT_RELATIVE_MEMBER')
    plans={}
    for old,pin in BASES.items():
        member='variants/'+pin['label']+'/update-manifest.json';raw=z.read(member)
        need(hashlib.sha256(raw).hexdigest()==pin['manifestSHA256'],'FIXED_VARIANT_MANIFEST')
        plan=json.loads(raw)
        need(plan['updateId']==pin['updateId']and plan['newReleaseSHA256']==NEW and set(plan['acceptedOldReleases'])=={old},'FIXED_SINGLE_BASE_UPDATE_IDENTITY')
        need(plan['targetApplication']==APP.as_posix()and plan['gatewayPort']==18892,'EXACT_VARIANT_TARGET')
        plans[pin['label']]=plan
    selected=plans[base['label']]
    need(all(v['files']==selected['files']and v['removedFrontendFiles']==selected['removedFrontendFiles']for v in plans.values()),'SAME_FINAL_PAYLOAD_FOR_BOTH_BASES')
    need(len(selected['files'])==196 and len(selected['removedFrontendFiles'])==181,'EXACT_CHANGE_SET_SIZE')
    need(set(names)=={'web.config'}|{'variants/'+v['label']+'/update-manifest.json'for v in BASES.values()}|{'payload/'+v for v in selected['files']},'EXACT_CLOSED_MEMBERS')
    for name,pin in selected['files'].items():
        raw=z.read('payload/'+name)
        need(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'],'EXACT_ARCHIVED_PAYLOAD_PIN:'+name)
    return selected

def extract_selected_archive(archive,stage,base):
    with zipfile.ZipFile(archive)as z:
        plan=validate_archive(z,base)
        stage=regular(stage);need(not stage.exists(),'NEW_OWN_STAGE_REQUIRED');stage.mkdir(parents=True)
        # Deny HTTP access before creating any executable or manifest in this directory.
        for origin,destination in [('web.config','web.config'),('variants/'+base['label']+'/update-manifest.json','update-manifest.json')]+[('payload/'+n,'payload/'+n)for n in plan['files']]:
            dest=regular(stage.joinpath(*PurePosixPath(destination).parts));dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb')as target,z.open(origin)as stream:
                while True:
                    chunk=stream.read(65536)
                    if not chunk:break
                    target.write(chunk)
    need(sha(stage/'update-manifest.json')==base['manifestSHA256'],'EXACT_SELECTED_STAGE_MANIFEST')
    return plan


def write_scoped_result(root,phase,base,old,budget=None):
    output=regular(root/'r45-scoped-result.json');schema='xnby.r45.scoped-deployment-result.v1'
    if output.exists():
        need(output.stat().st_size<=64*1024,'BOUNDED_OWN_SCOPED_RESULT_REQUIRED')
        previous=json.loads(output.read_bytes())
        need(previous.get('schema')==schema and previous.get('newReleaseSHA256')==NEW,'FOREIGN_SCOPED_RESULT_REFUSE_OVERWRITE')
    result={'schema':schema,'phase':phase,'selectedBase':base['label'],'updateId':base['updateId'],
        'oldReleaseSHA256':old,'newReleaseSHA256':NEW,'updaterSHA256':UPDATER_SHA,
        'serverLocalGatewayAndIISTLSStaticPassed':phase=='deploy-complete','externalHTTPSAndLoggedInTimingAccepted':False,
        'credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded':False,'fullCloneReady':False}
    if budget is not None:
        result['mysqlMaxConnections']=budget['budget']['mysqlMaxConnections']
        result['datasourceCount']=len(budget['budget']['datasources'])
    raw=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode();need(len(raw)<=4096,'BOUNDED_SCOPED_RESULT')
    temporary=regular(root/('r45-result-'+uuid.uuid4().hex+'.tmp'))
    with temporary.open('xb')as f:f.write(raw)
    os.replace(temporary,output)

def main():
    sys.dont_write_bytecode=True
    need(os.name=='nt'and regular(APP).resolve(strict=True)==APP,'EXACT_SERVER')
    mode=sys.argv[1:];need(mode in ([],['--check-only'],['--recover-this-update']),'ONLY_SCOPED_MODES')
    root=regular(Path(__file__).absolute().parent)
    source=regular(root/'r45_update_runtime.py');need(sha(source)==UPDATER_SHA,'EXACT_FIXED_R45_UPDATE_RUNTIME')
    installed=regular(APP/'tools/original_public_test_update.py')
    need(sha(installed) in {UPDATER_SHA,*[v['oldUpdaterSHA256']for v in BASES.values()]},'EXACT_OLD_OR_THIS_UPDATE_UPDATER')
    sys.path.insert(0,str(APP/'tools'))
    spec=importlib.util.spec_from_file_location('fixed_r45_updater',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if mode==['--recover-this-update']:
        pending_path=regular(APP/'UserData/OriginalPublicUpdates/pending.json')
        pending=m.read(pending_path)if pending_path.exists()else{}
        if pending.get('updateId')in {v['updateId']for v in BASES.values()}and pending.get('failureType')and not pending.get('ready'):
            recovery_guard(pending);m.recover_pending(APP)
        else:
            latest=m.read(regular(APP/'UserData/OriginalPublicUpdates/latest.json'));recovery_guard(latest)
            need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_ROLLBACK');m.rollback_latest(APP)
        return
    old,base=select_installed_base(APP)
    archive=regular(root/ARCHIVE_NAME);need(sha(archive)==ARCHIVE_SHA,'EXACT_FIXED_ARCHIVE')
    stage=regular(APP/'UserData/OriginalPublicUpdates/staging'/uuid.uuid4().hex)
    extract_selected_archive(archive,stage,base)
    checked,old_checked,changes=m.load_bundle(APP,stage,base['manifestSHA256'])
    need(old_checked==old and checked['newReleaseSHA256']==NEW,'EXACT_SELECTED_BASE_RECHECK')
    candidate_pool=m.candidate_runtime_pool_preflight(APP,stage,checked);need(candidate_pool is not None,'EXACT_CANDIDATE_POOL_PREFLIGHT_REQUIRED')
    verify_candidate_mapper_configuration(APP)
    print('R45_SELECTED_'+base['label'].upper()+'_XML_AND_POOL_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)
    row=m.owned_ready(APP,old);m.health(APP,row)
    if mode==['--check-only']:
        write_scoped_result(root,'preflight-passed',base,old,candidate_pool)
        print('R45_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return
    write_scoped_result(root,'deploy-started',base,old,candidate_pool)
    m.apply_update(APP,stage,base['manifestSHA256'])
    latest_path=regular(APP/'UserData/OriginalPublicUpdates/latest.json')
    applied_record_raw=latest_path.read_bytes();applied_record=json.loads(applied_record_raw)
    recovery_guard(applied_record)
    need(applied_record.get('ready')is True and applied_record['updateId']==base['updateId']and applied_record['oldReleaseSHA256']==old,'EXACT_THIS_APPLY_RECORD_REQUIRED')
    applied_record_sha=hashlib.sha256(applied_record_raw).hexdigest()
    try:verify_static_gateway_and_iis(m,root,checked)
    except BaseException:
        need(sha(latest_path)==applied_record_sha,'POSTCHECK_UPDATE_RECORD_DRIFT_REFUSE_ROLLBACK')
        latest=m.read(latest_path);recovery_guard(latest)
        need(latest['updateId']==base['updateId']and latest['oldReleaseSHA256']==old,'ONLY_THIS_SELECTED_BASE_POSTCHECK_ROLLBACK')
        need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_POSTCHECK_ROLLBACK')
        m.rollback_latest(APP)
        write_scoped_result(root,'postcheck-failed-rolled-back',base,old,candidate_pool)
        raise
    write_scoped_result(root,'deploy-complete',base,old,candidate_pool)
    print('R45_APPLY_COMPLETED_EXTERNAL_HTTPS_AND_USER_LAYOUT_PENDING',flush=True)
if __name__=='__main__':main()
