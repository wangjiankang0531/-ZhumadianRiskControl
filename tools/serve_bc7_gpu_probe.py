"""One bounded, loopback-only read-only BC7 hardware verification page."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import argparse,hashlib,json,threading,os,re
from urllib.parse import urlsplit
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from readonly_texture_store import ReadOnlyTextureStore
from readonly_landscape_store import owned,read_bytes,duplicates


def validate(folder, expected_sha):
    raw=read_bytes(owned(folder,Path('manifest.json')),1048576)
    if hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError('Pinned manifest SHA differs')
    manifest=json.loads(raw,object_pairs_hook=duplicates)
    if manifest.get('accepted') is not True or not all(m.get('accepted') is True for m in manifest.get('mips',[])):raise ValueError('Unaccepted quality cannot enter GPU probe')
    descriptor=ReadOnlyTextureStore._descriptor(manifest,manifest['sourceSHA256'])
    for row,original in zip(descriptor['mips'],manifest['mips']):
        expected=original.get('pillowDecodedSHA256')
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Invalid independent reference SHA')
        row['pillowDecodedSHA256']=expected
    payload=read_bytes(owned(folder,Path('texture.bc7')),32*1048576)
    if len(payload)!=descriptor['payloadBytes'] or hashlib.sha256(payload).hexdigest()!=descriptor['payloadSHA256']:raise ValueError('Pinned payload differs')
    for row in descriptor['mips']:
        if hashlib.sha256(payload[row['offset']:row['offset']+row['bytes']]).hexdigest()!=row['sha256']:raise ValueError('Mip payload differs')
    return descriptor,payload


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--folder',type=Path,required=True);parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--seconds',type=int,default=120);args=parser.parse_args()
    if not 15<=args.seconds<=300:parser.error('Probe duration must be 15..300 seconds')
    descriptor,payload=validate(args.folder.resolve(strict=True),args.manifest_sha256)
    root=Path(__file__).resolve().parent
    files={'/':('text/html; charset=utf-8',(root/'bc7_gpu_probe.html').read_bytes()),'/probe.js':('text/javascript',(root/'bc7_gpu_probe.js').read_bytes()),'/descriptor.json':('application/json',json.dumps(descriptor).encode()),'/texture.bc7':('application/octet-stream',payload)}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Host')!=urlsplit(url).netloc:self.send_error(403);return
            if self.path not in files:self.send_error(404);return
            mime,raw=files[self.path];self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);url=f'http://127.0.0.1:{server.server_port}';timer=threading.Timer(args.seconds,server.shutdown);timer.daemon=True;timer.start()
    print(json.dumps({'schema':'xnby.bc7.gpu_probe.server.v1','url':url+'/','PID':os.getpid(),'seconds':args.seconds,'payloadBytes':len(payload)}),flush=True)
    try:server.serve_forever(poll_interval=.1)
    finally:timer.cancel();server.server_close();print(json.dumps({'stopped':True}),flush=True)


if __name__=='__main__':main()
