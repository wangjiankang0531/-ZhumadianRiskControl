from pathlib import Path
import json,subprocess,hashlib,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/original_task_attachment_candidate_r250_20261103'
C=R/'work/event_delivery_consistency_20261030/full-controller-r163';A=R/'_g/Application'
assert not(C/'prepared-r121').exists()and not(C/'r121').exists()
scope=json.loads((D/'preparation.json').read_bytes())
for name,pin in scope['sources'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r121'],['configure_owned_parallel_gateway_r250.py'],['prepare_production_history_runtime_r250.py'],['prepare_personal_workflow_frontend_r250.py']]
results=[]
for args in steps:
 p=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 if p.returncode:
  (D/'preparation-failure.json').write_text(json.dumps({'step':args[0],'exitCode':p.returncode,'type':'PREPARATION_REFUSED_MANUAL_INSPECTION_REQUIRED'},indent=2)+'\n')
  raise RuntimeError('SCOPED_FIXTURE_PREPARATION_REFUSED:'+args[0])
 results.append({'step':args[0],'result':json.loads(p.stdout)})
(D/'prepared-result.json').write_text(json.dumps({'onlyOwnedG':True,'steps':results,'publicFormalOrDesktopChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r121','candidateCompiledFrontendFiles':341,'normalRunAndExactRestoreStillRequired':True}))
