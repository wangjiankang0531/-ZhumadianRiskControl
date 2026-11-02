from pathlib import Path
import importlib.util,json,subprocess,time,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r158';attempt=sys.argv[1]if len(sys.argv)==2 else'r1';assert attempt in['r1','r2'];assert not(C/attempt).exists()
spec=importlib.util.spec_from_file_location('r157_controller_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
with(C/(attempt+'-outer.private.log')).open('xb')as log:
 p=subprocess.Popen([sys.executable,str(V/'verify_avatar_controller_r158_20261102.py'),'--attempt',attempt,'--variant','combined'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p);p.wait()
while job.active_processes():print('OWN_AVATAR_CONTROLLER_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(.2)
job.close();(C/(attempt+'-outer-terminal.json')).write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8');print('OWN_AVATAR_CONTROLLER_OUTER_EXIT_'+str(p.returncode));assert p.returncode==0
