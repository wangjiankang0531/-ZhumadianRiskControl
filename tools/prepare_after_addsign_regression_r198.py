from pathlib import Path
import ast
V=Path(__file__).parent
def save(n,s):
 p=V/n;assert not p.exists(),n
 if n.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for old,new in [('prepare_native_history_runtime_r196.py','prepare_native_history_runtime_r198.py'),('prepare_personal_workflow_frontend_r196.py','prepare_personal_workflow_frontend_r198.py'),('restore_personal_workflow_frontend_r196.py','restore_personal_workflow_frontend_r198.py'),('restore_native_history_runtime_r196.py','restore_native_history_runtime_r198.py')]:
 s=(V/old).read_text(encoding='utf-8').replace('r196','r198').replace('r96','r97').replace('candidateFrontendFiles\":338','candidateFrontendFiles\":340')
 save(new,s)
s=(V/'configure_owned_countersign_r175.py').read_text(encoding='utf-8').replace('r75','r97');save('configure_owned_countersign_r198.py',s)
s=(V/'verify_full_controller_personal_workflow_r196_20261103.py').read_text(encoding='utf-8').replace('r196','r198').replace('r96','r97')
assert s.count("add_type='1'")==1;s=s.replace("add_type='1'","add_type='2'")
s=s.replace('independentBeforeAddsignOpinionRetained','independentAfterAddsignOpinionRetained').replace('native-before-addsign-history-check','native-after-addsign-history-regression')
save('verify_full_controller_personal_workflow_r198_20261103.py',s)
s=(V/'verify_native_personal_workflow_r196_20261103.mjs').read_text(encoding='utf-8')
old="if(!independentAddsignOpinionRetained||String(history[0].handleStatus)!=='10')throw Error('EXACTLY_ONE_TIMED_BEFORE_ADDSIGN_ORIGINAL_ACTOR_HISTORY_REQUIRED');"
new="if(!independentAddsignOpinionRetained||String(history[0].handleStatus)!==(wire.addsignType==='1'?'10':'6'))throw Error('EXACTLY_ONE_TIMED_MODE_CORRECT_ORIGINAL_ACTOR_ADDSIGN_RECORD_REQUIRED');"
assert s.count(old)==1;s=s.replace(old,new).replace('exactlyOneTimedOriginalActorBeforeAddsignRecord:true','exactlyOneTimedOriginalActorModeCorrectAddsignRecord:true').replace('completeAddsignAcceptance:independentAddsignOpinionRetained','completeAddsignAcceptance:false')
save('verify_native_personal_workflow_r198_20261103.mjs',s)
s=(V/'run_personal_workflow_r196_20261103.py').read_text(encoding='utf-8').replace('r196','r198').replace('r96','r97');save('run_personal_workflow_r198_20261103.py',s)
print('OWN_AFTER_ADDSIGN_ORIGINAL_COUNTERSIGN_AND_MISSING_MENUS_REGRESSION_PREPARED')
