from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;T=R/'Application/tools';D=R/'Document/Deployment/emergency_pool_layout_r139_20261101';S=R/'work/user_feedback_20261031/r27-duty-pool-candidate-r1/bundle/payload/tools'
out=D/'candidate-sources-r3';assert not out.exists();out.mkdir(parents=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
policy=(V/'original_connection_pool_policy_r139_20261101.py').read_text(encoding='utf-8');ast.parse(policy)
old=(S/'original_server_release_parameters.py').read_text(encoding='utf-8');a=old.index('"""Resolve bounded numeric pool settings');b=old.index('def materialize(',a);new=old[:a]+policy+'\n\n'+old[b:];ast.parse(new);raw=new.encode();pin=sha(raw);(out/'original_server_release_parameters.py').write_bytes(raw)
controller=(S/'serve_original_server_release.py').read_bytes();(out/'serve_original_server_release.py').write_bytes(controller)
source=(S/'original_public_test_update.py').read_text(encoding='utf-8');source=source.replace('f849b0ed52e281d7568831ec8a2097b882a64887b8e6cf7da2ec46adfa196dc6',pin).replace('pool-family-budget-v1','pool-family-budget-v2')
lines=source.splitlines(keepends=True)
for node in reversed(ast.parse(source).body):
    if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):continue
    name=node.targets[0].id
    if name not in ['R27_POOL_PINS','R27_POOL_WORKFLOW_CONTRACT']:continue
    value=ast.literal_eval(node.value)
    if name=='R27_POOL_PINS':value['tools/original_server_release_parameters.py'].update(bytes=len(raw),sha256=pin)
    else:value['parameterAdapter'].update(bytes=len(raw),sha256=pin)
    lines[node.lineno-1:node.end_lineno]=[name+'='+repr(value)+'\n']
source=''.join(lines)
fragment=(V/'runtime_pool_preflight_r139.fragment.py').read_text(encoding='utf-8');assert 'def candidate_runtime_pool_preflight(' not in source;source=source.replace('def apply_update(app, bundle, pin):',fragment+'\ndef apply_update(app, bundle, pin):')
needle='    plan, old_pin, changes = load_bundle(app, bundle, pin)';assert source.count(needle)==1;source=source.replace(needle,needle+'\n    candidate_pool = candidate_runtime_pool_preflight(app, bundle, plan)')
needle='        normal_stop(app, old_pin, row)';assert source.count(needle)==1;source=source.replace(needle,"        if candidate_pool is not None:\n            require(sha(regular(app, 'private/server-configuration.json')) == candidate_pool['configurationSHA256'],\n                    'CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP')\n"+needle)
ast.parse(source);(out/'original_public_test_update.py').write_bytes(source.replace('\n','\r\n').encode('utf-8'))
def functions(s):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
oldfn=functions((S/'original_public_test_update.py').read_text(encoding='utf-8'));newfn=functions(source)
same=['normal_stop','backup_code','replace_code','restore_code','rollback_latest','recover_pending','launch'];assert all(oldfn[n]==newfn[n]for n in same)
proof={'schema':'xnby.r139.pool-layout-source-candidate.v1','policySHA256':sha(policy.encode()),'parameterSHA256':pin,'controllerSHA256':sha(controller),'updaterSHA256':sha((out/'original_public_test_update.py').read_bytes()),'normalLifecycleBackupAndRecoveryFunctionsASTUnchanged':same,'preflightBeforeOwnedReadyBackupOrStop':True,'configurationDigestRecheckedBeforeNormalStop':True,'runtimeInstalled':False,'publicDeployed':False}
(D/'candidate-source-pins-r3.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
for name in ['original_connection_pool_policy_r139_20261101.py','runtime_pool_preflight_r139.fragment.py']: (T/name).write_bytes((V/name).read_bytes())
print(json.dumps(proof))
