"""Actual pinned nginx -> actual qualified managed worker; synthetic CurrentUser.

Default-off plus enabled routing. Only own config, empty SQLite and logs.
No original application/database/GIS/controller installation, desktop or public.
"""
from pathlib import Path
import hashlib,http.client,http.server,importlib.util,json,os,secrets,socket,sqlite3,subprocess,sys,threading,time,uuid
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
Q=Path('D:/Temp/Administrator/xnby-native-resource-r2404');assert not Q.exists();Q.mkdir()
P=A/'tools/experimental_source/client_resource_ingress_r2397/package'
MANIFEST='6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3'
sys.path.insert(0,str(P))
from tools.layer_sync_supervisor import verify_package
from tools.layer_sync_gateway_transaction import route_candidate
from tools.original_server_windows_job import OwnedWindowsJob
from services.layer_sync_bridge import process_creation
assert len(verify_package(P,MANIFEST)['inputs'])==44
spec=importlib.util.spec_from_file_location('r2404_bounds',V/'bounded_build_job_r671.py');bounds=importlib.util.module_from_spec(spec);spec.loader.exec_module(bounds)
assert bounds.memory_snapshot()['availablePhysicalBytes']>=2*1024**3
image=R/'_g/Application/runtime/nginx/nginx.exe';assert hashlib.sha256(image.read_bytes()).hexdigest()=='c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44'
dep=json.loads((A/'Packages/ClientGISSettingsCandidate_20261107/client-gis-install.json').read_bytes())
SOURCE={k:dep[k]for k in ['sourceRuntimeIdentity','sourceIndexIdentity']};SOURCE['budgetMiB']=2048
BINDING={k:SOURCE[k]for k in ['sourceRuntimeIdentity','sourceIndexIdentity']};BINDING['installationIdentity']='2d5561fa553ad5a199ff60a87cb1c89d334b78d3c0c67d2c909fb21f8db4e6b5'
ORIGIN='https://www.joinlinksmart.com';PUBLIC='/zhumadian/api/spatial-sync/v2/client-resources/grants'
EXPECTED={'origin':ORIGIN,'instanceId':secrets.token_hex(16),'challenge':secrets.token_hex(32),**BINDING}
tokens={role:'Synthetic '+secrets.token_hex(16)for role in ['reader','writer','outsider']}
identities={tokens['reader']:{'userId':'native-reader-fixture','roleIds':['reader']},tokens['writer']:{'userId':'native-writer-fixture','roleIds':['reader','writer']},tokens['outsider']:{'userId':'native-outsider-fixture','roleIds':[]}}
class Platform(http.server.ThreadingHTTPServer):daemon_threads=False;block_on_close=True
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        assert self.path=='/api/oauth/CurrentUser'
        info=identities.get(self.headers.get('Authorization'));value={'code':200,'data':{'userInfo':info}}if info else {'code':600}
        raw=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
platform=Platform(('127.0.0.1',0),Handler)
thread=threading.Thread(target=lambda:platform.serve_forever(poll_interval=.025),daemon=False)
checks=[];terminals=[];master=None;worker=None;failure=None
def check(ok,label):
    if not ok:raise AssertionError(label)
    checks.append(label)
def put(path,value):
    with path.open('x',encoding='utf-8')as f:json.dump(value,f,indent=2);f.write('\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def port():
    with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def spawn(args,label,cap=256*1024**2):
    log=(Q/(label+'.private.log')).open('xb')
    gate="import sys,subprocess;assert sys.stdin.buffer.readline(32)==b'R2404\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
    p=subprocess.Popen([sys.executable,'-I','-B','-c',gate,*map(str,args)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:job=OwnedWindowsJob(p);budget=bounds.BoundedBuildJob(job,cap)
    except BaseException:p.stdin.close();p.wait();log.close();raise
    p.stdin.write(b'R2404\n');p.stdin.flush();p.stdin.close()
    return {'process':p,'job':job,'budget':budget,'log':log,'label':label}
def finish(record):
    p=record['process'];job=record['job']
    while p.poll()is None:
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:print(json.dumps({'sameActualNormalExitPending':record['label'],'noForce':True}),flush=True)
    while job.active_processes()!=0:time.sleep(.05)
    result={'name':record['label'],'rootExitCode':p.returncode,'actualJobBeforeClose':job.active_processes(),'metrics':record['budget'].metrics()}
    job.close();record['log'].close();terminals.append(result)
    return result
def request(path,document=None,*,role=None,method='POST',raw=None,origin=True,cookie=False):
    body=raw if raw is not None else json.dumps(document).encode()if document is not None else None
    headers={'Content-Type':'application/json'}
    if origin:headers['Origin']=ORIGIN
    if role:headers['Authorization']=tokens[role]
    if cookie:headers['Cookie']='synthetic-denied-cookie'
    c=http.client.HTTPConnection('127.0.0.1',gateway_port,timeout=8)
    try:
        c.request(method,path,body=body,headers=headers);reply=c.getresponse();body=reply.read(262145);assert len(body)<=262144
        try:value=json.loads(body)if body else None
        except ValueError:value=None
        return reply.status,value,dict(reply.getheaders()),body
    finally:c.close()
def stop_master():
    global master
    if master is None:return
    record=master;root=record['folder'];p=record['process']
    if p.poll()is None:
        # A timeout is not terminal; observe the same owned launch until PID or exit.
        while p.poll()is None and not(root/'actual-master.json').exists():time.sleep(.05)
        if p.poll()is None:
            actual=json.loads((root/'actual-master.json').read_bytes());assert process_creation(actual['pid'])==actual['creation']
            assert int((root/'nginx.pid').read_text().strip())==actual['pid'] and sha(root/'nginx.conf')==record['configSHA256']
            quit=spawn([image,'-p',root.as_posix()+'/', '-c',(root/'nginx.conf').as_posix(),'-s','quit'],record['label']+'-quit')
            check(finish(quit)['rootExitCode']==0,'native-exact-prefix-quit-'+root.name)
    ended=finish(record);master=None
    actual=json.loads((root/'actual-master-terminal.json').read_bytes())
    check(ended['rootExitCode']==0 and ended['actualJobBeforeClose']==0 and actual['actualPopenExitCode']==0,'native-master-real-handle-and-job-zero-'+root.name)

try:
    thread.start();worker_port=port();instance=uuid.uuid4().hex;run=Q/instance;run.mkdir()
    config=Q/'worker-config.json'
    put(config,{'schema':'xnby.layer-sync.server.v1','listenPort':worker_port,'platformPort':platform.server_port,
      'access':{'readers':[],'writers':[],'read_roles':['reader'],'write_roles':['writer'],'administrators':False},
      'localGIS':{'schema':'xnby.local-gis.server-settings.v1','allowedSources':[SOURCE]},
      'clientResources':{'schema':'xnby.client-resources.server-settings.v1','allowedInstallations':[BINDING]}})
    cfg_sha=sha(config)
    worker=spawn([A/'runtime/python/python.exe','-I','-B',P/'tools/serve_layer_sync.py','--config',config,'--data-root',Q/'data','--run-root',run,'--instance-id',instance,'--config-sha256',cfg_sha,'--manifest-sha256',MANIFEST],'managed-worker',512*1024**2)
    deadline=time.monotonic()+30
    while not(run/'ready.json').exists():
        assert worker['process'].poll()is None,'OWN_WORKER_EXITED_BEFORE_READY'
        assert time.monotonic()<deadline,'OBSERVE_SAME_WORKER_NO_RESTART';time.sleep(.05)
    ready=json.loads((run/'ready.json').read_bytes());check(ready['manifestSHA256']==MANIFEST and ready['configSHA256']==cfg_sha,'new-44-package-managed-worker-qualified')
    for enabled in [False,True]:
        root=Q/('enabled'if enabled else'disabled');root.mkdir();(root/'logs').mkdir();(root/'temp').mkdir();gateway_port=port();nonce=secrets.token_hex(16)
        base=('daemon off;\nmaster_process on;\nworker_processes 1;\nworker_shutdown_timeout 3s;\npid "'+(root/'nginx.pid').as_posix()+'";\nerror_log "'+(root/'logs/error.log').as_posix()+'" warn;\nevents { worker_connections 64; }\nhttp { access_log off;\n server {\n listen 127.0.0.1:'+str(gateway_port)+';\n location ^~ /zhumadian/api/serv/ { return 204; }\n location / { return 404; }\n }\n}\n').encode()
        cfg=root/'nginx.conf';cfg.write_bytes(route_candidate(base,worker_port,nonce,local_gis=True,client_resources=enabled))
        syntax=spawn([image,'-p',root.as_posix()+'/', '-c',cfg.as_posix(),'-t'],'syntax-'+root.name)
        check(finish(syntax)['rootExitCode']==0,'actual-native-syntax-'+root.name)
        master=spawn([sys.executable,'-I','-B',V/'owned_resource_nginx_r2404.py',root,cfg],'gateway-'+root.name)
        master.update(folder=root,configSHA256=sha(cfg))
        deadline=time.monotonic()+20
        while True:
            assert master['process'].poll()is None,'OWN_NGINX_EXITED_BEFORE_READY'
            try:
                if request('/zhumadian/api/serv/probe',method='GET')[0]==204:break
            except OSError:pass
            assert time.monotonic()<deadline,'OBSERVE_SAME_NGINX_NO_RESTART';time.sleep(.05)
        check(request('/zhumadian/api/spatial-sync/v1/project/layers',method='GET',role='reader')[0]==200,'original-DLG-read-via-nginx-'+root.name)
        if not enabled:
            check(request(PUBLIC,{'expected':EXPECTED},role='writer')[0]==404,'default-off-resource-route-not-exposed')
            stop_master();continue
        check(request(PUBLIC,{'expected':EXPECTED})[0]==401,'anonymous-resource-issue401-through-native-nginx')
        check(request(PUBLIC,{'expected':EXPECTED},role='writer',origin=False)[0]==403,'missing-origin403-through-native-nginx')
        check(request(PUBLIC,{'expected':EXPECTED},role='writer',cookie=True)[0]==400,'cookie400-through-native-nginx')
        check(request(PUBLIC,role='writer',raw=b'x'*8193)[0]==413,'native-nginx-8KiB-body-bound413')
        check(request(PUBLIC,{'expected':EXPECTED},role='writer',method='GET')[0]==403,'native-nginx-POST-only403')
        check(request(PUBLIC+'/unknown',{'expected':EXPECTED},role='writer')[0]==404,'unlisted-resource-subpath404')
        for role,scopes in [('reader',['client.resources.read']),('writer',['client.resources.read','client.resources.write'])]:
            status,issued,headers,_=request(PUBLIC,{'expected':EXPECTED},role=role)
            check(status==201 and headers.get('Cache-Control')=='no-store'and headers.get('X-XNBY-Layer-Sync-Deployment')==nonce,'authorized-uncached-grant-'+role)
            body={'grant':issued['grant'],'expected':EXPECTED}
            status,receipt,headers,raw=request(PUBLIC+'/consume',body)
            check(status==200 and receipt['scopes']==scopes and 1<=int(headers['X-XNBY-Local-GIS-Remaining-Ms'])<=30000,'mandatory-monotonic-header-and-original-scopes-'+role)
            check(set(receipt)==set(EXPECTED)|{'accepted','scopes','actorKey','projectKey','expiresAt'}and all(token.encode()not in raw for token in tokens.values()),'exact11-receipt-no-original-auth-'+role)
            check(request(PUBLIC+'/consume',body)[0]==403,'native-one-use-grant-no-replay-'+role)
        unsupported=request(PUBLIC,{'expected':dict(EXPECTED,installationIdentity='0'*64)},role='writer')
        check(unsupported[0]==409 and unsupported[1]['code']=='RESOURCE_INSTALLATION_UNSUPPORTED','native-409-code-preserved')
        check(request(PUBLIC,{'expected':EXPECTED},role='outsider')[0]==403,'original-project-outsider403-through-native-nginx')
        _,issued,_,_=request(PUBLIC,{'expected':EXPECTED},role='writer');identities[tokens['writer']]['roleIds']=['reader']
        check(request(PUBLIC+'/consume',{'grant':issued['grant'],'expected':EXPECTED})[0]==403,'original-write-revocation403-through-native-nginx')
        discovery={'schema':'xnby.local-gis.discovery.v1','protocolVersion':1,'ready':True,'instanceId':secrets.token_hex(16),'challenge':secrets.token_hex(32),**SOURCE}
        gis='/zhumadian/api/spatial-sync/v2/local-gis/grants'
        status,issued,_,_=request(gis,{'schema':'xnby.local-gis.grant-request.v1','discovery':discovery},role='reader');check(status==201,'old-GIS-namespace-issue-retained')
        expected={'origin':ORIGIN,**{k:v for k,v in discovery.items()if k not in ('schema','protocolVersion','ready')}}
        status,receipt,headers,_=request(gis+'/consume',{'grant':issued['grant'],'expected':expected})
        check(status==200 and len(receipt)==9 and 1<=int(headers['X-XNBY-Local-GIS-Remaining-Ms'])<=30000,'old9-field-GIS-receipt-and-header-retained')
        stop_master()
except BaseException as error:failure={'type':type(error).__name__,'code':str(error)[:160]}
finally:
    if master is not None:stop_master()
    if worker is not None:
        if worker['process'].poll()is None:put(run/'stop.json',{'schema':'xnby.layer-sync.worker-stop.v1','instanceId':instance,'configSHA256':cfg_sha})
        ended=finish(worker);check(ended['rootExitCode']==0 and ended['actualJobBeforeClose']==0,'managed-worker-normal-root-and-job-zero')
    if thread.ident is not None:platform.shutdown()
    platform.server_close()
    if thread.ident is not None:thread.join()
    with sqlite3.connect((Q/'data/layers.sqlite').as_uri()+'?mode=ro',uri=True)as db:
        tables=[row[0]for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'AND name NOT LIKE 'sqlite_%'")]
        check(len(tables)==14 and all(db.execute('SELECT count(*)FROM "'+n+'"').fetchone()[0]==0 for n in tables),'only-own14-table-fixture-remains-empty')
    check(all(token.encode()not in f.read_bytes()for f in Q.rglob('*')if f.is_file()for token in tokens.values()),'synthetic-original-authorization-not-on-disk')
    result={'passed':failure is None,'failure':failure,'checks':checks,'distinctChecks':len(set(checks)),'actualNativeNginxTwoCycles':True,'actualQualified44ManagedWorker':True,
      'processes':terminals,'actualOriginalPlatformAccessSyntheticCurrentUser':True,'actualIIS_TLS_Java_NormalUser_252NotTested':True,
      'productionNoMutation':True,'noForceTermination':True,'allOwnUpstreamThreadsJoined':not thread.is_alive()}
    put(Q/'verification.json',result);print(json.dumps({k:v for k,v in result.items()if k!='checks'}))
raise SystemExit(0 if failure is None else 1)
