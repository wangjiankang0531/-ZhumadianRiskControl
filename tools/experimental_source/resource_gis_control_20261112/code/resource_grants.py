"""Distinct original-project management grants. No GIS-read or caller ACL fallback."""
from dataclasses import dataclass
import http.client,json,math,re,secrets,ssl,threading,time
from grant_clock import ClockBoundGrant,checked_remaining_header,deadline_after_roundtrip
ORIGIN='https://www.joinlinksmart.com'
SHA=re.compile(r'[a-f0-9]{64}')
READ='client.resources.read';WRITE='client.resources.write'
PROJECT_KEY='dc56f0196c88ed3835f9a38e7135f2594b6e99de8a400850df7b8cf9fdebaa4a'
EXPECTED={'origin','instanceId','challenge','installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity'}
RECEIPT=EXPECTED|{'accepted','scopes','actorKey','projectKey','expiresAt'}
def require(value,code):
    if not value:raise ValueError(code)
def pairs(rows):
    result={}
    for key,value in rows:
        require(key not in result,'RESOURCE_DUPLICATE_JSON_KEY');result[key]=value
    return result
def validate_descriptor(value):
    require(isinstance(value,dict)and set(value)==EXPECTED and value['origin']==ORIGIN,'RESOURCE_DESCRIPTOR_INVALID')
    require(isinstance(value['instanceId'],str)and re.fullmatch(r'[a-f0-9]{32}',value['instanceId']),'RESOURCE_DESCRIPTOR_INVALID')
    require(all(isinstance(value[k],str)and SHA.fullmatch(value[k])for k in EXPECTED-{'origin','instanceId'}),'RESOURCE_DESCRIPTOR_INVALID')
    return dict(value)
def consume_original_resource_grant(grant,expected):
    """Only this fixed TLS endpoint; the public authority is not deployed by this module."""
    validate_descriptor(expected);require(isinstance(grant,str)and SHA.fullmatch(grant),'RESOURCE_GRANT_INVALID')
    body=json.dumps({'grant':grant,'expected':expected},separators=(',',':')).encode('ascii');started=time.monotonic()
    connection=http.client.HTTPSConnection('www.joinlinksmart.com',443,timeout=10,context=ssl.create_default_context())
    try:
        connection.request('POST','/zhumadian/api/spatial-sync/v2/client-resources/grants/consume',body=body,headers={'Content-Type':'application/json','Accept':'application/json'})
        response=connection.getresponse();require(response.status==200 and response.getheader('Content-Type','').split(';')[0].strip().lower()=='application/json','RESOURCE_GRANT_CONSUME_REJECTED')
        remaining=checked_remaining_header(response.getheaders());raw=response.read(16385);require(len(raw)<=16384,'RESOURCE_GRANT_RESPONSE_TOO_LARGE')
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
        return ClockBoundGrant(value,deadline_after_roundtrip(remaining,started,time.monotonic()))
    finally:connection.close()
@dataclass(frozen=True,repr=False)
class Principal:
    actor:str
    project:str
    scopes:frozenset
    deadline:float
    @property
    def owner(self):return(self.actor,self.project)
class ResourceAuthority:
    def __init__(self,*,installation_identity,source_identity,index_identity,verifier,clock=time.monotonic,wall_clock=time.time):
        require(callable(verifier)and callable(clock)and callable(wall_clock),'RESOURCE_TRUSTED_VERIFIER_REQUIRED')
        self.expected=validate_descriptor({'origin':ORIGIN,'instanceId':secrets.token_hex(16),'challenge':secrets.token_hex(32),'installationIdentity':installation_identity,'sourceRuntimeIdentity':source_identity,'sourceIndexIdentity':index_identity})
        self.verifier=verifier;self.clock=clock;self.wall_clock=wall_clock;self.lock=threading.RLock();self.sessions={};self.closed=False;self.on_revoke=None
    def bind_revoke(self,callback):
        require(self.on_revoke is None and callable(callback),'RESOURCE_REVOKE_OWNER_REQUIRED');self.on_revoke=callback
    def discovery(self):
        return{'schema':'xnby.client-resources.discovery.v1','protocolVersion':1,**{k:v for k,v in self.expected.items()if k!='origin'},'ready':not self.closed}
    def _verified(self,grant):
        require(isinstance(grant,str)and SHA.fullmatch(grant),'RESOURCE_GRANT_INVALID');value=self.verifier(grant,dict(self.expected));now=self.clock()
        require(isinstance(value,ClockBoundGrant)and set(value)==RECEIPT and value['accepted']is True,'RESOURCE_GRANT_REJECTED')
        require(all(type(value[k])is type(v)and value[k]==v for k,v in self.expected.items()),'RESOURCE_GRANT_REJECTED')
        require(all(isinstance(value[k],str)and SHA.fullmatch(value[k])for k in ['actorKey','projectKey']),'RESOURCE_GRANT_REJECTED')
        require(value['projectKey']==PROJECT_KEY,'RESOURCE_PROJECT_REJECTED')
        scopes=value['scopes'];require(isinstance(scopes,list)and all(isinstance(x,str)for x in scopes)and len(scopes)==len(set(scopes))and READ in scopes and set(scopes)<= {READ,WRITE},'RESOURCE_SCOPE_REJECTED')
        require(type(value['expiresAt'])in(int,float)and math.isfinite(value['expiresAt'])and now<value.monotonic_deadline<=now+30,'RESOURCE_GRANT_EXPIRED')
        return Principal(value['actorKey'],value['projectKey'],frozenset(scopes),value.monotonic_deadline)
    def get(self,token,*,write=False):
        with self.lock:
            value=self.sessions.get(token)if isinstance(token,str)and SHA.fullmatch(token)else None
            valid=not self.closed and value is not None and value.deadline>self.clock()
        if not valid:
            self.revoke(token);raise ValueError('RESOURCE_SESSION_REQUIRED')
        require(not write or WRITE in value.scopes,'RESOURCE_WRITE_FORBIDDEN');return value
    def active(self,token):
        try:self.get(token);return True
        except ValueError:return False
    def _reply(self,token):
        principal=self.get(token)
        return{'schema':'xnby.client-resources.session.v1','session':token,'instanceId':self.expected['instanceId'],'expiresAt':self.wall_clock()+max(0,principal.deadline-self.clock())}
    def remaining_ms(self,token):
        return max(0,math.floor((self.get(token).deadline-self.clock())*1000))
    def establish(self,grant):
        principal=self._verified(grant)
        with self.lock:
            require(not self.closed and principal.deadline>self.clock(),'RESOURCE_SESSION_REQUIRED')
            expired=[token for token,value in self.sessions.items()if value.deadline<=self.clock()]
        for token in expired:self.revoke(token)
        with self.lock:
            require(not self.closed and len(self.sessions)<32,'RESOURCE_SESSION_LIMIT');token=secrets.token_hex(32);self.sessions[token]=principal
        return self._reply(token)
    def renew(self,token,grant):
        try:
            old=self.get(token);new=self._verified(grant)
            with self.lock:
                current=self.get(token);require(current==old and new.owner==old.owner and new.scopes==old.scopes,'RESOURCE_SESSION_BINDING_CHANGED');self.sessions[token]=new
            return self._reply(token)
        except Exception:self.revoke(token);raise
    def commit(self,token,operation):
        # This is the write linearization point, after slow filesystem qualification.
        with self.lock:self.get(token,write=True);return operation()
    def revoke(self,token):
        with self.lock:value=self.sessions.pop(token,None)if isinstance(token,str)else None
        if value is not None and self.on_revoke:self.on_revoke(token)
    def close(self):
        with self.lock:self.closed=True;tokens=list(self.sessions)
        for token in tokens:self.revoke(token)
