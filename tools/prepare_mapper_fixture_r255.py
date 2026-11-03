from pathlib import Path
import argparse,json,hashlib,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_registration_r255_20261103'
p=argparse.ArgumentParser();p.add_argument('mode',choices=['baseline','candidate']);o=p.parse_args();attempt='r123'if o.mode=='baseline'else'r124'
assert not(C/attempt).exists()and not(C/('prepared-'+attempt)).exists()
scope=json.loads((D/'preparation.json').read_bytes())
for name,pin in scope['sources'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt',attempt],['prepare_production_history_runtime_r255_'+o.mode+'.py'],['mapper_observation_support_r255.py','prepare','--attempt',attempt]]
if o.mode=='candidate':steps.append(['prepare_personal_workflow_frontend_r255_candidate.py'])
results=[]
for args in steps:
 r=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 if r.returncode:
  (D/('prepare-'+o.mode+'-failure.json')).write_text(json.dumps({'step':args[0],'exitCode':r.returncode,'diagnosticErrorTypesOnly':True},indent=2)+'\n',encoding='utf-8');raise RuntimeError('OWN_MAPPER_PREPARATION_REFUSED:'+args[0])
 results.append({'step':args[0],'result':json.loads(r.stdout)})
(D/('prepared-'+o.mode+'.json')).write_text(json.dumps({'attempt':attempt,'steps':results,'onlyOwnSyntheticFixture':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'prepared':True,'attempt':attempt,'mode':o.mode,'candidateMapperSetting':o.mode=='candidate','publicOrFormalOrDesktopChanged':False}))
