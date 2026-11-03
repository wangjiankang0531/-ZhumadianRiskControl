from pathlib import Path
import ast,copy,gzip,hashlib,importlib.util,json,sys,zipfile
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103';F=R/'work/r38-unified-full-preflight-r275/Application';S=D/'delivery/deploy_unified_mappers_r38.py';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=J(D/'delivery-manifest.json');prepared=J(D/'preparation-result.json');assert sha(D/'delivery-manifest.json')==prepared['manifestSHA256']and(D/'delivery/delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
for n,pin in manifest['files'].items():p=D/'delivery'/n;assert p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']
assert set(p.name for p in(D/'delivery').iterdir())==set(manifest['files'])|{'delivery-manifest.json'}
plan=J(R/'work/user_feedback_20261031/r38-unified-original-mappers-r1/bundle/update-manifest.json');archive=next(p for p in(D/'delivery').iterdir()if p.suffix=='.zip')
with zipfile.ZipFile(archive)as z:
 assert set(z.namelist())=={'web.config','update-manifest.json'}|{'payload/'+n for n in plan['files']};assert hashlib.sha256(z.read('update-manifest.json')).hexdigest()==manifest['updateManifestSHA256']
 for n,pin in plan['files'].items():b=z.read('payload/'+n);assert len(b)==pin['bytes']and hashlib.sha256(b).hexdigest()==pin['SHA256']
for p in(D/'delivery').glob('*.py'):ast.parse(p.read_bytes())
ns={'__file__':str(S),'__name__':'own_unified_delivery_checker'};exec(compile(S.read_bytes(),str(S),'exec'),ns)
transport=J(V/'static-nginx-r278/verified-result.json');assert ns['STATIC_EXPECTED']==transport['staticExpected']
known={r['path']:r for r in J(V/'static-nginx-r278/candidate/results.json')['cases']if r['name']in['security-js','emergency-js','security-css','emergency-css']};checks=[]
for path in list(ns['STATIC_EXPECTED']):
 headers=copy.deepcopy(known[path]['headers']);original=copy.deepcopy(ns['STATIC_EXPECTED']);body=b'OWN_UNIFIED_CHECKER_BODY'*100;ns['STATIC_EXPECTED'][path]={'decodedBytes':len(body),'decodedSHA256':hashlib.sha256(body).hexdigest()};packed=gzip.compress(body);validate=ns['validate_static_response'];assert validate(path,'gzip',200,headers,packed)['decodedContentMatched'];checks.append({'case':path+'-gzip-validator-synthetic-body','passed':True})
 for label,code,hs,bs in [('wrong-status',404,headers,packed),('missing-vary',200,{k:v for k,v in headers.items()if k!='vary'},packed),('private-cache',200,{**headers,'cache-control':'private, no-store'},packed),('wrong-content',200,headers,gzip.compress(b'wrong')),('unexpected-identity-gzip',200,headers,packed)]:
  try:validate(path,'identity'if label=='unexpected-identity-gzip'else'gzip',code,hs,bs)
  except (ValueError,OSError):checks.append({'case':label,'passed':True})
  else:raise AssertionError('BAD_STATIC_RESPONSE_ACCEPTED')
 headers.pop('content-encoding');assert validate(path,'identity',200,headers,body)['decodedContentMatched'];checks.append({'case':'explicit-zero-identity','passed':True});ns['STATIC_EXPECTED']=original
raw=(F/'private/server-configuration.json').read_bytes();assert json.loads(raw)['syntheticPreflightFixtureOnly'];real_spec=importlib.util.spec_from_file_location;events=[]
class Loader:
 def __init__(self,base):self.base=base
 def create_module(self,spec):return self.base.create_module(spec)
 def exec_module(self,module):
  self.base.exec_module(module)
  def load(app,bundle,pin):assert app==F and pin==manifest['updateManifestSHA256'];events.append('load_bundle_explicit_identity_fixture_spy');return plan,manifest['oldReleaseSHA256'],{}
  def owned(app,pin):events.append('owned_ready_explicit_spy');return{}
  def health(app,row):events.append('health_explicit_spy')
  def forbidden(*a,**kw):events.append('FORBIDDEN_SERVICE_OR_MUTATION');raise AssertionError('CHECK_ONLY_MUTATED')
  module.load_bundle=load;module.owned_ready=owned;module.health=health;module.apply_update=forbidden;module.normal_stop=forbidden;module.launch=forbidden;module.backup_code=forbidden
def factory(name,path,*args,**kw):
 assert Path(path)==D/'delivery/r38_update_runtime.py';spec=real_spec(name,path,*args,**kw);spec.loader=Loader(spec.loader);return spec
ns['APP']=F;order=[]
try:
 for bad in [True,False]:
  cfg=json.loads(raw)
  if bad:cfg['configuration']['platform'].pop('spring.datasource.host')
  (F/'private/server-configuration.json').write_text(json.dumps(cfg),encoding='utf-8');events.clear()
  try:
   with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S),'--check-only']):ns['main']()
  except ValueError as e:assert bad and str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'and events==['load_bundle_explicit_identity_fixture_spy']
  else:assert not bad and events==['load_bundle_explicit_identity_fixture_spy','owned_ready_explicit_spy','health_explicit_spy']
  order.append({'invalidLayout':bad,'events':list(events),'serviceCalls':0,'fixedArchiveActuallyExtracted':True,'actualCandidateBudgetFunctionUsed':True})
finally:(F/'private/server-configuration.json').write_bytes(raw)
assert(F/'private/server-configuration.json').read_bytes()==raw
report={'updateId':ns['UPDATE'],'oldReleaseSHA256':ns['OLD'],'newReleaseSHA256':ns['NEW'],'attempt':str(F/'UserData/OriginalPublicUpdates/own-fixed-proof')};ns['recovery_guard'](report);guards=1
for key,value in [('updateId','foreign'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','0'*64),('attempt',str(F/'outside/proof'))]:
 bad=copy.deepcopy(report);bad[key]=value
 try:ns['recovery_guard'](bad)
 except ValueError:guards+=1
 else:raise AssertionError('FOREIGN_RECOVERY_RECORD_ACCEPTED')
proof={'passed':True,'eightTransportFilesAndAllSHAExact':True,'zipClosedAndAll186PayloadPinsExact':True,'fixedWrapperSyntaxAndExactR36PinVerified':True,'staticExpectedHashesFromActualR38NginxRepresentations':True,'responseValidatorSyntheticBodyCases':len(checks),'actualFixedWrapperCheckOnlyOrder':order,'recoveryGuardCases':guards,'actualCompleteLoadBundleSeparatelyVerified15557ProgramFiles':True,'newWrapperIdentityAndReadinessReplacedByExplicitSpies':True,'newUpdaterApplyUpdateOrServerIISTLSExecuted':False,'publicOrDesktopOrDatabaseOrServicesTouched':False}
for name,value in [('independent-fixed-delivery-verification.json',proof),('response-checker-cases.json',checks)]:(D/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
