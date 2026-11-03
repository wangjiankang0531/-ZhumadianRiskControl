from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools')
def save(n,s):
 p=T/n;assert not p.exists(),n
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
def swap(s,a,b):
 assert s.count(a)==1,(a[:90],s.count(a));return s.replace(a,b)
mapper=(T/'plan_mapper_patch_r223.py').read_text(encoding='utf-8').replace('r223','r226').replace('r111','r113').replace('r112','r114').replace('subprocess,zipfile','subprocess,zipfile,importlib.util')
mapper=swap(mapper,"old={n:(A/n).read_bytes()for n in ['payload-manifest.json','release-manifest.json']}","old={n:(A/n).read_bytes()for n in ['payload-manifest.json','release-manifest.json','tools/original_public_test_update.py']}")
anchor="changed={target:raw,'payload-manifest.json':encode(payload)};release['payloadManifestSHA256']=digest(changed['payload-manifest.json']);changed['release-manifest.json']=encode(release)"
replacement="""updater=R/'Application/tools/original_public_test_update_r37_plan_exercise_r225.py'
 assert J(R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103/descriptor-gates.json')['passed']
 assert sha(updater)==J(R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103/updater-source-preparation.json')['updaterSHA256']
 spec=importlib.util.spec_from_file_location('declared_plan_updater',updater);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 release[module.R37_PLAN_FIELD]=module.R37_PLAN_CONTRACT
 changed={target:raw,'payload-manifest.json':encode(payload),'tools/original_public_test_update.py':updater.read_bytes()}
 release['controllerFiles']['tools/original_public_test_update.py']=digest(changed['tools/original_public_test_update.py'])
 release['payloadManifestSHA256']=digest(changed['payload-manifest.json']);changed['release-manifest.json']=encode(release)"""
mapper=swap(mapper,anchor,replacement)
mapper=swap(mapper,"ready['releaseSHA256']=sha(A/'release-manifest.json');", "ready['updaterSHA256']=sha(A/'tools/original_public_test_update.py');ready['releaseSHA256']=sha(A/'release-manifest.json');")
mapper=mapper.replace("'onlyOwnCodeAndManifestPaths':3","'onlyOwnCodeAndManifestPaths':4").replace("'onlyOriginalPlanXMLAndTwoManifestsRestored'","'onlyOriginalPlanXMLUpdaterAndTwoManifestsRestored'")
save('plan_mapper_patch_r226.py',mapper)
dictionary=(T/'OwnPlanDictionaryR222.java').read_text(encoding='utf-8').replace('OwnPlanDictionaryR222','OwnPlanDictionaryR226')
anchor='   ensureKind(c,18502,"exerciseTypeData","OWN_EXERCISE_TYPE_R222");'
dictionary=swap(dictionary,anchor,anchor+'\n   ensureKind(c,18503,"goodsTypeData","OWN_GOODS_TYPE_R226");\n   ensureKind(c,18504,"inspectionCategory","OWN_INSPECTION_CATEGORY_R226");')
save('OwnPlanDictionaryR226.java',dictionary)
save('verify_native_plan_exercise_r226_20261103.mjs',(T/'verify_native_plan_exercise_r223_20261103.mjs').read_text(encoding='utf-8'))
host=(T/'verify_full_controller_plan_exercise_r223_20261103.py').read_text(encoding='utf-8').replace('r223','r226').replace('r111','r113').replace('r112','r114').replace('OwnPlanDictionaryR222','OwnPlanDictionaryR226')
anchor="history_scope=read(prepared_base/'history-runtime-scope.json');assert history_scope['onlyOwnedSyntheticG']"
host=swap(host,anchor,anchor+"\nplan_mapper_scope=read(prepared_base/'plan-mapper-scope.json');assert plan_mapper_scope['onlyOwnedStoppedSyntheticFixture']")
host=swap(host,"if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']","if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==plan_mapper_scope['newFiles'].get(n,pin['sha256'])")
anchor="        checks['productionNativeServiceGateInstalled']=True"
host=swap(host,anchor,anchor+"\n        checks['exactDeclaredOriginalPlanXMLRuntimePinsPassed']=m.plan_mapper_ready(app,row)is not None\n        assert checks['exactDeclaredOriginalPlanXMLRuntimePinsPassed']")
save('verify_full_controller_plan_exercise_r226_20261103.py',host)
for mode,old_attempt,new_attempt in [('baseline','r111','r113'),('candidate','r112','r114')]:
 for base in ['prepare_personal_workflow_frontend','restore_personal_workflow_frontend','prepare_production_history_runtime','restore_production_history_runtime']:
  old=base+'_r223_'+mode+'.py';new=base+'_r226_'+mode+'.py'
  s=(T/old).read_text(encoding='utf-8').replace('r223','r226').replace(old_attempt,new_attempt)
  if mode=='candidate'and base=='prepare_personal_workflow_frontend':s=s.replace('plan-exercise-retained-r221','plan-exercise-retained-r224')
  save(new,s)
 s=(T/('run_plan_exercise_r223_'+mode+'_20261103.py')).read_text(encoding='utf-8').replace('r223','r226').replace(old_attempt,new_attempt)
 save('run_plan_exercise_r226_'+mode+'_20261103.py',s)
print(json.dumps({'prepared':True,'frontBaselineWithExactDeclaredMapper':'r113','fourteenSourceFrontendAndMapperCandidate':'r114','legacyChecksKeptAndNewDescriptorRequired':True,'previousFailuresPreserved':True,'newRunNotStarted':True}))
