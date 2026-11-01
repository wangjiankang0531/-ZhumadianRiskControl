"""Use real owned Python processes to check Job retention and failure cleanup."""
from pathlib import Path
import argparse, ast, ctypes, hashlib, importlib.util, json, os, re, subprocess, sys, threading, time
from ctypes import wintypes

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r1');args=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
W=R/'work'/('r23-graceful-controller-'+args.revision);assert not W.exists();W.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
job_source=T/'original_server_windows_job_graceful_20261101.py'
controller=T/'serve_original_server_release_r23_graceful_20261101.py'
spec=importlib.util.spec_from_file_location('own_nonterminating_job',job_source)
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
old=(T/'serve_original_server_release_r23_20261101.py').read_text(encoding='utf-8')
new=controller.read_text(encoding='utf-8');tree=ast.parse(new)
node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Child')
namespace={'subprocess':subprocess,'threading':threading,'os':os,'OwnedWindowsJob':j.OwnedWindowsJob}
exec(compile(ast.Module(body=[node],type_ignores=[]),'exact-controller-child','exec'),namespace)
Child=namespace['Child'];python=Path('D:/Zqa20261025/Application/runtime/python/python.exe')
worker='''from pathlib import Path
import sys,time
p=Path(sys.argv[1]);(p/'ready').write_text('ready',encoding='ascii')
end=time.monotonic()+30
while not(p/'stop').exists() and time.monotonic()<end:time.sleep(.02)
if not(p/'stop').exists():sys.exit(2)
(p/'normal-exit').write_text('0',encoding='ascii')
'''
def wait_for(fn,seconds=10):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if fn():return
        time.sleep(.02)
    raise AssertionError('OWN_PROCESS_OBSERVATION_TIMEOUT')
def refused(fn):
    try:fn()
    except RuntimeError:return
    raise AssertionError('LIVE_JOB_CLOSED_OR_FAILURE_NOT_REPORTED')
cases=[]
for label,failure in [('actual-owned-job',False),('job-construction-failure',True)]:
    folder=W/label;folder.mkdir()
    def failed_job(process):raise RuntimeError('OWN_INJECTED_JOB_ASSIGNMENT_FAILURE')
    namespace['OwnedWindowsJob']=failed_job if failure else j.OwnedWindowsJob
    child=Child('fixture',[str(python),'-I','-B','-c',worker,str(folder)],folder,dict(os.environ))
    try:
        wait_for(lambda:(folder/'ready').exists())
        assert child.process.poll()is None
        if failure:
            assert child.job is None and child.job_assignment_failure=='RuntimeError'
            refused(child.require_job)
            assert child.process.poll()is None,'JOB_FAILURE_MUST_NOT_KILL_CHILD'
        else:
            child.require_job();initial_active=child.job.active_processes()
            (folder/'observed-job-count.json').write_text(json.dumps({'activeProcesses':initial_active}),encoding='utf-8')
            assert child.job.limit_flags==0 and initial_active>=1
            refused(child.close_job)
            assert child.process.poll()is None
    finally:
        (folder/'stop').write_text('stop',encoding='ascii')
        while child.process.poll()is None:time.sleep(.02)
        if child.job:
            while child.job.active_processes():time.sleep(.02)
        child.close_job();child.thread.join(timeout=5)
    assert child.process.returncode==0 and(folder/'normal-exit').read_text()=='0'
    assert not child.thread.is_alive()
    cases.append({'case':label,'normalExitCode':0,'noKillIssued':True,'loggingThreadExited':True})

folder=W/'descendant-after-parent-exit';folder.mkdir();descendant=folder/'descendant';descendant.mkdir()
parent='''from pathlib import Path
import subprocess,sys,time,json
p=Path(sys.argv[1]);end=time.monotonic()+30
while not(p/'release-parent').exists() and time.monotonic()<end:time.sleep(.02)
if not(p/'release-parent').exists():sys.exit(3)
child=subprocess.Popen([sys.executable,'-I','-B','-c',sys.argv[2],str(p/'descendant')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
(p/'own-child.json').write_text(json.dumps({'pid':child.pid}),encoding='ascii')
while not(p/'descendant/ready').exists() and time.monotonic()<end:time.sleep(.02)
if not(p/'descendant/ready').exists():sys.exit(4)
'''
process=subprocess.Popen([str(python),'-I','-B','-c',parent,str(folder),worker],stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
job=None;child_handle=None;api=ctypes.WinDLL('kernel32',use_last_error=True)
api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];api.OpenProcess.restype=wintypes.HANDLE
api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];api.WaitForSingleObject.restype=wintypes.DWORD
api.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];api.GetExitCodeProcess.restype=wintypes.BOOL
api.CloseHandle.argtypes=[wintypes.HANDLE];api.CloseHandle.restype=wintypes.BOOL
try:
    job=j.OwnedWindowsJob(process);assert job.limit_flags==0
    (folder/'release-parent').write_text('go',encoding='ascii')
    wait_for(lambda:(descendant/'ready').exists()and process.poll()is not None)
    active_descendants=job.active_processes()
    assert process.returncode==0 and active_descendants>=1
    own_pid=json.loads((folder/'own-child.json').read_bytes())['pid']
    child_handle=api.OpenProcess(0x1000|0x100000,False,own_pid)
    assert child_handle
    refused(job.close)
    assert job.handle is not None and job.active_processes()>=1
finally:
    (folder/'release-parent').write_text('go',encoding='ascii')
    (descendant/'stop').write_text('stop',encoding='ascii')
    while process.poll()is None:time.sleep(.02)
    if job:
        while job.active_processes():time.sleep(.02)
        job.close()
assert process.returncode==0 and(descendant/'normal-exit').read_text()=='0'
assert api.WaitForSingleObject(child_handle,5000)==0
exit_code=wintypes.DWORD();assert api.GetExitCodeProcess(child_handle,ctypes.byref(exit_code))and exit_code.value==0
assert api.CloseHandle(child_handle)
cases.append({'case':'parent-exited-live-descendant-job-retained','parentExitCode':0,'descendantExitCode':0,
              'jobCloseRefusedUntilActualZeroDescendants':True,'noKillIssued':True})
defs=lambda text:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(old),defs(new);assert{k for k in a if a[k]!=b[k]}=={'Child','main'}
assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['kill','terminate']for n in ast.walk(tree))
assert new.count('.require_job()')==6
assert 'while pending_children():'in new and 'child.job.active_processes' in new
proof={'schema':'xnby.r23.graceful-controller-process-checks.v1','allPassed':True,'cases':cases,
       'actualOwnedProgramLaunchesNormalExit':4,'actualWindowsJobAccountingUsed':True,
       'firstLaunchObservedActiveProcesses':json.loads((W/'actual-owned-job/observed-job-count.json').read_bytes())['activeProcesses'],
       'observedActiveDescendantsAfterParentExit':active_descendants,
       'actualChildDefinitionExtractedWithoutReimplementation':True,'allSixMainCallSitesTrackBeforeJobRefusal':True,
       'noDirectKillCallsInController':True,'controllerSHA256':sha(controller),'jobSHA256':sha(job_source),
       'wholeSixComponentControllerActuallyExecuted':False,'integratedIntoR23UpdaterAndBundle':False,
       'privateConfigurationDatabaseOrAccountsRead':False,'publicOrFormalChanged':False}
(W/'result.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
change_path=S/'graceful-control-preparation/source-change-proof.json'
change=json.loads(change_path.read_bytes());change.update(actualTestsPassed=True,actualOwnProgramLaunchesNormalExit=4)
change_path.write_text(json.dumps(change,indent=2),encoding='utf-8')
print(json.dumps(proof))
