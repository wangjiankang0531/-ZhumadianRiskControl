from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
def once(s,a,b):
 assert s.count(a)==1,(a[:150],s.count(a));return s.replace(a,b)
s=(T/'build_header_delivery_r168_20261102.py').read_text(encoding='utf-8')
s=s.replace("S=W/'r33-project-header-candidate-r1'","S=W/'r34-pending-visibility-candidate-r1'").replace("D=R/'Document/Deployment/public_test_project_header_r33_20261102'","D=R/'Document/Deployment/public_test_pending_visibility_r34_20261102'").replace("C=R/'work/event_delivery_consistency_20261030/full-controller-r167'","C=R/'work/event_delivery_consistency_20261030/full-controller-r163'")
s=s.replace("R/'work/r33gv-r1/full-preflight-result.json'","R/'work/r34gv-r1/full-preflight-result.json'").replace("runtime=J(C/'r1/result.json')","runtime=J(C/'r78/result.json')").replace("J(C/'prepared-r1/frontend-restored.json')","J(C/'prepared-r78/frontend-restored.json')")
old="browser=[J(C/'r1'/('avatar-browser-emergency_pc-'+a)/'result.json')for a in ['own_operator_a','own_reviewer_b']];assert all(x['passed']and x['normalChromeExitCode']==0 for x in browser)and sum(len(x['checks'])for x in browser)==34"
new="browser=[J(p/'result.json')for p in (C/'r78').glob('workflow-browser-*')if p.is_dir()];assert len(browser)==10 and all(x['passed']and not x['exceptions']for x in browser);native_checks=sum(len(x['cases'])for x in browser)"
s=once(s,old,new)
s=s.replace("source=T/'original_public_test_update_r33_20261102.py'","source=T/'original_public_test_update_r34_20261102.py'")
s=s.replace("archive=delivery/'Zhumadian_Project_Header_Home_20261102_R33.zip'","archive=delivery/'Zhumadian_Pending_Visibility_20261102_R34.zip'")
s=once(s,"R/'Document/Deployment/public_test_avatar_r32_20261102/delivery/deploy_avatar_r32.py'","R/'Document/Deployment/public_test_project_header_r33_20261102/delivery/deploy_project_header_r33.py'")
old=".replace('Zhumadian_Avatar_Two_Portals_20261102_R32.zip',archive.name).replace('r32_update_runtime.py','r33_update_runtime.py').replace('fixed_r32_updater','fixed_r33_updater').replace('R32_','R33_').replace('EXACT_R31_BASE','EXACT_R32_BASE')"
new=".replace('Zhumadian_Project_Header_Home_20261102_R33.zip',archive.name).replace('r33_update_runtime.py','r34_update_runtime.py').replace('fixed_r33_updater','fixed_r34_updater').replace('R33_','R34_').replace('EXACT_R32_BASE','EXACT_R33_BASE')"
s=once(s,old,new)
s=s.replace("delivery/'deploy_project_header_r33.py'","delivery/'deploy_pending_visibility_r34.py'").replace("delivery/'r33_update_runtime.py'","delivery/'r34_update_runtime.py'")
s=s.replace("label+'_Project_Header_R33.cmd'","label+'_Pending_Visibility_R34.cmd'").replace('%~dp0deploy_project_header_r33.py','%~dp0deploy_pending_visibility_r34.py')
s=s.replace("'revision':'R33-emergency-project-mark-and-canonical-home'","'revision':'R34-emergency-exact-pending-operator-visibility'").replace("'/Zhumadian/Zhumadian_Project_Header_Home_20261102_R33/'","'/Zhumadian/Zhumadian_Pending_Visibility_20261102_R34/'")
s=s.replace("'actualFullOriginalSDKPortalBrowserSessions':2,'actualNativeBrowserChecks':34","'actualFullOriginalSDKPortalBrowserSessions':10,'actualNativeBrowserChecks':native_checks")
p=V/'build_pending_delivery_r179_20261102.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
print(json.dumps({'prepared':True,'exactR33WrapperBaseAndR34Names':True,'nativeRuntimeReferencesFinalR178TenPhases':True}))
