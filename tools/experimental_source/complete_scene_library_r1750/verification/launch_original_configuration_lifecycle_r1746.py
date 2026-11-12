"""Release the real original-parent harness only after a non-terminating 6-GiB Job."""
from pathlib import Path
import importlib.util,subprocess,json,hashlib,time,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/su1746';D=R/'Document/Deployment/fine_browser_original_r1745_20261107';S=V/'run_original_configuration_lifecycle_r1746.py';PLAN=R/'work/fine-browser-parent-r1745/prepared-plan.private.json'
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
assert not W.exists();W.mkdir();assert not(W/'parent-started-r1746.json').exists()and not(W/'harness-started-r1746.json').exists()
plan=json.loads((PLAN).read_bytes());assert hashlib.sha256((PLAN).read_bytes()).hexdigest()=='244ce85ac28ce4da083e7f530d55473b76cbf58cd63dd2e34586682a4d20e09b';ast.parse(S.read_text('utf8'))
resource=json.loads((R/'work/fine-browser-parent-r1745/resource-and-reconciliation.json').read_bytes());assert hashlib.sha256((R/'work/fine-browser-parent-r1745/resource-and-reconciliation.json').read_bytes()).hexdigest()=='5750bf622263202c01a03fb4dd49c3e39a4fb55cfdbc9d2a37cf2fbb3d98fc95'
b=load('r1466_budget',R/'Application/tools/bounded_build_job_r671.py');j=load('r1466_jobs',R/'_g/Application/tools/original_server_windows_job.py');memory=b.memory_snapshot();assert min(memory['availablePhysicalBytes'],memory['availableCommitBytes'])>=15*1024**3
bootstrap="import sys,runpy;assert sys.stdin.buffer.readline(128)==b'OWN_ORIGINAL_SPATIAL_R1456\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
with(W/'harness-r1746.private.log').open('xb')as out:
    p=subprocess.Popen(['D:/Python/Python313/python.exe','-X','utf8','-I','-B','-c',bootstrap,str(S)],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
job=j.OwnedWindowsJob(p);cap=b.BoundedBuildJob(job,12*1024**3);(W/'parent-started-r1746.json').write_text(json.dumps({'pid':p.pid,'sourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'jobAssignedBeforeGate':True,'budgetBytes':12*1024**3}),encoding='utf8');p.stdin.write(b'OWN_ORIGINAL_SPATIAL_R1456\n');p.stdin.flush();p.stdin.close()
print(json.dumps({'actualHarnessPID':p.pid,'sameHandleWillBeRetained':True,'availablePhysicalBytes':memory['availablePhysicalBytes']}),flush=True)
while p.poll()is None:
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:print(json.dumps({'sameHarnessHandleLive':True,'metrics':cap.metrics()}),flush=True)
while job.active_processes():print('ACTUAL_OWN_JOB_NOT_ZERO_NO_CLOSE_OR_RESTART',flush=True);time.sleep(.5)
result={'exitCode':p.returncode,'actualOuterJobZero':True,'metrics':cap.metrics(),'forceTerminationUsed':False};job.close();(D/'actual-parent-terminal-r1746.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True);raise SystemExit(p.returncode)
