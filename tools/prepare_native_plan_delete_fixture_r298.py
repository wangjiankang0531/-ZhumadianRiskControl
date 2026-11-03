from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_delete_roundtrip_r297_20261103';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(C/'prepared-r133').exists()and not(C/'r133').exists()
preparation=J(D/'preparation-r297.json')
for name,pin in preparation['sourcePins'].items():assert sha(T/name)==pin
p=T/'verify_native_plan_delete_r297_20261103.mjs';s=p.read_text(encoding='utf-8');needle='deleteTargetId=deletePage.records[0].id;';assert s.count(needle)==1
p.write_text(s.replace(needle,'deleteTargetId=String(deletePage.records[0].id);'),encoding='utf-8',newline='\n')
r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
preparation['sourcePins'][p.name]=sha(p);preparation['deletionIdentityComparedAsString']=True
(D/'preparation-r297.json').write_text(json.dumps(preparation,indent=2)+'\n',encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r133'],
 ['prepare_production_history_runtime_r297.py'],['mapper_product_patch_r297.py','prepare','--attempt','r133'],
 ['mapper_observation_support_r297.py','prepare','--attempt','r133'],['prepare_personal_workflow_frontend_r297.py']]
results=[]
for args in steps:
    completed=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if completed.returncode:
        (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':completed.returncode},indent=2)+'\n',encoding='utf-8')
        raise RuntimeError('OWN_NATIVE_DELETE_FIXTURE_PREPARATION_REFUSED:'+args[0])
    results.append({'step':args[0],'result':json.loads(completed.stdout)})
(D/'prepared-result-r298.json').write_text(json.dumps({'prepared':True,'attempt':'r133','steps':results,
 'onlyOwnSyntheticConfigurationAndData':True,'actualProductParameterAndFinalUpdaterSource':True,
 'newPublicOrFormalOrDesktopChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r133','normalRoleCases':14,'onlyOwnFixtureCodeAndFakeConfiguration':True,'servicesStarted':False}))
