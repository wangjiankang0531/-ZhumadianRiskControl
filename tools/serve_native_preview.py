"""Loopback-only static viewer for a resource-linked local editor project; stdlib only."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,unquote
from urllib.request import build_opener,ProxyHandler,Request
import argparse,json,os,threading,secrets,hmac,shutil,mimetypes,webbrowser,ctypes,sys,re

SCHEMA='xnby.native.preview.server.v1'
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def store(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temporary,path)
def hide_own_console():
    if os.name!='nt':return
    user=ctypes.windll.user32;kernel=ctypes.windll.kernel32;pids=(ctypes.c_ulong*2)()
    kernel.GetConsoleWindow.restype=ctypes.c_void_p;user.ShowWindow.argtypes=[ctypes.c_void_p,ctypes.c_int]
    if kernel.GetConsoleProcessList(pids,2)==1 and pids[0]==os.getpid():
        window=kernel.GetConsoleWindow()
        if window:user.ShowWindow(window,0)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True);parser.add_argument('--bundle',type=Path);parser.add_argument('--resources',type=Path);parser.add_argument('--layers',type=Path)
    parser.add_argument('--prepared-resource',type=Path,action='append',default=[],help='Explicit fallback resource root; read-only, same scene/catalog only')
    parser.add_argument('--source-budget-mib',type=int,choices=[512,1024,2048],default=512,help='Explicit tracked source-resource budget; not total VRAM')
    parser.add_argument('--hybrid-textures',type=Path,help='Pinned read-only hybrid texture publication')
    parser.add_argument('--prepared-lod',action='store_true',help='Read existing verified fine pages; never run converters or native readers')
    parser.add_argument('--stop',action='store_true');parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    if (args.prepared_resource or args.hybrid_textures) and not args.prepared_lod:parser.error('prepared-resource requires prepared-lod')
    if len(args.prepared_resource)>3:parser.error('At most three fallback resource roots')
    hide_own_console();opener=build_opener(ProxyHandler({}))
    def current():
        if not args.state.is_file():return None
        value=load(args.state)
        if value.get('schema')!=SCHEMA or value.get('host')!='127.0.0.1' or not isinstance(value.get('port'),int) or not 1<=value['port']<=65535:return None
        try:
            with opener.open(f"http://127.0.0.1:{value['port']}/__preview__/health",timeout=2) as r:health=json.load(r)
        except OSError:return None
        return value if health.get('owner')==value.get('owner') and health.get('schema')==SCHEMA else None
    def entry(value):return "" if value.get("preparedLOD") else "?preview=base"
    owned=current()
    if args.stop:
        if not owned:return
        request=Request(f"http://127.0.0.1:{owned['port']}/__preview__/stop",data=b'',method='POST',headers={'X-Preview-Key':owned['controlKey']})
        with opener.open(request,timeout=3) as response:response.read(512)
        return
    if owned:
        if not args.no_browser:webbrowser.open(f"http://127.0.0.1:{owned['port']}/{entry(owned)}")
        return
    args.state.parent.mkdir(parents=True,exist_ok=True)
    lock=args.state.with_suffix('.lock').open('a+b')
    if lock.seek(0,2)==0:lock.write(b'0');lock.flush()
    lock.seek(0)
    if os.name=='nt':
        import msvcrt
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            owned=current()
            if owned:
                if not args.no_browser:webbrowser.open(f"http://127.0.0.1:{owned['port']}/{entry(owned)}")
                return
            raise RuntimeError('Preview service is starting; try again shortly')
    if not all([args.bundle,args.resources,args.layers]):parser.error('bundle, resources and layers are required for a new service')
    bundle=args.bundle.resolve();resource=args.resources.resolve();project=args.layers.resolve()
    if not project.is_file():raise ValueError('Project file is missing')
    files={'/':bundle/'web/index.html','/index.html':bundle/'web/index.html','/viewer.js':bundle/'web/viewer.js','/source-gain-worker.js':bundle/'web/source-gain-worker.js','/layers/default.json':project,'/layers/sample.json':project}
    resources=['data/showcase/zhumadian_native_hierarchy.json','assets/landscape/icons.png','assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin','assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf','assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg','assets/showcase/runtime/zhumadian/full/base_lod_quality.json']
    for rel in resources:
        path=(resource/rel).resolve()
        if not path.is_relative_to(resource) or not path.is_file():raise ValueError('Required existing landscape resource is missing')
        files['/'+rel]=path
    if any(not p.is_file() for p in files.values()):raise ValueError('Preview build is incomplete')
    lod=None
    if args.prepared_lod:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from preview_prepared_lod import PreviewPreparedLOD
        lod=PreviewPreparedLOD(resource,args.prepared_resource)
    hybrid=None
    if args.hybrid_textures:
        from readonly_hybrid_store import ReadOnlyHybridStore
        hybrid=ReadOnlyHybridStore(args.hybrid_textures)
    control=secrets.token_urlsafe(32);owner=secrets.token_hex(16)
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.0'
        def log_message(self,*unused):pass
        def reply(self,status,data,kind='application/json',headers=None):
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));
            for header,value in (headers or {}).items():self.send_header(header,value)
            if getattr(self,'source_marker_sha256',None):self.send_header('X-XNBY-Source-Marker-SHA256',self.source_marker_sha256)
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers()
            if self.command!='HEAD':self.wfile.write(data)
        def do_POST(self):
            origin=self.headers.get('Origin')
            key=self.headers.get('X-Preview-Key','')
            is_lease=bool(lod and re.fullmatch(r'/api/lod-lease/[0-9a-f]{32}/release',self.path))
            if self.headers.get('Host')!=urlsplit(url).netloc or (origin is not None and origin!=url) or (not is_lease and not hmac.compare_digest(key.encode('utf-8'),control.encode('ascii'))):return self.reply(403,b'{"error":"FORBIDDEN"}')
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length','0')!='0':return self.reply(400,b'{"error":"EMPTY_BODY_REQUIRED"}')
            if lod and self.path.startswith('/api/lod-lease/'):
                return lod.handle(self)
            if self.path!='/__preview__/stop':return self.reply(404,b'{"error":"NOT_FOUND"}')
            self.reply(200,b'{"stopping":true}');threading.Thread(target=server.shutdown,daemon=True).start()
        def do_HEAD(self):self.do_GET()
        def do_GET(self):
            if self.headers.get('Host')!=urlsplit(url).netloc:return self.reply(403,b'{"error":"INVALID_HOST"}')
            if hybrid and hybrid.handle(self):return
            if lod and lod.handle(self):return
            path=unquote(urlsplit(self.path).path)
            if lod and path=='/' and 'preview=base' in urlsplit(self.path).query:
                self.send_response(303);self.send_header('Location','/');self.send_header('Content-Length','0');self.end_headers();return
            if path=='/__preview__/status':
                page='<meta charset="utf-8"><title>驻马店网页体验服务</title><h1>网页体验服务正在运行</h1><p>与本机编辑器共用当前标注项目。保存后，在三维页面点击“读取编辑端保存”。</p><p><a href="/?preview=base">打开三维场景</a></p><p>结束体验时，请双击体验文件夹中的“停止网页查看”快捷方式。</p>'
                if lod:page=page.replace('/?preview=base','/').replace('与本机编辑器共用当前标注项目。','只读加载已准备细层，与本机编辑器共用当前标注项目。')
                return self.reply(200,page.encode('utf-8'),'text/html; charset=utf-8')
            if path=='/__preview__/health':return self.reply(200,json.dumps({'schema':SCHEMA,'owner':owner,'mode':'prepared-read-only' if lod else 'static-base-only'}).encode())
            if path=='/application/config.json':return self.reply(200,b'{"schema":"xnby.portal.config.v1","mode":"local"}',headers={'X-XNBY-Source-Budget-MiB':str(args.source_budget_mib)})
            if path=='/api/health':return self.reply(200,b'{"status":"static-preview","nativeReaderEnabled":false}')
            file=files.get(path)
            if lod and re.fullmatch(r'/assets/showcase/runtime/zhumadian/native_hierarchy/tile_[0-9]{1,4}\.json',path):
                catalog_root=(resource/'assets/showcase/runtime/zhumadian/native_hierarchy').resolve()
                candidate=(catalog_root/Path(path).name).resolve()
                if candidate.is_relative_to(catalog_root) and candidate.is_file():file=candidate
            if file is None:return self.reply(404,b'{"error":"NOT_FOUND"}')
            try:
                size=file.stat().st_size
                if file==project and size>16*1048576:return self.reply(413,b'{"error":"PROJECT_TOO_LARGE"}')
                stream=file.open('rb')
            except OSError:return self.reply(503,b'{"error":"FILE_TEMPORARILY_UNAVAILABLE"}')
            with stream:
                kind='text/javascript' if file.suffix=='.js' else (mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
                self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(size));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
                if self.command!='HEAD':
                    try:shutil.copyfileobj(stream,self.wfile,65536)
                    except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);url=f'http://127.0.0.1:{server.server_port}'
    state={'schema':SCHEMA,'owner':owner,'host':'127.0.0.1','port':server.server_port,'PID':os.getpid(),'controlKey':control,'stopped':False,'preparedLOD':bool(lod)}
    store(args.state,state)
    if not args.no_browser:webbrowser.open(url+('/' if lod else '/?preview=base'))
    try:server.serve_forever(poll_interval=.2)
    finally:
        if lod:lod.close()
        server.server_close();state['stopped']=True;state.pop('controlKey');store(args.state,state)
if __name__=='__main__':main()
