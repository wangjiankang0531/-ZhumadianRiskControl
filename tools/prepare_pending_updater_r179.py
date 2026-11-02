from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';D=R/'Document/Deployment/public_test_pending_visibility_r34_20261102';target=T/'original_public_test_update_r34_20261102.py';assert not target.exists()and not D.exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=T/'original_public_test_update_r33_20261102.py';assert sha(prior)=='a05348d866afef8e72a507c80679ba99228be779ca33fd2efc9f80a27361ef21'
assert J(R/'Document/Deployment/workflow_pending_visibility_r178_20261102/verified-result.json')['passed']
spec=importlib.util.spec_from_file_location('prior_r33',prior);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldq=J(W/'r33-project-header-candidate-r1/bundle/payload/payload-manifest.json');newq=copy.deepcopy(oldq)
newq['files']={n:p for n,p in newq['files'].items()if not n.startswith('frontend/emergency_pc/')};newq['files'].update({'frontend/emergency_pc/'+n:p for n,p in J(W/'workflow-pending-visibility-r178/full-build-result.json')['compiledFiles'].items()})
front={role:m.r32_frontend_manifest(newq['files'],role)for role in['security_pc','emergency_pc']}
contract={'revision':'exact-native-pending-operator-visibility-v1','component':'src/components/workflow/info.vue','componentSHA256':sha(T/'frontend/WorkflowInfoPendingVisibilityR178.vue'),'adapterSHA256':sha(T/'original_workflow_pending_visibility_r178.py'),'frontends':front,'exactCurrentUserProcessAndOperatorMembership':True,'pendingLookupFailureDoesNotOfferApproval':True,'originalAuthAuditAPIsAndInitiatorRulesRetained':True,'independentBeforeAddsignOpinionFixed':False}
text=prior.read_text(encoding='utf-8');start=text.index('def r33_project_header_bundle_contract(');end=text.index('def r32_avatar_bundle_contract(',start);func=text[start:end]
func=func.replace('def r33_project_header_bundle_contract(','def r34_pending_visibility_bundle_contract(')
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
func=once(func,'R33_HEADER_FIELD in release and release[R33_HEADER_FIELD] == R33_HEADER_CONTRACT','R34_PENDING_FIELD in release and release[R34_PENDING_FIELD] == R34_PENDING_CONTRACT')
func=once(func,"require(R33_HEADER_FIELD not in old, 'R33_REQUIRES_EXACT_PRE_HEADER_BASE')","require(old.get(R33_HEADER_FIELD) == R33_HEADER_CONTRACT and R34_PENDING_FIELD not in old, 'R34_REQUIRES_EXACT_R33_HEADER_BASE')")
func=once(func,'for role, expected in R33_OLD_FRONTENDS.items():',"for role, expected in R33_HEADER_CONTRACT['frontends'].items():")
func=once(func,"for role, expected in R33_HEADER_CONTRACT['frontends'].items():\n        require(r32_frontend_manifest(payload", "for role, expected in R34_PENDING_CONTRACT['frontends'].items():\n        require(r32_frontend_manifest(payload")
func=func.replace('R33_OLD_UPDATER_SHA','R34_OLD_UPDATER_SHA').replace("'publicAccepted',R33_HEADER_FIELD}","'publicAccepted',R34_PENDING_FIELD}")
func=func.replace("'R33_","'R34_").replace("'EXACT_R32_FRONTEND_BASE_REQUIRED:","'EXACT_R33_FRONTEND_BASE_REQUIRED:").replace("'EXACT_R33_COMPILED_FRONTEND_REQUIRED:","'EXACT_R34_COMPILED_FRONTEND_REQUIRED:").replace("'EXACT_R32_UPDATER_BASE_REQUIRED'","'EXACT_R33_UPDATER_BASE_REQUIRED'")
func=func.replace("'EXACT_R33_PROJECT_HEADER_DESCRIPTOR_REQUIRED'","'EXACT_R34_PENDING_VISIBILITY_DESCRIPTOR_REQUIRED'")
constants='R34_PENDING_FIELD = "nativeWorkflowPendingOperatorVisibility"\nR34_PENDING_CONTRACT = '+repr(contract)+'\nR34_OLD_UPDATER_SHA = '+repr(sha(prior))+'\n\n'
needle='def r32_avatar_bundle_contract(app, bundle, plan, old, release, payload):\n';assert text.count(needle)==1
text=text.replace(needle,constants+func+needle+"    if R34_PENDING_FIELD in release or R34_PENDING_FIELD in old:\n        return r34_pending_visibility_bundle_contract(app, bundle, plan, old, release, payload)\n",1)
before,after=ast.parse(prior.read_bytes()),ast.parse(text);functions=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};a,b=functions(before),functions(after)
assert set(b)-set(a)=={'r34_pending_visibility_bundle_contract'}and set(a)-set(b)==set()
assert {n for n in a if a[n]!=b[n]}=={'r32_avatar_bundle_contract'}
target.write_text(text,encoding='utf-8');D.mkdir()
proof={'newUpdaterSHA256':sha(target),'exactR33UpdaterSHA256':sha(prior),'onlyExistingFunctionChanged':'r32_avatar_bundle_contract','onlyNewFunction':'r34_pending_visibility_bundle_contract','allLifecycleNormalStopRestoreAndOtherFunctionsASTUnchanged':True,'contract':contract,'publicUploadedOrInstalled':False}
(D/'updater-source-comparison.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in proof.items()if k!='contract'}))
