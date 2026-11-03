from pathlib import Path
import ast
V=Path(__file__).parent
def save(n,s):
 p=V/n;assert not p.exists(),n
 if n.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for old in ['prepare_production_history_runtime_r200.py','prepare_personal_workflow_frontend_r200.py','restore_personal_workflow_frontend_r200.py','restore_production_history_runtime_r200.py','run_personal_workflow_r200_20261103.py','OwnPersonalWorkflowMenuVisibilityR200.java','verify_native_personal_workflow_r200_20261103.mjs']:
 s=(V/old).read_text(encoding='utf-8').replace('r200','r201').replace('R200','R201').replace('r100','r101');save(old.replace('r200','r201').replace('R200','R201'),s)
s=(V/'OwnNativeHistoryFaultR200.java').read_text(encoding='utf-8').replace('R200','R201').replace('r200','r201').replace('r100','r101').replace('NEW.f_node_id','NEW.f_task_node_id')
needle='  }\n }\n}\n';assert s.count(needle)==1;s=s.replace(needle,'  }catch(SQLException e){System.err.println("OWN_HISTORY_FAULT_SQL:"+e.getSQLState()+":"+e.getErrorCode());throw e;}\n }\n}\n');save('OwnNativeHistoryFaultR201.java',s)
s=(V/'verify_full_controller_personal_workflow_r200_20261103.py').read_text(encoding='utf-8').replace('r200','r201').replace('R200','R201').replace('r100','r101')
needle="    assert completed.returncode==0,'OWN_HISTORY_SQL_FAULT_'+mode.upper()+'_FAILED'"
assert s.count(needle)==1;s=s.replace(needle,"    if completed.returncode:dump(root/('own-history-fault-'+mode+'-diagnostic.json'),{'exitCode':completed.returncode,'codes':re.findall(r'OWN_HISTORY_FAULT_SQL:[0-9A-Z]+:[0-9]+',completed.stderr.decode('utf-8',errors='replace')),'rawStderrOrRowsExported':False})\n"+needle)
save('verify_full_controller_personal_workflow_r201_20261103.py',s)
print('FAULT_FIXTURE_USES_ORIGINAL_F_TASK_NODE_ID_FIELD_AND_BOUNDED_SQLSTATE_DIAGNOSTICS')
