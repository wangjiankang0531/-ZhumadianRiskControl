"""R48 with exact event result metadata and retained supervision preflight.

R2 selects the staged module only when transported, otherwise the installed
module. Existing process, mutation, restoration, authentication and health
function bodies are retained from the first prepared R48 candidate.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).absolute()
CORE_NAME='original_public_test_base_r46.py'
CORE_SHA = '3884a7029205ab418d41d48d969c96e69c9798bc75d806c8d85b2f0b59ab1b88'
BASE_METADATA_SHA='241be37651aa5ed141d78fc6e0c119966cb5194f3770d3b6bf687be4b3f5c712'
FIELD='businessSupervisionPdf'
OUTER_FIELD='supervisionBaseR46'
UPDATER='tools/original_public_test_update.py'
CONTROLLER='tools/serve_original_server_release.py'
HELPER='tools/original_supervision_release_support.py'
CORE='tools/'+CORE_NAME
REVISION = '20261105-R48-event-write-results-home-and-supervision'
PINS = {'tools/serve_original_server_release.py': {'bytes': 27903, 'sha256': 'eb08fd00221f175d00d0bc62cef0b15b97217d2c19306e96fb434c715f3f9f3d'}, 'tools/original_supervision_release_support.py': {'bytes': 8300, 'sha256': '872e20abba87d10133da7008766e4ea8786786ff33064698d822b04eca8dccde'}, 'payload/business/run-template/own-supervision-pdf.jar': {'bytes': 20041203, 'sha256': '12b5023faf68bdbca1d462df66be75b507d9f40b02721b419a074f7645df3fcd'}, 'tools/original_public_test_base_r46.py': {'bytes': 316357, 'sha256': '3884a7029205ab418d41d48d969c96e69c9798bc75d806c8d85b2f0b59ab1b88'}}
DESCRIPTOR={'revision': 'original-supervision-spring-factories-v1', 'file': 'payload/business/run-template/own-supervision-pdf.jar', 'bytes': 20041203, 'sha256': '12b5023faf68bdbca1d462df66be75b507d9f40b02721b419a074f7645df3fcd', 'originalBusinessJarSHA256': '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'}

R47_LEGACY_PINS = {'tools/serve_original_server_release.py': {'bytes': 27903, 'sha256': 'eb08fd00221f175d00d0bc62cef0b15b97217d2c19306e96fb434c715f3f9f3d'}, 'tools/original_supervision_release_support.py': {'bytes': 8300, 'sha256': '872e20abba87d10133da7008766e4ea8786786ff33064698d822b04eca8dccde'}, 'payload/business/run-template/own-supervision-pdf.jar': {'bytes': 20041203, 'sha256': '12b5023faf68bdbca1d462df66be75b507d9f40b02721b419a074f7645df3fcd'}, 'tools/original_public_test_base_r46.py': {'bytes': 241433, 'sha256': '83244ea13218416b062285c44c01e925b95249243b3691543d6475e69b461251'}}
R47_LEGACY_UPDATER_SHA = '5ade6da03f3a1d7d483806154286829d123c4ae4bc70090a67911f0df8b78af0'
R48_EVENT_FIELD = 'emergencyEventWriteResults'
R48_RELEASE_METADATA = {'emergencyEventWriteResults': {'revision': 'event-form-boolean-write-and-detail-results-r996-v1', 'eventSource': 'src/views/emergencyResponse/response/info/addOrEdit.vue', 'beforeSourceSHA256': '65d6569ed0f56e422472caa23aefca101ecc0b57122c78042e9721c633ab2954', 'afterSourceSHA256': '5f7c014ab20e473475b2ef412af61f5019dfec2e0709799f549c29df7864359e', 'actualCompilerInputDiffFromRetainedR841': ['src/views/emergencyResponse/response/info/addOrEdit.vue'], 'compiledFrontend': {'files': 344, 'manifestSHA256': 'b0999ea69bf7ea24d008d2a43a643e576353b498b9960ff5e5b298e201de06d1'}, 'normalSaveRequiresCode0AndTrue': True, 'falseOrRejectedSaveKeepsEditorInput': True, 'invalidDetailsDoNotReplaceForm': True, 'postFixNormalOriginalSDKAccepted': False, 'publicAccepted': False}, 'nativePlanExerciseRetainedFrontend': {'revision': 'retained-features-original-online-forms-and-authenticated-bootstrap-v4', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 344, 'manifestSHA256': 'b0999ea69bf7ea24d008d2a43a643e576353b498b9960ff5e5b298e201de06d1'}}, 'changedCompiledSourcePaths': 31, 'actualCompiledSourceInventorySHA256': 'ddc3ee63dae0e32b91c8a0022ad1542a53fb322287a3170911a1755c33c0e322', 'originalLoginWorkflowAndPermissionsRetained': True, 'resourceDeleteCancellation': {'actions': ['cancel', 'close'], 'unknownRejectionsPropagated': True, 'relativeToR224OnlyThreeComponentsChanged': True, 'components': {'src/views/emergencyPlans/structured/components/expertsList.vue': '4a3f2979dc9dffafdd5582f528be602cf45e1b1b340aaf5927074a6be060366e', 'src/views/emergencyPlans/structured/components/goodsList.vue': '12ab095631066f1a7c8c64bcfe567888b8c5c48bff8524b17e7f54c862139456', 'src/views/emergencyPlans/structured/components/teamsList.vue': '867e696d9244c64da09bf906c03acf78eb13d1ead4282fe28d602f8d05f314b7'}}, 'researchRequiredLevelVisibility': {'component': 'src/views/emergencyResponse/response/info/detail.vue', 'beforeSHA256': '96f79d5373bdf2c7580abde20e95908d87f6e3c20c91f608b0ac2b055b2a36eb', 'afterSHA256': '639c4cb2daf37d6fa7c5a2f56102c2f26bcac0ea5a5632c2c0358fc8a01d5155', 'onlyResearchFormHiddenBindingChanged': True, 'baseReadonlyDetailVisibilityRetained': True, 'relativeToR40OnlyOneSourceChanged': True}, 'compiledSourceInventoryComparisonOrigin': 'retained-emergency-workflow-source-r17'}, 'emergencyOriginalFormBootstrap': {'revision': 'original-sdk-online-forms-and-canonical-authenticated-bootstrap-v1', 'compiledSourceDeltaFromR44': {'src/components/workflow/components/OriginalWorkflowOnlineFormR470.vue': {'bytes': 2551, 'sha256': 'abbd35fc8dd149551acc4258706bd5746726ece6d1331a8abd16bab01d0cca00'}, 'src/router/index.ts': {'bytes': 1798, 'sha256': '6f643bf842c6c98ac007dfd2d2c2d4e5d2fb924f83bf192a312ccbd986d8809e'}, 'src/components/workflow/components/businessForm.vue': {'bytes': 3614, 'sha256': '4ca60991bfa6965e4b6c173a8b762d923ce4d2fdf8303f291e2048848f1eaef6'}, 'src/OriginalAuthenticatedInstallerR817.ts': {'bytes': 363, 'sha256': 'bdf96d80fdd267e0965175333f1d665e3657683f7d99bb579027f56ec5db6371'}, 'src/global-import.ts': {'bytes': 890, 'sha256': 'b491dcab7a8fd8538f43cab1713c6c126209cbeea86795d803cca789cb6a3e01'}, 'src/components/workflow/components/OriginalWorkflowOnlineFormModelR470.ts': {'bytes': 5575, 'sha256': 'c2d0a881c86cf94c27585cfa06e427bf6575ec2df26a37472f17f5ecc763010d'}, 'src/components/workflow/info.vue': {'bytes': 13790, 'sha256': '5d5a3e102a70413a8991fce712f41de720b85b10af4fe8900250bbc93cb9c17c'}, 'src/views/emergencyResponse/response/info/addOrEdit.vue': {'bytes': 7477, 'sha256': '5f7c014ab20e473475b2ef412af61f5019dfec2e0709799f549c29df7864359e'}}, 'staticBase': '/zhumadian/emergency/branding-20261025/', 'originalApplicationBase': '/zhumadian/emergency/', 'originalRouterBase': '/zhumadian/emergency', 'completeGlobalComponentsRetained': True, 'onlyCodeLoadPromiseShared': True, 'originalSDKAndBackendRetained': True, 'newSupervisionModuleRequired': False, 'onlySupportedOriginalSchemaFieldsRendered': True, 'allOriginalNangangSchemasAccepted': False, 'actualIISOrPublicAcceptance': False}, 'homeTransferAssets': {'allOriginalGlyphsRetained': True, 'changedFiles': {'frontend/security_pc/assets/css/xnby-home-transfer-162b8ebe4004d78f.css': {'bytes': 381, 'sha256': '162b8ebe4004d78febc02d070c40734d9b1d0de66629d8aa6dfc83f63bd7797f'}, 'frontend/security_pc/assets/webp/home-background-415f7103fab4437c.webp': {'bytes': 2591292, 'sha256': '415f7103fab4437c13faeca1d33461c49cee62a3671e6ee290a3bb18e301fb97'}, 'frontend/security_pc/assets/woff2/YouSheBiaoTiHei-7af84bf1c97ae44e.woff2': {'bytes': 745328, 'sha256': '7af84bf1c97ae44e868e87303b6fcf485e7aa76cad58852ffaeb4c6c24e2d87b'}, 'frontend/security_pc/index.html': {'bytes': 2737, 'sha256': '730062a12cd7b52e4297302cbaaf3ed6756fa259e37297129ce8620a005aa562'}}, 'completeSecurityFrontendAfter': {'files': 840, 'manifestSHA256': 'bc5e0c96b588bb3155f63f90f661d5d29260e29b57bdc3436ae072b985207202'}, 'normalOriginalSDKAccepted': False, 'originalICCAndPixelsRetained': True, 'originalR45HTMLSHA256': '27b3a64cbac2189bc7ff39e7b797ce46b8afefc92e739ea6ba9b119c016bd296', 'publicAccepted': False, 'revision': 'lossless-navigation-assets-r900', 'staticFixturePixelChecksPassed': 3}}

def need(value,reason):
    if not value:raise ValueError(reason)

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def regular(path):
    path=Path(path).absolute()
    need('..'not in path.parts,'SUPERVISION_NORMAL_PATH_REQUIRED')
    for p in [path,*path.parents]:
        need(not p.is_symlink(),'SUPERVISION_REPARSE_REFUSED')
        if p.exists():need(not p.lstat().st_file_attributes&0x400,'SUPERVISION_REPARSE_REFUSED')
    return path
def read(path):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_SUPERVISION_JSON_KEY');out[k]=v
        return out
    def bad(value):raise ValueError('NONFINITE_SUPERVISION_JSON_VALUE')
    return json.loads(regular(path).read_bytes(),object_pairs_hook=pairs,parse_constant=bad)
def equal(a,b):return canonical(a)==canonical(b)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def _pin(path):return {'bytes':Path(path).stat().st_size,'sha256':digest(path)}
def declared(release):
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
    return True
def expected_release(base,payload_sha):
    release=copy.deepcopy(base)
    release['controllerFiles'].update({n:p['sha256']for n,p in PINS.items()if n.startswith('tools/')})
    release['controllerFiles'][UPDATER]=digest(HERE)
    release[FIELD]=copy.deepcopy(DESCRIPTOR);release['publicTestRevision']=REVISION;release['payloadManifestSHA256']=payload_sha
    return release
def expected_payload(base):
    payload=copy.deepcopy(base);payload['files'].update(copy.deepcopy(PINS));payload['files'][UPDATER]=_pin(HERE);return payload

def runtime():
    core=regular(HERE.with_name(CORE_NAME));need(core.is_file()and digest(core)==CORE_SHA,'PINNED_UNMODIFIED_R46_CORE_REQUIRED')
    m=load('frozen_r46_supervision_runtime',core)
    m.R48_UPDATER_PIN=_pin(HERE)
    original_load=m.load_bundle;original_history=m.history_declared;original_pool=m.pool_control_pins;original_controller=m.controller_pin_for;original_health=m.health;original_preflight=m.candidate_runtime_pool_preflight;original_static=m.static_performance_declared
    def history(release):
        if not declared(release):return original_history(release)
        m.require(release.get(m.R36_HISTORY_FIELD)==m.R36_HISTORY_CONTRACT,'EXACT_RETAINED_NATIVE_HISTORY_REQUIRED')
        m.require(release['controllerFiles'].get(m.R36_HISTORY_HELPER)==m.R36_HISTORY_HELPER_SHA,'EXACT_RETAINED_NATIVE_HISTORY_HELPER_REQUIRED')
        return True
    def pool(release):
        value=original_pool(release)
        if declared(release):value[CONTROLLER]=PINS[CONTROLLER]
        return value
    def controller(release):return PINS[CONTROLLER]['sha256']if declared(release)else original_controller(release)
    def static(release):
        if R48_EVENT_FIELD not in release:return original_static(release)
        need(declared(release),'EXACT_R48_SUPERVISION_REQUIRED_FOR_STATIC_CONTROLS')
        need(release.get(m.R37_STATIC_FIELD)==m.R37_STATIC_CONTRACT,'EXACT_RETAINED_STATIC_DESCRIPTOR_REQUIRED')
        expected=dict(m.R37_STATIC_BASE_METADATA['controllerFiles'])
        expected.update({n:p['sha256']for n,p in m.R37_STATIC_CONTRACT['files'].items()})
        expected[UPDATER]=digest(HERE)
        if m.original_mapper_defaults_declared(release):expected[m.R24_PARAMETER]=m.R38_PARAMETER_PIN['sha256']
        expected.update({n:p['sha256']for n,p in PINS.items()if n.startswith('tools/')})
        need(release.get('controllerFiles')==expected,'EXACT_COMPOSED_R48_STATIC_AND_ALL_CONTROL_PINS_REQUIRED')
        return True
    def staged_helper(app,bundle,plan,release):
        root=bundle/'payload'if HELPER in plan['files']else app
        path=m.check_file(root,HELPER,PINS[HELPER]['sha256'],PINS[HELPER]['bytes'])
        return load('pinned_supervision_candidate_helper',path)
    def preflight(app,bundle,plan):
        result=original_preflight(app,bundle,plan);release=read(bundle/'payload/release-manifest.json')
        if not declared(release):return result
        need(result is not None,'RETAINED_BOUNDED_POOL_PREFLIGHT_REQUIRED')
        static(release) # Validate the same post-replacement control contract before downtime.
        raw=m.regular(app,'private/server-configuration.json').read_bytes()
        need(len(raw)<=1024*1024 and hashlib.sha256(raw).hexdigest()==result['configurationSHA256'],'CONFIGURATION_CHANGED_DURING_SUPERVISION_PREFLIGHT')
        staged_helper(app,bundle,plan,release).configure_business(release,json.loads(raw))
        module_root=bundle/'payload' if DESCRIPTOR['file'] in plan['files'] else app
        m.check_file(module_root,DESCRIPTOR['file'],DESCRIPTOR['sha256'],DESCRIPTOR['bytes'])
        m.check_file(app,'payload/business/application.jar',DESCRIPTOR['originalBusinessJarSHA256'])
        return dict(result,supervisionModuleAndInitializerPreflightPassed=True)
    def health(app,row,guarded=True,*,gateway_port=18892):
        original_health(app,row,guarded,gateway_port=gateway_port)
        release=read(app/'release-manifest.json')
        if not declared(release):return None
        m.check_file(app,HELPER,PINS[HELPER]['sha256'],PINS[HELPER]['bytes'])
        m.check_file(app,DESCRIPTOR['file'],DESCRIPTOR['sha256'],DESCRIPTOR['bytes'])
        helper=load('pinned_installed_supervision_helper',app/HELPER)
        need(helper.require_ready(app,release,Path(row['run'])/'b')['installed']is True,'EXACT_SUPERVISION_RUNTIME_READY_REQUIRED')
        return {'supervisionReady':True,'normalRoleHTTPAcceptedByStartup':False}

    def outer_load(app,bundle,pin,*,expected_target=m.TARGET,expected_port=18892):
        app=regular(app);bundle=regular(bundle)
        m.check_file(bundle,'update-manifest.json',pin)
        plan=read(bundle/'update-manifest.json')
        if OUTER_FIELD not in plan:return original_load(app,bundle,pin,expected_target=expected_target,expected_port=expected_port)
        need(app==Path(expected_target).absolute(),'EXACT_SUPERVISION_APPLICATION_TARGET_REQUIRED')
        base_info=plan[OUTER_FIELD]
        need(isinstance(base_info,dict)and set(base_info)=={'relativeRoot','manifestSHA256','coreSHA256'}
             and base_info['relativeRoot']=='base-r46'and base_info['coreSHA256']==CORE_SHA,'EXACT_FROZEN_BASE_REFERENCE_REQUIRED')
        inner=bundle/'base-r46'
        base,old_sha,changes=original_load(app,inner,base_info['manifestSHA256'],expected_target=expected_target,expected_port=expected_port)
        base_release=read(inner/'payload/release-manifest.json');base_payload=read(inner/'payload/payload-manifest.json')
        metadata={k:v for k,v in base_release.items()if k!='payloadManifestSHA256'}
        need(hashlib.sha256(canonical(metadata)).hexdigest()==BASE_METADATA_SHA,'FROZEN_R46_BASE_METADATA_REQUIRED')
        need(set(plan)==set(base)|{OUTER_FIELD},'NO_EXTRA_SUPERVISION_PLAN_FIELDS')
        mutable={'updateId','files','newReleaseSHA256','newPayloadManifestSHA256','oldPayloadFiles',OUTER_FIELD}
        need(equal({k:v for k,v in plan.items()if k not in mutable},{k:v for k,v in base.items()if k not in mutable}),'ALL_R46_DATA_IDENTITY_SCOPE_CALLBACK_AND_REMOVAL_FIELDS_RETAINED')
        need(re.fullmatch(r'20261104-r47-home-supervision-from-r45',plan['updateId'])is not None,'EXACT_SUPERVISION_UPDATE_ID_REQUIRED')
        need(len(plan['files'])<=1000 and sum(p['bytes']for p in plan['files'].values())<=32*1024**2,'UNCHANGED_SPARSE_UPDATE_LIMIT_REQUIRED')
        for n in ['release-manifest.json','payload-manifest.json']:
            p=plan['files'].get(n);need(isinstance(p,dict)and set(p)=={'bytes','SHA256'},'NEW_RELEASE_AND_PAYLOAD_ROWS_REQUIRED');m.check_file(bundle/'payload',n,p['SHA256'],p['bytes'])
        release=read(bundle/'payload/release-manifest.json');payload=read(bundle/'payload/payload-manifest.json')
        payload_sha=digest(bundle/'payload/payload-manifest.json');release_sha=digest(bundle/'payload/release-manifest.json')
        need(plan['newPayloadManifestSHA256']==payload_sha and plan['newReleaseSHA256']==release_sha,'EXACT_OUTER_METADATA_FILE_PINS_REQUIRED')
        need(equal(payload,expected_payload(base_payload)),'ONLY_DECLARED_SUPERVISION_PAYLOAD_DELTA_ALLOWED')
        need(equal(release,expected_release(base_release,payload_sha))and declared(release),'ONLY_DECLARED_SUPERVISION_RELEASE_DELTA_ALLOWED')
        expected_files=copy.deepcopy(base['files'])
        for n,p in {**PINS,UPDATER:_pin(HERE)}.items():expected_files[n]={'bytes':p['bytes'],'SHA256':p['sha256']}
        for n in ['release-manifest.json','payload-manifest.json']:
            p=_pin(bundle/'payload'/n);expected_files[n]={'bytes':p['bytes'],'SHA256':p['sha256']}
        need(equal(plan['files'],expected_files),'EXACT_COMBINED_R46_SUPERVISION_FILE_SET_REQUIRED')
        old=read(app/'release-manifest.json');old_payload=read(m.check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
        need(equal(plan['oldPayloadFiles'],{n:old_payload['files'][n]for n in expected_files if n in old_payload['files']}),'EXACT_INSTALLED_PAYLOAD_PREIMAGES_REQUIRED')
        # The original base validator checks every retained extension. Also pin
        # every installed immutable program before any downtime; never read seed,
        # business data or private configuration through this program scan.
        for n,p in old_payload['files'].items():
            if n.startswith(('private/','UserData/','seed/','Assets/')):continue
            m.check_file(app,n,p['sha256'],p['bytes'])
        accepted=plan['acceptedOldReleases'][old_sha]
        for n,p in expected_files.items():
            m.check_file(bundle/'payload',n,p['SHA256'],p['bytes'])
            before=changes[n]['before']if n in changes else accepted['controllerFiles'].get(n)
            if before is None and n in old_payload['files']:before=old_payload['files'][n]['sha256']
            target=m.regular(app,n)
            if before is None:need(not target.exists(),'UNDECLARED_EXISTING_SUPERVISION_PATH:'+n)
            else:m.check_file(app,n,before)
            changes[n]={'before':before,'after':p['SHA256']}
        for n,p in release['controllerFiles'].items():
            root=bundle/'payload'if n in plan['files']else app;m.check_file(root,n,p)
        return plan,old_sha,changes

    m.history_declared=history;m.pool_control_pins=pool;m.controller_pin_for=controller
    m.load_bundle=outer_load;m.candidate_runtime_pool_preflight=preflight;m.health=health;m.static_performance_declared=static
    return m

if __name__=='__main__':runtime().main()
