from pathlib import Path
import hashlib,json,secrets,socket,subprocess,sys,threading,time
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_control_20261112';W=R/'work/resource_gis_control_20261112';D=R/'Document/Deployment/resource_gis_control_20261112';GIS=A/'Packages/ClientGISSettingsCandidate_20261107'
sys.path[:0]=[str(P/'code'),str(GIS/'code'),str(GIS/'provider/tools')]
from registered_gis import RegisteredGIS
from client_settings import workspace_document
from client_manifest import workspace_context
from client_gis_runtime import current_owner,stop as original_stop
from osgb_stdio_worker import OwnedWindowsJob
root=W/'synthetic/Zhumadian';root.mkdir(parents=True,exist_ok=False);cfg=root/'Config/client-workspace.json';cfg.parent.mkdir();cfg.write_text(json.dumps(workspace_document(root.as_posix())),encoding='utf-8')
listener=socket.socket();listener.bind(('127.0.0.1',0));port=listener.getsockname()[1];listener.close();children=[];progress=[];accepts=[]
def start(context,*,progress):
 log=(D/'synthetic-controller.log').open('xb');child=subprocess.Popen([str(GIS/'runtime/python/python.exe'),'-I','-B',str(P/'tests/synthetic_controller.py'),str(cfg),str(port)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);log.close();job=OwnedWindowsJob(child);children.append((child,job,context));child.stdin.write(b'D175-SYNTHETIC\n');child.stdin.close()
 deadline=time.monotonic()+45
 while True:
  assert child.poll()is None,'Synthetic controller unexpectedly exited'
  owner=current_owner(context)
  if owner is not None:assert owner['port']==port;return{'phase':'ready'}
  assert time.monotonic()<deadline,'Original synthetic controller not ready';time.sleep(.03)
gis=RegisteredGIS(GIS,cfg,expected_manifest=hashlib.sha256((GIS/'client-gis-install.json').read_bytes()).hexdigest(),qa=True,port=port,starter=start,base_override=root)
def commit(operation):accepts.append(True);return operation()
rows=[]
try:
 assert gis.status()['phase']=='stopped'
 value=gis.execute('start',commit=commit,cancel_event=threading.Event(),progress=progress.append);assert value['phase']=='ready'and gis.status()['owned']is True
 assert len(children)==1
 value=gis.execute('stop',commit=commit,cancel_event=threading.Event(),progress=progress.append);assert value['phase']=='stopped'and value['registeredOwnerOnly']is True
 assert gis.status()['phase']=='stopped'
finally:
 for child,job,context in children:
  if child.poll()is None:original_stop(context)
  child.wait()
  while job.active_processes():time.sleep(.03)
  job.close();rows.append({'originalPID':child.pid,'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes})
  assert child.returncode==0 and job.final_active_processes==0
assert len(accepts)==2
result={'passed':True,'actualNewAdapterToUnmodifiedOriginalStopProtocol':True,'original953AndOriginalConfigQualification':True,'syntheticControllerExplicitNoGISOrProviderData':True,'fixedQAOnlyRandomPort':True,'separateOriginalPopenAndActualJobZero':rows,'twoExplicitAcceptedIntents':len(accepts),'noLive250252OrPublicAction':True,'fullOriginalProviderStartAndRootRelocationNotTested':True}
(D/'actual-synthetic-control.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
