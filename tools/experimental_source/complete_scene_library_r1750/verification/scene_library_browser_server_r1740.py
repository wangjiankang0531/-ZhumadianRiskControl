"""Own synthetic browser fixture using the real qualified HTTP handlers and original ACL adapter."""
from pathlib import Path
import copy,hashlib,http.server,json,secrets,socket,sys,threading
R=Path('D:/Project/Zhumadian');W=R/'work/scene-library-browser-r1740';P=R/'work/scene-file-frontend-r1735/backend';sys.path.insert(0,str(P))
from services.scene_projects import SceneProjectRepository
from services.layer_sync_server import LayerSyncServer,LayerSyncHandler,OriginalPlatformAccess,checked_project_origin,empty_document
def doc():return{'schema':'xnby.scene-project.v2','scene':'zhumadian','landscape':empty_document(),'models':[{'id':'instance-a','assetId':'asset-a','name':'初始实例','assetSHA256':'a'*64,'anchor':[1,2,3],'scale':.01,'rotationDegrees':0,'visible':True}],'lighting':{'intensity':1.8,'azimuth':135,'textures':True,'shadows':True,'targetModelId':'instance-a'}}
class Fixture:
 def __init__(self):
  self.token=secrets.token_urlsafe(24);self.control=secrets.token_urlsafe(24);self.subject='own-scene-component-writer';self.current=doc();self.posts=0;self.successes=0;self.drop=False;self.dropped=0;self.handles=[];self.started=False;self.threads=[]
  self.repo=SceneProjectRepository(W/'scene-files',{'schema':'xnby.scene-model-library.v1','models':[{'id':'asset-a','sha256':'a'*64}]});fixture=self
  class Platform(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    value=fixture.identity(self.headers.get('Authorization'));raw=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  self.platform=http.server.ThreadingHTTPServer(('127.0.0.1',0),Platform);access=OriginalPlatformAccess(self.platform.server_port,write_roles=['writer']);self.server=LayerSyncServer(0,None,access,scene_projects=self.repo);self.origin='http://127.0.0.1:'+str(self.server.server_port);self.server.project_origin=checked_project_origin(self.origin)
  class Handler(LayerSyncHandler):
   def data(self,status,value):
    raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
   def do_GET(self):
    if self.path in ['/','/ui.js']:
     raw=(W/('index.html'if self.path=='/'else'ui.js')).read_bytes();self.send_response(200);self.send_header('Content-Type','text/html'if self.path=='/'else'application/javascript');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
    if self.path=='/fixture-session':return self.data(200,{'authorization':'Bearer '+fixture.token,'subject':fixture.subject,'document':fixture.current})
    if self.path=='/fixture-stats':return self.data(200,{'posts':fixture.posts,'successful':fixture.successes,'dropped':fixture.dropped})
    if self.path=='/zhumadian/api/jnpf/oauth/CurrentUser':return self.data(200,fixture.identity(self.headers.get('Authorization')))
    if self.path.startswith('/zhumadian/api/spatial-sync/'):
     self.path=self.path.removeprefix('/zhumadian/api/spatial-sync');return super().do_GET()
    self.send_error(404)
   def do_POST(self):
    if self.path=='/fixture-control':
     if self.headers.get('X-Own-Fixture')!=fixture.control:return self.data(403,{'error':'denied'})
     value=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));op=value['operation']
     if op=='drop-next':fixture.drop=True
     elif op=='remote-edit':
      item=fixture.repo.get(value['name']);d=item['document'];d['models'][0]['name']='另一个编辑者';fixture.repo.save(value['name'],d,item['sha256'])
     else:return self.data(422,{'error':'invalid'})
     return self.data(200,{'done':True})
    if self.path=='/zhumadian/api/spatial-sync/v2/project/scenes':fixture.posts+=1;self.path='/v2/project/scenes';return super().do_POST()
    self.send_error(404)
   def output(self,status,payload):
    if self.command=='POST'and self.path=='/v2/project/scenes'and status==200:
     fixture.successes+=1
     if fixture.drop:
      fixture.drop=False;fixture.dropped+=1;self.close_connection=True
      try:self.connection.shutdown(socket.SHUT_RDWR)
      except OSError:pass
      self.connection.close();return
    return super().output(status,payload)
  self.server.RequestHandlerClass=Handler;original=self.server.process_request_thread
  def observed(*args):self.handles.append(threading.current_thread());return original(*args)
  self.server.process_request_thread=observed
 def identity(self,authorization):
  if authorization!='Bearer '+self.token:return{'code':401}
  return{'code':200,'data':{'userInfo':{'userId':self.subject,'roleIds':['writer'],'isAdministrator':False}}}
 def start(self):
  for server in[self.platform,self.server]:
   thread=threading.Thread(target=server.serve_forever);thread.start();self.threads.append((server,thread))
  self.started=True
 def close(self):
  for server,thread in reversed(self.threads):server.shutdown();server.server_close();thread.join();assert not thread.is_alive()
  for server in[self.server,self.platform]:
   if not any(s is server for s,t in self.threads):server.server_close()
  for t in self.handles:t.join();assert not t.is_alive()
