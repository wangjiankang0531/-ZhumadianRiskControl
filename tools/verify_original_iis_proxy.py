from pathlib import Path
import argparse,hashlib,http.server,json,os,subprocess,threading

parser=argparse.ArgumentParser(description='Owned loopback HTTP contract; no original backend or IIS runtime test.')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--application',type=Path,default=Path(__file__).resolve().parents[1])
args=parser.parse_args();app=args.application.resolve(strict=True)
stage=args.output.resolve();assert not stage.exists();stage.mkdir(parents=True)
source=app/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs'
worker=app/'tools/iis_reference_proxy_contract.cs'
csc=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe');assembly=stage/'proxy-contract.exe'
cmd=[str(csc),'/nologo','/target:exe','/out:'+str(assembly),'/r:System.Web.dll','/r:System.Configuration.dll','/r:System.Web.Extensions.dll',str(source),str(worker),str(app/'tools/original_iis_proxy_contract_main.cs')]
compiled=subprocess.run(cmd,capture_output=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
(stage/'compile.log').write_bytes(compiled.stdout+compiled.stderr);assert compiled.returncode==0
handled=subprocess.run([str(assembly)],capture_output=True,timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
(stage/'handled-failure.stderr.log').write_bytes(handled.stderr)
assert handled.returncode==1 and b'FIXTURE_FAILED: System.ArgumentException:' in handled.stderr
large=b'x'*(3*1024*1024);observed=[]
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def handle_request(self):
        with (stage/'http-progress.log').open('a') as f:f.write(self.command+' '+self.path+'\n')
        body=self.rfile.read(int(self.headers.get('Content-Length','0')))
        observed.append(dict(path=self.path,method=self.command,authorization=self.headers.get('Authorization'),bodySHA256=hashlib.sha256(body).hexdigest(),range=self.headers.get('Range')))
        if self.path.endswith('/large'):status=200;payload=large
        elif self.path.endswith('/denied'):status=403;payload=b'original-backend-denied-fixture'
        elif self.path.endswith('/range'):status=206;payload=b'0123'
        elif self.command=='OPTIONS':status=204;payload=b''
        else:status=200;payload=b'transport-fixture-only'
        self.send_response(status);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(payload)))
        self.send_header('Set-Cookie','transport_fixture=owned; Path=/zhumadian/; HttpOnly')
        if status==206:self.send_header('Content-Range','bytes 0-3/10')
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(payload)
    do_GET=handle_request;do_POST=handle_request;do_PUT=handle_request;do_DELETE=handle_request;do_PATCH=handle_request;do_OPTIONS=handle_request;do_HEAD=handle_request
server=http.server.ThreadingHTTPServer(('127.0.0.1',18892),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
cases=[]
for name,method,suffix in [('large','GET','large'),('put','PUT','put'),('patch','PATCH','patch'),('delete','DELETE','delete'),('head','HEAD','head'),('options','OPTIONS','options'),('denied','GET','denied'),('range','GET','range')]:
    headers={'Authorization':'Bearer synthetic-transport-fixture'}
    if name=='range':headers['Range']='bytes=0-3'
    cases.append(dict(name=name,path='/zhumadian/_transport/'+suffix,method=method,secure=True,host='www.joinlinksmart.com',body='{"fixture":"owned"}' if method in ['PUT','PATCH','DELETE'] else '',headers=headers))
cases += [dict(name='traversal',path='/zhumadian/%2e%2e/private',method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={}),dict(name='wrong-host',path='/zhumadian/home',method='GET',secure=True,host='other.invalid',body='',headers={}),dict(name='wrong-method',path='/zhumadian/home',method='CONNECT',secure=True,host='www.joinlinksmart.com',body='',headers={}),dict(name='websocket-no-iis',path='/zhumadian/api/serv/websocket',method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={'Upgrade':'websocket','Connection':'Upgrade'}),dict(name='websocket-wrong-route',path='/zhumadian/private',method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={'Upgrade':'websocket','Connection':'Upgrade'})]
casefile=stage/'cases.json';casefile.write_text(json.dumps(cases),encoding='utf-8')
try:
    try:run=subprocess.run([str(assembly),str(casefile)],capture_output=True,timeout=12,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except subprocess.TimeoutExpired as e:
        (stage/'timeout.json').write_text(json.dumps({'timeoutSeconds':e.timeout,'observedRequests':observed}),encoding='utf-8')
        raise
    (stage/'run.stdout.log').write_bytes(run.stdout);(stage/'run.stderr.log').write_bytes(run.stderr)
    assert run.returncode==0,run.stderr[-1000:]
    results=json.loads(run.stdout.decode('utf-8-sig'));indexed={r['name']:r for r in results}
    assert indexed['large']['status']==200 and indexed['large']['bytes']==len(large) and indexed['large']['sha256']==hashlib.sha256(large).hexdigest()
    for name in ['put','patch','delete','head']:assert indexed[name]['status']==200,(name,indexed[name])
    assert indexed['head']['bytes']==0
    assert indexed['options']['status']==204 and indexed['denied']['status']==403
    assert indexed['range']['status']==206 and indexed['range']['bytes']==4
    assert indexed['traversal']['status']==404 and indexed['wrong-host']['status']==403 and indexed['wrong-method']['status']==405
    assert indexed['websocket-no-iis']['status']==503 and indexed['websocket-wrong-route']['status']==404
    assert len(observed)==8 and all(r['authorization']=='Bearer synthetic-transport-fixture' for r in observed)
    for row in observed:
        if row['method'] in ['PUT','PATCH','DELETE']:assert row['bodySHA256']==hashlib.sha256(b'{"fixture":"owned"}').hexdigest()
    receipt=dict(checks=len(cases),results=results,upstreamRequests=observed,sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),iisRuntimeVerified=False,webSocketRuntimeVerified=False,originalBackendCalled=False,fixtureOnly=True)
    (stage/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['results','upstreamRequests']}))
finally:
    server.shutdown();server.server_close();thread.join(timeout=3)
    assert not thread.is_alive()
