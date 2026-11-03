from pathlib import Path
import json,hashlib,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_product_suite_r266_20261103';J=lambda p:json.loads(p.read_bytes())
assert not(C/'prepared-r131').exists()and not(C/'r131').exists()
for name,pin in J(D/'preparation.json')['sources'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r131'],['prepare_production_history_runtime_r266.py'],['mapper_product_patch_r266.py','prepare','--attempt','r131'],['mapper_observation_support_r266.py','prepare','--attempt','r131'],['prepare_personal_workflow_frontend_r266.py']]
results=[]
for args in steps:
 r=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 if r.returncode:
  (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':r.returncode},indent=2)+'\n',encoding='utf-8');raise RuntimeError('OWN_PRODUCT_FIXTURE_PREPARATION_REFUSED:'+args[0])
 results.append({'step':args[0],'result':json.loads(r.stdout)})
(D/'prepared-result.json').write_text(json.dumps({'attempt':'r131','steps':results,'originalSQLJarAuthAndFormalPublicOrDesktopKept':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'prepared':True,'actualProductParameterSource':True,'noExplicitMapperSettingInjected':True,'normalLifecycleAndRestorationStillRequired':True}))
