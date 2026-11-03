from pathlib import Path
import ast
V=Path(__file__).parent;T=Path('D:/Project/Zhumadian/Application/tools')
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def save(n,s):
 p=V/n;assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(T/'build_pending_delivery_r179_20261102.py').read_text(encoding='utf-8')
s=s.replace('r34-pending-visibility-candidate-r1','r35-personal-workflow-candidate-r1').replace('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103').replace('r34gv-r1','r35gv-r1').replace('r78','r96').replace('len(browser)==10','len(browser)==8').replace('actualFullOriginalSDKPortalBrowserSessions\':10','actualFullOriginalSDKPortalBrowserSessions\':8')
s=s.replace('original_public_test_update_r34_20261102.py','original_public_test_update_r35_20261103.py').replace('Zhumadian_Pending_Visibility_20261102_R34','Zhumadian_Personal_Workflow_20261103_R35').replace('r34_update_runtime','r35_update_runtime').replace('deploy_pending_visibility_r34','deploy_personal_workflow_r35').replace('_Pending_Visibility_R34.cmd','_Personal_Workflow_R35.cmd').replace('R34-emergency-exact-pending-operator-visibility','R35-emergency-authenticated-personal-workflow-pages')
s=once(s,"wrapper=(R/'Document/Deployment/public_test_project_header_r33_20261102/delivery/deploy_project_header_r33.py')","wrapper=(R/'Document/Deployment/public_test_pending_visibility_r34_20261102/delivery/deploy_pending_visibility_r34.py')")
old="wrapper=''.join(lines).replace('Zhumadian_Project_Header_Home_20261102_R33.zip',archive.name).replace('r33_update_runtime.py','r35_update_runtime.py').replace('fixed_r33_updater','fixed_r34_updater').replace('R33_','R34_').replace('EXACT_R32_BASE','EXACT_R33_BASE');ast.parse(wrapper)"
new="wrapper=''.join(lines).replace('Zhumadian_Pending_Visibility_20261102_R34.zip',archive.name).replace('r34_update_runtime.py','r35_update_runtime.py').replace('fixed_r34_updater','fixed_r35_updater').replace('R34_','R35_').replace('EXACT_R33_BASE','EXACT_R34_BASE').replace('EXACT_R31_RUNTIME','EXACT_R34_RUNTIME');ast.parse(wrapper)"
s=once(s,old,new)
save('build_personal_workflow_delivery_r197_20261103.py',s)
s=(T/'verify_pending_delivery_r179_20261102.py').read_text(encoding='utf-8')
s=s.replace('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103').replace('r34-pending-visibility-candidate-r1','r35-personal-workflow-candidate-r1').replace('r33-project-header-candidate-r1','r34-pending-visibility-candidate-r1').replace('original_public_test_update_r34_20261102.py','original_public_test_update_r35_20261103.py').replace('original_public_test_update_r33_20261102.py','original_public_test_update_r34_20261102.py').replace('Zhumadian_Pending_Visibility_20261102_R34','Zhumadian_Personal_Workflow_20261103_R35').replace('r34_update_runtime','r35_update_runtime').replace('deploy_pending_visibility_r34','deploy_personal_workflow_r35').replace('R34_PENDING_FIELD','R35_PERSONAL_FIELD').replace('R34_PENDING_CONTRACT','R35_PERSONAL_CONTRACT').replace('len(expected)==176','len(expected)==178').replace("'writes':176","'writes':178").replace('EXACT_R33_BASE','EXACT_R34_BASE').replace('xnby.r179.independent-fixed-pending-visibility-delivery.v1','xnby.r197.independent-fixed-personal-workflow-delivery.v1')
save('verify_personal_workflow_delivery_r197_20261103.py',s)
s=(T/'verify_pending_transport_order_r179_20261102.py').read_text(encoding='utf-8')
s=s.replace('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103').replace('r34gv-r1','r35gv-r1').replace('deploy_pending_visibility_r34','deploy_personal_workflow_r35').replace('r34-pending-visibility-candidate-r1','r35-personal-workflow-candidate-r1').replace('r34_update_runtime','r35_update_runtime').replace('xnby.r179.actual-fixed-wrapper-order.v1','xnby.r197.actual-fixed-wrapper-order.v1').replace('actualFullLoadBundleSeparatelyPassed15553ProgramFiles','actualFullLoadBundleSeparatelyPassedR34ProgramFiles')
save('verify_personal_workflow_transport_order_r197_20261103.py',s)
print('R35_FIXED_DELIVERY_AND_INDEPENDENT_VERIFIERS_PREPARED')
