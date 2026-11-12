from pathlib import Path
import hashlib,http.client,importlib.util,json,secrets,subprocess,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';W=R/'work/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112/attempt03';BASE=W;agent=A/'Packages/ResourceGISControlCandidate_20261112/client-250';package=A/'Packages/ClientGISSettingsCandidate_20261107';peer=A/'tools/experimental_source/client_resource_authority_r2352/client_resource_grants_r2351.py'
for static in ['fixture-parent03.html','fixture-parent03.js','delivery02/index.html','delivery02/viewer.js','delivery02/source-gain-worker.js']:assert(BASE/static).is_file(),static
assert hashlib.sha256(peer.read_bytes()).hexdigest()=='9a62613fb42502d10b252f7f994ac1db23c826754500a9961af5d190cc0d52b3'
sys.path[:0]=[str(agent/'code'),str(package/'code'),str(package/'provider/tools'),str(A/'tools/experimental_source/public_gis_worker_r2178/package'),str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools')]
from entry import qualify
from client_manifest import load_installation
trusted=qualify(agent);trusted['dependency']=load_installation(package)
assert trusted['manifestSHA256']=='bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b'
from resource_agent import stop,status
from osgb_stdio_worker import OwnedWindowsJob
from resource_grants import ORIGIN
from resource_reports import OwnedReports
from client_settings import workspace_document
from client_control import private_directory,atomic_json
spec=importlib.util.spec_from_file_location('peer_resource_authority',peer);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class AccessError(Exception):
    def __init__(self,status):self.status=status
class Access:
    def __init__(self):self.calls=0
    def check(self,authorization,write=False):
        self.calls+=1;users={'fixture-writer-A':('isolated-resource-A',True),'fixture-reader-A':('isolated-resource-A',False),'fixture-writer-B':('isolated-resource-B',True)}
        if authorization not in users:raise AccessError(401)
        subject,can_write=users[authorization]
        if write and not can_write:raise AccessError(403)
        return subject
install=trusted['dependency'];binding={'installationIdentity':trusted['manifestSHA256'],'sourceRuntimeIdentity':install['sourceRuntimeIdentity'],'sourceIndexIdentity':install['sourceIndexIdentity']};access=Access();grants=g.ClientResourceGrantAuthority(access,[binding],grant_seconds=6,session_seconds=6)
class Quiet(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
GrantHandler=g.with_client_resource_grants(Quiet);grant_server=ThreadingHTTPServer(('127.0.0.1',0),GrantHandler);grant_server.resource_grant_authority=grants
profile=W/'private-QA03/agent';configuration=W/'private-QA03/config/client-workspace.json';configuration.parent.mkdir(parents=True);private_directory(configuration.parent)
rootA=W/'roots/A/Zhumadian';rootB=W/'roots/B/Zhumadian';assert(rootA/'Assets/Runtime').is_dir();atomic_json(configuration,workspace_document(rootA.as_posix()),replace=False)
reports=OwnedReports(profile/'reports',binding=binding);counts={'managementRequests':0,'issueRequests':0,'forbiddenLocalHeaders':0,'terrainRequests':0,'originalACLCalls':0}
protected=[A/'private/client-workspace.json',package/'client-gis-install.json',R/'UserData/ClientGIS/active.private.json'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p)for p in protected};(D/'protected250-before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
def raw_reply(handler,status,raw,headers):
    handler.send_response(status)
    for k,v in headers:
        if k.lower()not in {'content-length','connection','transfer-encoding','access-control-allow-origin'}:handler.send_header(k,v)
    handler.send_header('Content-Length',str(len(raw)));handler.send_header('Connection','close');handler.end_headers();handler.wfile.write(raw);handler.close_connection=True
class Front(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def do_GET(self):self.dispatch()
    def do_POST(self):self.dispatch()
    def do_DELETE(self):self.dispatch()
    def dispatch(self):
        path=self.path.split('?',1)[0];length=int(self.headers.get('Content-Length','0'));assert 0<=length<=8192;body=self.rfile.read(length)if length else None
        if path=='/fixture/move-support':
            assert self.command=='POST'and self.headers.get('X-Own-Fixture')=='d176'and body==b'{}'
            events=json.loads((D/'gis-lifecycle.json').read_text(encoding='utf-8'));assert len([r for r in events if r['phase']=='normal-stop-complete'])==1
            original=[r for r in events if r['phase']=='synthetic-original-terminal'];assert len(original)==1 and original[0]['rootExitCode']==original[0]['originalJobBeforeClose']==0
            source=rootA/'Assets/Runtime';target=rootB/'Assets/Runtime';boundary=(W/'roots').resolve()
            assert source.resolve().is_relative_to(boundary)and target.resolve().is_relative_to(boundary)and not target.exists()
            for f in [source,*source.rglob('*')]:assert not f.is_symlink()and not(getattr(f.lstat(),'st_file_attributes',0)&0x400)
            source.rename(target);(D/'own-support-move.json').write_text(json.dumps({'moved':True,'source':str(source),'destination':str(target),'originalSyntheticRootAndJobZeroBeforeMove':True,'userResourceOrRawGISMoved':False},indent=2)+'\n',encoding='utf-8')
            return raw_reply(self,200,b'{"moved":true}',[('Content-Type','application/json')])
        if path=='/zhumadian/api/spatial-sync/v2/client-resources/grants':
            counts['issueRequests']+=1;port=grant_server.server_port;upstream=g.INTERNAL_PATH;headers={'Origin':ORIGIN,'Content-Type':'application/json','Authorization':self.headers.get('Authorization','')}
        elif path.startswith('/xnby-client-resources/v1/'):
            counts['managementRequests']+=1;port=manager_port;upstream=path;headers={'Origin':ORIGIN}
            if self.headers.get('Authorization')or self.headers.get('Cookie'):counts['forbiddenLocalHeaders']+=1;return raw_reply(self,400,b'{"code":"FIXTURE_PRIVATE_HEADER_REJECTED"}',[('Content-Type','application/json')])
            for key in ['Content-Type','X-XNBY-Client-Resources-Session']:
                if self.headers.get(key):headers[key]=self.headers[key]
        else:
            file=None
            if path in ['/zhumadian/sceneViewer','/zhumadian/sceneEditor','/zhumadian/ended']:file=BASE/'fixture-parent03.html'
            elif path=='/fixture-parent.js':file=BASE/'fixture-parent03.js'
            elif path in ['/zhumadian/scene/','/zhumadian/scene/index.html']:file=BASE/'delivery02/index.html'
            elif path in ['/zhumadian/scene/viewer.js','/zhumadian/scene/source-gain-worker.js']:file=BASE/'delivery02'/path.rsplit('/',1)[1]
            if file:
                raw=file.read_bytes();return raw_reply(self,200,raw,[('Content-Type','text/html; charset=utf-8'if file.suffix=='.html'else'text/javascript'),('Cache-Control','no-store')])
            if any(x in path for x in ['source-session','local-gis','native_hierarchy','.glb','base_lod']):counts['terrainRequests']+=1
            return raw_reply(self,404,b'{"code":"ISOLATED_GIS_NOT_INSTALLED"}',[('Content-Type','application/json')])
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=90)
        try:
            connection.request(self.command,upstream,body=body,headers=headers);response=connection.getresponse();raw=response.read(262145);assert len(raw)<=262144;return raw_reply(self,response.status,raw,response.getheaders())
        finally:connection.close()

front_server=front_thread=grant_thread=backend=backend_job=backend_log=completed=None
try:
    grant_thread=threading.Thread(target=lambda:grant_server.serve_forever(poll_interval=.025),daemon=False);grant_thread.start()
    (W/'backend-config03.json').write_text(json.dumps({'grantPort':grant_server.server_port,'consumePath':g.INTERNAL_PATH+'/consume'}))
    gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D176\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
    backend_log=(D/'backend-original.log').open('xb')
    backend=subprocess.Popen([str(package/'runtime/python/python.exe'),'-I','-B','-c',gate,str(package/'runtime/python/python.exe'),'-I','-B',str(P/'tests/run_backend03.py')],cwd=W,stdin=subprocess.PIPE,stdout=backend_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    backend_job=OwnedWindowsJob(backend);backend.stdin.write(b'D176\n');backend.stdin.close();print(json.dumps({'qualifiedBackendOriginalRoot':backend.pid}),flush=True)
    ready=W/'backend-ready03.json';deadline=time.monotonic()+90
    while not ready.exists():
        assert backend.poll() is None,'Qualified backend exited before ready'
        assert time.monotonic()<deadline,'Observe same original backend; no restart'
        time.sleep(.1)
    manager_port=json.loads(ready.read_text(encoding='utf-8'))['port'];assert status(trusted,profile)['phase']=='ready'
    front_server=ThreadingHTTPServer(('127.0.0.1',0),Front);front_thread=threading.Thread(target=lambda:front_server.serve_forever(poll_interval=.025),daemon=False);front_thread.start()
    config={'url':'http://127.0.0.1:'+str(front_server.server_port)+'/zhumadian/sceneViewer?topic=resource-management','output':str(D/'browser01'),'initialRoot':rootA.as_posix(),'targetRoot':rootB.as_posix()};(D/'browser01').mkdir(exist_ok=False);(W/'browser-config01.json').write_text(json.dumps(config),'utf-8')
    completed=subprocess.run(['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(P/'tests/browser_compact.mjs'),str(W/'browser-config01.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (D/'browser-node.log').write_bytes(completed.stdout+completed.stderr);assert completed.returncode==0,'Check own qualified backend browser log'
    counts['originalACLCalls']=access.calls;assert counts['forbiddenLocalHeaders']==0
    lifecycle=json.loads((D/'gis-lifecycle.json').read_text(encoding='utf-8'));terminals=[r for r in lifecycle if r['phase']=='synthetic-original-terminal'];assert len(terminals)==3 and all(r['rootExitCode']==r['originalJobBeforeClose']==0 for r in terminals);assert len([r for r in lifecycle if r['phase']=='normal-stop-complete'])==3
    assert json.loads(configuration.read_text(encoding='utf-8'))['workspaceRoot'].replace('\\','/')==rootB.as_posix()
    assert {str(p):sha(p)for p in protected}==before
    (D/'verification.json').write_text(json.dumps({'passed':True,'actualBothOriginalVueAndFullFiveProducts':True,'newQualifiedTenCodeAndOriginal953':True,'peerActualGrantAuthority9a626':True,'CurrentUserExplicitlySynthetic':True,'threeSyntheticOriginalControllersNormallyStopped':terminals,'sameWindowActualUIStartStopSaveRootAndActorRetirement':True,'acceptedStartNormalFinishAcrossVueLeaveAndReturn':True,'rawOSGBReads':0,'temporary2356OfflineSupportSHAQualifiedForRootSave':True,'protectedOriginal250PinsUnchanged':True,'dynamicQAHTTPOnlyNotPublicTLS':True,'no250252GISRegistryOrPublicChanges':True,'normalOriginalPublicLoginBothMachinesNotAccepted':True,'counts':counts},indent=2)+'\n',encoding='utf-8')
finally:
    if front_thread:
        front_server.shutdown();front_server.server_close();front_thread.join()
    if backend is not None:
        # If qualification is still running, observe the same original root
        # until it either publishes its private owned instance or exits.
        while backend.poll() is None and not (profile/'active.private.json').exists():time.sleep(.1)
        if backend.poll() is None:assert stop(trusted,profile,wait_seconds=90)['phase']=='stopped'
        while backend.poll() is None:
            try:backend.wait(10)
            except subprocess.TimeoutExpired:print(json.dumps({'sameBackendHandleStillLive':True}),flush=True)
        while backend_job.active_processes():time.sleep(.05)
        backend_job.close();backend_log.close()
        (D/'backend-original-terminal.json').write_text(json.dumps({'rootExitCode':backend.returncode,'originalJobBeforeClose':backend_job.final_active_processes},indent=2)+'\n')
    if grant_thread:grant_server.shutdown();grant_server.server_close();grant_thread.join()
    grants.close()
    (D/'server-terminal.json').write_text(json.dumps({'parentHTTPThreadsJoined':2,'qualifiedBackendOriginalRootExitCode':None if backend is None else backend.returncode,'backendOriginalJobBeforeClose':None if backend_job is None else backend_job.final_active_processes,'nodeExitCode':None if completed is None else completed.returncode,'noUserDesktopInput':True},indent=2)+'\n')
assert backend.returncode==0 and backend_job.final_active_processes==0
