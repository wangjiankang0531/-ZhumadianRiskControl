from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
s=(T/'verify_project_header_delivery_r168_20261102.py').read_text(encoding='utf-8')
s=s.replace('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102').replace('r33-project-header-candidate-r1','r34-pending-visibility-candidate-r1').replace('original_public_test_update_r33_20261102.py','original_public_test_update_r34_20261102.py')
s=s.replace('Zhumadian_Project_Header_Home_20261102_R33.zip','Zhumadian_Pending_Visibility_20261102_R34.zip').replace('r33_update_runtime.py','r34_update_runtime.py').replace("oldroot=W/'r32-avatar-candidate-r1/bundle/payload'","oldroot=W/'r33-project-header-candidate-r1/bundle/payload'")
s=s.replace('m.R33_HEADER_FIELD]==m.R33_HEADER_CONTRACT','m.R34_PENDING_FIELD]==m.R34_PENDING_CONTRACT').replace('len(expected)==175','len(expected)==176').replace("delivery/'deploy_project_header_r33.py'","delivery/'deploy_pending_visibility_r34.py'").replace('EXACT_R32_BASE','EXACT_R33_BASE').replace('original_public_test_update_r32_20261102.py','original_public_test_update_r33_20261102.py')
s=s.replace('xnby.r168.independent-fixed-project-header-delivery.v1','xnby.r179.independent-fixed-pending-visibility-delivery.v1').replace("'writes':175","'writes':176")
p=V/'verify_pending_delivery_r179_20261102.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(T/'verify_project_header_transport_order_r168_20261102.py').read_text(encoding='utf-8')
s=s.replace('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102').replace('r33gv-r1','r34gv-r1').replace('delivery/deploy_project_header_r33.py','delivery/deploy_pending_visibility_r34.py').replace('r33-project-header-candidate-r1','r34-pending-visibility-candidate-r1').replace('delivery/r33_update_runtime.py','delivery/r34_update_runtime.py')
s=s.replace('xnby.r168.actual-fixed-wrapper-order.v1','xnby.r179.actual-fixed-wrapper-order.v1').replace('actualFullLoadBundleSeparatelyPassed15554ProgramFiles','actualFullLoadBundleSeparatelyPassed15553ProgramFiles')
p=V/'verify_pending_transport_order_r179_20261102.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
print(json.dumps({'preparedChecks':2,'archivePinsAndLifecycleASTAndRecoveryScope':True,'actualWrapperBudgetOrderAndCheckOnlyMutationsForbidden':True}))
