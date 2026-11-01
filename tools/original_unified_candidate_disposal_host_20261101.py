"""Serve the exact production R22 safety build through the normal gateway; other readonly roots are not accepted by this test."""
from pathlib import Path
import contextlib,json,os,socket,subprocess,time,urllib.request
import verify_emergency_business_http_20261030 as c
from original_unified_candidate_frontend_roots_20261101 import prepare,roots as staged_roots
from original_task_identity_authority import listener_owner
@contextlib.contextmanager
def host(root,business_port,platform_port,phase):
 assert phase in ('task-dispose','task-reopen')
 selected_roots=staged_roots();frontend=selected_roots['emergency_pc'];assert frontend.is_dir()
 safety=selected_roots['security_pc']
 runtime=c.Q/'runtime/nginx';manifest=c.read(c.R/'work/user_feedback_20261031/r22-risk-candidate-r1/r21-base-payload-manifest.json')['files'];assert c.sha(runtime/'nginx.exe')==manifest['runtime/nginx/nginx.exe']['sha256'];folder=root/('compiled-security-gateway-'+phase);lease=socket.socket();lease.bind(('127.0.0.1',0));port=lease.getsockname()[1];roots={n:c.Q/'frontend'/n for n in ['security_pc','mobile','bigscreen','tiles']};roots['emergency_pc']=frontend;roots['security_pc']=safety;receipt=prepare(folder,runtime,roots,port,business_port,platform_port,base_path='/zhumadian');p=folder/'nginx.conf';s=p.read_text(encoding='utf-8');old='proxy_pass http://127.0.0.1:'+str(business_port)+'/;';assert s.count(old)==1;s=s.replace(old,'proxy_pass http://127.0.0.1:'+str(business_port)+'/serv/;');s=s.replace('proxy_pass http://127.0.0.1:'+str(business_port)+'/websocket/;','proxy_pass http://127.0.0.1:'+str(business_port)+'/serv/websocket/;');p.write_text(s,encoding='utf-8');receipt.update(fixtureBusinessServletContext='/serv',allSafetyFrontend836BytesMatchedNewCandidate=True,emergencyLoginAndDisposalGuardFromExact204PublishedFiles=True,combined1047FileStageUsed=True,publishedGateway006bUsed=True,originalGeneratorUsed=True,nginxConfigurationSHA256=c.sha(p),businessResponsesSynthesized=False);c.dump(root/('compiled-security-gateway-input-'+phase+'.json'),receipt)
 lease.close();command=[str(runtime/'nginx.exe'),'-p',str(folder)+os.sep,'-c',str(p)];check=subprocess.run(command+['-t'],capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/('compiled-security-nginx-check-'+phase+'.json'),{'exitCode':check.returncode,'portReservationReleasedBeforeCheck':True,'diagnostic':check.stderr.decode('utf-8',errors='replace')[-1800:]});assert check.returncode==0,'OWN_COMPILED_PORTAL_NGINX_CONFIG';out=open(folder/'stdout.log','wb');err=open(folder/'stderr.log','wb');process=subprocess.Popen(command,cwd=folder,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);job=c.OwnedWindowsJob(process);c.dump(root/('compiled-security-gateway-started-'+phase+'.json'),{'pid':process.pid,'port':port});forced=False
 try:
  deadline=time.monotonic()+10;opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  while True:
   assert process.poll() is None and time.monotonic()<deadline,'OWN_COMPILED_PORTAL_GATEWAY_READY'
   try:
    with opener.open('http://127.0.0.1:'+str(port)+'/zhumadian/login',timeout=1) as response:
     if response.status==200:break
   except OSError:time.sleep(.05)
  assert listener_owner(port);yield 'http://127.0.0.1:'+str(port)
 finally:
  if process.poll() is None:
   result=subprocess.run(command+['-s','quit'],capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW);assert result.returncode==0
  while process.poll()is None:
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:print('OWN_NGINX_NORMAL_QUIT_PENDING_NO_FORCE',flush=True)
  import ctypes
  class Accounting(ctypes.Structure):
   _fields_=[('user',ctypes.c_longlong),('kernel',ctypes.c_longlong),('periodUser',ctypes.c_longlong),('periodKernel',ctypes.c_longlong),('faults',ctypes.c_ulong),('total',ctypes.c_ulong),('active',ctypes.c_ulong),('terminated',ctypes.c_ulong)]
  while True:
   value=Accounting();assert job.api.QueryInformationJobObject(job.handle,1,ctypes.byref(value),ctypes.sizeof(value),None)
   if value.active==0:break
   print('OWN_NGINX_CHILDREN_PENDING_NO_FORCE',flush=True);time.sleep(1)
  job.close();out.close();err.close();c.dump(root/('compiled-security-gateway-stopped-'+phase+'.json'),{'pid':process.pid,'exitCode':process.returncode,'forcedJobClosure':False,'listenerGone':not listener_owner(port),'normalQuit':process.returncode==0})
