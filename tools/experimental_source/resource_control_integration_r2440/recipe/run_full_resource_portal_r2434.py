"""Gated complete safety build with an explicit non-terminating Windows Job budget."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');W=R/'work/hazard-management-full-r2434'
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not W.exists()
 jobs_path=R/'_g/Application/tools/original_server_windows_job.py'
 assert hashlib.sha256(jobs_path.read_bytes()).hexdigest()=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 jobs=load('hazard_build_r1123_jobs',jobs_path);budget=load('hazard_build_r1123_budget',R/'Application/tools/bounded_build_job_r671.py')
 cap=3*1024**3;snap=budget.memory_snapshot();assert snap['availablePhysicalBytes']>cap+3*1024**3 and snap['availableCommitBytes']>cap+2*1024**3
 source=V/'build_full_resource_portal_r2434.py';log=V/'hazard-management-full-r2434.private.log';assert not log.exists()
 env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','BROWSER']};env['BROWSER']='none'
 gate="import sys,runpy;line=sys.stdin.buffer.readline();assert line==b'XNBY_SCENE_HOST_PRODUCTION_R1509\\n';runpy.run_path(sys.argv[1],run_name='__main__')"
 with log.open('xb')as f:p=subprocess.Popen([sys.executable,'-I','-B','-c',gate,str(source)],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
 try:job=jobs.OwnedWindowsJob(p);bound=budget.BoundedBuildJob(job,cap)
 except BaseException:
  p.stdin.close();p.wait();raise
 print(json.dumps({'pid':p.pid,'actualJobAssignedBeforeGate':True,'jobCommitLimitBytes':cap,'memoryBefore':snap}),flush=True)
 p.stdin.write(b'XNBY_SCENE_HOST_PRODUCTION_R1509\n');p.stdin.flush();p.stdin.close()
 while p.poll()is None:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameHandleLive':True,'metrics':bound.metrics()}),flush=True)
 while job.active_processes():time.sleep(.2)
 result={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'metrics':bound.metrics(),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()};job.close()
 out=V/'hazard-management-full-r2434-outer-terminal.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True)
 assert p.returncode==0,'BUILD_ATTEMPT_FAILED_PRESERVE_AND_INSPECT_DO_NOT_RESTART'
if __name__=='__main__':main()
