"""Adapter for the original platform ACL; no standalone public listener."""
import re,sqlite3,time
from urllib.parse import urlsplit
from services.common import ApiError,loads
from services.layer_sync_identity import ACCOUNT_HEADER,account_key
from services.project_files_api import reject_project_file
from .repository import LIMIT
ROUTE='/v2/project/scene-models';PUBLIC_ROUTE='/zhumadian/api/spatial-sync'+ROUTE;ORIGIN='https://www.joinlinksmart.com'
def verified_subject(access,authorization,write):
 # The original host may load its ACL under a private module namespace.
 # Normalize only its trusted result/errors, never forward exception text.
 try:return access.check(authorization,write)
 except ApiError:raise
 except Exception as error:
  status=getattr(error,'status',None)
  if type(status)is int and status in(401,403):raise ApiError(status,'LOGIN_REQUIRED'if status==401 else'PROJECT_MODEL_ACCESS_DENIED')from None
  raise ApiError(503,'LOGIN_CHECK_UNAVAILABLE')from None
def serve_scene_models(handler,write=False):
 h=handler;consumed=0
 try:
  route=urlsplit(h.path)
  operation=re.fullmatch(re.escape(ROUTE)+r'/operations/([0-9a-f]{32})',route.path)
  if(route.path!=ROUTE and not operation)or route.query or route.fragment:raise ApiError(404,'NOT_FOUND')
  if operation and write:raise ApiError(405,'METHOD_NOT_ALLOWED')
  if h.command not in(('POST',)if write else('GET','HEAD')):raise ApiError(405,'METHOD_NOT_ALLOWED')
  values=h.headers.get_all('Authorization',[]);bindings=h.headers.get_all(ACCOUNT_HEADER,[]);origins=h.headers.get_all('Origin',[])
  if len(values)!=1:raise ApiError(401,'LOGIN_REQUIRED')
  if origins and origins!=[getattr(h.server,'project_origin',ORIGIN)]:raise ApiError(403,'PROJECT_ORIGIN_REQUIRED')
  if len(bindings)!=1 or not re.fullmatch('[0-9a-f]{64}',bindings[0]):raise ApiError(403,'ACCOUNT_BINDING_REQUIRED')
  subject=verified_subject(h.server.access,values[0],write)
  if account_key(subject)!=bindings[0]:raise ApiError(403,'ACCOUNT_BINDING_MISMATCH')
  repository=getattr(h.server,'scene_models',None)
  if repository is None:raise ApiError(501,'SCENE_MODEL_SYNC_NOT_INSTALLED')
  lengths=h.headers.get_all('Content-Length',[])
  if h.headers.get('Transfer-Encoding')or len(lengths)>1:raise ApiError(400,'INVALID_REQUEST')
  if not write:
   if lengths and lengths!=['0']:raise ApiError(400,'INVALID_REQUEST')
   return h.output(200,repository.operation(operation.group(1),bindings[0])if operation else repository.get())
  if len(lengths)!=1 or not re.fullmatch('[0-9]{1,8}',lengths[0]):raise ApiError(400,'CONTENT_LENGTH_REQUIRED')
  size=int(lengths[0])
  if not 1<=size<=LIMIT:raise ApiError(413,'SCENE_STATE_TOO_LARGE')
  if h.headers.get_all('Content-Type',[])not in[['application/json'],['application/json; charset=utf-8']]:raise ApiError(415,'JSON_REQUIRED')
  parts=[];count=0;deadline=time.monotonic()+8
  while count<size:
   if time.monotonic()>deadline:raise ApiError(408,'REQUEST_TIMEOUT')
   chunk=h.rfile.read1(min(16384,size-count))
   if not chunk:break
   parts.append(chunk);count+=len(chunk);consumed=count
  if count!=size:raise ApiError(400,'INVALID_REQUEST')
  request=loads(b''.join(parts))
  if not isinstance(request,dict)or set(request)!={'document','expectedRevision','operationId'}:raise ApiError(400,'INVALID_REQUEST')
  if verified_subject(h.server.access,values[0],True)!=subject:raise ApiError(403,'ACCOUNT_BINDING_MISMATCH')
  return h.output(200,repository.save(request['document'],request['expectedRevision'],request['operationId'],bindings[0]))
 except ApiError as error:return reject_project_file(h,error.status,{'error':error.code},consumed)
 except(ValueError,TypeError,KeyError,UnicodeError):return reject_project_file(h,422,{'error':'INVALID_SCENE_MODEL_STATE'},consumed)
 except(OSError,TimeoutError,sqlite3.Error):return reject_project_file(h,503,{'error':'SCENE_MODEL_STORAGE_UNAVAILABLE'},consumed)
