from pathlib import Path
import importlib.util,json,subprocess,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/scene_library_original_package_r1737_20261107'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
j=load('r1739_jobs',R/'_g/Application/tools/original_server_windows_job.py');b=load('r1739_budget',R/'Application/tools/bounded_build_job_r671.py');assert min(b.memory_snapshot()[k]for k in['availablePhysicalBytes','availableCommitBytes'])>3*1024**3
out=D/'actual-backend-r1739.private.log';assert not out.exists()
with out.open('xb')as log:
 p=subprocess.Popen(['D:/Python/Python313/python.exe','-X','utf8','-I','-B',str(V/'test_scene_original_package_r1739.py')],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p);cap=b.BoundedBuildJob(job,1024**3);p.stdin.write(b'OWN_SCENE_BACKEND_R1739\n');p.stdin.close()
 while p.poll()is None:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameOwnedBackendTestHandleLive':True,'metrics':cap.metrics()}),flush=True)
 while job.active_processes():time.sleep(.05)
 result={'exitCode':p.returncode,'actualJobZero':True,'metrics':cap.metrics(),'forceTerminationUsed':False};job.close()
(D/'actual-backend-terminal-r1739.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result));raise SystemExit(p.returncode)
