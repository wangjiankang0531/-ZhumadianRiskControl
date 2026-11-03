from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103';S=D/'delivery/deploy_unified_mappers_r38.py';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(D/'delivery-manifest-r279-draft.json').exists();(D/'delivery-manifest-r279-draft.json').write_bytes((D/'delivery-manifest.json').read_bytes());(D/'deploy-wrapper-r279-draft.py').write_bytes(S.read_bytes())
function='''
def verify_candidate_mapper_configuration(app):
    # Read only in memory; never return setting values or credentials.
    cfg=json.loads(regular(app/'private/server-configuration.json').read_bytes())
    business=cfg['configuration']['business'];need(isinstance(business,dict),'MAPPER_CONFIGURATION_SHAPE_REQUIRED')
    def mapper_key(key):return re.fullmatch(r'mybatisplusmapperlocations(?:\\[[0-9]+\\])?',re.sub(r'[-_.]','',key).lower())is not None
    explicit=[value for key,value in business.items()if mapper_key(key)]
    explicit.extend(value for key,value in os.environ.items()if mapper_key(key))
    for argument in cfg.get('businessArguments',[]):
        if argument.startswith('-D')or argument.startswith('--'):
            key,separator,value=argument[2:].partition('=')
            if mapper_key(key):need(separator=='=','EXPLICIT_MAPPER_ARGUMENT_VALUE_REQUIRED');explicit.append(value)
    need(not explicit or all(isinstance(value,str)and value=='classpath*:/xml/**/*.xml'for value in explicit),'EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN')
    return {'passed':True,'defaultWillApply':not explicit,'explicitOriginalPatternRetained':bool(explicit),'settingValuesOrCredentialsReturned':False}

'''
s=S.read_text(encoding='utf-8');assert s.count('def main():')==1;s=s.replace('def main():',function+'def main():')
anchor="    need(candidate_pool is not None,'EXACT_CANDIDATE_POOL_PREFLIGHT_REQUIRED')";assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    mapper_input=verify_candidate_mapper_configuration(APP)\n    print('R38_ORIGINAL_XML_CONFIGURATION_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)");ast.parse(s);S.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode())
manifest=J(D/'delivery-manifest.json');manifest['files'][S.name]={'bytes':S.stat().st_size,'sha256':sha(S)};manifest['mapperConfigurationGateBeforeAnyShutdown']=True;raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();(D/'delivery-manifest.json').write_bytes(raw);(D/'delivery/delivery-manifest.json').write_bytes(raw)
prepared=J(D/'preparation-result.json');prepared['manifestSHA256']=sha(D/'delivery-manifest.json');prepared['transportBytes']=sum(p.stat().st_size for p in(D/'delivery').iterdir());prepared['draftR279NotForExecution']=True;(D/'preparation-result.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'mapperInputGateAddedBeforeReadinessAndStop':True,'finalTransportFiles':prepared['transportFiles'],'finalTransportBytes':prepared['transportBytes'],'finalManifestSHA256':prepared['manifestSHA256'],'payloadAndUpdaterSourceUnchanged':True}))
