"""Verify actual confirmation handlers with real Element Plus in one fresh owned headless browser."""
from pathlib import Path
import argparse,datetime,hashlib,http.server,json,subprocess,sys,threading,time,urllib.parse
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/event_disposal_atomic_20261029';W=R/'work/event_disposal_atomic_20261029';CHROME=Path('C:/Program Files/Google/Chrome/Application/chrome.exe');NODE=Path('D:/Program Files/nodejs/node.exe');sys.path.insert(0,str(T));sys.dont_write_bytecode=True
from original_server_windows_job import OwnedWindowsJob
from verify_original_work_reservation_sql import run
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--revision',choices=['r1','r2','r3','r4','r5'],required=True);parser.add_argument('--kind',choices=['disposal','exercise'],required=True);a=parser.parse_args();out=D/('browser-'+a.kind+'-'+a.revision);work=W/('browser-'+a.kind+'-'+a.revision);fixture=W/('event-form-fixture-'+a.kind+'-'+a.revision);assert not out.exists() and not work.exists() and not fixture.exists();out.mkdir();(out/'tmp').mkdir();work.mkdir()
 qa=Path('D:/Zqa20261025/Application');before={'releaseSHA256':sha(qa/'release-manifest.json'),'run':read(qa/'UserData/OriginalServer/current-run.json')['run'],'PID':read(qa/'UserData/OriginalServer/current-run.json')['controllerPID']};assert before['PID']==11344 and Path(before['run']).name=='j57'
 sources={str(T/n):sha(T/n) for n in ['build_event_actual_form_fixture.mjs','verify_event_actual_form_browser.mjs',Path(__file__).name,'original_event_operations_frontend_compat.py','original_confirmed_operation_callers_20261029.json']};write(out/'prepared.json',{'revision':a.revision,'sourcePins':sources,'nodeSHA256':sha(NODE),'chromeSHA256':sha(CHROME),'desktopInputs':False,'personalBrowserOrAuthenticationUsed':False,'QA':before})
 run(out,'build-fixture',[NODE,T/'build_event_actual_form_fixture.mjs',R,W,fixture,a.kind],120)
 allowed={}
 for p in fixture.rglob('*'):
  if p.is_file() and p.suffix in ('.html','.js','.css'):allowed['/'+p.relative_to(fixture).as_posix()]=p
 assert len(allowed)==5;served=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   route=urllib.parse.urlsplit(self.path).path
   if route=='/favicon.ico':self.send_response(204);self.end_headers();return
   if route.endswith('/'):route+='index.html'
   p=allowed.get(route)
   if p is None:self.send_error(404);return
   raw=p.read_bytes();assert len(raw)<8*1024**2;self.send_response(200);self.send_header('Content-Type',{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[p.suffix]);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);served.append({'path':route,'bytes':len(raw)})
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port);profile=work/'own-fresh-headless-profile';profile.mkdir();stdout=(out/'chrome.stdout.log').open('xb');stderr=(out/'chrome.stderr.log').open('xb');command=[str(CHROME),'--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+str(profile),'--window-size=1280,1000','about:blank'];process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(process);write(out/'chrome-started.json',{'PID':process.pid,'command':command});passed=False
 try:
  end=time.monotonic()+25;active=profile/'DevToolsActivePort'
  while time.monotonic()<end:
   if process.poll() is not None:raise RuntimeError('OWN_BROWSER_TERMINAL_NO_RESTART')
   if active.is_file() and len(active.read_text(encoding='utf8').splitlines())>=2:break
   time.sleep(.1)
  else:raise RuntimeError('OWN_BROWSER_TIMEOUT_INSPECT_SAME_PROCESS')
  lines=active.read_text(encoding='utf8').splitlines();run(out,'real-confirmation-controls',[NODE,T/'verify_event_actual_form_browser.mjs',lines[0],lines[1],base,out,a.kind],180);result=read(out/'browser-result.json');assert result['sceneCount']==(7 if a.kind=='disposal' else 9) and not result['outsideRequests'];process.wait(timeout=15);assert process.returncode==0;passed=True
 finally:
  job.close()
  if process.poll() is None:process.wait(timeout=10)
  server.shutdown();server.server_close();thread.join(timeout=5);stdout.close();stderr.close();write(out/'lifecycle-result.json',{'passed':passed,'browserExitCode':process.returncode,'ownBrowserStopped':process.poll() is not None,'ownServerThreadStopped':not thread.is_alive(),'served':served,'sourcePinsUnchanged':all(sha(Path(p))==v for p,v in sources.items()),'desktopInputs':False,'backendUsed':False})
 assert before=={'releaseSHA256':sha(qa/'release-manifest.json'),'run':read(qa/'UserData/OriginalServer/current-run.json')['run'],'PID':read(qa/'UserData/OriginalServer/current-run.json')['controllerPID']};print(json.dumps({'scenes':result['sceneCount'],'sourceAndJ57Unchanged':True,'ownBrowserAndServerStopped':True,'actualFullPageMounted':False}))
if __name__=='__main__':main()
