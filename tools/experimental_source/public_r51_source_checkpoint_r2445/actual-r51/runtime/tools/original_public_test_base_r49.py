"""Unified attachment update over a byte-pinned R48 validator and R46 lifecycle.

Preserves the original process ownership, shutdown, backup, restore, launch and
health function bodies. Only this reviewed release's exact source/metadata
variants and sparse program changes are composed here. No business data import.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,re,sys,types,zipfile
sys.dont_write_bytecode=True
HERE=Path(__file__).absolute()
CONTRACT_NAME='original_unified_attachment_contract_r49.json'
CONTRACT_SHA='729e035dd4b13e25da57aff09bc694d89501f267918c25335d672a207b975d69'
BASE_NAME='original_public_test_base_r48.py'
BASE_SHA='81cc5e3d27062002bc18b142b577530ac940800b9e75dbc7c268f74d246a3211'
CORE_NAME='original_public_test_base_r46.py'
CORE_SHA='3884a7029205ab418d41d48d969c96e69c9798bc75d806c8d85b2f0b59ab1b88'
PREIMAGE_NAME='original_untracked_callback_preimages_r1301.py'
PREIMAGE_SHA='94f4cc4abc97a6eb8c617d2599033a14a035fb0b20d66c4caea7e5d63405c0ad'
IIS_NAME='original_iis_upload_transaction_r1315.py'
IIS_SHA='97146eb28799d16538771a2855edc9fb8dd41f10ca455667e046e16025cfcd01'
LIMITS_NAME='original_iis_upload_limits_r1313.py'
LIMITS_SHA='b6c7f7140264e434d77c892954d70ca5565e1a4711848f0a154064c15b83f0a1'
IIS_FIELD='serverDerivedIISUploadLimits'
UPDATER='tools/original_public_test_update.py'
FIELD='unifiedAttachmentDelivery'
PLAN_FIELD='unifiedAttachmentBaseR48'
REVISION='20261106-R49-unified-attachment-home-and-supervision'

def need(ok,code):
    if not ok:raise ValueError(code)

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def digest(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pin(path):return {'bytes':Path(path).stat().st_size,'sha256':digest(path)}
def regular(path):
    path=Path(path).absolute();need('..'not in path.parts,'R49_NORMAL_PATH_REQUIRED')
    for part in [*reversed(path.parents),path]:
        need(not part.is_symlink()and(not part.exists()or not getattr(part.lstat(),'st_file_attributes',0)&0x400),'R49_REPARSE_REFUSED')
    return path
def read(path):
    path=regular(path);need(path.is_file()and path.stat().st_size<=8*1024**2,'R49_BOUNDED_JSON_REQUIRED')
    def pairs(items):
        result={}
        for k,v in items:need(k not in result,'R49_DUPLICATE_JSON_KEY');result[k]=v
        return result
    def bad(_):raise ValueError('R49_NONFINITE_JSON')
    return json.loads(path.read_bytes(),object_pairs_hook=pairs,parse_constant=bad)
def module(name,path,expected):
    path=regular(path);need(path.is_file()and digest(path)==expected,'R49_EXACT_MODULE_REQUIRED:'+path.name)
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def contract():
    p=regular(HERE.with_name(CONTRACT_NAME));need(digest(p)==CONTRACT_SHA,'R49_FIXED_CONTRACT_REQUIRED')
    value=read(p);need(value.get('schema')=='xnby.unified-attachment-contract.r49.v1','R49_CONTRACT_SCHEMA_REQUIRED');return value
def expected_payload(base,c=None):
    c=contract()if c is None else c;value=copy.deepcopy(base)
    value['files']={n:r for n,r in base['files'].items()if not n.startswith('frontend/security_pc/')}
    value['files'].update(copy.deepcopy(c['safetyFiles']));value['files'].update(copy.deepcopy(c['productPins']))
    for name,path in [('tools/'+BASE_NAME,HERE.with_name(BASE_NAME)),('tools/'+PREIMAGE_NAME,HERE.with_name(PREIMAGE_NAME)),('tools/'+CONTRACT_NAME,HERE.with_name(CONTRACT_NAME)),('tools/'+IIS_NAME,HERE.with_name(IIS_NAME)),('tools/'+LIMITS_NAME,HERE.with_name(LIMITS_NAME)),(UPDATER,HERE)]:value['files'][name]=pin(regular(path))
    return value
def expected_release(payload_sha,c=None):
    c=contract()if c is None else c;value=copy.deepcopy(c['baseR48Release']);value.update(copy.deepcopy(c['metadataVariants']))
    value['controllerFiles'].update({n:r['sha256']for n,r in c['productPins'].items()if n in c['baseR48Release']['controllerFiles']})
    for name,path in [('tools/'+BASE_NAME,HERE.with_name(BASE_NAME)),('tools/'+PREIMAGE_NAME,HERE.with_name(PREIMAGE_NAME)),('tools/'+CONTRACT_NAME,HERE.with_name(CONTRACT_NAME)),('tools/'+IIS_NAME,HERE.with_name(IIS_NAME)),('tools/'+LIMITS_NAME,HERE.with_name(LIMITS_NAME)),(UPDATER,HERE)]:value['controllerFiles'][name]=digest(regular(path))
    value[FIELD]=copy.deepcopy(c['descriptor']);value['publicTestRevision']=REVISION;value['payloadManifestSHA256']=payload_sha
    return value
def declared(release,c=None):
    if FIELD not in release:return False
    c=contract()if c is None else c;need(release==expected_release(release.get('payloadManifestSHA256'),c),'R49_EXACT_COMPOSED_RELEASE_REQUIRED');return True

def verify_business_class_sources(m,c,app,root):
    args_path=m.regular(root,'b/java-arguments.private.txt');need(args_path.is_file()and args_path.stat().st_size<=65536,'R49_BOUNDED_BUSINESS_ARGUMENT_FILE_REQUIRED')
    arguments=[json.loads(line)for line in args_path.read_text('utf8').splitlines()];need(len(arguments)<=512 and all(isinstance(a,str)for a in arguments),'R49_BOUNDED_BUSINESS_ARGUMENTS_REQUIRED')
    positions=[i for i,a in enumerate(arguments)if a in ('-cp','-classpath','--class-path')];need(len(positions)==1 and positions[0]+1<len(arguments),'R49_EXACT_BUSINESS_CLASSPATH_REQUIRED')
    entries=arguments[positions[0]+1].split(os.pathsep);need(len(entries)<=512,'R49_CLASSPATH_ENTRY_BOUND')
    prefix=[root/'b/own-supervision-pdf.jar',root/'b/classes',app/'payload/business/legacy-classes']
    need(len(entries)>=3 and [Path(p).absolute()for p in entries[:3]]==prefix,'R49_EXACT_SUPERVISION_RUNTIME_LEGACY_CLASSPATH_PREFIX_REQUIRED')
    jar=c['baseR48Release']['businessSupervisionPdf'];m.check_file(root,'b/own-supervision-pdf.jar',jar['sha256'],jar['bytes'])
    with zipfile.ZipFile(prefix[0])as archive:
        for relative,product in c['businessRunClasses'].items():
            need(relative not in archive.namelist(),'R49_SUPERVISION_MUST_NOT_SHADOW_PRODUCT_CLASS')
            row=c['productPins'][product]
            if product.startswith('payload/callback-overlay/'):
                m.check_file(root,'b/classes/'+relative,row['sha256'],row['bytes'])
            else:
                need(product=='payload/business/legacy-classes/'+relative,'R49_EXACT_LEGACY_PRODUCT_CLASS_MAPPING_REQUIRED')
                need(not m.regular(root,'b/classes/'+relative).exists(),'R49_UNKNOWN_RUNTIME_CLASS_SHADOWS_LEGACY_PRODUCT')
                m.check_file(app,product,row['sha256'],row['bytes'])
    return {'exactClasspathPrefixAndFourProductSourcesVerified':True,'privateArgumentValuesReturned':False}

def bind_candidate_static_preflight(original,static,module):
    # The frozen R48 wrapper captures its static contract in a closure. Clone
    # that exact preflight code with one new cell; never mutate the old runtime
    # or drop its original pool/Mapper/supervision checks.
    need(isinstance(original,types.FunctionType)and isinstance(static,types.FunctionType),'R49_EXACT_PREFLIGHT_FUNCTIONS_REQUIRED')
    names=original.__code__.co_freevars
    need(set(names)=={'m','original_preflight','staged_helper','static'}and original.__closure__ is not None,'R49_EXACT_FROZEN_PREFLIGHT_CLOSURE_REQUIRED')
    source=regular(HERE.with_name(BASE_NAME));need(digest(source)==BASE_SHA,'R49_FROZEN_PREFLIGHT_SOURCE_REQUIRED')
    need(Path(original.__code__.co_filename).absolute()==source and original.__code__.co_name=='preflight','R49_EXACT_FROZEN_PREFLIGHT_CODE_REQUIRED')
    cells=dict(zip(names,original.__closure__));need(cells['m'].cell_contents is module,'R49_PREFLIGHT_MODULE_BINDING_REQUIRED')
    old_static=cells['static'].cell_contents;core=cells['original_preflight'].cell_contents;staged=cells['staged_helper'].cell_contents
    need(all(isinstance(f,types.FunctionType)for f in [old_static,core,staged]),'R49_TRUSTED_PREFLIGHT_CELLS_REQUIRED')
    need(Path(old_static.__code__.co_filename).absolute()==source and old_static.__code__.co_name=='static'and Path(staged.__code__.co_filename).absolute()==source and staged.__code__.co_name=='staged_helper','R49_EXACT_RETAINED_STATIC_AND_HELPER_CELLS_REQUIRED')
    need(Path(core.__code__.co_filename).absolute()==regular(HERE.with_name(CORE_NAME))and core.__code__.co_name=='candidate_runtime_pool_preflight','R49_EXACT_ORIGINAL_CORE_PREFLIGHT_REQUIRED')
    def cell(value):
        def capture():return value
        return capture.__closure__[0]
    closure=tuple(cell(static)if name=='static'else cells[name]for name in names)
    bound=types.FunctionType(original.__code__,original.__globals__,original.__name__,original.__defaults__,closure)
    bound.__kwdefaults__=copy.copy(original.__kwdefaults__);bound.__annotations__=dict(original.__annotations__)
    need(bound.__code__ is original.__code__ and bound.__globals__ is original.__globals__ and cells['static'].cell_contents is old_static,'R49_PREFLIGHT_BODY_AND_ORIGINAL_CELLS_MUST_REMAIN_UNCHANGED')
    return bound

def runtime():
    c=contract();regular(HERE);module('r49_verified_preimage_helper',HERE.with_name(PREIMAGE_NAME),PREIMAGE_SHA)
    iis_transaction=module('r49_iis_transaction',HERE.with_name(IIS_NAME),IIS_SHA);limits=module('r49_iis_limits',HERE.with_name(LIMITS_NAME),LIMITS_SHA)
    need(c.get('serverDerivedIISUploadLimits')==iis_transaction.POLICY,'R49_EXACT_SERVER_DERIVED_IIS_POLICY_REQUIRED')
    need(digest(regular(HERE.with_name(CORE_NAME)))==CORE_SHA,'R49_RETAINED_LIFECYCLE_CORE_REQUIRED')
    old_factory=module('r49_retained_r48_legacy',HERE.with_name(BASE_NAME),BASE_SHA);legacy=old_factory.runtime()
    new_factory=module('r49_retained_r48_candidate',HERE.with_name(BASE_NAME),BASE_SHA);m=new_factory.runtime()
    original_declared=new_factory.declared
    def selected(release):return declared(release,c)if FIELD in release else original_declared(release)
    new_factory.declared=selected
    # Register a source variant only in the candidate runtime. Old installed
    # releases continue through a separate unmodified R48/R46 module instance.
    m.R38_PARAMETER_PIN=copy.deepcopy(c['parameterPin']);m.R38_MAPPER_CONTRACT=copy.deepcopy(c['metadataVariants']['nativeOriginalXmlMapperDefaults'])
    mapper=m.original_mapper_defaults_declared;pool=m.pool_control_pins;workflow=m.workflow_contract_for
    m.original_mapper_defaults_declared=lambda release:mapper(release)if FIELD in release and declared(release,c)else legacy.original_mapper_defaults_declared(release)
    m.pool_control_pins=lambda release:pool(release)if FIELD in release and declared(release,c)else legacy.pool_control_pins(release)
    m.workflow_contract_for=lambda release:workflow(release)if FIELD in release and declared(release,c)else legacy.workflow_contract_for(release)
    def static(release):
        if FIELD not in release:return legacy.static_performance_declared(release)
        need(declared(release,c),'R49_STATIC_FULL_GRAPH_REQUIRED')
        need(release.get(m.R37_STATIC_FIELD)==c['metadataVariants']['staticInitialLoadPerformance'],'R49_STATIC_DESCRIPTOR_REQUIRED');return True
    m.static_performance_declared=static
    candidate_health=m.health;candidate_preflight=bind_candidate_static_preflight(m.candidate_runtime_pool_preflight,static,m)
    def preflight(app,bundle,plan):
        release=read(bundle/'payload/release-manifest.json')
        if FIELD not in release:return legacy.candidate_runtime_pool_preflight(app,bundle,plan)
        declared(release,c);result=candidate_preflight(app,bundle,plan)
        need(result is not None and result.get('supervisionModuleAndInitializerPreflightPassed')is True,'R49_ORIGINAL_POOL_MAPPER_AND_SUPERVISION_PREFLIGHT_REQUIRED')
        for n,r in c['productPins'].items():
            root=bundle/'payload'if n in plan['files']else app;m.check_file(root,n,r['sha256'],r['bytes'])
        return dict(result,unifiedAttachmentSourcesPreflightPassed=True)
    def health(app,row,guarded=True,*,gateway_port=18892):
        release=read(app/'release-manifest.json')
        if FIELD not in release:return legacy.health(app,row,guarded,gateway_port=gateway_port)
        declared(release,c);candidate_health(app,row,guarded,gateway_port=gateway_port)
        for n,r in c['productPins'].items():m.check_file(app,n,r['sha256'],r['bytes'])
        root=Path(row['run']).absolute();need(root.parent==app/'UserData/OriginalServer/runs'and re.fullmatch(r'j[1-9][0-9]{0,3}',root.name),'R49_OWN_BUSINESS_RUN_REQUIRED')
        verify_business_class_sources(m,c,app,root)
        report=m.regular(root,'b/configured-dock-boundary-ready.properties');need(report.stat().st_size<=4096,'R49_BOUNDED_DOCK_REPORT_REQUIRED');v=m.marker(report)
        need(v.get('schema')=='xnby.configured-dock-boundary.r1250.v1'and all(v.get(k)=='true'for k in ['installed','originalGuardRetained','onlyOriginalHttpCaller','dnsSnapshotBounded'])and v.get('originalComponentPorts')=='4','R49_RETAINED_SOURCE_BOUND_DOCK_GUARD_REQUIRED')
        need(all(v.get(k,'').isdigit()and 1<=int(v[k])<=6 for k in ['configuredOrigins','configuredResources']),'R49_BOUNDED_DOCK_DESTINATIONS_REQUIRED')
        return {'retainedOriginalReadinessAndSupervisionPassed':True,'unifiedAttachmentClassesAndDockGuardReady':True,'businessDeliveryProvenByReadiness':False}
    def load_bundle(app,bundle,manifest_sha,*,expected_target=m.TARGET,expected_port=18892):
        app=regular(app);bundle=regular(bundle);m.check_file(bundle,'update-manifest.json',manifest_sha);plan=read(bundle/'update-manifest.json')
        need(app==Path(expected_target).absolute(),'R49_EXACT_APPLICATION_TARGET_REQUIRED')
        need(plan.get(PLAN_FIELD)==c['baseReference'],'R49_EXACT_FROZEN_R48_REFERENCE_REQUIRED')
        base,old_sha,_=legacy.load_bundle(app,bundle/'base-r48',c['baseReference']['manifestSHA256'],expected_target=expected_target,expected_port=expected_port)
        need(old_sha==c['acceptedOldReleaseSHA256'],'R49_EXACT_PUBLIC_BASE_REQUIRED')
        need(set(plan)==set(base)|{PLAN_FIELD,IIS_FIELD},'R49_EXACT_PLAN_KEYS_REQUIRED')
        mutable={'updateId','files','newReleaseSHA256','newPayloadManifestSHA256','oldPayloadFiles','removedFrontendFiles','legacyEntrySHA256','callbackOverlaySHA256',PLAN_FIELD,IIS_FIELD}
        need({k:v for k,v in plan.items()if k not in mutable}=={k:v for k,v in base.items()if k not in mutable},'R49_RETAINED_DATA_IDENTITY_IIS_TARGET_PORT_REQUIRED')
        need(plan['updateId']==c['updateId'],'R49_EXACT_UPDATE_ID_REQUIRED')
        need(plan.get(IIS_FIELD)==iis_transaction.POLICY,'R49_EXACT_DERIVED_IIS_PLAN_REQUIRED')
        need(len(plan['files'])<=1000 and sum(r['bytes']for r in plan['files'].values())<=64*1024**2,'R49_BOUNDED_SPARSE_FILES_REQUIRED')
        base_release=read(bundle/'base-r48/payload/release-manifest.json');need(base_release==c['baseR48Release'],'R49_EXACT_R48_RELEASE_INPUT_REQUIRED')
        base_payload=read(m.check_file(bundle/'base-r48/payload','payload-manifest.json',base_release['payloadManifestSHA256']))
        pm_path=m.check_file(bundle/'payload','payload-manifest.json',plan['newPayloadManifestSHA256']);release_path=m.check_file(bundle/'payload','release-manifest.json',plan['newReleaseSHA256'])
        payload=read(pm_path);release=read(release_path);need(payload==expected_payload(base_payload,c),'R49_ONLY_DECLARED_PAYLOAD_DELTA_ALLOWED')
        need(release==expected_release(digest(pm_path),c)and declared(release,c),'R49_ONLY_DECLARED_RELEASE_DELTA_ALLOWED')
        need(plan['callbackOverlaySHA256']==release['missingAuthOverlayManifestSHA256'],'R49_EXACT_NEW_CALLBACK_OVERLAY_REQUIRED')
        old=read(app/'release-manifest.json');old_payload=read(m.check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
        writes={n:{'bytes':r['bytes'],'SHA256':r['sha256']}for n,r in payload['files'].items()if old_payload['files'].get(n)!=r}
        for n in ['release-manifest.json','payload-manifest.json']:
            r=pin(bundle/'payload'/n);writes[n]={'bytes':r['bytes'],'SHA256':r['sha256']}
        removals={n:{'bytes':r['bytes'],'SHA256':r['sha256']}for n,r in old_payload['files'].items()if n not in payload['files']}
        need(all(n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))for n in removals),'R49_ONLY_RETIRED_FRONTEND_REMOVALS_ALLOWED')
        need(plan['files']==writes and plan['removedFrontendFiles']==removals and not set(writes)&set(removals),'R49_EXACT_CHANGED_AND_RETIRED_FILES_REQUIRED')
        need(plan['oldPayloadFiles']=={n:old_payload['files'][n]for n in writes if n in old_payload['files']},'R49_EXACT_OLD_PAYLOAD_PREIMAGES_REQUIRED')
        helper=module('r49_original_preimage_validator',HERE.with_name(PREIMAGE_NAME),PREIMAGE_SHA)
        overlay_module=module('r49_original_overlay_loader',app/'tools/original_callback_overlay.py',old['controllerFiles']['tools/original_callback_overlay.py'])
        legacy_pins=helper.checked_preimages(app,old,overlay_module.load_callback_overlay)
        need(plan['legacyEntrySHA256']==legacy_pins,'R49_ONLY_EXACT_TWO_CALLBACK_LEGACY_PREIMAGES_REQUIRED')
        changes={}
        for n,r in {**writes,**removals}.items():
            need(not n.startswith(('private/','UserData/','seed/','Assets/','runtime/')),'R49_CODE_ONLY_UPDATE_REQUIRED')
            before=old_payload['files'].get(n,{}).get('sha256')or old['controllerFiles'].get(n)
            if n=='release-manifest.json':before=old_sha
            elif n=='payload-manifest.json':before=old['payloadManifestSHA256']
            elif n in legacy_pins:before=legacy_pins[n][0]
            target=m.regular(app,n)
            if before is None:need(not target.exists(),'R49_UNKNOWN_EXISTING_PATH:'+n)
            else:m.check_file(app,n,before)
            after=None if n in removals else r['SHA256']
            if after is not None:m.check_file(bundle/'payload',n,after,r['bytes'])
            changes[n]={'before':before,'after':after}
        for n,h in release['controllerFiles'].items():m.check_file(bundle/'payload'if n in writes else app,n,h)
        # Original inner validator already scanned the full immutable program;
        # private rows are checked for preservation, never copied or sampled.
        for n,r in old_payload['files'].items():
            if n.startswith(('private/','UserData/','seed/','Assets/')):need(payload['files'].get(n)==r,'R49_PUBLIC_PRIVATE_DATA_ROWS_RETAINED')
        derived,_=iis_transaction.inspect_config(m,limits,app,old_payload['files'],plan['files']);need(not set(derived)&set(changes),'R49_IIS_CHANGE_COLLISION');changes.update(derived)
        return plan,old_sha,changes
    m.load_bundle=load_bundle;m.candidate_runtime_pool_preflight=preflight;m.health=health
    m.replace_code=iis_transaction.bind_replace(m,limits)
    m.R49_CONTRACT=c;m.R49_LEGACY_RUNTIME=legacy
    return m

if __name__=='__main__':runtime().main()
