from pathlib import Path
import ast,hashlib,json,importlib.util,copy,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';OLD=W/'r36-native-history-candidate-r2/bundle';STATIC=W/'r37-static-performance-r1/bundle';FRONT=W/'plan-exercise-retained-r224';OUT=W/'r38-unified-original-mappers-r1';D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103'
assert not OUT.exists()and not D.exists();J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');assert sha(OLD/'payload/release-manifest.json')=='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'
build=J(FRONT/'full-build-result.json');assert build['passed']and len(build['changedSourcePaths'])==14
rows={'frontend/emergency_pc/'+n:p for n,p in build['compiledFiles'].items()};assert len(rows)==341
base=T/'original_public_test_update_mapper_runtime_r268.py';spec=importlib.util.spec_from_file_location('r38_base',base);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fronts={'security_pc':m.R35_PERSONAL_CONTRACT['frontends']['security_pc'],'emergency_pc':m.r32_frontend_manifest(rows,'emergency_pc')}
contract={'revision':'retained-plan-exercise-task-and-original-mapper-v1','frontends':fronts,'changedCompiledSourcePaths':14,'actualCompiledSourceInventorySHA256':sha(FRONT/'actual-compiled-source-files.json'),'originalLoginWorkflowAndPermissionsRetained':True}
constants='\nR38_FRONTEND_FIELD="nativePlanExerciseRetainedFrontend"\nR38_FRONTEND_CONTRACT='+repr(contract)+'\nR38_FRONTEND_ROWS='+repr(rows)+'\nR38_REVISION="20261103-R38-original-mappers-plan-exercise-performance"\n'
function='''
def r38_unified_bundle_contract(app,bundle,plan,old,release,payload):
    require(original_mapper_defaults_declared(release), 'R38_EXACT_MAPPER_DEFAULT_DESCRIPTOR_REQUIRED')
    require(release.get(R38_FRONTEND_FIELD)==R38_FRONTEND_CONTRACT, 'R38_EXACT_COMPILED_FRONTEND_DESCRIPTOR_REQUIRED')
    require(static_performance_declared(release), 'R38_RETAINED_STATIC_PERFORMANCE_REQUIRED')
    require({n:p for n,p in old.items()if n!='payloadManifestSHA256'}==R37_STATIC_BASE_METADATA, 'R38_EXACT_R36_BASE_METADATA_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    oldfront={n:p for n,p in previous['files'].items()if n.startswith('frontend/emergency_pc/')}
    expected_files={n:p for n,p in previous['files'].items()if n not in oldfront};expected_files.update(R38_FRONTEND_ROWS)
    updater='tools/original_public_test_update.py';parameter=R24_PARAMETER
    source_pins={**R37_STATIC_CONTRACT['files'],parameter:R38_PARAMETER_PIN,updater:{'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__))}}
    for n,pin in source_pins.items():
        if n in previous['files']:expected_files[n]=pin
    expected_payload=dict(previous);expected_payload['files']=expected_files
    require(payload==expected_payload,'R38_ALL_OTHER_PAYLOAD_AND_PRIVATE_CONFIGURATION_RETAINED')
    expected=json.loads(json.dumps(old));expected['payloadManifestSHA256']=release['payloadManifestSHA256']
    expected['controllerFiles'].update({n:p['sha256']for n,p in source_pins.items()})
    expected[R24_WORKFLOW_FIELD]=workflow_contract_for(release);expected[R38_MAPPER_FIELD]=R38_MAPPER_CONTRACT
    expected[R38_FRONTEND_FIELD]=R38_FRONTEND_CONTRACT;expected[R37_STATIC_FIELD]=R37_STATIC_CONTRACT
    expected.update(publicAccepted=False,publicTestRevision=R38_REVISION)
    require(release==expected,'R38_EXACT_COMPOSITION_AND_ALL_OTHER_RELEASE_FIELDS_RETAINED')
    require(workflow_declared(release,payload)and runtime_pool_declared(release),'R38_RETAINED_WORKFLOW_AND_POOL_REQUIRED')
    changed={n:p for n,p in R38_FRONTEND_ROWS.items()if oldfront.get(n)!=p}
    removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldfront.items()if n not in R38_FRONTEND_ROWS}
    required=set(changed)|set(source_pins)|{'release-manifest.json','payload-manifest.json'}
    require(set(plan['files'])==required,'R38_ONLY_EXACT_COMPOSED_INSTALL_PATHS_REQUIRED')
    require(plan['removedFrontendFiles']==removed,'R38_ONLY_EXACT_OBSOLETE_EMERGENCY_FRONTEND_REMOVALS')
    require(plan['oldPayloadFiles']=={n:previous['files'][n]for n in required if n in previous['files']},'R38_EXACT_OLD_PAYLOAD_PINS_REQUIRED')
    for n,pin in {**changed,**source_pins}.items():
        require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'R38_EXACT_COMPOSED_TRANSPORT_PIN_REQUIRED:'+n)
        check_file(bundle/'payload',n,pin['sha256'],pin['bytes'])
    proxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs';actual='iis/App_Code/XnbyReferenceProxy.cs'
    require(plan.get('iisProxySHA256')==old['controllerFiles'][proxy]and plan.get('legacyEntrySHA256')=={actual:[old['controllerFiles'][proxy]]},'R38_EXACT_OLD_IIS_PROXY_SOURCE_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))}and plan['acceptedOldReleases'][sha(app/'release-manifest.json')]=={'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']},'R38_ONE_EXACT_INSTALLED_BASE_REQUIRED')
    require(plan.get('callbackOverlay')=='payload/callback-overlay/20261026-password-identity/manifest.json'and plan.get('callbackOverlaySHA256')=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb','R38_ORIGINAL_CALLBACK_OVERLAY_RETAINED')
    return True

'''
s=base.read_text(encoding='utf-8');anchor='def static_performance_declared(release):';assert s.count(anchor)==1;s=s.replace(anchor,constants+function+anchor)
anchor="    expected[updater]=sha(Path(__file__))";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"\n    if original_mapper_defaults_declared(release):expected[R24_PARAMETER]=R38_PARAMETER_PIN['sha256']")
anchor='    if R37_STATIC_FIELD in release:\n        static_performance_bundle_contract(app,bundle,plan,old,release,payload)';assert s.count(anchor)==1
s=s.replace(anchor,"    if R38_FRONTEND_FIELD in release or R38_MAPPER_FIELD in release:\n        r38_unified_bundle_contract(app,bundle,plan,old,release,payload)\n    elif R37_STATIC_FIELD in release:\n        static_performance_bundle_contract(app,bundle,plan,old,release,payload)")
before={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(base.read_bytes()).body if isinstance(n,ast.FunctionDef)};after={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};changed=[n for n in before if before[n]!=after[n]];assert set(changed)=={'static_performance_declared','load_bundle'}
source=T/'original_public_test_update_r38_unified_20261103.py';assert not source.exists();source.write_text(s,encoding='utf-8',newline='\n')
spec=importlib.util.spec_from_file_location('r38_unified',source);newm=importlib.util.module_from_spec(spec);spec.loader.exec_module(newm)
OUT.mkdir();D.mkdir();bundle=OUT/'bundle'
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
newq=copy.deepcopy(oldq);oldfront={n:p for n,p in oldq['files'].items()if n.startswith('frontend/emergency_pc/')};newq['files']={n:p for n,p in oldq['files'].items()if n not in oldfront};newq['files'].update(rows)
sources={n:STATIC/'payload'/n for n in m.R37_STATIC_CONTRACT['files']};sources.update({'tools/original_server_release_parameters.py':T/'original_server_release_parameters_r263_mapper_default.py','tools/original_public_test_update.py':source})
for n,p in sources.items():
 if n in oldq['files']:newq['files'][n]={'bytes':p.stat().st_size,'sha256':sha(p)}
new=copy.deepcopy(old);new['controllerFiles'].update({n:sha(p)for n,p in sources.items()});new[m.R38_MAPPER_FIELD]=m.R38_MAPPER_CONTRACT;new[m.R24_WORKFLOW_FIELD]=newm.workflow_contract_for(new);new[newm.R38_FRONTEND_FIELD]=newm.R38_FRONTEND_CONTRACT;new[m.R37_STATIC_FIELD]=m.R37_STATIC_CONTRACT;new.update(publicAccepted=False,publicTestRevision=newm.R38_REVISION)
newqraw=enc(newq);new['payloadManifestSHA256']=hashlib.sha256(newqraw).hexdigest();newraw=enc(new)
plan=copy.deepcopy(J(STATIC/'update-manifest.json'));plan.update(updateId='20261103-R38-unified-original-mappers-plan-exercise-performance',newPayloadManifestSHA256=hashlib.sha256(newqraw).hexdigest(),newReleaseSHA256=hashlib.sha256(newraw).hexdigest());plan['files']={}
for n,p in sources.items():put(bundle/'payload'/n,p.read_bytes())
for n,pin in rows.items():
 if oldfront.get(n)!=pin:
  p=FRONT/'dist'/n.split('/',2)[2];assert sha(p)==pin['sha256']and p.stat().st_size==pin['bytes'];put(bundle/'payload'/n,p.read_bytes())
put(bundle/'payload/payload-manifest.json',newqraw);put(bundle/'payload/release-manifest.json',newraw)
for p in(bundle/'payload').rglob('*'):
 if p.is_file():plan['files'][p.relative_to(bundle/'payload').as_posix()]={'bytes':p.stat().st_size,'SHA256':sha(p)}
plan['oldPayloadFiles']={n:oldq['files'][n]for n in plan['files']if n in oldq['files']};plan['removedFrontendFiles']={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldfront.items()if n not in rows}
put(bundle/'update-manifest.json',enc(plan));assert len(plan['files'])<=1000 and sum(p['bytes']for p in plan['files'].values())<=32*1024**2
report={'prepared':True,'oldReleaseSHA256':sha(OLD/'payload/release-manifest.json'),'newReleaseSHA256':plan['newReleaseSHA256'],'updaterSHA256':sha(source),'updateManifestSHA256':sha(bundle/'update-manifest.json'),'writes':len(plan['files']),'removals':len(plan['removedFrontendFiles']),'onlyAdditionalExistingFunctionsChanged':changed,'allStopLaunchBackupReplaceRestoreRecoveryASTUnchanged':True,'originalSQLJarAuthConfigurationDataAndSecurityFrontendRetained':True,'staticPerformanceIncludedFromFixedR37':True,'fullPreflightAndTransactionsStillPending':True,'publicDeployed':False}
put(D/'bundle-preparation.json',enc(report));put(OUT/'preparation.json',enc(report));print(json.dumps(report))
