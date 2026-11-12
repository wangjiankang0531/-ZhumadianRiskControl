from pathlib import Path
import ctypes,json,subprocess,sys,time
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';W=R/'work/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112/attempt03';GIS=A/'Packages/ClientGISSettingsCandidate_20261107'
sys.path.insert(0,str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools'));from osgb_stdio_worker import OwnedWindowsJob
class Memory(ctypes.Structure):_fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('commitTotal',ctypes.c_ulonglong),('commitAvailable',ctypes.c_ulonglong),('virtualTotal',ctypes.c_ulonglong),('virtualAvailable',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
memory=Memory();memory.length=ctypes.sizeof(memory);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory));assert min(memory.available,memory.commitAvailable)>3*1024**3,'Need actual3GiB before resource-only UI test'
payload=[str(GIS/'runtime/python/python.exe'),'-I','-B',str(P/'tests/run_browser03.py')]
gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D176\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
with (D/'outer-original.log').open('xb') as log:
 child=subprocess.Popen([sys.executable,'-I','-B','-c',gate,*payload],cwd=W,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=OwnedWindowsJob(child);child.stdin.write(b'D176\n');child.stdin.close();print(json.dumps({'phase':'actualVue-qualified-resource-service','originalPID':child.pid}),flush=True)
 while child.poll() is None:
  try:child.wait(10)
  except subprocess.TimeoutExpired:print(json.dumps({'sameOriginalHandleLive':True,'pid':child.pid}),flush=True)
 while job.active_processes():time.sleep(.1)
 job.close();row={'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes};(D/'outer-original-terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
 assert child.returncode==0 and job.final_active_processes==0,'Inspect original qualified browser log'
