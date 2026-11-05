"""Gate the actual-apply harness inside a non-terminating 4-GiB Job."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';W=R/'work/ua1049'
SOURCE=V/'run_real_apply_bridge_r1049.py'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert digest(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
    assert not(W/'parent-started.json').exists(),'NO_DUPLICATE_OWN_ATTEMPT'
    budget=load('real_apply_outer_budget_r1049',R/'Application/tools/bounded_build_job_r671.py')
    job_module=load('real_apply_nonterminating_job_r1049',G/'tools/original_server_windows_job.py')
    snapshot=budget.memory_snapshot();assert min(snapshot['availablePhysicalBytes'],snapshot['availableCommitBytes'])>7*1024**3
    gate=b'XNBY_REAL_APPLY_R1049\n'
    bootstrap="import sys,runpy; assert sys.stdin.buffer.readline(128)==b'XNBY_REAL_APPLY_R1049\\n','OWN_GATE_REQUIRED'; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
    (W/'parent-started.json').write_text(json.dumps({'harnessSHA256':digest(SOURCE),'terminateOrKillOnCloseUsed':False})+'\n',encoding='utf-8')
    with(W/'run-harness.private.log').open('xb')as output:
        process=subprocess.Popen([sys.executable,'-I','-B','-c',bootstrap,str(SOURCE),'--run'],stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    job=job_module.OwnedWindowsJob(process)
    bounded=budget.BoundedBuildJob(job,4*1024**3)
    process.stdin.write(gate);process.stdin.flush();process.stdin.close()
    print(json.dumps({'harnessPID':process.pid,'actualOwnedJobAttachedBeforeGate':True,'memoryLimitBytes':4*1024**3}),flush=True)
    while process.poll()is None:
        print(json.dumps({'harnessHandleLive':True,'metrics':bounded.metrics()}),flush=True)
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:pass
    while job.active_processes()!=0:
        print('ACTUAL_JOB_DESCENDANTS_STILL_LIVE_NO_CLOSE_NO_RESTART',flush=True);time.sleep(5)
    final={'harnessExitCode':process.returncode,'actualJobDescendantsZero':True,'budget':bounded.metrics(),'forceTerminationUsed':False}
    job.close()
    (W/'actual-parent-terminal-r1049.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(final),flush=True)
    raise SystemExit(process.returncode)

if __name__=='__main__':main()
