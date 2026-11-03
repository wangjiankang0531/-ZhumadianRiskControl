from pathlib import Path
import ast,hashlib,json,importlib.util
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/original_mapper_product_runtime_r265_20261103';assert not D.exists();D.mkdir()
base=T/'original_public_test_update_r37_static_20261103.py';raw=base.read_bytes();assert hashlib.sha256(raw).hexdigest()=='52daac9f348be6622592920240794a1ba701d46683fa6b7c3e0cb34da47fcf62'
parameter=T/'original_server_release_parameters_r263_mapper_default.py';pin={'bytes':parameter.stat().st_size,'sha256':hashlib.sha256(parameter.read_bytes()).hexdigest()};assert pin['sha256']=='b804d7e29921fd70bab4db2f711d01175a35bf11a1a77dcf99a8d147e9f41471'
field='nativeOriginalXmlMapperDefaults';contract={'revision':'original-xml-mapper-default-v1','parameterAdapter':{'path':'tools/original_server_release_parameters.py',**pin},'originalBusinessJar':{'path':'payload/business/application.jar','bytes':1371849,'sha256':'363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'},'defaultResourcePattern':'classpath*:/xml/**/*.xml','expectedOriginalXMLResources':96,'expectedOriginalXMLStatements':226,'onlyWhenNoExplicitMapperLocations':True,'originalSQLBytesUnchanged':True,'newDatasourceOrDDL':False}
text=raw.decode('utf-8').replace('\r\n','\n')
addition='\nR38_MAPPER_FIELD='+repr(field)+'\nR38_PARAMETER_PIN='+repr(pin)+'\nR38_MAPPER_CONTRACT='+repr(contract)+'\n\n'+'''def original_mapper_defaults_declared(release):
    controls = release['controllerFiles']
    if R38_MAPPER_FIELD not in release:
        require(controls.get(R24_PARAMETER) != R38_PARAMETER_PIN['sha256'], 'EXPLICIT_ORIGINAL_MAPPER_DEFAULTS_REQUIRED')
        return False
    require(release[R38_MAPPER_FIELD] == R38_MAPPER_CONTRACT, 'EXACT_ORIGINAL_MAPPER_DEFAULT_CONTRACT_REQUIRED')
    require(controls.get(R24_PARAMETER) == R38_PARAMETER_PIN['sha256'], 'EXACT_ORIGINAL_MAPPER_PARAMETER_SOURCE_REQUIRED')
    require(release.get(R27_POOL_FIELD) == R27_POOL_POLICY and history_declared(release), 'ORIGINAL_MAPPER_REQUIRES_RETAINED_POOL_AND_HISTORY')
    return True

'''
anchor='def pool_control_pins(release):';assert text.count(anchor)==1;text=text.replace(anchor,addition+anchor)
a='    if history_declared(release):pins[R23_CONTROLLER]=R36_HISTORY_CONTROLLER_PIN\n    return pins';b='    if history_declared(release):pins[R23_CONTROLLER]=R36_HISTORY_CONTROLLER_PIN\n    if original_mapper_defaults_declared(release):pins[R24_PARAMETER]=R38_PARAMETER_PIN\n    return pins';assert text.count(a)==1;text=text.replace(a,b)
a='    return R27_POOL_WORKFLOW_CONTRACT if runtime_pool_declared(release)else R24_WORKFLOW_CONTRACT';b="    if runtime_pool_declared(release):\n        value=dict(R27_POOL_WORKFLOW_CONTRACT)\n        if original_mapper_defaults_declared(release):value['parameterAdapter']={'path':R24_PARAMETER,**R38_PARAMETER_PIN}\n        return value\n    return R24_WORKFLOW_CONTRACT";assert text.count(a)==1;text=text.replace(a,b)
a='    return R27_POOL_PINS[R24_PARAMETER]if runtime_pool_declared(release)else R24_PARAMETER_PIN';b='    return pool_control_pins(release)[R24_PARAMETER]if runtime_pool_declared(release)else R24_PARAMETER_PIN';assert text.count(a)==1;text=text.replace(a,b)
before={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)};after={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
changed=[n for n in before if before[n]!=after[n]];assert set(changed)=={'pool_control_pins','workflow_contract_for','parameter_pin_for'}
out=T/'original_public_test_update_mapper_runtime_r265.py';assert not out.exists();out.write_text(text,encoding='utf-8',newline='\n')
spec=importlib.util.spec_from_file_location('mapper_runtime',out);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report={'generated':True,'updaterSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'parameterPin':pin,'contract':contract,'onlyChangedExistingFunctions':changed,'allStopLaunchBackupReplaceRestoreAndRecoveryFunctionsASTIdentical':True,'publicTransportContractNotYetImplemented':True,'publicDeploymentOrCompleteLifecycleProven':False}
(D/'source-preparation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'generated':True,'onlyChangedRuntimeDeclarationFunctions':changed,'allLifecycleASTUnchanged':True,'publicBundleSupportNotYetImplemented':True}))
