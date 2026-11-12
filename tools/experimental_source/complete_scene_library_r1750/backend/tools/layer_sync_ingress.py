"""Exact IIS header patch, read-only ingress probe and two-file deployment journal.

No default server addresses/ports, hidden login, schema migration or public
installation. Publisher supplies fresh gateway ownership and activation probes.
"""
import http.client
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from tools.layer_sync_server_owner import plain,read,loads,sha
from tools.layer_sync_gateway_transaction import GatewayTransaction,RecoveryRequired,_journal,_write_new,route_candidate
from tools.layer_sync_supervisor import Lease,encode

HEADER='X-XNBY-Sync-Account'
ANCHOR=b'foreach (string name in new string[]{"Authorization","Cookie","Origin",'


def proxy_candidate(original,expected_sha):
    if not isinstance(original,bytes) or len(original)>1048576 or sha(original)!=expected_sha:
        raise ValueError('EXACT_IIS_PREIMAGE_REQUIRED')
    if HEADER.encode() in original:raise ValueError('EXISTING_IIS_BINDING_REQUIRES_EXPLICIT_REVIEW')
    if original.count(ANCHOR)!=1:raise ValueError('EXACT_IIS_FORWARD_LIST_REQUIRED')
    return original.replace(ANCHOR,ANCHOR+b'"'+HEADER.encode()+b'",',1)


class IngressProbe:
    """GET with deliberately invalid synthetic auth: never a login or write."""
    def __init__(self,origin):
        parsed=urlsplit(origin)
        if origin=='https://www.joinlinksmart.com':
            self.tls=True;self.host=parsed.hostname;self.port=443
        elif (isinstance(origin,str) and re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}',origin)
              and 1024<=parsed.port<=65535):
            self.tls=False;self.host='127.0.0.1';self.port=parsed.port
        else:raise ValueError('EXACT_PUBLIC_OR_LOOPBACK_INGRESS_REQUIRED')
    def sample(self,nonce):return self._sample(nonce,'/zhumadian/api/spatial-sync/v2/project/layers')
    def sample_files(self,nonce):return self._sample(nonce,'/zhumadian/api/spatial-sync/v2/project/files')
    def _sample(self,nonce,path):
        if not isinstance(nonce,str) or not re.fullmatch('[0-9a-f]{32}',nonce):raise ValueError('EXACT_INGRESS_NONCE_REQUIRED')
        factory=http.client.HTTPSConnection if self.tls else http.client.HTTPConnection
        conn=factory(self.host,self.port,timeout=8)
        try:
            conn.request('GET',path,
                         headers={'Authorization':'XNBY-INGRESS-PROBE-'+nonce,HEADER:'0'*64,'Accept':'application/json','Cache-Control':'no-store'})
            response=conn.getresponse();raw=response.read(8193)
            if len(raw)>8192:raise ValueError('BOUNDED_INGRESS_PROBE_REQUIRED')
            tag=response.getheader('X-XNBY-Layer-Sync-Deployment');error=None
            try:
                value=loads(raw)
                if isinstance(value,dict) and set(value)=={'error'} and value['error'] in ('LOGIN_REQUIRED','ACCOUNT_BINDING_REQUIRED','ACCOUNT_BINDING_MISMATCH'):error=value['error']
            except (ValueError,TypeError):pass
            return {'status':response.status,'bodySHA256':sha(raw),'tagPresent':tag is not None,
                    'tag':tag if isinstance(tag,str) and re.fullmatch('[0-9a-f]{32}',tag) else None,'error':error}
        finally:conn.close()
    def installed(self,nonce):
        value=self.sample(nonce)
        return value['status']==401 and value['error']=='LOGIN_REQUIRED' and value['tag']==nonce
    def files_installed(self,nonce):
        value=self.sample_files(nonce)
        return value['status']==401 and value['error']=='LOGIN_REQUIRED' and value['tag']==nonce
    def restored(self,nonce,baseline):return self.sample(nonce)==baseline


def checked_service(value):
    fields={'schema','controller','worker','port','instanceId','configSHA256','manifestSHA256'}
    if not isinstance(value,dict) or set(value)!=fields or value['schema']!='xnby.layer-sync.deployment-service.v1':
        raise ValueError('EXACT_LIVE_SYNC_SERVICE_PROOF_REQUIRED')
    for name in ['controller','worker']:
        item=value[name]
        if (not isinstance(item,dict) or set(item)!={'pid','creation'} or type(item['pid']) is not int or not 0<item['pid']<2**32
                or not isinstance(item['creation'],str) or not re.fullmatch('[0-9]{1,20}',item['creation'])):
            raise ValueError('EXACT_LIVE_SYNC_PROCESS_REQUIRED')
    if type(value['port']) is not int or not 1024<=value['port']<=65535 or not re.fullmatch('[0-9a-f]{32}',value['instanceId']):
        raise ValueError('EXACT_LIVE_SYNC_SERVICE_PROOF_REQUIRED')
    for name in ['configSHA256','manifestSHA256']:
        if not isinstance(value[name],str) or not re.fullmatch('[0-9a-f]{64}',value[name]):raise ValueError('EXACT_LIVE_SYNC_SERVICE_PIN_REQUIRED')
    return value


class IngressBundle:
    """IIS first, gateway second; explicit recovery reverses that order.

    Handler dictionaries require current probe/syntax/activate/live callables.
    The gateway installed live callback must check the full IIS->gateway->V2
    path, including nonce and the deliberately invalid auth response, plus the
    original site's health. Recovery live checks original baseline behavior.
    """
    def __init__(self,root,plan_sha,service_probe,proxy_handlers,gateway_handlers):
        self.root=plain(root);raw=read(self.root/'bundle.json',65536)
        if sha(raw)!=plan_sha:raise ValueError('INGRESS_BUNDLE_PLAN_CHANGED')
        self.plan=loads(raw)
        if (not isinstance(self.plan,dict) or set(self.plan)not in ({'schema','proxyPlanSHA256','gatewayPlanSHA256','service'},{'schema','proxyPlanSHA256','gatewayPlanSHA256','service','projectFiles'})
                or self.plan['schema']!='xnby.layer-sync.ingress-bundle.v1'):
            raise ValueError('INVALID_INGRESS_BUNDLE')
        if 'projectFiles'in self.plan and self.plan['projectFiles']is not True:raise ValueError('EXPLICIT_PROJECT_FILES_MODE_REQUIRED')
        checked_service(self.plan['service'])
        self.service_probe=service_probe
        def transaction(name,pin,handlers):
            if set(handlers)!={'probe','syntax','activate','live'} or not all(callable(f) for f in handlers.values()):raise ValueError('EXPLICIT_INGRESS_HANDLERS_REQUIRED')
            return GatewayTransaction(self.root/name,pin,handlers['probe'],handlers['syntax'],handlers['activate'],handlers['live'])
        self.proxy=transaction('proxy',self.plan['proxyPlanSHA256'],proxy_handlers)
        self.gateway=transaction('gateway',self.plan['gatewayPlanSHA256'],gateway_handlers)
        if self.proxy.plan['kind']!='iis-header' or self.gateway.plan['kind']!='gateway' or self.proxy.app!=self.gateway.app or self.proxy.plan['owner']!=self.gateway.plan['owner']:
            raise ValueError('CONSISTENT_INGRESS_APPLICATION_AND_OWNER_REQUIRED')
        self.status=loads(read(self.root/'bundle-journal.json',65536))
        if not isinstance(self.status,dict) or self.status.get('planSHA256')!=plan_sha:raise ValueError('INGRESS_BUNDLE_JOURNAL_CHANGED')
    @classmethod
    def prepare(cls,application,proxy_path,gateway_path,root,proxy_sha,gateway_sha,proxy_after,gateway_after,nonce,
                service_probe,proxy_handlers,gateway_handlers,*,project_files=False):
        if type(project_files)is not bool:raise ValueError('EXPLICIT_PROJECT_FILES_MODE_REQUIRED')
        root=plain(root)
        if root.exists():raise ValueError('NEW_INGRESS_BUNDLE_ROOT_REQUIRED')
        service=checked_service(service_probe())
        if proxy_after!=proxy_candidate(read(proxy_path),proxy_sha):
            raise ValueError('EXACT_ACCOUNT_HEADER_INSERTION_REQUIRED')
        before=read(gateway_path)
        if sha(before)!=gateway_sha or gateway_after!=route_candidate(before,service['port'],nonce,project_files=project_files):
            raise ValueError('EXACT_BOUND_SYNC_ROUTES_REQUIRED')
        root.mkdir(parents=True)
        proxy=GatewayTransaction.prepare(application,proxy_path,root/'proxy',proxy_sha,proxy_after,nonce,
                                        proxy_handlers['probe'],proxy_handlers['syntax'],proxy_handlers['activate'],proxy_handlers['live'],kind='iis-header')
        gateway=GatewayTransaction.prepare(application,gateway_path,root/'gateway',gateway_sha,gateway_after,nonce,
                                          gateway_handlers['probe'],gateway_handlers['syntax'],gateway_handlers['activate'],gateway_handlers['live'])
        if service!=checked_service(service_probe()):raise RecoveryRequired('SYNC_SERVICE_CHANGED_DURING_PLAN')
        plan={'schema':'xnby.layer-sync.ingress-bundle.v1','proxyPlanSHA256':sha(read(root/'proxy/plan.json',65536)),
              'gatewayPlanSHA256':sha(read(root/'gateway/plan.json',65536)),'service':service}
        if project_files:plan['projectFiles']=True
        raw=encode(plan);_write_new(root/'bundle.json',raw);_journal(root/'bundle-journal.json',{'schema':'xnby.layer-sync.ingress-bundle-journal.v1','planSHA256':sha(raw),'phase':'prepared'})
        return cls(root,sha(raw),service_probe,proxy_handlers,gateway_handlers)
    def _save(self,phase):
        self.status['phase']=phase;_journal(self.root/'bundle-journal.json',self.status)
    def _current(self):
        if loads(read(self.root/'bundle-journal.json',65536))!=self.status:raise RecoveryRequired('INGRESS_BUNDLE_ADVANCED_REOPEN_REQUIRED')
    def _service(self):
        if checked_service(self.service_probe())!=self.plan['service']:raise RecoveryRequired('LIVE_SYNC_SERVICE_CHANGED')
    def apply(self):
        with Lease(self.root/'bundle.lock'):
            self._current()
            if self.status['phase']!='prepared':raise ValueError('PREPARED_INGRESS_BUNDLE_REQUIRED')
            try:
                self._service();self.proxy.apply();self._save('proxy-candidate-healthy')
                self._service();self.gateway.apply();self._service();self._save('validated')
                return dict(self.status)
            except RecoveryRequired:
                self._save('recovery-required');raise
            except Exception:
                self._recover();raise
    def recover(self):
        with Lease(self.root/'bundle.lock'):
            self._current();return self._recover()
    def _recover(self):
        try:
            self.gateway.recover();self._save('gateway-restored')
            self.proxy.recover();self._save('restored')
            return dict(self.status)
        except Exception:
            self._save('recovery-required');raise
