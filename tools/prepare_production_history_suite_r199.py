from pathlib import Path
import ast
V=Path(__file__).parent
def save(name,s):
 p=V/name;assert not p.exists(),name
 if name.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for old,new in [('configure_owned_countersign_r198.py','configure_owned_countersign_r199.py'),('prepare_personal_workflow_frontend_r198.py','prepare_personal_workflow_frontend_r199.py'),('restore_personal_workflow_frontend_r198.py','restore_personal_workflow_frontend_r199.py')]:
 s=(V/old).read_text(encoding='utf-8').replace('r198','r199').replace('r97','r99').replace("'candidateFrontendFiles':338","'candidateFrontendFiles':340");save(new,s)
java=(V/'OwnPersonalWorkflowMenuVisibility.java').read_text(encoding='utf-8').replace('OwnPersonalWorkflowMenuVisibility','OwnPersonalWorkflowMenuVisibilityR199').replace('r9[67]','r99');save('OwnPersonalWorkflowMenuVisibilityR199.java',java)
host=(V/'verify_full_controller_personal_workflow_r198_20261103.py').read_text(encoding='utf-8').replace('r198','r199').replace('r97','r99').replace('OwnPersonalWorkflowMenuVisibility','OwnPersonalWorkflowMenuVisibilityR199').replace("opinion['exactlyOneTimedOriginalActorBeforeAddsignRecord']","opinion['exactlyOneTimedOriginalActorModeCorrectAddsignRecord']")
host=host.replace("'onlyOwnSyntheticPrototypeModuleTemporarilyInstalled':True","'onlyOwnDeclaredSeparateHistoryModuleTemporarilyInstalled':True").replace("'normalOriginalServiceGateAndNativeRoleOpinionReadbackPassed'","'normalSeparateModuleOriginalServiceGateAndNativeRoleOpinionReadbackPassed'")
save('verify_full_controller_personal_workflow_r199_20261103.py',host)
browser=(V/'verify_native_personal_workflow_r198_20261103.mjs').read_text(encoding='utf-8');save('verify_native_personal_workflow_r199_20261103.mjs',browser)
runner=(V/'run_personal_workflow_r198_20261103.py').read_text(encoding='utf-8').replace('r198','r199').replace('r97','r99').replace('restore_native_history_runtime_r199.py','restore_production_history_runtime_r199.py');save('run_personal_workflow_r199_20261103.py',runner)
restore=(V/'restore_native_history_runtime_r198.py').read_text(encoding='utf-8').replace('r198','r199').replace('r97','r99')
anchor="for name,raw in targets.items():\n"
assert restore.count(anchor)==1
restore=restore.replace(anchor,"for name in scope['newPaths']:\n p=A/name;assert p.resolve()==p and p.is_file()and not p.lstat().st_file_attributes&0x400 and sha(p)==scope['newFiles'][name]['sha256'],'NEW_HISTORY_PATH_DRIFT_REFUSED'\n"+anchor)
anchor="assert all((A/n).read_bytes()==b for n,b in targets.items())"
assert restore.count(anchor)==1;restore=restore.replace(anchor,"for name in scope['newPaths']:(A/name).unlink()\nassert all(not(A/name).exists()for name in scope['newPaths'])\n"+anchor)
save('restore_production_history_runtime_r199.py',restore)
print('PRODUCTION_SEPARATE_HISTORY_AFTER_ADDSIGN_SUITE_WITH_CORRECTED_MODE_PROOF_PREPARED')
