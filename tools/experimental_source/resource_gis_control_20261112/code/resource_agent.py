"""Independent current-user manager; explicit registered GIS intents may outlive it."""
from pathlib import Path
import hashlib,http.client,json,os,re,secrets,subprocess,threading,time
from client_control import atomic_json,check,load_json,ordinary,private_directory,process_identity,same_process
from client_settings import default_profile_folder
from client_job import StateLock
from resource_grants import ResourceAuthority,consume_original_resource_grant,ORIGIN
from resource_reports import OwnedReports
from resource_service import ResourceManager
from resource_http import ResourceHTTPServer
from qualified_settings import QualifiedResourceSettings
from registered_gis import RegisteredGIS

KEYS={'schema','runId','controller','installation','installationIdentity','externalInstallation','externalIdentity','port','phase','instanceId','stopSecret'}

def profile_folder():return ordinary(default_profile_folder().parent/'ClientResources')

def binding(trusted):
    return {'installationIdentity':trusted['manifestSHA256'],'sourceRuntimeIdentity':trusted['dependency']['sourceRuntimeIdentity'],
            'sourceIndexIdentity':trusted['dependency']['sourceIndexIdentity']}

def active(trusted,folder):
    file=ordinary(folder/'active.private.json')
    if not file.exists():return None
    value=load_json(file)
    check(isinstance(value,dict) and set(value)==KEYS and value['schema']=='xnby.client-resources.active.v1','UNKNOWN_RESOURCE_AGENT_OWNER')
    check(isinstance(value['runId'],str) and re.fullmatch('[a-f0-9]{32}',value['runId']) and
        isinstance(value['stopSecret'],str) and re.fullmatch('[a-f0-9]{64}',value['stopSecret']),'UNKNOWN_RESOURCE_AGENT_OWNER')
    check(Path(value['installation'])==trusted['folder'] and value['installationIdentity']==trusted['manifestSHA256'] and
        Path(value['externalInstallation'])==trusted['installation'] and value['externalIdentity']==trusted['registration']['GISInstallSHA256'],
        'DIFFERENT_RESOURCE_AGENT_INSTALLATION_ACTIVE')
    check(type(value['port']) is int and 1024<=value['port']<=65535 and value['phase'] in ('ready','stopping') and
        isinstance(value['instanceId'],str) and re.fullmatch('[a-f0-9]{32}',value['instanceId']),'UNKNOWN_RESOURCE_AGENT_OWNER')
    expected=value['controller'];check(isinstance(expected,dict) and set(expected)=={'pid','created100ns','image'} and
        any(os.path.normcase(expected['image'])==os.path.normcase(str(trusted['installation']/name)) for name in ('runtime/python/python.exe','runtime/python/pythonw.exe')),
        'UNKNOWN_RESOURCE_AGENT_PROCESS_IMAGE')
    return value

def get_discovery(port):
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
    try:
        connection.request('GET','/xnby-client-resources/v1/discovery',headers={'Origin':ORIGIN})
        response=connection.getresponse();raw=response.read(16385)
        check(response.status==200 and len(raw)<=16384,'RESOURCE_AGENT_DISCOVERY_FAILED')
        return json.loads(raw)
    finally:connection.close()

def live_owner(trusted,folder):
    owner=active(trusted,folder)
    if owner is None:return None
    check(same_process(owner['controller']),'RESOURCE_AGENT_ORPHANED_RECOVERY_REQUIRED')
    if owner['phase']=='ready':
        public=get_discovery(owner['port'])
        check(public.get('ready') is True and public.get('instanceId')==owner['instanceId'] and
            all(public.get(k)==v for k,v in binding(trusted).items()),'RESOURCE_AGENT_LIVE_IDENTITY_MISMATCH')
    return owner

def status(trusted,folder):
    owner=live_owner(trusted,folder)
    return {'phase':'stopped','ownedActiveController':False} if owner is None else {
        'phase':owner['phase'],'ownedActiveController':True,'pid':owner['controller']['pid'],'port':owner['port']}

def recover(trusted,folder):
    folder=ordinary(folder,directory=True);lock=StateLock(folder)
    try:
        owner=active(trusted,folder)
        if owner is None:return {'phase':'stopped','recovered':False}
        check(not same_process(owner['controller']),'LIVE_RESOURCE_AGENT_RECOVERY_REFUSED')
        # Explicit registered GIS starts use the original durable GIS controller
        # and can outlive this manager. Recover only this manager record;
        # never reap/restart the GIS or claim its Job/normal terminal here.
        import socket
        probe=socket.socket();probe.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        try:probe.bind(('127.0.0.1',owner['port']))
        finally:probe.close()
        check(load_json(folder/'active.private.json')==owner,'RESOURCE_AGENT_OWNER_CHANGED')
        result={'schema':'xnby.client-resources.orphan-observation.v1','runId':owner['runId'],
            'originalProcessMissing':True,'previousNormalExitProved':False,'previousJobZeroProved':False,
            'separatelyOwnedGISMayOutliveManager':True,'GISStoppedOrReaped':False,'portWasFree':True,'forceTerminationUsed':False}
        run=ordinary(folder/'runs'/owner['runId'],directory=True)
        atomic_json(run/'orphan-observation.json',result,replace=False)
        (folder/'active.private.json').unlink()
        return {'phase':'stopped','recovered':True,'previousNormalExitProved':False}
    finally:lock.close()

def stop(trusted,folder,*,wait_seconds=60):
    owner=live_owner(trusted,folder)
    if owner is None:return {'phase':'stopped','ownedActiveController':False}
    run=ordinary(folder/'runs'/owner['runId'],directory=True)
    atomic_json(run/'stop.request.json',{'schema':'xnby.client-resources.stop.v1','runId':owner['runId'],'stopSecret':owner['stopSecret']})
    deadline=time.monotonic()+wait_seconds
    while same_process(owner['controller']):
        if time.monotonic()>=deadline:return {'phase':'stopping','observationExpired':True,'sameControllerPreserved':True,'pid':owner['controller']['pid']}
        time.sleep(.05)
    terminal=load_json(run/'terminal.json')
    check(terminal.get('runId')==owner['runId'] and terminal.get('allThreadsJoined') is True and terminal.get('passed') is True,
        'RESOURCE_AGENT_TERMINAL_INCOMPLETE')
    return {'phase':'stopped','ownedActiveController':False,'terminal':terminal}

class ResourceAgent:
    def __init__(self,trusted,*,folder=None,port=18768,qa=False,verifier=None):
        check(port==18768 or qa is True,'RESOURCE_FIXED_PORT_REQUIRED')
        check(verifier is None or qa is True,'RESOURCE_VERIFIER_OVERRIDE_REQUIRES_QA')
        self.trusted=trusted;self.folder=profile_folder() if folder is None else ordinary(folder)
        self.port=port;self.qa=qa;self.verifier=consume_original_resource_grant if verifier is None else verifier
        self.manager=self.server=self.http_thread=self.lock=self.owner=self.run=None;self.owns=False;self.completed_normally=False
    def requested(self):
        file=self.run/'stop.request.json'
        if not file.exists():return False
        value=load_json(file)
        return isinstance(value,dict) and set(value)=={'schema','runId','stopSecret'} and value['schema']=='xnby.client-resources.stop.v1' and value['runId']==self.owner['runId'] and secrets.compare_digest(str(value['stopSecret']),self.owner['stopSecret'])
    def serve(self,*,ready_callback=None):
        self.folder.mkdir(parents=True,exist_ok=True);private_directory(self.folder);self.lock=StateLock(self.folder)
        try:
            check(active(self.trusted,self.folder) is None,'RESOURCE_AGENT_ALREADY_ACTIVE_OR_RECOVERY_REQUIRED')
            data=binding(self.trusted);authority=ResourceAuthority(installation_identity=data['installationIdentity'],source_identity=data['sourceRuntimeIdentity'],index_identity=data['sourceIndexIdentity'],verifier=self.verifier)
            gis=RegisteredGIS(self.trusted['installation'],self.trusted['configuration'],expected_manifest=self.trusted['registration']['GISInstallSHA256'],history_file=self.folder/'gis-workspace-history.json')
            settings=QualifiedResourceSettings(self.trusted['installation'],self.trusted['configuration'],gis=gis)
            reports=OwnedReports(self.folder/'reports',binding=data)
            self.manager=ResourceManager(authority=authority,settings=settings,reports=reports,gis=gis)
            self.server=ResourceHTTPServer(self.manager,port=self.port,qa=self.qa)
            self.run=ordinary(self.folder/'runs'/secrets.token_hex(16));self.run.mkdir(parents=True);private_directory(self.run)
            self.owner={'schema':'xnby.client-resources.active.v1','runId':self.run.name,'controller':process_identity(os.getpid()),
                'installation':str(self.trusted['folder']),'installationIdentity':data['installationIdentity'],
                'externalInstallation':str(self.trusted['installation']),'externalIdentity':self.trusted['registration']['GISInstallSHA256'],
                'port':self.server.server_port,'phase':'ready','instanceId':authority.expected['instanceId'],'stopSecret':secrets.token_hex(32)}
            self.http_thread=threading.Thread(target=self.server.serve_forever,name='XNBY-Resources-HTTP',daemon=False);self.http_thread.start()
            atomic_json(self.folder/'active.private.json',self.owner,replace=False);self.owns=True
            if ready_callback:ready_callback(self.owner['port'])
            while not self.requested():time.sleep(.05)
            self.completed_normally=True
            return {'phase':'stopped','normalStop':True}
        finally:
            try:
                if self.manager:self.manager.close()
                if self.http_thread:self.server.shutdown();self.http_thread.join()
                if self.server:self.server.server_close()
                if self.owns:
                    terminal={'schema':'xnby.client-resources.terminal.v1','runId':self.owner['runId'],'passed':self.completed_normally,
                        'allThreadsJoined':True,'separateRegisteredGISPreserved':True,'forceTerminationUsed':False}
                    atomic_json(self.run/'terminal.json',terminal,replace=False)
                    check(load_json(self.folder/'active.private.json')==self.owner,'RESOURCE_AGENT_OWNER_CHANGED')
                    (self.folder/'active.private.json').unlink();atomic_json(self.folder/'latest-terminal.json',terminal)
            finally:
                if self.lock:self.lock.close()

def start(trusted,folder):
    owner=active(trusted,folder)
    if owner is not None:
        if not same_process(owner['controller']):recover(trusted,folder)
        else:return {**status(trusted,folder),'alreadyRunning':True}
    folder.mkdir(parents=True,exist_ok=True);private_directory(folder)
    logfile=folder/('bootstrap-'+secrets.token_hex(8)+'.log')
    args=[str(trusted['installation']/'runtime/python/python.exe'),'-I','-B',str(trusted['folder']/'code/entry.py'),'serve']
    with logfile.open('xb') as log:
        child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+60
    while True:
        owner=active(trusted,folder)
        if owner is not None:
            result=status(trusted,folder)
            if result['phase']=='ready':
                if owner['controller']['pid']==child.pid:return {**result,'createdControllerPID':child.pid}
                while child.poll() is None:time.sleep(.05)
                return {**result,'alreadyRunning':True,'concurrentCandidateExitCode':child.returncode}
        if child.poll() is not None:raise ValueError('RESOURCE_AGENT_START_EXITED:'+str(child.returncode))
        if time.monotonic()>=deadline:return {'phase':'starting','pid':child.pid,'observationExpired':True,'sameControllerPreserved':True}
        time.sleep(.1)

def command(trusted,action):
    folder=profile_folder()
    if action=='check':return {'passed':True,'programmeQualified':True,'managementPort':18768,'GISAssetsRequired':False,
        'managerInstallationIdentity':trusted['manifestSHA256'],'GISDependencyFiles':trusted['programFiles'],'resourceHTTPStarted':False,'configurationExists':trusted['configuration'].is_file()}
    if action=='serve':return ResourceAgent(trusted).serve()
    if action=='status':return status(trusted,folder)
    if action=='stop':return stop(trusted,folder)
    if action=='recover':return recover(trusted,folder)
    if action=='start':return start(trusted,folder)
    raise ValueError('RESOURCE_AGENT_COMMAND_INVALID')
