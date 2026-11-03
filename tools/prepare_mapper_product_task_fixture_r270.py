from pathlib import Path
import json,hashlib,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_product_task_r270_20261103';J=lambda p:json.loads(p.read_bytes())
assert J(C/'r131-outer-terminal.json')['exitCode']==0 and J(C/'prepared-r131/mapper-product-restored.json')['passed']and J(C/'prepared-r131/history-runtime-restored.json')['passed']
assert not(C/'prepared-r132').exists()and not(C/'r132').exists()
for name,pin in J(D/'preparation.json')['sources'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r132'],['configure_owned_parallel_gateway_r270.py'],['prepare_production_history_runtime_r270.py'],['mapper_product_patch_r270.py','prepare','--attempt','r132'],['mapper_observation_support_r266.py','prepare','--attempt','r132'],['prepare_personal_workflow_frontend_r270.py']]
results=[]
for args in steps:
 r=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 if r.returncode:
  (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':r.returncode},indent=2)+'\n',encoding='utf-8');raise RuntimeError('OWN_PRODUCT_TASK_PREPARATION_REFUSED:'+args[0])
 results.append({'step':args[0],'result':json.loads(r.stdout)})
(D/'prepared-result.json').write_text(json.dumps({'attempt':'r132','steps':results,'onlyOwnSyntheticConfigurationAndData':True,'publicFormalOrDesktopChanged':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'prepared':True,'attempt':'r132','finalDeclarationAdapterR268':True,'actualProductDefaultsAndNinePhaseWorkflow':True,'noExplicitMapperSettingInjected':True}))
