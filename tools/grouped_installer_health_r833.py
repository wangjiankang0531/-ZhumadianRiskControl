"""Health profile for the exact owned R678 full-application candidate only.

This is not a public updater. It retains every R42 health/ownership/auth check,
recognizes the one new pinned controller, and requires the supervision report.
"""
from pathlib import Path
import hashlib,importlib.util,json

R=Path('D:/Project/Zhumadian')
APP=R/'_g/Application'
D=R/'Document/Deployment/grouped_installer_candidate_r831_20261104'
UPDATER=R/'Application/tools/original_public_test_update_r42_mapper_equivalence_r457.py'
UPDATER_SHA='5e63e0f3e1f7d1064b5ae1276bfee56d51ce58b0e0ea64f59e30238c1c2d8b30'

def need(value,reason):
    if not value:raise ValueError(reason)

def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def profile():
    need(sha(D/'full-source-and-restore-plan.private.json')=='55ff0db454498e562c7addb396ec2ea6354b900e19227d94598108fb35e1ed52','EXACT_INTEGRATED_PLAN_PIN_REQUIRED')
    plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes())
    need(plan.get('schema')=='xnby.integrated-online.owned-full-candidate.plan.v1'
         and plan.get('target')==str(APP) and plan.get('onlyExistingOwnedSyntheticFixture')is True,
         'EXACT_OWNED_SUPERVISION_PLAN_REQUIRED')
    candidate=D/'runtime-manifests/release-manifest.json'
    need(sha(candidate)==plan['runtimeCandidateReleaseSHA256'], 'EXACT_OWNED_SUPERVISION_RELEASE_REQUIRED')
    release=json.loads(candidate.read_bytes())
    need(sha(D/'runtime-manifests/payload-manifest.json')==plan['runtimePayloadManifestSHA256'],'EXACT_INTEGRATED_PAYLOAD_PIN_REQUIRED')
    need(release['payloadManifestSHA256']==plan['runtimePayloadManifestSHA256'],'EXACT_RUNTIME_MANIFEST_CHAIN_REQUIRED')
    helperPath=Path(plan['sources']['tools/original_supervision_release_support.py']['source'])
    need(sha(helperPath)==release['controllerFiles']['tools/original_supervision_release_support.py'],
         'PINNED_OWNED_SUPERVISION_HELPER_REQUIRED')
    helper=load('owned_supervision_helper_r680',helperPath)
    helper.descriptor(release)
    need(sha(UPDATER)==UPDATER_SHA,'ORIGINAL_R42_HEALTH_SOURCE_REQUIRED')
    runtime=load('owned_supervision_health_base_r680',UPDATER)
    n='tools/serve_original_server_release.py'
    # R42's metadata gate pins this controller in its history and pool checks.
    # Replace the expectation with the exact candidate bytes, retaining functions.
    controller=plan['sources'][n]
    need(controller['sha256']==release['controllerFiles'][n], 'DECLARED_SUPERVISION_CONTROLLER_REQUIRED')
    runtime.R36_HISTORY_CONTROLLER_PIN={'bytes':controller['bytes'],'sha256':controller['sha256']}
    return plan,runtime,helper

def health(app,row,*,gateway_port):
    app=Path(app).absolute()
    need(app==APP,'ONLY_EXISTING_OWNED_G_ALLOWED')
    plan,runtime,helper=profile()
    need(sha(app/'release-manifest.json')==plan['runtimeCandidateReleaseSHA256'],
         'OWNED_FULL_CANDIDATE_NOT_APPLIED')
    release=runtime.read(runtime.regular(app,'release-manifest.json'))
    runtime.check_file(app,'payload-manifest.json',plan['runtimePayloadManifestSHA256'])
    for name in ['tools/serve_original_server_release.py','tools/original_supervision_release_support.py']:
        runtime.check_file(app,name,release['controllerFiles'][name])
    config=app/'private/server-configuration.json'
    need({'bytes':config.stat().st_size,'sha256':sha(config)}==plan['runtimeConfigurationAfterPin'],'EXACT_INTEGRATED_TASK_CONFIGURATION_REQUIRED')
    runtime.health(app,row,True,gateway_port=gateway_port)
    run=Path(row['run']).absolute()
    need(run.parent==app/'UserData/OriginalServer/runs','OWNED_SUPERVISION_RUN_REQUIRED')
    result=helper.require_ready(app,release,run/'b')
    need(result is not None and result['installed']is True,'SUPERVISION_REPORT_REQUIRED')
    return {'originalR42HealthChecksRetained':True,'supervisionReady':True,
            'normalRoleHTTPAcceptedByStartup':False,'publicIISOrTLSAccepted':False}
