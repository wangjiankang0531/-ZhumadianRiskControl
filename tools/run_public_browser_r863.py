"""Run one isolated anonymous browser with a gated 1-GiB non-terminating Job."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;A=Path('D:/Project/Zhumadian/Application');O=V/'public-login-browser-r863'
assert not O.exists()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ownedSource=Path('D:/Project/Zhumadian/_g/Application/tools/original_server_windows_job.py')
assert hashlib.sha256(ownedSource.read_bytes()).hexdigest()=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=module('public_browser_owned_r863',ownedSource);policy=module('public_browser_budget_r863',A/'tools/bounded_build_job_r671.py')
limit=1024**3;memory=policy.memory_snapshot()
assert memory['availablePhysicalBytes']>=2*limit and memory['availableCommitBytes']>=2*limit,'TWO_GIB_BROWSER_RESERVE_REQUIRED_NO_USER_APPS_CLOSED'
O.mkdir();(O/'resource-plan.json').write_text(json.dumps({'jobCommitLimitBytes':limit,'minimumPhysicalAndCommitBytes':2*limit,'memoryBefore':memory,'ownProfileOnly':True,'forceTermination':False})+'\n',encoding='utf8')
p=None;job=None;budget=None;released=False;failure=None;metrics=None
try:
 with(O/'driver.private.log').open('xb')as out:
  p=subprocess.Popen(['node',str(V/'measure_public_login_browser_r863.mjs'),O.as_posix()],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  job=jobs.OwnedWindowsJob(p);budget=policy.BoundedBuildJob(job,limit)
  p.stdin.write(b'XNBY_PUBLIC_STATIC_BROWSER_R863\n');p.stdin.close();released=True
  while p.poll()is None:
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:print('OWN_PUBLIC_BROWSER_HANDLE_STILL_LIVE_NO_RESTART',flush=True)
except BaseException as error:failure=type(error).__name__
finally:
 if p is not None:
  if p.stdin is not None and not p.stdin.closed:p.stdin.write(b'ABORT_BEFORE_BROWSER\n');p.stdin.close()
  while p.poll()is None:
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:print('OWN_DRIVER_STILL_LIVE_NO_FORCE',flush=True)
 if job is not None:
  while job.active_processes():print('OWN_BROWSER_DESCENDANTS_STILL_LIVE_NO_CLEANUP',flush=True);time.sleep(2)
  if budget is not None:metrics=budget.metrics()
  job.close()
 proof={'driverExitCode':p.returncode if p else None,'actualJobDescendantsZero':job is not None,'gateReleased':released,'failureType':failure,'budgetMetricsBeforeClose':metrics,'publicWritePerformed':False,'desktopOperated':False,'userBrowserProfileUsed':False,'forceTerminationUsed':False}
 (O/'actual-job-terminal.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof),flush=True)
if failure or p is None or p.returncode!=0:raise SystemExit(1)
result=json.loads((O/'browser-results.json').read_bytes());assert result['completed']and len(result['rows'])==4
for row in result['rows']:print(json.dumps({k:v for k,v in row.items()if k!='assets'}),flush=True)
