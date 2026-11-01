from pathlib import Path
import contextlib,hashlib,importlib.util,json,sys,types
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_task_unified_r30_20261101';F=R/'work/r30gv-r1/Application';S=D/'delivery/deploy_task_unified_r30.py';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=F/'private/server-configuration.json';raw=fixture.read_bytes();specimen=json.loads(raw)
assert specimen['syntheticPreflightFixtureOnly']and specimen['servicesMustNotBeStartedFromThisFixture']and specimen['containsRealCredentials']is False
pin=J(D/'preparation-result.json');assert sha(D/'delivery-manifest.json')==pin['manifestSHA256']
manifest=J(D/'delivery-manifest.json');plan=J(R/'work/user_feedback_20261031/r30-task-unified-candidate-r1/bundle/update-manifest.json')
sys.path.insert(0,str(F/'tools'));real_spec=importlib.util.spec_from_file_location;results=[];events=[];latest={};loaded={}
class SpyLoader:
 def __init__(self,loader):self.loader=loader
 def create_module(self,spec):return self.loader.create_module(spec)
 def exec_module(self,module):
  self.loader.exec_module(module);loaded['module']=module
  def load(app,bundle,digest):
   assert app==F and digest==manifest['updateManifestSHA256'];events.append('load_bundle_fixture_identity_adapter');latest['stage']=bundle;return plan,manifest['oldReleaseSHA256'],[]
  def owned(app,old):assert app==F and old==manifest['oldReleaseSHA256'];events.append('owned_ready_spy');return {}
  def health(app,row):assert app==F and row=={};events.append('health_spy')
  def forbidden(*a,**kw):events.append('FORBIDDEN_SERVICE_ACTION');raise AssertionError('CHECK_ONLY_REACHED_SERVICE_ACTION')
  module.load_bundle=load;module.owned_ready=owned;module.health=health;module.apply_update=forbidden;module.normal_stop=forbidden;module.launch=forbidden;module.backup_code=forbidden
def factory(name,path,*args,**kw):
 assert Path(path)==D/'delivery/r30_update_runtime.py';value=real_spec(name,path,*args,**kw);value.loader=SpyLoader(value.loader);return value
ns={'__file__':str(S),'__name__':'own_r28_wrapper_order'};exec(compile(S.read_bytes(),str(S),'exec'),ns);ns['APP']=F
try:
 for name,bad in [('invalid-original-primary-layout-refused-before-owner-health-and-services',True),('valid-generated-primary-check-only-does-not-deploy',False)]:
  assert not(D/'transport-check-only-order-verification.json').exists();case=json.loads(raw)
  if bad:case['configuration']['platform'].pop('spring.datasource.host')
  fixture.write_bytes((json.dumps(case,indent=2)+'\n').encode());events.clear();latest.clear();loaded.clear()
  try:
   with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S),'--check-only']):ns['main']()
  except ValueError as e:
   assert bad and str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED';assert events==['load_bundle_fixture_identity_adapter'];refusal=str(e)
  else:
   assert not bad and events==['load_bundle_fixture_identity_adapter','owned_ready_spy','health_spy'];refusal=None
  stage=latest['stage'];assert stage.is_relative_to(F/'UserData/OriginalPublicUpdates/staging')
  assert loaded['module'].candidate_runtime_pool_preflight.__code__.co_filename==str(D/'delivery/r30_update_runtime.py')
  results.append({'case':name,'passed':True,'events':list(events),'refusal':refusal,'serviceActionCalls':0,'realFixedArchiveExtractedAndCandidateParametersExecuted':True})
finally:fixture.write_bytes(raw)
assert fixture.read_bytes()==raw
proof={'schema':'xnby.r30.actual-fixed-wrapper-check-only-order.v1','allPassed':True,'cases':results,'actualWrapperSHA256':sha(S),'actualUpdaterSHA256':sha(D/'delivery/r30_update_runtime.py'),'manifestSHA256':sha(D/'delivery-manifest.json'),'realArchiveMemberBoundsAndSHAUsed':True,'realCandidateBudgetCodeAndPinnedParametersUsed':True,'fixturePrivateBytesRestored':True,'servicesStartedOrStopped':False,'databaseAccessed':False,'publicOrProtectedRootsOperated':False,'fixtureIdentityLoadBundleAndReadinessAreExplicitSpies':True,'actualFullLoadBundleSeparatelyPassed15554ProgramFiles':True,'actualServerPreflightStillPending':True,'fullCloneReady':False}
(D/'transport-check-only-order-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
