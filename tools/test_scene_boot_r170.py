from pathlib import Path
import importlib.util,json,hashlib,subprocess,concurrent.futures,threading,http.server,os,datetime
from unittest.mock import patch
R=Path('D:/Project/Zhumadian');A=R/'Application';D=R/'Document/Deployment/local_scene_recovery_20261102';source=A/'tools/scene_boot.py';spec=importlib.util.spec_from_file_location('scene_boot_under_test',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();database=m.PACKAGE/'UserData/BusinessData/layers.sqlite';before=sha(database);expected=json.loads((D/'http-verification.json').read_bytes())['servicePID'];cases=[]
files=m.pin_package(m.PACKAGE);assert m.health(m.PACKAGE,8767,files)['servicePID']==expected;cases.append({'case':'real-running-service-image-identity-and-viewer-match','passed':True})
owners=m.existing_owner_count(m.PACKAGE,8767);assert owners>=1,'CURRENT_OWN_LAUNCHER_MUST_BE_DETECTED';cases.append({'case':'real-current-own-launcher-detected-before-duplicate-start','passed':True,'owners':owners})
def invoke(_):
 r=subprocess.run([str(A/'runtime/python/python.exe'),'-I','-B',str(source)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45);assert r.returncode==0,(r.stderr.decode('utf-8',errors='replace')[:300]);data=json.loads(r.stdout);assert data['ready']and data['reusedExistingService']and not data['newServiceStarted']and data['servicePID']==expected;return {'ready':True,'sameServicePID':True,'newServiceStarted':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(invoke,range(4)))
cases.append({'case':'four-concurrent-launches-reuse-same-real-service','passed':True,'invocations':results})
manual=subprocess.run([os.environ.get('COMSPEC','C:/Windows/System32/cmd.exe'),'/d','/c',str(A/'启动本机三维应急.cmd')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45);assert manual.returncode==0;value=json.loads(manual.stdout);assert value['ready']and value['servicePID']==expected and not value['newServiceStarted'];cases.append({'case':'actual-unicode-manual-cmd-entry-reuses-live-service','passed':True})
class Fake(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  body=b'{"identity":"unrelated","pid":1,"readOnly":true,"conversionEnabled":false}';self.send_response(200);self.end_headers();self.wfile.write(body)
 def log_message(self,*a):pass
server=http.server.HTTPServer(('127.0.0.1',0),Fake);thread=threading.Thread(target=server.serve_forever);thread.start()
try:
 with patch.object(m.subprocess,'Popen',side_effect=AssertionError('UNEXPECTED_PROCESS_START')):
  try:m.ensure(m.PACKAGE,server.server_port)
  except RuntimeError as e:assert str(e)=='SCENE_PORT_OCCUPIED_IDENTITY_MISMATCH_NO_SERVICE_CHANGED'
  else:raise AssertionError('UNRELATED_LISTENER_ACCEPTED')
 cases.append({'case':'unrelated-live-port-refused-without-process-start-or-stop','passed':True})
finally:server.shutdown();thread.join();server.server_close()
try:m.pin_package(A/'work/nonexistent-unapproved-scene')
except ValueError as e:assert str(e)=='ONLY_FIXED_LOCAL_SCENE_PACKAGE'
else:raise AssertionError('OTHER_PACKAGE_ACCEPTED')
cases.append({'case':'different-package-path-refused-before-start','passed':True})
assert sha(database)==before and m.health(m.PACKAGE,8767,files)['servicePID']==expected
proof={'schema':'xnby.scene-boot.r170.real-reuse-and-isolation.v1','at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'sourceSHA256':sha(source),'cases':cases,'sameActualServicePID':True,'runningServiceStoppedOrRestarted':False,'userLayerDatabaseBytesUnchangedDuringTests':True,'desktopInputSent':False,'automaticStartupInstalled':False}
(D/'scene-boot-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'sameServicePID':expected,'fourConcurrentLaunchesDidNotStartDuplicate':True,'userLayerBytesKept':True,'automaticStartupInstalled':False}))
