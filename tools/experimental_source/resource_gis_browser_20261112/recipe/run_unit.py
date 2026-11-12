from pathlib import Path
import json,subprocess,sys,time
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112';sys.path.insert(0,str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools'));from osgb_stdio_worker import OwnedWindowsJob
tests=sorted((P/'web/tests').glob('*.test.mjs'));assert len(tests)==4;gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D176\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
with(D/'compact-node.log').open('xb')as log:
 child=subprocess.Popen([sys.executable,'-I','-B','-c',gate,'D:/Program Files/nodejs/node.exe','--max-old-space-size=256','--test',*[str(f)for f in tests]],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(child);child.stdin.write(b'D176\n');child.stdin.close();child.wait()
 while job.active_processes():time.sleep(.05)
 job.close();result={'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes};(D/'compact-node-original-root.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert child.returncode==0 and job.final_active_processes==0
