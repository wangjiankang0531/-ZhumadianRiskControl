"""Owned frontend QA against the fixed existing read-only runtime; no native launch."""
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs,unquote
import argparse,datetime,hashlib,json,math,os,re,secrets,socket,struct,threading,time,urllib.request,urllib.error,zlib

IDENTITY='f6a5758586635b70025773c3e40083e0c51c7bc01cc02db74cf491233dd7293a'
def runtime_source(port=None,service_pid=None,reader_pid=None):
 values=(port,service_pid,reader_pid)
 if all(v is None for v in values):port,service_pid,reader_pid=8768,45700,57944
 elif any(v is None for v in values):raise ValueError('source port and both expected process IDs must be supplied together')
 if any(type(v) is not int for v in (port,service_pid,reader_pid)) or not 1024<=port<=65535 or any(not 1<=v<=0xffffffff for v in (service_pid,reader_pid)) or service_pid==reader_pid:raise ValueError('invalid explicit runtime identity')
 return {'base':'http://127.0.0.1:'+str(port),'port':port,'servicePID':service_pid,'readerPID':reader_pid}

def verify_protected_runtime(value,source):
 if not isinstance(value,dict) or not isinstance(value.get('worker'),dict):raise ValueError('existing runtime identity unavailable')
 worker=value['worker']
 required=(value.get('schema')=='zhumadian.source.runtime.status.v1',value.get('identity')==IDENTITY,
  type(value.get('pid')) is int and value['pid']==source['servicePID'],type(worker.get('pid')) is int and worker['pid']==source['readerPID'],
  type(worker.get('starts')) is int and worker['starts']==1,worker.get('alive') is True,worker.get('handshakeComplete') is True,
  worker.get('failed') is False,value.get('readOnly') is True,value.get('conversionEnabled') is False,
  type(value.get('protectedWrites')) is int and value['protectedWrites']==0)
 if not all(required):raise ValueError('existing runtime identity or read-only health differs')
 return value

FLAGS=set('topic mode levelIndex levelCut lodDebug qa profile inspect height witness witnessArchive pageLoads budgetAudit rootFloor planAhead qualityAudit textureFirst textureTier admissionAudit knownCost traceConsole profileMode familyAhead texelGuard clientCrop sourceYield sourceSampling residencyAudit surfacePair'.split())
def trusted_request(headers,method,path,expected_host):
 if headers.get('Host')!=expected_host:return False
 if headers.get('Sec-Fetch-Site') in (None,'none','same-origin'):return True
 # A browser extension can initiate a top-level navigation from another site.
 # Permit only the entry document; subresources and every POST stay same-origin.
 return method=='GET' and urlsplit(path).path=='/' and headers.get('Sec-Fetch-Mode')=='navigate' and headers.get('Sec-Fetch-Dest')=='document'
def query(path):return parse_qs(urlsplit(path).query,strict_parsing=True,max_num_fields=len(FLAGS),keep_blank_values=True)
def allowed_route(path,leases,indexed):
 u=urlsplit(path);route=unquote(u.path)
 if len(path)>4096 or u.scheme or u.netloc or u.fragment or '\\' in route or any(s in ('.','..') for s in route.split('/')):return None
 q=query(path)
 if any(len(v)!=1 for v in q.values()):return None
 if route=='/':return 'static' if set(q)<=FLAGS else None
 if route in ('/application/config.json','/api/health','/api/prepared-textures','/api/level-index/status','/layers/default.json','/business/default.json','/spatial/default.json','/data/showcase/zhumadian_native_hierarchy.json'):return 'static' if not q else None
 if not q and (re.fullmatch(r'/api/level-index/files/[A-Za-z0-9_./-]+',route) or route.startswith(('/assets/','/markers/')) or re.fullmatch(r'/prepared-textures/[0-9a-f]{64}/[0-9a-f]{64}/(?:manifest.json|texture.bc7)',route)):return 'static'
 m=re.fullmatch(r'/native/(?:tile_[0-9]+_depth_[0-9]+|family_tile_[0-9]+_[0-9a-f]{16})/part_[0-9]{3}/(?:geometry\.gltf|geometry\.bin|texture\.png|atlas\.jpg)',route)
 if m:return 'payload' if set(q)=={'lease'} and q['lease'][0] in leases else None
 m=re.fullmatch(r'/api/(lod|lod-plan)/([0-9]+)/([0-9]+)',route)
 if m:
  if not 1<=int(m[2])<=2346 or not 1<=int(m[3])<=12:return None
  if m[1]=='lod':return 'grant' if not q else None
  return 'plan' if set(q)<={'wait_ms'} and ('wait_ms' not in q or q['wait_ms'][0].isdigit() and 0<=int(q['wait_ms'][0])<=200) else None
 m=re.fullmatch(r'/api/(lod-family|lod-family-plan|lod-index-family-plan)/([0-9]+)/(Tile_([0-9]+)_L[0-9]+_0[0-9u]+\.osgb)',route)
 if m:
  if not 1<=int(m[2])<=2346 or m[2]!=m[4]:return None
  if m[1]=='lod-family':return 'grant' if not q else None
  if 'wait_ms' in q and (not q['wait_ms'][0].isdigit() or not 0<=int(q['wait_ms'][0])<=200):return None
  if m[1]=='lod-family-plan':return 'plan' if set(q)<={'wait_ms'} else None
  if set(q) not in ({'view'},{'view','wait_ms'}) or len(q['view'][0])>512:return None
  try:v=list(map(float,q['view'][0].split(',')))
  except ValueError:return None
  return 'plan' if len(v)==10 and all(math.isfinite(n) for n in v) and all(abs(n)<=1e7 for n in v[:6]) and 0<v[6]<179 and v[7]>0 and 1<=v[8]<=16384 and .25<=v[9]<=512 else None
 m=re.fullmatch(r'/api/lod-index-family/([0-9]+)/([0-9a-f]{32})',route)
 if m:return 'grant' if not q and 1<=int(m[1])<=2346 and m[2] in indexed else None
 return None

def png_info(raw):
 if not 33<=len(raw)<=8*1048576 or raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('invalid bounded PNG')
 at=8;first=True;ended=False;size=None
 while at<len(raw):
  if at+12>len(raw):raise ValueError('truncated PNG chunk')
  n=struct.unpack_from('>I',raw,at)[0];kind=raw[at+4:at+8];end=at+12+n
  if end>len(raw) or zlib.crc32(raw[at+4:at+8+n])&0xffffffff!=struct.unpack_from('>I',raw,at+8+n)[0]:raise ValueError('PNG chunk CRC differs')
  if first:
   if kind!=b'IHDR' or n!=13:raise ValueError('PNG IHDR missing')
   width,height=struct.unpack_from('>II',raw,at+8)
   if not 1<=width<=8192 or not 1<=height<=8192:raise ValueError('PNG dimensions exceed bound')
   size=[width,height];first=False
  if kind==b'IEND':
   if n or end!=len(raw):raise ValueError('PNG trailing data')
   ended=True
  at=end
 if not ended:raise ValueError('PNG IEND missing')
 return size

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k):raise PermissionError('upstream redirect refused')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-port',type=int);parser.add_argument('--expected-service-pid',type=int);parser.add_argument('--expected-reader-pid',type=int);parser.add_argument('--static',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--case',choices=['baseline_near','crop_near','baseline_mid','crop_mid'],required=True);parser.add_argument('--source-yield',choices=['frame','task'],default='frame');parser.add_argument('--source-sampling',choices=['legacy','centroid'],default='legacy');parser.add_argument('--plan-lookahead',choices=['off','root','both'],default='off');parser.add_argument('--residency-audit',action='store_true');parser.add_argument('--surface-pair',action='store_true');parser.add_argument('--timeout',type=int,default=600);parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if not 60<=args.timeout<=1200:parser.error('bounded runtime required')
 try:source=runtime_source(args.source_port,args.expected_service_pid,args.expected_reader_pid)
 except ValueError as error:parser.error(str(error))
 P=args.static.resolve(strict=True);C=args.output.resolve();assert all((P/n).is_file() for n in ('index.html','viewer.js','source-gain-worker.js'))
 base=source['base'];opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect());owner=secrets.token_hex(16);nonce=secrets.token_hex(16);leases=set();indexed=set();lock=threading.RLock();closing=threading.Event();started=time.monotonic()
 def upstream(path,method='GET'):
  request=urllib.request.Request(base+path,method=method,headers={'Content-Length':'0'} if method=='POST' else {})
  try:return opener.open(request,timeout=30)
  except urllib.error.HTTPError as error:return error
 def protected():
  with upstream('/api/runtime/status') as f:v=json.load(f)
  return verify_protected_runtime(v,source)
 before=protected()
 if args.check:print(json.dumps({'mode':'check_only','nativeStarts':0,'protectedPid':before['pid']}));return
 C.mkdir(parents=True,exist_ok=False);stats={'upstreamGets':0,'ownLeaseReleases':0,'denied':0,'errors':0,'archiveCount':0};report={'kind':'owned_existing_viewer_qa','state':'starting','pid':os.getpid(),'case':args.case,'sourceRuntime':source,'sourceYield':args.source_yield,'sourceSampling':args.source_sampling,'planLookahead':args.plan_lookahead,'residencyAudit':args.residency_audit,'surfacePair':args.surface_pair,'owner':owner,'nativeStarts':0,'protectedBefore':before,'viewerSHA256':hashlib.sha256((P/'viewer.js').read_bytes()).hexdigest(),'runtimeLimitSeconds':args.timeout,'archive':[],'routes':[]}
 def save():
  with lock:
   pending=C/'runtime.pending.json';pending.write_text(json.dumps(report,indent=2),encoding='utf-8');pending.replace(C/'runtime.json')
 def release(token):
  with lock:
   if token not in leases:raise PermissionError('foreign lease release refused')
  with upstream('/api/lod-lease/'+token+'/release','POST') as f:
   if f.status!=204:raise RuntimeError('owned upstream lease release failed')
  with lock:leases.discard(token);stats['ownLeaseReleases']+=1
 class Handler(BaseHTTPRequestHandler):
  protocol_version='HTTP/1.0';disable_nagle_algorithm=True
  def setup(self):super().setup();self.connection.settimeout(30)
  def trusted(self):return trusted_request(self.headers,self.command,self.path,f'127.0.0.1:{server.server_port}')
  def log_message(self,*a):pass
  def send_json(self,value,code=200):
   raw=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
  def do_GET(self):
   if not self.trusted() or closing.is_set():return self.send_error(403)
   if self.path=='/qa/witness-capability.json':return self.send_json({'schema':'xnby.witness_archive.v1','nonce':nonce,'targets':[5000,20000,40000]})
   route=urlsplit(self.path).path
   if route in ('/','/index.html','/viewer.js','/source-gain-worker.js'):
    if route=='/':
     if allowed_route(self.path,leases,indexed) is None:return self.send_error(403)
    elif urlsplit(self.path).query:return self.send_error(403)
    name=route.lstrip('/') or 'index.html';raw=(P/name).read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if name=='index.html' else 'text/javascript');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
   try:
    with lock:kind=allowed_route(self.path,leases,indexed)
    if kind is None:stats['denied']+=1;return self.send_error(403)
    start=time.monotonic()
    with upstream(self.path) as response:
     n=int(response.headers.get('Content-Length','-1'));limit=(16*1048576+2048) if kind in ('plan','grant') else 1024*1048576
     if not 0<=n<=limit:raise ValueError('bounded upstream response required')
     raw=None
     if kind in ('plan','grant'):
      raw=response.read(n+1)
      if len(raw)!=n:raise ValueError('truncated source metadata')
      if response.status==200:
       value=json.loads(raw)
       with lock:
        if kind=='plan' and re.fullmatch('[0-9a-f]{32}',str(value.get('indexedRequest',''))):indexed.add(value['indexedRequest'])
        if kind=='grant':
         token=value.get('cache_lease');assert isinstance(token,str) and re.fullmatch('[0-9a-f]{32}',token);leases.add(token)
     self.send_response(response.status)
     for name in ('Content-Length','Content-Type','X-XNBY-Source-Marker-SHA256','X-XNBY-Level-Index-SHA256'):
      value=response.headers.get(name)
      if value:self.send_header(name,value)
     self.send_header('Cache-Control','no-store');self.end_headers()
     if raw is not None:self.wfile.write(raw)
     else:
      while n:
       chunk=response.read(min(n,1048576))
       if not chunk:raise ValueError('truncated upstream payload')
       self.wfile.write(chunk);n-=len(chunk)
     with lock:
      stats['upstreamGets']+=1
      if len(report['routes'])<4096:report['routes'].append({'route':route,'kind':kind,'ms':(time.monotonic()-start)*1000})
     save()
   except (OSError,ValueError,AssertionError,TypeError) as e:
    stats['errors']+=1;report['lastError']=str(e)[:512];save()
    try:self.send_error(502)
    except OSError:pass
  def do_POST(self):
   if not self.trusted() or self.headers.get('Transfer-Encoding'):return self.send_error(403)
   if self.path=='/__stop' and self.headers.get('X-QA-Owner')==owner and self.headers.get('Content-Length','0')=='0':
    closing.set();self.send_response(204);self.send_header('Content-Length','0');self.end_headers();threading.Thread(target=server.shutdown,daemon=True).start();return
   m=re.fullmatch('/api/lod-lease/([0-9a-f]{32})/release',self.path)
   if m and self.headers.get('Content-Length','0')=='0':
    try:release(m[1])
    except (PermissionError,OSError,RuntimeError):return self.send_error(403)
    self.send_response(204);self.send_header('Content-Length','0');self.end_headers();return
   m=re.fullmatch('/qa/witness/(5000|20000|40000)',self.path)
   if m and secrets.compare_digest(self.headers.get('X-Witness-Archive',''),nonce):
    try:
     n=int(self.headers.get('Content-Length','-1'));elapsed=float(self.headers.get('X-Witness-Elapsed-Ms','nan'));target=int(m[1]);assert 0<n<=8*1048576 and math.isfinite(elapsed) and target<=elapsed<=180000 and self.headers.get('Content-Type')=='image/png'
     raw=self.rfile.read(n);assert len(raw)==n;size=png_info(raw);filename=str(target)+'_scene.png';path=C/filename
     with path.open('xb') as f:f.write(raw)
     receipt={'targetMs':target,'actualElapsedMs':elapsed,'filename':filename,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest(),'dimensions':size,'receivedUTC':datetime.datetime.now().astimezone().isoformat(),'serverSeconds':time.monotonic()-started}
     (C/(str(target)+'_receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
     with lock:report['archive'].append(receipt);stats['archiveCount']+=1
     save();return self.send_json(receipt,201)
    except FileExistsError:return self.send_error(409)
    except (ValueError,AssertionError,OSError):return self.send_error(422)
   stats['denied']+=1;return self.send_error(403)
 class Server(ThreadingHTTPServer):
  allow_reuse_address=False;daemon_threads=False;block_on_close=True
  def server_bind(self):
   if os.name=='nt':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
   return super().server_bind()
 server=Server(('127.0.0.1',0),Handler)
 height=350 if args.case.endswith('mid') else 100;crop=1 if args.case.startswith('crop') else 0
 q=f'?topic=emergency&mode=command&levelIndex=1&levelCut=1&lodDebug=1&qa=1&profile=1&inspect=-317,-1988,43&height={height}&witness=1&witnessArchive=1&pageLoads=1&budgetAudit=1&rootFloor=0&planAhead={int(args.plan_lookahead!='off')}&qualityAudit=1&textureFirst=1&textureTier=alternate&admissionAudit=1&knownCost=1&traceConsole=0&profileMode=manual&familyAhead={int(args.plan_lookahead=='both')}&texelGuard=0&clientCrop={crop}&sourceYield={args.source_yield}&sourceSampling={args.source_sampling}&residencyAudit={int(args.residency_audit)}&surfacePair={int(args.surface_pair)}'
 report.update(state='ready',port=server.server_port,url=f'http://127.0.0.1:{server.server_port}/'+q);save();print(json.dumps({k:report[k] for k in ('state','case','pid','port','url','nativeStarts')}),flush=True)
 timer=threading.Timer(args.timeout,server.shutdown);timer.daemon=True;timer.start()
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:
  closing.set();timer.cancel();server.server_close()
  failures=[]
  for token in list(leases):
   try:release(token)
   except Exception as e:failures.append(str(e)[:512])
  report.update(state='stopped',stats=stats,seconds=time.monotonic()-started,remainingOwnLeases=len(leases),releaseErrors=failures,protectedAfter=protected());save();print(json.dumps({'state':'stopped','case':args.case,'remainingOwnLeases':len(leases),'stats':stats}),flush=True)
if __name__=='__main__':main()
