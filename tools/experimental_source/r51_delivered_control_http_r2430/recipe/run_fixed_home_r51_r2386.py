"""Fixed R51 server operation through the pinned channel; no raw log readback."""
from pathlib import Path
import base64, importlib.util, json, subprocess, sys

R=Path('D:/Project/Zhumadian')
D=R/'Document/Deployment/public_home_same_window_r51_20261112'
PIN='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'

REMOTE_CODE=r'''
from pathlib import Path
import base64,contextlib,hashlib,importlib.util,json,os,runpy,socket,subprocess,sys,traceback
root=Path('C:/FTP_Root/Zhumadian/Zhumadian_Home_Same_Window_20261112_R51')
app=Path('C:/inetpub/wwwroot/Zhumadian/Application')
mode='__MODE__';pin='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
assert socket.gethostname().casefold()=='izcdi578349jcez'
assert hashlib.sha256((root/'prepared-manifest.json').read_bytes()).hexdigest()==pin
manifest=json.loads((root/'prepared-manifest.json').read_bytes())
for name,row in manifest['files'].items():
 assert (root/name).stat().st_size==row['bytes']and hashlib.sha256((root/name).read_bytes()).hexdigest()==row['sha256']
def write_new(path,value):
 with path.open('x',encoding='utf-8')as f:json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
if mode in ('prepare','check'):
 result_path=root/(mode+'-scoped-result.json');assert not result_path.exists()
 exitcode=0;error=None
 with(root/(mode+'.private.log')).open('x',encoding='utf-8')as log:
  with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
   try:
    sys.argv=[str(root/'public_home_r51_controller.py'),mode,'--scope-sha256',pin]
    runpy.run_path(sys.argv[0],run_name='__main__')
   except BaseException as e:
    exitcode=1;error=type(e).__name__;traceback.print_exc()
 value={'passed':exitcode==0,'mode':mode,'safeErrorType':error,'scopeSHA256':pin,'actualReleaseSHA256':hashlib.sha256((app/'release-manifest.json').read_bytes()).hexdigest(),'noServiceChanged':True,'rawLogsNotReturned':True}
 write_new(result_path,value);print(json.dumps(value));raise SystemExit(exitcode)
assert mode in ('apply','recover','rollback')
ops=root/'operations';ops.mkdir(exist_ok=True)
attempt=ops/(mode+'-r2386');assert not attempt.exists(),'NO_REPEAT_OR_UNKNOWN_OPERATION_DIRECTORY'
attempt.mkdir()
scope={'schema':'xnby.durable-original-operation.v1','operation':str(root/'public_home_r51_controller.py'),
 'operationSHA256':manifest['files']['public_home_r51_controller.py']['sha256'],
 'arguments':[mode,'--scope-sha256',pin],
 'controllerScript':str(app/'tools/serve_original_server_release.py'),
 'allowedReleaseSHA256':[manifest['oldReleaseSHA256'],manifest['newReleaseSHA256']],
 'python':str(app/'runtime/python/python.exe')}
scope_path=attempt/'operation-scope.json';write_new(scope_path,scope)
scope_pin=hashlib.sha256(scope_path.read_bytes()).hexdigest()
command=subprocess.list2cmdline([str(app/'runtime/python/python.exe'),'-I','-B',str(root/'durable_original_operation_r2327.py'),str(scope_path),scope_pin])
body=json.dumps({'command':command,'directory':str(app)}).encode()
ps=r"""$ErrorActionPreference='Stop';if([Environment]::MachineName-ine 'iZcdi578349jceZ'){throw 'EXACT_SERVER_REQUIRED'};$cfg=ConvertFrom-Json ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__CONFIG__')));$startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0};$created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$cfg.command;CurrentDirectory=$cfg.directory;ProcessStartupInformation=$startup};[pscustomobject]@{returnValue=[int]$created.ReturnValue;wrapperPID=[int]$created.ProcessId}|ConvertTo-Json -Compress""".replace('__CONFIG__',base64.b64encode(body).decode())
p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16-le')).decode()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
out,err=p.communicate();assert p.returncode==0 and len(out)<8192 and len(err)<8192,'DURABLE_WMI_CREATE_FAILED_NO_RETRY'
created=json.loads(out.decode('utf-8-sig'));assert created['returnValue']==0,'DURABLE_WMI_CREATE_REFUSED_NO_RETRY'
value={'submitted':True,'mode':mode,'wrapperPID':created['wrapperPID'],'operationScopeSHA256':scope_pin,'outsideTransientSSHJob':True,'completionStillPending':True,'noAutomaticRepeat':True}
write_new(attempt/'submission-scoped-result.json',value);print(json.dumps(value))
'''


def main():
    assert len(sys.argv)==2 and sys.argv[1]in ('prepare','check','apply','recover','rollback')
    mode=sys.argv[1]
    spec=importlib.util.spec_from_file_location('r51_operation_channel',R/'Application/tools/remote_publish/zhumadian_ssh_channel.py')
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);assert c.inspect()['ready']
    p=subprocess.Popen([str(c.SSH),'-F',str(c.PRIVATE_ROOT/c.CONFIG_NAME),'-T',c.ALIAS,
      r'C:\inetpub\wwwroot\Zhumadian\Application\runtime\python\python.exe -I -B -'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    body=REMOTE_CODE.replace('__MODE__',mode).encode('ascii');first=True
    while True:
        try:out,err=p.communicate(body if first else None,timeout=15);break
        except subprocess.TimeoutExpired:
            first=False;body=b''
            print(json.dumps({'sameActualSSHOperationHandleLive':p.poll()is None,'mode':mode,'noRepeat':True}),flush=True)
    assert len(out)<=32768 and len(err)<=32768,'BOUNDED_SSH_RESULT_REQUIRED'
    try:value=json.loads(out.decode('utf-8-sig'))
    except Exception:value={'passed':False,'mode':mode,'stdoutBytes':len(out),'stderrBytes':len(err),'rawOutputsNotReturned':True}
    value['actualSSHExitCode']=p.returncode
    with(D/('server-'+mode+'-submission-r2386.json')).open('x',encoding='utf-8')as f:json.dump(value,f,indent=2)
    print(json.dumps(value));raise SystemExit(0 if p.returncode==0 and (value.get('passed')or value.get('submitted'))else 1)


if __name__=='__main__':main()
