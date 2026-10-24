"""Serve pinned original static files from memory, without extracting or providing a business backend."""
import argparse,collections,datetime,hashlib,http.client,http.server,io,json,mimetypes,os,pathlib,re,subprocess,tarfile,threading,time
from urllib.parse import unquote,urlsplit


def member_name(value,root):
    if not isinstance(value,str) or '\\' in value or any(ord(c)<32 for c in value):raise ValueError('Invalid static member name')
    parts=value.rstrip('/').split('/')
    if not parts or parts[0]!=root or any(part in ('','.','..') for part in parts):raise ValueError('Static member outside pinned root')
    return '/'.join(parts[1:])


def load_archive(path,expected_sha256,root='dist_new',max_compressed=64*1024**2,max_expanded=128*1024**2,max_files=20000):
    if not re.fullmatch(r'[a-f0-9]{64}',expected_sha256) or not re.fullmatch(r'[A-Za-z0-9_-]+',root):raise ValueError('Explicit archive SHA and root required')
    path=pathlib.Path(path)
    if path.stat().st_size>max_compressed:raise ValueError('Compressed archive limit exceeded')
    with path.open('rb') as source:raw=source.read(max_compressed+1)
    if len(raw)>max_compressed or hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('Archive SHA mismatch or limit exceeded')
    files={};entries=set();expanded=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for entry in archive:
            rel=member_name(entry.name,root)
            if entry.name.rstrip('/') in entries:raise ValueError('Duplicate archive member')
            entries.add(entry.name.rstrip('/'))
            if not entry.isdir() and not entry.isfile():raise ValueError('Archive links or special files forbidden')
            if len(entries)>max_files:raise ValueError('Archive member limit exceeded')
            if entry.isdir():continue
            if not rel or entry.size<0:raise ValueError('Invalid regular member')
            expanded+=entry.size
            if expanded>max_expanded:raise ValueError('Expanded archive limit exceeded')
            stream=archive.extractfile(entry);data=stream.read(entry.size+1)
            if len(data)!=entry.size:raise ValueError('Truncated static file')
            files[rel]=data
    if 'index.html' not in files:raise ValueError('Original static index required')
    return files,{'archiveSHA256':expected_sha256,'archiveBytes':len(raw),'files':len(files),'expandedBytes':expanded,'resourcesExtracted':False}


def request_name(target):
    parsed=urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):raise ValueError('Origin-form request required')
    path=unquote(parsed.path,encoding='utf-8',errors='strict')
    if '\\' in path or '//' in path or any(ord(c)<32 for c in path):raise ValueError('Invalid static request path')
    pieces=path.strip('/').split('/')
    if any(piece in ('.','..') for piece in pieces):raise ValueError('Traversal request denied')
    return path.lstrip('/')


class ArchiveServer(http.server.ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=False
    def __init__(self,files,platform_port=None):
        if platform_port is not None and (isinstance(platform_port,bool) or not isinstance(platform_port,int) or not 1024<=platform_port<=65535):raise ValueError('Explicit loopback platform port required')
        self.files=files;self.counts=collections.Counter();self.api_reads=collections.Counter();self.unavailable_reads=collections.Counter();self.bytes_served=0;self.static_bytes_served=0
        self.platform_port=platform_port;self.original_reads=[]
        super().__init__(('127.0.0.1',0),ArchiveHandler)


class ArchiveHandler(http.server.BaseHTTPRequestHandler):
    server_version='OriginalStaticQA'
    sys_version=''
    protocol_version='HTTP/1.1'
    def log_message(self,*args):pass
    def do_HEAD(self):self.serve(False)
    def do_GET(self):self.serve(True)
    def do_POST(self):
        # This fixture never accepts logins, uploads, or other business writes.
        self.close_connection=True;self.respond(503,b'Original backend unavailable','text/plain; charset=utf-8',True)
    do_PUT=do_POST
    do_PATCH=do_POST
    do_DELETE=do_POST
    def respond(self,status,data,kind,body,static=False):
        self.server.counts[status]+=1
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"connect-src 'self'")
        self.end_headers()
        if body:
            try:
                self.wfile.write(data);self.server.bytes_served+=len(data)
                if static:self.server.static_bytes_served+=len(data)
            except (BrokenPipeError,ConnectionResetError):pass
    def serve(self,body):
        try:name=request_name(self.path)
        except (ValueError,UnicodeError):self.respond(400,b'Invalid path','text/plain',body);return
        if name=='api' or name.startswith('api/'):
            self.server.api_reads['/'+name]+=1
            if self.server.platform_port and name in ('api/oauth/getLoginConfig','api/oauth/CurrentUser'):
                connection=http.client.HTTPConnection('127.0.0.1',self.server.platform_port,timeout=8)
                try:
                    connection.request('GET','/'+name+('?' + urlsplit(self.path).query if urlsplit(self.path).query else ''))
                    response=connection.getresponse();data=response.read(2*1024**2+1)
                    if len(data)>2*1024**2:raise ValueError('Original read response limit exceeded')
                    self.server.original_reads.append({'path':'/'+name,'status':response.status,'bodyBytes':len(data),'bodySHA256':hashlib.sha256(data).hexdigest()})
                    self.respond(response.status,data,response.getheader('Content-Type') or 'application/octet-stream',body)
                except (OSError,http.client.HTTPException,ValueError):self.respond(502,b'Owned original backend unavailable','text/plain',body)
                finally:connection.close()
                return
            self.server.unavailable_reads['/'+name]+=1
            self.respond(503,b'Original backend unavailable','text/plain; charset=utf-8',body);return
        key=name
        if not key or (key not in self.server.files and '.' not in key.rsplit('/',1)[-1]):key='index.html'
        if key not in self.server.files:self.respond(404,b'Not found','text/plain',body);return
        kind=mimetypes.guess_type(key)[0] or 'application/octet-stream'
        if key.endswith(('.js','.mjs')):kind='application/javascript'
        if key.endswith(('.html','.css','.js','.mjs','.json')):kind+='; charset=utf-8'
        self.respond(200,self.server.files[key],kind,body,static=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=pathlib.Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--output',type=pathlib.Path,required=True);parser.add_argument('--minutes',type=int,default=15)
    parser.add_argument('--platform-owner-root',type=pathlib.Path)
    args=parser.parse_args()
    if not 1<=args.minutes<=20:raise ValueError('Bounded independent test duration required')
    output=args.output.resolve()
    if output.exists():raise ValueError('Fresh evidence directory required')
    output.mkdir(parents=True)
    files,receipt=load_archive(args.archive,args.sha256)
    platform_port=None;owner_pid=None
    if args.platform_owner_root:
        owner_root=args.platform_owner_root.resolve()
        if not re.fullmatch(r'own-pboot-r[1-9][0-9]*',owner_root.name):raise ValueError('Owned platform run required')
        preparation=json.loads((owner_root/'preparation.json').read_bytes())
        if preparation['sourceJarSHA256']!='294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8':raise ValueError('Original runtime identity differs')
        if not (owner_root/'own-platform-ready.txt').is_file():raise ValueError('Original context not ready')
        platform_port=int((owner_root/'own-platform-http-port.txt').read_text())
        if not 1024<=platform_port<=65535:raise ValueError('Invalid original loopback port')
        marker='-Down.platform.root='+str(owner_root)+' '
        literal=marker.replace("'","''")
        java_path=str(pathlib.Path(preparation.get('platformJavaHome',preparation['javaHome']))/'bin/java.exe').replace("'","''")
        script="$ErrorActionPreference='Stop'; $listener=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort "+str(platform_port)+" -State Listen; $owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess); if ($owner.CommandLine.IndexOf('"+literal+"',[StringComparison]::OrdinalIgnoreCase) -lt 0 -or -not [String]::Equals($owner.ExecutablePath,'"+java_path+"',[StringComparison]::OrdinalIgnoreCase)) { throw 'Different platform owner' }; $owner.ProcessId"
        checked=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if checked.returncode!=0:raise ValueError('Original loopback listener ownership not verified')
        owner_pid=int(checked.stdout.strip())
    server=ArchiveServer(files,platform_port);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    receipt.update(recordedAt=datetime.datetime.now().astimezone().isoformat(),pid=os.getpid(),url='http://127.0.0.1:'+str(server.server_port)+'/',
                   businessBackendConnected=False,originalPlatformReadOnlyProxy=platform_port is not None,originalPlatformOwnerPID=owner_pid,
                   permittedOriginalGETPaths=['/api/oauth/getLoginConfig','/api/oauth/CurrentUser'] if platform_port else [],
                   loginPOSTPermitted=False,businessParityVerified=False,fullCloneReady=False)
    (output/'ready.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps({'state':'ready','url':receipt['url'],'files':len(files),'resourcesExtracted':False}),flush=True)
    try:
        deadline=time.monotonic()+args.minutes*60
        while not (output/'stop').exists() and time.monotonic()<deadline:
            if not worker.is_alive():raise RuntimeError('Owned static server unexpectedly stopped')
            time.sleep(.25)
    finally:
        server.shutdown();server.server_close();worker.join(timeout=3)
        receipt.update(finishedAt=datetime.datetime.now().astimezone().isoformat(),ownedServerStopped=not worker.is_alive(),
                       statusCounts=dict(server.counts),apiReadPaths=dict(server.api_reads),unavailableAPIReads=dict(server.unavailable_reads),
                       responseBytesServed=server.bytes_served,staticBytesServed=server.static_bytes_served,
                       originalReadResponses=server.original_reads,
                       resourcesExtracted=False,originalSourceChanged=False)
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    assert receipt['ownedServerStopped'];print(json.dumps({'state':'stopped'}),flush=True)


if __name__=='__main__':main()
