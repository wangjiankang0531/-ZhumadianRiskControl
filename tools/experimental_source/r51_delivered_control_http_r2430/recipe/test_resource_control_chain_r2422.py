"""Original managed worker -> actual D172 manager. CurrentUser is synthetic.

New private SQLite/configuration/profile only. No Java/MySQL, GIS provider,
production listener, desktop, public upload, or installed application changes.
"""
from pathlib import Path
import hashlib,http.client,http.server,importlib.util,json,os,secrets,socket,sqlite3,subprocess,sys,threading,time,uuid

R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
Q=Path('D:/Temp/Administrator/xnby-resource-control-r2422')
P=A/'tools/experimental_source/client_resource_ingress_r2397/package'
C=A/'Packages/ResourceGISControlCandidate_20261112/client-250'
PY=A/'Packages/ClientGISSettingsCandidate_20261107/runtime/python/python.exe'
MANIFEST='6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3'
ORIGIN='https://www.joinlinksmart.com';PREFIX='/xnby-client-resources/v1/'
HELPER=V/'resource_control_http_backend_r2422.py'
assert not Q.exists();Q.mkdir()
sys.path[:0]=[str(P),str(C/'code'),str(A/'Packages/ClientGISSettingsCandidate_20261107/code'),str(A/'Packages/ClientGISSettingsCandidate_20261107/provider/tools')]
from tools.layer_sync_supervisor import verify_package
from tools.original_server_windows_job import OwnedWindowsJob
from client_manifest import load_installation,workspace_context
from client_settings import workspace_document
from client_control import private_directory,atomic_json
from client_gis_runtime import current_owner
assert len(verify_package(P,MANIFEST)['inputs'])==44
dep=load_installation(A/'Packages/ClientGISSettingsCandidate_20261107')
binding={'installationIdentity':'bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b',
         'sourceRuntimeIdentity':dep['sourceRuntimeIdentity'],'sourceIndexIdentity':dep['sourceIndexIdentity']}
spec=importlib.util.spec_from_file_location('r2393_job_budget',V/'bounded_build_job_r671.py');limits=importlib.util.module_from_spec(spec);spec.loader.exec_module(limits)
assert limits.memory_snapshot()['availablePhysicalBytes']>=2*1024**3
context=workspace_context(A/'private/client-workspace.json',A/'Packages/ClientGISSettingsCandidate_20261107',verify_resources=False)
protected=[A/'private/client-workspace.json',A/'Packages/ClientGISSettingsCandidate_20261107/client-gis-install.json',context['state']/'active.private.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=[sha(p)for p in protected];owner=current_owner(context);assert owner['phase']=='ready'
tokens={name:'Synthetic '+secrets.token_hex(16)for name in ['writerA','readerA','writerB','outsider']}
identities={tokens['writerA']:{'userId':'receiver-r2422-A','roleIds':['qa-read','qa-write']},
            tokens['readerA']:{'userId':'receiver-r2422-A','roleIds':['qa-read']},
            tokens['writerB']:{'userId':'receiver-r2422-B','roleIds':['qa-read','qa-write']},
            tokens['outsider']:{'userId':'receiver-r2422-outside','roleIds':[]}}
class PlatformHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        assert self.path=='/api/oauth/CurrentUser';self.server.calls+=1
        info=identities.get(self.headers.get('Authorization'))
        body=json.dumps({'code':200,'data':{'userInfo':info}}if info else{'code':600}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
class Platform(http.server.ThreadingHTTPServer):daemon_threads=False;block_on_close=True
platform=Platform(('127.0.0.1',0),PlatformHandler);platform.calls=0
upstream=threading.Thread(target=lambda:platform.serve_forever(poll_interval=.025),daemon=False)
checks=[];terminals=[];worker=None;manager=None;failure=None
def check(ok,name):
    if not ok:raise AssertionError(name)
    checks.append(name)
def dump(path,value):
    with path.open('x',encoding='utf-8')as f:json.dump(value,f,separators=(',',':'));f.flush();os.fsync(f.fileno())
def free_port():
    with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def launch(python,args,name,cap=256*1024**2):
    log=(Q/(name+'.private.log')).open('xb')
    gate="import sys,runpy;assert sys.stdin.buffer.readline(32)==b'R2422\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
    child=subprocess.Popen([str(python),'-I','-B','-c',gate,*map(str,args)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:job=OwnedWindowsJob(child);budget=limits.BoundedBuildJob(job,cap)
    except BaseException:child.stdin.close();child.wait();log.close();raise
    child.stdin.write(b'R2422\n');child.stdin.flush();child.stdin.close()
    return {'child':child,'job':job,'budget':budget,'log':log,'name':name}
def observe_ready(process,file):
    deadline=time.monotonic()+90
    while not file.exists():
        if process['child'].poll()is not None:raise AssertionError(process['name']+'_EXITED_BEFORE_READY')
        if time.monotonic()>deadline:raise TimeoutError('SAME_OWNED_PROCESS_READY_OBSERVATION_EXPIRED')
        time.sleep(.05)
    return json.loads(file.read_bytes())
def join(process):
    p=process['child'];job=process['job']
    while p.poll()is None:
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:print(json.dumps({'waitingSameNormalExit':process['name'],'noForce':True}),flush=True)
    while job.active_processes()!=0:time.sleep(.05)
    row={'name':process['name'],'rootExitCode':p.returncode,'actualJobBeforeClose':job.active_processes(),'metrics':process['budget'].metrics()}
    job.close();process['log'].close();terminals.append(row)
    return row
def request(port,path,body=None,method='GET',role=None,session=None,private_negative=False):
    headers={'Origin':ORIGIN}
    if body is not None:headers['Content-Type']='application/json'
    if role:headers['Authorization']=tokens[role]
    if session:headers['X-XNBY-Client-Resources-Session']=session
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=90)
    try:
        conn.request(method,path,json.dumps(body).encode()if body is not None else None,headers)
        response=conn.getresponse();raw=response.read(262145);assert len(raw)<=262144
        return response.status,json.loads(raw)if raw else None,dict(response.getheaders())
    finally:conn.close()
def establish(port,role):
    status,discovery,_=request(port,PREFIX+'discovery');check(status==200,'actual-manager-discovery-'+role)
    expected={'origin':ORIGIN,**{k:discovery[k]for k in ['instanceId','challenge','installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity']}}
    status,issued,_=request(worker_port,'/v2/client-resources/grants',{'expected':expected},'POST',role=role)
    check(status==201,'actual-original-worker-issue-'+role)
    status,session,headers=request(port,PREFIX+'sessions',{'grant':issued['grant']},'POST')
    check(status==201 and 1<=int(headers['X-XNBY-Local-GIS-Remaining-Ms'])<=30000,'actual-qualified-manager-consume-'+role)
    return session['session'],expected
def renew_session(port,session,expected,role):
    status,issued,_=request(worker_port,'/v2/client-resources/grants',{'expected':expected},'POST',role=role)
    check(status==201,'original-authority-session-renew-issue-'+role)
    status,value,_=request(port,PREFIX+'sessions/current',{'grant':issued['grant']},'POST',session=session)
    check(status==201 and value['session']==session,'qualified-local-same-session-renew-'+role)

def stop_manager(cycle):
    global manager
    if manager is None:return
    active=Q/'private-QA/manager/active.private.json'
    while manager['child'].poll()is None and not active.exists():time.sleep(.05)
    if manager['child'].poll()is None:
        stopper=launch(PY,[HELPER,'stop',str(cycle)],'manager-stop-'+str(cycle))
        result=join(stopper);check(result['rootExitCode']==0,'own-qualified-stop-command-'+str(cycle))
    result=join(manager);manager=None
    check(result['rootExitCode']==0 and result['actualJobBeforeClose']==0,'own-manager-root-and-job-zero-'+str(cycle))

# Appended to the fixed R2395 orchestration helpers by prepare_control_chain_r2422.py.
import ctypes,shutil
from ctypes import wintypes
from client_control import process_identity,kernel_api
def j(p):return json.loads(p.read_bytes())
pending=[];observed=[];own_contexts=[];config=Q/'private-QA/config/client-workspace.json'
old_root=Q/'old/Zhumadian';new_root=Q/'new/Zhumadian'
def observe_own_controller(context):
    record=current_owner(context);assert record is not None and record['port']==synthetic_port
    expected=record['controller'];api=kernel_api();api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];api.OpenProcess.restype=wintypes.HANDLE
    handle=api.OpenProcess(0x101000,False,expected['pid']);assert handle
    api.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];api.GetProcessTimes.restype=wintypes.BOOL
    times=[wintypes.FILETIME()for _ in range(4)];assert api.GetProcessTimes(handle,*map(ctypes.byref,times))
    assert (times[0].dwHighDateTime<<32)|times[0].dwLowDateTime==expected['created100ns'] and process_identity(expected['pid'])==expected
    api.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];api.GetExitCodeProcess.restype=wintypes.BOOL
    api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];api.WaitForSingleObject.restype=wintypes.DWORD
    value={'api':api,'handle':handle,'expected':expected,'context':context,'terminal':False};observed.append(value);own_contexts.append(context);return value
def normal_controller_terminal(value):
    if value['terminal']:return
    api=value['api'];handle=value['handle']
    while api.WaitForSingleObject(handle,1000)==258:print(json.dumps({'observingSameSyntheticKernelHandle':True}),flush=True)
    code=wintypes.DWORD();assert api.GetExitCodeProcess(handle,ctypes.byref(code))and code.value==0
    api.CloseHandle(handle);value['terminal']=True;value['exitCode']=code.value
def completed_operation(port,token,expected,identifier,label):
    deadline=time.monotonic()+90;last=time.monotonic()
    while True:
        if time.monotonic()-last>8:renew_session(port,token,expected,'writerA');last=time.monotonic()
        status,value,_=request(port,PREFIX+'gis/operations/'+identifier,session=token);assert status==200
        if value['state']in('completed','failed','cancelled'):break
        assert time.monotonic()<deadline,'SAME_CONTROL_THREAD_OBSERVATION_EXPIRED';time.sleep(.03)
    check(value['state']=='completed'and value['accepted']and value['result']['registeredOwnerOnly'],label);return value
try:
    config.parent.mkdir(parents=True);private_directory(config.parent)
    assert len(dep['offlineResources'])==2356
    logical=sum(row['bytes']for row in dep['offlineResources'].values())*2
    check(logical<1024**3 and shutil.disk_usage(Q).free>2*1024**3,'two-support-views-budgeted-under-one-GiB-logical-no-raw-GIS')
    for root in(old_root,new_root):
        (root/'Assets/3DGIS/驻马店园区/Data').mkdir(parents=True)
        resource=root/'Assets/Runtime';resource.mkdir()
        for name,row in dep['offlineResources'].items():
            source=context['resources']/name;assert source.is_file()and source.stat().st_size==row['bytes']and sha(source)==row['sha256']
            dest=resource/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest)
    dump(Q/'support-view-storage-plan.json',{'views':2,'files':2356*2,'logicalBytes':logical,'source':str(context['resources']),'immutableHardLinksNotIndependentPhysicalCopies':True,'rawOSGBFilesCopied':0})
    atomic_json(config,workspace_document(old_root.as_posix()),replace=False)
    from client_manifest import workspace_context
    synthetic_port=free_port();assert synthetic_port!=18767
    upstream.start();worker_port=free_port();instance=uuid.uuid4().hex;run=Q/instance;run.mkdir();cfg=Q/'worker-config.json'
    document={'schema':'xnby.layer-sync.server.v1','listenPort':worker_port,'platformPort':platform.server_port,
       'access':{'readers':[],'writers':[],'read_roles':['qa-read'],'write_roles':['qa-write'],'administrators':False},
       'clientResources':{'schema':'xnby.client-resources.server-settings.v1','allowedInstallations':[binding]}}
    dump(cfg,document);cfg_sha=sha(cfg);dump(Q/'backend-config.json',{'workerPort':worker_port,'syntheticGISPort':synthetic_port})
    worker=launch(A/'runtime/python/python.exe',[P/'tools/serve_layer_sync.py','--config',cfg,'--data-root',Q/'data','--run-root',run,'--instance-id',instance,'--config-sha256',cfg_sha,'--manifest-sha256',MANIFEST],'actual-managed-worker',512*1024**2)
    ready=observe_ready(worker,run/'ready.json');check(ready['pid']==worker['child'].pid and ready['manifestSHA256']==MANIFEST,'new-44-worker-actual-owner')
    manager=launch(PY,[HELPER,'serve','1'],'qualified-manager-1');port=observe_ready(manager,Q/'manager-ready-1.json')['port']
    writer,expected=establish(port,'writerA');reader,_=establish(port,'readerA');other,_=establish(port,'writerB')
    check(request(worker_port,'/v2/client-resources/grants',{'expected':dict(expected,installationIdentity='0'*64)},'POST',role='writerA')[0]==409,'unknown-GIS-control-installation-not-granted')
    check(request(worker_port,'/v2/client-resources/grants',{'expected':expected},'POST',role='outsider')[0]==403,'outside-original-project-no-control-grant')
    status,value,_=request(port,PREFIX+'gis/status',session=reader);check(status==200 and value['phase']=='stopped'and not value['owned'],'original-reader-can-read-own-registered-GIS-status')
    for action in('start','stop'):check(request(port,PREFIX+'gis/'+action,{},'POST',session=reader)[0]==403,'original-reader-cannot-'+action+'-GIS')
    check(request(port,PREFIX+'gis/start',{'pid':1234},'POST',session=writer)[0]==400,'caller-PID-body-not-accepted')
    status,value,_=request(port,PREFIX+'gis/start',{},'POST',session=writer);check(status==202,'explicit-writer-start-accepted-over-real-local-HTTP')
    operation=value['id'];check(request(port,PREFIX+'gis/operations/'+operation,session=other)[0]==404,'foreign-original-subject-cannot-read-control-operation')
    done=completed_operation(port,writer,expected,operation,'new-D175-qualified-start-and-original-intent-complete')
    own_old=workspace_context(config,A/'Packages/ClientGISSettingsCandidate_20261107',verify_resources=False);first=observe_own_controller(own_old)
    status,value,_=request(port,PREFIX+'gis/status',session=reader);check(status==200 and value['owned']and value['phase']=='ready','real-synthetic-controller-ready-through-original-status')
    config_before=sha(config);status,value,_=request(port,PREFIX+'configuration',{'workspaceRoot':new_root.as_posix()},'POST',session=writer)
    check(status==400 and value['code']=='STOP_GIS_BEFORE_CHANGING_WORKSPACE'and sha(config)==config_before,'live-registered-controller-blocks-root-change-and-preserves-file')
    check(request(port,PREFIX+'gis/stop',{'command':'ignored'},'POST',session=writer)[0]==400,'caller-command-body-not-accepted')
    status,value,_=request(port,PREFIX+'gis/stop',{},'POST',session=writer);check(status==202,'explicit-stop-accepted-over-real-local-HTTP')
    completed_operation(port,writer,expected,value['id'],'new-D175-stop-uses-unmodified-original-private-protocol');normal_controller_terminal(first)
    check(current_owner(own_old)is None,'old-controller-terminal-before-root-save')
    renew_session(port,writer,expected,'writerA')
    status,value,_=request(port,PREFIX+'configuration',{'workspaceRoot':new_root.as_posix()},'POST',session=writer)
    check(status==200 and value['workspaceRoot']==new_root.as_posix()and sha(config)!=config_before,'actual-qualified-save-after-normal-stop-moves-only-own-config')
    check(j(config)==workspace_document(new_root.as_posix()),'saved-new-root-keeps-original-six-relative-path-schema')
    renew_session(port,writer,expected,'writerA')
    status,value,_=request(port,PREFIX+'gis/start',{},'POST',session=writer);check(status==202,'explicit-start-on-new-QA-root-accepted')
    completed_operation(port,writer,expected,value['id'],'new-root-original-controller-identity-binds-to-new-config')
    own_new=workspace_context(config,A/'Packages/ClientGISSettingsCandidate_20261107',verify_resources=False);second=observe_own_controller(own_new)
    check(second['expected']!=first['expected']and current_owner(own_old)is None,'new-root-does-not-reuse-old-controller')
    stopper=launch(PY,[HELPER,'stop','1'],'manager-stop-detach-1');check(join(stopper)['rootExitCode']==0,'first-manager-normal-stop-observed')
    original_manager=manager;original_manager['child'].wait();check(original_manager['child'].returncode==0 and original_manager['job'].active_processes()>0,'manager-root-zero-is-not-GIS-job-zero')
    pending.append(original_manager);manager=None
    check(process_identity(second['expected']['pid'])==second['expected'],'registered-synthetic-GIS-survives-manager-normal-exit')
    manager=launch(PY,[HELPER,'serve','2'],'qualified-manager-2');port2=observe_ready(manager,Q/'manager-ready-2.json')['port']
    check(request(port2,PREFIX+'gis/status',session=writer)[0]==401,'old-resource-session-not-reused-by-new-manager')
    writer2,expected2=establish(port2,'writerA');reader2,_=establish(port2,'readerA')
    status,value,_=request(port2,PREFIX+'gis/status',session=reader2);check(status==200 and value['owned']and value['phase']=='ready','new-manager-finds-separately-owned-registered-GIS')
    status,value,_=request(port2,PREFIX+'gis/start',{},'POST',session=writer2);assert status==202
    result=completed_operation(port2,writer2,expected2,value['id'],'already-running-control-reuses-existing-synthetic-controller')
    check(result['result']['alreadyRunning']and process_identity(second['expected']['pid'])==second['expected'],'no-second-controller-started-after-manager-restart')
    status,value,_=request(port2,PREFIX+'gis/stop',{},'POST',session=writer2);assert status==202
    completed_operation(port2,writer2,expected2,value['id'],'new-manager-normally-stops-original-previous-manager-controller')
    normal_controller_terminal(second)
    ended=join(pending.pop());check(ended['rootExitCode']==0 and ended['actualJobBeforeClose']==0,'previous-manager-job-zero-only-after-synthetic-GIS-normal-exit')
    stop_manager(2)
    check(before==[sha(p)for p in protected]and current_owner(context)==owner,'real250-config-program-active-and-GIS-owner-byte-preserved')
except BaseException as error:
    failure={'type':type(error).__name__,'code':str(error)[:160]}
finally:
    # Only this registered QA configuration and the two known roots are eligible.
    if config.is_file():
        qa_context=workspace_context(config,A/'Packages/ClientGISSettingsCandidate_20261107',verify_resources=False)
        assert qa_context['root']in(old_root,new_root)
        qa_owner=current_owner(qa_context)
        if qa_owner is not None:
            assert qa_owner['port']==synthetic_port
            stopper=launch(PY,[HELPER,'stopGIS','2'],'cleanup-own-synthetic-GIS');check(join(stopper)['rootExitCode']==0,'cleanup-only-own-synthetic-original-stop')
    for value in observed:normal_controller_terminal(value)
    if manager is not None:stop_manager(2 if(Q/'manager-ready-2.json').exists()else 1)
    for record in pending:check(join(record)['actualJobBeforeClose']==0,'pending-original-manager-job-drained-after-own-GIS')
    if worker is not None:
        marker={'schema':'xnby.layer-sync.worker-stop.v1','instanceId':instance,'configSHA256':cfg_sha}
        if worker['child'].poll()is None:
            if(run/'stop.json').exists():assert j(run/'stop.json')==marker
            else:dump(run/'stop.json',marker)
        ended=join(worker);check(ended['rootExitCode']==0 and ended['actualJobBeforeClose']==0,'actual-managed-worker-normal-root-and-job-zero')
    if upstream.ident is not None:platform.shutdown()
    platform.server_close()
    if upstream.ident is not None:upstream.join()
    if(Q/'data/layers.sqlite').exists():
        with sqlite3.connect((Q/'data/layers.sqlite').as_uri()+'?mode=ro',uri=True)as db:
            tables=[row[0]for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            check(len(tables)==14 and all(db.execute('SELECT count(*) FROM "'+n+'"').fetchone()[0]==0 for n in tables),'own-fourteen-layer-tables-unchanged-empty')
    small_text=[p for p in Q.rglob('*')if p.is_file()and p.suffix in('.json','.log','.txt')and p.stat().st_size<1048576 and 'Assets'not in p.parts]
    check(not any(t.encode()in p.read_bytes()for p in small_text for t in tokens.values()),'synthetic-original-authorization-not-persisted-in-QA-control-records')
    check(before==[sha(p)for p in protected]and current_owner(context)==owner,'real250-protected-bytes-and-owner-preserved-at-final')
    result={'passed':failure is None,'failure':failure,'checks':checks,'distinctChecks':len(set(checks)),
        'actual44SourceManagedWorkerAndTenPlus953QualifiedManager':True,'originalCurrentUserExplicitlySynthetic':True,
        'GISProviderStartupExplicitlySynthetic':True,'actualOriginalPrivateStopAndKernelExitHandles':True,
        'syntheticControllers':[{'normalExitCode':v.get('exitCode'),'sameKernelHandleObserved':v['terminal']}for v in observed],
        'actualOriginalRootsAndJobs':terminals,'noForceTermination':True,'allOwnUpstreamThreadsJoined':not upstream.is_alive(),
        'noProduction18767Or18768RegistryPublicOrLiveGISMutation':True,'originalNormalJavaLoginTLSBrowserFullGISAnd252NotAccepted':True}
    dump(Q/'verification.json',result);print(json.dumps(result),flush=True)
raise SystemExit(0 if failure is None else 1)
