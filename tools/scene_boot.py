"""Ensure the existing pinned local scene is ready; never replace an active listener."""
from pathlib import Path
import argparse,ctypes,datetime,hashlib,json,os,socket,subprocess,sys,time,urllib.request,uuid

APP=Path('D:/Project/Zhumadian/Application')
PACKAGE=APP/'work/demo_20261024/local_scene'
IDENTITY='f6a5758586635b70025773c3e40083e0c51c7bc01cc02db74cf491233dd7293a'
STATE=APP/'UserData/LocalEmergencyScene'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path):
 path=Path(path).absolute()
 for p in [path,*path.parents]:
  if p.exists()and(p.is_symlink()or getattr(p.lstat(),'st_file_attributes',0)&0x400):raise ValueError('SCENE_REPARSE_PATH_REFUSED')
 if path.exists()and path.resolve()!=path:raise ValueError('SCENE_REDIRECTED_PATH_REFUSED')
 return path
def pin_package(root):
 root=regular(root)
 if root!=PACKAGE:raise ValueError('ONLY_FIXED_LOCAL_SCENE_PACKAGE')
 manifest=(root/'source_runtime_manifest.json').read_bytes()
 if sha(manifest)!=IDENTITY:raise ValueError('SCENE_PACKAGE_MANIFEST_DRIFT')
 files=json.loads(manifest)['files']
 for name in ['runtime/python/python.exe','application/tools/portable_web_entry.py']:
  raw=regular(root/name).read_bytes();pin=files[name]
  if len(raw)!=pin['bytes']or sha(raw)!=pin['sha256']:raise ValueError('SCENE_LAUNCH_INPUT_DRIFT')
 return files
def process_image(pid):
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
 kernel.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)];kernel.QueryFullProcessImageNameW.restype=ctypes.c_int
 kernel.CloseHandle.argtypes=[ctypes.c_void_p]
 handle=kernel.OpenProcess(0x1000,False,pid)
 if not handle:return None
 try:
  text=ctypes.create_unicode_buffer(32768);size=ctypes.c_uint32(len(text))
  if not kernel.QueryFullProcessImageNameW(handle,0,text,ctypes.byref(size)):return None
  return Path(text.value).resolve()
 finally:kernel.CloseHandle(handle)
def health(root,port,files):
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 try:
  with opener.open(f'http://127.0.0.1:{port}/api/runtime/status',timeout=3)as r:
   value=json.loads(r.read(2*1024**2+1))
  if value.get('identity')!=IDENTITY or value.get('readOnly')is not True or value.get('conversionEnabled')is not False or value.get('port')!=port:return None
  pid=value.get('pid')
  if type(pid)is not int or process_image(pid)!=(root/'runtime/python/python.exe').resolve():return None
  pin=files['web/viewer.js']
  with opener.open(f'http://127.0.0.1:{port}/viewer.js',timeout=3)as r:body=r.read(pin['bytes']+1)
  if len(body)!=pin['bytes']or sha(body)!=pin['sha256']:return None
  return {'servicePID':pid,'port':port,'identity':IDENTITY,'readOnlySource':True,'conversionEnabled':False,'servedViewerMatchesFrozenSource':True}
 except Exception:return None
def port_free(port):
 with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as probe:
  probe.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
  try:probe.bind(('127.0.0.1',port));return True
  except OSError:return False
def existing_owner_count(root,port):
 # Return a count only; neither command lines nor any other process data leave the subprocess.
 scope=str(root).replace("'","''")
 ps="$p=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.ExecutablePath -eq '"+scope+"\\runtime\\python\\python.exe' -and $_.CommandLine -match 'portable_web_entry.py|portable_source_runtime.py' -and $_.CommandLine -match '--port[ =]+"+str(port)+"(?: |$)' });[Console]::Write($p.Count)"
 r=subprocess.run([str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-NonInteractive','-Command',ps],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
 if r.returncode or not r.stdout.decode('ascii').strip().isdigit():raise RuntimeError('SCENE_EXISTING_PROCESS_CHECK_FAILED')
 return int(r.stdout.decode('ascii').strip())
def ensure(root=PACKAGE,port=8767):
 files=pin_package(root);live=health(root,port,files)
 if live:return {'ready':True,'reusedExistingService':True,'newServiceStarted':False,**live}
 if not port_free(port):raise RuntimeError('SCENE_PORT_OCCUPIED_IDENTITY_MISMATCH_NO_SERVICE_CHANGED')
 if existing_owner_count(root,port):raise RuntimeError('SCENE_OWNER_STILL_STARTING_OBSERVE_EXISTING_NO_DUPLICATE')
 regular(STATE);STATE.mkdir(parents=True,exist_ok=True);tag=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
 command=[str(root/'runtime/python/python.exe'),'-I','-B',str(root/'application/tools/portable_web_entry.py'),'--package',str(root),'--port',str(port),'--no-browser']
 with (STATE/(tag+'.out.log')).open('xb')as out,(STATE/(tag+'.err.log')).open('xb')as err:
  child=subprocess.Popen(command,cwd=root,stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
 started={'launcherPID':child.pid,'at':datetime.datetime.now().astimezone().isoformat(),'identity':IDENTITY,'commandIsPinnedOriginalLauncher':True,'browserRequested':False,'state':'starting-observe-this-process'}
 (STATE/(tag+'.launch.json')).write_text(json.dumps(started,indent=2)+'\n',encoding='utf-8')
 end=time.monotonic()+60
 while time.monotonic()<end:
  live=health(root,port,files)
  if live:return {'ready':True,'reusedExistingService':False,'newServiceStarted':True,'launcherPID':child.pid,**live}
  if child.poll()is not None:raise RuntimeError('SCENE_LAUNCHER_EXITED_CHECK_OWN_LOGS')
  time.sleep(.25)
 raise RuntimeError('SCENE_READY_PENDING_OBSERVE_EXISTING_LAUNCHER_NO_RESTART')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 if os.name!='nt':raise RuntimeError('WINDOWS_SCENE_LAUNCHER_ONLY')
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p;kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
 mutex=kernel.CreateMutexW(None,False,'Local\\XNBYZhumadianScene8767')
 if not mutex:raise RuntimeError('SCENE_SINGLE_START_LOCK_FAILED')
 acquired=False;result=None
 try:
  code=kernel.WaitForSingleObject(mutex,65000)
  if code not in (0,0x80):raise RuntimeError('SCENE_START_ALREADY_IN_PROGRESS')
  acquired=True
  if args.check_only:
   files=pin_package(PACKAGE);live=health(PACKAGE,8767,files)
   if live is None:raise RuntimeError('SCENE_NOT_CURRENTLY_READY_NO_START_REQUESTED')
   result={'ready':True,'checkOnly':True,'newServiceStarted':False,**live}
  else:result=ensure()
  result.update(at=datetime.datetime.now().astimezone().isoformat(),desktopInputSent=False,userLayersOrSourceGISChangedByEnsurer=False)
 except Exception as error:
  result={'ready':False,'error':str(error),'at':datetime.datetime.now().astimezone().isoformat(),'forcedStopOrRestartUsed':False,'desktopInputSent':False}
  raise
 finally:
  if result is not None:
   regular(STATE);STATE.mkdir(parents=True,exist_ok=True);target=STATE/'latest-start.json';temp=STATE/('state-'+uuid.uuid4().hex+'.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,target)
   print(json.dumps(result,ensure_ascii=False),flush=True)
  if acquired:kernel.ReleaseMutex(mutex)
  kernel.CloseHandle(mutex)
if __name__=='__main__':main()
