from pathlib import Path
import hashlib,importlib.util,json

R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
O=R/'work/r39-full-preflight-r37-r341';app=O/'Application';bundle=O/'bundle'
SOURCE=T/'original_public_test_update_r39_plan_runtime_r337.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert not(D/'r37/full-program-preflight.json').exists()and not(O/'verified-result.json').exists()
assert O.resolve()==O and app.is_dir()and bundle.is_dir()
log=(D/'r37/full-preflight-driver-r341.log').read_text(encoding='utf-8')
assert "str(e)=='UNKNOWN_OLD_ENTRY_SCRIPT'"in log and 'FILE_PIN_MISMATCH:iis/App_Code/XnbyReferenceProxy.cs'in log
assert sha(SOURCE)==J(D/'updater-preparation-r337.json')['sourceSHA256']
resolution=J(O/'resolution.json');programs=resolution['programs'];controls=resolution['controls']
plan=J(bundle/'update-manifest.json');old=J(app/'release-manifest.json');oldq=J(app/'payload-manifest.json')
new=J(bundle/'payload/release-manifest.json');newq=J(bundle/'payload/payload-manifest.json')
private='private/server-configuration.json';fake=(app/private).read_bytes();cfg=json.loads(fake)
assert cfg['syntheticPreflightFixtureOnly']and cfg['servicesMustNotBeStartedFromThisFixture']and not cfg['containsRealCredentials']
assert oldq['files'][private]=={'bytes':len(fake),'sha256':hashlib.sha256(fake).hexdigest()}
assert plan['acceptedOldReleases']=={sha(app/'release-manifest.json'):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}}
spec=importlib.util.spec_from_file_location('owned_r37_resume',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
live='iis/App_Code/XnbyReferenceProxy.cs';assert live in old['controllerFiles']
assert (app/live).read_bytes()==b'own foreign IIS edit'
checks=[]
expected_iis='FILE_PIN_MISMATCH:'+live
try:m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app)
except ValueError as error:assert str(error)==expected_iis
else:raise AssertionError('DECLARED_R37_IIS_DRIFT_ACCEPTED')
assert (app/live).read_bytes()==b'own foreign IIS edit'
checks.append({'case':'registered-R37-IIS-drift-refused-before-stop','refused':expected_iis,'noWritesByLoadBundle':True})
source=Path(controls[live]['source'])
assert source.stat().st_size==controls[live]['bytes']and sha(source)==controls[live]['sha256']==old['controllerFiles'][live]
m.atomic(app/live,source.read_bytes())
for n,pin in {**programs,**controls}.items():assert (app/n).stat().st_size==pin['bytes']and sha(app/n)==pin['sha256']
loaded,oldpin,changes=m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app)
assert oldpin==sha(app/'release-manifest.json')and len(changes)==364
capacity=m.candidate_runtime_pool_preflight(app,bundle,loaded)
assert capacity['budget']['mysqlMaxConnections']==24 and len(capacity['budget']['datasources'])==3
assert capacity['originalMapperPreflight']['passed']and capacity['originalMapperPreflight']['defaultWillApply']
assert m.native_plan_runtime_declared(new,newq)
checks.append({'case':'all-R37-programs-and-final-R39-load_bundle','passed':True})
checks.append({'case':'same-snapshot-original-mapper-and-numeric-budget-before-stop','passed':True})
mutable=set(plan['files'])|set(plan['removedFrontendFiles'])
for n in [next(n for n in programs if n.startswith('runtime/jdk17/')and n not in mutable),next(iter(m.R26_TEAM_ROWS))]:
    p=app/n;before=p.read_bytes();m.atomic(p,before+b'own drift')
    try:
        try:m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app)
        except ValueError as error:assert str(error)=='FILE_PIN_MISMATCH:'+n
        else:raise AssertionError('RETAINED_PROGRAM_DRIFT_ACCEPTED')
        assert sha(Path(programs[n]['source']))==programs[n]['sha256']
    finally:m.atomic(p,before)
    checks.append({'case':'retained-program-drift-refused:'+n,'passed':True})
p=app/m.R39_PLAN_CLASS;assert not p.exists()
candidate=(bundle/'payload'/m.R39_PLAN_CLASS).read_bytes();assert hashlib.sha256(candidate).hexdigest()==m.R39_PLAN_ROW['sha256']
m.atomic(p,candidate)
try:
    try:m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app)
    except ValueError as error:assert str(error)=='NEW_PATH_ALREADY_EXISTS:'+m.R39_PLAN_CLASS
    else:raise AssertionError('UNDECLARED_OLD_PLAN_CLASS_ACCEPTED')
    assert p.read_bytes()==candidate
finally:p.unlink()
checks.append({'case':'unexpected-preexisting-plan-override-refused-before-stop','passed':True})
bad=json.loads(fake);bad['configuration']['platform'].pop('spring.datasource.host')
m.atomic(app/private,enc(bad))
try:
    try:m.candidate_runtime_pool_preflight(app,bundle,loaded)
    except ValueError as error:assert str(error)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'
    else:raise AssertionError('UNKNOWN_PLATFORM_LAYOUT_ACCEPTED')
finally:m.atomic(app/private,fake)
checks.append({'case':'unknown-primary-layout-refused-before-stop','passed':True})
assert all(sha(app/n)==pin['sha256']for n,pin in {**programs,**controls}.items())
assert (app/private).read_bytes()==fake and not(app/m.R39_PLAN_CLASS).exists()
result={'allPassed':True,'baselineVariant':'R37','fullProgramFilesVerified':len(programs),'oldDeclaredControls':len(old['controllerFiles']),
 'newDeclaredControls':len(new['controllerFiles']),'liveIISProxyExtraPinVerified':True,'candidateInstallPaths':len(plan['files']),
 'obsoleteEmergencyFrontendRemovals':len(plan['removedFrontendFiles']),'allChangePaths':len(changes),'cases':checks,
 'newUpdaterSHA256':sha(SOURCE),'sourceProgramsUnchanged':True,'onlyLocalTargetAndSyntheticPrivateManifestMetadataAdapted':True,
 'candidatePlanClassContractAndTransportPassed':True,'internalSameSnapshotMapperGatePassed':True,'servicesStarted':False,
 'initialSharedHistorySourceAndIISExpectedCodeDriverFailuresRetained':True,'earlierOwnedViewFullyRevalidatedAndRestored':True,
 'actualServerPreflightOrIISOrPublicDeploymentPassed':False}
for file in [D/'r37/full-program-preflight.json',O/'verified-result.json']:file.write_bytes(enc(result))
combined={'passed':True,'variants':[{k:v for k,v in J(D/label/'full-program-preflight.json').items()if k in ['baselineVariant','fullProgramFilesVerified','oldDeclaredControls','newDeclaredControls','candidateInstallPaths','obsoleteEmergencyFrontendRemovals','allChangePaths','sourceProgramsUnchanged','allPassed']}for label in ['r36','r37']],
 'initialR37DriverFailuresRetained':True,'servicesStarted':False,'candidateSourceSHA256':sha(SOURCE),'actualServerIISOrPublicDeploymentPassed':False}
(D/'full-program-verification-r343.json').write_bytes(enc(combined));print(json.dumps(combined),flush=True)
