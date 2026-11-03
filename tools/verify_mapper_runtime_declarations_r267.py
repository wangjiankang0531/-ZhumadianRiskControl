from pathlib import Path
import copy,json,importlib.util,hashlib
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/original_mapper_runtime_declarations_r267_20261103';assert not D.exists();D.mkdir()
source=T/'original_public_test_update_mapper_runtime_r265.py';spec=importlib.util.spec_from_file_location('mapper_declarations',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=copy.deepcopy(m.R37_STATIC_BASE_METADATA);new=copy.deepcopy(old);new['controllerFiles'][m.R24_PARAMETER]=m.R38_PARAMETER_PIN['sha256'];new[m.R38_MAPPER_FIELD]=copy.deepcopy(m.R38_MAPPER_CONTRACT);new[m.R24_WORKFLOW_FIELD]=m.workflow_contract_for(new)
payload=json.loads((R/'work/user_feedback_20261031/r37-static-performance-r1/bundle/payload/payload-manifest.json').read_bytes());cases=[]
assert m.runtime_pool_declared(old)and m.parameter_pin_for(old)==m.R27_POOL_PINS[m.R24_PARAMETER]and not m.original_mapper_defaults_declared(old);cases.append({'case':'legacy-original-parameter-and-pool-metadata-still-valid','passed':True})
assert m.runtime_pool_declared(new)and m.workflow_declared(new,payload)and m.parameter_pin_for(new)==m.R38_PARAMETER_PIN;cases.append({'case':'new-exact-parameter-pool-workflow-contract-valid','passed':True})
def reject(name,change,fn=None):
 r=copy.deepcopy(new);q=copy.deepcopy(payload);change(r,q)
 try:(fn or m.runtime_pool_declared)(r)
 except (ValueError,AssertionError,KeyError):cases.append({'case':name,'rejected':True});return
 raise AssertionError('INVALID_DECLARATION_ACCEPTED:'+name)
reject('new-parameter-without-explicit-mapper-contract',lambda r,q:r.pop(m.R38_MAPPER_FIELD))
reject('mapper-contract-revision-drift',lambda r,q:r[m.R38_MAPPER_FIELD].update(revision='unapproved'))
reject('old-parameter-source-under-new-contract',lambda r,q:r['controllerFiles'].update({m.R24_PARAMETER:m.R27_POOL_PINS[m.R24_PARAMETER]['sha256']}))
reject('foreign-parameter-source-under-new-contract',lambda r,q:r['controllerFiles'].update({m.R24_PARAMETER:'1'*64}))
reject('mapper-contract-invented-DDL',lambda r,q:r[m.R38_MAPPER_FIELD].update(newDatasourceOrDDL=True))
reject('mapper-contract-dropped-original-Jar-pin',lambda r,q:r[m.R38_MAPPER_FIELD].pop('originalBusinessJar'))
reject('pool-policy-missing',lambda r,q:r.pop(m.R27_POOL_FIELD))
reject('history-contract-missing',lambda r,q:r.pop(m.R36_HISTORY_FIELD))
r=copy.deepcopy(new);r[m.R24_WORKFLOW_FIELD]=copy.deepcopy(old[m.R24_WORKFLOW_FIELD])
try:m.workflow_declared(r,payload)
except ValueError:cases.append({'case':'old-workflow-parameter-pin-not-silently-reused','rejected':True})
else:raise AssertionError('OLD_WORKFLOW_DESCRIPTOR_ACCEPTED')
q=copy.deepcopy(payload);q['files'].pop(m.R24_TASK_CLASS)
try:m.workflow_declared(new,q)
except ValueError:cases.append({'case':'task-class-cannot-be-dropped-by-mapper-extension','rejected':True})
else:raise AssertionError('TASK_CLASS_DROP_ACCEPTED')
original=copy.deepcopy(m.R27_POOL_WORKFLOW_CONTRACT);m.workflow_contract_for(new);assert m.R27_POOL_WORKFLOW_CONTRACT==original;cases.append({'case':'legacy-global-workflow-contract-not-mutated','passed':True})
proof={'passed':True,'cases':cases,'updaterSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'lifecycleOrPublicTransportAcceptanceClaimed':False,'sqlOrNetworkOrCredentialsUsed':False}
(D/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'allInvalidContractsRejected':True,'publicTransportStillPending':True}))
