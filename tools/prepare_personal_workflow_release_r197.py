from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';V=Path(__file__).parent
D=R/'Document/Deployment/public_test_personal_workflow_r35_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def save(p,s):
 assert not p.exists(),str(p);ast.parse(s);p.write_text(s,encoding='utf-8')
prior=T/'original_public_test_update_r34_20261102.py';target=T/'original_public_test_update_r35_20261103.py'
assert sha(prior)=='2d18035b3df4c4489f3e221c168b789cf94d2f4ae93d08fa98a88d5a2e20ec71'
build=J(W/'personal-workflow-routes-r195/full-build-result.json');assert build['passed'] and build['exactR34OtherCompilerInputsKept']
assert J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r96/result.json')['allPassed']
spec=importlib.util.spec_from_file_location('prior_r34',prior);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
q=J(W/'r34-pending-visibility-candidate-r1/bundle/payload/payload-manifest.json');q['files']={n:p for n,p in q['files'].items()if not n.startswith('frontend/emergency_pc/')}
dist=W/'personal-workflow-routes-r195/dist'
for p in dist.rglob('*'):
 if p.is_file():q['files']['frontend/emergency_pc/'+p.relative_to(dist).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
contract={'revision':'authenticated-native-personal-workflow-pages-v1','frontends':{role:m.r32_frontend_manifest(q['files'],role)for role in ['security_pc','emergency_pc']},'adapterSHA256':sha(V/'original_personal_workflow_routes_r195.py'),'compiledSourceSHA256':{n:sha(W/'personal-workflow-routes-r195/compiled-inputs'/n)for n in build['changedSourcePaths']},'originalAuthenticatedMenuLoaderAndBackendAPIsRetained':True,'configuredMenuRoutesNotReplaced':True,'missingPersonalPagesRegisteredAfterAuthentication':True,'handledDetailReadOnly':True,'originalPendingOperatorVisibilityRetained':True,'publicIndependentBeforeAddsignOpinionFixed':False}
text=prior.read_text(encoding='utf-8');start=text.index('def r34_pending_visibility_bundle_contract(');end=text.index('def r32_avatar_bundle_contract(',start);func=text[start:end]
func=once(func,"require(old.get(R33_HEADER_FIELD) == R33_HEADER_CONTRACT and R34_PENDING_FIELD not in old, 'R34_REQUIRES_EXACT_R33_HEADER_BASE')","require(old.get(R34_PENDING_FIELD) == R34_PENDING_CONTRACT and R35_PERSONAL_FIELD not in old, 'R35_REQUIRES_EXACT_R34_PENDING_BASE')")
func=once(func,"for role, expected in R33_HEADER_CONTRACT['frontends'].items():","for role, expected in R34_PENDING_CONTRACT['frontends'].items():")
func=func.replace('r34_pending_visibility_bundle_contract','r35_personal_workflow_bundle_contract')
func=once(func,'R34_PENDING_FIELD in release and release[R34_PENDING_FIELD] == R34_PENDING_CONTRACT','R35_PERSONAL_FIELD in release and release[R35_PERSONAL_FIELD] == R35_PERSONAL_CONTRACT')
func=once(func,"for role, expected in R34_PENDING_CONTRACT['frontends'].items():\n        require(r32_frontend_manifest(payload","for role, expected in R35_PERSONAL_CONTRACT['frontends'].items():\n        require(r32_frontend_manifest(payload")
func=func.replace('R34_OLD_UPDATER_SHA','R35_OLD_UPDATER_SHA').replace("'publicAccepted',R34_PENDING_FIELD}","'publicAccepted',R35_PERSONAL_FIELD}")
func=func.replace("'R34_","'R35_").replace("'EXACT_R34_PENDING_VISIBILITY_DESCRIPTOR_REQUIRED'","'EXACT_R35_PERSONAL_WORKFLOW_DESCRIPTOR_REQUIRED'").replace("'EXACT_R33_FRONTEND_BASE_REQUIRED:","'EXACT_R34_FRONTEND_BASE_REQUIRED:").replace("'EXACT_R34_COMPILED_FRONTEND_REQUIRED:","'EXACT_R35_COMPILED_FRONTEND_REQUIRED:").replace("'EXACT_R33_UPDATER_BASE_REQUIRED'","'EXACT_R34_UPDATER_BASE_REQUIRED'")
constants='R35_PERSONAL_FIELD = "nativePersonalWorkflowRoutes"\nR35_PERSONAL_CONTRACT = '+repr(contract)+'\nR35_OLD_UPDATER_SHA = '+repr(sha(prior))+'\n\n'
needle='def r32_avatar_bundle_contract(app, bundle, plan, old, release, payload):\n'
text=once(text,needle,constants+func+needle+'    if R35_PERSONAL_FIELD in release or R35_PERSONAL_FIELD in old:\n        return r35_personal_workflow_bundle_contract(app, bundle, plan, old, release, payload)\n')
functions=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
a,b=functions(prior.read_bytes()),functions(text);assert set(b)-set(a)=={'r35_personal_workflow_bundle_contract'} and {n for n in a if a[n]!=b[n]}=={'r32_avatar_bundle_contract'}
assert not D.exists();save(target,text);D.mkdir()
(D/'updater-source-comparison.json').write_text(json.dumps({'newUpdaterSHA256':sha(target),'exactR34UpdaterSHA256':sha(prior),'onlyExistingFunctionChanged':'r32_avatar_bundle_contract','onlyNewFunction':'r35_personal_workflow_bundle_contract','allLifecycleNormalStopRestoreAndOtherFunctionsASTUnchanged':True,'contract':contract,'publicUploadedOrInstalled':False},indent=2)+'\n',encoding='utf-8')
s=(T/'prepare_pending_visibility_sparse_r179_20261102.py').read_text(encoding='utf-8')
s=s.replace("r33-project-header-candidate-r1/bundle","r34-pending-visibility-candidate-r1/bundle").replace('r34-pending-visibility-candidate-r1','r35-personal-workflow-candidate-r1').replace("OLD=W/'r35-personal-workflow-candidate-r1/bundle'","OLD=W/'r34-pending-visibility-candidate-r1/bundle'")
s=s.replace('r34tx-r1','r35tx-r1').replace('original_public_test_update_r34_20261102.py','original_public_test_update_r35_20261103.py').replace('original_public_test_update_r33_20261102.py','original_public_test_update_r34_20261102.py')
s=s.replace("r78/result.json","r96/result.json").replace("prepared-r78/frontend-restored.json","prepared-r96/frontend-restored.json")
s=s.replace('330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13','5f214688ed3038ecdc75f7cf03fb209f94b28f2233c219c26a9fc46e1dd65b5f')
s=s.replace("'emergency_pc':W/'workflow-pending-visibility-r178/dist'","'emergency_pc':W/'personal-workflow-routes-r195/dist'").replace("'emergency_pc':W/'project-header-home-r167/dist'","'emergency_pc':W/'workflow-pending-visibility-r178/dist'")
s=s.replace('len(front)==1174','len(front)==1176').replace('R34_PENDING_FIELD','R35_PERSONAL_FIELD').replace('R34_PENDING_CONTRACT','R35_PERSONAL_CONTRACT').replace('20261102-R34-emergency-exact-pending-operator-visibility','20261103-R35-emergency-authenticated-personal-workflow-pages').replace('20261102-R34-emergency-pending-visibility-from-exact-R33','20261103-R35-personal-workflow-from-exact-R34')
old="for field,value in [('revision','other'),('componentSHA256','0'*64),('adapterSHA256','0'*64),('exactCurrentUserProcessAndOperatorMembership',False),('pendingLookupFailureDoesNotOfferApproval',False),('originalAuthAuditAPIsAndInitiatorRulesRetained',False),('independentBeforeAddsignOpinionFixed',True)]:"
new="for field,value in [('revision','other'),('adapterSHA256','0'*64),('compiledSourceSHA256',{}),('originalAuthenticatedMenuLoaderAndBackendAPIsRetained',False),('configuredMenuRoutesNotReplaced',False),('missingPersonalPagesRegisteredAfterAuthentication',False),('handledDetailReadOnly',False),('originalPendingOperatorVisibilityRetained',False),('publicIndependentBeforeAddsignOpinionFixed',True)]:"
s=once(s,old,new)
s=once(s,"negative('drop-retained-project-header-home-contract'","negative('drop-retained-pending-visibility-contract',lambda p,o,r,n:r.pop(m.R34_PENDING_FIELD))\nnegative('drop-retained-project-header-home-contract'")
s=s.replace('xnby.r179.exact-pending-visibility-sparse-update.v1','xnby.r197.exact-personal-workflow-sparse-update.v1')
save(V/'prepare_personal_workflow_sparse_r197_20261103.py',s)
s=(T/'verify_pending_visibility_full_program_r179_20261102.py').read_text(encoding='utf-8')
s=s.replace("S=W/'r34-pending-visibility-candidate-r1'","S=W/'r35-personal-workflow-candidate-r1'").replace("OLD=W/'r33-project-header-candidate-r1/bundle'","OLD=W/'r34-pending-visibility-candidate-r1/bundle'").replace('r34gv-r1','r35gv-r1').replace('original_public_test_update_r34_20261102.py','original_public_test_update_r35_20261103.py').replace('original_public_test_update_r33_20261102.py','original_public_test_update_r34_20261102.py').replace('project-header-home-r167/dist','workflow-pending-visibility-r178/dist').replace('xnby.r179.pending-visibility-full-program-preflight.v1','xnby.r197.personal-workflow-full-program-preflight.v1').replace('full-R33-program-view-and-20-controls-exact-composition','full-R34-program-view-and-20-controls-exact-composition').replace('actualR33ProgramAndR34CandidatePinsRetained','actualR34ProgramAndR35CandidatePinsRetained').replace('fullR31ProgramViewBuilt','fullR34ProgramViewBuilt')
save(V/'verify_personal_workflow_full_program_r197_20261103.py',s)
print(json.dumps({'prepared':True,'updaterSHA256':sha(target),'frontendFiles':contract['frontends'],'servicesOrPublicOperated':False}))
