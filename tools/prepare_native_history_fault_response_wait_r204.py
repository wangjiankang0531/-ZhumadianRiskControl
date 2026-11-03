from pathlib import Path
import ast
V=Path(__file__).parent
for old in ['prepare_production_history_runtime_r201.py','prepare_personal_workflow_frontend_r201.py','restore_personal_workflow_frontend_r201.py','restore_production_history_runtime_r201.py','run_personal_workflow_r201_20261103.py','OwnPersonalWorkflowMenuVisibilityR201.java','OwnNativeHistoryFaultR201.java','verify_full_controller_personal_workflow_r201_20261103.py','verify_native_personal_workflow_r201_20261103.mjs']:
 s=(V/old).read_text(encoding='utf-8').replace('r201','r204').replace('R201','R204').replace('r101','r102')
 if old.endswith('.mjs'):
  a="stage='original-transfer-one-real-post';\n   if(!await click('.audit-form button','提交'))throw Error('ORIGINAL_TRANSFER_SUBMIT_REQUIRED');\n   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).length>before);"
  b="stage='original-transfer-one-real-post';\n   if(!await click('.audit-form button','提交'))throw Error('ORIGINAL_TRANSFER_SUBMIT_REQUIRED');\n   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).length>before+(wire.expectNativeHistorySQLFault?1:0));"
  assert s.count(a)==1;s=s.replace(a,b)
 if old.startswith('verify_full_controller'):
  s=s.replace("'independentBeforeAddsignOpinionRetained':True","'independentBeforeAddsignOpinionRetained':True,'actualSQLFaultEightScopedTableRollbackAndOneRetryPassed':checks['nativeSQLFaultAllEightScopedTableFingerprintsIdentical'],'temporaryOwnFaultTriggerRemoved':checks['ownHistoryFaultTriggerRemoved']")
 if old.endswith('.py'):ast.parse(s)
 p=V/old.replace('r201','r204').replace('R201','R204');assert not p.exists();p.write_text(s,encoding='utf-8')
print('FAULT_RETRY_WAITS_FOR_SECOND_ACTUAL_RESPONSE_WITH_ALL_DATA_AND_ENGINE_ASSERTIONS_RETAINED')
