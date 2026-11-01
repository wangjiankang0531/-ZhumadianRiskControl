"""Read-only ownership verification for the one user-created local acceptance record.
Preparation pins current runtime and original dependencies; execution is single-use.
No HTTP login, token/session acquisition, business calls, writes or service restarts.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_server_windows_job import OwnedWindowsJob
from run_original_work_start_sql_probe import alive_image
R=Path('D:/Project/Zhumadian');A=R/'Application';Q=Path('D:/Zqa20261025/Application')
O=R/'Document/Deployment/original_inventory_ownership_20261026';W=R/'work/original_inventory_ownership_20261026'
SOURCE=A/'tools/java/OriginalInventoryOwnershipReadProbe.java'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,j):
 assert not p.exists(),'FRESH_EVIDENCE_REQUIRED';p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def state():
 s=load(Q/'UserData/OriginalServer/current-run.json');assert s['ready'] and s['persistent']
 for pid,path in [(s['controllerPID'],Q/'runtime/python/python.exe'),(s['children']['mysql'],Q/'runtime/mysql/bin/mysqld.exe'),(s['children']['business'],Q/'runtime/jdk17/bin/java.exe')]:alive_image(pid,path)
 return s
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args();s=state()
 env={k:v for k,v in os.environ.items() if k.upper() not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
 if a.prepare:
  assert not W.exists() and not O.exists(),'FRESH_PHASE_REQUIRED';W.mkdir();O.mkdir();classes=W/'classes';classes.mkdir()
  prior=load(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
  for n,v in prior['inputPins'].items():assert sha(n)==v['SHA256'],'ORIGINAL_DEPENDENCY_CHANGED'
  java=Q/'runtime/jdk17/bin/java.exe';javac=java.with_name('javac.exe');assert sha(java)==prior['javaSHA256']
  c=subprocess.run([str(javac),'-encoding','UTF-8','-proc:none','-cp',prior['classpath'],'-d',str(classes),str(SOURCE)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
  (O/'compile.stdout.log').write_bytes(c.stdout);(O/'compile.stderr.log').write_bytes(c.stderr);assert c.returncode==0,'COMPILE_FAILED'
  pins={p.relative_to(classes).as_posix():sha(p) for p in classes.rglob('*.class')};assert len(pins)==1
  plan={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':sha(SOURCE),'runnerSHA256':sha(Path(__file__)),'java':str(java),'javaSHA256':sha(java),'javacSHA256':sha(javac),'inputPins':prior['inputPins'],'classpath':prior['classpath'],'classPins':pins,'runtimeStateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'releaseSHA256':sha(Q/'release-manifest.json'),'businessPropertiesSHA256':sha(Path(s['run'])/'b/application.properties'),'controllerPID':s['controllerPID'],'databaseUUID':s['databaseUUID'],'databasePort':s['databasePort'],'maximumStarts':1,'maximumSeconds':45,'maximumConnections':1,'maximumHeapMiB':128,'rawNamesOrIdsOutput':False,'originalBusinessOrAuthMethodsCalled':False,'SQLWritesOrDDLAllowed':False,'compileExitCode':0}
  write(O/'prepared.private.json',plan);print(json.dumps({'prepared':True,'compiledClasses':1,'databaseConnected':False,'dependenciesPinned':len(prior['inputPins'])}));return
 plan=load(O/'prepared.private.json');assert not (O/'started.json').exists(),'NO_UNCHANGED_RETRY';assert sha(SOURCE)==plan['sourceSHA256'] and sha(Path(__file__))==plan['runnerSHA256'];assert sha(Q/'UserData/OriginalServer/current-run.json')==plan['runtimeStateSHA256'] and sha(Q/'release-manifest.json')==plan['releaseSHA256'] and sha(Path(s['run'])/'b/application.properties')==plan['businessPropertiesSHA256'],'CURRENT_RUNTIME_CHANGED'
 for n,v in plan['inputPins'].items():assert sha(n)==v['SHA256'],'PINNED_DEPENDENCY_CHANGED'
 classes=W/'classes';assert {p.relative_to(classes).as_posix():sha(p) for p in classes.rglob('*.class')}==plan['classPins'];assert sha(plan['java'])==plan['javaSHA256']
 secret=load(Q/'private/server-configuration.json')['seedRootPassword'];out=O/'ownership.private.json';cmd=[plan['java'],'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(classes)+';'+plan['classpath'],'xnby.replica.OriginalInventoryOwnershipReadProbe',str(s['databasePort']),s['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),str(out)]
 process=subprocess.Popen(cmd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW);write(O/'started.json',{'PID':process.pid,'recordedAt':datetime.datetime.now().astimezone().isoformat()});print(json.dumps({'readOnlyProbePID':process.pid,'maximumSeconds':45}),flush=True);job=None;timed=False
 try:
  job=OwnedWindowsJob(process)
  try:stdout,stderr=process.communicate(secret.encode(),timeout=45)
  except subprocess.TimeoutExpired:timed=True;job.close();stdout,stderr=process.communicate(timeout=10)
 finally:
  if job:job.close()
  if process.poll() is None:process.kill();process.wait(timeout=5)
 for n,raw in [('stdout',stdout),('stderr',stderr)]:assert secret.encode() not in raw;(O/(n+'.log')).write_bytes(raw)
 del secret
 write(O/'process-result.json',{'PID':process.pid,'exitCode':process.returncode,'timedOut':timed,'resultExists':out.exists()});assert process.returncode==0 and not timed,'READ_ONLY_PROBE_FAILED'
 report=load(out);assert report['consistentReadOnlySnapshot'] and report['connectionClosed'] and not report['SQLWritesOrDDLExecuted'];state();assert sha(Q/'release-manifest.json')==plan['releaseSHA256'];print(json.dumps(report),flush=True)
if __name__=='__main__':main()
