from pathlib import Path
import copy,hashlib,importlib.util,json,os,zipfile

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
O=R/'work/r39-plan-runtime-unified-r1';D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
OLD=W/'r38-unified-original-mappers-r2/bundle';BASE36=W/'r36-native-history-candidate-r2/bundle'
SOURCE=T/'original_public_test_update_r39_plan_runtime_r337.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
assert not O.exists()and not(D/'bundle-preparation-r338.json').exists()
assert J(D/'updater-preparation-r337.json')['sourceSHA256']==sha(SOURCE.read_bytes())
spec=importlib.util.spec_from_file_location('plan_unified',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
module_root=W/'native-plan-runtime-r333';module=J(module_root/'module-manifest.json')
assert J(R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103/verified-result-r334.json')['passed']
raw36=(BASE36/'payload/release-manifest.json').read_bytes();q36=(BASE36/'payload/payload-manifest.json').read_bytes()
assert sha(raw36)=='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'
zip37=list((R/'Document/Deployment/public_test_static_performance_r37_20261103/delivery').glob('*.zip'));assert len(zip37)==1
with zipfile.ZipFile(zip37[0])as z:raw37=z.read('payload/release-manifest.json');q37=z.read('payload/payload-manifest.json')
assert sha(raw37)=='909b64aa1315b8764b169c9874b8f52f903268b59c67adbf7b3799e85e29448c'and q36==q37
old_plan=J(OLD/'update-manifest.json');release=J(OLD/'payload/release-manifest.json');payload=J(OLD/'payload/payload-manifest.json')
assert m.R39_PLAN_CLASS not in payload['files']and m.R39_PLAN_FIELD not in release
payload['files'][m.R39_PLAN_CLASS]=m.R39_PLAN_ROW
updater='tools/original_public_test_update.py';updater_pin={'bytes':SOURCE.stat().st_size,'sha256':sha(SOURCE.read_bytes())}
if updater in payload['files']:payload['files'][updater]=updater_pin
payload_raw=enc(payload)
release['payloadManifestSHA256']=sha(payload_raw);release['controllerFiles'][updater]=updater_pin['sha256']
release[m.R39_PLAN_FIELD]=m.R39_PLAN_CONTRACT;release['publicTestRevision']=m.R38_REVISION
release_raw=enc(release)
assert m.native_plan_runtime_declared(release,payload)
O.mkdir();shared=O/'shared/payload'
replacements={updater:SOURCE.read_bytes(),'payload-manifest.json':payload_raw,'release-manifest.json':release_raw,
              m.R39_PLAN_CLASS:(module_root/m.R39_PLAN_CLASS).read_bytes()}
assert sha(replacements[m.R39_PLAN_CLASS])==module['classSHA256']==m.R39_PLAN_ROW['sha256']
files=copy.deepcopy(old_plan['files'])
for name,raw in replacements.items():files[name]={'bytes':len(raw),'SHA256':sha(raw)}
for name,pin in files.items():
    out=shared/name;out.parent.mkdir(parents=True,exist_ok=True)
    if name in replacements:out.write_bytes(replacements[name])
    else:
        original=OLD/'payload'/name;assert original.stat().st_size==pin['bytes']and sha(original.read_bytes())==pin['SHA256'];os.link(original,out)
assert len(files)==187
variants={}
for label,raw,oldqraw in [('R36',raw36,q36),('R37',raw37,q37)]:
    old=json.loads(raw);oldq=json.loads(oldqraw);bundle=O/label.lower()/'bundle'
    plan=copy.deepcopy(old_plan)
    plan.update(updateId='20261103-r39-plan-runtime-from-'+label.lower(),
        acceptedOldReleases={sha(raw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
        basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=sha(payload_raw),newReleaseSHA256=sha(release_raw),files=copy.deepcopy(files))
    plan['oldPayloadFiles']={name:oldq['files'][name]for name in files if name in oldq['files']}
    proxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs';actual='iis/App_Code/XnbyReferenceProxy.cs'
    plan['iisProxySHA256']=old['controllerFiles'][proxy];plan['legacyEntrySHA256']={actual:[old['controllerFiles'][proxy]]}
    for name,pin in files.items():
        out=bundle/'payload'/name;out.parent.mkdir(parents=True,exist_ok=True);os.link(shared/name,out)
    (bundle/'update-manifest.json').write_bytes(enc(plan))
    assert len(plan['acceptedOldReleases'])==1 and len(plan['files'])==187 and len(plan['removedFrontendFiles'])==177
    d=D/label.lower();d.mkdir()
    variants[label]={'bundle':bundle.as_posix(),'oldReleaseSHA256':sha(raw),'oldPayloadManifestSHA256':old['payloadManifestSHA256'],
      'updateManifestSHA256':sha((bundle/'update-manifest.json').read_bytes()),'newReleaseSHA256':sha(release_raw),
      'newPayloadManifestSHA256':sha(payload_raw),'writes':187,'removals':177,'oldControls':len(old['controllerFiles']),
      'newControls':len(release['controllerFiles']),'eachBundleAcceptsOneExactBase':True}
report={'prepared':True,'variants':variants,'sameFinalReleaseAndPayloadForBothBases':True,
 'candidateUpdaterSHA256':updater_pin['sha256'],'candidatePlanClassSHA256':m.R39_PLAN_ROW['sha256'],
 'allOriginalOtherPayloadAuthenticationConfigurationAndDataRetained':True,'sharedUnchangedPayloadByHardlink':True,
 'publicTransportWrapperPrepared':False,'fullProgramAndTransactionVerificationPending':True,
 'publicOrFormalOrDesktopChanged':False,'fullCloneReady':False}
(D/'bundle-preparation-r338.json').write_bytes(enc(report));(O/'preparation-r338.json').write_bytes(enc(report))
print(json.dumps(report))
