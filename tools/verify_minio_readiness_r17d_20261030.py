from pathlib import Path
import ast,json,time,re,types,threading,http.server,sys
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/server_directory_migration_20261030_r17d';source=D/'delivery/payload/tools/serve_original_server_release.py'
sys.path.insert(0,str(R/'Application/tools'));from original_object_store_runtime import request_owned_http,signed_owned_request
tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('ensure_object_store_ready','stop_object_store_when_available')];assert len(nodes)==2
checks=[]
def run_case(label,mode,expected=None,timeout=2):
 counts={};operations=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def answer(self,method):
   key=(method,self.path);counts[key]=counts.get(key,0)+1;n=counts[key];operations.append(key)
   if self.path=='/minio/health/live':status=200
   elif self.path=='/minio/health/ready':status=503 if mode=='timeout' or mode=='warming' and n<=2 else 200
   elif method=='HEAD':
    if mode=='auth':status=403
    elif mode=='bad-gateway':status=502
    elif mode=='conflict-denied':status=404 if n==1 else 403
    elif mode=='conflict-missing':status=404
    elif mode in ('warming','conflict'):status=503 if n==1 and mode=='warming' else 404 if not counts.get(('PUT',self.path)) else 200
    else:status=200
   elif method=='PUT':status=409 if mode.startswith('conflict') else 200
   else:status=500
   self.send_response(status);self.send_header('Content-Length','0');self.end_headers()
  def do_GET(self):self.answer('GET')
  def do_HEAD(self):self.answer('HEAD')
  def do_PUT(self):self.answer('PUT')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 env={'time':time,'re':re,'request_owned_http':request_owned_http,'signed_owned_request':signed_owned_request,'stop_owned_provider':lambda *args:{'status':200}}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),env)
 state={};error=None;child=types.SimpleNamespace(process=types.SimpleNamespace(poll=lambda:0 if mode=='exited' else None));start=time.monotonic()
 try:
  env['ensure_object_store_ready'](server.server_port,'synthetic-access','synthetic-secret',['synthetic-bucket'],[child],state,timeout)
 except (RuntimeError,ValueError) as e:error=str(e)
 finally:server.shutdown();server.server_close();thread.join(timeout=2)
 if expected:assert error and expected in error,(label,error);assert not state.get('objectStoreInitialization',{}).get('ready',False)
 else:assert error is None and state['objectStoreInitialization']['ready'],(label,error)
 assert 'synthetic-access' not in json.dumps(state) and 'synthetic-secret' not in json.dumps(state) and 'synthetic-bucket' not in json.dumps(state)
 if mode=='timeout':assert not any(m in ('HEAD','PUT') for m,p in operations)
 if mode=='auth':assert not any(m=='PUT' for m,p in operations)
 checks.append({'case':label,'passed':True,'failureCode':error,'attempts':state.get('objectStoreInitialization',{}).get('attempts',0),'elapsedSeconds':round(time.monotonic()-start,3)})
for row in [('already-ready','normal',None,2),('live-before-ready-and-transient-head','warming',None,3),('create-conflict-only-after-head-confirms','conflict',None,2),('auth-fails-without-create','auth','bucket-head:403',2),('unknown-status-fails','bad-gateway','bucket-head:502',2),('conflict-without-access-fails','conflict-denied','created-bucket-head:403',2),('ready-never-arrives','timeout','OWN_COMPONENT_TIMEOUT',.3),('conflict-never-verified','conflict-missing','OWN_COMPONENT_TIMEOUT',.3),('child-exited-fails','exited','OWN_COMPONENT_EXITED',2)]:run_case(*row)
env={'time':time,'re':re,'request_owned_http':request_owned_http,'signed_owned_request':signed_owned_request};responses=iter([503,503,200]);env['stop_owned_provider']=lambda *args:{'status':next(responses)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),env);s=env['stop_object_store_when_available'](12345,'fake','fake',2);assert s=={'status':200,'attempts':3};checks.append({'case':'normal-stop-retries-initialization-503','passed':True})
env['stop_owned_provider']=lambda *args:{'status':403};assert env['stop_object_store_when_available'](12345,'fake','fake',2)=={'status':403,'attempts':1};checks.append({'case':'stop-auth-not-retried','passed':True})
v={'schema':'xnby.object-store-readiness-gate.verification.v1','actualCandidateFunctionsAndRealLoopbackHTTPUsed':True,'syntheticResponsesNotBusinessAcceptance':True,'tests':checks,'allPassed':True};(D/'readiness-gate-verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8');print(json.dumps(v))
