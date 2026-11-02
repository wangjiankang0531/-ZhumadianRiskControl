from pathlib import Path
import importlib.util,json,subprocess,time,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;role=sys.argv[1];assert role in ['security_pc','emergency_pc'];out=R/'work/user_feedback_20261031/avatar-full-r157';out.mkdir(exist_ok=True)
assert json.loads((R/'_g/own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']
spec=importlib.util.spec_from_file_location('r157_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
log=out/(role+'-outer.log');assert not log.exists()
with log.open('wb')as stream:
 p=subprocess.Popen([sys.executable,str(V/'build_avatar_full_r157_20261102.py'),role],stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p);p.wait()
while job.active_processes():print('OWN_BUILD_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(.2)
job.close();(out/(role+'-outer-terminal.json')).write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8');print(log.read_text(encoding='utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii'));assert p.returncode==0
