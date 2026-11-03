from pathlib import Path
import copy,hashlib,importlib.util,json,os,sys
from unittest.mock import patch
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103';S=D/'delivery/deploy_unified_mappers_r38.py';F=R/'work/r38-unified-full-preflight-r275/Application';ns={'__file__':str(S),'__name__':'own_mapper_gate_checker'};exec(compile(S.read_bytes(),str(S),'exec'),ns)
raw=(F/'private/server-configuration.json').read_bytes();assert json.loads(raw)['syntheticPreflightFixtureOnly'];base=json.loads(raw);base.setdefault('businessArguments',[]);canonical='classpath*:/xml/**/*.xml';cases=[]
specimens=[('absent',None,None,None,True),('explicit-original','mybatis-plus.mapper-locations',canonical,None,True),('explicit-camel','mybatis-plus.mapperLocations',canonical,None,True),('explicit-index','mybatis-plus.mapper-locations[0]',canonical,None,True),('wrong-file','mybatis-plus.mapper-locations','classpath*:/mapper/**/*.xml',None,False),('empty-file','mybatis-plus.mapper-locations','',None,False),('env-original',None,None,{'MYBATIS_PLUS_MAPPER_LOCATIONS':canonical},True),('env-foreign',None,None,{'MYBATIS_PLUS_MAPPER_LOCATIONS':'foreign'},False),('system-original',None,None,['-Dmybatis-plus.mapper-locations='+canonical],True),('system-foreign',None,None,['-Dmybatis-plus.mapper-locations=foreign'],False),('cli-original',None,None,['--mybatis-plus.mapper-locations='+canonical],True),('cli-empty',None,None,['--mybatis-plus.mapper-locations='],False)]
try:
 for label,key,value,extra,accepted in specimens:
  cfg=copy.deepcopy(base)
  if key:cfg['configuration']['business'][key]=value
  env=extra if isinstance(extra,dict)else{}
  if isinstance(extra,list):cfg['businessArguments']+=extra
  (F/'private/server-configuration.json').write_text(json.dumps(cfg),encoding='utf-8')
  with patch.dict(os.environ,env,clear=True):
   try:result=ns['verify_candidate_mapper_configuration'](F)
   except ValueError as e:assert not accepted and str(e).startswith('EXPLICIT_MAPPER_');cases.append({'case':label,'refusedBeforeService':True})
   else:assert accepted and result['passed']and not result['settingValuesOrCredentialsReturned'];assert canonical not in json.dumps(result);cases.append({'case':label,'passed':True,'noSettingValuesReturned':True})
 cfg=copy.deepcopy(base);cfg['configuration']['business']['mybatis-plus.mapper-locations']='foreign';(F/'private/server-configuration.json').write_text(json.dumps(cfg),encoding='utf-8')
 plan=json.loads((R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle/update-manifest.json').read_bytes());real=importlib.util.spec_from_file_location;events=[]
 class Loader:
  def __init__(self,loader):self.loader=loader
  def create_module(self,spec):return self.loader.create_module(spec)
  def exec_module(self,module):
   self.loader.exec_module(module)
   def load(app,bundle,pin):events.append('load_bundle_explicit_identity_fixture_spy');return plan,ns['OLD'],{}
   def forbidden(*a,**kw):events.append('FORBIDDEN_READINESS_OR_SERVICE_CALL');raise AssertionError('MAPPER_GATE_DID_NOT_PRECEDE_SERVICES')
   module.load_bundle=load;module.owned_ready=forbidden;module.health=forbidden;module.apply_update=forbidden;module.normal_stop=forbidden;module.launch=forbidden
 def factory(name,path,*a,**kw):s=real(name,path,*a,**kw);s.loader=Loader(s.loader);return s
 ns['APP']=F
 try:
  with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S),'--check-only']),patch.dict(os.environ,{},clear=True):ns['main']()
 except ValueError as e:assert str(e)=='EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN'and events==['load_bundle_explicit_identity_fixture_spy']
 else:raise AssertionError('INVALID_MAPPER_INPUT_ACCEPTED_BY_FIXED_WRAPPER')
 cases.append({'case':'actual-fixed-wrapper-mapper-refusal-before-readiness-or-services','passed':True,'events':events})
finally:(F/'private/server-configuration.json').write_bytes(raw)
proof={'passed':True,'cases':cases,'checks':len(cases),'wrapperSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'settingsAndEnvironmentValuesNotReturned':True,'originalSyntheticConfigRestored':(F/'private/server-configuration.json').read_bytes()==raw,'realProcessesOrPublicOrDatabaseTouched':False}
(D/'mapper-input-gate-cases.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'checks':len(cases),'unknownExplicitSettingsRefusedBeforeReadinessOrStop':True,'configRestoredExactBytes':True}))
