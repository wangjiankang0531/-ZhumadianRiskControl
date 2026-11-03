from pathlib import Path
from unittest.mock import patch
import copy,hashlib,importlib.util,json,os
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/original_mapper_install_preflight_r285_20261103'
F=V/'mapper-install-gate-r287/Application';assert not F.exists();(F/'private').mkdir(parents=True)
B=R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle'
S=T/'original_public_test_update_r38_mapper_preflight_r286.py'
prep=json.loads((D/'candidate-preparation-r286.json').read_bytes());assert hashlib.sha256(S.read_bytes()).hexdigest()==prep['candidateSourceSHA256']
spec=importlib.util.spec_from_file_location('actual_candidate_with_mapper_snapshot',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
plan=json.loads((B/'update-manifest.json').read_bytes())
base=json.loads((V/'mapper-preflight-r285/Application/private/server-configuration.json').read_bytes())
assert base['syntheticPreflightFixtureOnly'] and base['servicesMustNotBeStartedFromThisFixture']
canonical='classpath*:/xml/**/*.xml';cases=[]
def put(cfg):
    raw=(json.dumps(cfg,sort_keys=True)+'\n').encode();(F/'private/server-configuration.json').write_bytes(raw);return raw
specimens=[('absent',None,None,None,True),('file-original','mybatis-plus.mapper-locations',canonical,None,True),
 ('file-camel','mybatis-plus.mapperLocations',canonical,None,True),('file-index','mybatis-plus.mapper-locations[0]',canonical,None,True),
 ('file-foreign','mybatis-plus.mapper-locations','unvalidated',None,False),('file-empty','mybatis-plus.mapperLocations','',None,False),
 ('file-list','mybatis-plus.mapper-locations',[canonical],None,False),('environment-original',None,None,{'MYBATIS_PLUS_MAPPER_LOCATIONS':canonical},True),
 ('environment-foreign',None,None,{'MYBATIS_PLUS_MAPPER_LOCATIONS':'unvalidated'},False),
 ('jvm-original',None,None,['-Dmybatis-plus.mapper-locations='+canonical],True),
 ('jvm-foreign',None,None,['-Dmybatis-plus.mapper-locations=unvalidated'],False),
 ('jvm-missing-equals',None,None,['-Dmybatis-plus.mapper-locations'],False),
 ('cli-original',None,None,['--mybatis-plus.mapper-locations='+canonical],True),
 ('cli-empty',None,None,['--mybatis-plus.mapper-locations='],False),
 ('conflicting-explicit-values','mybatis-plus.mapper-locations',canonical,['-Dmybatis-plus.mapper-locations=unvalidated'],False),
 ('argument-shape-non-list',None,None,'invalid-list-shape',False),
 ('argument-shape-non-string',None,None,[None],False)]
for label,key,value,extra,accepted in specimens:
    cfg=copy.deepcopy(base);env={}
    if key:cfg['configuration']['business'][key]=value
    if isinstance(extra,dict):env=extra
    elif extra is not None:cfg['businessArguments']=extra
    raw=put(cfg)
    with patch.dict(os.environ,env,clear=True):
        try:result=m.candidate_runtime_pool_preflight(F,B,plan)
        except ValueError as e:
            assert not accepted and str(e).startswith(('EXPLICIT_MAPPER_','MAPPER_BUSINESS_ARGUMENTS_'))
            cases.append({'case':label,'refusedBeforeServiceEntry':True})
        else:
            assert accepted and result['originalMapperPreflight']['passed']
            assert result['configurationSHA256']==hashlib.sha256(raw).hexdigest()
            assert not result['originalMapperPreflight']['settingValuesOrCredentialsReturned']
            assert result['budget']['mysqlMaxConnections']==24
            cases.append({'case':label,'acceptedWithSameSnapshotHash':True,'onlyBooleanMapperSummaryReturned':True})

# Invoke the real apply_update body. Identity/ingress are explicit spies; all
# service/lifecycle functions refuse to run. No claim of a six-component test.
def forbidden(*a,**kw):raise AssertionError('NO_ACTUAL_SERVICE_OR_MUTATION_ALLOWED')
def load_fixture(*a,**kw):return plan,'0'*64,{}
for label in ['already-foreign-at-apply','changed-after-preflight-before-stop']:
    cfg=copy.deepcopy(base)
    if label=='already-foreign-at-apply':cfg['configuration']['business']['mybatis-plus.mapper-locations']='unvalidated'
    put(cfg);events=[]
    def owned_fixture(*a,**kw):
        events.append('explicit-owned-ready-spy')
        changed=copy.deepcopy(base);changed['configuration']['business']['mybatis-plus.mapper-locations']='unvalidated';put(changed)
        return {'databaseUUID':'synthetic-identity-only'}
    def ingress_fixture(*a,**kw):events.append('explicit-ingress-spy');return None,None
    for name,value in [('UserData/OriginalServer/installation.json',{'releaseId':plan['releaseId'],'databaseUUID':'synthetic-identity-only'}),
                       ('UserData/OriginalDeployment/active-deployment.private.json',{'releaseId':plan['releaseId']})]:
        p=F/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8')
    try:
        with patch.dict(os.environ,{},clear=True),patch.object(m,'load_bundle',load_fixture),patch.object(m,'owned_ready',owned_fixture),patch.object(m,'ingress_preflight',ingress_fixture),patch.object(m,'normal_stop',forbidden),patch.object(m,'launch',forbidden),patch.object(m,'replace_code',forbidden):
            m.apply_update(F,B,'0'*64)
    except ValueError as e:
        expected='EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN'if label=='already-foreign-at-apply'else'CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP'
        assert str(e)==expected
        if label=='already-foreign-at-apply':assert events==[]
        else:assert events==['explicit-owned-ready-spy','explicit-ingress-spy']
    else:raise AssertionError('MAPPER_DRIFT_DID_NOT_REFUSE')
    cases.append({'case':label,'realApplyUpdateRefusedBeforeNormalStop':True,'explicitFixtureEvents':events})

# Legacy releases that have no original-mapper descriptor keep their old pool
# behavior; this addition must not change prior source configuration semantics.
legacy=copy.deepcopy(json.loads((B/'payload/release-manifest.json').read_bytes()));legacy.pop(m.R38_MAPPER_FIELD)
# Avoid pretending an invalid release is deployable: this is only the explicit
# descriptor predicate path, with its absence decision spied for pool preflight.
put(copy.deepcopy(base))
with patch.dict(os.environ,{},clear=True),patch.object(m,'original_mapper_defaults_declared',lambda candidate:False):
    result=m.candidate_runtime_pool_preflight(F,B,plan)
    assert result['originalMapperPreflight']is None and result['budget']['mysqlMaxConnections']==24
cases.append({'case':'legacy-absence-predicate-spy-does-not-add-mapper-restrictions','passed':True,'releaseDeployabilityNotAsserted':True})
proof={'passed':True,'checks':len(cases),'cases':cases,'candidateSourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),
 'actualCandidateSnapshotPreflightExecuted':True,'actualApplyUpdateBodyReachedOnlyExplicitIdentityIngressSpies':True,
 'sameConfigurationSnapshotAndPreStopHashCloseReportedGap':True,
 'actualSixComponentLifecycleOrIISTLSVerified':False,
 'databaseNetworkPublicDesktopOrRealCredentialsTouched':False,
 'fixedR38TransportStillNeedsRebuildAndVerification':True}
(D/'verified-cases-r287.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(cases),'bothRealApplyUpdateRefusalsBeforeStop':True,'actualServicesStarted':False}))
