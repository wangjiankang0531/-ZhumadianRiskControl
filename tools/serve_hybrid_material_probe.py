"""Bounded original-geometry Three material fixture; no native processes."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
import argparse,hashlib,json,threading,os,sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hybrid_texture import ReadOnlyHybridTexture
from readonly_landscape_store import read_bytes,owned,duplicates

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--source-part',type=Path,required=True);p.add_argument('--probe-js',type=Path,required=True);p.add_argument('--probe-sha256',required=True);p.add_argument('--seconds',type=int,default=180);args=p.parse_args()
    if not 15<=args.seconds<=300:p.error('seconds must be 15..300')
    store=ReadOnlyHybridTexture(args.folder,args.manifest_sha256);descriptor=store.descriptor();manifest=json.loads(read_bytes(owned(args.folder,Path('manifest.json')),1048576),object_pairs_hook=duplicates)
    complete=json.loads(read_bytes(args.source_part.parent/'complete.json',4*1048576),object_pairs_hook=duplicates);part=next(x for x in complete['parts'] if x['directory']==args.source_part.name)
    sources={}
    for name in ['atlas.jpg','geometry.gltf','geometry.bin']:
        pin=next(x for x in part['files'] if x['name']==name);data=read_bytes(owned(args.source_part,Path(name)),32*1048576)
        if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:raise ValueError('Source part SHA differs: '+name)
        sources[name]=data
    if hashlib.sha256(sources['atlas.jpg']).hexdigest()!=descriptor['sourceSHA256']:raise ValueError('Source photograph differs')
    import io
    with Image.open(io.BytesIO(sources['atlas.jpg'])) as image:
        if image.mode!='RGB' or list(image.size)!=descriptor['sourceSize']:raise ValueError('Source dimensions differ')
        base=image.convert('RGBA')
    rows=[];pieces=[];offset=0
    for row in manifest['mips']:
        mip=base.resize((row['width'],row['height']),Image.Resampling.LANCZOS);data=mip.tobytes();mip.close();digest=hashlib.sha256(data).hexdigest()
        if digest!=row['sourceRgbaSHA256']:raise ValueError('Full original reference mip differs')
        rows.append(dict(level=row['level'],width=row['width'],height=row['height'],offset=offset,bytes=len(data),sha256=digest));pieces.append(data);offset+=len(data)
    overlap_rows=[];overlap_pieces=[];overlap_offset=0
    for row in manifest['mips'][descriptor['tailStartLevel']-2:descriptor['tailStartLevel']]:
        if descriptor['tailStartLevel']<2:raise ValueError('Two overlap levels required')
        mip=base.resize((row['width'],row['height']),Image.Resampling.LANCZOS);data=mip.tobytes();mip.close();digest=hashlib.sha256(data).hexdigest()
        if digest!=row['sourceRgbaSHA256']:raise ValueError('Overlap differs from original proof')
        overlap_rows.append(dict(level=row['level'],width=row['width'],height=row['height'],offset=overlap_offset,bytes=len(data),sha256=digest,sourceRgbaSHA256=digest,accepted=True,quality=dict(rgbPSNR=999,rgbChannelP99=0,rgbMaxError=0)));overlap_pieces.append(data);overlap_offset+=len(data)
    overlap=b''.join(overlap_pieces);overlap_descriptor=dict(schema='xnby.bc7_rgba_overlap.v1',sourceSHA256=descriptor['sourceSHA256'],basePayloadSHA256=descriptor['payloadSHA256'],startLevel=descriptor['tailStartLevel']-2,payloadBytes=len(overlap),payloadSHA256=hashlib.sha256(overlap).hexdigest(),mips=overlap_rows)
    base.close();reference=b''.join(pieces)
    if len(reference)>32*1048576:raise ValueError('Reference exceeds 32 MiB')
    script=read_bytes(args.probe_js,4*1048576)
    if hashlib.sha256(script).hexdigest()!=args.probe_sha256:raise ValueError('Probe SHA differs')
    files={'/':('text/html; charset=utf-8',Path(__file__).with_name('hybrid_material_probe.html').read_bytes()),'/probe.js':('text/javascript',script),'/descriptor.json':('application/json',json.dumps(descriptor).encode()),'/prefix.bc7':('application/octet-stream',store.payload('bc7')),'/tail.rgba':('application/octet-stream',store.payload('rgba8')),'/reference.json':('application/json',json.dumps(dict(payloadBytes=len(reference),payloadSHA256=hashlib.sha256(reference).hexdigest(),mips=rows)).encode()),'/reference.rgba':('application/octet-stream',reference),'/geometry.gltf':('application/json',sources['geometry.gltf']),'/geometry.bin':('application/octet-stream',sources['geometry.bin']),'/source-proof.json':('application/json',json.dumps(dict(vertices=part['vertices'],indices=part['indices'],geometrySHA256=hashlib.sha256(sources['geometry.bin']).hexdigest())).encode())}
    files['/overlap.json']=('application/json',json.dumps(overlap_descriptor).encode());files['/overlap.rgba']=('application/octet-stream',overlap)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Host')!=urlsplit(url).netloc:self.send_error(403);return
            path=urlsplit(self.path).path
            if path not in files:self.send_error(404);return
            mime,data=files[path];self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);url=f'http://127.0.0.1:{server.server_port}';timer=threading.Timer(args.seconds,server.shutdown);timer.daemon=True;timer.start()
    print(json.dumps(dict(url=url+'/',PID=os.getpid(),seconds=args.seconds,hybridBytes=descriptor['payloadBytes'],referenceBytes=len(reference),originalGeometryBytes=len(sources['geometry.bin']))),flush=True)
    try:server.serve_forever(poll_interval=.1)
    finally:timer.cancel();server.server_close();print(json.dumps(dict(stopped=True)),flush=True)
if __name__=='__main__':main()
