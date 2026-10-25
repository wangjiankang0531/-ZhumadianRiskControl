from pathlib import Path
import argparse,datetime,json,subprocess,sys,time
from original_server_windows_job import OwnedWindowsJob
parser=argparse.ArgumentParser(description='Own synthetic Python child Job cleanup; no original application or database.')
parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
out=args.output.resolve();assert not out.exists();out.mkdir(parents=True)
p=subprocess.Popen([sys.executable,'-B','-c','import time; print("OWN_JOB_FIXTURE_READY",flush=True); time.sleep(30); print("NATURAL_COMPLETION",flush=True)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
job=None
try:
 job=OwnedWindowsJob(p);assert p.stdout.readline().strip()==b'OWN_JOB_FIXTURE_READY';assert p.poll() is None
 flags=job.limit_flags;started=time.monotonic();job.close();job=None;code=p.wait(timeout=5);remaining=p.stdout.read();elapsed=time.monotonic()-started;assert elapsed<5 and b'NATURAL_COMPLETION' not in remaining
 receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'ownedFixturePID':p.pid,'jobLimitFlags':flags,'jobClosureCollectedOwnChild':True,'fixtureExitCode':code,'naturalCompletionObserved':False,'forcedStopElapsedSeconds':elapsed,'originalBackendStarted':False,'originalReaderStarted':False,'otherProcessesTargeted':False,'priorFixtureAssumptionCorrected':'Job closure can terminate an owned process with exit 0; do not equate that with normal shutdown.'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
finally:
 if job:job.close()
 if p.poll() is None:p.kill();p.wait(timeout=5)
