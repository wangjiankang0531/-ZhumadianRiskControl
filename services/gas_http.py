"""Authenticated bounded HTTP facade; ordinary browser users cannot impersonate adapters."""
import json,re,uuid
from contextlib import ExitStack
from urllib.parse import urlsplit,quote
from .common import ApiError,loads
from .focus_http import authenticate,authorization_version
from .focus_materials import MATERIAL_JSON_LIMIT
from .gas_spatial import resolve as resolve_spatial

PREFIX='/api/v1/gas_alerts'
WRITES={'source-update','classify','verify','cooperate','handoff-request','handoff-result','archive','reopen','materials'}

def public_points(service,snapshot=None):
    # A configuration identifier alone cannot make a private/missing DLG object public.
    return frozenset(feature['id'] for feature,owner,*_ in (snapshot if snapshot is not None else service.store.snapshot())['objects'] if owner is None and feature['type']=='point' and feature['id'] in service.store.public)

def dispatch(service,handler):
    with ExitStack() as stack:return _dispatch(service,handler,stack)

def _dispatch(service,handler,stack):
    request_id=uuid.uuid4().hex;principal=None;status=200;success=False;binary=None
    try:
        url=urlsplit(handler.path)
        if len(handler.path)>8192 or any(ord(ch)<32 for ch in handler.path) or url.scheme or url.netloc or url.fragment:raise ApiError(400,'INVALID_REQUEST')
        match=re.fullmatch(PREFIX+r'(?:/([a-f0-9]{32})(?:/(history|spatial|source-update|classify|verify|cooperate|handoff-request|handoff-result|archive|reopen|materials)(?:/([a-f0-9]{32}))?)?)?',url.path)
        if not match:raise ApiError(404,'NOT_FOUND')
        event_id,action,material_id=match.groups()
        if material_id and action!='materials':raise ApiError(404,'NOT_FOUND')
        write=handler.command=='POST' and material_id is None and (event_id is None or action in WRITES)
        if handler.command not in {'GET','HEAD'} and not write or handler.command in {'GET','HEAD'} and action not in {None,'history','materials','spatial'}:raise ApiError(405,'METHOD_NOT_ALLOWED')
        principal=authenticate(service,handler);principal.require('gas:read')
        if service.gas is None:raise ApiError(503,'GAS_NOT_CONFIGURED')
        if action=='materials' and (write or material_id is not None):
            if not service.gas.http_material_slots.acquire(blocking=False):raise ApiError(429,'MATERIAL_BUSY')
            stack.callback(service.gas.http_material_slots.release)
        if handler.headers.get_all('Transfer-Encoding',[]):raise ApiError(400,'INVALID_REQUEST')
        sizes=handler.headers.get_all('Content-Length',[])
        if len(sizes)>1:raise ApiError(400,'INVALID_REQUEST')
        snapshot=service.store.snapshot() if action=='spatial' else None
        points=public_points(service,snapshot)
        if write:
            service.query(url.query,[])
            if len(sizes)!=1 or not re.fullmatch('[0-9]{1,8}',sizes[0]):raise ApiError(400,'INVALID_REQUEST')
            size=int(sizes[0]);maximum=MATERIAL_JSON_LIMIT if action=='materials' else 32768
            if not 1<=size<=maximum:raise ApiError(413,'BODY_TOO_LARGE')
            if handler.headers.get_all('Content-Type',[]) not in (['application/json'],['application/json; charset=utf-8']):raise ApiError(415,'JSON_REQUIRED')
            keys=handler.headers.get_all('Idempotency-Key',[])
            if len(keys)!=1 or not re.fullmatch('[a-f0-9]{32}',keys[0]):raise ApiError(400,'IDEMPOTENCY_KEY_REQUIRED')
            raw=handler.rfile.read(size)
            if len(raw)!=size:raise ApiError(400,'INVALID_REQUEST')
            payload=loads(raw)
            if not isinstance(payload,dict):raise ValueError('command object required')
            service.audit(request_id,'gas_write',202,principal,'WRITE_ATTEMPT')
            if event_id is None:result=service.gas.ingest(principal,points,payload,keys[0])
            elif action=='materials':result=service.gas.add_material(principal,points,event_id,payload,keys[0])
            else:result=service.gas.mutate(principal,points,event_id,action,payload,keys[0])
            success=True
        else:
            if sizes and sizes[0]!='0':raise ApiError(400,'INVALID_REQUEST')
            query=service.query(url.query,['offset','limit','status','classification','search'] if event_id is None else ['offset','limit'] if action=='history' else ['revision'] if action=='spatial' else [])
            if event_id is None:
                if query.get('limit',50)>100:raise ApiError(400,'INVALID_QUERY')
                result=service.gas.list(principal,points,**query)
            elif action=='spatial':result=resolve_spatial(service,principal,snapshot,points,event_id,query.get('revision'))
            elif action=='history':result=service.gas.history(principal,points,event_id,page=True,**query)
            elif action=='materials':
                if material_id is None:result=service.gas.materials(principal,points,event_id)
                else:
                    metadata,raw=service.gas.material(principal,points,event_id,material_id);binary=(metadata,raw);result={}
            else:result={'event':service.gas.detail(principal,points,event_id)}
        body={'requestId':request_id,**result,'policyVersion':principal.policy_version,'authorizationVersion':authorization_version(service,principal)}
    except ApiError as e:binary=None;status=e.status;body={'requestId':request_id,'error':e.code}
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):binary=None;status=400;body={'requestId':request_id,'error':'INVALID_BODY'}
    except Exception:binary=None;status=503;body={'requestId':request_id,'error':'GAS_UNAVAILABLE'}
    if not success:
        try:service.audit(request_id,'gas_alerts',status,principal,body.get('error','OK'))
        except ApiError:binary=None;status=503;body={'requestId':request_id,'error':'AUDIT_UNAVAILABLE'}
    if binary is None:raw=json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf8');content_type='application/json; charset=utf-8'
    else:metadata,raw=binary;content_type=metadata['mediaType']
    handler.send_response(status)
    for name,value in {'Content-Type':content_type,'Content-Length':str(len(raw)),'Cache-Control':'no-store','Vary':'Authorization','X-Content-Type-Options':'nosniff','X-Request-Id':request_id}.items():handler.send_header(name,value)
    if binary is not None:
        extension={'application/pdf':'.pdf','image/png':'.png','image/jpeg':'.jpg'}[content_type]
        handler.send_header('Content-Disposition',"attachment; filename=\"material-"+metadata['id']+extension+"\"; filename*=UTF-8''"+quote(metadata['name'],safe=''))
        handler.send_header('X-XNBY-Material-SHA256',metadata['sha256']);handler.send_header('X-XNBY-Authorization-Version',body['authorizationVersion']);handler.send_header('Content-Security-Policy',"sandbox; default-src 'none'")
    if status==401:handler.send_header('WWW-Authenticate','Bearer')
    if status==405:handler.send_header('Allow','GET, HEAD, POST')
    if status==429:handler.send_header('Retry-After','1')
    handler.end_headers()
    if handler.command!='HEAD':handler.wfile.write(raw)
