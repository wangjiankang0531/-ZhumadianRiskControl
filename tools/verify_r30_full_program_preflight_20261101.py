from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';S=W/'r30-task-unified-candidate-r1';G=R/'_g/Application';OLD=W/'r28-duty-layout-candidate-r1/bundle';OUT=R/'work/r30gv-r1';C=R/'work/event_delivery_consistency_20261030/full-controller-r136';assert not OUT.exists()and not(G.parent/'user-manual-protected.json').exists()
J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
source=T/'original_public_test_update_r28_20261101.py';spec=importlib.util.spec_from_file_location('r27_full_program',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');new=J(S/'bundle/payload/release-manifest.json');newq=J(S/'bundle/payload/payload-manifest.json');publicPlan=J(S/'bundle/update-manifest.json');plan=copy.deepcopy(publicPlan);programs={};controllers={}
protected=[R/n for n in ['_c','_d','_e','_f']]
for name,pin in oldq['files'].items():
    if name=='private/server-configuration.json'or name.startswith('seed/mysql/'):continue
    assert not name.startswith(('private/','seed/','UserData/','Assets/','Reference/'))
    candidates=[G/name]
    if name.startswith('frontend/emergency_pc/'):candidates.insert(0,W/'emergency-workflow-source-r14/dist'/name.removeprefix('frontend/emergency_pc/'))
    matched=None
    for p in candidates:
        assert not any(root==p or root in p.parents for root in protected)
        if p.is_file()and p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']:m.regular(p.parent,p.name);matched=p;break
    assert matched is not None,'OLD_PROGRAM_UNRESOLVED:'+name
    programs[name]={'source':str(matched),**pin}
for name,pin in old['controllerFiles'].items():
    p=G/name
    assert sha(p)==pin;controllers[name]={'source':str(p),'bytes':p.stat().st_size,'sha256':pin}
logical=sum(pin['bytes']for pin in programs.values());free=shutil.disk_usage(R).free;assert free>2*1024**3
OUT.mkdir();app=OUT/'Application';bundle=OUT/'bundle';resolution={'allResolved':True,'programs':programs,'controllers':controllers,'logicalHardlinkProgramViewBytes':logical,'plannedAdditionalAllocatedBytesUpperBound':128*1024**2,'freeBytesBefore':free,'realPrivateSeedOrBusinessDataRead':False,'protectedUserRootsReadOrChanged':False};put(OUT/'dependency-resolution.json',enc(resolution))
private='private/server-configuration.json';fake=enc({'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False,'configuration':{'platform':{'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_preflight','spring.datasource.dynamic.primary':'jnpf','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'},'business':{'spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'}}});pin={'bytes':len(fake),'sha256':digest(fake)};oldq['files'][private]=copy.deepcopy(pin);newq['files'][private]=copy.deepcopy(pin);oldqraw=enc(oldq);newqraw=enc(newq);old['payloadManifestSHA256']=digest(oldqraw);new['payloadManifestSHA256']=digest(newqraw);oldraw=enc(old);newraw=enc(new)
plan.update(targetApplication=app.as_posix(),acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=new['payloadManifestSHA256'],newReleaseSHA256=digest(newraw));plan['files']['release-manifest.json']={'bytes':len(newraw),'SHA256':digest(newraw)};plan['files']['payload-manifest.json']={'bytes':len(newqraw),'SHA256':digest(newqraw)}
mutable=set(plan['files'])|set(plan['removedFrontendFiles']);linked=0;copied=0
for collection in [programs,controllers]:
    for name,pin in collection.items():
        p=Path(pin['source']);target=m.regular(app,name);target.parent.mkdir(parents=True,exist_ok=True)
        if name in mutable:shutil.copyfile(p,target);copied+=1
        else:os.link(p,target);linked+=1
put(app/private,fake);put(app/'payload-manifest.json',oldqraw);put(app/'release-manifest.json',oldraw)
for name,pin in plan['files'].items():
    if name=='release-manifest.json':put(bundle/'payload'/name,newraw)
    elif name=='payload-manifest.json':put(bundle/'payload'/name,newqraw)
    else:p=m.check_file(S/'bundle/payload',name,pin['SHA256'],pin['bytes']);target=bundle/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);os.link(p,target)
put(bundle/'update-manifest.json',enc(plan));bundlepin=sha(bundle/'update-manifest.json');print(json.dumps({'fullOldR28ProgramViewBuilt':True,'programFiles':len(programs),'logicalBytes':logical,'readOnlyHardlinks':linked,'mutableCopies':copied,'realPrivateOrDataCopied':False}),flush=True)
result,oldpin,changes=m.load_bundle(app,bundle,bundlepin,expected_target=app);assert oldpin==digest(oldraw)and set(changes)==set(publicPlan['files'])|set(publicPlan['removedFrontendFiles']);assert {n:v for n,v in result['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}=={n:v for n,v in publicPlan['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}
cases=[{'case':'complete-exact-R28-programs-and-20-controls-with-synthetic-private-only','passed':True}]
budget=m.candidate_runtime_pool_preflight(app,bundle,result);assert budget['budget']['mysqlMaxConnections']==24 and len(budget['budget']['datasources'])==3
cases.append({'case':'exact-candidate-original-generated-primary-budget-before-service-actions','passed':True})
for retained in [next(n for n in programs if n.startswith('runtime/jdk17/')and n not in mutable),next(iter(m.R26_TEAM_ROWS))]:
    f=app/retained;raw=f.read_bytes();m.atomic(f,raw+b'own-drift')
    try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
    except ValueError as e:assert str(e)=='FILE_PIN_MISMATCH:'+retained
    else:raise AssertionError('RETAINED_PROGRAM_DRIFT_ACCEPTED')
    assert sha(Path(programs[retained]['source']))==programs[retained]['sha256'];m.atomic(f,raw);cases.append({'case':'retained-source-drift-refused-with-source-unchanged:'+retained,'passed':True})
name=next(n for n in plan['files']if n.startswith('frontend/emergency_pc/')and n not in oldq['files']);assert not(app/name).exists();m.atomic(app/name,b'own unexpected preexisting new frontend path\n')
try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
except ValueError as e:assert str(e)=='NEW_PATH_ALREADY_EXISTS:'+name
else:raise AssertionError('UNEXPECTED_MAPPER_ALREADY_EXISTS_ACCEPTED')
(app/name).unlink();cases.append({'case':'preexisting-new-frontend-path-refused','passed':True})
assert sha(app/'release-manifest.json')==digest(oldraw)and sha(app/'payload-manifest.json')==digest(oldqraw)and all(sha(app/name)==pin['sha256']for name,pin in {**programs,**controllers}.items())
proof={'schema':'xnby.r30.full-program-preflight.v1','allPassed':True,'cases':cases,'fullProgramFilesVerified':len(programs),'fullProgramLogicalBytes':logical,'oldAndNewControllerFiles':20,'updaterSHA256':sha(source),'candidateInstallPaths':len(changes),'exactPublicProgramPinsAndRemovalsRetained':True,'syntheticPrivateAndLocalTargetManifestAdaptationsOnly':True,'realPublicPrivateIdentityOrIISPreflightPassed':False,'servicesOrDatabasesStarted':False,'protectedUserRootsReadOrChanged':False,'readOnlyHardlinks':linked,'mutableIndependentCopies':copied};put(OUT/'full-preflight-result.json',enc(proof));put(OUT/'fixture-changes.json',enc(changes));print(json.dumps(proof),flush=True)
