"""Bounded loopback management API. Never serves arbitrary files or accepts login tokens."""
import http.server,json,re,socket,threading
from urllib.parse import urlsplit
from resource_grants import ORIGIN,require,pairs
from resource_service import safe_code
from grant_clock import REMAINING_HEADER
PREFIX='/xnby-client-resources/v1/'
SESSION='X-XNBY-Client-Resources-Session'
ALLOWED={'content-type',SESSION.lower()}
class ResourceHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads=False
    block_on_close=True
    allow_reuse_address=False
    def __init__(self,manager,*,port=18768,qa=False):
        require(type(port)is int and (port==18768 or qa is True and 0<=port<=65535),'RESOURCE_FIXED_PORT_REQUIRED');self.manager=manager;self.slots=threading.BoundedSemaphore(4);super().__init__(('127.0.0.1',port),ResourceHandler)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()
class ResourceHandler(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1';server_version='XNBYResources/1';sys_version=''
    def setup(self):super().setup();self.connection.settimeout(3)
    def log_message(self,*_):pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin',ORIGIN);self.send_header('Vary','Origin');self.send_header('Access-Control-Expose-Headers',REMAINING_HEADER)
    def reply(self,status,value=None,*,cors=True,remaining=None):
        raw=b''if value is None else json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8');require(len(raw)<=262144,'RESOURCE_RESPONSE_TOO_LARGE');self.send_response(status);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('Connection','close')
        if raw:self.send_header('Content-Type','application/json; charset=utf-8')
        if cors:self.cors()
        if remaining is not None:self.send_header(REMAINING_HEADER,str(remaining))
        self.end_headers();self.close_connection=True
        if self.command!='HEAD'and raw:self.wfile.write(raw)
    def boundary(self):
        if self.headers.get_all('Host',[])!=['127.0.0.1:'+str(self.server.server_port)]or self.headers.get_all('Origin',[])!=[ORIGIN]:self.reply(403,{'code':'RESOURCE_ORIGIN_OR_HOST_REJECTED'},cors=False);return False
        if any(self.headers.get_all(key)for key in ['Cookie','Authorization','Transfer-Encoding','X-Provider-Owner','X-XNBY-Fine-Provider']):self.reply(400,{'code':'RESOURCE_PRIVATE_HEADERS_REJECTED'});return False
        if any(len(self.headers.get_all(key,[]))>1 for key in [SESSION,'Content-Length','Content-Type']):self.reply(400,{'code':'RESOURCE_DUPLICATE_HEADER'});return False
        if len(self.path)>256 or '\\'in self.path or '%'in self.path or '?'in self.path or '#'in self.path or not self.path.startswith(PREFIX):self.reply(404,{'code':'RESOURCE_ROUTE_INVALID'});return False
        return True
    def body(self):
        require(self.headers.get('Content-Type')=='application/json','RESOURCE_JSON_REQUIRED');length=self.headers.get('Content-Length','');require(re.fullmatch(r'[1-9][0-9]{0,3}',length)and int(length)<=8192,'RESOURCE_BODY_INVALID');raw=self.rfile.read(int(length));require(len(raw)==int(length),'RESOURCE_BODY_INVALID');value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs);require(isinstance(value,dict),'RESOURCE_BODY_INVALID');return value
    def do_OPTIONS(self):
        if not self.boundary():return
        method=self.headers.get_all('Access-Control-Request-Method',[]);fields=self.headers.get_all('Access-Control-Request-Headers',[]);names=[x.strip().lower()for x in fields[0].split(',')]if len(fields)==1 else[]
        if len(method)!=1 or method[0]not in {'GET','POST','DELETE'}or len(fields)>1 or any(x not in ALLOWED for x in names)or self.headers.get_all('Access-Control-Request-Private-Network',[])not in([] ,['true']):return self.reply(403,{'code':'RESOURCE_PREFLIGHT_REJECTED'})
        self.send_response(204);self.cors();self.send_header('Access-Control-Allow-Methods','GET, POST, DELETE');self.send_header('Access-Control-Allow-Headers',', '.join(sorted(ALLOWED)));self.send_header('Access-Control-Allow-Private-Network','true');self.send_header('Access-Control-Max-Age','60');self.send_header('Content-Length','0');self.send_header('Connection','close');self.end_headers();self.close_connection=True
    def dispatch(self):
        if not self.boundary():return
        service=self.server.manager;authority=service.authority;route=self.path[len(PREFIX):];token=self.headers.get(SESSION)
        try:
            if self.command=='GET'and route=='discovery':
                require(self.headers.get('Content-Length','0')=='0','RESOURCE_EMPTY_BODY_REQUIRED');return self.reply(200,authority.discovery())
            if self.command=='POST'and route in {'sessions','sessions/current'}:
                value=self.body();require(set(value)=={'grant'},'RESOURCE_GRANT_INVALID');result=authority.establish(value['grant'])if route=='sessions'else authority.renew(token,value['grant']);return self.reply(201,result,remaining=authority.remaining_ms(result['session']))
            if self.command=='DELETE'and route=='sessions/current':
                require(self.headers.get('Content-Length','0')=='0','RESOURCE_EMPTY_BODY_REQUIRED');service.close_session(token);return self.reply(204)
            authority.get(token)
            if self.command=='GET':
                require(self.headers.get('Content-Length','0')=='0','RESOURCE_EMPTY_BODY_REQUIRED')
                if route=='configuration':return self.reply(200,service.configuration(token))
                if route=='gis/status':return self.reply(200,service.gis_status(token))
                match=re.fullmatch(r'gis/operations/([a-f0-9]{32})',route)
                if match:return self.reply(200,service.gis_operation(token,match[1]))
                if route=='reports':return self.reply(200,service.list_reports(token))
                match=re.fullmatch(r'audits/([a-f0-9]{32})',route)
                if match:return self.reply(200,service.audit(token,match[1]))
                match=re.fullmatch(r'reports/([a-f0-9]{32})',route)
                if match:return self.reply(200,service.report(token,match[1]))
            if self.command=='POST':
                value=self.body()
                if route=='configuration':require(set(value)=={'workspaceRoot'},'RESOURCE_BODY_INVALID');return self.reply(200,service.save(token,value['workspaceRoot']))
                require(value=={},'RESOURCE_EMPTY_OBJECT_REQUIRED')
                if route in ('gis/start','gis/stop'):return self.reply(202,service.start_gis_operation(token,route.rsplit('/',1)[1]))
                if route=='audits':return self.reply(202,service.start_audit(token))
                match=re.fullmatch(r'audits/([a-f0-9]{32})/cancel',route)
                if match:return self.reply(202,service.cancel_audit(token,match[1]))
            return self.reply(404,{'code':'RESOURCE_ROUTE_INVALID'})
        except(FileNotFoundError,NotADirectoryError):return self.reply(404,{'code':'RESOURCE_REPORT_NOT_FOUND'})
        except Exception as error:
            code=safe_code(error);status=401 if code=='RESOURCE_SESSION_REQUIRED'else 403 if code in {'RESOURCE_WRITE_FORBIDDEN','RESOURCE_SCOPE_REJECTED'}else 409 if code=='RESOURCE_OPERATION_BUSY'else 404 if code in ('GIS_OPERATION_NOT_FOUND','GIS_CONTROL_UNAVAILABLE')else 400;return self.reply(status,{'code':code})
    do_GET=dispatch;do_POST=dispatch;do_DELETE=dispatch
