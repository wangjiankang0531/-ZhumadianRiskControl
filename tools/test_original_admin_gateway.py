"""Real nginx transport checks. Fixtures below never represent an application backend."""
import argparse,hashlib,http.client,http.server,json,pathlib,socket,subprocess,sys,threading,time,unittest
from prepare_original_frontend_gateway import prepare


class AdminGatewayConfiguration(unittest.TestCase):
    def test_admin_static_port_cannot_point_to_gateway_or_backend(self):
        for bad in [True,0,80,65536,12000,12001,12002]:
            with self.subTest(port=bad),self.assertRaises(ValueError):
                prepare('unused-fresh-output','unused-runtime',{},12000,12001,12002,base_path='/zhumadian',admin_frontend_port=bad)


def verify_runtime(runtime,output,roots,pin):
    runtime,output=pathlib.Path(runtime).resolve(),pathlib.Path(output).resolve()
    if output.exists():raise ValueError('Fresh gateway evidence directory required')
    if hashlib.sha256((runtime/'nginx.exe').read_bytes()).hexdigest()!=pin:raise ValueError('Nginx runtime SHA mismatch')
    output.mkdir();observed=[]
    class ProtocolFixture(http.server.BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def do_GET(self):self.reply()
        def do_POST(self):self.reply()
        def reply(self):
            body=self.rfile.read(int(self.headers.get('Content-Length',0)))
            row={'fixture':self.server.kind,'path':self.path,'method':self.command,'body':body.decode('ascii'),'authorization':self.headers.get('Authorization'),'cookie':self.headers.get('Cookie')}
            observed.append(row)
            payload=json.dumps(row).encode();status=200 if self.server.kind=='admin-static-protocol-fixture' else 418
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    servers=[];threads=[];processes=[]
    def fixture(kind):
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),ProtocolFixture);server.kind=kind
        worker=threading.Thread(target=server.serve_forever);worker.start();servers.append(server);threads.append(worker);return server.server_port
    def free_port():
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
    def request(port,path,method='GET',body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        try:
            connection.request(method,path,body,headers or {});response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
        finally:connection.close()
    def start(site,port):
        command=[str(runtime/'nginx.exe'),'-p',site.as_posix()+'/', '-c',(site/'nginx.conf').as_posix()]
        checked=subprocess.run(command+['-t'],capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));(site/'configuration_test.log').write_bytes(checked.stdout+checked.stderr);assert checked.returncode==0
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));processes.append((process,command))
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            assert process.poll() is None
            try:
                if request(port,'/')[0]==302:return
            except OSError:pass
            time.sleep(.1)
        raise RuntimeError('Owned nginx not ready')
    result={'protocolFixturesOnly':True,'originalBusinessBackendConnected':False,'loginAttemptPerformed':False,'publicDeployed':False,'businessParityVerified':False}
    try:
        static_port=fixture('admin-static-protocol-fixture');backend_port=fixture('backend-protocol-fixture')
        port=free_port();site=output/'connected'
        prepare(site,runtime,roots,port,backend_port,backend_port,'/zhumadian',static_port);start(site,port)
        status,headers,data=request(port,'/zhumadian/admin?kept=1');assert status==301 and headers['Location'].endswith('/zhumadian/admin/?kept=1')
        status,headers,data=request(port,'/zhumadian/admin/login?redirect=/home');row=json.loads(data)
        assert status==200 and row['fixture']=='admin-static-protocol-fixture' and row['path']=='/zhumadian/admin/login?redirect=/home'
        for method,body in [('GET',None),('POST','fixture-only=1')]:
            status,headers,data=request(port,'/zhumadian/admin/api/oauth/getLoginConfig?fixture=1',method,body,{'Authorization':'Bearer fixture-not-a-token','Cookie':'fixture=only'})
            row=json.loads(data);assert status==418 and row['fixture']=='backend-protocol-fixture' and row['path']=='/api/oauth/getLoginConfig?fixture=1'
            assert row['method']==method and row['body']==(body or '') and row['authorization']=='Bearer fixture-not-a-token' and row['cookie']=='fixture=only'
        assert not any(row['fixture']=='admin-static-protocol-fixture' and '/api/' in row['path'] for row in observed)
        assert request(port,'/zhumadian/admin/api')[0]==404
        status,headers,data=request(port,'/zhumadian/api/jnpf/oauth/getLoginConfig?fixture=1');assert status==418 and json.loads(data)['path']=='/api/oauth/getLoginConfig?fixture=1'
        result.update(adminBareRedirectAndQuery=True,adminStaticMountAndQuery=True,adminAPIBypassesStaticAndSPA=True,bareAdminAPI404=True,GETAndPOSTBodyPreserved=True,authorizationAndCookiePreserved=True,backendErrorStatusAndBodyPreserved=True,existingPlatformProxyPreserved=True)
        unavailable_port=free_port();unavailable=output/'unavailable'
        prepare(unavailable,runtime,roots,unavailable_port,base_path='/zhumadian',admin_frontend_port=static_port);start(unavailable,unavailable_port)
        assert request(unavailable_port,'/zhumadian/admin/api/oauth/getLoginConfig')[0]==503
        assert request(unavailable_port,'/zhumadian/admin/login')[0]==200
        result['unavailableAdminAPI503WithoutSPAFallback']=True
    finally:
        exits=[]
        for process,command in reversed(processes):
            stopped=subprocess.run(command+['-s','quit'],capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            (pathlib.Path(command[2])/'shutdown.log').write_bytes(stopped.stdout+stopped.stderr)
            try:code=process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=4);raise RuntimeError('Owned gateway forced shutdown')
            assert stopped.returncode==0 and code==0;exits.append(code)
        for server in servers:server.shutdown();server.server_close()
        for worker in threads:worker.join(timeout=3);assert not worker.is_alive()
        result.update(ownedNginxExitCodes=exits,ownedFixturesStopped=True,ownedNginxStopped=True)
        (output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    result['passed']=True;(output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result


if __name__=='__main__':
    if sys.argv[1:2]==['verify-runtime']:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--runtime',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True)
        parser.add_argument('--roots-receipt',type=pathlib.Path,required=True);parser.add_argument('--runtime-sha256',required=True)
        args=parser.parse_args(sys.argv[2:]);metadata=json.loads(args.roots_receipt.read_bytes())
        print(json.dumps(verify_runtime(args.runtime,args.output,metadata['roots'],args.runtime_sha256)),flush=True)
    else:unittest.main()
