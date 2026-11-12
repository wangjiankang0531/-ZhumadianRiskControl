"""One-use, in-memory GIS grants backed by the original project read ACL.

No listener, file, default identity or credentials are created by import. The
owning original server must supply its existing access object and explicitly
approved offline resource descriptors. Original authorization never leaves the
server through a grant response or consume receipt.
"""
from __future__ import annotations
import hashlib
import http.client
import json
import math
import re
import secrets
import threading
import time

ORIGIN='https://www.joinlinksmart.com'
PUBLIC_PATH='/zhumadian/api/spatial-sync/v2/local-gis/grants'
INTERNAL_PATH='/v2/local-gis/grants'
REMAINING_HEADER='X-XNBY-Local-GIS-Remaining-Ms'
EXPECTED_FIELDS={'origin','instanceId','challenge','sourceRuntimeIdentity','sourceIndexIdentity','budgetMiB'}
DISCOVERY_FIELDS={'schema','protocolVersion','instanceId','challenge','sourceRuntimeIdentity','sourceIndexIdentity','budgetMiB','ready'}
SHA=re.compile(r'[0-9a-f]{64}')

class GrantError(Exception):
 def __init__(self,status,code):
  self.status,self.code=status,code
  super().__init__(code)

def require(value,status,code):
 if not value:raise GrantError(status,code)

def hex_value(value,length):
 return isinstance(value,str)and re.fullmatch('[0-9a-f]{'+str(length)+'}',value)is not None

def checked_expected(value):
 require(isinstance(value,dict)and set(value)==EXPECTED_FIELDS,400,'GIS_EXPECTED_FIELDS_REQUIRED')
 require(value['origin']==ORIGIN and hex_value(value['instanceId'],32)and hex_value(value['challenge'],64)
         and hex_value(value['sourceRuntimeIdentity'],64)and hex_value(value['sourceIndexIdentity'],64)
         and type(value['budgetMiB'])is int and value['budgetMiB']in (512,1024,2048),400,'GIS_EXPECTED_INVALID')
 return dict(value)

def checked_discovery(value):
 require(isinstance(value,dict)and set(value)==DISCOVERY_FIELDS
         and value['schema']=='xnby.local-gis.discovery.v1'and type(value['protocolVersion'])is int
         and value['protocolVersion']==1 and value['ready']is True,400,'GIS_DISCOVERY_INVALID')
 return checked_expected(dict(origin=ORIGIN,**{k:value[k]for k in EXPECTED_FIELDS-{'origin'}}))

def loads(raw):
 def pairs(rows):
  result={}
  for k,v in rows:
   if k in result:raise ValueError('DUPLICATE_JSON_FIELD')
   result[k]=v
  return result
 return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                   parse_constant=lambda _:(_ for _ in()).throw(ValueError('NONFINITE_JSON')))

class _ConsumeReceipt(dict):
 __slots__=('_deadline','_tag')
 def __init__(self,payload,deadline,tag):
  super().__init__(payload);self._deadline,self._tag=deadline,tag

class LocalGISGrantAuthority:
 def __init__(self,access,allowed_sources,*,clock=time.time,monotonic_clock=time.monotonic,grant_seconds=30,session_seconds=30,capacity=256):
  require(callable(getattr(access,'check',None))and callable(clock)and callable(monotonic_clock),500,'ORIGINAL_PROJECT_ACCESS_REQUIRED')
  require(type(grant_seconds)is int and 1<=grant_seconds<=30 and type(session_seconds)is int
          and 1<=session_seconds<=30 and type(capacity)is int and 1<=capacity<=256,500,'BOUNDED_GRANT_CONFIGURATION_REQUIRED')
  require(isinstance(allowed_sources,(list,tuple))and 1<=len(allowed_sources)<=16,500,'EXPLICIT_OFFLINE_SOURCES_REQUIRED')
  approved=set()
  for row in allowed_sources:
   require(isinstance(row,dict)and set(row)=={'sourceRuntimeIdentity','sourceIndexIdentity','budgetMiB'},500,'EXACT_OFFLINE_SOURCE_REQUIRED')
   require(hex_value(row['sourceRuntimeIdentity'],64)and hex_value(row['sourceIndexIdentity'],64)
           and type(row['budgetMiB'])is int and row['budgetMiB']in (512,1024,2048),500,'OFFLINE_SOURCE_INVALID')
   approved.add((row['sourceRuntimeIdentity'],row['sourceIndexIdentity'],row['budgetMiB']))
  self.access,self.allowed,self.clock,self.monotonic_clock=access,frozenset(approved),clock,monotonic_clock
  self.grant_seconds,self.session_seconds,self.capacity=grant_seconds,session_seconds,capacity
  self._rows={};self._lock=threading.Lock();self._closed=False;self._last_tick=None;self._receipt_tag=object()

 def _now(self):
  value=self.clock()
  require(type(value)in (int,float)and math.isfinite(value),503,'GIS_CLOCK_UNAVAILABLE')
  return value

 def _tick_locked(self):
  # Only call while holding this authority's lock. Wall UTC is metadata only.
  value=self.monotonic_clock()
  require(type(value)in (int,float)and math.isfinite(value),503,'GIS_CLOCK_UNAVAILABLE')
  require(self._last_tick is None or value>=self._last_tick,503,'GIS_CLOCK_UNAVAILABLE')
  self._last_tick=value
  return value

 def _expiry(self,start,seconds):
  value=start+seconds
  require(math.isfinite(value)and value>start,503,'GIS_CLOCK_UNAVAILABLE')
  return value

 def remaining_ms(self,receipt):
  require(isinstance(receipt,_ConsumeReceipt)and receipt._tag is self._receipt_tag,403,'GIS_GRANT_REJECTED')
  with self._lock:
   require(not self._closed,503,'GIS_GRANTS_CLOSED')
   remaining=math.floor((receipt._deadline-self._tick_locked())*1000)
  require(1<=remaining<=self.session_seconds*1000,403,'GIS_GRANT_EXPIRED')
  return remaining

 def _purge(self,now):
  self._rows={k:v for k,v in self._rows.items()if v[0]>now}

 def _authorize(self,authorization):
  require(isinstance(authorization,str)and 1<=len(authorization)<=16384 and authorization.strip()==authorization
          and all(32<=ord(c)<=126 for c in authorization),401,'LOGIN_REQUIRED')
  try:subject=self.access.check(authorization,write=False)
  except Exception as error:
   status=getattr(error,'status',503)
   raise GrantError(status if status in (401,403)else 503,
                    'LOGIN_REQUIRED'if status==401 else 'PROJECT_GIS_ACCESS_DENIED'if status==403 else 'LOGIN_CHECK_UNAVAILABLE')from None
  require(isinstance(subject,str)and 1<=len(subject)<=256 and subject.strip()==subject
          and not any(ord(c)<32 or ord(c)==127 for c in subject),503,'LOGIN_CHECK_UNAVAILABLE')
  return subject

 def issue(self,authorization,document):
  require(isinstance(document,dict)and set(document)=={'schema','discovery'}and document['schema']=='xnby.local-gis.grant-request.v1',400,'GIS_GRANT_REQUEST_INVALID')
  expected=checked_discovery(document['discovery'])
  require((expected['sourceRuntimeIdentity'],expected['sourceIndexIdentity'],expected['budgetMiB'])in self.allowed,409,'GIS_OFFLINE_VERSION_UNSUPPORTED')
  subject=self._authorize(authorization);metadata_expiry=self._expiry(self._now(),self.grant_seconds)
  with self._lock:
   require(not self._closed,503,'GIS_GRANTS_CLOSED');now=self._tick_locked();self._purge(now)
   require(len(self._rows)<self.capacity,503,'GIS_GRANTS_BUSY')
   require(sum(row[2]==subject for row in self._rows.values())<8,429,'GIS_ACCOUNT_GRANTS_BUSY')
   grant=secrets.token_hex(32);key=hashlib.sha256(grant.encode('ascii')).digest()
   expiry=self._expiry(now,self.grant_seconds)
   self._rows[key]=(expiry,authorization,subject,expected)
  return {'schema':'xnby.local-gis.grant.v1','grant':grant,'expiresAt':metadata_expiry}

 def consume(self,document):
  require(isinstance(document,dict)and set(document)=={'grant','expected'}and hex_value(document['grant'],64),403,'GIS_GRANT_REJECTED')
  expected=checked_expected(document['expected']);key=hashlib.sha256(document['grant'].encode('ascii')).digest()
  with self._lock:
   require(not self._closed,503,'GIS_GRANTS_CLOSED');now=self._tick_locked();self._purge(now)
   # Pop before any upstream I/O: concurrent uses or a failed verification never
   # replay an already presented capability. The original login is checked again.
   record=self._rows.pop(key,None)
  require(record is not None,403,'GIS_GRANT_REJECTED')
  expiry,authorization,subject,bound=record
  require(expected==bound,403,'GIS_GRANT_REJECTED')
  require(self._authorize(authorization)==subject,403,'GIS_ACCOUNT_CHANGED')
  metadata_expiry=self._expiry(self._now(),self.session_seconds)
  with self._lock:
   require(not self._closed,503,'GIS_GRANTS_CLOSED')
   now=self._tick_locked();require(now<expiry,403,'GIS_GRANT_EXPIRED')
   deadline=self._expiry(now,self.session_seconds)
  return _ConsumeReceipt({'accepted':True,'scope':'gis.read',**bound,'expiresAt':metadata_expiry},deadline,self._receipt_tag)

 def close(self):
  with self._lock:self._closed=True;self._rows.clear()

 @property
 def summary(self):
  with self._lock:
   if not self._closed:self._purge(self._tick_locked())
   return {'pendingGrants':len(self._rows),'closed':self._closed}

def serve_local_gis_grants(handler,authority):
 """Bounded opt-in handler for the original adapter, before its existing routes.

 Returns False for unrelated paths so original DLG/model APIs remain owned by
 their existing handler. Production nginx mounts must retain the original
 authentication routes and explicitly proxy these two paths only.
 """
 if handler.path not in (INTERNAL_PATH,INTERNAL_PATH+'/consume'):return False
 def output(status,value):
  raw=json.dumps(value,allow_nan=False,separators=(',',':')).encode()
  remaining=None
  if status==200 and handler.path==INTERNAL_PATH+'/consume':
   # A private monotonic deadline stays in this authority process. No hidden
   # fields enter the nine-field JSON. Consumers still subtract full request RTT.
   remaining=authority.remaining_ms(value)
  handler.send_response(status)
  if remaining is not None:handler.send_header(REMAINING_HEADER,str(remaining))
  for k,v in [('Content-Type','application/json'),('Content-Length',str(len(raw))),('Cache-Control','no-store'),
              ('X-Content-Type-Options','nosniff'),('Connection','close')]:handler.send_header(k,v)
  handler.end_headers();handler.close_connection=True
  if handler.command!='HEAD':handler.wfile.write(raw)
 try:
  require(isinstance(authority,LocalGISGrantAuthority),503,'GIS_AUTHORITY_NOT_INSTALLED')
  require(handler.command=='POST',405,'GIS_POST_REQUIRED')
  require(handler.headers.get_all('Origin',[])in ([],[ORIGIN]),403,'PROJECT_ORIGIN_REQUIRED')
  require(not handler.headers.get_all('Cookie',[])and not handler.headers.get_all('Transfer-Encoding',[]),400,'GIS_PRIVATE_HEADERS_REJECTED')
  auth=handler.headers.get_all('Authorization',[])
  consume=handler.path.endswith('/consume')
  require(not auth if consume else len(auth)==1,401,'GIS_GRANT_AUTHORIZATION_INVALID')
  require(consume or handler.headers.get_all('Origin',[])==[ORIGIN],403,'PROJECT_ORIGIN_REQUIRED')
  require(handler.headers.get_all('Content-Type',[])in (['application/json'],['application/json; charset=utf-8']),415,'JSON_REQUIRED')
  lengths=handler.headers.get_all('Content-Length',[])
  require(len(lengths)==1 and re.fullmatch('[1-9][0-9]{0,3}',lengths[0])and int(lengths[0])<=8192,413,'GIS_BOUNDED_BODY_REQUIRED')
  size=int(lengths[0]);blocks=[];count=0;deadline=time.monotonic()+8
  while count<size:
   require(time.monotonic()<deadline,408,'GIS_BODY_TIMEOUT')
   block=handler.rfile.read1(size-count)
   require(bool(block),400,'GIS_TRUNCATED_BODY');blocks.append(block);count+=len(block)
  raw=b''.join(blocks)
  try:document=loads(raw)
  except (ValueError,UnicodeError):raise GrantError(400,'GIS_JSON_INVALID')from None
  result=authority.consume(document)if consume else authority.issue(auth[0],document)
  output(200 if consume else 201,result)
 except GrantError as error:output(error.status,{'code':error.code})
 except (OSError,TimeoutError):
  try:output(503,{'code':'GIS_GRANT_UNAVAILABLE'})
  except OSError:pass
 return True

def with_local_gis_grants(base_handler):
 """Wrap the original handler without replacing any unrelated route semantics."""
 require(isinstance(base_handler,type),500,'ORIGINAL_HANDLER_REQUIRED')
 class GrantHandler(base_handler):
  pass
 def method(name):
  def dispatch(self):
   if serve_local_gis_grants(self,getattr(self.server,'gis_grant_authority',None)):return
   original=getattr(base_handler,name,None)
   if original is None:self.send_error(501)
   else:original(self)
  return dispatch
 for name in ('do_GET','do_HEAD','do_POST','do_PUT','do_DELETE','do_OPTIONS'):
  setattr(GrantHandler,name,method(name))
 return GrantHandler
