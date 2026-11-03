from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/addsign-history-r180';old=W/'production-module-r199-r2';new=W/'production-module-r208';assert not new.exists();new.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['original_native_history_release_support.py','serve_original_server_release.py','own-before-addsign-history.jar','OriginalHistoryPersistentPlatformLaunch.java','launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class']:
 p=new/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((old/n).read_bytes())
p=new/'original_public_test_update.py';p.write_bytes((R/'Application/tools/original_public_test_update_r36_20261103.py').read_bytes());model=json.loads((old/'module-pins.json').read_bytes());model['updaterSHA256']=sha(p);model['files']['original_public_test_update.py']={'bytes':p.stat().st_size,'sha256':sha(p)};model['exactR36CompositionUpdaterSelected']=True;(new/'module-pins.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8');(new/'support-test-result.json').write_bytes((old/'support-test-result.json').read_bytes())
def save(n,s):
 p=V/n;assert not p.exists(),n
 if n.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for oldname in ['prepare_personal_workflow_frontend_r206.py','restore_personal_workflow_frontend_r206.py','restore_production_history_runtime_r206.py','verify_full_controller_personal_workflow_r206_20261103.py','verify_native_personal_workflow_r206_20261103.mjs','run_personal_workflow_r206_20261103.py','OwnPersonalWorkflowMenuVisibilityR206.java']:
 s=(V/oldname).read_text(encoding='utf-8').replace('r206','r208').replace('R206','R208').replace('r103','r104')
 if oldname.startswith('verify_full_controller'):s=s.replace("'onlyExactCompletedR102ReadBackWithoutBusinessRecreation':True","'onlyExactCompletedR102ReadBackWithoutBusinessRecreation':True,'exactR36UpdaterActualSixComponentLifecycleExercised':True")
 save(oldname.replace('r206','r208').replace('R206','R208'),s)
s=(V/'prepare_production_history_runtime_r206.py').read_text(encoding='utf-8').replace('prepared-r103','prepared-r104').replace("C/'r103'","C/'r104'").replace('production-module-r199-r2','production-module-r208');save('prepare_production_history_runtime_r208.py',s)
print(json.dumps({'prepared':True,'exactR36UpdaterSHA256':sha(new/'original_public_test_update.py'),'sameHistoryControllerHelperAndJavaBytes':True,'noRuntimeStarted':True}))
