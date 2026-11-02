"""Bounded loopback hardware fixture for a pinned hybrid texture."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
import argparse,hashlib,json,threading,os,sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hybrid_texture import ReadOnlyHybridTexture
from readonly_landscape_store import read_bytes,owned,duplicates
def reference_fixture(source,descriptor,manifest):
    before=source.stat();raw=read_bytes(source,32*1048576)
    if hashlib.sha256(raw).hexdigest()!=descriptor['sourceSHA256']:raise ValueError('Original GPU reference SHA differs')
    with Image.open(source) as loaded:
        if loaded.mode!='RGB' or list(loaded.size)!=descriptor['sourceSize']:raise ValueError('Original GPU reference size differs')
        base=loaded.convert('RGBA')
    start=descriptor['tailStartLevel']-1;rows=[];payload=[];offset=0
    if sum(row['width']*row['height']*4 for row in descriptor['mips'][start:])>1048576:raise ValueError('GPU reference fixture exceeds 1 MiB window')
    for row in descriptor['mips'][start:]:
        image=base.resize((row['width'],row['height']),Image.Resampling.LANCZOS);data=image.tobytes();image.close();digest=hashlib.sha256(data).hexdigest()
        if digest!=manifest['mips'][row['level']]['sourceRgbaSHA256']:raise ValueError('Original GPU reference mip differs')
        payload.append(data);rows.append(dict(level=row['level'],width=row['width'],height=row['height'],offset=offset,bytes=len(data),sha256=digest));offset+=len(data)
    base.close();after=source.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or hashlib.sha256(source.read_bytes()).hexdigest()!=descriptor['sourceSHA256']:raise ValueError('Original GPU reference changed')
    data=b''.join(payload);return dict(startLevel=start,payloadBytes=len(data),payloadSHA256=hashlib.sha256(data).hexdigest(),mips=rows),data
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--reference-source',type=Path,required=True);p.add_argument('--probe-js',type=Path,required=True);p.add_argument('--probe-sha256',required=True);p.add_argument('--seconds',type=int,default=120);args=p.parse_args()
    if not 15<=args.seconds<=300:p.error('Probe seconds must be 15..300')
    store=ReadOnlyHybridTexture(args.folder,args.manifest_sha256);descriptor=store.descriptor();raw=read_bytes(owned(args.folder,Path('manifest.json')),1048576);manifest=json.loads(raw,object_pairs_hook=duplicates)
    refmeta,reference=reference_fixture(args.reference_source,descriptor,manifest);script=read_bytes(args.probe_js,4*1048576)
    if hashlib.sha256(script).hexdigest()!=args.probe_sha256:raise ValueError('GPU script SHA differs')
    files={'/':('text/html; charset=utf-8',Path(__file__).with_name('hybrid_gpu_probe.html').read_bytes()),'/probe.js':('text/javascript',script),'/descriptor.json':('application/json',json.dumps(descriptor).encode()),'/prefix.bc7':('application/octet-stream',store.payload('bc7')),'/tail.rgba':('application/octet-stream',store.payload('rgba8')),'/reference.json':('application/json',json.dumps(refmeta).encode()),'/reference.rgba':('application/octet-stream',reference)}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Host')!=urlsplit(url).netloc:self.send_error(403);return
            if self.path not in files:self.send_error(404);return
            mime,data=files[self.path];self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);url=f'http://127.0.0.1:{server.server_port}';timer=threading.Timer(args.seconds,server.shutdown);timer.daemon=True;timer.start()
    print(json.dumps(dict(url=url+'/',PID=os.getpid(),seconds=args.seconds,hybridBytes=descriptor['payloadBytes'],referenceBytes=len(reference))),flush=True)
    try:server.serve_forever(poll_interval=.1)
    finally:timer.cancel();server.server_close();print(json.dumps(dict(stopped=True)),flush=True)
if __name__=='__main__':main()
