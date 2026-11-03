from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';A=R/'_g/Application';D=R/'Document/Deployment/original_plan_exercise_fixture_identity_r243_20261103'
assert not D.exists()and not(C/'r117').exists()and not(C/'prepared-r117').exists()and not(C/'r118').exists()and not(C/'prepared-r118').exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'release-manifest.json')==J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256']
assert J(C/'r115-outer-terminal.json')['actualDescendantsZeroBeforeClose']and J(C/'prepared-r115/history-runtime-restored.json')['passed']
seed=(T/'OwnPlanPortalMenusR222.java').read_text(encoding='utf-8');assert 'return "a531"+String.format("%028x",n);'in seed and 'id(100+n)'in seed and '"own_operator_a"'in seed
names=['verify_full_controller_plan_exercise_r227_20261103.py','verify_native_plan_exercise_r227_20261103.mjs','plan_mapper_patch_r227.py']
for mode in ['baseline','candidate']:
 names += [f'{verb}_personal_workflow_frontend_r227_{mode}.py'for verb in ['prepare','restore']]
 names += [f'{verb}_production_history_runtime_r227_{mode}.py'for verb in ['prepare','restore']]
 names += [f'run_plan_exercise_r227_{mode}_20261103.py']
sourcePins={};outputPins={};hostBefore=(T/names[0]).read_text(encoding='utf-8');hostAfter=None
for name in names:
 original=(T/name).read_text(encoding='utf-8');sourcePins[name]=sha(T/name)
 if name==names[0]:
  needle="own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r116/own-normal-login.private.json');assert own['credentialsSynthetic']"
  assert original.count(needle)==1
  replacement="""seed_text=(R/'Application/tools/OwnPlanPortalMenusR222.java').read_text(encoding='utf-8')
        assert 'return "a531"+String.format("%028x",n);' in seed_text and 'id(100+n)' in seed_text and '"own_operator_a"' in seed_text
        own={'credentialsSynthetic':True,'accounts':{'own_operator_a':{'id':'a531'+format(100,'028x')}}}"""
  original=original.replace(needle,replacement)
 text=original.replace('r227','r243').replace('r115','r117').replace('r116','r118')
 dest=T/name.replace('r227','r243');assert not dest.exists();dest.write_text(text,encoding='utf-8');outputPins[dest.name]=sha(dest)
 if dest.suffix=='.py':ast.parse(text)
 else:
  q=subprocess.run(['node','--check',str(dest)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert q.returncode==0
 if name==names[0]:hostAfter=text
assert hostAfter and 'own-normal-login.private.json'not in hostAfter
otherChanges=hostBefore.replace("own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r116/own-normal-login.private.json');assert own['credentialsSynthetic']",replacement).replace('r227','r243').replace('r115','r117').replace('r116','r118');assert hostAfter==otherChanges
D.mkdir(parents=True);result={'prepared':True,'sourcePins':sourcePins,'outputPins':outputPins,'onlyActualHostBehaviorChange':'Derive exact synthetic normal user ID from existing compiled seeder contract instead of absent historical credentials JSON.','syntheticSeederSHA256':sha(T/'OwnPlanPortalMenusR222.java'),'syntheticExpectedUserID':'a531'+format(100,'028x'),'normalLoginAndCurrentUserExactIdentityAssertionKept':True,'businessAccountRowsPasswordsSourceAndProductUnchanged':True,'baselineAttempt':'r117','candidateAttempt':'r118','runStarted':False,'r115PriorFileNotFoundBeforeBrowserAndExactRestorePreserved':True}
(D/'preparation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k not in['sourcePins','outputPins']}))
