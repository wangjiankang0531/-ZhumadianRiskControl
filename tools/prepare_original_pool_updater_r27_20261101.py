from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent;D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101'
old=T/'original_public_test_update_r26_20261101.py';raw=old.read_bytes();assert hashlib.sha256(raw).hexdigest()=='6307a61826e4d77b4b5381e10f97ecff0d6ec76f54d90fa01e2a9ff4915b2f5a';s=raw.decode('utf-8')
spec=importlib.util.spec_from_file_location('exact_old_pool_contract',old);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
policy={'revision':'pool-family-budget-v1','mysqlMinimum':24,'mysqlMaximum':256,'reservedConnections':12,'maximumSinglePool':128};pins={}
for name in ['serve_original_server_release.py','original_server_release_parameters.py']:
    p=T/'connection-budget-r136'/name;pins['tools/'+name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
workflow=copy.deepcopy(m.R24_WORKFLOW_CONTRACT);workflow['revision']='original-task-short-temp-and-pool-budget-v1';workflow['parameterAdapter']={'path':m.R24_PARAMETER,**pins[m.R24_PARAMETER]}
block="R27_POOL_FIELD='runtimeConnectionPoolPolicy'\nR27_POOL_POLICY="+repr(policy)+"\nR27_POOL_PINS="+repr(pins)+"\nR27_POOL_WORKFLOW_CONTRACT="+repr(workflow)+'\n\n'+(V/'runtime_pool_contract_r27.fragment.py').read_text(encoding='utf-8')+'\n\n'
anchor='def team_declared(';assert s.count(anchor)==1;s=s.replace(anchor,block+anchor)
def replace(a,b,count=1):
    global s
    assert s.count(a)==count,(a,s.count(a));s=s.replace(a,b)
replace("    require(release.get(R24_WORKFLOW_FIELD) == R24_WORKFLOW_CONTRACT", "    require(release.get(R24_WORKFLOW_FIELD) == workflow_contract_for(release)")
replace("    require(release[R24_WORKFLOW_FIELD] == R24_WORKFLOW_CONTRACT,", "    require(release[R24_WORKFLOW_FIELD] == workflow_contract_for(release),")
replace("and release['controllerFiles'].get(R24_PARAMETER) == R24_PARAMETER_PIN['sha256'],", "and release['controllerFiles'].get(R24_PARAMETER) == parameter_pin_for(release)['sha256'],")
replace("require(old[R24_WORKFLOW_FIELD] == R24_WORKFLOW_CONTRACT\n                and old['controllerFiles'].get(R24_PARAMETER) == R24_PARAMETER_PIN['sha256'],", "require(old[R24_WORKFLOW_FIELD] == workflow_contract_for(old)\n                and old['controllerFiles'].get(R24_PARAMETER) == parameter_pin_for(old)['sha256'],")
replace("for name, pin in ((R24_TASK_CLASS, R24_TASK_PIN), (R24_PARAMETER, R24_PARAMETER_PIN)):", "for name, pin in ((R24_TASK_CLASS, R24_TASK_PIN), (R24_PARAMETER, parameter_pin_for(release))):")
replace("    check_file(app, R24_PARAMETER, R24_PARAMETER_PIN['sha256'], R24_PARAMETER_PIN['bytes'])", "    parameter_pin=parameter_pin_for(release)\n    check_file(app, R24_PARAMETER, parameter_pin['sha256'], parameter_pin['bytes'])")
replace("expected = {R23_CONTROLLER: R23_CONTROLLER_SHA, helper:","expected = {R23_CONTROLLER: controller_pin_for(release), helper:")
replace("expected[R24_PARAMETER] = R24_PARAMETER_PIN['sha256']","expected[R24_PARAMETER] = parameter_pin_for(release)['sha256']")
replace("for name, pin in ((R23_CONTROLLER, R23_CONTROLLER_SHA), (R23_ASYNC_HELPER, R23_HELPER_SHA), (R23_JOB, R23_JOB_SHA)):","for name, pin in ((R23_CONTROLLER, controller_pin_for(release)), (R23_ASYNC_HELPER, R23_HELPER_SHA), (R23_JOB, R23_JOB_SHA)):")
replace("    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))", "    if runtime_pool_declared(release):legal.update(R27_POOL_PINS)\n    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))",2)
replace('    async_bundle_contract(app, bundle, plan, old, release, payload)', '    runtime_pool_bundle_contract(app, bundle, plan, old, release, payload)\n    async_bundle_contract(app, bundle, plan, old, release, payload)')
replace('    team_ready(app, row)\n','    team_ready(app, row)\n    runtime_pool_ready(app, row)\n')
ast.parse(s);p=T/'original_public_test_update_r27_20261101.py';assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
old_functions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};new_functions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};changed=[n for n in old_functions if old_functions[n]!=new_functions[n]]
assert not set(changed)&{'stop_owned','backup_code','replace_code','restore_code','rollback_latest','recover_pending','apply_update','launch','server_lock','installed_overlay'}
(D/'pool-updater-source-comparison.json').write_text(json.dumps({'oldSHA256':hashlib.sha256(raw).hexdigest(),'newSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'changedFunctions':changed,'normalLifecycleAndRecoveryASTUnchanged':True,'exactOldContractBranchesRetained':True,'newPolicyExactTwoSourcesBound':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'newUpdaterWritten':True,'changedFunctions':changed,'lifecycleAndRecoveryUnchanged':True}))
