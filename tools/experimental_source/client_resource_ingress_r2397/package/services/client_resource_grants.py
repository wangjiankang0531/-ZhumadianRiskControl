"""Separate, opt-in resource-management capability authority.

The owning project server supplies its original access checker and the fixed
qualified management package descriptors. Import creates no listener or files.
This module never changes the existing gis.read authority or its semantics.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import secrets
import threading
import time
from services.layer_sync_identity import account_key

ORIGIN='https://www.joinlinksmart.com'
PROJECT_URI=ORIGIN+'/zhumadian/'
PROJECT_KEY=hashlib.sha256(json.dumps(['xnby.client-resources.project.v1',PROJECT_URI],ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()
PUBLIC_PATH='/zhumadian/api/spatial-sync/v2/client-resources/grants'
INTERNAL_PATH='/v2/client-resources/grants'
REMAINING_HEADER='X-XNBY-Local-GIS-Remaining-Ms'
READ='client.resources.read'
WRITE='client.resources.write'
IDENTITIES=('installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity')
EXPECTED_FIELDS={'origin','instanceId','challenge',*IDENTITIES}

class GrantError(Exception):
    def __init__(self,status,code):
        self.status,self.code=status,code
        super().__init__(code)

def require(value,status,code):
    if not value: raise GrantError(status,code)

def hex_value(value,length):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(length)+'}',value) is not None

def checked_expected(value):
    require(isinstance(value,dict) and set(value)==EXPECTED_FIELDS,400,'RESOURCE_EXPECTED_FIELDS_REQUIRED')
    require(value['origin']==ORIGIN and hex_value(value['instanceId'],32) and hex_value(value['challenge'],64)
            and all(hex_value(value[k],64) for k in IDENTITIES),400,'RESOURCE_EXPECTED_INVALID')
    return dict(value)

def loads(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result: raise ValueError('DUPLICATE_JSON_FIELD')
            result[key]=value
        return result
    return json.loads(raw.decode('utf8'),object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))

class _Receipt(dict):
    __slots__=('_deadline','_tag')
    def __init__(self,value,deadline,tag):
        super().__init__(value)
        self._deadline,self._tag=deadline,tag

class ClientResourceGrantAuthority:
    def __init__(self,access,allowed_installations,*,clock=time.time,monotonic_clock=time.monotonic,grant_seconds=30,session_seconds=30,capacity=256):
        require(callable(getattr(access,'check',None)) and callable(clock) and callable(monotonic_clock),500,'ORIGINAL_PROJECT_ACCESS_REQUIRED')
        require(type(grant_seconds) is int and 1<=grant_seconds<=30 and type(session_seconds) is int and 1<=session_seconds<=30
                and type(capacity) is int and 1<=capacity<=256,500,'BOUNDED_RESOURCE_CONFIGURATION_REQUIRED')
        require(isinstance(allowed_installations,(list,tuple)) and 1<=len(allowed_installations)<=16,500,'QUALIFIED_RESOURCE_INSTALLATIONS_REQUIRED')
        approved=set()
        for row in allowed_installations:
            require(isinstance(row,dict) and set(row)==set(IDENTITIES) and all(hex_value(row[k],64) for k in IDENTITIES),500,'RESOURCE_INSTALLATION_INVALID')
            approved.add(tuple(row[k] for k in IDENTITIES))
        self.access,self.allowed=access,frozenset(approved)
        self.clock,self.monotonic_clock=clock,monotonic_clock
        self.grant_seconds,self.session_seconds,self.capacity=grant_seconds,session_seconds,capacity
        self._lock=threading.Lock(); self._rows={}; self._last_tick=None; self._closed=False; self._receipt_tag=object()

    def _now(self):
        now=self.clock()
        require(type(now) in (int,float) and math.isfinite(now),503,'RESOURCE_CLOCK_UNAVAILABLE')
        return now

    def _tick_locked(self):
        now=self.monotonic_clock()
        require(type(now) in (int,float) and math.isfinite(now) and (self._last_tick is None or now>=self._last_tick),503,'RESOURCE_CLOCK_UNAVAILABLE')
        self._last_tick=now
        return now

    @staticmethod
    def _expiry(start,seconds):
        result=start+seconds
        require(math.isfinite(result) and result>start,503,'RESOURCE_CLOCK_UNAVAILABLE')
        return result

    def _check(self,authorization,write):
        try: subject=self.access.check(authorization,write=write)
        except Exception as error:
            status=getattr(error,'status',503)
            # Only an explicit original-project 403 may remove the write scope.
            if write and type(status) is int and status==403: return None
            status=status if type(status) is int and status in (401,403) else 503
            raise GrantError(status,'LOGIN_REQUIRED' if status==401 else 'RESOURCE_ACCESS_DENIED' if status==403 else 'LOGIN_CHECK_UNAVAILABLE') from None
        require(isinstance(subject,str) and 1<=len(subject)<=256 and subject.strip()==subject
                and not any(ord(c)<32 or ord(c)==127 for c in subject),503,'LOGIN_CHECK_UNAVAILABLE')
        return subject

    def _authorize(self,authorization):
        require(isinstance(authorization,str) and 1<=len(authorization)<=16384 and authorization.strip()==authorization
                and all(32<=ord(c)<=126 for c in authorization),401,'LOGIN_REQUIRED')
        subject=self._check(authorization,False)
        writer=self._check(authorization,True)
        require(writer is None or writer==subject,403,'RESOURCE_ACCOUNT_CHANGED')
        return subject,(READ,WRITE) if writer is not None else (READ,)

    def _purge(self,now):
        self._rows={key:row for key,row in self._rows.items() if row[0]>now}

    def issue(self,authorization,document):
        require(isinstance(document,dict) and set(document)=={'expected'},400,'RESOURCE_GRANT_REQUEST_INVALID')
        expected=checked_expected(document['expected'])
        require(tuple(expected[k] for k in IDENTITIES) in self.allowed,409,'RESOURCE_INSTALLATION_UNSUPPORTED')
        subject,scopes=self._authorize(authorization)
        actor=account_key(subject)
        metadata_expiry=self._expiry(self._now(),self.grant_seconds)
        with self._lock:
            require(not self._closed,503,'RESOURCE_GRANTS_CLOSED')
            now=self._tick_locked(); self._purge(now)
            require(len(self._rows)<self.capacity,503,'RESOURCE_GRANTS_BUSY')
            require(sum(row[2]==subject for row in self._rows.values())<8,429,'RESOURCE_ACCOUNT_GRANTS_BUSY')
            grant=secrets.token_hex(32); key=hashlib.sha256(grant.encode('ascii')).digest()
            require(key not in self._rows,503,'RESOURCE_GRANT_COLLISION')
            self._rows[key]=(self._expiry(now,self.grant_seconds),authorization,subject,expected,scopes,actor)
        return {'schema':'xnby.client-resources.grant.v1','grant':grant,'expiresAt':metadata_expiry}

    def consume(self,document):
        require(isinstance(document,dict) and set(document)=={'grant','expected'} and hex_value(document['grant'],64),403,'RESOURCE_GRANT_REJECTED')
        expected=checked_expected(document['expected'])
        key=hashlib.sha256(document['grant'].encode('ascii')).digest()
        with self._lock:
            require(not self._closed,503,'RESOURCE_GRANTS_CLOSED')
            now=self._tick_locked(); self._purge(now)
            record=self._rows.pop(key,None)
        require(record is not None,403,'RESOURCE_GRANT_REJECTED')
        expiry,authorization,subject,bound,scopes,actor=record
        require(expected==bound,403,'RESOURCE_GRANT_REJECTED')
        current,current_scopes=self._authorize(authorization)
        require(current==subject and account_key(current)==actor,403,'RESOURCE_ACCOUNT_CHANGED')
        require(all(scope in current_scopes for scope in scopes),403,'RESOURCE_PERMISSION_CHANGED')
        metadata_expiry=self._expiry(self._now(),self.session_seconds)
        with self._lock:
            require(not self._closed,503,'RESOURCE_GRANTS_CLOSED')
            now=self._tick_locked()
            require(now<expiry,403,'RESOURCE_GRANT_EXPIRED')
            deadline=self._expiry(now,self.session_seconds)
        return _Receipt({'accepted':True,'scopes':list(scopes),'actorKey':actor,'projectKey':PROJECT_KEY,**bound,'expiresAt':metadata_expiry},deadline,self._receipt_tag)

    def remaining_ms(self,receipt):
        require(isinstance(receipt,_Receipt) and receipt._tag is self._receipt_tag,403,'RESOURCE_GRANT_REJECTED')
        with self._lock:
            require(not self._closed,503,'RESOURCE_GRANTS_CLOSED')
            remaining=math.floor((receipt._deadline-self._tick_locked())*1000)
        require(1<=remaining<=self.session_seconds*1000,403,'RESOURCE_GRANT_EXPIRED')
        return remaining

    def close(self):
        with self._lock: self._closed=True; self._rows.clear()

    @property
    def summary(self):
        with self._lock:
            if not self._closed: self._purge(self._tick_locked())
            return {'pendingGrants':len(self._rows),'closed':self._closed}

def serve_client_resource_grants(handler,authority):
    """Original adapter opt-in; unrelated application routes remain unchanged."""
    if handler.path not in (INTERNAL_PATH,INTERNAL_PATH+'/consume'): return False
    body_read=0
    def output(status,value):
        remaining=authority.remaining_ms(value) if status==200 and handler.path.endswith('/consume') else None
        raw=json.dumps(value,allow_nan=False,separators=(',',':')).encode('utf8')
        handler.send_response(status)
        if remaining is not None: handler.send_header(REMAINING_HEADER,str(remaining))
        for key,val in [('Content-Type','application/json'),('Content-Length',str(len(raw))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Connection','close')]: handler.send_header(key,val)
        handler.end_headers(); handler.close_connection=True
        if handler.command!='HEAD': handler.wfile.write(raw)
        handler.wfile.flush()
        # On Windows closing with a small unread request body may reset TCP and
        # hide the original rejection from a normal HTTP client. Discard only a
        # uniquely declared bounded body, never parse or replay denied requests.
        if status>=400 and not handler.headers.get_all('Transfer-Encoding',[]):
            lengths=handler.headers.get_all('Content-Length',[])
            if len(lengths)==1 and re.fullmatch('[1-9][0-9]{0,3}',lengths[0]) and int(lengths[0])<=8192:
                remaining=int(lengths[0])-body_read; end=time.monotonic()+0.5
                try:
                    while remaining>0 and time.monotonic()<end:
                        handler.connection.settimeout(max(0.001,end-time.monotonic()))
                        part=handler.rfile.read1(remaining)
                        if not part: break
                        remaining-=len(part)
                except OSError: pass
    try:
        require(isinstance(authority,ClientResourceGrantAuthority),503,'RESOURCE_AUTHORITY_NOT_INSTALLED')
        require(handler.command=='POST',405,'RESOURCE_POST_REQUIRED')
        require(handler.headers.get_all('Origin',[]) in ([],[ORIGIN]),403,'PROJECT_ORIGIN_REQUIRED')
        require(not handler.headers.get_all('Cookie',[]) and not handler.headers.get_all('Transfer-Encoding',[]),400,'RESOURCE_PRIVATE_HEADERS_REJECTED')
        auth=handler.headers.get_all('Authorization',[]); consume=handler.path.endswith('/consume')
        require(not auth if consume else len(auth)==1,401,'RESOURCE_AUTHORIZATION_INVALID')
        require(consume or handler.headers.get_all('Origin',[])==[ORIGIN],403,'PROJECT_ORIGIN_REQUIRED')
        require(handler.headers.get_all('Content-Type',[]) in (['application/json'],['application/json; charset=utf-8']),415,'JSON_REQUIRED')
        lengths=handler.headers.get_all('Content-Length',[])
        require(len(lengths)==1 and re.fullmatch('[1-9][0-9]{0,3}',lengths[0]) and int(lengths[0])<=8192,413,'RESOURCE_BOUNDED_BODY_REQUIRED')
        size=int(lengths[0]); blocks=[]; count=0; deadline=time.monotonic()+8
        while count<size:
            require(time.monotonic()<deadline,408,'RESOURCE_BODY_TIMEOUT')
            handler.connection.settimeout(max(0.001,deadline-time.monotonic()))
            block=handler.rfile.read1(size-count)
            require(bool(block),400,'RESOURCE_TRUNCATED_BODY'); blocks.append(block); count+=len(block); body_read=count
        try: document=loads(b''.join(blocks))
        except (ValueError,UnicodeError): raise GrantError(400,'RESOURCE_JSON_INVALID') from None
        result=authority.consume(document) if consume else authority.issue(auth[0],document)
        output(200 if consume else 201,result)
    except GrantError as error: output(error.status,{'code':error.code})
    except (OSError,TimeoutError):
        try: output(503,{'code':'RESOURCE_GRANT_UNAVAILABLE'})
        except OSError: pass
    return True

def with_client_resource_grants(base_handler):
    require(isinstance(base_handler,type),500,'ORIGINAL_HANDLER_REQUIRED')
    class ResourceGrantHandler(base_handler): pass
    def method(name):
        def dispatch(self):
            if serve_client_resource_grants(self,getattr(self.server,'resource_grant_authority',None)): return
            original=getattr(base_handler,name,None)
            if original is None: self.send_error(501)
            else: original(self)
        return dispatch
    for name in ('do_GET','do_HEAD','do_POST','do_PUT','do_DELETE','do_OPTIONS','do_PATCH'):
        setattr(ResourceGrantHandler,name,method(name))
    return ResourceGrantHandler
