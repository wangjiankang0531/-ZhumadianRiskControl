"""Exercise the real local nginx transport and original built assets.
The temporary loopback echo server below is a protocol fixture, never an
application backend, and is not used in the prepared unavailable-mode gateway.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote
import base64
import hashlib
import http.client
import json
import socket
import subprocess
import threading
import time
from prepare_original_frontend_gateway import prepare

def run(runtime, roots, output, runtime_sha256):
    NGINX=Path(runtime).resolve()
    ROOTS={k:Path(v).resolve() for k,v in roots.items()}
    RUN=Path(output).resolve()
    assert hashlib.sha256((NGINX/'nginx.exe').read_bytes()).hexdigest()==runtime_sha256
    assert not RUN.exists()
    RUN.mkdir()
    def free_port():
        with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
    
    def request(port,path,method='GET',body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=4)
        try:
            conn.request(method,path,body=body,headers=headers or {})
            r=conn.getresponse();data=r.read()
            return r.status,dict(r.getheaders()),data
        finally:conn.close()
    
    processes=[];process_configs={}
    def start(config_dir,port):
        command=[str(NGINX/'nginx.exe'),'-p',config_dir.as_posix()+'/', '-c',(config_dir/'nginx.conf').as_posix()]
        flags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0
        check=subprocess.run(command+['-t'],capture_output=True,timeout=8,creationflags=flags)
        (config_dir/'config_test.log').write_bytes(check.stdout+check.stderr)
        assert check.returncode==0,'nginx configuration check failed'
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        processes.append(process);process_configs[process.pid]=config_dir
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            assert process.poll() is None,'Owned nginx exited during startup'
            try:
                if request(port,'/')[0]==302:return process
            except (OSError,http.client.HTTPException):pass
            time.sleep(.1)
        raise RuntimeError('Owned nginx did not accept HTTP')
    
    def stop(process,config_dir):
        command=[str(NGINX/'nginx.exe'),'-p',config_dir.as_posix()+'/', '-c',(config_dir/'nginx.conf').as_posix(),'-s','quit']
        result=subprocess.run(command,capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (config_dir/'shutdown.log').write_bytes(result.stdout+result.stderr)
        try:code=process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate();code=process.wait(timeout=4)
            raise RuntimeError('Owned nginx required forced shutdown')
        assert result.returncode==0 and code==0
    
    report={'runtimePinnedSHA256Verified':True,'localTransportOnly':True,'businessAPISynthesized':False,
            'originalBusinessConnections':0,'publicDeployed':False,'businessParityVerified':False}
    fixture=None
    try:
        port=free_port();site=RUN/'unavailable'
        prepare(site,NGINX,ROOTS,port)
        process=start(site,port)
        report['unavailableAPIStatus']=request(port,'/tianjinrisk/api/serv/work/getPage?current=1&size=100')[0]
        assert report['unavailableAPIStatus']==503
        report['unavailablePlatformStatus']=request(port,'/tianjinrisk/api/jnpf/oauth/CurrentUser')[0]
        assert report['unavailablePlatformStatus']==503
        assert request(port,'/tianjinrisk/api/unknown-operation')[0]==404
        redirects=[]
        for kind,prefix in [('emergency_pc','/tianjinrisk/emergency/'),
                            ('mobile','/tianjinrisk/h5/'),('bigscreen','/reference-bigscreen/')]:
            for query in ('','?entry=portal&mode=readonly'):
                status,headers,data=request(port,prefix.rstrip('/')+query)
                assert status==301,kind+': bare mount must redirect before security SPA fallback'
                location=headers['Location']
                from urllib.parse import urlsplit
                parsed=urlsplit(location)
                assert parsed.path==prefix and ('?'+parsed.query if parsed.query else '')==query
                assert not parsed.netloc or parsed.netloc=='127.0.0.1:'+str(port)
                status,headers,data=request(port,parsed.path+('?' + parsed.query if parsed.query else ''))
                assert status==200 and data==(ROOTS[kind]/'index.html').read_bytes()
                redirects.append({'kind':kind,'queryPreserved':bool(query),'status':301,'correctIndexSHA256':True})
        report['bareMountRedirectsVerified']=redirects
        counts={};byte_count=0
        for kind,prefix in [('security_pc','/tianjinrisk/'),('emergency_pc','/tianjinrisk/emergency/'),
                            ('mobile','/tianjinrisk/h5/'),('bigscreen','/reference-bigscreen/')]:
            status,headers,data=request(port,prefix)
            assert status==200 and data==(ROOTS[kind]/'index.html').read_bytes()
            count=0
            for path in sorted(ROOTS[kind].rglob('*')):
                if not path.is_file():continue
                status,headers,data=request(port,prefix+quote(path.relative_to(ROOTS[kind]).as_posix()))
                assert status==200,kind+': original static file unavailable: '+path.name
                assert hashlib.sha256(data).digest()==hashlib.sha256(path.read_bytes()).digest(),'Static response bytes changed'
                count+=1;byte_count+=len(data)
            counts[kind]=count
            status,headers,data=request(port,prefix+'nested/original-route?kept=1')
            assert status==200 and data==(ROOTS[kind]/'index.html').read_bytes()
            assert request(port,prefix+'assets/missing-file.js')[0]==404
        report['staticFilesSHA256Verified']=counts
        report['staticBytesServed']=byte_count
        tile=next(ROOTS['tiles'].rglob('*.png'))
        rel=quote(tile.relative_to(ROOTS['tiles']).as_posix())
        for prefix in ('/tianjinrisk/map/','/tianjinrisk/api/map/'):
            status,headers,data=request(port,prefix+rel)
            assert status==200 and data==tile.read_bytes()
        assert request(port,'/tianjinrisk/map/9999/no-such-tile.png')[0]==404
        assert request(port,'/not-an-original-mount')[0]==404
        report['sharedTileRoutesVerified']=2
        stop(process,site)
    
        observed=[]
        class EchoFixture(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args):pass
            def do_POST(self):self.do_GET()
            def do_GET(self):
                data=self.rfile.read(int(self.headers.get('Content-Length',0)))
                observed.append({'path':self.path,'method':self.command,'bodySHA256':hashlib.sha256(data).hexdigest(),
                                 'fixtureAuthorization':self.headers.get('Authorization')})
                if self.headers.get('Upgrade','').lower()=='websocket':
                    key=self.headers['Sec-WebSocket-Key']
                    accept=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
                    self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade')
                    self.send_header('Sec-WebSocket-Accept',accept);self.end_headers();self.wfile.flush()
                    frame=self.rfile.read(10)
                    assert frame==b'\x81\x84abcd'+bytes(c^b'abcd'[i%4] for i,c in enumerate(b'ping'))
                    self.wfile.write(b'\x81\x04ping');self.wfile.flush();self.close_connection=True;return
                if self.path=='/download?kind=fixture':
                    response=b'\x00\xff\x01\x80'
                    self.send_response(206);self.send_header('Content-Type','application/octet-stream')
                    self.send_header('Content-Disposition','attachment; filename="fixture.bin"')
                    self.send_header('Content-Range','bytes 0-3/4')
                elif self.path=='/missing':
                    response=b'original-style-error-fixture';self.send_response(404)
                else:
                    response=json.dumps({'path':self.path,'method':self.command,'receivedBytes':len(data)}).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json')
                    self.send_header('Set-Cookie','fixture_only=1; Path=/; HttpOnly')
                self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)
        fixture=ThreadingHTTPServer(('127.0.0.1',0),EchoFixture)
        thread=threading.Thread(target=fixture.serve_forever,daemon=True);thread.start()
        fixture_port=fixture.server_address[1]
        proxy_port=free_port();proxy_site=RUN/'transport-fixture'
        prepare(proxy_site,NGINX,ROOTS,proxy_port,fixture_port,fixture_port)
        process=start(proxy_site,proxy_port)
        fixture_header={'Authorization':'Bearer gateway-fixture-only'}
        status,headers,body=request(proxy_port,'/tianjinrisk/api/serv/work/getPage?current=1&size=100',headers=fixture_header)
        assert status==200 and json.loads(body)['path']=='/work/getPage?current=1&size=100'
        assert headers['Set-Cookie']=='fixture_only=1; Path=/; HttpOnly'
        payload=b'fixture=only&not_a_real_account=1'
        status,headers,body=request(proxy_port,'/tianjinrisk/api/jnpf/oauth/Login','POST',payload,fixture_header)
        assert status==200 and json.loads(body)=={'path':'/api/oauth/Login','method':'POST','receivedBytes':len(payload)}
        assert observed[-1]['bodySHA256']==hashlib.sha256(payload).hexdigest()
        assert all(r['fixtureAuthorization']=='Bearer gateway-fixture-only' for r in observed)
        status,headers,body=request(proxy_port,'/tianjinrisk/api/serv/download?kind=fixture')
        assert status==206 and body==b'\x00\xff\x01\x80' and headers['Content-Disposition']=='attachment; filename="fixture.bin"'
        assert headers['Content-Range']=='bytes 0-3/4'
        status,headers,body=request(proxy_port,'/tianjinrisk/api/serv/missing')
        assert status==404 and body==b'original-style-error-fixture'
        with socket.create_connection(('127.0.0.1',proxy_port),timeout=4) as ws:
            ws.sendall(b'GET /tianjinrisk/api/serv/websocket/fixture?mode=only HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: Z2F0ZXdheS1maXh0dXJlIQ==\r\nSec-WebSocket-Version: 13\r\n\r\n')
            head=b''
            while b'\r\n\r\n' not in head:head+=ws.recv(4096)
            assert head.startswith(b'HTTP/1.1 101')
            frame=b'\x81\x84abcd'+bytes(c^b'abcd'[i%4] for i,c in enumerate(b'ping'))
            ws.sendall(frame);reply=b''
            while len(reply)<6:reply+=ws.recv(6-len(reply))
            assert reply==b'\x81\x04ping'
        assert observed[-1]['path']=='/websocket/fixture?mode=only'
        report['transportFixtureChecks']=['business URI/query','platform URI/form POST','authorization header','cookie header',
            'binary 206/content disposition/range','original error status/body','websocket upgrade and bidirectional frame']
        stop(process,proxy_site)
        for closed_port in (port,proxy_port):
            try:
                with socket.create_connection(('127.0.0.1',closed_port),timeout=.5):pass
            except OSError:continue
            raise RuntimeError('Owned gateway port remained open after shutdown')
        report['ownedNginxProcessesStopped']=all(p.poll()==0 for p in processes)
        assert report['ownedNginxProcessesStopped']
        report['success']=True
        (RUN/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False))
    finally:
        if fixture:fixture.shutdown();fixture.server_close()
        for p in processes:
            if p.poll() is None:stop(p,process_configs[p.pid])

def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--runtime-sha256',required=True)
    ap.add_argument('--output',type=Path,required=True)
    for kind in ('security_pc','emergency_pc','mobile','bigscreen','tiles'):
        ap.add_argument('--'+kind.replace('_','-'),type=Path,required=True)
    a=ap.parse_args()
    run(a.runtime,{k:getattr(a,k) for k in ('security_pc','emergency_pc','mobile','bigscreen','tiles')},a.output,a.runtime_sha256)

if __name__=='__main__':main()
