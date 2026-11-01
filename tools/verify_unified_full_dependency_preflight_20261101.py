"""Run the real updater preflight over a full program view and an owned synthetic config.

Only private-config bytes and the manifest identities depending on them differ
from the prepared public delta. Never read installed private configuration/DBs.
"""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, os, re, shutil, sys

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r1');args=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
ROOT=R/'work'/('r23pv-'+args.revision);resolution_path=ROOT/'dependency-resolution.json'
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
resolution=read(resolution_path);assert resolution['allResolved']and not resolution['realPrivateConfigurationRead']
app=ROOT/'Application';bundle=ROOT/'bundle';assert not app.exists()and not bundle.exists()
assert shutil.disk_usage(ROOT).free>1024**3
updater=T/'original_public_test_update_r23_20261101.py'
assert sha(updater)=='91f430212639b2db91d9606927d39257ca764e3909573154e73caa7945eda479'
spec=importlib.util.spec_from_file_location('exact_full_preflight',updater)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prepared=S/'sparse-update-preparation-r2/bundle'
plan=read(prepared/'update-manifest.json');public_plan=copy.deepcopy(plan)
old=read(S/'r21-base-release-manifest.json');old_payload=read(S/'r21-base-payload-manifest.json')
new=read(prepared/'payload/release-manifest.json');new_payload=read(prepared/'payload/payload-manifest.json')
private='private/server-configuration.json'
fake_config=enc({'schema':'zhumadian.original.server.configuration.v1',
                 'syntheticPreflightFixtureOnly':True,'servicesMustNotBeStartedFromThisFixture':True,
                 'containsRealCredentials':False})
fake_pin={'bytes':len(fake_config),'sha256':digest(fake_config)}
old_payload['files'][private]=fake_pin;new_payload['files'][private]=fake_pin
old_payload_raw=enc(old_payload);new_payload_raw=enc(new_payload)
old['payloadManifestSHA256']=digest(old_payload_raw);new['payloadManifestSHA256']=digest(new_payload_raw)
old_raw=enc(old);new_raw=enc(new)
plan.update(targetApplication=app.as_posix(),
    acceptedOldReleases={digest(old_raw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
    basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=new['payloadManifestSHA256'],
    newReleaseSHA256=digest(new_raw))
plan['files']['release-manifest.json']={'bytes':len(new_raw),'SHA256':digest(new_raw)}
plan['files']['payload-manifest.json']={'bytes':len(new_payload_raw),'SHA256':digest(new_payload_raw)}
mutable=set(plan['files'])|set(plan['removedFrontendFiles'])
before_free=shutil.disk_usage(ROOT).free;linked=0;copied=0;source_pins={}
for collection in ['programs','controllers']:
    for name,pin in resolution[collection].items():
        source=Path(pin['source']);m.check_file(source.parent,source.name,pin['sha256'],pin['bytes'])
        target=m.regular(app,name);target.parent.mkdir(parents=True,exist_ok=True)
        if name in mutable:shutil.copyfile(source,target);copied+=1
        else:os.link(source,target);linked+=1
        source_pins[str(source)]=pin['sha256']
put(app/private,fake_config);put(app/'payload-manifest.json',old_payload_raw);put(app/'release-manifest.json',old_raw)
for name,pin in plan['files'].items():
    target=bundle/'payload'/name
    if name=='release-manifest.json':put(target,new_raw)
    elif name=='payload-manifest.json':put(target,new_payload_raw)
    else:
        source=m.check_file(prepared/'payload',name,pin['SHA256'],pin['bytes'])
        target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
put(bundle/'update-manifest.json',enc(plan));bundle_pin=sha(bundle/'update-manifest.json')
print(json.dumps({'phase':'full-program-view-created','readOnlyProgramHardlinks':linked,
                  'independentMutableCopies':copied,'realPrivateOrSeedRead':False}),flush=True)
result_plan,old_pin,changes=m.load_bundle(app,bundle,bundle_pin,expected_target=app)
assert old_pin==digest(old_raw)and len(changes)==1182
assert set(changes)==set(public_plan['files'])|set(public_plan['removedFrontendFiles'])
assert {n:v for n,v in result_plan['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}=={
    n:v for n,v in public_plan['files'].items()if n not in ['release-manifest.json','payload-manifest.json']}
assert result_plan['removedFrontendFiles']==public_plan['removedFrontendFiles']
cases=[{'case':'full-program-view-and-owned-private-config','passed':True}]
# Change a retained immutable dependency by atomic replacement, never writing a shared inode.
retained=next(n for n in resolution['programs']if n not in mutable and n.startswith('runtime/jdk17/'))
file=app/retained;original=file.read_bytes();source=Path(resolution['programs'][retained]['source'])
m.atomic(file,original+b'own-drift')
try:m.load_bundle(app,bundle,bundle_pin,expected_target=app)
except ValueError as error:assert str(error)=='FILE_PIN_MISMATCH:'+retained
else:raise AssertionError('RETAINED_DEPENDENCY_DRIFT_ACCEPTED')
assert sha(source)==resolution['programs'][retained]['sha256']
m.atomic(file,original);cases.append({'case':'retained-dependency-drift-refused-source-unchanged','passed':True})
helper='tools/original_platform_async_release_support.py';assert not(app/helper).exists()
m.atomic(app/helper,b'own unexpected pre-existing new path\n')
try:m.load_bundle(app,bundle,bundle_pin,expected_target=app)
except ValueError as error:assert str(error)=='NEW_PATH_ALREADY_EXISTS:'+helper
else:raise AssertionError('PREEXISTING_EXTENSION_ACCEPTED')
(app/helper).unlink();cases.append({'case':'unexpected-new-helper-path-refused','passed':True})
assert sha(app/'release-manifest.json')==digest(old_raw)
assert sha(app/'payload-manifest.json')==digest(old_payload_raw)
assert sha(bundle/'update-manifest.json')==bundle_pin
assert all(sha(app/n)==pin['sha256']for n,pin in {**resolution['programs'],**resolution['controllers']}.items())
after_free=shutil.disk_usage(ROOT).free
proof={'schema':'xnby.r23.full-program-preflight.v1','updaterSHA256':sha(updater),'allPassed':True,
       'cases':cases,'fullProgramFilesVerified':len(resolution['programs']),
       'fullProgramBytesVerified':resolution['resolvedProgramBytes'],'oldControllerFilesVerified':19,
       'newControllerFilesVerified':20,'candidateInstallPaths':len(changes),
       'exactPublicProgramFilePinsAndRemovalsRetained':True,
       'privateConfigurationUsesOwnSyntheticBytes':True,'manifestIdentityAdaptedForSyntheticConfigAndLocalTarget':True,
       'actualPublicReleaseAndPrivateIdentityPreflightPassed':False,
       'realPrivateConfigurationOrSeedOrBusinessRead':False,'readOnlyProgramHardlinks':linked,
       'mutableFilesIndependentlyCopied':copied,'sharedSourceUsedForDriftTestUnchanged':True,
       'observedAdditionalDiskUsageBytes':before_free-after_free,
       'servicesStartedOrStopped':False,'publicOrFormalChanged':False,
       'publicControllerWholeLifecycleActuallyExecuted':False}
put(ROOT/'full-preflight-result.json',enc(proof))
put(ROOT/'fixture-changes.json',enc(changes))
print(json.dumps(proof),flush=True)
