"""Pinned complete client-offline original-scene successor; R49 lifecycle remains intact.

Local integration candidate, not an approved public release or a deploy command.
"""
from pathlib import Path
import copy, hashlib, importlib.util

HERE = Path(__file__).absolute()
BASE_SHA = 'fca03c5afb5afacfb47abdbd1a1af6b491b8d2b31ad22c4c54ea4685a13c9b7f'
HELPER_SHA = '3c47fc0090a542f26b10af25d4f8c745240e0e41214825062b34448a8954ea89'
RESOURCE_SHA = '8d2eb746db35dcb3a0b1b0cbcf0b27922d41007d939c62811e6d32abec0cbd79'
CONTRACT_SHA = '1548e91c6e6c1445d46a666e1dc13532b762bcea9e9da417707bb02cc40f3efd'

def need(ok, reason):
    if not ok: raise ValueError(reason)

def load(name, path, pin):
    path = Path(path).absolute()
    for p in [*path.parents, path]:
        if p.exists() or p.is_symlink():
            need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,
                 'SCENE_IIS_REDIRECTED_SOURCE_REFUSED')
    need(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==pin,
         'SCENE_IIS_EXACT_SOURCE_REQUIRED')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def runtime():
    legacy_factory=load('scene_iis_retained_r49',HERE.with_name('original_public_test_base_r49.py'),BASE_SHA)
    legacy=legacy_factory.runtime()
    h=load('scene_full_closed_profile',HERE.with_name('original_offline_scene_profile_r2191.py'),HELPER_SHA)
    profile=h.Profile(legacy,HERE.parent.parent,CONTRACT_SHA)
    resource=load('scene_full_resource_preflight',HERE.with_name('original_offline_scene_resource_preflight_r2192.py'),RESOURCE_SHA)
    candidate_factory=load('scene_iis_candidate_r49',HERE.with_name('original_public_test_base_r49.py'),BASE_SHA)
    c=candidate_factory.contract()
    need(legacy_factory.declared(profile.c['baseRelease'],c),'SCENE_IIS_VERIFIED_ORIGINAL_R49_GRAPH_REQUIRED')
    candidate_contract=copy.deepcopy(c)
    for n, row in profile.c['candidatePayload']['files'].items():
        if n in candidate_contract['productPins']:
            candidate_contract['productPins'][n]=copy.deepcopy(row)
    candidate_contract['metadataVariants']['staticInitialLoadPerformance']=copy.deepcopy(
        profile.c['candidateRelease']['staticInitialLoadPerformance'])
    # Select the complete graph and its exact retained product variants in a separate
    # factory. The independent original factory remains usable for recovery.
    candidate_factory.contract=lambda:copy.deepcopy(candidate_contract)
    candidate_factory.expected_release=lambda payload_sha,c=None:profile.release(payload_sha)
    m=candidate_factory.runtime()
    selected_names=('original_mapper_defaults_declared','pool_control_pins',
                    'workflow_contract_for','static_performance_declared',
                    'history_declared','controller_pin_for')
    for name in selected_names:
        new=getattr(m,name);old=getattr(legacy,name)
        def selected(release,new=new,old=old):
            if h.FIELD not in release:return old(release)
            need(profile.declared(release),'SCENE_IIS_EXACT_SELECTED_RELEASE_REQUIRED')
            return new(release)
        setattr(m,name,selected)
    h.install_selected_lifecycle(m,legacy,profile)
    new_health=m.health
    def health(app,row,guarded=True,*,gateway_port=18892):
        release=h.read(m.regular(app,'release-manifest.json'))
        if h.FIELD not in release:return legacy.health(app,row,guarded,gateway_port=gateway_port)
        need(profile.declared(release),'SCENE_IIS_EXACT_HEALTH_RELEASE_REQUIRED')
        return new_health(app,row,guarded,gateway_port=gateway_port)
    new_preflight=m.candidate_runtime_pool_preflight
    def preflight(app,bundle,plan):
        release=h.read(m.regular(bundle,'payload/release-manifest.json'))
        need(profile.declared(release),'SCENE_IIS_EXACT_PREFLIGHT_RELEASE_REQUIRED')
        result=new_preflight(app,bundle,plan)
        need(result.get('unifiedAttachmentSourcesPreflightPassed') is True,
             'SCENE_IIS_RETAINED_POOL_MAPPER_SUPERVISION_ATTACHMENT_CHECKS_REQUIRED')
        resources=resource.preflight(m,app,bundle,plan,release)
        return dict(result,completeOriginalSceneSourcesPreflightPassed=True,sceneResourcesPreflightPassed=True,sceneResourceChecks=resources)
    def load_bundle(app,bundle,pin,*,expected_target=m.TARGET,expected_port=18892):
        return profile.load_bundle(app,bundle,pin,expected_target=expected_target,expected_port=expected_port)
    m.load_bundle=load_bundle;m.health=health;m.candidate_runtime_pool_preflight=preflight
    m.SCENE_IIS_PROFILE=profile;m.SCENE_IIS_LEGACY_RUNTIME=legacy
    return m

if __name__=='__main__':
    runtime().main()
