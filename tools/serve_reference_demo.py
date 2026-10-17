"""Loopback-only reference demo; independent SQLite and static asset whitelist."""
import argparse, json, sys, secrets, hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.reference_demo import DemoStore,DemoError,MODULES

class Handler(BaseHTTPRequestHandler):
    def json(self,status,value):
        raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def trusted(self,write=False):
        host=self.headers.get('Host','')
        if host not in self.server.allowed_hosts:raise DemoError(403,'仅允许本机验收地址')
        if write and (self.headers.get('Origin')!='http://'+host or self.headers.get('X-XNBY-Demo')!=self.server.demo_token):raise DemoError(403,'模拟写入来源无效')
    def do_GET(self):
        try:
            self.trusted();u=urlsplit(self.path);q=parse_qs(u.query,max_num_fields=8)
            if any(len(v)!=1 for v in q.values()):raise DemoError(400,'重复查询参数')
            q={k:v[0] for k,v in q.items()}
            if u.path=='/api/demo/health':return self.json(200,dict(schema='xnby.reference.demo.v1',version='0.8.6',synthetic=True,databaseBinding=self.server.database_binding,modules=len(MODULES),initialRecords=len(MODULES)*12))
            if u.path=='/api/demo/catalog':return self.json(200,dict(schema='xnby.reference.demo.v1',synthetic=True,version='0.8.6',databaseBinding=self.server.database_binding,token=self.server.demo_token,modules=list(MODULES.values())))
            if u.path=='/api/demo/summary' and set(q)=={'entity'}:return self.json(200,self.server.store.summary(q['entity']))
            if u.path=='/api/demo/records':
                if set(q)-{'entity','q','state','enterprise','page','id'}:raise DemoError(400,'未知查询参数')
                if 'id' in q:return self.json(200,self.server.store.detail(q.get('entity',''),q['id']))
                return self.json(200,self.server.store.list(q.get('entity',''),q.get('q','')[:256],q.get('state',''),q.get('enterprise',''),int(q.get('page','1'))))
            names={'/':'reference-demo.html','/reference-demo.html':'reference-demo.html','/reference-demo.js':'reference-demo.js','/reference-demo.css':'reference-demo.css'}
            name=names.get(u.path)
            if not name:raise DemoError(404,'资源不存在')
            path=self.server.static/name;raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type',{'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[name.rsplit('.',1)[-1]]);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-cache');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
        except DemoError as e:self.json(e.status,dict(error=e.message))
        except (ValueError,KeyError):self.json(400,dict(error='请求参数无效'))
    def do_POST(self):
        try:
            self.trusted(True)
            if self.headers.get('Content-Type')!='application/json':raise DemoError(415,'需JSON请求')
            size=int(self.headers.get('Content-Length','0'))
            if size<2 or size>16384:raise DemoError(413,'请求大小无效')
            value=json.loads(self.rfile.read(size))
            if not isinstance(value,dict):raise DemoError(400,'请求格式无效')
            path=urlsplit(self.path).path
            if path=='/api/demo/transition' and set(value)=={'entity','id','revision','note'}:result=self.server.store.change(value['entity'],value['id'],value['revision'],value['note'])
            elif path=='/api/demo/create' and set(value)=={'entity','fields','enterprise','note'}:result=self.server.store.create(**value)
            else:raise DemoError(400,'模拟操作无效')
            self.json(200,result)
        except DemoError as e:self.json(e.status,dict(error=e.message))
        except (ValueError,TypeError):self.json(400,dict(error='请求格式无效'))

def make_server(port,static,database):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.static=static;server.store=DemoStore(database);server.demo_token=secrets.token_urlsafe(24);server.database_binding=hashlib.sha256(str(database.resolve()).lower().encode()).hexdigest()
    server.allowed_hosts={'127.0.0.1:'+str(server.server_port),'localhost:'+str(server.server_port)}
    return server

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8791);p.add_argument('--static',type=Path,default=root/'web/dist');p.add_argument('--database',type=Path,default=root/'work/reference_demo/demo.sqlite');a=p.parse_args()
    server=make_server(a.port,a.static,a.database);print(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}/',version='0.8.6',synthetic=True),ensure_ascii=False),flush=True);server.serve_forever()
