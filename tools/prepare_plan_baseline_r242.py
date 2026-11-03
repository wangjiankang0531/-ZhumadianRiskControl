from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_plan_exercise_verified_repro_r242_20261103'
assert not D.exists()and not(C/'r115').exists()and not(C/'prepared-r115').exists();assert not(A.parent/'user-manual-protected.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json').read_bytes());assert sha(A/'release-manifest.json')==baseline['releaseSHA256']
names=['prepare_owned_return_serial_r163_20261102.py','prepare_production_history_runtime_r227_baseline.py','plan_mapper_patch_r227.py','prepare_personal_workflow_frontend_r227_baseline.py','run_plan_exercise_r227_baseline_20261103.py','verify_full_controller_plan_exercise_r227_20261103.py','verify_native_plan_exercise_r227_20261103.mjs','restore_personal_workflow_frontend_r227_baseline.py','restore_production_history_runtime_r227_baseline.py','OwnPlanPortalMenusR222.java','OwnPlanDictionaryR226.java']
D.mkdir(parents=True);scope={'onlyOwnedSyntheticFixture':True,'originalReleaseSHA256':baseline['releaseSHA256'],'attempt':'r115','testScope':'Old R36/R35 compiled frontend after restoring original plan mapper XML, not an unchanged-public-runtime claim.','sources':{n:sha(T/n)for n in names},'originalXMLBytesUnchanged':True,'formal18891PublicAndScene8767OrDesktopTouched':False}
(D/'source-and-execution-scope.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r115'],['prepare_production_history_runtime_r227_baseline.py'],['plan_mapper_patch_r227.py','prepare','--attempt','r115'],['prepare_personal_workflow_frontend_r227_baseline.py']]
for index,step in enumerate(steps):
 q=subprocess.run([sys.executable,str(T/step[0]),*step[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 (D/f'prepare-step-{index+1}.stdout.log').write_bytes(q.stdout);(D/f'prepare-step-{index+1}.stderr.log').write_bytes(q.stderr)
 assert q.returncode==0,'PREPARATION_STEP_FAILED_'+step[0]
 print(json.dumps({'preparedStep':index+1,'tool':step[0],'result':json.loads(q.stdout)}),flush=True)
assert all(sha(T/n)==pin for n,pin in scope['sources'].items());scope['prepared']=True;scope['actualRunNotYetStarted']=True
(D/'prepared-result.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8');print('OWN_R115_EXACT_SOURCES_AND_STOPPED_FIXTURE_PREPARED')
