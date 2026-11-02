from pathlib import Path
import hashlib,importlib.util,json,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_avatar_r32_20261102';F=R/'work/r32gv-r1/Application';S=D/'delivery/deploy_avatar_r32.py';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=F/'private/server-configuration.json';raw=fixture.read_bytes();specimen=json.loads(raw);assert specimen['syntheticPreflightFixtureOnly']and specimen['servicesMustNotBeStartedFromThisFixture']and not specimen['containsRealCredentials'];assert not(D/'transport-order-verification.json').exists()
manifest=J(D/'delivery-manifest.json');plan=J(R/'work/user_feedback_20261031/r32-avatar-candidate-r1/bundle/update-manifest.json');real_spec=importlib.util.spec_from_file_location;events=[];latest={};loaded={};cases=[]
class Loader:
 def __init__(self,base):self.base=base
 def create_module(self,spec):return self.base.create_module(spec)
 def exec_module(self,module):
  self.base.exec_module(module);loaded['module']=module
  def load(app,bundle,pin):assert app==F and pin==manifest['updateManifestSHA256'];events.append('load_bundle_explicit_fixture_identity_spy');latest['stage']=bundle;return plan,manifest['oldReleaseSHA256'],[]
  def owned(app,pin):assert app==F and pin==manifest['oldReleaseSHA256'];events.append('owned_ready_explicit_spy');return {}
  def health(app,row):assert app==F and row=={};events.append('health_explicit_spy')
  def forbidden(*a,**kw):events.append('FORBIDDEN_MUTATION_OR_SERVICE_ACTION');raise AssertionError('CHECK_ONLY_MUTATED')
  module.load_bundle=load;module.owned_ready=owned;module.health=health;module.apply_update=forbidden;module.normal_stop=forbidden;module.launch=forbidden;module.backup_code=forbidden
def factory(name,path,*args,**kw):
 assert Path(path)==D/'delivery/r32_update_runtime.py';value=real_spec(name,path,*args,**kw);value.loader=Loader(value.loader);return value
ns={'__file__':str(S),'__name__':'own_r32_fixed_wrapper_order'};exec(compile(S.read_bytes(),str(S),'exec'),ns);ns['APP']=F
try:
 for label,bad in [('invalid-original-primary-layout-before-owner-health-and-services',True),('valid-retained-primary-check-only-never-deploys',False)]:
  config=json.loads(raw)
  if bad:config['configuration']['platform'].pop('spring.datasource.host')
  fixture.write_bytes((json.dumps(config,indent=2)+'\n').encode());events.clear();latest.clear();loaded.clear()
  try:
   with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S),'--check-only']):ns['main']()
  except ValueError as e:assert bad and str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'and events==['load_bundle_explicit_fixture_identity_spy'];refusal=str(e)
  else:assert not bad and events==['load_bundle_explicit_fixture_identity_spy','owned_ready_explicit_spy','health_explicit_spy'];refusal=None
  assert latest['stage'].is_relative_to(F/'UserData/OriginalPublicUpdates/staging');assert loaded['module'].candidate_runtime_pool_preflight.__code__.co_filename==str(D/'delivery/r32_update_runtime.py');cases.append({'case':label,'passed':True,'events':list(events),'refusal':refusal,'serviceActionCalls':0,'realFixedArchiveExtractedAndExactRetainedParameterCodeExecuted':True})
finally:fixture.write_bytes(raw)
assert fixture.read_bytes()==raw;proof={'schema':'xnby.r158.actual-fixed-wrapper-order.v1','allPassed':True,'cases':cases,'wrapperSHA256':sha(S),'updaterSHA256':sha(D/'delivery/r32_update_runtime.py'),'manifestSHA256':sha(D/'delivery-manifest.json'),'realFixedArchiveAndCandidateBudgetUsed':True,'identityAndReadinessExplicitSpies':True,'actualFullLoadBundleSeparatelyPassed15554ProgramFiles':True,'fixtureConfigurationBytesRestored':True,'servicesOrDatabasesStarted':False,'publicOrProtectedRootsOperated':False,'actualPublicServerPreflightStillPending':True};(D/'transport-order-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
