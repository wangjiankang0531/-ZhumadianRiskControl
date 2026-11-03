from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/original_mapper_install_preflight_r285_20261103'
base=T/'original_public_test_update_r38_unified_20261103.py'
out=T/'original_public_test_update_r38_mapper_preflight_r286.py'
assert not out.exists()
assert hashlib.sha256(base.read_bytes()).hexdigest()=='61b76c8eab5594cf4294cd40e0750af34b415891c2bbd3f7e5ef80bd34129eab'
helper='''def candidate_original_mapper_preflight(configuration):
    """Validate the same bounded config snapshot that is pinned before shutdown."""
    business = configuration['configuration']['business']
    require(isinstance(business, dict), 'MAPPER_CONFIGURATION_SHAPE_REQUIRED')
    def mapper_key(key):
        return isinstance(key, str) and re.fullmatch(
            r'mybatisplusmapperlocations(?:\\[[0-9]+\\])?',
            re.sub(r'[-_.]', '', key).lower()) is not None
    values = [value for key, value in business.items() if mapper_key(key)]
    values.extend(value for key, value in os.environ.items() if mapper_key(key))
    arguments = configuration.get('businessArguments', [])
    require(isinstance(arguments, list) and all(isinstance(a, str) for a in arguments),
            'MAPPER_BUSINESS_ARGUMENTS_SHAPE_REQUIRED')
    for argument in arguments:
        if argument.startswith(('-D', '--')):
            key, separator, value = argument[2:].partition('=')
            if mapper_key(key):
                require(separator == '=', 'EXPLICIT_MAPPER_ARGUMENT_VALUE_REQUIRED')
                values.append(value)
    require(not values or all(isinstance(v, str) and v == 'classpath*:/xml/**/*.xml' for v in values),
            'EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN')
    return {'passed': True, 'defaultWillApply': not values,
            'explicitOriginalPatternRetained': bool(values),
            'settingValuesOrCredentialsReturned': False}


'''
s=base.read_text(encoding='utf-8')
anchor='def candidate_runtime_pool_preflight(app, bundle, plan):';assert s.count(anchor)==1
s=s.replace(anchor,helper+anchor)
anchor="    module = types.ModuleType('owned_candidate_numeric_parameters')"
assert s.count(anchor)==1
s=s.replace(anchor,"    mapper_input = (candidate_original_mapper_preflight(configuration)\n"
 "                    if original_mapper_defaults_declared(candidate) else None)\n\n"+anchor)
anchor="            'candidateParametersSHA256': candidate['controllerFiles'][name]}"
assert s.count(anchor)==1
s=s.replace(anchor,"            'candidateParametersSHA256': candidate['controllerFiles'][name],\n"
 "            'originalMapperPreflight': mapper_input}")
before={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(base.read_bytes()).body if isinstance(n,ast.FunctionDef)}
after={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
changed=[n for n in before if before[n]!=after[n]]
assert changed==['candidate_runtime_pool_preflight']
assert set(after)-set(before)=={'candidate_original_mapper_preflight'}
out.write_text(s,encoding='utf-8',newline='\n')
proof={'prepared':True,'baseSourceSHA256':hashlib.sha256(base.read_bytes()).hexdigest(),
 'candidateSourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'existingFunctionsChanged':changed,'newHelper':'candidate_original_mapper_preflight',
 'sameRawConfigurationSnapshotUsedForPoolMapperAndPreStopHash':True,
 'applyStopLaunchReplaceRestoreRecoveryFunctionsUnchanged':True,
 'fixedR38PackageNotRebuiltOrAuthorizedForThisPrototype':True,
 'runtimeVerificationPending':True,'publicOrDatabaseOrDesktopTouched':False}
(D/'candidate-preparation-r286.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
