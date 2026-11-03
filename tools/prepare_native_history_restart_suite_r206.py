from pathlib import Path
import ast
V=Path(__file__).parent
def save(n,s):
 p=V/n;assert not p.exists(),n
 if n.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for old in ['prepare_personal_workflow_frontend_r199.py','restore_personal_workflow_frontend_r199.py','restore_production_history_runtime_r199.py']:
 save(old.replace('r199','r206'),(V/old).read_text(encoding='utf-8').replace('r199','r206').replace('r99','r103'))
s=(V/'prepare_production_history_runtime_r199.py').read_text(encoding='utf-8').replace('prepared-r99','prepared-r103').replace("C/'r99'","C/'r103'");save('prepare_production_history_runtime_r206.py',s)
s=(V/'OwnPersonalWorkflowMenuVisibilityR199.java').read_text(encoding='utf-8').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR206').replace('r99','r103');save('OwnPersonalWorkflowMenuVisibilityR206.java',s)
s=(V/'verify_full_controller_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r206').replace('r99','r103').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR206').replace("add_type='2'","add_type='1'").replace("assert options.attempt=='r74'","assert options.attempt=='r103'")
s=s.replace("'actualNativeCreateUploadFeedbackAddsignAndTargetApprovalPassed':True","'actualNativeCreateUploadFeedbackAddsignAndTargetApprovalPassed':False,'onlyExactCompletedR102ReadBackWithoutBusinessRecreation':True").replace('independentAfterAddsignOpinionRetained','independentBeforeAddsignOpinionRetained').replace('native-after-addsign-history-regression','native-history-normal-restart-durable-readback')
save('verify_full_controller_personal_workflow_r206_20261103.py',s)
save('verify_native_personal_workflow_r206_20261103.mjs',(V/'verify_native_personal_workflow_r199_20261103.mjs').read_text(encoding='utf-8'))
s=(V/'run_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r206').replace('r99','r103').replace("'--event-dictionaries']","'--event-dictionaries','--completed-addsign-readback']");save('run_personal_workflow_r206_20261103.py',s)
print('NORMAL_RESTART_EXACT_COMPLETED_R102_READBACK_ONLY_SUITE_PREPARED')
