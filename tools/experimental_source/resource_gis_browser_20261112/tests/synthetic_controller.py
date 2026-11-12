from pathlib import Path
import http.server,json,os,secrets,sys,threading,time
R=Path('D:/Project/Zhumadian');GIS=R/'Application/Packages/ClientGISSettingsCandidate_20261107'
sys.path[:0]=[str(GIS/'code'),str(GIS/'provider/tools')]
from client_manifest import workspace_context
from client_control import atomic_json,load_json,process_identity
from client_gis_runtime import state_directory
from client_job import StateLock
assert sys.stdin.buffer.readline(100)==b'D175-SYNTHETIC\n'
context=workspace_context(Path(sys.argv[1]),GIS,verify_resources=False);port=int(sys.argv[2]);folder=state_directory(context);lock=StateLock(folder)
runid='r'+secrets.token_hex(16);run=folder/'runs'/runid;run.mkdir(parents=True);instance=secrets.token_hex(16);secret=secrets.token_hex(32)
meta={'schema':'xnby.client-gis.active.v1','runId':runid,'controller':process_identity(os.getpid()),'installation':str(context['installation']),'installSHA256':context['installSHA256'],'configurationSHA256':context['configurationSHA256'],'port':port,'ownerToken':secret,'phase':'ready','instanceId':instance}
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path!='/xnby-gis/v1/discovery':self.send_error(404);return
  raw=json.dumps({'instanceId':instance,'sourceRuntimeIdentity':context['install']['sourceRuntimeIdentity'],'sourceIndexIdentity':context['install']['sourceIndexIdentity'],'ready':True}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def log_message(self,*a):pass
server=http.server.HTTPServer(('127.0.0.1',port),Handler);thread=threading.Thread(target=server.serve_forever);thread.start();atomic_json(folder/'active.private.json',meta,replace=False)
try:
 while True:
  request=run/'stop.request.json'
  if request.exists():
   value=load_json(request)
   if value=={'schema':'xnby.client-gis.stop.v1','runId':runid,'ownerToken':secret}:break
  time.sleep(.02)
finally:
 server.shutdown();thread.join();server.server_close();atomic_json(run/'terminal.json',{'runId':runid,'allOwnedChildrenExited':True,'syntheticNoProviderChildren':True,'HTTPThreadJoined':not thread.is_alive()});(folder/'active.private.json').unlink();lock.close()
print(json.dumps({'syntheticControllerNormalStop':True,'HTTPThreadJoined':True}),flush=True)
