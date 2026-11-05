from pathlib import Path
import importlib.util,subprocess,json,time,hashlib
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
jobs=load('click_probe_job_r954',R/'_g/Application/tools/original_server_windows_job.py');budget=load('click_probe_budget_r954',R/'Application/tools/bounded_build_job_r671.py')
assert not(R/'work/dl957').exists() and min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>2*1024**3
pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [V/'test_stable_download_click_r957.mjs',V/'stable_original_download_click_r954.mjs']}
with(V/'stable-download-r957.private.log').open('xb')as out:
 p=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=128',str(V/'test_stable_download_click_r957.mjs')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,1024**3);p.wait()
 while job.active_processes():time.sleep(.1)
 proof={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics(),'sourcePins':pins};job.close()
(V/'stable-download-terminal-r957.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof));raise SystemExit(p.returncode)
