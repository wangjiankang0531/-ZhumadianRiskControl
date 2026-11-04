from pathlib import Path
import ctypes,hashlib,json,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/workplace_style_delivery_r561_20261104';m=(ctypes.c_ulonglong*8)();m[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))and m[2]>1536*1024**2
assert not(R/'work/workplace-style-browser-r562').exists();sys.path.insert(0,str(R/'_g/Application/tools'));import original_server_windows_job as jobs
source=V/'verify_workplace_style_delivery_r562.mjs'
with(D/'chart-style-driver-r563.private.log').open('xb')as log:
 p=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=512',str(source)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=jobs.OwnedWindowsJob(p);p.wait()
 while job.active_processes():print('OWN_CHART_BROWSER_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(2)
 job.close()
terminal={'exitCode':p.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()};(D/'chart-style-terminal-r563.json').write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8');assert p.returncode==0,'OWN_CHART_BROWSER_FAILED_SEE_SCOPED_LOG'
r=json.loads((D/'chart-style-browser-result-r562.json').read_bytes());assert r['passed'];print(json.dumps({'passed':True,'layoutScenarios':len(r['rows']),'baselineOverlapReproduced':r['baselineReportedOverlapReproduced'],'actualDescendantsZero':True}))
