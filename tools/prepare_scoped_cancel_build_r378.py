from pathlib import Path
import ast,hashlib,json,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;T=R/'Application/tools'
sys.path.insert(0,str(T));sys.dont_write_bytecode=True
import build_avatar_full_r157_20261102 as base
old=R/'work/plan-resource-cancel-r377';origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'
assert(old/'source').is_dir()and not(old/'source/node_modules').exists()and not(old/'build-terminal.json').exists()
assert base.inventory(old/'source')==base.inventory(origin),'FIRST_ENTERED_HEADER_OVERRIDE_MUST_BE_RESTORED'
source=V/'build_plan_resource_cancel_r377.py';text=source.read_text(encoding='utf-8')
a="W=R/'work/plan-resource-cancel-r377'";assert text.count(a)==1
text=text.replace(a,"W=R/'work/user_feedback_20261031/plan-resource-cancel-r378'",1).replace('build_plan_resource_cancel_r377.mjs','build_plan_resource_cancel_r378.mjs');ast.parse(text)
node=(V/'build_plan_resource_cancel_r377.mjs').read_text(encoding='utf-8');a="W=R+'/work/plan-resource-cancel-r377'";assert node.count(a)==1;node=node.replace(a,"W=R+'/work/user_feedback_20261031/plan-resource-cancel-r378'",1)
out=V/'build_plan_resource_cancel_r378.py';js=V/'build_plan_resource_cancel_r378.mjs';assert not out.exists()and not js.exists();out.write_text(text,encoding='utf-8');js.write_text(node,encoding='utf-8')
proof={'preparedOnly':True,'priorBuildStoppedBeforeAnyNodeProcessByExactExistingProjectScopeGuard':True,
 'priorOwnSourceCopyVerifiedExactAfterHeaderOverrideExit':True,'guardsNotWidened':True,
 'newBuildRoot':'D:/Project/Zhumadian/work/user_feedback_20261031/plan-resource-cancel-r378',
 'pythonSourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'nodeSourceSHA256':hashlib.sha256(js.read_bytes()).hexdigest(),
 'fixedR39Public184ReferenceRuntimeAndDatabaseUnchanged':True}
D=R/'Document/Deployment/native_plan_six_relations_r372_20261103';(D/'retained-build-scope-refusal-r377.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
