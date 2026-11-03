"""Exact R36 program view, synthetic config, complete final R37 load_bundle."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';OLD=W/'r36-native-history-candidate-r2/bundle';S=R/'work/r39-plan-runtime-unified-r1/r36';G=R/'_g/Application';O=R/'work/r39-full-preflight-r36-r339';D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103/r36'
assert not O.exists() and not (G.parent/'user-manual-protected.json').exists()
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest()
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
source=T/'original_public_test_update_r39_plan_runtime_r337.py';spec=importlib.util.spec_from_file_location('r37_full',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(OLD/'payload/release-manifest.json');q=J(OLD/'payload/payload-manifest.json');new=J(S/'bundle/payload/release-manifest.json');publicPlan=J(S/'bundle/update-manifest.json');plan=copy.deepcopy(publicPlan);programs={};controls={}
def resolve(n,pin,control=False):
 if n.startswith('frontend/security_pc/'):candidates=[W/'avatar-full-r157/security_pc/build/dist'/n.split('/',2)[2]]
 elif n.startswith('frontend/emergency_pc/'):candidates=[W/'personal-workflow-routes-r195/dist'/n.split('/',2)[2]]
 else:candidates=[OLD/'payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]
 for p in candidates:
  if p.is_file()and p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']:m.regular(p.parent,p.name);return p
 raise ValueError('UNRESOLVED_R36_PROGRAM:'+n)
for n,pin in q['files'].items():
 if n=='private/server-configuration.json'or n.startswith('seed/mysql/'):continue
 assert not n.startswith(('private/','UserData/','Assets/','Reference/','seed/'))
 p=resolve(n,pin);programs[n]={'source':str(p),**pin}
for n,pin in old['controllerFiles'].items():
 for p in [OLD/'payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]:
  if p.is_file()and sha(p)==pin:break
 else:raise ValueError('UNRESOLVED_R36_CONTROL:'+n)
 controls[n]={'source':str(p),'bytes':p.stat().st_size,'sha256':pin}
live='iis/App_Code/XnbyReferenceProxy.cs';controls[live]=copy.deepcopy(controls['deploy/iis_original/App_Code/XnbyReferenceProxy.cs'])
budget=128*1024**2;free=shutil.disk_usage(R).free;assert free>budget+2*1024**3;O.mkdir();app=O/'Application';bundle=O/'bundle'
put(O/'resolution.json',enc({'programs':programs,'controls':controls,'newAllocatedBytesBudget':budget,'freeBefore':free,'logicalHardlinkProgramBytes':sum(p['bytes']for p in programs.values()),'privateConfigSeedAssetsOrBusinessDataRead':False}))
private='private/server-configuration.json';fake=enc({'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False,'configuration':{'platform':{'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_preflight','spring.datasource.dynamic.primary':'jnpf','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'},'business':{'spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'}}})
q['files'][private]={'bytes':len(fake),'sha256':digest(fake)};qraw=enc(q);old['payloadManifestSHA256']=digest(qraw)
newq=J(S/'bundle/payload/payload-manifest.json');newq['files'][private]={'bytes':len(fake),'sha256':digest(fake)};newqraw=enc(newq);new['payloadManifestSHA256']=digest(newqraw);oldraw=enc(old);newraw=enc(new)
plan.update(targetApplication=app.as_posix(),acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':digest(qraw),'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=digest(qraw),newPayloadManifestSHA256=digest(newqraw),newReleaseSHA256=digest(newraw))
plan['files']['release-manifest.json']={'bytes':len(newraw),'SHA256':digest(newraw)};plan['files']['payload-manifest.json']={'bytes':len(newqraw),'SHA256':digest(newqraw)}
mutable=set(plan['files'])|set(plan['removedFrontendFiles']);linked=copied=0
for n,pin in {**programs,**controls}.items():
 target=m.regular(app,n);target.parent.mkdir(parents=True,exist_ok=True)
 if n in mutable:shutil.copyfile(pin['source'],target);copied+=1
 else:os.link(pin['source'],target);linked+=1
put(app/private,fake);put(app/'release-manifest.json',oldraw);put(app/'payload-manifest.json',qraw)
for n,pin in plan['files'].items():put(bundle/'payload'/n,newraw if n=='release-manifest.json'else newqraw if n=='payload-manifest.json'else(S/'bundle/payload'/n).read_bytes())
put(bundle/'update-manifest.json',enc(plan));pin=sha(bundle/'update-manifest.json')
print(json.dumps({'fullR36ViewBuilt':True,'programFiles':len(programs),'readOnlyHardlinks':linked,'mutableCopies':copied,'syntheticConfigOnly':True}),flush=True)
loaded,oldpin,changes=m.load_bundle(app,bundle,pin,expected_target=app);assert oldpin==digest(oldraw)and len(changes)==len(plan['files'])+len(plan['removedFrontendFiles'])
capacity=m.candidate_runtime_pool_preflight(app,bundle,loaded);assert capacity['budget']['mysqlMaxConnections']==24 and len(capacity['budget']['datasources'])==3;assert capacity['originalMapperPreflight']['passed']and capacity['originalMapperPreflight']['defaultWillApply']
assert m.native_plan_runtime_declared(new,newq)and len(loaded['acceptedOldReleases'])==1
checks=[{'case':'all-R36-programs-and-final-R39-unified-path-load_bundle','passed':True},{'case':'exact-retained-pool-budget-before-any-services','passed':True}]
# A retained hardlink is changed with atomic replace, never in-place.
for n in [next(n for n in programs if n.startswith('runtime/jdk17/')and n not in mutable),next(iter(m.R26_TEAM_ROWS))]:
 p=app/n;before=p.read_bytes();m.atomic(p,before+b'own drift')
 try:m.load_bundle(app,bundle,pin,expected_target=app)
 except ValueError as e:assert str(e)=='FILE_PIN_MISMATCH:'+n
 else:raise AssertionError('RETAINED_DRIFT_ACCEPTED')
 assert sha(Path(programs[n]['source']))==programs[n]['sha256'];m.atomic(p,before);checks.append({'case':'retained-source-drift-refused:'+n,'passed':True})
p=app/live;before=p.read_bytes();m.atomic(p,b'own foreign IIS edit')
try:m.load_bundle(app,bundle,pin,expected_target=app)
except ValueError as e:assert str(e)=='UNKNOWN_OLD_ENTRY_SCRIPT'
else:raise AssertionError('UNKNOWN_IIS_FILE_ACCEPTED')
m.atomic(p,before);checks.append({'case':'live-IIS-source-drift-refused-before-stop','passed':True})
bad=copy.deepcopy(json.loads(fake));bad['configuration']['platform'].pop('spring.datasource.host');put(app/private,enc(bad))
try:m.candidate_runtime_pool_preflight(app,bundle,loaded)
except ValueError as e:assert str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'
else:raise AssertionError('BAD_POOL_LAYOUT_ACCEPTED')
put(app/private,fake);checks.append({'case':'invalid-platform-layout-refused-before-stop','passed':True})
assert all(sha(app/n)==p['sha256']for n,p in {**programs,**controls}.items())and(app/private).read_bytes()==fake
result={'allPassed':True,'fullProgramFilesVerified':len(programs),'oldDeclaredControls':len(old['controllerFiles']),'newDeclaredControls':22,'liveIISProxyExtraPinVerified':True,'candidateInstallPaths':len(plan['files']),'obsoleteEmergencyFrontendRemovals':len(plan['removedFrontendFiles']),'allChangePaths':len(changes),'cases':checks,'newUpdaterSHA256':sha(source),'readOnlyHardlinks':linked,'mutableIndependentCopies':copied,'sourceProgramsUnchanged':True,'onlyLocalTargetAndSyntheticPrivateManifestMetadataAdapted':True,'publicDeliveryWrapperNotPreparedYet':True,'internalSameSnapshotMapperGatePassed':True,'candidatePlanClassContractAndTransportPassed':True,'baselineVariant':'R36','realConfigDatabaseOrAccountRecordsRead':False,'servicesStarted':False,'actualServerPreflightOrIISOrPublicDeploymentPassed':False}
put(D/'full-program-preflight.json',enc(result));put(O/'verified-result.json',enc(result));print(json.dumps(result),flush=True)
