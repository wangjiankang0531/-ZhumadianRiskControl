from pathlib import Path
import ast,hashlib,json,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;T=R/'Application/tools';W=R/'work/user_feedback_20261031/plan-resource-cancel-r378'
sys.path.insert(0,str(T));sys.dont_write_bytecode=True
import build_avatar_full_r157_20261102 as base
J=lambda p:json.loads(p.read_bytes());terminal=J(W/'build-terminal.json')
assert terminal['nodeExitCode']==134 and terminal['actualDescendantsZeroBeforeClose']and J(W/'source-restored.json')['allSevenOverrideLayersRestored']
assert'JavaScript heap out of memory'in(W/'build.private.log').read_text(encoding='utf-8',errors='replace')
origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'
assert base.inventory(W/'source')==base.inventory(origin)and not(W/'source/node_modules').exists()
text=(V/'build_plan_resource_cancel_r378.py').read_text(encoding='utf-8')
text=text.replace('memory[2]>3*1024**3','memory[2]>6*1024**3').replace('FULL_FRONTEND_BUILD_REQUIRES_THREE_GIB_AVAILABLE','FULL_FRONTEND_BUILD_RETRY_REQUIRES_SIX_GIB_AVAILABLE')
a="W=R/'work/user_feedback_20261031/plan-resource-cancel-r378';P=W/'source';assert not W.exists();W.mkdir()"
b="ROOT=R/'work/user_feedback_20261031/plan-resource-cancel-r378';W=ROOT/'retry-r2';P=ROOT/'source';assert not W.exists();W.mkdir()"
assert text.count(a)==1;text=text.replace(a,b,1)
a="before=base.own_copy(R/'work/user_feedback_20261031/emergency-workflow-source-r17/source',P)"
b="before=base.inventory(P);assert before==base.inventory(R/'work/user_feedback_20261031/emergency-workflow-source-r17/source')"
assert text.count(a)==1;text=text.replace(a,b,1).replace('build_plan_resource_cancel_r378.mjs','build_plan_resource_cancel_r380.mjs').replace('max-old-space-size=768','max-old-space-size=2048').replace("'nodeHeapLimitMiB':768","'nodeHeapLimitMiB':2048")
ast.parse(text);out=V/'build_plan_resource_cancel_r380.py';assert not out.exists();out.write_text(text,encoding='utf-8')
node=(V/'build_plan_resource_cancel_r378.mjs').read_text(encoding='utf-8')
a="W=R+'/work/user_feedback_20261031/plan-resource-cancel-r378',P=W+'/source'"
b="W=R+'/work/user_feedback_20261031/plan-resource-cancel-r378/retry-r2',P=R+'/work/user_feedback_20261031/plan-resource-cancel-r378/source'"
assert node.count(a)==1;node=node.replace(a,b,1);js=V/'build_plan_resource_cancel_r380.mjs';assert not js.exists();js.write_text(node,encoding='utf-8')
proof={'preparedOnly':True,'priorActualNodeHeapOOMExit134AndDescendantsZero':True,'allSevenSourceLayersExactRestored':True,
 'existingSourceCopyReusedNoNewFullSourceCopy':True,'retryOwnRoot':str(W/'retry-r2'),'nodeHeapLimitMiB':2048,'availableMemoryAdmissionGiB':6,
 'baselineSixComponentGuardNotLowered':True,'pythonSourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'nodeSourceSHA256':hashlib.sha256(js.read_bytes()).hexdigest(),
 'frozenR39Public184RuntimeAndDatabaseChanged':False}
D=R/'Document/Deployment/native_plan_six_relations_r372_20261103';(D/'retained-build-heap-refusal-r378.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
