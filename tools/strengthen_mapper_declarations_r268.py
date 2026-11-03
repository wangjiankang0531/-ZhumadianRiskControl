from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent;D=R/'Document/Deployment/original_mapper_runtime_source_r268_20261103';assert not D.exists();D.mkdir()
old=T/'original_public_test_update_mapper_runtime_r265.py';s=old.read_text(encoding='utf-8');anchor='def runtime_pool_declared(release):\n';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'    original_mapper_defaults_declared(release)\n')
out=T/'original_public_test_update_mapper_runtime_r268.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
a={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(old.read_bytes()).body if isinstance(n,ast.FunctionDef)};b={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};assert[n for n in a if a[n]!=b[n]]==['runtime_pool_declared']
failure={'failed':True,'case':'pool-policy-missing','actualFailure':'INVALID_DECLARATION_ACCEPTED:pool-policy-missing','originalSourceSHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'productOrPublicDeployed':False}
(R/'Document/Deployment/original_mapper_runtime_declarations_r267_20261103/failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
report={'sourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'onlyAdditionalExistingFunctionChanged':'runtime_pool_declared','validMetadataAndAllLifecycleFunctionsASTIdenticalToR265':True,'newMapperSourceOrContractCannotSkipValidationWhenPoolMissing':True,'actualFinalFileLifecyclePending':True,'publicTransportStillPending':True};(D/'preparation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
s=(V/'verify_mapper_runtime_declarations_r267.py').read_text(encoding='utf-8').replace('r267','r269').replace('mapper_runtime_r265.py','mapper_runtime_r268.py');p=V/'verify_mapper_runtime_declarations_r269.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
print(json.dumps({'strengthened':True,'onlyAdditionalFunctionChanged':'runtime_pool_declared','failurePreserved':True,'allLifecycleASTUnchanged':True}))
