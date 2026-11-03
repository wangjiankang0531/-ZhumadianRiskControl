from pathlib import Path
import argparse,ctypes,hashlib,importlib.util,json,os,subprocess,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline','candidate']);o=p.parse_args()
memory=(ctypes.c_ulonglong*8)();memory[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>1536*1024**2,'ISOLATED_COMPONENT_TEST_REQUIRES_1536MIB_AVAILABLE'
W=R/'work/plan-resource-cancel-r375';out=W/o.variant;assert not out.exists()
source=V/'verify_resource_cancel_component_r375.mjs'
if o.variant=='candidate':assert json.loads((W/'baseline/result.json').read_bytes())['actualUnhandledRejections']==6
spec=importlib.util.spec_from_file_location('own_component_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
env={k:v for k,v in os.environ.items()if k not in ['NODE_OPTIONS','BROWSER']};env['NODE_OPTIONS']='--max-old-space-size=256';env['BROWSER']='none'
W.mkdir(exist_ok=True);log=W/(o.variant+'-node.private.log');assert not log.exists()
with log.open('wb')as f:
    process=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(source),o.variant],stdout=f,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(process)
    print(json.dumps({'headlessComponentStarted':True,'variant':o.variant,'pid':process.pid,'memoryAvailableGiBBefore':round(memory[2]/1024**3,3),'nodeHeapLimitMiB':256,'noBackendOrDesktop':True}),flush=True)
    while process.poll()is None:
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:print('OWN_COMPONENT_TEST_STILL_LIVE_NO_FORCE_OR_RESTART',flush=True)
    while job.active_processes():time.sleep(.1)
    job.close()
proof={'nodeExitCode':process.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'componentOnlyNotNormalRoleOrSixComponents':True}
(W/(o.variant+'-outer-terminal.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
assert process.returncode==0,'OWN_COMPONENT_TEST_FAILED_SEE_SCOPED_FAILURE'
result=json.loads((out/'result.json').read_bytes());assert result['passed']and len(result['cases'])==9 and json.loads((out/'terminal.json').read_bytes())['chromeExitCode']==0
print(json.dumps({'passed':True,'variant':o.variant,'cases':9,'actualUnhandledRejections':result['actualUnhandledRejections'],'actualDescendantsNormalZero':True,'sixComponentAndNormalRoleNotClaimed':True}),flush=True)
