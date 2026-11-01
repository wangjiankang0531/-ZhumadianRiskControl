"""Compile and run an unchanged-original special-work SQL characterization on owned temporary tables."""
from pathlib import Path
import argparse,ctypes,datetime,hashlib,json,subprocess,sys
from ctypes import wintypes
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_server_windows_job import OwnedWindowsJob
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application');O=R/'Document/Deployment/original_work_start_sql_20261026';W=R/'work/original_work_start_sql_20261026'
SOURCE=R/'Application/tools/java/OriginalWorkStartSqlProbe.java'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,j):
 p=Path(p);assert not p.exists(),'FRESH_EVIDENCE_REQUIRED';p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def alive_image(pid,expected):
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x1000,False,pid);assert h,'LIVE_OWNED_PROCESS_REQUIRED'
 try:
  code=wintypes.DWORD();assert k.GetExitCodeProcess(h,ctypes.byref(code)) and code.value==259,'OWNED_PROCESS_MUST_BE_RUNNING';buf=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(buf));assert k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size));assert Path(buf.value).resolve()==Path(expected).resolve(),'OWNED_IMAGE_REQUIRED'
 finally:k.CloseHandle(h)
def inputs():
 j=load(O/'prepared-inputs.private.json')
 for p,pin in j['inputPins'].items():assert sha(p)==pin['SHA256'],'PINNED_ORIGINAL_DEPENDENCY_DRIFT'
 assert sha(j['java'])==j['javaSHA256']
 state=load(Q/'UserData/OriginalServer/current-run.json');assert state['ready'] and state['persistent'] and state['controllerPID']==j['controllerPID'] and state['children']['business']==j['businessPID'] and state['databaseUUID']==j['databaseUUID'],'OWNED_CURRENT_RUN_REQUIRED';assert sha(Q/'release-manifest.json')==j['localReleaseSHA256']
 for pid,image in [(state['controllerPID'],Q/'runtime/python/python.exe'),(state['children']['mysql'],Q/'runtime/mysql/bin/mysqld.exe'),(state['children']['business'],j['java'])]:alive_image(pid,image)
 return j,state

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compile',action='store_true');p.add_argument('--execute',action='store_true');p.add_argument('--revision',choices=['r1','r2','r3'],default='r1');a=p.parse_args();suffix='' if a.revision=='r1' else '-'+a.revision;assert a.compile!=a.execute,'EXACTLY_ONE_ACTION_REQUIRED';j,state=inputs();classes=W/('classes'+suffix)
 if a.compile:
  assert not classes.exists(),'FRESH_CLASSES_REQUIRED';classes.mkdir();javac=Path(j['java']).with_name('javac.exe');cmd=[str(javac),'-encoding','UTF-8','-proc:none','-cp',j['classpath'],'-d',str(classes),str(SOURCE)];r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45);(O/('compile'+suffix+'.stdout.log')).write_bytes(r.stdout);(O/('compile'+suffix+'.stderr.log')).write_bytes(r.stderr)
  result={'exitCode':r.returncode,'sourceSHA256':sha(SOURCE),'javacSHA256':sha(javac),'classPins':{str(x.relative_to(classes)):sha(x) for x in classes.rglob('*.class')},'classes':str(classes),'activeApplicationPropertiesSHA256':sha(Path(state['run'])/'b/application.properties'),'compiledAt':datetime.datetime.now().astimezone().isoformat()};write(O/('compiled'+suffix+'.json'),result);print(json.dumps({'compileExitCode':r.returncode,'classCount':len(result['classPins']),'stderr':r.stderr.decode('utf-8',errors='replace')[-1800:],'originalMethodsExecuted':False}));raise SystemExit(r.returncode)
 c=load(O/('compiled'+suffix+'.json'));assert c['exitCode']==0 and sha(SOURCE)==c['sourceSHA256'];assert {str(x.relative_to(classes)):sha(x) for x in classes.rglob('*.class')}==c['classPins'],'COMPILED_CLASS_DRIFT'
 active_config=Path(state['run'])/'b/application.properties';assert sha(active_config)==c['activeApplicationPropertiesSHA256'],'CURRENT_CONFIG_DRIFT';formats=[line.split('=',1)[1] for line in active_config.read_text(encoding='iso-8859-1').splitlines() if line.startswith('mybatis-plus.global-config.db-config.column-format=')];assert formats==['`%s`'],'EXACT_CURRENT_COLUMN_FORMAT_REQUIRED'
 attempt=O/('attempt'+suffix);assert not attempt.exists(),'SINGLE_START_ONLY_NO_UNCHANGED_RETRY';attempt.mkdir();(attempt/'tmp').mkdir();result=attempt/'result.private.json';write(attempt/'plan.json',{'preparedSHA256':sha(O/'prepared-inputs.private.json'),'compiledSHA256':sha(O/('compiled'+suffix+'.json')),'maximumStarts':1,'maximumSeconds':90,'heapMiB':192,'maximumConnections':2,'temporaryTables':11,'originalServiceAndRealMappers':True,'permanentRowsOrSchemaWritesAllowed':False,'authenticationOrSessionAcquisition':False,'currentServicesRestarted':False,'fullCloneReady':False})
 secret=load(Q/'private/server-configuration.json')['seedRootPassword'];cmd=[j['java'],'-Xmx192m','-XX:ActiveProcessorCount=2','-Djava.io.tmpdir='+str(attempt/'tmp'),'-Dlogback.configurationFile='+str(O/'quiet-logback.xml'),'-cp',str(classes)+';'+j['classpath'],'xnby.replica.OriginalWorkStartSqlProbe',str(state['databasePort']),state['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),str(result),formats[0]]
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW);write(attempt/'started.json',{'PID':process.pid,'recordedAt':datetime.datetime.now().astimezone().isoformat()});print(json.dumps({'probePID':process.pid,'maximumSeconds':90}),flush=True);job=None;timeout=False
 try:
  job=OwnedWindowsJob(process)
  try:stdout,stderr=process.communicate(secret.encode(),timeout=90)
  except subprocess.TimeoutExpired:timeout=True;job.close();stdout,stderr=process.communicate(timeout=10)
 finally:
  if job:job.close()
  if process.poll() is None:process.kill();process.wait(timeout=5)
 for label,raw in [('stdout',stdout),('stderr',stderr)]:assert secret.encode() not in raw,'SECRET_OUTPUT_REJECTED';(attempt/(label+'.log')).write_bytes(raw)
 del secret
 outcome={'PID':process.pid,'exitCode':process.returncode,'timedOut':timeout,'resultExists':result.exists(),'sourceAndClassesUnchanged':sha(SOURCE)==c['sourceSHA256'] and {str(x.relative_to(classes)):sha(x) for x in classes.rglob('*.class')}==c['classPins']};write(attempt/'process-result.json',outcome);print(json.dumps({**outcome,'stdoutTail':stdout.decode('utf-8',errors='replace')[-700:],'stderrTail':stderr.decode('utf-8',errors='replace')[-1700:]}),flush=True)
 assert process.returncode==0 and not timeout and outcome['sourceAndClassesUnchanged'],'ORIGINAL_SQL_CHARACTERIZATION_FAILED'
 report=load(result);assert len(report['cases'])==36 and report['permanentRowsAndDDLUnchanged'] and report['temporaryTablesDropped'];print(json.dumps({'cases':36,'originalServiceAndRealMappersExecuted':True,'permanentRowsAndDDLUnchanged':True,'fullCloneReady':False}),flush=True)
if __name__=='__main__':main()