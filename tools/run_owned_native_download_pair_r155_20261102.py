from pathlib import Path
import importlib.util,json,subprocess,time,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r154';J=lambda p:json.loads(p.read_bytes());assert J(C/'r4/controller-terminal.json')['actualDescendantJobCountZeroBeforeClose'];assert J(R/'_g/own-fixture.json')['ownedSyntheticFixtureOnly']and not(R/'_g/user-manual-protected.json').exists();spec=importlib.util.spec_from_file_location('own_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
p=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(V/'verify_owned_native_download_pair_r155_20261102.mjs')],creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p)
try:
 p.wait()
 while job.active_processes():print('OWN_DIAGNOSTIC_BROWSER_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(.2)
finally:
 if p.poll()is not None and job.active_processes()==0:job.close()
assert p.returncode==0
out=C/'native-download-driver-r155-r2';(out/'outer-terminal.json').write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8')
