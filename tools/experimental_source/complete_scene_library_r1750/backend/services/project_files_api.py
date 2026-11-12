"""Authenticated project-file routes reuse the original platform project ACL."""
import copy,json,re,sqlite3,time
from urllib.parse import unquote,urlsplit
from services.common import ApiError,loads
from services.layer_sync_identity import ACCOUNT_HEADER,account_key
FILE_ROUTE='/v2/project/files'
LIMIT=16*1048576
ORIGIN='https://www.joinlinksmart.com'

def reject_project_file(handler,status,payload,consumed):
    """Flush a denial, then discard only its bounded framed body before close.

    A loopback proxy can still be uploading a large buffered request when an
    authorization rejection is ready. Closing with unread bytes can reset that
    connection and replace the intended 401/403 with a proxy 502. Never parse or
    store rejected bytes, and never wait longer than the discard deadline.
    """
    handler.output(status,payload)
    handler.wfile.flush()
    lengths=handler.headers.get_all('Content-Length',[])
    if (handler.command!='POST'or handler.headers.get('Transfer-Encoding')or len(lengths)!=1
            or not re.fullmatch('[0-9]{1,8}',lengths[0])):return
    size=int(lengths[0])
    if not 0<=consumed<size<=LIMIT:return
    deadline=time.monotonic()+0.5;previous=handler.connection.gettimeout()
    try:
        remaining=size-consumed
        while remaining:
            available=deadline-time.monotonic()
            if available<=0:break
            handler.connection.settimeout(min(0.1,available))
            chunk=handler.rfile.read1(min(16384,remaining))
            if not chunk:break
            remaining-=len(chunk)
    except(OSError,TimeoutError):pass
    finally:handler.connection.settimeout(previous)


def serve_project_files(handler,write=False):
    h=handler;consumed=0
    try:
        route=urlsplit(h.path)
        if route.query or route.fragment:raise ApiError(404,'NOT_FOUND')
        collection=route.path==FILE_ROUTE
        name=None
        if not collection:
            if not route.path.startswith(FILE_ROUTE+'/')or '/'in route.path[len(FILE_ROUTE)+1:]:raise ApiError(404,'NOT_FOUND')
            from services.project_files import project_filename
            name=project_filename(unquote(route.path[len(FILE_ROUTE)+1:],errors='strict'))
        if write and not collection:raise ApiError(405,'METHOD_NOT_ALLOWED')
        values=h.headers.get_all('Authorization',[])
        if len(values)!=1:raise ApiError(401,'LOGIN_REQUIRED')
        origins=h.headers.get_all('Origin',[])
        if origins and origins!=[getattr(h.server,'project_origin',ORIGIN)]:raise ApiError(403,'PROJECT_ORIGIN_REQUIRED')
        bindings=h.headers.get_all(ACCOUNT_HEADER,[])
        if len(bindings)!=1 or not re.fullmatch('[0-9a-f]{64}',bindings[0]):raise ApiError(403,'ACCOUNT_BINDING_REQUIRED')
        subject=h.server.access.check(values[0],write)
        if account_key(subject)!=bindings[0]:raise ApiError(403,'ACCOUNT_BINDING_MISMATCH')
        repository=getattr(h.server,'project_files',None)
        if repository is None:raise ApiError(501,'PROJECT_FILE_LIBRARY_NOT_INSTALLED')
        lengths=h.headers.get_all('Content-Length',[])
        if h.headers.get('Transfer-Encoding')or len(lengths)>1:raise ApiError(400,'INVALID_REQUEST')
        if not write:return h.output(200,repository.list()if collection else repository.get(name))
        if len(lengths)!=1 or not re.fullmatch('[0-9]{1,8}',lengths[0]):raise ApiError(400,'CONTENT_LENGTH_REQUIRED')
        size=int(lengths[0])
        if not 1<=size<=LIMIT:raise ApiError(413,'PROJECT_FILE_TOO_LARGE')
        if h.headers.get_all('Content-Type',[])not in [['application/json'],['application/json; charset=utf-8']]:raise ApiError(415,'JSON_REQUIRED')
        parts=[];count=0;deadline=time.monotonic()+8
        while count<size:
            if time.monotonic()>deadline:raise ApiError(408,'REQUEST_TIMEOUT')
            chunk=h.rfile.read1(min(16384,size-count))
            if not chunk:break
            parts.append(chunk);count+=len(chunk);consumed=count
        if count!=size:raise ApiError(400,'INVALID_REQUEST')
        request=loads(b''.join(parts))
        if not isinstance(request,dict)or set(request)!={'name','expectedSHA256','document'}:raise ApiError(400,'INVALID_REQUEST')
        # Revalidate the original account and write ACL after a potentially long upload.
        if h.server.access.check(values[0],True)!=subject:raise ApiError(403,'ACCOUNT_BINDING_MISMATCH')
        return h.output(200,repository.save(request['name'],copy.deepcopy(request['document']),request['expectedSHA256']))
    except ApiError as error:return reject_project_file(h,error.status,{'error':error.code},consumed)
    except(UnicodeError,ValueError,TypeError,KeyError):return reject_project_file(h,422,{'error':'INVALID_PROJECT_FILE'},consumed)
    except(OSError,TimeoutError,sqlite3.Error):return reject_project_file(h,503,{'error':'PROJECT_FILE_LIBRARY_UNAVAILABLE'},consumed)
