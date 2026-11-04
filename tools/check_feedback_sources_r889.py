"""Compile the fixed Java probes before any fixture relation or callback SQL."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;D=V/'feedback_r889';R=Path('D:/Project/Zhumadian');T=R/'Application/tools';G=R/'_g/Application';O=V/'feedback-source-compile-r889'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not O.exists()
 pins=json.loads((D/'feedback-existing-r889-source-pins.json').read_bytes())['files']
 for name,pin in pins.items():assert sha(Path(name))==pin
 for p in D.glob('*.py'):ast.parse(p.read_bytes())
 budget=module('feedback_compile_budget_r881',T/'bounded_build_job_r671.py');snap=budget.memory_snapshot();assert min(snap['availablePhysicalBytes'],snap['availableCommitBytes'])>2*1024**3
 jobs=module('feedback_compile_jobs_r881',G/'tools/original_server_windows_job.py')
 O.mkdir();classes=O/'classes';classes.mkdir()
 source=[T/'OwnedOriginalCallbacksR648.java',T/'OwnedOriginalCallbackProvisioningR659.java',T/'OwnedWindowsProcessArgumentsR747.java',
  D/'OwnedCallbackProvisioningJournalR658.java',D/'OwnOriginalCallbackRuntimeR770.java',D/'OwnManagerBusinessReadbackR783.java',D/'OwnOriginalManagerDirectoryR609.java']
 cmd=[str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',str(G/'payload/platform/boot-loader.jar'),'-d',str(classes),*map(str,source)]
 with(O/'compile.log').open('xb')as log:
  p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,512*1024**2)
  while p.poll()is None:
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:print('SAME_OWN_COMPILER_HANDLE_LIVE_NO_RESTART',flush=True)
  while job.active_processes():time.sleep(.1)
  metrics=cap.metrics();job.close()
 assert all(sha(Path(n))==pin for n,pin in pins.items())
 result={'passed':p.returncode==0,'sources':{str(p):sha(p)for p in source},'compilerExitCode':p.returncode,'actualJobDescendantsZero':True,'budget':metrics,
  'servicesStarted':False,'databaseAccessed':False,'businessWritesPerformed':False,'nativeEXEBuiltOrRun':False}
 (O/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='sources'}))
 if p.returncode:raise SystemExit(1)
if __name__=='__main__':main()
