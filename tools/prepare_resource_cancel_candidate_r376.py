from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;W=R/'work/plan-resource-cancel-r375';D=R/'Document/Deployment/native_plan_six_relations_r372_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=J(W/'baseline/result.json');terminal=J(W/'baseline/terminal.json');outer=J(W/'baseline-outer-terminal.json')
assert baseline['passed']and baseline['actualUnhandledRejections']==6 and len(baseline['cases'])==9
assert terminal['chromeExitCode']==outer['nodeExitCode']==0 and outer['actualDescendantsZero']
spec=importlib.util.spec_from_file_location('own_cancel_patch',V/'original_plan_resource_cancel_compat_r376.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=W/'candidate-sources';assert not out.exists();out.mkdir()
actual=J(R/'work/user_feedback_20261031/plan-exercise-retained-r224/actual-compiled-source-files.json')
rows=[]
for kind in m.PINS:
    source=R/'Application/source-review/emergency-plan-exercise-r224'/m.BASE/(kind+'.vue');assert sha(source)==actual[m.BASE+kind+'.vue']['sha256']
    raw,proof=m.transform(kind,source.read_bytes());target=out/(kind+'.vue');target.write_bytes(raw);rows.append({'component':kind,'candidateSHA256':sha(target),**proof})
proof={'preparedOnly':True,'baselineRealComponentsNineCasesAndSixUnhandledRejectionsReproduced':True,'candidateComponents':rows,
 'moduleSHA256':sha(V/'original_plan_resource_cancel_compat_r376.py'),'onlyNormalCancelCloseCaughtUnexpectedErrorsPreserved':True,
 'fullSixComponent29CasesNotRun':True,'r373DriverSupersededBeforeAnyAllocationOrService':True,
 'r39AndPublic184FrozenBytesUnchanged':True,'publicFormalSceneOrDesktopChanged':False}
(D/'resource-cancel-candidate-r376.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
