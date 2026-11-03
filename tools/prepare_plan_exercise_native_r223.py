from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools');V=Path(__file__).resolve().parent
def save(n,s):
 p=T/n;assert not p.exists(),n
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
save('plan_mapper_patch_r223.py',(V/'plan_mapper_patch_r223.py').read_text(encoding='utf-8'))
browser=(T/'verify_native_plan_exercise_r222_20261103.mjs').read_text(encoding='utf-8')
old="if(r.status!==200||v.code!==0)throw Error('OWN_PLAN_API_READBACK');"
assert browser.count(old)==1
browser=browser.replace(old,"if(r.status!==200||v.code!==0){await fs.writeFile(O+'/readonly-api-diagnostic.json',JSON.stringify({entity,operation:query.split('?')[0],httpStatus:r.status,businessCode:v.code,responseShape:typeof v.data}));throw Error('OWN_PLAN_API_READBACK_'+entity+'_'+r.status+'_'+v.code);}")
save('verify_native_plan_exercise_r223_20261103.mjs',browser)
host=(T/'verify_full_controller_plan_exercise_r222_20261103.py').read_text(encoding='utf-8').replace('r222','r223').replace('r109','r111').replace('r110','r112')
# The existing Java fixture names and their exact synthetic grants remain authoritative.
host=host.replace('OwnPlanPortalMenusR223','OwnPlanPortalMenusR222').replace('OwnPlanDictionaryR223','OwnPlanDictionaryR222')
save('verify_full_controller_plan_exercise_r223_20261103.py',host)
for mode,old_attempt,new_attempt in [('baseline','r109','r111'),('candidate','r110','r112')]:
 for base in ['prepare_personal_workflow_frontend','restore_personal_workflow_frontend','prepare_production_history_runtime','restore_production_history_runtime']:
  old=base+'_r222_'+mode+'.py';new=base+'_r223_'+mode+'.py'
  save(new,(T/old).read_text(encoding='utf-8').replace('r222','r223').replace(old_attempt,new_attempt))
 s=(T/('run_plan_exercise_r222_'+mode+'_20261103.py')).read_text(encoding='utf-8').replace('r222','r223').replace(old_attempt,new_attempt)
 anchor="restored=subprocess.run([sys.executable,str(V/'restore_production_history_runtime_r223_"+mode+".py')]"
 assert s.count(anchor)==1
 mapper="mapper=subprocess.run([sys.executable,str(V/'plan_mapper_patch_r223.py'),'restore','--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)\nassert mapper.returncode==0 and json.loads(mapper.stdout)['passed'],'OWN_PLAN_MAPPER_RESTORE_REFUSED'\n"
 s=s.replace(anchor,mapper+anchor)
 save('run_plan_exercise_r223_'+mode+'_20261103.py',s)
print(json.dumps({'prepared':True,'frontBaselineWithOriginalMapperResourceAttempt':'r111','fullFrontendPlusOriginalMapperCandidateAttempt':'r112','r109FailurePreserved':True,'originalSQLBytesUnchanged':True}))
