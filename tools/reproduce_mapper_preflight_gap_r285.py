from pathlib import Path
from unittest.mock import patch
import copy,hashlib,importlib.util,json,os

R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
V=Path(__file__).resolve().parent
D=R/'Document/Deployment/original_mapper_install_preflight_r285_20261103'
F=V/'mapper-preflight-r285/Application'
S=T/'original_public_test_update_r38_unified_20261103.py'
B=R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='61b76c8eab5594cf4294cd40e0750af34b415891c2bbd3f7e5ef80bd34129eab'
assert not D.exists() and not F.exists()
D.mkdir();(F/'private').mkdir(parents=True)
spec=importlib.util.spec_from_file_location('actual_r38_candidate',S)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
plan=json.loads((B/'update-manifest.json').read_bytes())
fake={'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,
 'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False,
 'configuration':{'platform':{'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_preflight',
  'spring.datasource.dynamic.primary':'jnpf','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'},
 'business':{'spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:9/own_preflight',
 'spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:9/own_preflight',
 'spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'}},'businessArguments':[]}
canonical='classpath*:/xml/**/*.xml';cases=[]
def run(label,cfg,env):
    raw=(json.dumps(cfg,sort_keys=True)+'\n').encode();(F/'private/server-configuration.json').write_bytes(raw)
    with patch.dict(os.environ,env,clear=True):result=m.candidate_runtime_pool_preflight(F,B,plan)
    assert result['budget']['mysqlMaxConnections']==24
    assert result['configurationSHA256']==hashlib.sha256(raw).hexdigest()
    return {'case':label,'numericPoolPreflightAccepted':True,'mapperSettingShouldRequireValidation':True}

with patch.dict(os.environ,{},clear=True):
    for label,key,value in [('file-foreign','mybatis-plus.mapper-locations','classpath*:/unvalidated/**/*.xml'),
                            ('file-empty','mybatis-plus.mapperLocations','')]:
        cfg=copy.deepcopy(fake);cfg['configuration']['business'][key]=value;cases.append(run(label,cfg,{}))
    cases.append(run('environment-foreign',fake,{'MYBATIS_PLUS_MAPPER_LOCATIONS':'unvalidated'}))
    cfg=copy.deepcopy(fake);cfg['businessArguments']=['-Dmybatis-plus.mapper-locations=unvalidated'];cases.append(run('java-system-property-foreign',cfg,{}))
    cfg=copy.deepcopy(fake);cfg['businessArguments']=['--mybatis-plus.mapper-locations=unvalidated'];cases.append(run('application-argument-foreign',cfg,{}))
    # A valid wrapper input may change before apply_update makes its own snapshot.
    (F/'private/server-configuration.json').write_text(json.dumps(fake),encoding='utf-8')
    wrapper=R/'Document/Deployment/public_test_unified_mappers_r38_20261103/delivery/deploy_unified_mappers_r38.py'
    ns={'__file__':str(wrapper),'__name__':'wrapper_gate_reproduction'}
    exec(compile(wrapper.read_bytes(),str(wrapper),'exec'),ns)
    assert ns['verify_candidate_mapper_configuration'](F)['passed']
    cfg=copy.deepcopy(fake);cfg['configuration']['business']['mybatis-plus.mapper-locations']='unvalidated'
    (F/'private/server-configuration.json').write_text(json.dumps(cfg),encoding='utf-8')
    reached=[]
    def stop_before_services(*a,**kw):reached.append('owned_ready');raise RuntimeError('OWN_STOP_BEFORE_ANY_SERVICES')
    try:
        with patch.object(m,'load_bundle',lambda *a,**kw:(plan,'0'*64,{})),patch.object(m,'owned_ready',stop_before_services):
            m.apply_update(F,B,'0'*64)
    except RuntimeError as e:assert str(e)=='OWN_STOP_BEFORE_ANY_SERVICES'
    else:raise AssertionError('EXPECTED_SERVICE_ENTRY_WAS_NOT_OBSERVED')
    assert reached==['owned_ready']
    cases.append({'case':'configuration-changed-after-wrapper-gate-before-apply-snapshot',
      'actualApplyUpdateReachedOwnedReadyWithUnknownMapper':True,'ownedReadyReplacedByStopSpy':True})
proof={'gapReproduced':True,'cases':cases,'candidateSourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),
 'actualCandidateRuntimePoolPreflightExecuted':True,'applyUpdateReachedOnlyExplicitOwnedReadySpy':True,
 'actualServiceStopLaunchDatabaseOrPublicTouched':False,'realConfigurationOrCredentialsRead':False,
 'fixedR38DeliveryMustNotBePublishedUntilGuardStrengthened':True}
(D/'reproduction.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
(F/'private/server-configuration.json').write_text(json.dumps(fake),encoding='utf-8')
print(json.dumps({'gapReproduced':True,'cases':len(cases),'servicesOrPublicTouched':False}))
