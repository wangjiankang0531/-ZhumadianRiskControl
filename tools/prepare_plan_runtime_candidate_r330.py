from pathlib import Path
import ast,hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;T=R/'Application/tools'
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103'
J=lambda p:json.loads(p.read_bytes())
assert not D.exists()and J(C/'prepared-r141/history-runtime-restored.json')['passed']
assert J(C/'r141-outer-terminal.json')['actualDescendantsZeroBeforeClose']
audit=J(R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103/runtime-plan-class-audit-r328.json')
assert audit['passed']and audit['currentStoppedFixturePlanOverrideAbsent']
src=V/'own_plan_runtime_patch_r329.py';dst=T/src.name;ast.parse(src.read_bytes());assert not dst.exists();dst.write_bytes(src.read_bytes())
text=(V/'prepare_parent_delete_exercises_generated_r325.py').read_text(encoding='utf-8')
text=text.replace('native_parent_delete_with_exercises_r325_20261103','native_plan_runtime_candidate_r329_20261103')
text=text.replace('r141','r143').replace('_r325','_r330')
text=text.replace('prepared-result-r325.json','prepared-result-r330.json')
text=text.replace('restore_parent_delete_prestart_r326.py','restore_plan_runtime_prestart_r331.py')

anchor="ast.parse(text);host.write_text(text,encoding='utf-8');pins[host.name]=hashlib.sha256(host.read_bytes()).hexdigest()"
assert text.count(anchor)==1
new_host_check="""plan_scope = read(prepared_base / 'plan-runtime-scope.json')
assert plan_scope['onlyOwnedStoppedSyntheticFixture']
for name, entry in plan_scope['newFiles'].items():
    if name not in ['payload-manifest.json', 'release-manifest.json']:
        assert sha(app / name) == entry['sha256']
"""
runtime_check="""        candidate_plan_rel = 'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
        runtime_plan = Path(row['run']) / 'b/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
        assert sha(runtime_plan) == plan_scope['newFiles'][candidate_plan_rel]['sha256']
        checks['actualCandidatePlanOverrideRuntimeBytesMatched'] = True
"""
extra_host="ready_anchor=\"prepared = read(prepared_base / 'controller-fixture-ready.json')\\n\"\nassert text.count(ready_anchor)==1\ntext=text.replace(ready_anchor,ready_anchor+"+repr(new_host_check)+",1)\nbrowser_anchor=\"        browser_source = Path(__file__).parent / 'verify_native_parent_delete_r330_20261103.mjs'\"\nassert text.count(browser_anchor)==1\ntext=text.replace(browser_anchor,"+repr(runtime_check)+"+browser_anchor,1)\n"
extra_runner="""plan_restore = subprocess.run([sys.executable, str(V / 'own_plan_runtime_patch_r329.py'), 'restore', '--attempt', attempt], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
assert plan_restore.returncode == 0 and json.loads(plan_restore.stdout)['passed'], 'OWN_PLAN_RUNTIME_RESTORE_REFUSED'
"""
modify_runner="runner_source=runner.read_text(encoding='utf-8')\nassert runner_source.count('mapper = subprocess.run(')==1\nrunner_source=runner_source.replace('mapper = subprocess.run(',"+repr(extra_runner)+"+'mapper = subprocess.run(',1)\nast.parse(runner_source);runner.write_text(runner_source,encoding='utf-8');pins[runner.name]=hashlib.sha256(runner.read_bytes()).hexdigest()\n"
text=text.replace(anchor,extra_host+anchor+'\n'+modify_runner,1)
anchor=" ['mapper_product_patch_r330.py','prepare','--attempt','r143'],['mapper_observation_support_r330.py','prepare','--attempt','r143'],['prepare_personal_workflow_frontend_r330.py']]"
assert text.count(anchor)==1
text=text.replace(anchor," ['mapper_product_patch_r330.py','prepare','--attempt','r143'],['mapper_observation_support_r330.py','prepare','--attempt','r143'],['own_plan_runtime_patch_r329.py','prepare','--attempt','r143'],['prepare_personal_workflow_frontend_r330.py']]",1)
anchor='results=[]\nfor args in steps:'
assert text.count(anchor)==1
text=text.replace(anchor,"pins['own_plan_runtime_patch_r329.py']=hashlib.sha256((T/'own_plan_runtime_patch_r329.py').read_bytes()).hexdigest()\n"+anchor,1)

anchor="ast.parse(restore);rp=V/'restore_plan_runtime_prestart_r331.py';"
assert text.count(anchor)==1
restore_changes="""restore=restore.replace('native_plan_delete_roundtrip_r330_20261103','native_plan_runtime_candidate_r329_20261103')
restore=restore.replace('verify_full_controller_plan_delete_r330.py','verify_full_controller_parent_delete_r330.py').replace('run_native_plan_delete_r330.py','run_native_parent_delete_r330.py')
restore=restore.replace("observer=J(P/'mapper-observer-scope.json');", "plan=J(P/'plan-runtime-scope.json');assert plan['onlyOwnedStoppedSyntheticFixture'];layer('plan-runtime',plan,'plan-runtime-before')\\nobserver=J(P/'mapper-observer-scope.json');",1)
restore=restore.replace("'restoredLayers':['frontend','observer'", "'restoredLayers':['frontend','plan-runtime','observer'")
"""
text=text.replace(anchor,restore_changes+anchor,1)
ast.parse(text)
generated=V/'prepare_plan_runtime_candidate_generated_r330.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
done=subprocess.run([sys.executable,str(generated)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
if done.returncode:
    print(done.stderr.decode('utf-8',errors='replace')[-2200:]);raise RuntimeError('OWN_PLAN_RUNTIME_PREPARATION_REFUSED')
proof=J(D/'prepared-result-r330.json')
assert len(proof['sourcePins'])==10 and any(v['step']=='own_plan_runtime_patch_r329.py'for v in proof['steps'])
failure=J(C/'r141/plan-browser/failure.json')
assert failure['message']=='OWN_PLAN_API_READBACK_emergencyPlan_500_100000'
baseline={'reproduced':True,'attempt':'r141','actualNormalRoleNativeBrowserCompletedCases':len(failure['cases']),
 'phase':failure['stage'],'failure':failure['message'],'deletedParentOldDetailHTTP':500,
 'deleteReturnedSuccessBeforeOldDetailRead':True,'controllerAndAllChildrenNormallyExitedZero':True,
 'allFiveRestoreLayersPassed':True,'notCountedAsWholeFlowPass':True}
(D/'baseline-failure-r329.json').write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8')
(D/'runtime-plan-class-audit-r328.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(done.stdout.decode('utf-8').strip())
