"""Preflight and publish an installed original-system test server to the existing IIS app.

No IIS role installation, credential reset, old backend restart, or database migration.
"""
from pathlib import Path
import argparse,datetime,hashlib,http.client,json,os,re,socket,ssl,subprocess,sys,time,uuid,winreg,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_iis_cutover import apply,rollback,regular,atomic

HOST='www.joinlinksmart.com'
IIS_ROOT=Path('C:/FTP_Root/Zhumadian/ZhumadianBusiness_0.8.7_public_1/iis')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def http(port,path):
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
    try:
        c.request('GET',path,headers={'Connection':'close'});r=c.getresponse();b=r.read(4*1024*1024+1);assert len(b)<=4*1024*1024;return r.status,b
    finally:c.close()
def tls_local(address,path):
    context=ssl.create_default_context();raw=socket.create_connection((address,443),timeout=12)
    secure=context.wrap_socket(raw,server_hostname=HOST);c=http.client.HTTPConnection(HOST,timeout=12);c.sock=secure
    try:
        c.request('GET',path,headers={'Host':HOST,'Connection':'close'});r=c.getresponse();b=r.read(4*1024*1024+1);assert len(b)<=4*1024*1024;return r.status,b
    finally:c.close()
def owned_controller(pid,app,pin):
    if type(pid)!=int or pid<=0:return False
    command="Get-CimInstance Win32_Process -Filter 'ProcessId="+str(pid)+"' | Select-Object ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
    if r.returncode or not r.stdout.strip():return False
    row=json.loads(r.stdout.decode('utf-8-sig'))
    return Path(row['ExecutablePath']).resolve()==(app/'runtime/python/python.exe').resolve() and pin in row['CommandLine'] and 'serve_original_server_release.py' in row['CommandLine']
def preflight(app,iis,report):
    assert iis==IIS_ROOT and iis.resolve(strict=True)==iis and app.name=='Application' and len(str(app/'UserData/TianjinOriginalPlatform/runs/j9999/tmp'))<=80,'EXACT_EXISTING_IIS_AND_SHORT_APPLICATION_ROOT_REQUIRED'
    regular(iis);regular(app)
    assert __import__('shutil').disk_usage(app).free>=12*1024**3,'SERVER_TWELVE_GIB_FREE_REQUIRED'
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:net=winreg.QueryValueEx(key,'Release')[0]
    assert net>=378389,'EXISTING_DOTNET_45_OR_LATER_REQUIRED'
    system=Path(os.environ['SystemRoot']);host=system/'System32/inetsrv/config/applicationHost.config'
    tree=ET.parse(host).getroot();modules=tree.findall('./system.webServer/globalModules/add')
    assert any(v.get('name')=='WebSocketModule' for v in modules) and (system/'System32/inetsrv/iiswsock.dll').is_file(),'EXISTING_IIS_WEBSOCKET_ROLE_REQUIRED_NO_ROLE_CHANGES_MADE'
    sites=[]
    for site in tree.findall('./system.applicationHost/sites/site'):
        if any(Path(os.path.expandvars(v.get('physicalPath',''))).absolute()==iis for v in site.findall('./application/virtualDirectory')):sites.append(site)
    assert len(sites)==1,'EXACT_EXISTING_ZHUMADIAN_SITE_MAPPING_REQUIRED'
    addresses=[]
    for binding in sites[0].findall('./bindings/binding'):
        if binding.get('protocol')!='https':continue
        ip,port,host=binding.get('bindingInformation','').rsplit(':',2)
        if port=='443' and host.lower() in ('',HOST):addresses.append('127.0.0.1' if ip in ('','*') else ip.strip('[]'))
    assert addresses,'EXISTING_CANONICAL_HTTPS_BINDING_REQUIRED'
    for address in dict.fromkeys(addresses):
        try:
            code,_=tls_local(address,'/zhumadian/')
            if code in (200,301,302):report.update(dotNetRelease=net,httpsAddress=address,existingSiteTLSVerified=True);return address
        except (OSError,ssl.SSLError):pass
    raise RuntimeError('EXISTING_SITE_TLS_PREFLIGHT_FAILED_NO_FILES_CHANGED')
def refresh_rollback_owner(active_path,expected_bytes,active,ready,app,release_id):
    """Refresh process ownership only; preserve the existing IIS transaction."""
    pid=ready.get('controllerPID');run_value=ready.get('run')
    if (ready.get('releaseId')!=release_id or ready.get('ready') is not True or
        type(pid)!=int or pid<=0 or not isinstance(run_value,str)):
        raise ValueError('OWNED_READY_CONTROLLER_REQUIRED')
    run=Path(run_value);regular(run)
    if (not run.is_dir() or run.resolve()!=run or
        not run.is_relative_to(app/'UserData/OriginalServer/runs') or
        not re.fullmatch(r'j[1-9][0-9]{0,3}',run.name)):
        raise ValueError('OWNED_READY_CONTROLLER_REQUIRED')
    active_path=regular(active_path)
    if active_path.read_bytes()!=expected_bytes:
        raise ValueError('DEPLOYMENT_OWNER_CHANGED')
    updated=dict(active,controllerPID=pid,run=str(run))
    if updated==active:return False
    atomic(active_path,json.dumps(updated,indent=2).encode('utf-8'))
    return True

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--application',type=Path,required=True);parser.add_argument('--release-manifest-sha256',required=True);parser.add_argument('--rollback',action='store_true');a=parser.parse_args()
    app=a.application.resolve(strict=True);manifest=app/'release-manifest.json';assert sha(manifest)==a.release_manifest_sha256
    release=json.loads(manifest.read_bytes());assert release['schema']=='zhumadian.original.server.release.v1'
    for rel,pin in release['controllerFiles'].items():assert sha(regular(app/rel))==pin,'OWN_RELEASE_CONTROLLER_CHANGED'
    data=app/'UserData/OriginalDeployment';regular(data);data.mkdir(parents=True,exist_ok=True)
    if a.rollback:
        active=json.loads((data/'active-deployment.private.json').read_bytes());backup=Path(active['backup'])
        assert backup.resolve()==backup and backup.is_relative_to(data) and active['releaseId']==release['releaseId']
        assert Path(json.loads((backup/'transaction.private.json').read_bytes())['root'])==IIS_ROOT
        result=rollback(backup)
        if owned_controller(active['controllerPID'],app,a.release_manifest_sha256):
            run=Path(active['run']);assert run.resolve()==run and run.is_relative_to(app/'UserData/OriginalServer/runs')
            (run/'stop-requested.txt').write_text('stop\n',encoding='ascii')
        (data/'rollback-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('EXISTING_IIS_ENTRY_RESTORED; NEW_TEST_DATA_RETAINED');return
    report={'schema':'zhumadian.original.server.deployment.v1','releaseId':release['releaseId'],'startedAt':datetime.datetime.now().astimezone().isoformat(),'publicAccepted':False,'oldBackendOrDatabaseChanged':False,'iisFilesChanged':False}
    attempt=data/str(uuid.uuid4());attempt.mkdir();controller=None;controller_log=None
    try:
        address=preflight(app,IIS_ROOT,report)
        xml=ET.fromstring((IIS_ROOT/'web.config').read_bytes());key=next(v.get('value') for v in xml.findall('./appSettings/add') if v.get('key')=='XnbyIngressKey')
        assert re.fullmatch('[0-9a-f]{64}',key) and key!='0'*64,'EXISTING_PRIVATE_INGRESS_KEY_REQUIRED'
        source=app/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs';csc=Path(os.environ['SystemRoot'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        compile_result=subprocess.run([str(csc),'/nologo','/target:library','/out:'+str(attempt/'proxy-preflight.dll'),'/r:System.Web.dll','/r:System.Configuration.dll',str(source)],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        (attempt/'compiler.log').write_bytes(compile_result.stdout+compile_result.stderr);assert compile_result.returncode==0,'SERVER_PROXY_COMPILE_FAILED_NO_ENTRY_CHANGED'
        current=app/'UserData/OriginalServer/current-run.json';ready=None
        if current.exists():
            prior=json.loads(current.read_bytes())
            if prior.get('releaseId')==release['releaseId'] and owned_controller(prior.get('controllerPID'),app,a.release_manifest_sha256):ready=prior
        if ready is None:
            with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',18892))
            controller_log=(attempt/'controller.log').open('wb')
            controller=subprocess.Popen([str(app/'runtime/python/python.exe'),'-I','-B',str(app/'tools/serve_original_server_release.py'),'--application',str(app),'--release-manifest-sha256',a.release_manifest_sha256],cwd=app,stdout=controller_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
            until=time.monotonic()+540
            while time.monotonic()<until:
                assert controller.poll() is None,'NEW_OWN_CONTROLLER_EXITED_NO_ENTRY_CHANGED'
                if current.exists():
                    row=json.loads(current.read_bytes())
                    if row.get('controllerPID')==controller.pid and row.get('releaseId')==release['releaseId'] and row.get('ready'):ready=row;break
                time.sleep(.5)
            assert ready is not None,'NEW_ORIGINAL_SERVER_READY_TIMEOUT_NO_ENTRY_CHANGED'
        report['controllerPID']=ready['controllerPID'];report['newServerReady']=True
        for path in ['/zhumadian/home','/zhumadian/h5/','/zhumadian/api/jnpf/oauth/getLoginConfig']:
            code,body=http(18892,path);assert code==200
            if path.endswith('getLoginConfig'):assert json.loads(body)['code']==200
        expected_icon=sha(app/'deploy/branding/zhumadian-emergency.svg')
        def validate():
            for n in range(5):
                try:
                    code,body=tls_local(address,'/zhumadian/project-icon-20261025.svg')
                    if code==200 and hashlib.sha256(body).hexdigest()==expected_icon:
                        for path in ['/zhumadian/home','/zhumadian/h5/','/zhumadian/api/jnpf/oauth/getLoginConfig']:
                            code,body=tls_local(address,path);assert code==200
                            if path.endswith('getLoginConfig'):assert json.loads(body)['code']==200
                        return True
                except (OSError,ValueError,AssertionError):pass
                time.sleep(1)
            return False
        template=(app/'deploy/iis_original/web.config.template').read_text('utf-8');assert template.count('REPLACE_WITH_PRIVATE_64_HEX_KEY')==1
        new={'App_Code/XnbyReferenceProxy.cs':source.read_bytes(),'web.config':template.replace('REPLACE_WITH_PRIVATE_64_HEX_KEY',key).encode('utf-8')}
        active_path=data/'active-deployment.private.json'
        if active_path.exists():
            active_snapshot=regular(active_path).read_bytes();active=json.loads(active_snapshot);backup=Path(active['backup'])
            assert backup.resolve()==backup and backup.is_relative_to(data),'OWN_ACTIVE_DEPLOYMENT_BACKUP_REQUIRED'
            transaction=json.loads((backup/'transaction.private.json').read_bytes())
            same=active.get('releaseId')==release['releaseId'] and transaction.get('applied') and not transaction.get('rolledBack') and all(sha(IIS_ROOT/rel)==hashlib.sha256(body).hexdigest() for rel,body in new.items())
            if same and validate():
                refreshed=refresh_rollback_owner(active_path,active_snapshot,active,ready,app,release['releaseId'])
                report.update(alreadyApplied=True,rollbackOwnerRefreshed=refreshed,serverLocalTLSValidationPassed=True,externalPublicValidationPending=True)
                print('OWN_RELEASE_ALREADY_RUNNING; NO_IIS_FILES_REWRITTEN',flush=True);return
        backup=attempt/'iis-backup';result=apply(IIS_ROOT,backup,new,validate);assert result['applied']
        report.update(iisFilesChanged=True,serverLocalTLSValidationPassed=True,externalPublicValidationPending=True,originalUserLoginVerified=False,webSocketBusinessFlowVerified=False)
        (data/'active-deployment.private.json').write_text(json.dumps({'releaseId':release['releaseId'],'backup':str(backup),'controllerPID':ready['controllerPID'],'run':ready['run']},indent=2),encoding='utf-8')
        print('ORIGINAL_TEST_SERVER_PUBLISHED; EXTERNAL_PC_H5_AND_USER_LOGIN_VALIDATION_PENDING',flush=True)
    except BaseException as error:
        report['failureType']=type(error).__name__;report['failureMessage']=str(error) if isinstance(error,AssertionError) else type(error).__name__
        if controller is not None and controller.poll() is None:
            if (app/'UserData/OriginalServer/current-run.json').exists():
                row=json.loads((app/'UserData/OriginalServer/current-run.json').read_bytes())
                if row.get('controllerPID')==controller.pid:(Path(row['run'])/'stop-requested.txt').write_text('stop\n',encoding='ascii')
            try:controller.wait(timeout=120)
            except subprocess.TimeoutExpired:report['newControllerForcedStop']=True;controller.terminate();controller.wait(timeout=15)
        raise
    finally:
        report['endedAt']=datetime.datetime.now().astimezone().isoformat();(attempt/'deployment-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        if controller_log is not None:controller_log.close()

if __name__=='__main__':main()
