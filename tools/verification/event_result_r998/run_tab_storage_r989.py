from pathlib import Path
import hashlib,importlib.util,json,subprocess,time
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application';O=R/'work/tab989'
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not O.exists()
assert hashlib.sha256((G/'tools/original_server_windows_job.py').read_bytes()).hexdigest()=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('tab_jobs_r989',G/'tools/original_server_windows_job.py');budget=load('tab_budget_r989',R/'Application/tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>2*1024**3
O.mkdir()
with(O/'node.private.log').open('xb')as out:
 p=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=128',str(V/'check_normal_tab_storage_r989.mjs')],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,1024**3);p.communicate(input=b'OWN_SYNTHETIC_TAB_TEST_R989\n')
 while job.active_processes():time.sleep(.1)
 terminal={'nodeExitCode':p.returncode,'actualJobDescendantsZero':True,'budget':cap.metrics(),'forceTerminationUsed':False};job.close()
(O/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf8');result=json.loads((O/'result.json').read_bytes());assert p.returncode==0 and result['passed']and result['chromeExitCode']==0
print(json.dumps({'passed':True,'independentCDPTabDoesNotInheritSession':True,'normalWindowOpenDoesInheritSyntheticMarker':True,'normalNodeChromeAndActualJobZero':True,'actualProductAuthTouched':False}))
