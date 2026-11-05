from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/event_result_runtime_r1000_20261105'
BUILD=R/'work/event-result-full-r996';FIXED=R/'Document/Deployment/public_test_home_supervision_r47_20261104/delivery'
J=lambda p:json.loads(Path(p).read_bytes());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def replace_assignment(text,name,value):
 nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name];assert len(nodes)==1
 old=ast.get_source_segment(text,nodes[0]);assert text.count(old)==1;return text.replace(old,name+' = '+repr(value))
def functions(text):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
assert not D.exists();proof=J(BUILD/'verified-bounded-full-build-r673.json')
assert proof['passed']and proof['oneEventGuardDifferenceFromActualR841Inputs']and proof['sourceRestored']and proof['terminal']['nodeExitCode']==0 and proof['terminal']['actualJobDescendantsZeroBeforeClose']
assert sha(FIXED/'original_public_test_base_r46.py')=='83244ea13218416b062285c44c01e925b95249243b3691543d6475e69b461251'
assert sha(FIXED/'r47_update_runtime.py')=='5ade6da03f3a1d7d483806154286829d123c4ae4bc70090a67911f0df8b78af0'
legacy=load('r48_source_legacy_r47',FIXED/'r47_update_runtime.py');oldcore=load('r48_source_legacy_core',FIXED/legacy.CORE_NAME)
bases={};base_data={}
for label,root,expected in [
 ('r45',R/'work/original-backend-bootstrap-r847/r36/bundle/payload','3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'),
 ('r47',R/'work/unified-home-supervision-r928/bundle/payload','5e3ec6c0e63f4987bc412752357ba47ea17bc0b77aa7782f13cbf7b9416c439c')]:
 assert sha(root/'release-manifest.json')==expected
 release=J(root/'release-manifest.json');payload=J(root/'payload-manifest.json');assert sha(root/'payload-manifest.json')==release['payloadManifestSHA256']
 bases[expected]={'label':label,'accepted':{'payloadManifestSHA256':release['payloadManifestSHA256'],'controllerFiles':release['controllerFiles']}}
 base_data[label]=(release,payload)
rows={'frontend/emergency_pc/'+n:pin for n,pin in proof['files'].items()}
for n,pin in proof['files'].items():p=BUILD/'dist'/n;assert p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']
actual=J(BUILD/'actual-compiled-source-files.json');prior=J(R/'work/canonical-bootstrap-compatible-r841/actual-compiled-source-files.json')
event='src/views/emergencyResponse/response/info/addOrEdit.vue';assert {n for n in set(actual)|set(prior)if actual.get(n)!=prior.get(n)}=={event}
front=copy.deepcopy(oldcore.R38_FRONTEND_CONTRACT);front['frontends']['emergency_pc']=oldcore.r32_frontend_manifest(rows,'emergency_pc')
front['changedCompiledSourcePaths']=front['changedCompiledSourcePaths']+1
front['actualCompiledSourceInventorySHA256']=sha(BUILD/'actual-compiled-source-files.json')
bootstrap=copy.deepcopy(oldcore.R45_BOOTSTRAP_CONTRACT);bootstrap['compiledSourceDeltaFromR44'][event]=actual[event]
feature={'revision':'event-form-boolean-write-and-detail-results-r996-v1','eventSource':event,'beforeSourceSHA256':prior[event]['sha256'],'afterSourceSHA256':actual[event]['sha256'],
 'actualCompilerInputDiffFromRetainedR841':[event],'compiledFrontend':front['frontends']['emergency_pc'],
 'normalSaveRequiresCode0AndTrue':True,'falseOrRejectedSaveKeepsEditorInput':True,'invalidDetailsDoNotReplaceForm':True,
 'postFixNormalOriginalSDKAccepted':False,'publicAccepted':False}
template=J(R/'work/unified-home-supervision-r928/bundle/update-manifest.json')
mutable={'acceptedOldReleases','basePayloadManifestSHA256','files','newPayloadManifestSHA256','newReleaseSHA256','oldPayloadFiles','removedFrontendFiles','updateId'}
common={k:v for k,v in template.items()if k not in mutable and k!='supervisionBaseR46'}
support={k:v for k,v in legacy.PINS.items()if k!=legacy.CORE}
constants={'R48_FIELD':'emergencyEventWriteResults','R48_FEATURE':feature,'R48_EMERGENCY_ROWS':rows,'R48_FRONTEND_CONTRACT':front,
 'R48_BOOTSTRAP_CONTRACT':bootstrap,'R48_SUPPORT_ROWS':support,'R48_CORE':legacy.CORE,'R48_UPDATER_PIN':None,
 'R48_HOME_ROWS':oldcore.R46_HOME_FRONTEND,'R48_SUPERVISION_DESCRIPTOR':legacy.DESCRIPTOR,'R48_BASES':bases,
 'R48_PLAN_COMMON':common,'R48_REVISION':'20261105-R48-event-write-results-home-and-supervision'}
coretext=(FIXED/legacy.CORE_NAME).read_text('utf8');core_before=functions(coretext)
anchor="        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),"
assert coretext.count(anchor)==1
coretext=coretext.replace(anchor,"        allowed = allowed or (R48_FIELD in read(bundle / 'payload/release-manifest.json') and name in R48_SUPPORT_ROWS)\n\n"+anchor)
anchor="    if R46_HOME_FIELD in release:\n        r46_home_bundle_contract(app,bundle,plan,old,release,payload)"
assert coretext.count(anchor)==1
coretext=coretext.replace(anchor,"    if R48_FIELD in release:\n        r48_bundle_contract(app,bundle,plan,old,release,payload)\n    elif R46_HOME_FIELD in release:\n        r46_home_bundle_contract(app,bundle,plan,old,release,payload)")
guard=next(n for n in ast.parse(coretext).body if isinstance(n,ast.If)and'__name__'in ast.get_source_segment(coretext,n.test))
start=coretext.index(ast.get_source_segment(coretext,guard))
insert='\n'.join(k+' = '+repr(v)for k,v in constants.items())+'\n\n'+(V/'r48_event_result_contract_r1000.py').read_text('utf8')+'\n\n'
coretext=coretext[:start]+insert+coretext[start:];core_after=functions(coretext)
assert [n for n,v in core_before.items()if core_after.get(n)!=v]==['load_bundle']
assert set(core_after)-set(core_before)=={'r48_runtime_rows','r48_expected_files','r48_expected_release','r48_bundle_contract'}
D.mkdir();S=D/'source';S.mkdir();corep=S/legacy.CORE_NAME;corep.write_text(coretext,encoding='utf8')
newpins=copy.deepcopy(legacy.PINS);newpins[legacy.CORE]={'bytes':corep.stat().st_size,'sha256':sha(corep)}
wrapper=(FIXED/'r47_update_runtime.py').read_text('utf8');wrapper_before=functions(wrapper)
for key,value in [('CORE_SHA',sha(corep)),('PINS',newpins),('REVISION',constants['R48_REVISION'])]:wrapper=replace_assignment(wrapper,key,value)
declared=next(n for n in ast.parse(wrapper).body if isinstance(n,ast.FunctionDef)and n.name=='declared');old=ast.get_source_segment(wrapper,declared)
new='''def declared(release):
    if FIELD not in release:return False
    need(equal(release[FIELD],DESCRIPTOR),'EXACT_SUPERVISION_RELEASE_DESCRIPTOR_REQUIRED')
    current=R48_EVENT_FIELD in release
    expected=PINS if current else R47_LEGACY_PINS
    expected_updater=digest(HERE) if current else R47_LEGACY_UPDATER_SHA
    controls=release.get('controllerFiles',{})
    for n in [CONTROLLER,HELPER,CORE]:need(controls.get(n)==expected[n]['sha256'],'EXACT_SUPERVISION_CONTROL_REQUIRED:'+n)
    need(controls.get(UPDATER)==expected_updater,'EXACT_DECLARED_OLD_OR_CURRENT_UPDATER_REQUIRED')
    if current:
        for n,p in R48_RELEASE_METADATA.items():need(equal(release.get(n),p),'EXACT_R48_RELEASE_METADATA_REQUIRED:'+n)
    return True'''
wrapper=wrapper.replace(old,new)
anchor="    m=load('frozen_r46_supervision_runtime',core)";assert wrapper.count(anchor)==1
wrapper=wrapper.replace(anchor,anchor+"\n    m.R48_UPDATER_PIN=_pin(HERE)")
metadata={constants['R48_FIELD']:feature,oldcore.R38_FRONTEND_FIELD:front,oldcore.R45_BOOTSTRAP_FIELD:bootstrap,oldcore.R46_HOME_FIELD:oldcore.R46_HOME_FEATURE}
header='R47_LEGACY_PINS = '+repr(legacy.PINS)+'\nR47_LEGACY_UPDATER_SHA = '+repr(sha(FIXED/'r47_update_runtime.py'))+'\nR48_EVENT_FIELD = '+repr(constants['R48_FIELD'])+'\nR48_RELEASE_METADATA = '+repr(metadata)+'\n\n'
pos=wrapper.index('def need(');wrapper=wrapper[:pos]+header+wrapper[pos:]
wrapper_after=functions(wrapper);assert set(wrapper_before)==set(wrapper_after)
assert [n for n,v in wrapper_before.items()if wrapper_after[n]!=v]==['declared','runtime']
wp=S/'original_public_test_update.py';wp.write_text(wrapper,encoding='utf8')
newmod=load('r48_prepared_runtime_r1000',wp);m=newmod.runtime()
targets={}
for label,(release,payload)in base_data.items():
 target=copy.deepcopy(payload);target['files']=m.r48_expected_files(payload['files']);raw=enc(target)
 target_release=m.r48_expected_release(release,hashlib.sha256(raw).hexdigest())
 assert newmod.declared(target_release)
 targets[label]=(target,target_release)
assert targets['r45']==targets['r47'],'BOTH_EXACT_BASES_MUST_PRODUCE_ONE_IDENTICAL_FINAL_RELEASE'
payload,release=targets['r47'];C=D/'candidate';C.mkdir();(C/'payload-manifest.json').write_bytes(enc(payload));(C/'release-manifest.json').write_bytes(enc(release))
variants={}
for base_pin,b in bases.items():
 label=b['label'];oldrelease,oldpayload=base_data[label]
 changed={n:p for n,p in payload['files'].items()if oldpayload['files'].get(n)!=p}
 files={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in changed.items()}
 for n in ['release-manifest.json','payload-manifest.json']:
  p=C/n;files[n]={'bytes':p.stat().st_size,'SHA256':sha(p)}
 removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldpayload['files'].items()if n.startswith('frontend/emergency_pc/')and n not in payload['files']}
 plan={**common,'acceptedOldReleases':{base_pin:b['accepted']},'basePayloadManifestSHA256':b['accepted']['payloadManifestSHA256'],
  'files':files,'newPayloadManifestSHA256':sha(C/'payload-manifest.json'),'newReleaseSHA256':sha(C/'release-manifest.json'),
  'oldPayloadFiles':{n:oldpayload['files'][n]for n in files if n in oldpayload['files']},'removedFrontendFiles':removed,'updateId':'20261105-r48-event-results-from-'+label}
 assert len(files)<=1000 and sum(p['bytes']for p in files.values())<=32*1024**2
 p=D/('update-from-'+label+'.json');p.write_bytes(enc(plan));variants[label]={'writes':len(files),'removedFrontendFiles':len(removed),'payloadBytes':sum(x['bytes']for x in files.values()),'manifestSHA256':sha(p)}
report={'preparedOnly':True,'exactBases':list(bases),'oneIdenticalFinalTargetFromBothBases':True,'newReleaseSHA256':sha(C/'release-manifest.json'),'newPayloadSHA256':sha(C/'payload-manifest.json'),
 'originalCoreFunctionsChangedOnly':['load_bundle'],'originalCoreFunctionsUnchanged':len(core_before)-1,'newContractFunctions':4,
 'wrapperFunctionsChangedOnly':['declared','runtime'],'originalStopStartMutationRestoreAuthTLSAndHealthFunctionBodiesUnchanged':True,
 'currentR47HealthDeclarationRetained':newmod.declared(base_data['r47'][0]),'newR48DeclarationPassed':newmod.declared(release),'variants':variants,
 'fullFileContractNativeLifecycleAndPublicAcceptancePassed':False,'fixedR47PackageChanged':False,'fullCloneReady':False}
(D/'prepared-runtime-r1000.json').write_bytes(enc(report));print(json.dumps(report))
