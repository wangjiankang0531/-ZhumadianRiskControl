"""QA composition only: unchanged D175 HTTP/service, fixed synthetic GIS adapter."""
from pathlib import Path
import hashlib,http.client,json,secrets,subprocess,sys,time
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
Q=Path('D:/Temp/Administrator/xnby-resource-control-r2422')
C=A/'Packages/ResourceGISControlCandidate_20261112/client-250'
SOURCE=A/'tools/experimental_source/resource_gis_control_20261112'
assert len(sys.argv)==3 and sys.argv[1]in('serve','stop','stopGIS')and sys.argv[2]in('1','2')
cycle=sys.argv[2];sys.path.insert(0,str(C/'code'))
from entry import qualify
trusted=qualify(C);assert trusted['manifestSHA256']=='bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b'
sys.path[:0]=[str(C/'code'),str(trusted['installation']/'code'),str(trusted['installation']/'provider/tools')]
from client_manifest import load_installation,workspace_context
from client_control import process_identity
from client_gis_runtime import current_owner,stop as original_stop,state_directory
from grant_clock import ClockBoundGrant,checked_remaining_header,deadline_after_roundtrip
import resource_agent
from registered_gis import RegisteredGIS
trusted['dependency']=load_installation(trusted['installation']);trusted['configuration']=Q/'private-QA/config/client-workspace.json'
cfg=json.loads((Q/'backend-config.json').read_bytes());children=[]
assert 1024<=cfg['syntheticGISPort']<=65535 and cfg['syntheticGISPort']!=18767
if sys.argv[1]=='stop':
 value=resource_agent.stop(trusted,Q/'private-QA/manager',wait_seconds=90);assert value['phase']=='stopped';print(json.dumps({'normalManagerStopObserved':True}))
elif sys.argv[1]=='stopGIS':
 context=workspace_context(trusted['configuration'],trusted['installation'],verify_resources=False)
 assert context['root']in (Q/'old/Zhumadian',Q/'new/Zhumadian')
 owner=current_owner(context)
 if owner is not None:assert owner['port']==cfg['syntheticGISPort'];value=original_stop(context);assert value['phase']=='stopped'
 print(json.dumps({'normalSyntheticOriginalProtocolStopObserved':True}))
else:
 def start(context,*,progress):
  assert context['root']in(Q/'old/Zhumadian',Q/'new/Zhumadian')and context['configuration']==trusted['configuration']
  existing=current_owner(context)
  if existing is not None:
   assert existing['port']==cfg['syntheticGISPort'];return{'phase':existing['phase'],'alreadyRunning':True}
  source=SOURCE/'tests/synthetic_controller.py';assert hashlib.sha256(source.read_bytes()).hexdigest()=='30172eafcc83c3438958750035629c598d70b68804ce0be834065b7d53d6a0a1'
  folder=state_directory(context);log=folder/('bootstrap-'+secrets.token_hex(8)+'.log')
  with log.open('xb')as f:child=subprocess.Popen([str(context['installation']/'runtime/python/python.exe'),'-I','-B',str(source),str(context['configuration']),str(cfg['syntheticGISPort'])],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  children.append((child,context));child.stdin.write(b'D175-SYNTHETIC\n');child.stdin.flush();child.stdin.close()
  identity=process_identity(child.pid)
  (Q/('synthetic-launched-'+cycle+'-'+str(len(children))+'.json')).write_text(json.dumps({'controller':identity,'contextRoot':str(context['root']),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'syntheticNoProvider':True})+'\n','utf8')
  deadline=time.monotonic()+60
  while True:
   assert child.poll()is None,'OWN_SYNTHETIC_CONTROLLER_EXITED_BEFORE_READY'
   owner=current_owner(context)
   if owner is not None:assert owner['controller']['pid']==child.pid and owner['port']==cfg['syntheticGISPort'];return{'phase':'ready'}
   assert time.monotonic()<deadline,'OBSERVE_SAME_SYNTHETIC_HANDLE_NO_RESTART';time.sleep(.03)
 def factory(installation,configuration,*,expected_manifest,history_file):
  assert installation==trusted['installation']and configuration==trusted['configuration']and expected_manifest==trusted['registration']['GISInstallSHA256']
  context=workspace_context(configuration,installation,verify_resources=False);assert context['root']in(Q/'old/Zhumadian',Q/'new/Zhumadian')
  return RegisteredGIS(installation,configuration,expected_manifest=expected_manifest,history_file=history_file,qa=True,port=cfg['syntheticGISPort'],starter=start,base_override=context['root'])
 resource_agent.RegisteredGIS=factory
 def verify(grant,expected):
  began=time.monotonic();c=http.client.HTTPConnection('127.0.0.1',cfg['workerPort'],timeout=10)
  try:
   c.request('POST','/v2/client-resources/grants/consume',json.dumps({'grant':grant,'expected':expected}),{'Content-Type':'application/json'})
   response=c.getresponse();raw=response.read(16385);assert response.status==200 and len(raw)<=16384
   return ClockBoundGrant(json.loads(raw),deadline_after_roundtrip(checked_remaining_header(response.getheaders()),began,time.monotonic()))
  finally:c.close()
 agent=resource_agent.ResourceAgent(trusted,folder=Q/'private-QA/manager',port=0,qa=True,verifier=verify)
 def ready(port):
  with(Q/('manager-ready-'+cycle+'.json')).open('x',encoding='utf8')as f:json.dump({'port':port,'qualifiedTenCodePlus953':True},f)
 try:
  value=agent.serve(ready_callback=ready);assert value['normalStop']
 except BaseException:
  for child,context in children:
   if child.poll()is None:original_stop(context)
   child.wait()
  raise
 print(json.dumps({'normalManagerExit':True,'syntheticGISMayOutliveManager':True,'realOriginalProviderStarted':False}),flush=True)
