"""Only the registered current-user GIS. No caller command/path/PID or anonymous stop."""
from pathlib import Path
import ctypes,os,re,secrets,subprocess,threading,time
from ctypes import wintypes
from client_control import check,ordinary,load_json,atomic_json,kernel_api,same_process
from client_manifest import workspace_context,digest_file
from client_gis_runtime import current_owner,active_record,state_directory,stop as original_stop,request
from client_recovery import recover
from client_job import StateLock
from client_workspace import read_configuration,parse_document,inspect_existing
from client_settings import workspace_document

class ConfigurationReadLease:
    def __init__(self,file):
        file=ordinary(file,directory=False);self.api=kernel_api();self.handle=None
        self.api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        self.api.CreateFileW.restype=wintypes.HANDLE
        value=self.api.CreateFileW(str(file),0x80000000,1,None,3,0x80,None)
        if value==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        self.handle=value
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None

class LoginStartGate:
    def __init__(self,context):
        folder=state_directory(context);self.api=kernel_api();self.handle=None
        self.api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];self.api.CreateFileW.restype=wintypes.HANDLE
        deadline=time.monotonic()+65;file=ordinary(folder/'login-start.lock')
        while True:
            value=self.api.CreateFileW(str(file),0xC0000000,0,None,4,0x80,None)
            if value!=ctypes.c_void_p(-1).value:self.handle=value;break
            error=ctypes.get_last_error()
            if error!=32:raise ctypes.WinError(error)
            check(time.monotonic()<deadline,'GIS_LOGIN_START_BUSY');time.sleep(.1)
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None

class RootChangeGuard:
    def __init__(self,gis):
        self.gis=gis;self.gates=[];self.logs=[];self.permits_missing_root=False;self.closed=False
        doc=read_configuration(gis.configuration);inspect_existing(doc);base,_=parse_document(doc);self.old_root=Path(str(base));self.config_sha=digest_file(gis.configuration)
        self.permits_missing_root=not self.old_root.exists();gis.remember_root(self.old_root)
        try:
            for root in gis.root_snapshot():
                folder=ordinary(Path(root)/'UserData/ClientGIS')
                if folder.is_dir():self.gates.append(LoginStartGate({'state':folder}))
            self._check()
        except BaseException:self.close();raise
    def _check(self):
        check(digest_file(self.gis.configuration)==self.config_sha,'GIS_CONFIGURATION_CHANGED_AFTER_CHECK')
        state=self.gis.status();check(not state['owned']and state['phase']in ('stopped','missing-workspace'),'STOP_GIS_BEFORE_CHANGING_WORKSPACE')
        # Opening with read-sharing only proves no bootstrap stdout writer is
        # still alive at that file. Keep these handles and known-root login
        # gates through the atomic configuration commit. Never parse log text.
        for handle in self.logs:handle.close()
        self.logs=self.gis.bootstrap_read_leases()
    def commit(self,operation):
        self._check();self.gis.persist_known_roots();return operation()
    def close(self):
        if self.closed:return
        self.closed=True
        for handle in self.logs:handle.close()
        for gate in reversed(self.gates):gate.close()

class RegisteredGIS:
    def __init__(self,installation,configuration,*,expected_manifest,qa=False,port=18767,starter=None,stopper=None,history_file=None,base_override=None):
        check(qa or port==18767 and starter is None and stopper is None and base_override is None,'GIS_TEST_OVERRIDE_REQUIRES_QA')
        check(type(port)is int and 1024<=port<=65535,'GIS_REGISTERED_PORT_REQUIRED')
        self.installation=ordinary(installation,directory=True);self.configuration=ordinary(configuration);self.expected_manifest=expected_manifest
        self.port=port;self.starter=self._start_owned if starter is None else starter;self.stopper=original_stop if stopper is None else stopper
        self.cache=None;self.cache_key=None;self.cache_lock=threading.Lock();self.roots_lock=threading.Lock();self.remembered_owner=None
        self.history_file=None if history_file is None else ordinary(history_file)
        base=next((path for path in self.installation.parents if path.name.casefold()=='zhumadian'),None) if base_override is None else ordinary(base_override,directory=True)
        check(base is not None,'GIS_PROGRAMME_PROJECT_ROOT_REQUIRED');self.known_roots={str(base)}
        if self.history_file is not None and self.history_file.exists():
            history=load_json(self.history_file,32768)
            check(isinstance(history,dict)and set(history)=={'schema','installation','configuration','externalIdentity','roots'}and history['schema']=='xnby.client-resources.root-history.v1'and history['installation']==str(self.installation)and history['configuration']==str(self.configuration)and history['externalIdentity']==self.expected_manifest and isinstance(history['roots'],list)and len(history['roots'])<=64,'GIS_ROOT_HISTORY_BINDING_INVALID')
            for root in history['roots']:
                doc=workspace_document(root);inspect_existing(doc);self.known_roots.add(str(Path(doc['workspaceRoot'])))
    def remember_root(self,root):
        with self.roots_lock:self.known_roots.add(str(root))
    def root_snapshot(self):
        with self.roots_lock:return sorted(self.known_roots)
    def context(self,*,fresh=False):
        check(self.configuration.is_file(),'SAVE_WORKSPACE_FIRST')
        check(digest_file(self.installation/'client-gis-install.json')==self.expected_manifest,'GIS_REGISTERED_PROGRAMME_CHANGED')
        key=digest_file(self.configuration)
        with self.cache_lock:
            if fresh or self.cache is None or key!=self.cache_key:
                context=workspace_context(self.configuration,self.installation,verify_resources=False)
                check(context['configurationSHA256']==key,'GIS_CONFIGURATION_CHANGED_DURING_CHECK')
                self.cache=context;self.cache_key=key;self.remember_root(context['root'])
            return self.cache
    def _owner(self,context,*,allow_dead=False):
        record=active_record(context)
        if record is None:
            previous=self.remembered_owner
            if previous is not None and previous[0]==str(context['state']) and same_process(previous[1]['controller']):return{**previous[1],'phase':'stopping'}
            # An empty state file must never make a different process bound to
            # the registered port look stopped or eligible for takeover.
            try:request(self.port,'/xnby-gis/v1/discovery',headers={'Origin':'https://www.joinlinksmart.com'})
            except ConnectionRefusedError:return None
            except Exception:raise ValueError('GIS_PORT_OWNER_UNVERIFIED')
            raise ValueError('GIS_UNOWNED_INSTANCE_PRESENT')
        check(record['port']==self.port,'GIS_REGISTERED_PORT_MISMATCH');self.remembered_owner=(str(context['state']),record)
        if allow_dead and not same_process(record['controller']):return record
        return current_owner(context)
    def bootstrap_read_leases(self):
        handles=[]
        try:
            count=0
            for root in self.root_snapshot():
                folder=ordinary(Path(root)/'UserData/ClientGIS')
                if not folder.exists():continue
                for file in folder.iterdir():
                    if not re.fullmatch(r'bootstrap-[a-f0-9]{16}\.log',file.name):continue
                    count+=1;check(count<=1024,'GIS_BOOTSTRAP_HISTORY_LIMIT')
                    try:handles.append(ConfigurationReadLease(file))
                    except OSError:raise ValueError('GIS_PENDING_BOOTSTRAP_MUST_FINISH')
            return handles
        except BaseException:
            for handle in handles:handle.close()
            raise
    def persist_known_roots(self):
        if self.history_file is None:return
        roots=self.root_snapshot();check(len(roots)<=64,'GIS_ROOT_HISTORY_LIMIT')
        # Parent is the qualified manager's already private current-user state.
        atomic_json(self.history_file,{'schema':'xnby.client-resources.root-history.v1','installation':str(self.installation),'configuration':str(self.configuration),'externalIdentity':self.expected_manifest,'roots':roots})
    def begin_root_change(self):return RootChangeGuard(self)
    def status(self):
        if not self.configuration.is_file():return {'schema':'xnby.client-resources.gis-status.v1','phase':'unconfigured','owned':False}
        doc=read_configuration(self.configuration);inspect_existing(doc);base,_=parse_document(doc);self.remember_root(Path(str(base)))
        if not Path(str(base)).exists():
            try:request(self.port,'/xnby-gis/v1/discovery',headers={'Origin':'https://www.joinlinksmart.com'})
            except ConnectionRefusedError:return{'schema':'xnby.client-resources.gis-status.v1','phase':'missing-workspace','owned':False}
            except Exception:raise ValueError('GIS_PORT_OWNER_UNVERIFIED')
            raise ValueError('GIS_UNOWNED_INSTANCE_PRESENT')
        context=self.context()
        try:owner=self._owner(context)
        except ValueError as error:
            if str(error)=='CLIENT_GIS_ORIGINAL_CONTROLLER_MISSING_RECOVERY_REQUIRED':return {'schema':'xnby.client-resources.gis-status.v1','phase':'recovery-required','owned':False}
            raise
        if owner is None:
            try:
                leases=self.bootstrap_read_leases()
                for lease in leases:lease.close()
            except ValueError as error:
                if str(error)=='GIS_PENDING_BOOTSTRAP_MUST_FINISH':return{'schema':'xnby.client-resources.gis-status.v1','phase':'starting','owned':False}
                raise
        return {'schema':'xnby.client-resources.gis-status.v1','phase':'stopped'if owner is None else owner['phase'],'owned':owner is not None}
    def execute(self,action,*,commit,cancel_event,progress):
        check(action in ('start','stop') and callable(commit),'GIS_EXPLICIT_ACTION_REQUIRED')
        lease=ConfigurationReadLease(self.configuration)
        try:
            context=self.context(fresh=True);self._owner(context,allow_dead=action=='start')
            check(not cancel_event.is_set(),'RESOURCE_CONTROL_CANCELLED')
            def accept_intent():
                check(digest_file(self.configuration)==context['configurationSHA256'],'GIS_CONFIGURATION_CHANGED_AFTER_CHECK')
                check(not cancel_event.is_set(),'RESOURCE_CONTROL_CANCELLED')
                return True
            # Slow qualification precedes this point. An explicitly accepted
            # local start/stop intent normally finishes even after logout. Do
            # not hold the authorization lock across a provider startup/wait.
            commit(accept_intent)
            progress('starting'if action=='start'else'stopping')
            value=self.starter(context,progress=progress)if action=='start'else self.stopper(context)
            if action=='stop'and value.get('phase')=='stopped':
                previous=self.remembered_owner
                if previous is not None and previous[0]==str(context['state'])and same_process(previous[1]['controller']):value={'phase':'stopping','observationExpired':True}
            check(isinstance(value,dict)and value.get('phase')in ('ready','starting','stopping','stopped','recovering'),'GIS_CONTROL_RESULT_INVALID')
            return {'phase':value['phase'],'observationExpired':value.get('observationExpired')is True,
                    'alreadyRunning':value.get('alreadyRunning')is True,'registeredOwnerOnly':True}
        finally:lease.close()
    def _start_owned(self,context,*,progress):
        gate=LoginStartGate(context)
        try:
            previous=active_record(context)
            if previous is not None and not same_process(previous['controller']):
                while True:
                    progress('waiting-original-guard');value=recover(context)
                    if not value.get('observationExpired'):break
                    # Observe the same original guard; no timeout-driven new root.
            owner=self._owner(context)
            if owner is not None:return {'alreadyRunning':True,'phase':owner['phase']}
            folder=state_directory(context)
            # An old controller can finish after withdrawing discovery/state.
            # Confirm its original owner lock is released before a new spawn.
            released=StateLock(folder);released.close()
            logfile=ordinary(folder/('bootstrap-'+secrets.token_hex(8)+'.log'))
            args=[str(context['installation']/'runtime/python/python.exe'),'-I','-B',str(context['installation']/'code/client_gis_launcher.py'),'serve','--workspace-config',str(context['configuration'])]
            with logfile.open('xb')as log:
                child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            observed=time.monotonic()
            # Keep this original Popen handle through readiness. Configuration
            # remains read-leased, preventing a root edit while serve preflights.
            while True:
                if child.poll()is not None:raise ValueError('GIS_NEW_CONTROLLER_EXITED_BEFORE_READY')
                value=active_record(context)
                if value is not None:
                    owner=current_owner(context)
                    if owner['controller']['pid']!=child.pid:
                        while child.poll()is None:
                            progress('observing-concurrent-controller');time.sleep(.1)
                        other=self._owner(context);return{'phase':other['phase'],'alreadyRunning':True,'concurrentAttemptExitCode':child.returncode}
                    if owner['phase']=='ready':return {'phase':'ready','explicitControllerHandedOff':True}
                if time.monotonic()-observed>60:progress('observing-same-controller')
                time.sleep(.1)
        finally:gate.close()
