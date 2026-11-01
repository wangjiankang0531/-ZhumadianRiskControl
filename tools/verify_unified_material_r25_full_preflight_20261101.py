"""Exact R24 program view -> R25 load_bundle; synthetic private config only, no services."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';S=W/'r25-material-unified-candidate-r1';BASE=W/'r24-unified-candidate-r1'
OUT=R/'work/r25gv-r1';assert not OUT.exists();OUT.mkdir();app=OUT/'Application';bundle=OUT/'bundle'
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
updater=T/'original_public_test_update_r25_20261101.py';spec=importlib.util.spec_from_file_location('own_r25_full_preflight',updater);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldbundle=BASE/'sparse-graceful-update-preparation-r1/bundle';prepared=S/'bundle';public_plan=read(prepared/'update-manifest.json');plan=copy.deepcopy(public_plan)
old=read(oldbundle/'payload/release-manifest.json');oldq=read(oldbundle/'payload/payload-manifest.json');new=read(prepared/'payload/release-manifest.json');newq=read(prepared/'payload/payload-manifest.json')
prior=read(R/'work/r24gv-r1/dependency-resolution.json');assert prior['allResolved']and not prior['realPrivateConfigurationRead']
protected=[R/p for p in ['_c','_d','_e','_f']];programs={};controllers={};missing=[]
def resolve(name,pin,candidates):
    for path in candidates:
        if path is None:continue
        path=Path(path).absolute();assert not any(p==path or p in path.parents for p in protected),'PROTECTED_SOURCE_REFUSED'
        if path.is_file()and path.stat().st_size==pin['bytes']and sha(path)==pin['sha256']:
            m.regular(path.parent,path.name);return {'source':str(path),**pin}
    missing.append(name);return None
for name,pin in oldq['files'].items():
    if name=='private/server-configuration.json'or name.startswith('seed/mysql/'):continue
    assert not name.startswith(('private/','UserData/','seed/')),'UNEXPECTED_NONPROGRAM_ROW'
    previous=prior['programs'].get(name)
    row=resolve(name,pin,[BASE/'payload'/name,oldbundle/'payload'/name,previous['source']if previous and previous['sha256']==pin['sha256']else None])
    if row:programs[name]=row
for name,h in old['controllerFiles'].items():
    previous=prior['controllers'].get(name);candidates=[BASE/'graceful-public-control'/name]
    if previous and previous['sha256']==h:candidates.append(previous['source'])
    row=None
    for path in candidates:
        p=Path(path)
        if p.is_file()and sha(p)==h:
            row=resolve(name,{'bytes':p.stat().st_size,'sha256':h},[p]);break
    if row:controllers[name]=row
    else:missing.append(name)
assert not missing,{'unresolvedProgramNames':missing}
logical=sum(p['bytes']for p in programs.values());free=shutil.disk_usage(OUT).free;assert free>2*1024**3
resolution={'schema':'xnby.r25.program-dependency-resolution.v1','allResolved':True,'programs':programs,'controllers':controllers,
    'resolvedProgramFiles':len(programs),'resolvedProgramBytes':logical,'realPrivateConfigurationRead':False,'realSeedOrBusinessDataRead':False,
    'logicalHardlinkProgramViewBytes':logical,'plannedAdditionalAllocatedBytesUpperBound':128*1024**2,'freeBytesBefore':free}
put(OUT/'dependency-resolution.json',enc(resolution))
private='private/server-configuration.json';fake=enc({'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,
    'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False});pin={'bytes':len(fake),'sha256':digest(fake)}
oldq['files'][private]=copy.deepcopy(pin);newq['files'][private]=copy.deepcopy(pin)
oldqraw=enc(oldq);newqraw=enc(newq);old['payloadManifestSHA256']=digest(oldqraw);new['payloadManifestSHA256']=digest(newqraw);oldraw=enc(old);newraw=enc(new)
plan.update(targetApplication=app.as_posix(),acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
    basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=new['payloadManifestSHA256'],newReleaseSHA256=digest(newraw))
plan['files']['release-manifest.json']={'bytes':len(newraw),'SHA256':digest(newraw)};plan['files']['payload-manifest.json']={'bytes':len(newqraw),'SHA256':digest(newqraw)}
mutable=set(plan['files'])|set(plan['removedFrontendFiles']);linked=0;copied=0
for collection in [programs,controllers]:
    for n,pin in collection.items():
        source=Path(pin['source']);target=m.regular(app,n);target.parent.mkdir(parents=True,exist_ok=True)
        if n in mutable:shutil.copyfile(source,target);copied+=1
        else:os.link(source,target);linked+=1
put(app/private,fake);put(app/'payload-manifest.json',oldqraw);put(app/'release-manifest.json',oldraw)
for n,pin in plan['files'].items():
    if n=='release-manifest.json':put(bundle/'payload'/n,newraw)
    elif n=='payload-manifest.json':put(bundle/'payload'/n,newqraw)
    else:
        source=m.check_file(prepared/'payload',n,pin['SHA256'],pin['bytes']);target=bundle/'payload'/n;target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
put(bundle/'update-manifest.json',enc(plan));bundlepin=sha(bundle/'update-manifest.json')
print(json.dumps({'phase':'complete-R24-program-view-created','programs':len(programs),'logicalBytes':logical,'hardlinks':linked,'mutableIndependentCopies':copied,'realPrivateOrSeedRead':False}),flush=True)
result,oldpin,changes=m.load_bundle(app,bundle,bundlepin,expected_target=app)
assert oldpin==digest(oldraw)and set(changes)==set(public_plan['files'])|set(public_plan['removedFrontendFiles'])
assert {n:v for n,v in result['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}=={n:v for n,v in public_plan['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}
cases=[{'case':'full-exact-R24-program-view-and-owned-private-config','passed':True}]
retained=next(n for n in programs if n.startswith('runtime/jdk17/')and n not in mutable);f=app/retained;raw=f.read_bytes();source=Path(programs[retained]['source']);m.atomic(f,raw+b'own-drift')
try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
except ValueError as e:assert str(e)=='FILE_PIN_MISMATCH:'+retained
else:raise AssertionError('RETAINED_DEPENDENCY_DRIFT_ACCEPTED')
assert sha(source)==programs[retained]['sha256'];m.atomic(f,raw);cases.append({'case':'retained-dependency-drift-refused-source-unchanged','passed':True})
for n in m.R25_MATERIAL_ROWS:
    assert not(app/n).exists();m.atomic(app/n,b'own preexisting unexpected material override\n')
    try:m.load_bundle(app,bundle,bundlepin,expected_target=app)
    except ValueError as e:assert str(e)=='NEW_PATH_ALREADY_EXISTS:'+n
    else:raise AssertionError('PREEXISTING_MATERIAL_CLASS_ACCEPTED')
    (app/n).unlink();cases.append({'case':'unexpected-new-material-override-refused-'+n,'passed':True})
assert sha(app/'release-manifest.json')==digest(oldraw)and sha(app/'payload-manifest.json')==digest(oldqraw)
assert all(sha(app/n)==pin['sha256']for n,pin in {**programs,**controllers}.items())
proof={'schema':'xnby.r25.full-program-preflight.v1','allPassed':True,'cases':cases,'updaterSHA256':sha(updater),'fullProgramFilesVerified':len(programs),
    'fullProgramBytesVerified':logical,'oldControllerFilesVerified':len(controllers),'newControllerFilesVerified':len(new['controllerFiles']),
    'candidateInstallPaths':len(changes),'exactPublicProgramPinsAndRemovalsRetained':True,'privateConfigurationUsesOwnSyntheticBytes':True,
    'manifestIdentityAdaptedForSyntheticConfigAndLocalTarget':True,'actualPublicReleaseAndPrivateIdentityPreflightPassed':False,
    'realPrivateConfigurationOrSeedOrBusinessRead':False,'protectedUserPreviewReadOrChanged':False,'readOnlyProgramHardlinks':linked,
    'mutableFilesIndependentlyCopied':copied,'servicesStartedOrStopped':False,'publicOrFormalChanged':False,'publicControllerWholeLifecycleActuallyExecuted':False}
put(OUT/'full-preflight-result.json',enc(proof));put(OUT/'fixture-changes.json',enc(changes));print(json.dumps(proof),flush=True)
