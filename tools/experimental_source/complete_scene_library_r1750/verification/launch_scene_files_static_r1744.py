"""Gate real static gateway test in a non-terminating bounded Job."""
from pathlib import Path
import importlib.util,json,subprocess,sys,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/scene_fine_auth_stage_r1743_20261107'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
jobs=load('jobs1483',R/'_g/Application/tools/original_server_windows_job.py');budget=load('budget1483',R/'Application/tools/bounded_build_job_r671.py')
assert not(D/'actual-static-outer-r1744.json').exists()
bootstrap="import sys,runpy;assert sys.stdin.buffer.readline(100)==b'OWN_SCENE_STATIC_R1564\\n';runpy.run_path(sys.argv[1],run_name='__main__')"
log=V/'scene-static-r1744.private.log';assert not log.exists()
with log.open('xb')as out:p=subprocess.Popen([sys.executable,'-I','-B','-c',bootstrap,str(V/'verify_scene_files_static_r1744.py')],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
try:job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,1024**3)
except BaseException:p.stdin.close();p.wait();raise
p.stdin.write(b'OWN_SCENE_STATIC_R1564\n');p.stdin.close()
while p.poll()is None:
 try:p.wait(timeout=15)
 except subprocess.TimeoutExpired:print(json.dumps({'sameActualStaticTestHandleLive':True,'metrics':cap.metrics()}),flush=True)
while job.active_processes():time.sleep(.1)
result={'exitCode':p.returncode,'actualJobZero':True,'forceTerminationUsed':False,'metrics':cap.metrics()};job.close();(D/'actual-static-outer-r1744.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True)
raise SystemExit(p.returncode)
