from pathlib import Path
import importlib.util,subprocess,json,time,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/public_test_personal_workflow_r35_20261103'
spec=importlib.util.spec_from_file_location('public_r33_browser_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
assert not(D/'public-ui-r202-outer-terminal.json').exists()
p=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(V/'verify_public_personal_workflow_r202.mjs')]);job=j.OwnedWindowsJob(p);p.wait()
while job.active_processes():print('PUBLIC_BROWSER_NORMAL_DESCENDANTS_STILL_EXITING_NO_FORCE',flush=True);time.sleep(.2)
job.close();(D/'public-ui-r202-outer-terminal.json').write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8');print('PUBLIC_R35_BROWSER_TERMINAL_'+str(p.returncode));assert p.returncode==0
