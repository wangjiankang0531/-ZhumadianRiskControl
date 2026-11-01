from pathlib import Path
import ast, hashlib, importlib.util, json, shutil, zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
D=R/'Document/Deployment/public_test_unified_r24_20261101';S=W/'r24-unified-candidate-r1'
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest()
sha=lambda p:digest(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(enc(value))
assert not(D/'code-fixture-cleanup.json').exists(),'OWN_R24_CLEANUP_ALREADY_COMPLETED_USE_EXISTING_PROOF'
scope=read(D/'preparation-result.json');manifest=read(D/'delivery-manifest.json');delivery=D/'delivery'
assert sha(D/'delivery-manifest.json')==scope['manifestSHA256']=='0a6d7682ba9d0b39611ad91ed1dea01c9eafd5c44d246d8873048a00260567e6'
assert (delivery/'delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
assert {p.name for p in delivery.iterdir()}==set(manifest['files'])|{'delivery-manifest.json'}
assert len(list(delivery.iterdir()))==8 and sum(p.stat().st_size for p in delivery.iterdir())==4506722
for n,pin in manifest['files'].items():assert sha(delivery/n)==pin['sha256']and(delivery/n).stat().st_size==pin['bytes']
with zipfile.ZipFile(delivery/'Zhumadian_Unified_Emergency_20261101_R24.zip')as z:
    assert z.testzip()is None and len(z.namelist())==len(set(z.namelist()))
    raw=z.read('update-manifest.json');plan=json.loads(raw);assert digest(raw)==manifest['updateManifestSHA256']
    assert set(z.namelist())=={'update-manifest.json','web.config'}|{'payload/'+n for n in plan['files']}
    assert len(plan['files'])==758 and len(plan['removedFrontendFiles'])==607
    assert all(not n.startswith(('private/','UserData/','runtime/','seed/','Assets/','Reference/'))for n in plan['files'])
    for n,pin in plan['files'].items():
        raw=z.read('payload/'+n);assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']
        assert raw==(S/'sparse-graceful-update-preparation-r1/bundle/payload'/n).read_bytes()
    release=json.loads(z.read('payload/release-manifest.json'));payload=json.loads(z.read('payload/payload-manifest.json'))
    assert digest(z.read('payload/release-manifest.json'))==plan['newReleaseSHA256']
    assert digest(z.read('payload/payload-manifest.json'))==release['payloadManifestSHA256']
    assert z.read('payload/tools/original_public_test_update.py')==(delivery/'r24_update_runtime.py').read_bytes()
rows=read(S/'candidate-stage.json')['allMaterializedPayloadFiles'];assert len(rows)==1182
assert all(payload['files'][n]==pin for n,pin in rows.items())
old=read(S/'r21-base-release-manifest.json');oldp=read(S/'r21-base-payload-manifest.json')
changed={'tools/serve_original_server_release.py','tools/original_server_windows_job.py','tools/original_public_test_update.py',
         'tools/original_platform_async_release_support.py','tools/original_server_release_parameters.py'}
assert {n:p for n,p in release['controllerFiles'].items()if n not in changed}=={n:p for n,p in old['controllerFiles'].items()if n not in changed}
assert len(release['controllerFiles'])==20
assert {n:p for n,p in payload['files'].items()if n not in rows and not n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))}=={
    n:p for n,p in oldp['files'].items()if n not in rows and not n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))}
assert all(n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))and n not in payload['files']for n in plan['removedFrontendFiles'])
F=W/'emergency-workflow-source-r6';build=read(F/'build-result.json')
assert len(build['files'])==338
for n,pin in build['files'].items():
    rel='frontend/emergency_pc/'+n;assert payload['files'][rel]==pin
    assert (R/'_f/Application'/rel).read_bytes()==(F/'dist'/n).read_bytes()
whole=read(R/'work/event_delivery_consistency_20261030/full-controller-r127/r1/result.json')
assert whole['allPassed']and whole['allSixComponentsNormallyExitedZero']and whole['checks']['actualR24WorkflowGuardRuntimePinsPassed']
for n,pin in release['controllerFiles'].items():assert sha(R/'_f/Application'/n)==pin
proof={'schema':'xnby.r24.independent-transport.v1','allPassed':True,'manifestSHA256':scope['manifestSHA256'],
    'transportFiles':8,'transportBytes':4506722,'writePaths':758,'obsoleteFrontendPaths':607,'totalInstallPaths':1365,
    'allTransportMembersAndHashesVerified':True,'all1182StagedProgramRowsVerified':True,
    'all338WF6CompiledFilesEqualActuallyExecutedFixture':True,'all20ControllerFilesEqualActuallyExecutedFixture':True,
    'other15ControlsOriginalJarsDatabaseConfigurationIISAndAssetsRetained':True,
    'actualSixComponentSyntheticRuntimeAnd398ModelsPassed':True,
    'actualPublicPreflightOrIISOrTLSOrRealNangangBusinessAccepted':False,'publicInstalled':False}
put(D/'independent-transport-verification.json',proof)
# Retain small proof/change manifests; remove only the exited, newly owned code-recovery replicas.
tx=R/'work/r24gx-r1';tx=tx.resolve(strict=True)
assert tx==(R/'work/r24gx-r1').resolve()and tx.parent==(R/'work').resolve()
result=read(S/'sparse-graceful-update-preparation-r1/result.json');cases=[r['scenario']for r in result['recoveryScenarios']]+['foreign-file-drift']
assert len(cases)==13 and {p.name for p in tx.iterdir()}==set(cases)
assert all((tx/n/'result.json').is_file()for n in cases)
targets=[];logical=0;count=0
for case in cases:
    for suffix in ['Application','backup/before']:
        target=tx/case/suffix
        if not target.exists():continue
        resolved=target.resolve(strict=True);assert resolved.is_relative_to(tx/case)and resolved!=tx/case
        assert resolved==target.absolute()
        for p in [target,*target.rglob('*')]:
            assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400
            if p.is_file():count+=1;logical+=p.stat().st_size
        targets.append(target)
before=shutil.disk_usage(tx).free
for target in targets:shutil.rmtree(target)
assert all(not p.exists()for p in targets)and all((tx/n/'result.json').is_file()for n in cases)
cleanup={'schema':'xnby.r24.owned-code-fixture-cleanup.v1','removedFileCount':count,'removedLogicalBytes':logical,
    'observedFreeByteIncreaseNotPreciselyAttributable':shutil.disk_usage(tx).free-before,
    'retainedAll13ProofsAndChangeManifests':True,'databasesUserPreviewsFormalSourceAssetsAndFixedDeliveriesUntouched':True}
put(D/'code-fixture-cleanup.json',cleanup)
print(json.dumps({'transport':proof,'cleanup':cleanup},ensure_ascii=False))
