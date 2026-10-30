"""Run one explicitly installed original-system test server on owned loopback ports.

Persistent by default; an optional QA duration applies only after real ready.
All data belongs to this installation. No source environment or automatic retry.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,msvcrt,os,re,secrets,shutil,socket,subprocess,sys,threading,time,uuid
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_server_release_parameters import materialize, runtime_temporary_path
from original_callback_overlay import load_callback_overlay, install_callback_overlay
from original_server_windows_job import OwnedWindowsJob
from original_object_store_runtime import signed_owned_request,stop_owned_provider,request_owned_http
from original_platform_files import OwnedPlatformFiles
from portable_original_admin_frontend import load as load_admin
from readonly_original_static_archive import ArchiveServer
from prepare_original_frontend_gateway import prepare

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def regular_tree_path(path,root):
    path=Path(path);root=Path(root)
    if '..' in path.parts or not path.absolute().is_relative_to(root.absolute()):raise ValueError('OWNED_INSTALLATION_PATH_REQUIRED')
    for q in [root,*reversed(path.relative_to(root).parents),path]:
        q=q if q.is_absolute() else root/q
        if q.exists() and (q.is_symlink() or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('INSTALLATION_REDIRECTION_REJECTED')

def port():
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',0));return s.getsockname()[1]

def resp(stream,*words):
    values=[str(v).encode('utf-8') for v in words]
    stream.write(b'*'+str(len(values)).encode()+b'\r\n'+b''.join(b'$'+str(len(v)).encode()+b'\r\n'+v+b'\r\n' for v in values));stream.flush()
    line=stream.readline(4096)
    if line.startswith(b'+'):return line[1:-2].decode('ascii')
    if line.startswith(b':'):return int(line[1:-2])
    raise RuntimeError('OWN_REDIS_COMMAND_FAILED')

class Child:
    def __init__(self,name,command,folder,env):
        self.name=name;self.folder=folder;self.tail=bytearray();self.lock=threading.Lock();self.job=None
        self.process=subprocess.Popen(command,cwd=folder,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        try:self.job=OwnedWindowsJob(self.process)
        except Exception:
            if self.process.poll() is None:self.process.kill()
            self.process.wait(timeout=5);raise
        self.thread=threading.Thread(target=self.drain,daemon=True,name='owned-'+name+'-log');self.thread.start()
    def drain(self):
        with self.process.stdout,(self.folder/(self.name+'.private.log')).open('wb') as out:
            while True:
                block=os.read(self.process.stdout.fileno(),65536)
                if not block:return
                with self.lock:
                    self.tail.extend(block);del self.tail[:-1024*1024]
                    out.seek(0);out.write(self.tail);out.truncate();out.flush()
    def contains(self,text):
        with self.lock:return text in self.tail
    def close_job(self):
        if self.job:self.job.close();self.job=None

def wait_for(predicate,children,timeout,label):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if any(v.process.poll() is not None for v in children):raise RuntimeError('OWN_COMPONENT_EXITED:'+label)
        if predicate():return
        time.sleep(.2)
    raise RuntimeError('OWN_COMPONENT_TIMEOUT:'+label)

def ensure_object_store_ready(api_port, access, secret, buckets, children, state, timeout=60):
    """Require real API readiness and every bucket; retry only initialization 503.

    Diagnostics contain status codes and counters, never bucket names or secrets.
    A live process alone is insufficient during an existing drive's initialization.
    """
    ordered=sorted(set(buckets))
    if not ordered or any(not isinstance(b,str) or not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',b) for b in ordered):
        raise ValueError('OWN_OBJECT_STORE_BUCKET_FORMAT_REQUIRED')
    progress={'healthMode':'live-ready-and-verified-buckets','bucketCount':len(ordered),'attempts':0,'ready':False,'transientStatuses':[]}
    state['objectStoreInitialization']=progress
    until=time.monotonic()+timeout
    def checked(status,phase,allowed):
        progress['lastPhase']=phase;progress['lastHTTPStatus']=status
        if status==503:
            if 503 not in progress['transientStatuses']:progress['transientStatuses'].append(503)
            return False
        if status not in allowed:raise RuntimeError('OWN_OBJECT_STORE_HTTP_STATUS:'+phase+':'+str(status))
        return True
    while time.monotonic()<until:
        if any(c.process.poll() is not None for c in children):raise RuntimeError('OWN_COMPONENT_EXITED:object-store-initialization')
        progress['attempts']+=1
        try:
            ready=True
            for path,phase in [('/minio/health/live','live'),('/minio/health/ready','ready')]:
                if not checked(request_owned_http(api_port,'GET',path)[0],phase,{200}):ready=False;break
            if ready:
                for bucket in ordered:
                    status,_=signed_owned_request(api_port,access,secret,'HEAD','/'+bucket)
                    if not checked(status,'bucket-head',{200,404}):ready=False;break
                    if status==404:
                        created,_=signed_owned_request(api_port,access,secret,'PUT','/'+bucket)
                        if not checked(created,'bucket-create',{200,204,409}):ready=False;break
                        # A concurrent/already-created response never counts as success by itself.
                        status,_=signed_owned_request(api_port,access,secret,'HEAD','/'+bucket)
                        if not checked(status,'created-bucket-head',{200,404}):ready=False;break
                        if status!=200:ready=False;break
            if ready:progress['ready']=True;return
        except OSError as error:progress['lastTransportFailureType']=type(error).__name__
        time.sleep(.2)
    raise RuntimeError('OWN_COMPONENT_TIMEOUT:object-store-api-readiness')

def stop_object_store_when_available(api_port, access, secret, timeout=20):
    until=time.monotonic()+timeout;attempts=0
    while True:
        attempts+=1
        result=stop_owned_provider(api_port,access,secret)
        result['attempts']=attempts
        if result['status']!=503 or time.monotonic()>=until:return result
        time.sleep(.2)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--application',type=Path,required=True);ap.add_argument('--release-manifest-sha256',required=True)
    ap.add_argument('--gateway-port',type=int,default=18892);ap.add_argument('--qa-seconds',type=int)
    ap.add_argument('--callback-overlay',type=Path);ap.add_argument('--callback-overlay-sha256')
    a=ap.parse_args();app=a.application.absolute();assert app.resolve(strict=True)==app and app.name=='Application'
    assert 1024<=a.gateway_port<=65535 and (a.qa_seconds is None or 1<=a.qa_seconds<=600)
    manifest_path=app/'release-manifest.json';assert sha(manifest_path)==a.release_manifest_sha256
    release=json.loads(manifest_path.read_bytes());assert release['schema']=='zhumadian.original.server.release.v1'
    for rel,pin in release['controllerFiles'].items():
        q=app/rel;regular_tree_path(q,app);assert sha(q)==pin,'CONTROLLER_FILE_CHANGED'
    payload_path=app/'payload-manifest.json';assert sha(payload_path)==release['payloadManifestSHA256']
    payload=json.loads(payload_path.read_bytes());assert payload['releaseId']==release['releaseId']
    config=json.loads((app/'private/server-configuration.json').read_bytes());assert config['schema']=='zhumadian.original.server.configuration.v1'
    if (a.callback_overlay is None)!=(a.callback_overlay_sha256 is None):raise ValueError('CALLBACK_OVERLAY_AND_PIN_REQUIRED')
    callback=load_callback_overlay(app,a.callback_overlay,a.callback_overlay_sha256) if a.callback_overlay is not None else None
    data=app/'UserData/OriginalServer';regular_tree_path(data,app);data.mkdir(parents=True,exist_ok=True)
    lock=(data/'server-owner.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    # Refuse an occupied ingress before starting any component or adopting data.
    with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',a.gateway_port))
    identity_path=data/'installation.json';installed=identity_path.exists()
    identity=json.loads(identity_path.read_bytes()) if installed else {'schema':'zhumadian.original.server.data.v1','ownerId':str(uuid.uuid4()),'releaseId':release['releaseId'],'databaseUUID':str(uuid.uuid4())}
    assert identity['schema']=='zhumadian.original.server.data.v1' and identity['releaseId']==release['releaseId']
    print('VERIFY_IMMUTABLE_INSTALLED_PAYLOAD',flush=True)
    for rel,row in payload['files'].items():
        q=app/rel;regular_tree_path(q,app)
        if installed and rel.startswith('seed/mysql/'):continue
        assert q.stat().st_size==row['bytes'] and sha(q)==row['sha256'],'INSTALLED_PAYLOAD_CHANGED:'+rel
    database=data/'database';database.mkdir(exist_ok=True)
    if not installed:
        assert not (database/'data').exists();os.replace(app/'seed/mysql',database/'data')
        (database/'data/auto.cnf').write_text('[auto]\nserver-uuid='+identity['databaseUUID']+'\n',encoding='ascii')
        (data/'store-data').mkdir();(data/'store-credentials.private.json').write_text(json.dumps({'accessKey':'own-'+secrets.token_hex(8),'secretKey':secrets.token_hex(24)}),encoding='ascii')
        identity_path.write_text(json.dumps(identity,indent=2),encoding='ascii')
    assert (database/'data/auto.cnf').read_text('ascii').strip().endswith(identity['databaseUUID'])
    own=json.loads((data/'store-credentials.private.json').read_bytes())
    runs=data/'runs';runs.mkdir(exist_ok=True)
    number=next((n for n in range(1,10000) if not (runs/('j'+str(n))).exists() and not (app/'UserData/TianjinOriginalPlatform/runs'/('j'+str(n))).exists()),None);assert number
    run=runs/('j'+str(number));run.mkdir();business=run/'b';business.mkdir();owner=str(uuid.uuid4())
    pf=OwnedPlatformFiles(app,'own-j'+str(number)).acquire();platform=pf.run_root
    for target,role in [(platform,'platform'),(business,'business')]:
        shutil.copytree(app/('payload/'+role+'/run-template'),target,dirs_exist_ok=True)
        for name in ['tmp','home','logs','files']:(target/name).mkdir(exist_ok=True)
        (target/'server-owner.properties').write_text('schema=zhumadian.original.server.owner.v1\nownerId='+owner+'\n',encoding='ascii')
    if callback is not None:install_callback_overlay(callback,platform,business)
    (run/'tmp').mkdir();(run/'certs').mkdir();(run/'profile').mkdir();(run/'appdata').mkdir();(run/'redis-data').mkdir()
    ports=[]
    while len(ports)<(5 if callback is not None else 4):
        value=port()
        if value not in ports and value!=a.gateway_port:ports.append(value)
    dbport,redisport,storeport,consoleport=ports[:4]
    callback_business_port=ports[4] if callback is not None else None
    redis_password=secrets.token_urlsafe(32);root_password=config['seedRootPassword']
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS')}
    env.update(PATH=str(Path(os.environ['SystemRoot'])/'System32'),TMP=str(run/'tmp'),TEMP=str(run/'tmp'),USERPROFILE=str(run/'profile'),APPDATA=str(run/'appdata'),LOCALAPPDATA=str(run/'appdata'))
    children=[];admin=None;admin_thread=None;gateway=None;state={'schema':'zhumadian.original.server.run.v1','releaseId':release['releaseId'],'ownerId':owner,'controllerPID':os.getpid(),'run':str(run),'platformRun':str(platform),'gatewayPort':a.gateway_port,'startedAt':datetime.datetime.now().astimezone().isoformat(),'persistent':a.qa_seconds is None,'publicAccepted':False,'ready':False,'databaseStartRequested':False,'children':{}}
    def start(name,cmd,folder,extra=None):
        child=Child(name,cmd,folder,dict(env,**(extra or {})));children.append(child);state['children'][name]=child.process.pid;return child
    def stop_wait(child,seconds):
        if child is not None:
            try:child.process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:state.setdefault('stopTimeouts',[]).append(child.name)
    db=redis=store=pchild=bchild=None
    try:
        store=start('store',[str(app/'runtime/minio/minio.exe'),'--quiet','--certs-dir',str(run/'certs'),'server','--address','127.0.0.1:'+str(storeport),'--console-address','127.0.0.1:'+str(consoleport),str(data/'store-data')],run,{'MINIO_ROOT_USER':own['accessKey'],'MINIO_ROOT_PASSWORD':own['secretKey'],'MINIO_BROWSER':'off','MINIO_UPDATE':'off','MINIO_CALLHOME_ENABLE':'off','GOMAXPROCS':'2'})
        buckets={config['configuration']['business']['minio.bucketName'],config['configuration']['platform']['config.file-storage.minio[0].bucket-name']}
        ensure_object_store_ready(storeport,own['accessKey'],own['secretKey'],buckets,children,state)
        state['databaseStartRequested']=True
        mh=app/'runtime/mysql'
        db=start('mysql',[str(mh/'bin/mysqld.exe'),'--no-defaults','--no-monitor','--basedir='+str(mh),'--datadir='+str(database/'data'),'--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL','--super-read-only=OFF','--read-only=OFF','--transaction-read-only=OFF','--bind-address=127.0.0.1','--port='+str(dbport),'--pid-file='+str(run/'mysqld.pid'),'--console','--max-connections=24','--skip-slave-start'],run)
        escaped=root_password.replace('\\','\\\\').replace('"','\\"')
        (run/'mysql-client.private.cnf').write_text('[client]\nhost=127.0.0.1\nport='+str(dbport)+'\nuser=root\npassword="'+escaped+'"\n',encoding='ascii')
        wait_for(lambda:db.contains(b'ready for connections'),children,60,'mysql')
        assert int((run/'mysqld.pid').read_text('ascii').strip())==db.process.pid
        rc=run/'redis.private.conf';rc.write_text('\n'.join(['bind 127.0.0.1','port '+str(redisport),'protected-mode yes','requirepass '+redis_password,'maxmemory 96mb','maxmemory-policy noeviction','persistence-available no','dir "'+(run/'redis-data').as_posix()+'"','logfile ""','loglevel notice'])+'\n',encoding='ascii')
        redis=start('redis',[str(app/'runtime/redis/redis-server.exe'),str(rc)],run)
        def cache_command(*words):
            with socket.create_connection(('127.0.0.1',redisport),timeout=2) as sock,sock.makefile('rwb') as stream:
                assert resp(stream,'AUTH',redis_password)=='OK';return resp(stream,*words)
        def cache_ready():
            try:return cache_command('PING')=='PONG'
            except OSError:return False
        wait_for(cache_ready,children,20,'redis');assert cache_command('CONFIG','SET','save','')=='OK'
        shutil.copyfile(database/'data/public_key.pem',platform/'own-mysql-public-key.pem')
        parameters=dict(application=app,platform_run=platform,business_run=business,platform_data_owner=pf.identity['ownerId'],run_owner=owner,database_uuid=identity['databaseUUID'],database_port=dbport,redis_port=redisport,object_port=storeport,database_password=root_password,redis_password=redis_password,object_access=own['accessKey'],object_secret=own['secretKey'])
        if callback is not None:parameters.update(business_port=callback_business_port,callback_pins=callback['pins'])
        prepared=materialize(config,side='platform',**parameters);(platform/'application.properties').write_bytes(prepared['properties'])
        if callback is not None:(platform/'callback-route-pins.json').write_bytes(prepared['callbackRoutingPinsBytes'])
        platform_tmp=runtime_temporary_path(app,platform,'platform');regular_tree_path(platform_tmp,app);platform_tmp.mkdir(parents=True,exist_ok=True)
        pchild=start('platform',[str(app/'runtime/jdk8/bin/java.exe'),*prepared['arguments']],platform,{'TMP':str(platform_tmp),'TEMP':str(platform_tmp)})
        wait_for(lambda:(platform/'server-ready.txt').is_file(),children,180,'platform')
        if callback is not None:wait_for(lambda:(platform/'callback-routes-ready.properties').is_file(),children,15,'platform-callback-adapter')
        pp=int((platform/'server-http-port.txt').read_text('ascii'))
        observed=dict(s.split('=',1) for s in (platform/'actual-writable-datasource.properties').read_text('ascii').splitlines() if '=' in s and not s.startswith(('#','!')))
        assert observed['uuidMatches']==observed['portMatches']==observed['databaseMatches']=='true'
        prepared=materialize(config,side='business',platform_port=pp,**parameters);(business/'application.properties').write_bytes(prepared['properties'])
        argfile=business/'java-arguments.private.txt';argfile.write_text('\n'.join(json.dumps(s,ensure_ascii=False) for s in prepared['arguments'])+'\n',encoding='utf-8')
        business_tmp=runtime_temporary_path(app,business,'business');regular_tree_path(business_tmp,app);business_tmp.mkdir(parents=True,exist_ok=True)
        bchild=start('business',[str(app/'runtime/jdk17/bin/java.exe'),'@'+str(argfile)],business,{'TMP':str(business_tmp),'TEMP':str(business_tmp)})
        wait_for(lambda:(business/'server-ready.txt').is_file(),children,180,'business')
        bp=int((business/'server-http-port.txt').read_text('ascii'))
        if callback is not None:assert bp==callback_business_port,'CALLBACK_BUSINESS_LISTENER_IDENTITY_MISMATCH'
        am=app/'payload/admin/admin_runtime.json';files,_=load_admin(am,sha(am),'/zhumadian/admin');admin=ArchiveServer(files,mount_prefix='/zhumadian/admin');admin_thread=threading.Thread(target=admin.serve_forever,daemon=True);admin_thread.start()
        gateway_folder=run/'gateway'
        prepare(gateway_folder,app/'runtime/nginx',{role:app/'frontend'/role for role in ['security_pc','emergency_pc','mobile','bigscreen','tiles']},a.gateway_port,bp,pp,'/zhumadian',admin.server_port,'https://www.joinlinksmart.com','驻马店重大风险防控')
        check=subprocess.run([str(app/'runtime/nginx/nginx.exe'),'-p',str(gateway_folder)+os.sep,'-c',str(gateway_folder/'nginx.conf'),'-t'],capture_output=True,timeout=10,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        (run/'nginx-config-check.log').write_bytes(check.stdout+check.stderr);assert check.returncode==0
        gateway=start('gateway',[str(app/'runtime/nginx/nginx.exe'),'-p',str(gateway_folder)+os.sep,'-c',str(gateway_folder/'nginx.conf')],run)
        def gateway_ready():
            try:return request_owned_http(a.gateway_port,'GET','/zhumadian/home')[0]==200
            except OSError:return False
        wait_for(gateway_ready,children,15,'gateway')
        assert request_owned_http(a.gateway_port,'GET','/zhumadian/h5/')[0]==200
        assert request_owned_http(a.gateway_port,'GET','/zhumadian/project-icon-20261025.svg')[0]==200
        state.update(ready=True,callbackProjectionEnabled=callback is not None,platformPort=pp,businessPort=bp,databasePort=dbport,redisPort=redisport,objectStorePort=storeport,databaseUUID=identity['databaseUUID'],readyAt=datetime.datetime.now().astimezone().isoformat())
        (run/'ready.json').write_text(json.dumps(state,indent=2),encoding='utf-8');(data/'current-run.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
        print(json.dumps({'ready':True,'releaseId':release['releaseId'],'gatewayPort':a.gateway_port,'persistent':a.qa_seconds is None,'run':str(run),'publicAccepted':False}),flush=True)
        until=None if a.qa_seconds is None else time.monotonic()+a.qa_seconds
        while not (run/'stop-requested.txt').exists() and (until is None or time.monotonic()<until):
            assert all(c.process.poll() is None for c in children),'OWN_COMPONENT_EXITED_AFTER_READY';time.sleep(.5)
    except BaseException as error:
        state['failureType']=type(error).__name__;state['failureStageMessage']=str(error) if isinstance(error,AssertionError) or str(error).startswith('OWN_') else type(error).__name__
        raise
    finally:
        def attempt(label,callback):
            try:return callback()
            except Exception as error:state.setdefault('cleanupErrors',{})[label]=type(error).__name__;return None
        for folder in [business,platform]:attempt('stop-marker-'+folder.name,lambda folder=folder:(folder/'own-stop-requested.txt').write_text('stop\n',encoding='ascii'))
        if gateway is not None and gateway.process.poll() is None:
            attempt('gateway-quit',lambda:subprocess.run([str(app/'runtime/nginx/nginx.exe'),'-p',str(run/'gateway')+os.sep,'-c',str(run/'gateway/nginx.conf'),'-s','quit'],capture_output=True,timeout=10,env=env,creationflags=subprocess.CREATE_NO_WINDOW))
        stop_wait(gateway,10)
        if admin is not None:attempt('admin-stop',lambda:admin.shutdown());attempt('admin-close',lambda:admin.server_close());admin_thread.join(timeout=3)
        stop_wait(bchild,30);stop_wait(pchild,30)
        if redis is not None and redis.process.poll() is None:
            try:cache_command('SHUTDOWN','NOSAVE')
            except (OSError,RuntimeError):pass
        stop_wait(redis,10)
        if db is not None and db.process.poll() is None:
            r=attempt('mysql-stop',lambda:subprocess.run([str(app/'runtime/mysql/bin/mysqladmin.exe'),'--defaults-extra-file='+str(run/'mysql-client.private.cnf'),'shutdown'],capture_output=True,timeout=30,env=env,creationflags=subprocess.CREATE_NO_WINDOW))
            if r is not None:state['mysqlAdminStopExitCode']=r.returncode
        stop_wait(db,30)
        if store is not None and store.process.poll() is None:
            try:state['objectStoreStop']=stop_object_store_when_available(storeport,own['accessKey'],own['secretKey'])
            except Exception as error:state['objectStoreStopError']=type(error).__name__
        stop_wait(store,15)
        state['exitCodesBeforeJobClose']={c.name:c.process.poll() for c in children}
        state['forcedJobClosureComponents']=[c.name for c in children if c.process.poll() is None]
        state['normalOwnedShutdown']=not state['forcedJobClosureComponents'] and all(v==0 for v in state['exitCodesBeforeJobClose'].values())
        for child in children:attempt('close-job-'+child.name,child.close_job)
        for child in children:
            try:child.process.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
            child.thread.join(timeout=3)
        state['allOwnedChildrenExited']=all(c.process.poll() is not None for c in children)
        state['platformContextClosed']=(platform/'server-context-closed.txt').exists();state['businessContextClosed']=(business/'server-context-closed.txt').exists();state['endedAt']=datetime.datetime.now().astimezone().isoformat()
        attempt('receipt',lambda:(run/'receipt.json').write_text(json.dumps(state,indent=2),encoding='utf-8'));attempt('platform-owner-release',pf.release);lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
        print(json.dumps({'stopped':True,'allOwnedChildrenExited':state['allOwnedChildrenExited'],'normalExitCodes':state['exitCodesBeforeJobClose'],'run':str(run)}),flush=True)

if __name__=='__main__':main()
