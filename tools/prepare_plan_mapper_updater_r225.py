from pathlib import Path
import ast,hashlib,json,importlib.util
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
base=T/'original_public_test_update_r36_20261103_r2.py';raw=base.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca'
s=raw.decode('utf-8').replace('\r\n','\n');old_ast=ast.parse(s)
W=R/'work/user_feedback_20261031/plan-exercise-retained-r224';build=json.loads((W/'full-build-result.json').read_bytes());assert build['passed']and len(build['changedSourcePaths'])==14
spec=importlib.util.spec_from_file_location('old_updater',base);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
q={'frontend/emergency_pc/'+n:p for n,p in build['compiledFiles'].items()}
fronts={'security_pc':old.R35_PERSONAL_CONTRACT['frontends']['security_pc'],'emergency_pc':old.r32_frontend_manifest(q,'emergency_pc')}
plan_xml='payload/business/run-template/classes/mapper/EmergencyPlanMapper.xml'
rows={plan_xml:{'bytes':829,'sha256':'a4d921f1b007444e3618233035a5453c05dec8ae59f33eed46d045de3609425c'}}
payload=json.loads((R/'_g/Application/payload-manifest.json').read_bytes())['files']
source={n:payload[n] for n in ['payload/business/application.jar']}
contract={'revision':'original-plan-default-scan-v1','resources':rows,'retainedSources':source,'originalSQLUnchanged':True,'newDDLOrDatasource':False}
package={'revision':'retained-plan-exercise-and-task-attachment-v1','frontends':fronts,'changedCompiledSourcePaths':14,'actualCompiledSourceInventorySHA256':hashlib.sha256((W/'actual-compiled-source-files.json').read_bytes()).hexdigest(),'originalLoginWorkflowAndPermissionsRetained':True}
constants='\nR37_PLAN_FIELD = "nativeEmergencyPlanMapper"\nR37_PACKAGE_FIELD = "nativePlanExerciseRetainedFrontend"\nR37_PLAN_XML = '+repr(plan_xml)+'\nR37_PLAN_ROWS = '+repr(rows)+'\nR37_PLAN_SOURCE = '+repr(source)+'\nR37_PLAN_CONTRACT = '+repr(contract)+'\nR37_PACKAGE_CONTRACT = '+repr(package)+'\nR37_OLD_UPDATER_SHA = '+repr(hashlib.sha256(raw).hexdigest())+'\n\n'
functions=(V/'plan_mapper_contract_r225.txt').read_text(encoding='utf-8')
anchor='def team_declared(release, payload):';assert s.count(anchor)==1;s=s.replace(anchor,constants+functions+anchor)
oldline="<= set(R26_TEAM_ROWS), 'UNDECLARED_TEAM_MAPPER_RESOURCE_REFUSED')"
newline="<= set(R26_TEAM_ROWS) | (set(R37_PLAN_ROWS) if plan_mapper_declared(release, payload) else set()), 'UNDECLARED_TEAM_MAPPER_RESOURCE_REFUSED')"
assert s.count(oldline)==1;s=s.replace(oldline,newline)
anchor="        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),)"
# Insert only the precisely declared plan resource into the existing file-path gate.
actual="        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),"
assert s.count(actual)==1
s=s.replace(actual,"        allowed = allowed or (name in R37_PLAN_ROWS and plan_mapper_declared(read(bundle / 'payload/release-manifest.json'), read(bundle / 'payload/payload-manifest.json')))\n\n"+actual)
start=s.index('    r32_avatar_bundle_contract(app, bundle, plan, old, release, payload)',s.index('def load_bundle('))
end=s.index("    point_class = ",start);block=s[start:end]
new="    if any(field in release or field in old for field in [R37_PLAN_FIELD, R37_PACKAGE_FIELD]):\n        r37_plan_bundle_contract(app, bundle, plan, old, release, payload)\n    else:\n"+''.join('    '+line if line.strip()else line for line in block.splitlines(keepends=True))+'\n'
s=s[:start]+new+s[end:]
anchor='    runtime_pool_ready(app, row)';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n\n    plan_mapper_ready(app, row)')
new_ast=ast.parse(s);before={x.name:ast.dump(x,include_attributes=False)for x in old_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))};after={x.name:ast.dump(x,include_attributes=False)for x in new_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
changed={n for n in before if before[n]!=after.get(n)};assert changed=={'team_declared','load_bundle','health'},changed
out=T/'original_public_test_update_r37_plan_exercise_r225.py';assert not out.exists();out.write_text(s,encoding='utf-8')
D=R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103';D.mkdir(exist_ok=False)
proof={'generated':True,'updaterSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'onlyChangedExistingFunctions':sorted(changed),'allOtherLifecycleRecoveryAndOldContractFunctionsASTUnchanged':True,'originalPlanMapperContract':contract,'newFrontendContract':package,'actualLifecyclePreflightOrPublicAcceptanceProven':False}
(D/'updater-source-preparation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'generated':True,'updaterSHA256':proof['updaterSHA256'],'onlyChangedExistingFunctions':sorted(changed),'allOtherLifecycleRecoveryASTUnchanged':True}))
