"""Pinned prepare/apply/recover adapter for the existing original-project ingress.

Only the publisher runs mutation commands. Source files, ownership, the managed
service and read-only HTTP behavior are revalidated; no process-name stop,
credentials, database writes or replacing the original app controller.
"""
import copy
import http.client
from pathlib import Path
import re
import time

from tools.layer_sync_server_owner import plain,read,sha,loads,inspect as inspect_original
from tools.layer_sync_gateway_transaction import NginxCommands,RecoveryRequired,route_candidate,checked_target,_write_new,_owner_key
from tools.layer_sync_ingress import IngressBundle,IngressProbe,proxy_candidate
from tools.layer_sync_service_owner import inspect_sync_instance
from tools.layer_sync_supervisor import encode,Lease


def capture_preflight(application,release_sha,*,original_inspector=inspect_original):
    """Fresh read-only snapshot; observations never authorize a later mutation."""
    app=plain(application);current=app/'UserData/OriginalServer/current-run.json'
    current_raw=read(current);ready=loads(current_raw.decode('utf-8-sig'))
    if not isinstance(ready,dict) or ready.get('ready') is not True:raise ValueError('READY_ORIGINAL_SERVER_REQUIRED')
    run=plain(ready['run'])
    if run.parent!=app/'UserData/OriginalServer/runs' or not re.fullmatch('j[1-9][0-9]{0,3}',run.name):
        raise ValueError('EXACT_ORIGINAL_SERVER_RUN_REQUIRED')
    release_raw=read(app/'release-manifest.json',4*1048576)
    if sha(release_raw)!=release_sha:raise ValueError('APPROVED_SERVER_RELEASE_PIN_CHANGED')
    release=loads(release_raw.decode('utf-8-sig'));nginx=run/'gateway/nginx.conf';nginx_raw=read(nginx)
    proxy=app/'iis/App_Code/XnbyReferenceProxy.cs';proxy_raw=read(proxy)
    report={'schema':'xnby.layer-sync.server-preflight.v1','passed':True,'application':str(app),'run':str(run),
            'releaseId':release['releaseId'],'ports':{name:ready[name] for name in ['gatewayPort','platformPort','businessPort']},
            'currentReadySHA256':sha(current_raw),'releaseManifestSHA256':release_sha,'nginxConfigSHA256':sha(nginx_raw)}
    owner=original_inspector(app,report)
    if owner.get('passed') is not True:raise ValueError('READ_ONLY_SERVER_OWNER_NOT_VERIFIED')
    for path,raw,limit in [(current,current_raw,1048576),(run/'ready.json',current_raw,1048576),
                           (app/'release-manifest.json',release_raw,4*1048576),(nginx,nginx_raw,1048576),(proxy,proxy_raw,1048576)]:
        if read(path,limit)!=raw:raise ValueError('SERVER_CHANGED_DURING_PREFLIGHT_CAPTURE')
    report.update(iisProxySHA256=sha(proxy_raw),ownerAtCapture=owner['identity'],deploymentPerformed=False,
                  ownershipRevalidationRequiredBeforeMutation=True,configurationServiceDatabaseAndLayerWrites=0)
    return report


class DeploymentDriver:
    def __init__(self,root,plan_sha,*,original_inspector=inspect_original,service_inspector=inspect_sync_instance,probe_factory=IngressProbe,home_probe=None):
        self.root=plain(root);raw=read(self.root/'deployment.json',131072)
        if sha(raw)!=plan_sha:raise ValueError('DEPLOYMENT_PLAN_SHA_CHANGED')
        self.params=loads(raw)
        fields={'schema','application','preflightSHA256','proxyBeforeSHA256','gatewayBeforeSHA256','nginxExecutableSHA256','origin','nonce','service','baselineIngress','baselineHome','owner','bundleSHA256'}
        if not isinstance(self.params,dict) or set(self.params)not in (fields,fields|{'projectFiles','baselineFileIngress'}) or self.params.get('schema')!='xnby.layer-sync.deployment-plan.v1':raise ValueError('EXACT_DEPLOYMENT_PLAN_REQUIRED')
        if 'projectFiles'in self.params and self.params['projectFiles']is not True:raise ValueError('EXPLICIT_PROJECT_FILES_MODE_REQUIRED')
        _owner_key(self.params['owner'])
        preflight_raw=read(self.root/'preflight.json',65536)
        if sha(preflight_raw)!=self.params['preflightSHA256']:raise ValueError('FROZEN_PREFLIGHT_CHANGED')
        self.preflight=loads(preflight_raw)
        self.proxy_before=read(self.root/'files/proxy/before.conf');self.gateway_before=read(self.root/'files/gateway/before.conf')
        self._bind(original_inspector,service_inspector,probe_factory,home_probe)
        self.bundle=IngressBundle(self.root/'files',self.params['bundleSHA256'],self._service,self.proxy_handlers,self.gateway_handlers)
        if self.bundle.proxy.app!=self.app or self.bundle.proxy.config!=self.proxy or self.bundle.gateway.config!=self.gateway:
            raise ValueError('DEPLOYMENT_TARGET_BINDING_CHANGED')

    @classmethod
    def prepare(cls,root,application,preflight_raw,preflight_sha,proxy_sha,service,nginx_sha,origin,nonce,*,
                original_inspector=inspect_original,service_inspector=inspect_sync_instance,probe_factory=IngressProbe,home_probe=None,project_files=False):
        if type(project_files)is not bool:raise ValueError('EXPLICIT_PROJECT_FILES_MODE_REQUIRED')
        root,app=map(plain,(root,application))
        if root.exists():raise ValueError('NEW_DEPLOYMENT_ROOT_REQUIRED')
        if sha(preflight_raw)!=preflight_sha:raise ValueError('PREFLIGHT_PIN_CHANGED')
        preflight=loads(preflight_raw)
        obj=cls.__new__(cls);obj.root=root;obj.preflight=preflight
        proxy=app/'iis/App_Code/XnbyReferenceProxy.cs';gateway=plain(preflight['run'])/'gateway/nginx.conf'
        if plain(preflight['application'])!=app:raise ValueError('DEPLOYMENT_APPLICATION_CHANGED')
        checked_target(app,proxy,root/'files/proxy','iis-header');checked_target(app,gateway,root/'files/gateway','gateway')
        obj.proxy_before=read(proxy);obj.gateway_before=read(gateway)
        if sha(obj.proxy_before)!=proxy_sha or sha(obj.gateway_before)!=preflight['nginxConfigSHA256']:raise ValueError('DEPLOYMENT_PREIMAGE_CHANGED')
        obj.params={'schema':'xnby.layer-sync.deployment-plan.v1','application':str(app),'preflightSHA256':preflight_sha,
                    'proxyBeforeSHA256':proxy_sha,'gatewayBeforeSHA256':preflight['nginxConfigSHA256'],
                    'nginxExecutableSHA256':nginx_sha,'origin':origin,'nonce':nonce,'service':service}
        if project_files:obj.params['projectFiles']=True
        obj._bind(original_inspector,service_inspector,probe_factory,home_probe)
        proof=obj._service();obj.proxy_after=proxy_candidate(obj.proxy_before,proxy_sha);obj.gateway_after=route_candidate(obj.gateway_before,proof['port'],nonce,project_files=project_files)
        owner=obj._owner('proxy',proxy_sha);obj.params['owner']=_owner_key(owner)
        baseline=obj.probe.sample(nonce);home=obj._home()
        if baseline['tagPresent'] or home['status']!=200:raise ValueError('ORIGINAL_INGRESS_BASELINE_NOT_READY')
        if project_files:
            file_baseline=obj.probe.sample_files(nonce)
            if file_baseline['tagPresent']:raise ValueError('PROJECT_FILE_INGRESS_ALREADY_INSTALLED')
            obj.params['baselineFileIngress']=file_baseline
        obj.params.update(baselineIngress=baseline,baselineHome=home)
        root.mkdir(parents=True);_write_new(root/'preflight.json',preflight_raw)
        bundle=IngressBundle.prepare(app,proxy,gateway,root/'files',proxy_sha,preflight['nginxConfigSHA256'],obj.proxy_after,obj.gateway_after,nonce,obj._service,obj.proxy_handlers,obj.gateway_handlers,project_files=project_files)
        obj.params['bundleSHA256']=sha(read(root/'files/bundle.json',65536));raw=encode(obj.params);_write_new(root/'deployment.json',raw)
        return cls(root,sha(raw),original_inspector=original_inspector,service_inspector=service_inspector,probe_factory=probe_factory,home_probe=home_probe)

    def _bind(self,original_inspector,service_inspector,probe_factory,home_probe):
        p=self.params;self.app=plain(p['application']);self.proxy=self.app/'iis/App_Code/XnbyReferenceProxy.cs';self.gateway=plain(self.preflight['run'])/'gateway/nginx.conf'
        if (sha(self.proxy_before)!=p['proxyBeforeSHA256'] or sha(self.gateway_before)!=p['gatewayBeforeSHA256']
                or not isinstance(p['nonce'],str) or not re.fullmatch('[0-9a-f]{32}',p['nonce'])
                or not re.fullmatch('[0-9a-f]{64}',p['nginxExecutableSHA256'])):raise ValueError('EXACT_DEPLOYMENT_IMAGES_AND_NONCE_REQUIRED')
        self.original_inspector=original_inspector;self.service_inspector=service_inspector;self.probe=probe_factory(p['origin']);self.home_probe=home_probe
        self.proxy_after=proxy_candidate(self.proxy_before,p['proxyBeforeSHA256'])
        s=p['service']
        expected={'controlRoot','codeRoot','configPath','configSHA256','manifestSHA256','dataRoot','pythonExecutable','listenPort'}
        if not isinstance(s,dict) or set(s)!=expected:raise ValueError('EXPLICIT_DEPLOYMENT_SERVICE_BINDING_REQUIRED')
        self.gateway_after=route_candidate(self.gateway_before,s['listenPort'],p['nonce'],project_files=p.get('projectFiles',False))
        commands=NginxCommands(self.app/'runtime/nginx/nginx.exe',p['nginxExecutableSHA256'],self.gateway.parent,self.gateway,lambda:self._owner('gateway',sha(read(self.gateway))))
        self.proxy_handlers={'probe':lambda expected:self._owner('proxy',expected),'syntax':lambda path:read(path) in (self.proxy_before,self.proxy_after),
                             'activate':lambda:read(self.proxy) in (self.proxy_before,self.proxy_after),
                             'live':lambda mode,nonce:self._wait(lambda:self._home()==self.params['baselineHome'])}
        self.gateway_handlers={'probe':lambda expected:self._owner('gateway',expected),'syntax':commands.syntax,'activate':commands.reload,
                               'live':lambda mode,nonce:self._wait(lambda:self._ingress_live(mode,nonce) and self._home()==self.params['baselineHome'])}
    def _ingress_live(self,mode,nonce):
        if mode=='installed':return self.probe.installed(nonce)and(not self.params.get('projectFiles',False)or self.probe.files_installed(nonce))
        return self.probe.restored(nonce,self.params['baselineIngress'])and(not self.params.get('projectFiles',False)or self.probe.sample_files(nonce)==self.params['baselineFileIngress'])
    def _service(self):
        s=self.params['service']
        # The public invalid-auth probe distinguishes missing binding only with
        # this approved backend revision. Do not mix the older24-source worker
        # with this deployment driver and accidentally accept a false positive.
        try:
            expected=read(Path(__file__).resolve().parents[1]/'services/layer_sync_server.py')
            actual=read(plain(s['codeRoot'])/'services/layer_sync_server.py')
            if sha(actual)!=sha(expected):raise ValueError('backend revision differs')
        except (OSError,ValueError):raise RecoveryRequired('ACCOUNT_BOUND_PREFLIGHT_BACKEND_REQUIRED') from None
        if self.params.get('projectFiles',False):
            try:
                config_raw=read(plain(s['configPath']),32768)
                if sha(config_raw)!=s['configSHA256']:raise ValueError('config differs')
                config=loads(config_raw);file_root=config.get('projectFilesRoot')
                if not isinstance(file_root,str)or not Path(file_root).is_absolute():raise ValueError('private root missing')
                file_root=plain(file_root);code_root=plain(s['codeRoot'])
                if file_root.is_relative_to(self.app)or self.app.is_relative_to(file_root)or file_root.is_relative_to(code_root)or code_root.is_relative_to(file_root):raise ValueError('project files overlap application or code')
                for name in ['project_files.py','project_files_api.py']:
                    expected=read(Path(__file__).resolve().parents[1]/'services'/name);actual=read(plain(s['codeRoot'])/'services'/name)
                    if sha(expected)!=sha(actual):raise ValueError('file backend differs')
            except(OSError,ValueError):raise RecoveryRequired('PROJECT_FILE_LIBRARY_BACKEND_AND_PRIVATE_ROOT_REQUIRED')from None
        proof=self.service_inspector(s['controlRoot'],s['codeRoot'],s['configPath'],s['configSHA256'],s['manifestSHA256'],s['dataRoot'],s['pythonExecutable'])
        if proof['port']!=s['listenPort']:raise RecoveryRequired('DEPLOYMENT_SYNC_LISTENER_CHANGED')
        return proof
    def _owner(self,kind,expected):
        gateway_sha=sha(read(self.gateway));proxy_sha=sha(read(self.proxy))
        if gateway_sha not in (sha(self.gateway_before),sha(self.gateway_after)) or proxy_sha not in (sha(self.proxy_before),sha(self.proxy_after)):
            raise RecoveryRequired('FOREIGN_INGRESS_BYTES_RETAINED')
        if (proxy_sha if kind=='proxy' else gateway_sha)!=expected:raise RecoveryRequired('INGRESS_PREIMAGE_CHANGED')
        snapshot=copy.deepcopy(self.preflight);snapshot['nginxConfigSHA256']=gateway_sha
        # Only the two approved nginx images may replace this one snapshot field.
        # Release/current-run/ready/ports/PIDs are always checked against the
        # original frozen preflight by the actual Win32/CIM owner inspector.
        result=self.original_inspector(self.app,snapshot)
        if result.get('passed') is not True:raise RecoveryRequired('ORIGINAL_GATEWAY_OWNERSHIP_NOT_VERIFIED')
        if 'owner' in self.params and _owner_key(result['identity'])!=self.params['owner']:
            raise RecoveryRequired('PINNED_ORIGINAL_GATEWAY_OWNER_CHANGED')
        return result['identity']
    def _home(self):
        if self.home_probe is not None:return self.home_probe()
        factory=http.client.HTTPSConnection if self.probe.tls else http.client.HTTPConnection
        conn=factory(self.probe.host,self.probe.port,timeout=8)
        try:
            conn.request('GET','/zhumadian/',headers={'Cache-Control':'no-store','Accept':'text/html'});response=conn.getresponse();raw=response.read(1048577)
            if len(raw)>1048576:raise ValueError('BOUNDED_ORIGINAL_HOME_REQUIRED')
            return {'status':response.status,'bodySHA256':sha(raw)}
        finally:conn.close()
    @staticmethod
    def _wait(check):
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            try:
                if check():return True
            except (OSError,http.client.HTTPException):pass
            time.sleep(.1)
        return False
    def apply(self):
        root=plain(self.app/'UserData/LayerSyncIngressControl');root.mkdir(exist_ok=True)
        with Lease(root/'owner.lock'):return self.bundle.apply()
    def recover(self):
        root=plain(self.app/'UserData/LayerSyncIngressControl');root.mkdir(exist_ok=True)
        with Lease(root/'owner.lock'):return self.bundle.recover()
