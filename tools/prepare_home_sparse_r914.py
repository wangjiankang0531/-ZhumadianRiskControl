"""Prepare an exact R45 -> R46 sparse static update with the frozen lifecycle core."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application'
B=R/'work/original-backend-bootstrap-r847/r36/bundle';D=R/'Document/Deployment/home_sparse_update_r914_20261104';O=R/'work/home-sparse-r914/bundle'
C=V/'performance-assets-r893/candidate-r900';P=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert not D.exists()and not O.exists()
assert J(R/'Document/Deployment/home_transfer_full_verified_r913_20261104/verified-original-sdk-home-r913.json')['passed']
old=J(B/'payload/release-manifest.json');before=J(B/'payload/payload-manifest.json')
old_sha=sha(B/'payload/release-manifest.json');assert old_sha=='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
assert sha(B/'payload/payload-manifest.json')==old['payloadManifestSHA256']=='8df6a57a9dfec2c8c5ff65964db66b27b752a73cc026241576222bd4bcfc58bb'
feature=J(P/'full-source-and-restore-plan.private.json')['homeTransferFeature'];front=feature['changedFiles']
assert len(front)==4 and all(n.startswith('frontend/security_pc/')for n in front)
for n,p in front.items():assert (C/n.removeprefix('frontend/security_pc/')).stat().st_size==p['bytes']and sha(C/n.removeprefix('frontend/security_pc/'))==p['sha256']
source=A/'tools/original_public_test_update_r45_bootstrap_r847.py';assert sha(source)=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
text=source.read_text('utf8');original=ast.parse(text)
helper='''
R46_HOME_BASE_RELEASE_SHA = __BASE_RELEASE__
R46_HOME_BASE_PAYLOAD_SHA = __BASE_PAYLOAD__
R46_HOME_FIELD = 'homeTransferAssets'
R46_HOME_FEATURE = __FEATURE__
R46_HOME_FRONTEND = __FRONTEND__
R46_HOME_REVISION = '20261104-R46-lossless-home-transfer'

def r46_home_bundle_contract(app,bundle,plan,old,release,payload):
    require(sha(regular(app,'release-manifest.json'))==R46_HOME_BASE_RELEASE_SHA,'R46_EXACT_R45_BASE_REQUIRED')
    require(old['payloadManifestSHA256']==R46_HOME_BASE_PAYLOAD_SHA,'R46_EXACT_R45_PAYLOAD_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={R46_HOME_BASE_RELEASE_SHA},'R46_SINGLE_EXACT_R45_BASE')
    accepted=plan['acceptedOldReleases'][R46_HOME_BASE_RELEASE_SHA]
    require(accepted=={'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']},'R46_ALL_OLD_CONTROLLERS_REQUIRED')
    require(release.get(R46_HOME_FIELD)==R46_HOME_FEATURE,'R46_EXACT_HOME_ASSET_DESCRIPTOR')
    require(plan['removedFrontendFiles']=={}and plan['legacyEntrySHA256']=={},'R46_NO_REMOVALS_OR_LEGACY_WRITES')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    updater='tools/original_public_test_update.py'
    updater_pin={'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__))}
    expected_files=dict(previous['files']);expected_files.update(R46_HOME_FRONTEND);expected_files[updater]=updater_pin
    expected_payload=dict(previous);expected_payload['files']=expected_files
    require(payload==expected_payload,'R46_ALL_OTHER_PROGRAM_PRIVATE_DATA_AND_DEPENDENCY_PINS_RETAINED')
    expected=json.loads(json.dumps(old));expected['payloadManifestSHA256']=release['payloadManifestSHA256']
    expected['controllerFiles'][updater]=updater_pin['sha256'];expected[R46_HOME_FIELD]=R46_HOME_FEATURE
    expected.update(publicAccepted=False,publicTestRevision=R46_HOME_REVISION)
    require(release==expected,'R46_ALL_OTHER_RELEASE_FEATURES_AND_IDENTITIES_RETAINED')
    names=set(R46_HOME_FRONTEND)|{updater,'payload-manifest.json','release-manifest.json'}
    require(set(plan['files'])==names and len(names)==7,'R46_EXACT_SEVEN_WRITES')
    for name,pin in {**R46_HOME_FRONTEND,updater:updater_pin}.items():
        require(plan['files'][name]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'R46_EXACT_WRITE_PIN:'+name)
    require(plan['oldPayloadFiles']=={name:previous['files'][name]for name in names if name in previous['files']},'R46_EXACT_OLD_FRONTEND_AND_UPDATER_PREIMAGES')

'''.replace('__BASE_RELEASE__',repr(old_sha)).replace('__BASE_PAYLOAD__',repr(old['payloadManifestSHA256'])).replace('__FEATURE__',repr(feature)).replace('__FRONTEND__',repr(front))
needle='def load_bundle(app, bundle, pin, *, expected_target=TARGET, expected_port=18892):';assert text.count(needle)==1;text=text.replace(needle,helper+'\n'+needle)
needle='    if R38_FRONTEND_FIELD in release or R38_MAPPER_FIELD in release:';assert text.count(needle)==1
text=text.replace(needle,"    if R46_HOME_FIELD in release:\n        r46_home_bundle_contract(app,bundle,plan,old,release,payload)\n    elif R38_FRONTEND_FIELD in release or R38_MAPPER_FIELD in release:")
candidate_tree=ast.parse(text)
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
f0,f1=funcs(original),funcs(candidate_tree);assert set(f1)-set(f0)=={'r46_home_bundle_contract'}and [n for n in f0 if f0[n]!=f1[n]]==['load_bundle']
runtime=V/'original_public_test_update_home_r46_r914.py';assert not runtime.exists();runtime.write_text(text,encoding='utf8',newline='\n')
payload=copy.deepcopy(before);release=copy.deepcopy(old);payload['files'].update(front)
updater='tools/original_public_test_update.py';upin={'bytes':runtime.stat().st_size,'sha256':sha(runtime)};payload['files'][updater]=upin
raw_payload=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(raw_payload).hexdigest();release['controllerFiles'][updater]=upin['sha256'];release['homeTransferAssets']=feature;release.update(publicAccepted=False,publicTestRevision='20261104-R46-lossless-home-transfer')
raw_release=enc(release);newsha=hashlib.sha256(raw_release).hexdigest()
plan=copy.deepcopy(J(B/'update-manifest.json'));raw={'payload-manifest.json':raw_payload,'release-manifest.json':raw_release}
files={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in {**front,updater:upin}.items()}
files.update({n:{'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}for n,b in raw.items()})
plan.update(updateId='20261104-r46-home-lossless-from-r45',acceptedOldReleases={old_sha:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],
 newReleaseSHA256=newsha,newPayloadManifestSHA256=release['payloadManifestSHA256'],files=files,oldPayloadFiles={n:before['files'][n]for n in files if n in before['files']},removedFrontendFiles={},legacyEntrySHA256={},
 iisProxySHA256=old['controllerFiles'].get('iis/App_Code/XnbyReferenceProxy.cs',old['controllerFiles']['deploy/iis_original/App_Code/XnbyReferenceProxy.cs']))
for n,p in files.items():
 b=raw[n]if n in raw else runtime.read_bytes()if n==updater else(C/n.removeprefix('frontend/security_pc/')).read_bytes()
 assert len(b)==p['bytes']and hashlib.sha256(b).hexdigest()==p['SHA256'];put(O/'payload'/n,b)
put(O/'update-manifest.json',enc(plan));D.mkdir()
proof={'prepared':True,'targetApplication':plan['targetApplication'],'acceptedBaseReleaseSHA256':old_sha,'newReleaseSHA256':newsha,'manifestSHA256':sha(O/'update-manifest.json'),
 'runtimeSHA256':sha(runtime),'writePaths':list(files),'writes':7,'removals':0,'normalLifecycleAndOriginal18UIAssertionsPassed':True,
 'runtimeChangedFunctions':['load_bundle'],'addedContractFunction':'r46_home_bundle_contract','unchangedRuntimeFunctionBodies':len(f0)-1,
 'originalStopStartHealthRecoveryMapperPoolAndAuthBodiesRetained':True,'payloadLogicalBytes':sum(p['bytes']for p in files.values()),
 'fullFileRecoveryAndTransportVerificationPending':True,'publicChanged':False,'fullCloneReady':False}
put(D/'prepared-sparse-r914.json',enc(proof));print(json.dumps(proof))
