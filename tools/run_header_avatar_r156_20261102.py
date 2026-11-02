from pathlib import Path
import importlib.util,json,subprocess,time,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;assert json.loads((R/'_g/own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly'];spec=importlib.util.spec_from_file_location('avatar_owned_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j);run=sys.argv[1]if len(sys.argv)==2 else'browser-r1';assert __import__('re').fullmatch('browser-r[1-9][0-9]*',run)
log=R/'work/user_feedback_20261031/avatar-source-r156'/(run+'-driver.log');assert not log.exists()
with log.open('wb') as stream:
 p=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(V/'verify_header_avatar_r156_20261102.mjs'),run],stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p);p.wait()
while job.active_processes():print('OWN_AVATAR_BROWSER_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(.2)
job.close();out=R/'work/user_feedback_20261031/avatar-source-r156'/run;out.mkdir(exist_ok=True);(out/'outer-terminal.json').write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8');print(log.read_text(encoding='utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii'));assert p.returncode==0
