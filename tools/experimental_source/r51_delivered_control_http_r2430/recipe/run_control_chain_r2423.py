"""Bound and gate the whole registered-3.12 control test; never force termination."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not Path('D:/Temp/Administrator/xnby-resource-control-r2422').exists()
 jp=R/'_g/Application/tools/original_server_windows_job.py';assert hashlib.sha256(jp.read_bytes()).hexdigest()=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 jobs=load('control2423jobs',jp);budget=load('control2423budget',R/'Application/tools/bounded_build_job_r671.py')
 snapshot=budget.memory_snapshot();assert snapshot['availablePhysicalBytes']>6*1024**3 and snapshot['availableCommitBytes']>5*1024**3
 gis=R/'Application/Packages/ClientGISSettingsCandidate_20261107';manifest=gis/'client-gis-install.json'
 assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='26342711ce4091661d71893ce43a1e0431417117ba9f9d522d3ce8ea738cac72'
 python=gis/'runtime/python/python.exe';pin=json.loads(manifest.read_bytes())['files']['runtime/python/python.exe'];assert python.stat().st_size==pin['bytes']and hashlib.sha256(python.read_bytes()).hexdigest()==pin['sha256']
 own=R/'Application/Packages/ResourceGISControlCandidate_20261112/client-250';own_manifest=own/'client-resources-install.json'
 assert hashlib.sha256(own_manifest.read_bytes()).hexdigest()=='bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b'
 for n,pin in json.loads(own_manifest.read_bytes())['files'].items():
  p=own/n;assert p.stat().st_size==pin['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256']
 script=V/'test_resource_control_chain_r2422.py'
 gate="import sys,runpy;assert sys.stdin.buffer.readline(64)==b'OWN_CONTROL_R2423\\n';runpy.run_path(sys.argv[1],run_name='__main__')"
 with(V/'resource-control-r2423.private.log').open('xb')as log:p=subprocess.Popen([str(python),'-I','-B','-c',gate,str(script)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 try:job=jobs.OwnedWindowsJob(p);bounded=budget.BoundedBuildJob(job,3*1024**3)
 except BaseException:p.stdin.close();p.wait();raise
 p.stdin.write(b'OWN_CONTROL_R2423\n');p.stdin.flush();p.stdin.close();print(json.dumps({'originalPID':p.pid,'gateAfterActualJobAssigned':True,'memoryBefore':snapshot}),flush=True)
 while p.poll()is None:
  try:p.wait(15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameOriginalHandleLive':True,'metrics':bounded.metrics()}),flush=True)
 while job.active_processes():time.sleep(.05)
 result={'rootExitCode':p.returncode,'actualJobBeforeClose':job.active_processes(),'metrics':bounded.metrics(),'forceTerminationUsed':False,'driverSHA256':hashlib.sha256(script.read_bytes()).hexdigest()};job.close()
 with(V/'resource-control-r2423-outer-terminal.json').open('x',encoding='utf8')as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result),flush=True);assert p.returncode==0,'FAILED_ATTEMPT_IS_TERMINAL_KEEP_EVIDENCE_DO_NOT_RESTART'
if __name__=='__main__':main()
