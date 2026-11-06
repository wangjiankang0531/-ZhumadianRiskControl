"""Launch only the frozen new original-statistics read-only fixture, never an old attempt."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;H=V/'hazard_transaction_r1214';D=R/'Document/Deployment/hazard_attachment_transaction_r1214_20261106'
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(R/'work/ht1214').exists()and not(R/'work/hazard-transaction-probe-r1214').exists()
 assert not(D/'parent-terminal-r1215.json').exists()
 pins=json.loads((H/'source-pins-r1214.json').read_bytes())
 assert (H/'run_hazard_runtime_r1214.py').is_file(),'EXPLICIT_FROZEN_PARENT_SCRIPT_REQUIRED'
 for p,h in pins['files'].items():assert sha(Path(p))==h
 callback=R/'work/original-manager-full-lifecycle-r609/attachment-r1072/resume-r1095/normal-restart/callback-normal-restart-journal.private.properties'
 assert sha(callback)=='b876d9aeb58fedcfeb1d17e5a718a4c9bc1f5d3c6826f06b00ea020ef3687c58'
 jobs=load('hazard_parent_jobs',R/'_g/Application/tools/original_server_windows_job.py');budget=load('hazard_parent_budget',R/'Application/tools/bounded_build_job_r671.py')
 cap=6*1024**3;snap=budget.memory_snapshot();assert snap['availablePhysicalBytes']>9*1024**3 and snap['availableCommitBytes']>9*1024**3
 gate="import sys,runpy;assert sys.stdin.buffer.readline()==b'OWN_HAZARD_R1215\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
 log=D/'parent-r1215.private.log';assert not log.exists()
 with log.open('xb')as out:p=subprocess.Popen([sys.executable,'-I','-B','-c',gate,str(H/'run_hazard_runtime_r1214.py'),'--run'],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);bound=budget.BoundedBuildJob(job,cap)
 print(json.dumps({'pid':p.pid,'actualJobAssignedBeforeGate':True,'budgetBytes':cap,'memoryBefore':snap}),flush=True)
 p.stdin.write(b'OWN_HAZARD_R1215\n');p.stdin.flush();p.stdin.close()
 while p.poll()is None:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameParentHandleLive':True,'metrics':bound.metrics()}),flush=True)
 while job.active_processes():time.sleep(.2)
 result={'exitCode':p.returncode,'actualJobDescendantsZero':True,'metrics':bound.metrics(),'callbackJournalUnchanged':sha(callback)=='b876d9aeb58fedcfeb1d17e5a718a4c9bc1f5d3c6826f06b00ea020ef3687c58','forceTerminationUsed':False};job.close()
 (D/'parent-terminal-r1215.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True)
 assert p.returncode==0,'ORIGINAL_RUNTIME_ATTEMPT_FAILED_INSPECT_CLOSED_STATE_DO_NOT_RESTART'
 assert result['callbackJournalUnchanged']
if __name__=='__main__':main()
