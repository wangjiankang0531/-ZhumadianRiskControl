from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
s=(T/'prepare_project_header_sparse_r168_20261102.py').read_text(encoding='utf-8')
s=s.replace("OLD=W/'r32-avatar-candidate-r1/bundle'","OLD=W/'r33-project-header-candidate-r1/bundle'").replace("OUT=W/'r33-project-header-candidate-r1'","OUT=W/'r34-pending-visibility-candidate-r1'").replace("TX=R/'work/r33tx-r1'","TX=R/'work/r34tx-r1'")
s=once(s,"assert J(R/'work/event_delivery_consistency_20261030/full-controller-r167/r1/result.json')['allPassed'] and J(R/'work/event_delivery_consistency_20261030/full-controller-r167/prepared-r1/frontend-restored.json')['passed']","assert J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r78/result.json')['allPassed'] and J(R/'work/event_delivery_consistency_20261030/full-controller-r163/prepared-r78/frontend-restored.json')['passed']")
s=s.replace("source=T/'original_public_test_update_r33_20261102.py'","source=T/'original_public_test_update_r34_20261102.py'")
s=once(s,"digest(oldraw)=='bd3da492c0f226c62bf00e2e416521bd860d8d4c748fe8b34b1537d69854f1ea'","digest(oldraw)=='330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13'")
s=once(s,"'emergency_pc':W/'project-header-home-r167/dist'","'emergency_pc':W/'workflow-pending-visibility-r178/dist'")
s=once(s,"'emergency_pc':F/'emergency_pc/dist'","'emergency_pc':W/'project-header-home-r167/dist'")
s=s.replace('m.R33_HEADER_FIELD','m.R34_PENDING_FIELD').replace('m.R33_HEADER_CONTRACT','m.R34_PENDING_CONTRACT')
s=s.replace('20261102-R33-emergency-project-mark-and-canonical-home','20261102-R34-emergency-exact-pending-operator-visibility').replace('20261102-R33-emergency-project-header-from-exact-R32','20261102-R34-emergency-pending-visibility-from-exact-R33')
s=s.replace("T/'original_public_test_update_r32_20261102.py'","T/'original_public_test_update_r33_20261102.py'")
old="for field,value in [('revision','other'),('originalLoginSDKAndPermissionsRetained',False),('originalMissingPhotoRestored',True),('headerSourceSHA256','0'*64),('normalizerSourceSHA256','0'*64)]:"
new="for field,value in [('revision','other'),('componentSHA256','0'*64),('adapterSHA256','0'*64),('exactCurrentUserProcessAndOperatorMembership',False),('pendingLookupFailureDoesNotOfferApproval',False),('originalAuthAuditAPIsAndInitiatorRulesRetained',False),('independentBeforeAddsignOpinionFixed',True)]:"
s=once(s,old,new)
needle="negative('drop-reusable-native-default-session'"
idx=s.index(needle)
s=s[:idx]+"negative('drop-retained-project-header-home-contract',lambda p,o,r,n:r.pop(m.R33_HEADER_FIELD))\n"+s[idx:]
s=s.replace('xnby.r168.emergency-project-header-sparse-update.v1','xnby.r179.exact-pending-visibility-sparse-update.v1')
target=V/'prepare_pending_visibility_sparse_r179_20261102.py';assert not target.exists();ast.parse(s);target.write_text(s,encoding='utf-8')
print(json.dumps({'prepared':True,'exactR33BaseAndNewR34Descriptor':True,'wrongClaimsAndRetainedHeaderNegativeCasesIncluded':True,'noPayloadBuiltYet':True}))
