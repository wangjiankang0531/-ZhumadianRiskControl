"""Copy only owned runtime code to the exact retained launch layout; no deployment or production configuration."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,uuid
sys.dont_write_bytecode=True
T=Path('D:/Project/Zhumadian/Application/tools');sys.path.insert(0,str(T))
import verify_emergency_business_http_20261030 as c
def checked_tree(source,target):
 source=source.resolve();assert not target.exists()
 for directory,dirs,files in os.walk(source):
  for name in dirs+files:assert not (Path(directory,name).lstat().st_file_attributes&0x400)
 shutil.copytree(source,target)
def main():
 p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();assert __import__('re').fullmatch('r[1-9][0-9]*',a.revision)
 root=c.W/('full-business-main-'+a.revision);short=c.R/'_b';assert not root.exists() and not short.exists();assert shutil.disk_usage(c.W).free>3*1024**3
 short.mkdir();owner=str(uuid.uuid4());(short/'own-fixture.json').write_text(json.dumps({'schema':'xnby.whole-business-short-runtime.v1','owner':owner,'evidenceRoot':str(root),'preparedRuntime':True}),encoding='utf8')
 runtime=short/'Application/runtime';runtime.mkdir(parents=True);checked_tree(c.Q/'runtime/jdk8',runtime/'jdk8');py=runtime/'python';py.mkdir();original=c.Q/'runtime/python'
 for name in ['python.exe','python3.dll','python312.dll','vcruntime140.dll','vcruntime140_1.dll']:shutil.copy2(original/name,py/name);assert c.sha(original/name)==c.sha(py/name)
 (py/'python312._pth').write_text('\n'.join([str(original/'Lib'),str(original/'DLLs'),str(T)])+'\n',encoding='utf8')
 c.dump(short/'runtime-code-pins.json',{str(p.relative_to(short)):c.sha(p) for p in runtime.rglob('*') if p.is_file()})
 env={k:v for k,v in os.environ.items() if k.upper() not in ['PYTHONHOME','PYTHONPATH','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
 with open(short/'bootstrap.stdout.log','wb') as out,open(short/'bootstrap.stderr.log','wb') as err:
  child=subprocess.Popen([str(py/'python.exe'),'-I','-B',str(T/'verify_unified_candidate_runtime_20261101.py'),'--revision',a.revision,'--prepared-short'],cwd=short,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);job=c.OwnedWindowsJob(child)
  import ctypes,time
  class Accounting(ctypes.Structure):
   _fields_=[('user',ctypes.c_longlong),('kernel',ctypes.c_longlong),('periodUser',ctypes.c_longlong),('periodKernel',ctypes.c_longlong),('faults',ctypes.c_ulong),('total',ctypes.c_ulong),('active',ctypes.c_ulong),('terminated',ctypes.c_ulong)]
  while child.poll()is None:
   try:child.wait(timeout=30)
   except subprocess.TimeoutExpired:pass
  while True:
   accounting=Accounting();assert job.api.QueryInformationJobObject(job.handle,1,ctypes.byref(accounting),ctypes.sizeof(accounting),None)
   if accounting.active==0:break
   print('OWN_SUBPROCESSES_STILL_LIVE_JOB_HELD_NO_FORCE',flush=True);time.sleep(10)
  job.close()

 c.dump(short/'controller-terminal.json',{'pid':child.pid,'exitCode':child.returncode,'jobClosed':True});print('OWN_WHOLE_MAIN_CONTROLLER_EXIT',child.returncode)
 if child.returncode:raise RuntimeError('OWN_FULL_MAIN_CONTROLLER_NOT_PASSED')
if __name__=='__main__':main()
