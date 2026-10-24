"""Canonical HTTPS forwarding and real nginx transport; no real application or account."""
import argparse
import base64
import hashlib
import http.client
import http.server
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import unittest

from prepare_original_frontend_gateway import checked_public_origin, prepare


class PublicOriginValidation(unittest.TestCase):
    def test_default_and_canonical_origin(self):
        self.assertIsNone(checked_public_origin(None))
        for raw in ['https://www.joinlinksmart.com','https://WWW.JoinLinkSmart.com/','https://www.joinlinksmart.com:443']:
            self.assertEqual(checked_public_origin(raw),'https://www.joinlinksmart.com')

    def test_explicit_nondefault_https_port(self):
        self.assertEqual(checked_public_origin('https://preview.example:8443/'),'https://preview.example:8443')

    def test_unsafe_ambiguous_or_non_origin_values(self):
        bad=[True,'','http://www.example.com','//www.example.com','https://user:secret@www.example.com',
             'https://www.example.com/path','https://www.example.com?x=1','https://www.example.com#x',
             'https://www.example.com:','https://www.example.com:0','https://www.example.com:65536',
             'https://localhost','https://127.0.0.1','https://[::1]','https://-bad.example',
             'https://bad-.example','https://bad..example','https://www.example.com.',
             'https://www.example.com\n','https://www.example.com;return','https://$host.example',
             'https://www.example.com\\path','https://'+('a'*64)+'.example']
        for value in bad:
            with self.subTest(value=value),self.assertRaises(ValueError):checked_public_origin(value)

    def test_rejected_before_output_creation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'unused'
            with self.assertRaises(ValueError):
                prepare(output,Path(tmp),{},12000,public_origin='https://www.example.com/with/path')
            self.assertFalse(output.exists())

    def test_actual_cli_applies_origin_and_rejects_bad_origin(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runtime=root/'runtime';(runtime/'conf').mkdir(parents=True)
            (runtime/'nginx.exe').write_bytes(b'configuration-only-fixture')
            (runtime/'conf/mime.types').write_text('types {}',encoding='ascii')
            command=[sys.executable,'-B',str(Path(__file__).with_name('prepare_original_frontend_gateway.py')),
                     '--runtime',str(runtime),'--port','12000','--base-path','/zhumadian']
            for name in ['security-pc','emergency-pc','mobile','bigscreen','tiles']:
                folder=root/name;folder.mkdir()
                if name!='tiles':(folder/'index.html').write_text('protocol-fixture-only',encoding='ascii')
                command+=['--'+name,str(folder)]
            good=root/'valid';bad=root/'invalid'
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            result=subprocess.run(command+['--output',str(good),'--public-origin','https://www.joinlinksmart.com'],capture_output=True,timeout=8,creationflags=flags)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads((good/'receipt.json').read_bytes())['canonicalPublicOrigin'],'https://www.joinlinksmart.com')
            result=subprocess.run(command+['--output',str(bad),'--public-origin','https://www.example.com/with/path'],capture_output=True,timeout=8,creationflags=flags)
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'Explicit canonical HTTPS DNS origin required',result.stderr)
            self.assertFalse(bad.exists())

    def test_integrated_bad_origin_rejected_before_workspace_or_lock(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);workspace=root/'never-created'
            command=[sys.executable,'-B',str(Path(__file__).with_name('serve_original_integrated_candidate.py')),
                     '--workspace',str(workspace),'--name','own-j999','--previous-receipt',str(root/'absent.json'),
                     '--public-origin','https://www.example.com/with/path']
            result=subprocess.run(command,capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'Explicit canonical HTTPS DNS origin required',result.stderr)
            self.assertFalse(workspace.exists())


def verify_runtime(runtime,output,pin):
    runtime=Path(runtime).resolve(strict=True);output=Path(output).resolve()
    if output.exists():raise ValueError('Fresh owned output required')
    executable=runtime/'nginx.exe'
    if hashlib.sha256(executable.read_bytes()).hexdigest()!=pin:raise ValueError('Fixed nginx pin required')
    output.mkdir();roots={}
    for name in ['security_pc','emergency_pc','mobile','bigscreen','tiles']:
        root=output/'fixture-static'/name;root.mkdir(parents=True);roots[name]=root
        if name!='tiles':(root/'index.html').write_bytes(('protocol-fixture-only:'+name).encode())
    observed=[];processes=[];ports=[];threads=[];fixtures=[]
    result={'protocolFixturesOnly':True,'originalBackendConnected':False,'loginAttempted':False,
            'runtimeSHA256':pin,'publicDeployed':False,'fullCloneReady':False,'passed':False}

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def do_GET(self):self.reply()
        def do_POST(self):self.reply()
        def reply(self):
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=4096:raise ValueError('Fixture body bound')
            body=self.rfile.read(size)
            row={'fixture':self.server.kind,'path':self.path,'method':self.command,'bodySHA256':hashlib.sha256(body).hexdigest(),
                 'headers':{name:self.headers.get(name) for name in ['Host','X-Forwarded-Host','X-Forwarded-Proto',
                    'X-Forwarded-Port','Forwarded','X-Forwarded-Prefix','X-Forwarded-Server','Authorization','Cookie']}}
            observed.append(row)
            if self.headers.get('Upgrade','').lower()=='websocket':
                accept=base64.b64encode(hashlib.sha1((self.headers['Sec-WebSocket-Key']+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
                self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade')
                self.send_header('Sec-WebSocket-Accept',accept);self.end_headers();self.wfile.flush()
                frame=self.rfile.read(10)
                expected=b'\x81\x84abcd'+bytes(v^b'abcd'[i%4] for i,v in enumerate(b'ping'))
                if frame!=expected:raise ValueError('Fixture masked ping expected')
                self.wfile.write(b'\x81\x04ping');self.wfile.flush();self.close_connection=True;return
            payload=json.dumps({'fixture':'protocol-only','observation':row}).encode()
            self.send_response(418);self.send_header('Content-Type','application/json')
            self.send_header('Set-Cookie','fixture-only=1; Path=/; HttpOnly')
            self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

    def free_port():
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
    def request(port,path,method='GET',body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=4)
        try:
            connection.request(method,path,body=body,headers=headers or {})
            response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
        finally:connection.close()
    def start(site,port):
        command=[str(executable),'-p',site.as_posix()+'/', '-c',(site/'nginx.conf').as_posix()]
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        check=subprocess.run(command+['-t'],capture_output=True,timeout=8,creationflags=flags)
        (site/'nginx-test.log').write_bytes(check.stdout+check.stderr)
        if check.returncode:raise RuntimeError('Owned nginx syntax failed')
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        processes.append((process,command,site));ports.append(port);deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Owned nginx exited before ready')
            try:
                if request(port,'/')[0]==302:return
            except OSError:pass
            time.sleep(.1)
        raise RuntimeError('Owned nginx observation timeout')
    def verify_headers(row):
        h=row['headers']
        assert h['Host']==h['X-Forwarded-Host']=='www.joinlinksmart.com'
        assert h['X-Forwarded-Proto']=='https' and h['X-Forwarded-Port']=='443'
        assert h['Forwarded'] is None and h['X-Forwarded-Prefix'] is None and h['X-Forwarded-Server'] is None
        assert h['Authorization']=='Bearer protocol-fixture-not-a-token' and h['Cookie']=='fixture-only=1'

    try:
        def fixture(kind):
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.kind=kind;fixtures.append(server)
            worker=threading.Thread(target=server.serve_forever);worker.start();threads.append(worker);return server.server_port
        backend=fixture('backend-protocol-fixture');static=fixture('admin-static-protocol-fixture')
        local=output/'local';local_port=free_port()
        prepare(local,runtime,roots,local_port,backend,backend,'/zhumadian',static);start(local,local_port)
        status,headers,_=request(local_port,'/zhumadian/h5?kept=1')
        assert status==301 and headers['Location']=='http://127.0.0.1:'+str(local_port)+'/zhumadian/h5/?kept=1'
        status,_,body=request(local_port,'/zhumadian/api/serv/fixture',headers={'Host':'www.joinlinksmart.com','X-Forwarded-Proto':'https'})
        row=json.loads(body)['observation'];assert status==418 and row['headers']['X-Forwarded-Proto']=='http'
        result['legacyLocalAbsoluteRedirectAndHTTPProtocolObserved']=True

        public=output/'public-origin';port=free_port()
        receipt=prepare(public,runtime,roots,port,backend,backend,'/zhumadian',static,public_origin='https://www.joinlinksmart.com')
        assert receipt['bind']=='127.0.0.1' and not receipt['publicProductionReady']
        start(public,port)
        malicious={'Host':'wrong.example:9999','X-Forwarded-Host':'wrong.example:9999',
                   'X-Forwarded-Proto':'http','X-Forwarded-Port':'1',
                   'Forwarded':'for=192.0.2.1;host=wrong.example;proto=http',
                   'X-Forwarded-Prefix':'/wrong','X-Forwarded-Server':'wrong.example',
                   'Authorization':'Bearer protocol-fixture-not-a-token','Cookie':'fixture-only=1'}
        redirects=[('/',302,'/zhumadian/home'),('/zhumadian',302,'/zhumadian/home')]
        for route in ['/zhumadian/h5','/zhumadian/emergency','/zhumadian/admin','/reference-bigscreen']:
            redirects.append((route+'?kept=1',301,route+'/?kept=1'))
        for route,expected,target in redirects:
            status,headers,_=request(port,route,headers=malicious)
            assert status==expected and headers['Location']==target
        result['relativeRedirectsWithQueryPreserved']=len(redirects)
        routes=[('/zhumadian/api/serv/fixture?kept=1','/fixture?kept=1'),
                ('/zhumadian/api/jnpf/fixture','/api/fixture'),
                ('/zhumadian/admin/api/fixture','/api/fixture'),
                ('/zhumadian/admin/fixture','/zhumadian/admin/fixture')]
        payload=b'\x00\xffprotocol-fixture-only'
        for external,target in routes:
            status,headers,body=request(port,external,'POST',payload,malicious)
            response=json.loads(body);row=response['observation']
            assert status==418 and response['fixture']=='protocol-only' and row['path']==target and row['method']=='POST'
            assert row['fixture']==('admin-static-protocol-fixture' if external.startswith('/zhumadian/admin/fixture') else 'backend-protocol-fixture')
            assert row['bodySHA256']==hashlib.sha256(payload).hexdigest()
            assert headers['Set-Cookie']=='fixture-only=1; Path=/; HttpOnly';verify_headers(row)
        result['canonicalOriginProxyRoutesVerified']=len(routes)
        key=base64.b64encode(b'0123456789abcdef').decode()
        with socket.create_connection(('127.0.0.1',port),timeout=4) as ws:
            headers=dict(malicious,Upgrade='websocket',Connection='Upgrade')
            headers.update({'Sec-WebSocket-Key':key,'Sec-WebSocket-Version':'13'})
            request_head='GET /zhumadian/api/serv/websocket/fixture HTTP/1.1\r\n'+''.join(k+': '+v+'\r\n' for k,v in headers.items())+'\r\n'
            ws.sendall(request_head.encode('ascii'));head=b''
            while b'\r\n\r\n' not in head:
                chunk=ws.recv(4096)
                if not chunk or len(head)>16384:raise RuntimeError('Fixture websocket handshake incomplete')
                head+=chunk
            assert head.startswith(b'HTTP/1.1 101')
            ws.sendall(b'\x81\x84abcd'+bytes(v^b'abcd'[i%4] for i,v in enumerate(b'ping')))
            reply=b''
            while len(reply)<6:
                chunk=ws.recv(6-len(reply))
                if not chunk:raise RuntimeError('Fixture websocket frame incomplete')
                reply+=chunk
            assert reply==b'\x81\x04ping'
        verify_headers(observed[-1]);assert observed[-1]['path']=='/websocket/fixture'
        result.update(websocketCanonicalOriginAndBidirectionalFrame=True,
            spoofedOriginHeadersReplacedOrRemoved=True,requestBodyAndSyntheticAuthCookiePreserved=True,
            realApplicationForwardedHeaderHandlingVerified=False,outerTLSIISVerified=False,passed=True)
    finally:
        exits=[]
        for process,command,site in reversed(processes):
            if process.poll() is None:
                stopped=subprocess.run(command+['-s','quit'],capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                (site/'shutdown.log').write_bytes(stopped.stdout+stopped.stderr)
                if stopped.returncode:result['shutdownCommandFailed']=True
                try:code=process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.terminate();code=process.wait(timeout=4);result['forcedTermination']=True
            else:code=process.returncode
            exits.append(code)
        for fixture in fixtures:fixture.shutdown();fixture.server_close()
        for thread in threads:thread.join(timeout=3)
        result.update(ownedNginxExitCodes=exits,ownedFixtureStopped=all(not thread.is_alive() for thread in threads),fixtureServers=len(fixtures))
        if any(code!=0 for code in exits) or result.get('forcedTermination') or result.get('shutdownCommandFailed') or not result['ownedFixtureStopped']:
            result['passed']=False
        result['ownedGatewayPortsClosed']=True
        for closed in ports:
            try:
                with socket.create_connection(('127.0.0.1',closed),timeout=.3):result['ownedGatewayPortsClosed']=False
            except OSError:pass
        result['passed']=result['passed'] and result['ownedGatewayPortsClosed']
        (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if not result['passed']:raise RuntimeError('Owned public-origin protocol validation did not pass')
    return result


if __name__=='__main__':
    if sys.argv[1:2]==['verify-runtime']:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
        parser.add_argument('--runtime-sha256',required=True)
        args=parser.parse_args(sys.argv[2:]);print(json.dumps(verify_runtime(args.runtime,args.output,args.runtime_sha256)),flush=True)
    else:unittest.main()
