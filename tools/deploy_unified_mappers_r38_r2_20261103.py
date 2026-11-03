from pathlib import Path,PurePosixPath
import hashlib,importlib.util,json,os,re,sys,uuid,zipfile
APP=Path('C:/inetpub/wwwroot/Zhumadian/Application')
ARCHIVE_SHA='1b8a8f169fb1421cdf27dc770ad861b9ffaed6cedb99b21b41c8c5974ab27fd3'
MANIFEST_SHA='7b76dc695252328d0c3e6a891ec9c67fb3038819ea763106f2a1926669732c66'
OLD='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'
NEW='4bca6275e23cfc44d2a18e60e8409345f6231e3b9c7a6975ca9334bbab6805a4'
UPDATE='20261103-R38-unified-original-mappers-plan-exercise-performance-r2'
UPDATER_SHA='f4eae55e6c2b35b4bee67d228bfc8904968ce49d86ea8265436e7e08b2e2964d'
OLD_UPDATER_SHA='67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca'
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

STATIC_EXPECTED={'/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js': {'decodedBytes': 2624898, 'decodedSHA256': '3fda69730a678c07a2c83117eae03796f9fd3ef5d34a5928cc578a8c957806df'}, '/zhumadian/emergency/branding-20261025/assets/js/wf-index-CeoNouGN.js': {'decodedBytes': 2575935, 'decodedSHA256': '812250a395899dee82b166db68c034e1f72417571821acc56ffc657383d104a1'}, '/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css': {'decodedBytes': 869689, 'decodedSHA256': '4672b6a197d7ab95683739a1dd1677b19dd0c117815f4bcfdec4244de5cd1b66'}, '/zhumadian/emergency/branding-20261025/assets/css/index-D0NHlCez.css': {'decodedBytes': 868546, 'decodedSHA256': '675d19500149b12bd203e210c359040c5b48f48b8b3f8818f521f1228692992a'}}

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
    result={'passed':True,'checks':rows,'realGatewayAndLocalIISTLS':True,'businessRecordsOrCredentialsRead':False,'publicExternalOrAuthenticatedTimingAccepted':False}
    m.write_json(root/'server-static-performance-result.json',result)
    print('R38_STATIC_GZIP_CACHE_HTML_AND_DECODED_BYTES_PASSED_GATEWAY_AND_IIS_TLS',flush=True)


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
    need(not explicit or all(isinstance(value,str)and value=='classpath*:/xml/**/*.xml'for value in explicit),'EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN')
    return {'passed':True,'defaultWillApply':not explicit,'explicitOriginalPatternRetained':bool(explicit),'settingValuesOrCredentialsReturned':False}

def main():
    sys.dont_write_bytecode=True
    need(os.name=='nt'and regular(APP).resolve(strict=True)==APP,'EXACT_SERVER')
    mode=sys.argv[1:]
    need(mode in ([],['--check-only'],['--recover-this-update']),'ONLY_SCOPED_MODES')
    root=regular(Path(__file__).absolute().parent)
    installed=regular(APP/'tools/original_public_test_update.py')
    need(sha(installed) in (OLD_UPDATER_SHA,UPDATER_SHA),'EXACT_OLD_OR_THIS_UPDATE_UPDATER')
    source=regular(root/'r38_update_runtime.py')
    need(sha(source)==UPDATER_SHA,'EXACT_FIXED_R38_UPDATE_RUNTIME')
    sys.path.insert(0,str(APP/'tools'))
    spec=importlib.util.spec_from_file_location('fixed_r38_updater',source)
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
    archive=regular(root/'Zhumadian_Unified_Original_Mappers_20261103_R38_R2.zip')
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
    need(old==OLD and checked['newReleaseSHA256']==NEW,'EXACT_R36_BASE')
    candidate_pool=m.candidate_runtime_pool_preflight(APP,stage,checked)
    need(candidate_pool is not None,'EXACT_CANDIDATE_POOL_PREFLIGHT_REQUIRED')
    mapper_input=verify_candidate_mapper_configuration(APP)
    print('R38_ORIGINAL_XML_CONFIGURATION_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)
    print('R38_CANDIDATE_POOL_LAYOUT_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)
    row=m.owned_ready(APP,old);m.health(APP,row)
    if mode==['--check-only']:
        print('R38_PREFLIGHT_PASSED_EXACT_R36_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return
    m.apply_update(APP,stage,MANIFEST_SHA)
    verify_static_gateway_and_iis(m,root,checked)
    print('R38_APPLY_COMPLETED_EXTERNAL_HTTPS_AND_USER_LAYOUT_PENDING',flush=True)
if __name__=='__main__':main()
