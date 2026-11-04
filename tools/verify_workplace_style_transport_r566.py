"""Exact production Nginx transport on one fresh loopback port; no backend/IIS/public."""
from pathlib import Path
import ctypes,gzip,hashlib,http.client,importlib.util,json,re,socket,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/workplace_style_delivery_r564_20261104';O=R/'work/workplace-style-transport-r566'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=(ctypes.c_ulonglong*8)();m[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))and m[2]>1536*1024**2
assert not O.exists()
release=J(R/'work/r42-mapper-equivalence-r457/r37/bundle/payload/release-manifest.json');payload=J(R/'work/r42-mapper-equivalence-r457/r37/bundle/payload/payload-manifest.json')['files']
branding=A/'tools/original_project_branding_r229.py';prepare=G/'tools/prepare_original_frontend_gateway.py';runtime=G/'runtime/nginx';jobsource=G/'tools/original_server_windows_job.py'
assert sha(branding)==release['controllerFiles']['tools/original_project_branding.py']
assert sha(prepare)==release['controllerFiles']['tools/prepare_original_frontend_gateway.py']
assert sha(jobsource)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
assert sha(runtime/'nginx.exe')==payload['runtime/nginx/nginx.exe']['sha256']
header=G/'tools/original_header_branding.py';assert sha(header)==release['controllerFiles']['tools/original_header_branding.py'];sys.modules['original_header_branding']=load('original_header_branding',header)
sys.modules['original_project_branding']=load('original_project_branding',branding);gateway_module=load('exact_gateway_prepare_r565',prepare);jobs=load('exact_owned_jobs_r565',jobsource)
info=J(D/'prepared-css-delivery-r564.json');old=J(R/'Document/Deployment/workplace_style_delivery_r561_20261104/prepared-css-delivery-r561.json')
assert info['cssSHA256']==old['cssSHA256']
root=R/'work/workplace-style-delivery-r564/payload/frontend/security_pc'
for name,pin in info['files'].items():assert (R/'work/workplace-style-delivery-r564/payload'/name).stat().st_size==pin['bytes']and sha(R/'work/workplace-style-delivery-r564/payload'/name)==pin['sha256']
O.mkdir();minimal=O/'other-static';minimal.mkdir();(minimal/'index.html').write_text('<!doctype html><title>own unused static fixture</title>',encoding='utf-8')
roots={k:(root if k=='security_pc'else minimal)for k in ['security_pc','emergency_pc','mobile','bigscreen','tiles']}
with socket.socket()as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
assert port not in [8767,18891,18892]
config_root=O/'gateway';gateway_module.prepare(config_root,runtime,roots,port,base_path='/zhumadian',public_origin='https://www.joinlinksmart.com',project_name='驻马店重大风险防控')
cmd=[str(runtime/'nginx.exe'),'-p',config_root.as_posix()+'/', '-c',str(config_root/'nginx.conf')]
terminals=[]
def terminal(proc,job,name):
 proc.wait(timeout=20);deadline=time.monotonic()+10
 while job.active_processes()and time.monotonic()<deadline:time.sleep(.1)
 active=job.active_processes();row={'name':name,'exitCode':proc.returncode,'actualDescendants':active,'forced':False};terminals.append(row)
 assert proc.returncode==0 and active==0,'NORMAL_OWN_PROCESS_EXIT_REQUIRED'
 job.close();return row

def short(args,name):
 with (O/(name+'.private.log')).open('xb')as log:
  proc=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=jobs.OwnedWindowsJob(proc);return terminal(proc,job,name)

def get(route,method='GET',encoding='gzip',headers=None):
 conn=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
 try:
  conn.request(method,route,headers={'Host':'www.joinlinksmart.com','Accept-Encoding':encoding,**(headers or {})});res=conn.getresponse();raw=res.read();h={k.lower():v for k,v in res.getheaders()};decoded=gzip.decompress(raw)if h.get('content-encoding')=='gzip'and raw else raw
  return {'method':method,'path':route,'status':res.status,'headers':h,'wireBytes':len(raw),'decodedBytes':len(decoded),'decodedSHA256':hashlib.sha256(decoded).hexdigest()},decoded
 finally:conn.close()

short(cmd+['-t'],'syntax')
master=None;job=None;passed=False;rows=[];failure=None
stream=(O/'nginx-process.private.log').open('xb')
try:
 master=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=jobs.OwnedWindowsJob(master)
 deadline=time.monotonic()+8
 while True:
  try:
   with socket.create_connection(('127.0.0.1',port),timeout=.2):break
  except OSError:assert master.poll()is None and time.monotonic()<deadline;time.sleep(.1)
 assert int((config_root/'nginx.pid').read_text('ascii').strip())==master.pid
 route='/zhumadian/assets/css/'+info['cssName'];versioned='/zhumadian/branding-20261025/assets/css/'+info['cssName']
 for name,url,method,encoding in [('css-gzip',route,'GET','gzip'),('css-identity',route,'GET','identity'),('css-weight-zero',route,'GET','gzip;q=0'),('css-query',route+'?v=own-fixture','GET','gzip'),('css-versioned',versioned,'GET','gzip'),('css-head',route,'HEAD','gzip')]:
  row,body=get(url,method,encoding);row['case']=name;rows.append(row)
  assert row['status']==200 and row['headers']['cache-control']=='public, max-age=31536000, immutable'
  assert row['headers']['content-type'].startswith('text/css')
  if method=='HEAD':assert row['wireBytes']==0
  else:assert row['decodedSHA256']==info['cssSHA256']
  if encoding in ['identity','gzip;q=0']:assert 'content-encoding'not in row['headers']
  elif method!='HEAD':assert row['headers']['content-encoding']=='gzip'and row['wireBytes']<row['decodedBytes']
 for name,url in [('home','/zhumadian/home'),('root','/zhumadian/'),('missing-css','/zhumadian/assets/css/missing-123456789abc.css'),('old-root-route','/zhumadian/'+info['cssName'])]:
  row,body=get(url);row['case']=name;rows.append(row)
  assert 'no-store'in row['headers'].get('cache-control','')
  if name in ['home','root']:
   assert row['status']==200;html=body.decode('utf-8');assert versioned in html and 'data-xnby-home-viewport'in html and html.count('data-xnby-workplace-period')==1
  else:assert row['status']==404
 passed=True
except BaseException as e:failure=type(e).__name__+':'+str(e);raise
finally:
 try:
  if master is not None and master.poll()is None:short(cmd+['-s','quit'],'normal-quit')
  if master is not None:terminal(master,job,'master-and-workers')
 finally:
  stream.close();dump(D/'nginx-transport-result-r566.json',{'passed':passed,'failure':failure,'cases':rows,'terminals':terminals,'exactProductionNginxAndGatewayAndCacheSourcePinned':True,'normalQuitAndActualDescendantsZero':bool(terminals)and all(x['exitCode']==0 and x['actualDescendants']==0 for x in terminals),'sameCSSBytesAsBrowserTestedR561':True,'actualIISIntegratedPipelineOrPublicTested':False,'backendDatabaseBrowserOrDesktopUsed':False,'fullCloneReady':False})
print(json.dumps({'passed':True,'transportCases':len(rows),'gzipWireBytes':rows[0]['wireBytes'],'cssDecodedBytes':rows[0]['decodedBytes'],'actualNormalNginxAndDescendantsZero':True,'publicTouched':False}))
