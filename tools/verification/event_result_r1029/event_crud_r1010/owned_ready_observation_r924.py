"""Retain an observed owned ready pointer and retry only its identity query timeout.

This is a test-harness adapter. It never replaces the original identity query,
starts a process, infers success from timeout, or edits production lifecycle code.
"""
from pathlib import Path
import hashlib,json,subprocess

def observe_ready(runtime,app,pin,record,persist_observation,*,gateway_port):
 app=Path(app).absolute();pointer=app/'UserData/OriginalServer/current-run.json';process=record['process']
 def read():
  raw=pointer.read_bytes();assert len(raw)<=1024**2,'BOUNDED_OBSERVED_READY_REQUIRED'
  row=json.loads(raw);assert row.get('ready')is True and row.get('controllerPID')==process.pid,'EXACT_LIVE_OWN_READY_OBSERVATION_REQUIRED'
  assert row.get('gatewayPort')==gateway_port and Path(row['run']).absolute().parent==app/'UserData/OriginalServer/runs','EXACT_OBSERVED_OWN_RUN_AND_PORT'
  assert all(k in row for k in ['schema','ownerId','releaseId','startedAt','children']),'COMPLETE_OBSERVED_READY_IDENTITY'
  return raw,row
 assert process.poll()is None,'ORIGINAL_HANDLE_MUST_BE_LIVE'
 raw,row=read();record['observedReady']=row;record['observedReadySHA256']=hashlib.sha256(raw).hexdigest()
 persist_observation({'pointerSHA256':record['observedReadySHA256'],'row':row,'identityValidationCompleted':False})
 for attempt in range(3):
  assert process.poll()is None,'ORIGINAL_HANDLE_TERMINAL_NO_RETRY'
  current,_=read();assert current==raw,'READY_POINTER_DRIFT_NO_IDENTITY_RETRY'
  try:
   verified=runtime.owned_ready(app,pin,gateway_port=gateway_port)
  except subprocess.TimeoutExpired:
   if attempt==2:raise
   assert process.poll()is None,'ORIGINAL_HANDLE_TERMINAL_NO_RETRY'
   current,_=read();assert current==raw,'READY_POINTER_DRIFT_NO_IDENTITY_RETRY'
   print('SAME_OWN_CONTROLLER_IDENTITY_QUERY_TIMEOUT_REOBSERVING_NO_RESTART',flush=True)
   continue
  assert pointer.read_bytes()==raw and verified==row and process.poll()is None,'OBSERVED_AND_VERIFIED_OWN_READY_MUST_MATCH'
  persist_observation({'pointerSHA256':record['observedReadySHA256'],'row':row,'identityValidationCompleted':True})
  return verified
 raise AssertionError('UNREACHABLE_READY_RETRY_STATE')
