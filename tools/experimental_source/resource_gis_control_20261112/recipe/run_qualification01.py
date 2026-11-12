from pathlib import Path
import json,subprocess,sys,time
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_control_20261112';W=R/'work/resource_gis_control_20261112';D=R/'Document/Deployment/resource_gis_control_20261112/qualification01';GIS=A/'Packages/ClientGISSettingsCandidate_20261107';LEGACY=A/'Packages/ClientGISIntegrityCandidate_20261107'
sys.path.insert(0,str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools'));from osgb_stdio_worker import OwnedWindowsJob
phases=[]
for label,file,dep in [('own-programme-qualification','actual_programme_qualification.py',GIS)]:
 boot="import sys,runpy;sys.path[:0]="+repr([str(P/'code'),str(dep/'code'),str(dep/'provider/tools')])+";runpy.run_path("+repr(str(P/'tests'/file))+",run_name='__main__')"
 phases.append((label,[str(dep/'runtime/python/python.exe'),'-I','-B','-c',boot]))

rows=[]
for label,args in phases:
 gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D175\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
 with (D/(label+'.log')).open('xb')as log:
  child=subprocess.Popen([sys.executable,'-I','-B','-c',gate,*args],cwd=W,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  job=OwnedWindowsJob(child);child.stdin.write(b'D175\n');child.stdin.close();print(json.dumps({'phase':label,'originalPID':child.pid}),flush=True)
  while child.poll()is None:
   try:child.wait(10)
   except subprocess.TimeoutExpired:print(json.dumps({'phase':label,'sameOriginalHandleLive':True}),flush=True)
  while job.active_processes():time.sleep(.05)
  job.close();row={'phase':label,'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes};rows.append(row);(D/'original-roots.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
print(json.dumps({'allPassed':all(row['rootExitCode']==0 and row['originalJobBeforeClose']==0 for row in rows),'syntheticFixturesOnlyNoLiveGISAction':True}),flush=True)
raise SystemExit(0 if all(row['rootExitCode']==0 for row in rows)else 1)
