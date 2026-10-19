"""Bounded authenticated HTTP facade for the focus issue auxiliary workflow."""
import hashlib, json, re, sqlite3, uuid
from urllib.parse import urlsplit,quote
from .common import ApiError, loads
from .focus_materials import MATERIAL_JSON_LIMIT

PREFIX = "/api/v1/focus_issues"

def authorization_version(service, principal):
    effective = {"subject":principal.subject,"tenant":principal.tenant,"permissions":sorted(principal.permissions),"enterprises":sorted(principal.enterprises),"allEnterprises":principal.all_enterprises,"publicSpatial":principal.public_spatial,"policyVersion":principal.policy_version,"publicSpatialIds":sorted(service.store.public) if principal.public_spatial else []}
    return hashlib.sha256(json.dumps(effective,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def authenticate(service, handler):
    headers=handler.headers.get_all("Authorization",[])
    if len(headers)!=1 or not headers[0].startswith("Bearer ") or len(headers[0])>16400:
        raise ApiError(401,"UNAUTHENTICATED")
    return service.policy.principal(service.jwt.verify(headers[0][7:]))

def dispatch(service, handler):
    request_id=uuid.uuid4().hex; principal=None;status=200;success_write=False;binary=None;material_slot=None
    try:
        url=urlsplit(handler.path)
        if len(handler.path)>8192 or url.scheme or url.netloc or url.fragment:raise ApiError(400,"INVALID_REQUEST")
        match=re.fullmatch(PREFIX+r"(?:/([a-f0-9]{32})(?:/(events|feedback|track|review|archive|reopen|materials)(?:/([a-f0-9]{32}))?)?)?",url.path)
        if not match:raise ApiError(404,"NOT_FOUND")
        issue_id,action,material_id=match.groups()
        if material_id and action!='materials':raise ApiError(404,'NOT_FOUND')
        write=handler.command=="POST" and (issue_id is None or action in ("feedback","track","review","archive","reopen","materials") and material_id is None)
        if handler.command not in ("GET","HEAD") and not write:raise ApiError(405,"METHOD_NOT_ALLOWED")
        if handler.command in ("GET","HEAD") and action not in (None,"events","materials"):raise ApiError(405,"METHOD_NOT_ALLOWED")
        principal=authenticate(service,handler);principal.require("focus:read")
        if service.focus is None:raise ApiError(503,"FOCUS_NOT_CONFIGURED")
        if action=='materials' and (write or material_id is not None):
            if not service.focus.material_slots.acquire(blocking=False):raise ApiError(429,'MATERIAL_BUSY')
            material_slot=service.focus.material_slots
        if handler.headers.get_all("Transfer-Encoding",[]):raise ApiError(400,"INVALID_REQUEST")
        sizes=handler.headers.get_all("Content-Length",[])
        if len(sizes)>1:raise ApiError(400,"INVALID_REQUEST")
        if write:
            service.query(url.query,[])
            if len(sizes)!=1 or not re.fullmatch(r"[0-9]{1,8}",sizes[0]):raise ApiError(400,"INVALID_REQUEST")
            size=int(sizes[0])
            if not 1<=size<=(MATERIAL_JSON_LIMIT if action=='materials' else 32768):raise ApiError(413,"BODY_TOO_LARGE")
            types=handler.headers.get_all("Content-Type",[])
            if len(types)!=1 or types[0].lower() not in ("application/json","application/json; charset=utf-8"):raise ApiError(415,"JSON_REQUIRED")
            raw=handler.rfile.read(size)
            if len(raw)!=size:raise ApiError(400,"INVALID_REQUEST")
            payload=loads(raw)
            if not isinstance(payload,dict):raise ValueError("object required")
            keys=handler.headers.get_all("Idempotency-Key",[])
            if len(keys)!=1:raise ApiError(400,"IDEMPOTENCY_KEY_REQUIRED")
            # Fail before mutation if the external request-attempt audit is unavailable.
            service.audit(request_id,"focus_write",202,principal,"WRITE_ATTEMPT")
            def spatial_check(p,enterprise,spatial_id):
                p.require("spatial:read")
                if not any(f["id"]==spatial_id and owner==enterprise for f,owner,*_ in service.store.snapshot()["objects"]):
                    raise ApiError(400,"SPATIAL_REFERENCE_UNAVAILABLE")
            result=(service.focus.add_material(principal,issue_id,payload,keys[0]) if action=='materials' else service.focus.mutate(principal,issue_id,action or "create",payload,keys[0],spatial_check))
            # Successful writes + actor + policy + payload + idempotency are already journaled atomically in SQLite.
            success_write=True
        else:
            if sizes and sizes[0]!="0":raise ApiError(400,"INVALID_REQUEST")
            if issue_id is None:
                result=service.focus.listing(principal,service.query(url.query,["enterpriseId","status","flag","search","offset","limit"]))
            elif action=='materials':
                query=service.query(url.query,[] if material_id else ['offset','limit'])
                if material_id is not None:
                    binary=service.focus.material(principal,issue_id,material_id);result={}
                else:result=service.focus.materials(principal,issue_id,query)
            else:
                result=service.focus.detail(principal,issue_id,service.query(url.query,["offset","limit"] if action=="events" else []),action=="events")
        body={"requestId":request_id,**result,"policyVersion":principal.policy_version,"authorizationVersion":authorization_version(service,principal)}
    except ApiError as error:
        binary=None;status=error.status;body={"requestId":request_id,"error":error.code}
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):
        binary=None;status=400;body={"requestId":request_id,"error":"INVALID_BODY"}
    except Exception:
        binary=None;status=503;body={"requestId":request_id,"error":"FOCUS_UNAVAILABLE"}
    if not success_write:
        try:service.audit(request_id,"focus_issues",status,principal,body.get("error","OK"))
        except ApiError:binary=None;status=503;body={"requestId":request_id,"error":"AUDIT_UNAVAILABLE"}
    try:
        if binary is None:
            raw=json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode();content_type='application/json; charset=utf-8'
        else:raw,metadata=binary;content_type=metadata['mediaType']
        handler.send_response(status)
        for name,value in {"Content-Type":content_type,"Content-Length":str(len(raw)),"Cache-Control":"no-store","Vary":"Authorization","X-Content-Type-Options":"nosniff","X-Request-Id":request_id}.items():handler.send_header(name,value)
        if binary is not None:
            extension={'application/pdf':'.pdf','image/png':'.png','image/jpeg':'.jpg'}[content_type]
            handler.send_header('Content-Disposition',"attachment; filename=\"material-"+metadata['id']+extension+"\"; filename*=UTF-8''"+quote(metadata['name'],safe=''))
            handler.send_header('X-XNBY-Material-SHA256',metadata['sha256'])
            handler.send_header('X-XNBY-Authorization-Version',body['authorizationVersion'])
            handler.send_header('Content-Security-Policy',"sandbox; default-src 'none'")
        if status==401:handler.send_header("WWW-Authenticate","Bearer")
        if status==405:handler.send_header("Allow","GET, HEAD, POST")
        if status==429:handler.send_header('Retry-After','1')
        handler.end_headers()
        if handler.command!="HEAD":handler.wfile.write(raw)
    finally:
        if material_slot is not None:material_slot.release()
