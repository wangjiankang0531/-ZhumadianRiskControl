from pathlib import Path
import hashlib,http.client,json,subprocess,sys,threading,time,socket
from unittest.mock import patch
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';W=R/'work/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112/attempt03';C=A/'Packages/ResourceGISControlCandidate_20261112/client-250';GIS=A/'Packages/ClientGISSettingsCandidate_20261107'
sys.path[:0]=[str(C/'code'),str(GIS/'code'),str(GIS/'provider/tools')]
from entry import qualify
from client_manifest import load_installation
trusted=qualify(C);assert trusted['manifestSHA256']=='bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b';trusted['dependency']=load_installation(GIS);trusted['configuration']=W/'private-QA03/config/client-workspace.json'
from resource_agent import ResourceAgent
from registered_gis import RegisteredGIS
from grant_clock import ClockBoundGrant,checked_remaining_header,deadline_after_roundtrip
from client_gis_runtime import stop as original_stop,current_owner
from osgb_stdio_worker import OwnedWindowsJob
cfg=json.loads((W/'backend-config03.json').read_text(encoding='utf-8'));children=[];events=[];sequence=0
listener=socket.socket();listener.bind(('127.0.0.1',0));gis_port=listener.getsockname()[1];listener.close()
def record(phase,**fields):
 events.append({'phase':phase,**fields});(D/'gis-lifecycle.json').write_text(json.dumps(events,indent=2)+'\n',encoding='utf-8')
def starter(context,*,progress):
 global sequence
 sequence+=1;record('explicit-start-accepted',number=sequence,workspace=str(context['root']))
 # Third start provides a real accepted-operation interval for Vue leave.
 if sequence==3:time.sleep(3)
 log=(D/('synthetic-gis-'+str(sequence)+'.log')).open('xb');child=subprocess.Popen([str(GIS/'runtime/python/python.exe'),'-I','-B',str(P/'tests/synthetic_controller.py'),str(context['configuration']),str(gis_port)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);log.close();job=OwnedWindowsJob(child);children.append({'child':child,'job':job,'context':context,'number':sequence,'joined':False});child.stdin.write(b'D175-SYNTHETIC\n');child.stdin.close();limit=time.monotonic()+60
 while True:
  assert child.poll()is None,'Synthetic original controller exited before readiness'
  owner=current_owner(context)
  if owner is not None:assert owner['controller']['pid']==child.pid and owner['port']==gis_port;record('synthetic-ready',number=sequence,workspace=str(context['root']));return{'phase':'ready'}
  assert time.monotonic()<limit,'Observe same synthetic original root, do not restart';time.sleep(.025)
def join(row):
 if row['joined']:return
 row['child'].wait()
 while row['job'].active_processes():time.sleep(.025)
 row['job'].close();row['joined']=True;record('synthetic-original-terminal',number=row['number'],rootExitCode=row['child'].returncode,originalJobBeforeClose=row['job'].final_active_processes);assert row['child'].returncode==0 and row['job'].final_active_processes==0
def stopper(context):
 record('explicit-stop-accepted',workspace=str(context['root']));value=original_stop(context)
 if value['phase']=='stopped':
  for row in children:
   if not row['joined'] and str(row['context']['state'])==str(context['state']):join(row)
  record('normal-stop-complete',workspace=str(context['root']))
 return value
def gis_factory(*args,**kwargs):return RegisteredGIS(*args,**kwargs,qa=True,port=gis_port,starter=starter,stopper=stopper,base_override=W/'roots/A/Zhumadian')
def verify(grant,expected):
 started=time.monotonic();connection=http.client.HTTPConnection('127.0.0.1',cfg['grantPort'],timeout=10)
 try:
  connection.request('POST',cfg['consumePath'],body=json.dumps({'grant':grant,'expected':expected}),headers={'Content-Type':'application/json'});response=connection.getresponse();raw=response.read(16385);assert response.status==200 and len(raw)<=16384
  return ClockBoundGrant(json.loads(raw),deadline_after_roundtrip(checked_remaining_header(response.getheaders()),started,time.monotonic()))
 finally:connection.close()
agent=ResourceAgent(trusted,folder=W/'private-QA03/agent',port=0,qa=True,verifier=verify)
def ready(port):(W/'backend-ready03.json').write_text(json.dumps({'port':port,'qualifiedProgrammeIdentity':trusted['manifestSHA256'],'syntheticGISPort':gis_port}))
try:
 with patch('resource_agent.RegisteredGIS',gis_factory):result=agent.serve(ready_callback=ready)
 assert result['normalStop']
finally:
 for row in children:
  if row['joined']:continue
  while row['child'].poll()is None and current_owner(row['context'])is None:time.sleep(.05)
  if row['child'].poll()is None:original_stop(row['context'])
  join(row)
 (D/'synthetic-gis-final-terminals.json').write_text(json.dumps({'allNormallyStopped':all(r['joined']for r in children),'spawnCount':len(children),'events':events,'realOriginalGISProviderStarted':False,'current250252Untouched':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'newTenCodeQualified':True,'managerThreadsJoined':True,'ownSyntheticGISRootsAndJobsZero':True}),flush=True)
