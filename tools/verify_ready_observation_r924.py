from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,subprocess,tempfile
V=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('ready_r924',V/'owned_ready_observation_r924.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
results=[]
with tempfile.TemporaryDirectory(prefix='ready-r924-',dir=V)as root:
 app=Path(root)/'Application';p=app/'UserData/OriginalServer/current-run.json';p.parent.mkdir(parents=True)
 row={'schema':'own.test.ready','ready':True,'controllerPID':100,'gatewayPort':23456,'run':str(app/'UserData/OriginalServer/runs/j1'),'ownerId':'own','releaseId':'known','startedAt':'known','children':{}}
 def run(name,actions,expected,change=None):
  p.write_text(json.dumps(row));saved=[];calls=[];state={'live':True}
  process=SimpleNamespace(pid=100,poll=lambda:None if state['live']else 0);record={'process':process}
  def owned_ready(*a,**k):
   action=actions[min(len(calls),len(actions)-1)];calls.append(action)
   if change:change(p,state,len(calls))
   if action=='timeout':raise subprocess.TimeoutExpired('scoped-own-query',20)
   if action=='refuse':raise ValueError('ORIGINAL_IDENTITY_REFUSED')
   return dict(row)
  error=None;value=None
  try:
   value=m.observe_ready(SimpleNamespace(owned_ready=owned_ready),app,'fixed',record,saved.append,gateway_port=23456)
  except (AssertionError,ValueError,subprocess.TimeoutExpired)as caught:error=caught
  if expected=='pass':assert error is None and value==row,error
  else:assert error is not None,'REJECTION_NOT_OBSERVED:'+name
  assert len(calls)<=3 and saved and saved[0]['identityValidationCompleted']is False
  if expected=='pass':assert saved[-1]['identityValidationCompleted']is True
  else:assert not any(x['identityValidationCompleted']for x in saved)
  results.append({'case':name,'passed':True,'identityQueries':len(calls)})
 run('normal-original-validator', ['ok'],'pass')
 run('one-timeout-reobserves-same-handle',['timeout','ok'],'pass')
 run('two-timeouts-reobserves-same-handle',['timeout','timeout','ok'],'pass')
 run('third-timeout-stops-without-success',['timeout'],'reject')
 run('original-identity-refusal-not-retried',['refuse'],'reject')
 run('pointer-drift-refuses-retry',['timeout'],'reject',lambda p,s,n:p.write_text(json.dumps({**row,'ownerId':'foreign'})))
 run('original-handle-exited-refuses-retry',['timeout'],'reject',lambda p,s,n:s.update(live=False))
 run('drift-during-success-refused',['ok'],'reject',lambda p,s,n:p.write_text(json.dumps({**row,'ownerId':'foreign'})))
report={'passed':True,'cases':results,'testHarnessOnly':True,'originalIdentityValidatorNotPatched':True,'processesOrNetworkOrDatabaseUsed':False}
(V/'ready-observation-r924-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
