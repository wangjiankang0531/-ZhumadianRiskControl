from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';S=W/'r34-pending-visibility-candidate-r1';OLD=W/'r33-project-header-candidate-r1/bundle';G=R/'_g/Application';OUT=R/'work/r34gv-r1'
assert not OUT.exists()and not(G.parent/'user-manual-protected.json').exists();J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
source=T/'original_public_test_update_r34_20261102.py';spec=importlib.util.spec_from_file_location('r32_full_program',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');new=J(S/'bundle/payload/release-manifest.json');newq=J(S/'bundle/payload/payload-manifest.json');publicPlan=J(S/'bundle/update-manifest.json');plan=copy.deepcopy(publicPlan);programs={};controllers={}
for n,pin in oldq['files'].items():
 if n=='private/server-configuration.json'or n.startswith('seed/mysql/'):continue
 assert not n.startswith(('private/','seed/','UserData/','Assets/','Reference/'))
 p=((W/'avatar-full-r157/security_pc/build/dist'if n.split('/')[1]=='security_pc'else W/'project-header-home-r167/dist')/n.split('/',2)[2])if n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))else G/n;assert p.is_file()and p.stat().st_size==pin['bytes']and sha(p)==pin['sha256'];m.regular(p.parent,p.name);programs[n]={'source':str(p),**pin}
for n,pin in old['controllerFiles'].items():p=(T/'original_public_test_update_r33_20261102.py')if n=='tools/original_public_test_update.py'else G/n;assert sha(p)==pin;controllers[n]={'source':str(p),'bytes':p.stat().st_size,'sha256':pin}
logical=sum(p['bytes']for p in programs.values());free=shutil.disk_usage(R).free;budget=128*1024**2;assert free>budget+2*1024**3;OUT.mkdir();app=OUT/'Application';bundle=OUT/'bundle';put(OUT/'dependency-resolution.json',enc({'allResolved':True,'programs':programs,'controllers':controllers,'logicalHardlinkProgramViewBytes':logical,'plannedAdditionalAllocatedBytesUpperBound':budget,'freeBytesBefore':free,'realPrivateSeedOrBusinessDataRead':False,'protectedUserRootsReadOrChanged':False}))
private='private/server-configuration.json';fake=enc({'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False,'configuration':{'platform':{'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_preflight','spring.datasource.dynamic.primary':'jnpf','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'},'business':{'spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'}}});pin={'bytes':len(fake),'sha256':digest(fake)};oldq['files'][private]=copy.deepcopy(pin);newq['files'][private]=copy.deepcopy(pin);oldqraw=enc(oldq);newqraw=enc(newq);old['payloadManifestSHA256']=digest(oldqraw);new['payloadManifestSHA256']=digest(newqraw);oldraw=enc(old);newraw=enc(new)
plan.update(targetApplication=app.as_posix(),acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=new['payloadManifestSHA256'],newReleaseSHA256=digest(newraw));plan['files']['release-manifest.json']={'bytes':len(newraw),'SHA256':digest(newraw)};plan['files']['payload-manifest.json']={'bytes':len(newqraw),'SHA256':digest(newqraw)}
mutable=set(plan['files'])|set(plan['removedFrontendFiles']);linked=copied=0
for rows in [programs,controllers]:
 for n,p in rows.items():
  target=m.regular(app,n);target.parent.mkdir(parents=True,exist_ok=True)
  if n in mutable:shutil.copyfile(p['source'],target);copied+=1
  else:os.link(p['source'],target);linked+=1
put(app/private,fake);put(app/'payload-manifest.json',oldqraw);put(app/'release-manifest.json',oldraw)
for n,pin in plan['files'].items():
 if n=='release-manifest.json':put(bundle/'payload'/n,newraw)
 elif n=='payload-manifest.json':put(bundle/'payload'/n,newqraw)
 else:p=m.check_file(S/'bundle/payload',n,pin['SHA256'],pin['bytes']);target=bundle/'payload'/n;target.parent.mkdir(parents=True,exist_ok=True);os.link(p,target)
put(bundle/'update-manifest.json',enc(plan));bundlepin=sha(bundle/'update-manifest.json');print(json.dumps({'fullR31ProgramViewBuilt':True,'programFiles':len(programs),'logicalBytes':logical,'readOnlyHardlinks':linked,'mutableIndependentCopies':copied,'noRealConfigOrDatabaseCopied':True}),flush=True)
loaded,oldpin,changes=m.load_bundle(app,bundle,bundlepin,expected_target=app);assert oldpin==digest(oldraw)and set(changes)==set(publicPlan['files'])|set(publicPlan['removedFrontendFiles']);assert {n:p for n,p in loaded['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}=={n:p for n,p in publicPlan['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}
cases=[{'case':'full-R33-program-view-and-20-controls-exact-composition','passed':True}]
capacity=m.candidate_runtime_pool_preflight(app,bundle,loaded);assert capacity['budget']['mysqlMaxConnections']==24 and len(capacity['budget']['datasources'])==3;assert 'tools/original_server_release_parameters.py'not in loaded['files'];cases.append({'case':'exact-retained-candidate-parameters-and-primary-budget-before-services','passed':True})
bad=json.loads(fake);bad['configuration']['platform'].pop('spring.datasource.host');put(app/private,enc(bad))
try:m.candidate_runtime_pool_preflight(app,bundle,loaded)
except ValueError as e:assert str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'
else:raise AssertionError('BAD_PRIMARY_LAYOUT_ACCEPTED')
put(app/private,fake);cases.append({'case':'invalid-primary-layout-refused-with-no-service-action','passed':True})
for retained in [next(n for n in programs if n.startswith('runtime/jdk17/')and n not in mutable),next(iter(m.R26_TEAM_ROWS))]:
 p=app/retained;raw=p.read_bytes();m.atomic(p,raw+b'own-drift')
 try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
 except ValueError as e:assert str(e)=='FILE_PIN_MISMATCH:'+retained
 else:raise AssertionError('RETAINED_PROGRAM_DRIFT_ACCEPTED')
 assert sha(Path(programs[retained]['source']))==programs[retained]['sha256'];m.atomic(p,raw);cases.append({'case':'retained-program-drift-refused:'+retained,'passed':True})
name=next(n for n in plan['files']if n.startswith('frontend/emergency_pc/')and n not in oldq['files']);assert not(app/name).exists();m.atomic(app/name,b'own unexpected file\n')
try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
except ValueError as e:assert str(e)=='NEW_PATH_ALREADY_EXISTS:'+name
else:raise AssertionError('UNEXPECTED_NEW_FRONTEND_ALREADY_EXISTS_ACCEPTED')
(app/name).unlink();cases.append({'case':'preexisting-new-main-frontend-refused','passed':True})
assert (app/private).read_bytes()==fake and sha(app/'release-manifest.json')==digest(oldraw)and sha(app/'payload-manifest.json')==digest(oldqraw)and all(sha(app/n)==p['sha256']for n,p in {**programs,**controllers}.items())
proof={'schema':'xnby.r179.pending-visibility-full-program-preflight.v1','allPassed':True,'cases':cases,'fullProgramFilesVerified':len(programs),'fullProgramLogicalBytes':logical,'oldAndNewControlFiles':20,'updaterSHA256':sha(source),'candidateInstallPaths':len(changes),'actualR33ProgramAndR34CandidatePinsRetained':True,'onlySyntheticPrivateAndLocalTargetMetadataAdapted':True,'realPublicPrivateIdentityOrIISPreflightPassed':False,'servicesOrDatabasesStarted':False,'protectedUserRootsReadOrChanged':False,'readOnlyHardlinks':linked,'mutableIndependentCopies':copied,'sourceProgramsUnchanged':True};put(OUT/'full-preflight-result.json',enc(proof));put(OUT/'fixture-changes.json',enc(changes));print(json.dumps(proof),flush=True)
