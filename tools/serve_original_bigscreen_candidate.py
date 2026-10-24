"""Bounded separate original bigscreen UI/backend gateway, reusing the live original business candidate."""
import argparse,datetime,hashlib,http.client,json,os,pathlib,re,subprocess,threading,time,traceback
from original_bigscreen_runtime import OriginalBigscreen
from original_bigscreen_mock_snapshot import SnapshotServer,load_capture
from prepare_original_bigscreen_gateway import prepare

def closed_normally(result):
 backend=result.get('backendClose',{})
 return (not result.get('failed') and not result.get('gatewayForcedTermination') and result.get('gatewayExitCode')==0 and result.get('mockStopped') is True and backend.get('ownExitCode')==0 and backend.get('contextClosed') is True and not backend.get('forcedTermination') and backend.get('referenceDatabaseUnchanged') is True and backend.get('sourceArchiveUnchanged') is True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--name',required=True);p.add_argument('--build-receipt',type=pathlib.Path,required=True);p.add_argument('--build-sha256',required=True);p.add_argument('--capture-receipt',type=pathlib.Path,required=True);p.add_argument('--capture-sha256',required=True);p.add_argument('--joint-ready',type=pathlib.Path,required=True);p.add_argument('--joint-sha256',required=True);p.add_argument('--port',type=int,default=18893);p.add_argument('--minutes',type=int,default=30);a=p.parse_args();assert re.fullmatch('own-bigscreen-j[1-9][0-9]{0,3}',a.name) and 1024<=a.port<=65535 and 1<=a.minutes<=45
 W=a.workspace.resolve(strict=True);A=W.parents[1];assert A.name=='Application';root=W/a.name;assert not root.exists();sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
 for file,pin in [(a.build_receipt,a.build_sha256),(a.capture_receipt,a.capture_sha256),(a.joint_ready,a.joint_sha256)]:assert file.resolve(strict=True).is_relative_to(W) and sha(file)==pin,'EXPLICIT_KNOWN_INPUT_PIN_REQUIRED'
 build=json.loads(a.build_receipt.read_bytes());assert build['buildCompleted'] and build['bothPinnedOverlaysActuallyCompiled'] and build['externalMockLiteralAbsent'] and not build['publicAssetsCopied'];dist=a.build_receipt.resolve().parent/'dist';assert build['mount']=='/zhumadian/bigscreen/' and build['mockBase']=='/zhumadian/api/reference-mock'
 for rel,pin in build['outputSHA256'].items():assert sha(dist/rel)==pin
 project=json.loads((A.parent/'Document/Deployment/tianjin_native_replica_20261023/original_source_copies.json').read_bytes())['projects']['bigscreen'];public=pathlib.Path(project['copy'])/'public';assert public.resolve()==pathlib.Path(build['readOnlyPublicAssetRoot']).resolve()
 for row in project['files']:assert sha(pathlib.Path(project['copy'])/row['path'])==row['sha256'],'ORIGINAL_BUILD_INPUT_CHANGED'
 joint=json.loads(a.joint_ready.read_bytes());jointroot=a.joint_ready.resolve().parent;assert not (jointroot/'receipt.json').exists() and joint['state']=='ready-for-original-login' and joint['portalURL']=='http://127.0.0.1:18891/zhumadian/home'
 expires=datetime.datetime.fromisoformat(joint['readyAt']).timestamp()+joint['remainingLeaseSeconds'];assert time.time()+a.minutes*60+45<expires,'BIGSCREEN_LEASE_MUST_END_BEFORE_ORIGINAL_BUSINESS_CANDIDATE'
 dataset=load_capture(a.capture_receipt,a.capture_sha256)
 def get(path):
  c=http.client.HTTPConnection('127.0.0.1',a.port,timeout=5)
  try:c.request('GET',path);r=c.getresponse();body=r.read(20*1024**2+1);return r.status,body,dict(r.getheaders())
  finally:c.close()
 c=http.client.HTTPConnection('127.0.0.1',18891,timeout=5)
 try:c.request('GET','/zhumadian/home');r=c.getresponse();assert r.status==200;r.read(1024)
 finally:c.close()
 root.mkdir();(root/'controller-source.py').write_bytes(pathlib.Path(__file__).read_bytes());result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'name':a.name,'upstreamOwnerId':joint['ownerId'],'upstreamReadySHA256':a.joint_sha256,'buildReceiptSHA256':a.build_sha256,'captureReceiptSHA256':a.capture_sha256,'publicAssetsCopied':False,'originalSourceChanged':False,'businessAPISynthesized':False,'referenceDatabaseOpenedWritable':False,'originalRendererAvailable':False,'realVideoQueryOrControlAttempted':False,'publicDeployed':False,'fullCloneReady':False};service=None;mock=None;worker=None;nginx=None;log=None;flags=subprocess.CREATE_NO_WINDOW
 try:
  config_command=['D:/Program Files/nodejs/node.exe',str(A/'tools/prepare_original_bigscreen_config.mjs'),'--source',str(public/'config.js'),'--parser',str(W/'security_pc/node_modules/@babel/parser/lib/index.js'),'--parser-sha256','82d72e197e27bf909ae10ffc8d1a969aeb94fe96ec96c4e9cb685a0a8229e40c','--origin','http://127.0.0.1:'+str(a.port),'--output',str(root/'runtime')]
  run=subprocess.run(config_command,capture_output=True,timeout=20,creationflags=flags);(root/'config.private.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'ORIGINAL_RUNTIME_CONFIG_PREPARATION_FAILED'
  service=OriginalBigscreen(W,root/'backend',a.minutes+1);native_port=service.start();print('ORIGINAL_BIGSCREEN_BACKEND_READY',flush=True)
  mock=SnapshotServer(dataset);worker=threading.Thread(target=mock.serve_forever,daemon=True);worker.start();runtime=W/'local-gateway-runtime_20261024/nginx-1.31.8';gateway=root/'gateway';prepared=prepare(gateway,runtime,dist,public,root/'runtime/config.js',a.port,18891,native_port,mock.server_port)
  command=[str(runtime/'nginx.exe'),'-p',str(gateway)+'/', '-c',str(gateway/'nginx.conf')];run=subprocess.run([*command,'-t'],cwd=gateway,capture_output=True,timeout=10,creationflags=flags);(gateway/'config-check.private.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'BIGSCREEN_GATEWAY_CONFIGURATION_FAILED'
  log=(gateway/'process.private.log').open('wb');nginx=subprocess.Popen(command,cwd=gateway,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
  end=time.monotonic()+12
  while True:
   assert nginx.poll() is None and service.process.poll() is None,'OWN_BIGSCREEN_COMPONENT_EXITED_BEFORE_HTTP'
   try:
    status,body,headers=get('/zhumadian/bigscreen/')
    assert status==200,'BIGSCREEN_GATEWAY_ENTRY_HTTP_ERROR';break
   except OSError:pass
   assert time.monotonic()<end,'BIGSCREEN_GATEWAY_READY_TIMEOUT';time.sleep(.1)
  assert body==(dist/'index.html').read_bytes() and int((gateway/'nginx.pid').read_text().strip())==nginx.pid and "connect-src 'self'" in headers.get('Content-Security-Policy','')
  for route,expected in dataset.items():
   status,body,_=get('/zhumadian/api/reference-mock'+route);assert status==200 and body==expected,'EXACT_LOCAL_DEFAULT_RESPONSE_REQUIRED'
  status,body,_=get('/zhumadian/bigscreen/config.js');assert status==200 and hashlib.sha256(body).hexdigest()==sha(root/'runtime/config.js')
  status,body,_=get('/zhumadian/bigscreen/logo.png');assert status==200 and body==(public/'logo.png').read_bytes()
  for rel,pin in build['outputSHA256'].items():
   status,body,_=get('/zhumadian/bigscreen/'+rel);assert status==200 and hashlib.sha256(body).hexdigest()==pin,'ALL_COMPILED_RESOURCES_MUST_BE_SERVED_EXACTLY'
  status,_,_=get('/zhumadian/unavailable-renderer/libac');assert status==503
  c=http.client.HTTPConnection('127.0.0.1',a.port,timeout=5)
  try:c.request('POST','/zhumadian/api/bigscreen/hikvideo/query',body=b'{}',headers={'Content-Type':'application/json'});response=c.getresponse();assert response.status==200 and json.loads(response.read())['success'] is False
  finally:c.close()
  result.update(readyAt=datetime.datetime.now().astimezone().isoformat(),portalURL='http://127.0.0.1:'+str(a.port)+'/zhumadian/bigscreen/',gatewayPID=nginx.pid,originalBackendPID=service.process.pid,originalBackendPort=native_port,mockPort=mock.server_port,exactDefaultRoutesVerified=16,compiledEntryAndScriptAndReferencedPublicAssetExact=True,runtimeConfigExact=True,rendererUnavailableHTTP503=True,originalVideoEmptyInputValidationVerified=True,upstreamLeaseEndsAt=datetime.datetime.fromtimestamp(expires).astimezone().isoformat(),expiresAt=datetime.datetime.fromtimestamp(time.time()+a.minutes*60).astimezone().isoformat(),originalBackend=service.result,preparedGateway=prepared)
  (root/'ready.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ('portalURL','expiresAt','exactDefaultRoutesVerified','originalRendererAvailable','fullCloneReady')}),flush=True);deadline=time.monotonic()+a.minutes*60
  while time.monotonic()<deadline and not (root/'stop').exists():
   assert nginx.poll() is None and service.process.poll() is None and worker.is_alive(),'OWN_BIGSCREEN_COMPONENT_EXITED';assert not (jointroot/'receipt.json').exists(),'ORIGINAL_BUSINESS_CANDIDATE_ENDED';time.sleep(.5)
  result['interactiveLeaseFinished']=True
 except Exception:
  result['failed']=True;(root/'failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');print('OWN_BIGSCREEN_CANDIDATE_FAILED_DETAILS_RETAINED',flush=True)
 finally:
  if nginx is not None and nginx.poll() is None:
   gateway=root/'gateway';assert int((gateway/'nginx.pid').read_text().strip())==nginx.pid,'OWN_BIGSCREEN_GATEWAY_OWNER_MISMATCH';run=subprocess.run([str(runtime/'nginx.exe'),'-p',str(gateway)+'/', '-c',str(gateway/'nginx.conf'),'-s','quit'],cwd=gateway,capture_output=True,timeout=10,creationflags=flags);(gateway/'stop.private.log').write_bytes(run.stdout+run.stderr)
   try:nginx.wait(timeout=8)
   except subprocess.TimeoutExpired:nginx.terminate();nginx.wait(timeout=10);result['gatewayForcedTermination']=True
  if log is not None:log.close()
  if service is not None:result['backendClose']=service.close()
  if mock is not None:mock.shutdown();mock.server_close()
  if worker is not None:worker.join(timeout=3);result['mockStopped']=not worker.is_alive()
  result.update(completedAt=datetime.datetime.now().astimezone().isoformat(),gatewayExitCode=nginx.returncode if nginx else None);(root/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result.get(k) for k in ('failed','gatewayExitCode','gatewayForcedTermination','mockStopped','fullCloneReady')}),flush=True)
 if not closed_normally(result):raise SystemExit(1)

if __name__=='__main__':main()
