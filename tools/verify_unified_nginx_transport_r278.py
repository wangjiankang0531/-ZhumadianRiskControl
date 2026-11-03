from pathlib import Path
import gzip,hashlib,http.client,http.server,importlib.util,json,os,socket,subprocess,sys,threading,time
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).parent;O=V/'static-nginx-r278';assert not O.exists();O.mkdir();sys.path.insert(0,str(T))
from original_server_windows_job_graceful_20261101 import OwnedWindowsJob
from prepare_original_frontend_gateway import prepare
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=J(V/'static-transport-r277/baseline/exit.json');assert prior=={'processExit':0,'normalQuitReturn':0,'ownedActiveProcesses':0}
dump(O/'prior-test-refused.json',{'priorNewTestExecutableStartRefused':True,'error':'PermissionError.WinError5','priorNginxNormalExitAndDescendantsZero':True,'quarantineRestoredOrAVSettingsChanged':False,'newAspNetTransportAcceptanceClaimed':False})
roots={'security_pc':R/'work/user_feedback_20261031/avatar-full-r157/security_pc/build/dist','emergency_pc':R/'work/user_feedback_20261031/plan-exercise-retained-r224/dist'};manifest=J(R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle/payload/payload-manifest.json')['files'];pins={}
for role,root in roots.items():
 rows={n.split('/',2)[2]:p for n,p in manifest.items()if n.startswith('frontend/'+role+'/')}
 for n,p in rows.items():b=(root/n).read_bytes();assert len(b)==p['bytes']and sha(b)==p['sha256']
 pins[role]={'files':len(rows),'allExactR38StaticFilesPinned':True}
for role in ['mobile','bigscreen','tiles']:
 root=O/('own-'+role);root.mkdir();(root/'index.html').write_text('<!doctype html><title>own static fixture</title>',encoding='utf-8');roots[role]=root
s=socket.socket();s.bind(('127.0.0.1',18892));s.close();observed=[]
class Backend(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  observed.append({'path':self.path,'authorizationPreserved':self.headers.get('Authorization')=='Bearer synthetic-transport-fixture','cookiePreserved':self.headers.get('Cookie')=='transport_fixture=owned'})
  b=json.dumps({'marker':'天津南港危化品智慧物流园','fixtureOnly':True},ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Backend);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
paths={'security-js':'/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js','emergency-js':'/zhumadian/emergency/branding-20261025/assets/js/wf-index-CeoNouGN.js','security-css':'/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css','emergency-css':'/zhumadian/emergency/branding-20261025/assets/css/index-D0NHlCez.css','security-html':'/zhumadian/home','emergency-html':'/zhumadian/emergency/home/index','api':'/zhumadian/api/serv/performance-fixture','missing-hash':'/zhumadian/branding-20261025/assets/js/absent-ABCDEFGH.js','non-hash':'/zhumadian/assets/nonhashed.js'}
cases=[{'name':name,'path':path,'method':'GET','encoding':'gzip'}for name,path in paths.items()]+[{'name':'identity','path':paths['security-js'],'method':'GET','encoding':'identity'},{'name':'explicit-zero','path':paths['security-js'],'method':'GET','encoding':'gzip;q=0, *;q=1'},{'name':'head','path':paths['security-js'],'method':'HEAD','encoding':'gzip'}];dump(O/'cases.json',cases)
runtime=R/'_g/Application/runtime/nginx';results={}
try:
 for mode in ['baseline','candidate']:
  path=T/('original_project_branding.py'if mode=='baseline'else'original_project_branding_r229.py');spec=importlib.util.spec_from_file_location('original_project_branding',path);branding=importlib.util.module_from_spec(spec);spec.loader.exec_module(branding);sys.modules['original_project_branding']=branding
  gateway=O/mode;prepare(gateway,runtime,roots,18892,server.server_port,server.server_port,base_path='/zhumadian',public_origin='https://www.joinlinksmart.com',project_name='驻马店重大风险防控');cmd=[str(runtime/'nginx.exe'),'-p',gateway.as_posix()+'/', '-c',str(gateway/'nginx.conf')]
  checked=subprocess.run(cmd+['-t'],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW);(gateway/'syntax.private.log').write_bytes(checked.stdout+checked.stderr);assert checked.returncode==0
  stream=(gateway/'process.private.log').open('wb');p=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(p)
  try:
   deadline=time.monotonic()+10
   while True:
    try:
     with socket.create_connection(('127.0.0.1',18892),timeout=.2):break
    except OSError:assert p.poll()is None and time.monotonic()<deadline;time.sleep(.1)
   rows=[]
   for case in cases:
    c=http.client.HTTPConnection('127.0.0.1',18892,timeout=20)
    try:
     c.request(case['method'],case['path'],headers={'Host':'www.joinlinksmart.com','Accept-Encoding':case['encoding'],'Authorization':'Bearer synthetic-transport-fixture','Cookie':'transport_fixture=owned','Connection':'close'});r=c.getresponse();headers={k.lower():v for k,v in r.getheaders()};body=r.read(4*1024*1024+1);assert len(body)<=4*1024*1024
     decoded=gzip.decompress(body)if headers.get('content-encoding')=='gzip'and body else body;assert len(decoded)<=4*1024*1024
     rows.append({'name':case['name'],'path':case['path'],'status':r.status,'wireBytes':len(body),'decodedBytes':len(decoded),'decodedSHA256':sha(decoded),'headers':headers})
    finally:c.close()
   results[mode]={row['name']:row for row in rows};dump(gateway/'results.json',{'cases':rows})
  finally:
   stop=subprocess.run(cmd+['-s','quit'],capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
   while p.poll()is None:
    try:p.wait(timeout=20)
    except subprocess.TimeoutExpired:print('OWN_STATIC_NGINX_NORMAL_EXIT_STILL_PENDING_NO_FORCE',flush=True)
   while job.active_processes():time.sleep(.2)
   dump(gateway/'exit.json',{'processExit':p.returncode,'normalQuitReturn':stop.returncode,'ownedActiveProcesses':0});assert p.returncode==0 and stop.returncode==0;job.close();stream.close()
 for name in results['baseline']:
  a=results['baseline'][name];b=results['candidate'][name];assert(a['status'],a['decodedBytes'],a['decodedSHA256'])==(b['status'],b['decodedBytes'],b['decodedSHA256']),name
 savings=[];expected={}
 for name in ['security-js','emergency-js','security-css','emergency-css']:
  a=results['baseline'][name];b=results['candidate'][name];assert b['status']==200 and b['headers'].get('content-encoding')=='gzip'and b['headers'].get('cache-control')=='public, max-age=31536000, immutable'and'accept-encoding'in b['headers'].get('vary','').lower();assert b['wireBytes']<a['wireBytes']*.5
  savings.append({'resource':name,'beforeBytes':a['wireBytes'],'afterBytes':b['wireBytes'],'reductionPercent':round(100*(1-b['wireBytes']/a['wireBytes']),2),'decodedContentIdentical':True});expected[b['path']]={'decodedBytes':b['decodedBytes'],'decodedSHA256':b['decodedSHA256']}
 for name in ['security-html','emergency-html','api','missing-hash','non-hash']:assert'no-store'in results['candidate'][name]['headers'].get('cache-control','')
 for name in ['identity','explicit-zero']:assert'content-encoding'not in results['candidate'][name]['headers']and results['candidate'][name]['decodedSHA256']==results['baseline']['security-js']['decodedSHA256']
 assert results['candidate']['head']['status']==200 and results['candidate']['head']['wireBytes']==0
 assert len(observed)==2 and all(x['authorizationPreserved']and x['cookiePreserved']for x in observed)
 report={'passed':True,'exactR38StaticSourcePins':pins,'actualNginxRequestsEachMode':len(cases),'decodedHTMLStaticAndSyntheticAPIIdentical':True,'savings':savings,'staticExpected':expected,'normalNginxExitAndDescendantsZero':True,'newAspNetHandlerOrActualIISTested':False,'previousByteExactAspNetHandlerEvidenceUnchanged':True,'quarantinedExecutableRestoredOrSecuritySettingsChanged':False,'realBusinessOrDatabaseOrPublicOrDesktopTouched':False};dump(O/'verified-result.json',report);print(json.dumps(report))
finally:server.shutdown();server.server_close();thread.join(5);assert not thread.is_alive()
