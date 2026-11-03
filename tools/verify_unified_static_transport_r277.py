"""Real Nginx + exact ASP.NET handler transport; anonymous static fixtures only."""
from pathlib import Path
import gzip,hashlib,http.client,http.server,importlib.util,json,os,socket,subprocess,sys,threading,time
R=Path('D:/Project/Zhumadian'); A=R/'Application'; T=A/'tools'
sys.path.insert(0,str(T))
from original_server_windows_job_graceful_20261101 import OwnedWindowsJob
from prepare_original_frontend_gateway import prepare
V=Path(__file__).resolve().parent
O=V/'static-transport-r277'; assert not O.exists(); O.mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def loadmodule(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
roots={'security_pc':R/'work/user_feedback_20261031/avatar-full-r157/security_pc/build/dist','emergency_pc':R/'work/user_feedback_20261031/plan-exercise-retained-r224/dist'}
manifest=json.loads((R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle/payload/payload-manifest.json').read_text(encoding='utf-8'))['files']
pins={}
for role,root in roots.items():
 rows={k[len('frontend/'+role+'/'):]:v for k,v in manifest.items() if k.startswith('frontend/'+role+'/')}
 assert rows,role
 for rel,row in rows.items():
  b=(root/rel).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'],rel
 pins[role]={'files':len(rows),'exactR38CandidateStaticRootVerified':True}
dump(O/'static-source-pins.json',pins)
for role in ['mobile','bigscreen','tiles']:
 root=O/('own-'+role);root.mkdir();(root/'index.html').write_text('<!doctype html><title>own transport fixture</title>',encoding='utf-8');roots[role]=root
for port in [18892]:
 s=socket.socket();s.bind(('127.0.0.1',port));s.close()
observed=[]
class Backend(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  observed.append({'path':self.path,'acceptEncoding':self.headers.get('Accept-Encoding'),'authorizationPreserved':self.headers.get('Authorization')=='Bearer synthetic-transport-fixture','cookiePreserved':self.headers.get('Cookie')=='transport_fixture=owned'})
  b=json.dumps({'marker':'天津南港危化品智慧物流园','fixtureOnly':True},ensure_ascii=False).encode()
  self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Backend)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
worker=(T/'iis_reference_proxy_contract.cs').read_text(encoding='utf-8')
worker=worker.replace('public string Body;','public string Body; public byte[] RawBody;').replace('Status=status,Body=','Status=status,RawBody=output.ToArray(),Body=')
(O/'worker.cs').write_text(worker,encoding='utf-8')
main=r'''using System;using System.Collections.Generic;using System.IO;using System.IO.Compression;using System.Security.Cryptography;using System.Text;using System.Web.Script.Serialization;
public class Case {public string name,path,method,host,body;public bool secure;public Dictionary<string,string> headers;}
public static class MainFixture {
 static string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
 public static int Main(string[] args){try{var json=new JavaScriptSerializer();var cases=json.Deserialize<Case[]>(File.ReadAllText(args[0],Encoding.UTF8));var rows=new List<object>();foreach(var c in cases){var r=XnbyProxyWorker.Invoke(c.path,c.method,c.secure,c.host,c.body,new Dictionary<string,string>(c.headers,StringComparer.OrdinalIgnoreCase),new string('1',64));var raw=r.RawBody;byte[] decoded=raw;bool gz=Array.Exists(r.Headers,h=>h.Equals("Content-Encoding: gzip",StringComparison.OrdinalIgnoreCase));if(gz && raw.Length>0){using(var s=new GZipStream(new MemoryStream(raw),CompressionMode.Decompress))using(var o=new MemoryStream()){s.CopyTo(o);decoded=o.ToArray();}}rows.Add(new{name=c.name,status=r.Status,wireBytes=raw.Length,decodedBytes=decoded.Length,decodedSHA256=Hash(decoded),headers=r.Headers});}Console.WriteLine(json.Serialize(rows));return 0;}catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}'''
(O/'main.cs').write_text(main,encoding='utf-8')
paths={
 'security-js':'/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js',
 'emergency-js':'/zhumadian/emergency/branding-20261025/assets/js/wf-index-CeoNouGN.js',
 'security-css':'/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css',
 'emergency-css':'/zhumadian/emergency/branding-20261025/assets/css/index-D0NHlCez.css',
 'security-html':'/zhumadian/home','emergency-html':'/zhumadian/emergency/home/index',
 'api':'/zhumadian/api/serv/performance-fixture',
 'missing-hash':'/zhumadian/branding-20261025/assets/js/absent-ABCDEFGH.js',
 'non-hash':'/zhumadian/assets/nonhashed.js'}
# No application root is modified to create the missing/non-hashed resources.
cases=[]
for name,path in paths.items():
 cases.append(dict(name=name,path=path,method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={'Accept-Encoding':'gzip','Authorization':'Bearer synthetic-transport-fixture','Cookie':'transport_fixture=owned'}))
for name,enc in [('identity','identity'),('explicit-zero','gzip;q=0, *;q=1'),('wildcard','br, *;q=0.5'),('weighted','br, gzip;q=0.3'),('upper','GZIP;Q=1.000'),('query','gzip')]:
 cases.append(dict(name=name,path=paths['security-js']+('?v=fixture' if name=='query' else ''),method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={'Accept-Encoding':enc}))
cases.extend([dict(name='head',path=paths['security-js'],method='HEAD',secure=True,host='www.joinlinksmart.com',body='',headers={'Accept-Encoding':'gzip'}),dict(name='wrong-host',path=paths['security-js'],method='GET',secure=True,host='other.invalid',body='',headers={}),dict(name='traversal',path='/zhumadian/%2e%2e/private',method='GET',secure=True,host='www.joinlinksmart.com',body='',headers={})])
dump(O/'cases.json',cases)
runtime=R/'_g/Application/runtime/nginx'
out={}
def headers(row):
 d={}
 for h in row['headers']:
  k,v=h.split(':',1);d[k.lower()]=v.strip()
 return d
try:
 for mode in ['baseline','candidate']:
  sys.modules['original_project_branding']=loadmodule('original_project_branding',T/('original_project_branding.py' if mode=='baseline' else 'original_project_branding_r229.py'))
  gateway=O/mode
  prepare(gateway,runtime,roots,18892,server.server_port,server.server_port,base_path='/zhumadian',public_origin='https://www.joinlinksmart.com',project_name='驻马店重大风险防控')
  config=gateway/'nginx.conf'
  cmd=[str(runtime/'nginx.exe'),'-p',gateway.as_posix()+'/', '-c',str(config)]
  check=subprocess.run(cmd+['-t'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
  (gateway/'syntax.log').write_bytes(check.stdout+check.stderr);assert check.returncode==0,check.stderr
  source=A/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs' if mode=='baseline' else T/'frontend/static_performance_r229/XnbyReferenceProxy.cs'
  exe=gateway/'transport.exe'
  compile=subprocess.run(['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/out:'+str(exe),'/r:System.Web.dll','/r:System.Configuration.dll','/r:System.Web.Extensions.dll',str(source),str(O/'worker.cs'),str(O/'main.cs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
  (gateway/'compile.log').write_bytes(compile.stdout+compile.stderr);assert compile.returncode==0,compile.stdout
  stream=(gateway/'process.log').open('wb');p=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(p)
  try:
   deadline=time.monotonic()+8
   while True:
    try:
     with socket.create_connection(('127.0.0.1',18892),timeout=.2):break
    except OSError:
     assert p.poll() is None and time.monotonic()<deadline;time.sleep(.1)
   started=time.monotonic()
   q=subprocess.run([str(exe),str(O/'cases.json')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=50)
   (gateway/'run.stderr.log').write_bytes(q.stderr);assert q.returncode==0,q.stderr
   rows=json.loads(q.stdout.decode('utf-8-sig'));out[mode]={r['name']:r for r in rows};dump(gateway/'results.json',{'elapsedSeconds':round(time.monotonic()-started,3),'cases':rows})
  finally:
   stop=subprocess.run(cmd+['-s','quit'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10)
   (gateway/'stop.log').write_bytes(stop.stdout+stop.stderr)
   p.wait(timeout=15);deadline=time.monotonic()+5
   while job.active_processes() and time.monotonic()<deadline:time.sleep(.1)
   active=job.active_processes();dump(gateway/'exit.json',{'processExit':p.returncode,'normalQuitReturn':stop.returncode,'ownedActiveProcesses':active});assert p.returncode==0 and stop.returncode==0 and active==0;job.close();stream.close()
  assert out[mode]['wrong-host']['status']==403 and out[mode]['traversal']['status']==404
 for name in paths:
  old,new=out['baseline'][name],out['candidate'][name]
  assert (old['status'],old['decodedBytes'],old['decodedSHA256'])==(new['status'],new['decodedBytes'],new['decodedSHA256']),name
 savings=[]
 for name in ['security-js','emergency-js','security-css','emergency-css']:
  old,new=out['baseline'][name],out['candidate'][name];h=headers(new)
  assert h['content-encoding']=='gzip' and 'Accept-Encoding' in h['vary'] and h['cache-control']=='public, max-age=31536000, immutable',(name,h)
  assert new['wireBytes']<old['wireBytes']*.5,name
  savings.append({'resource':name,'beforeBytes':old['wireBytes'],'afterBytes':new['wireBytes'],'reductionPercent':round(100*(1-new['wireBytes']/old['wireBytes']),2),'decodedContentIdentical':True})
 for name in ['security-html','emergency-html','api','missing-hash','non-hash']:
  h=headers(out['candidate'][name]);assert 'no-store' in h.get('cache-control',''),(name,h)
 for name in ['identity','explicit-zero']:
  assert 'content-encoding' not in headers(out['candidate'][name]);assert out['candidate'][name]['decodedSHA256']==out['baseline']['security-js']['decodedSHA256']
 for name in ['wildcard','weighted','upper','query']:
  assert headers(out['candidate'][name])['content-encoding']=='gzip';assert out['candidate'][name]['decodedSHA256']==out['baseline']['security-js']['decodedSHA256']
 assert out['candidate']['head']['status']==200 and out['candidate']['head']['wireBytes']==0
 assert len(observed)==2 and all(x['authorizationPreserved'] and x['cookiePreserved'] and x['acceptEncoding']!='gzip' for x in observed),observed
 result={'passed':True,'staticSourcePins':pins,'actualNginxSyntaxAndTransport':True,'actualAspNetHandlerToNginx':True,'iisIntegratedRuntimeTested':False,'publicDeployed':False,'realBusinessOrDatabaseUsed':False,'desktopTouched':False,'casesEachMode':len(cases),'savings':savings,'decodedHTMLAPIAndStaticIdentical':True,'hashOnlyCachingAndErrorNoStore':True,'syntheticAuthCookieAndAPINamesUnchanged':True,'normalNginxExitAndOwnedDescendantsZero':True}
 dump(O/'verified-result.json',result);print(json.dumps(result,ensure_ascii=False))
finally:
 server.shutdown();server.server_close();thread.join(3);assert not thread.is_alive()
