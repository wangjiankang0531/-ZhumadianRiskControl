from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools')
names=['configure_owned_parallel_countersign_r214.py','prepare_personal_workflow_frontend_r214.py','restore_personal_workflow_frontend_r214.py','restore_production_history_runtime_r214.py','prepare_production_history_runtime_r214.py','OwnPersonalWorkflowMenuVisibilityR214.java','OwnParallelWorkflowReadbackR214.java','verify_native_parallel_countersign_r214_20261103.mjs','verify_full_controller_parallel_countersign_r214_20261103.py','run_parallel_countersign_r214_20261103.py']
for name in names:
 s=(T/name).read_text(encoding='utf-8').replace('r214','r215').replace('R214','R215').replace('r105','r106')
 if name.endswith('.mjs'):
  a='''   if(await evaluate('!!document.querySelector(".audit-content .audit-form")'))throw Error('INITIATOR_READBACK_MUST_NOT_APPROVE_WAITING_COUNTERSIGN');
   cases.push({case:'initiator-detail-while-waiting-other-countersign-is-readonly',passed:true});'''
  b='''   const actualActions=await evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio")).filter(e=>e.getClientRects().length).map(e=>e.textContent.trim())');
   const expectedActions=nativeNodeProperties.hasRevokeBtn===false?[]:['撤回'];
   if(JSON.stringify(actualActions)!==JSON.stringify(expectedActions))throw Error('INITIATOR_MAY_ONLY_USE_ORIGINAL_WITHDRAW_WHILE_OTHER_COUNTERSIGN_PENDING');
   cases.push({case:'initiator-detail-keeps-only-original-withdraw-and-no-approval-while-other-countersign-pending',passed:true,originalWithdrawAvailable:expectedActions.length===1});'''
  assert s.count(a)==1;s=s.replace(a,b)
 dest=T/name.replace('r214','r215').replace('R214','R215');assert not dest.exists()
 if dest.suffix=='.py':ast.parse(s)
 dest.write_text(s,encoding='utf-8')
print(json.dumps({'correctedTestOnly':True,'originalInitiatorWithdrawPreserved':True,'firstApprovalThenWaitForOtherRoleStillRequired':True,'previousFailurePreserved':True,'attempt':'r106','newTestNotYetStarted':True,'productChanged':False}))
