"""Release the real original-parent harness only after a non-terminating 6-GiB Job."""
from pathlib import Path
import importlib.util,subprocess,json,hashlib,time,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/su1752';D=R/'Document/Deployment/fine_browser_original_r1748_20261107';S=V/'run_original_configuration_lifecycle_r1752.py';PLAN=R/'work/fine-browser-parent-r1748/prepared-plan.private.json'
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
assert not W.exists()
plan=json.loads((PLAN).read_bytes());assert hashlib.sha256((PLAN).read_bytes()).hexdigest()=='6ba8f485f70aea6853c7f956bc23e54a40413ca9195066028c2d46b30e17127d';ast.parse(S.read_text('utf8'))
resource=json.loads((R/'work/fine-browser-parent-r1748/resource-and-reconciliation.json').read_bytes());assert hashlib.sha256((R/'work/fine-browser-parent-r1748/resource-and-reconciliation.json').read_bytes()).hexdigest()=='6a1db7b61b29de64ead50f576f597f3e895fe4845c202781c9a748f61722cc69'
b=load('r1466_budget',R/'Application/tools/bounded_build_job_r671.py');j=load('r1466_jobs',R/'_g/Application/tools/original_server_windows_job.py');memory=b.memory_snapshot();assert min(memory['availablePhysicalBytes'],memory['availableCommitBytes'])>=15*1024**3
W.mkdir();assert not(W/'parent-started-r1752.json').exists()and not(W/'harness-started-r1752.json').exists()
bootstrap="import sys,runpy;assert sys.stdin.buffer.readline(128)==b'OWN_ORIGINAL_SPATIAL_R1456\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
with(W/'harness-r1752.private.log').open('xb')as out:
    p=subprocess.Popen(['D:/Python/Python313/python.exe','-X','utf8','-I','-B','-c',bootstrap,str(S)],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
job=j.OwnedWindowsJob(p);cap=b.BoundedBuildJob(job,12*1024**3);(W/'parent-started-r1752.json').write_text(json.dumps({'pid':p.pid,'sourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'jobAssignedBeforeGate':True,'budgetBytes':12*1024**3}),encoding='utf8');p.stdin.write(b'OWN_ORIGINAL_SPATIAL_R1456\n');p.stdin.flush();p.stdin.close()
print(json.dumps({'actualHarnessPID':p.pid,'sameHandleWillBeRetained':True,'availablePhysicalBytes':memory['availablePhysicalBytes']}),flush=True)
while p.poll()is None:
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:print(json.dumps({'sameHarnessHandleLive':True,'metrics':cap.metrics()}),flush=True)
while job.active_processes():print('ACTUAL_OWN_JOB_NOT_ZERO_NO_CLOSE_OR_RESTART',flush=True);time.sleep(.5)
result={'exitCode':p.returncode,'actualOuterJobZero':True,'metrics':cap.metrics(),'forceTerminationUsed':False};job.close();(D/'actual-parent-terminal-r1752.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True);raise SystemExit(p.returncode)
