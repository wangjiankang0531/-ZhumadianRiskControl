"""Pinned sparse update for an existing original-system public test installation.



The updater preserves the installed database, object store, credentials and IIS.

It requires a clean owned shutdown before changing code. No forced termination.

"""

from pathlib import Path, PurePosixPath

import argparse, contextlib, datetime, hashlib, http.client, json, os, re, shutil

import subprocess, sys, time, uuid, xml.etree.ElementTree as ET



TARGET = Path('C:/inetpub/wwwroot/Zhumadian/Application')

HOST = 'www.joinlinksmart.com'

IIS = Path('C:/inetpub/wwwroot/Zhumadian/Application/iis')



R22_RISK_SESSION_REVISION = "original-risk-current-session-atomic-v1"

R22_BACKEND_ROWS = {'payload/business/run-template/classes/com/iemp/endanger/server/hidden/service/impl/RiskLevelServiceImpl.class': {'bytes': 9885, 'sha256': '636822c3930a036ddb294dac990c1b9f0f3f62e09baa40afdd46feddcc30070c'}, 'payload/business/run-template/classes/com/iemp/endanger/server/hidden/controller/RiskLevelController.class': {'bytes': 6102, 'sha256': '7d866e4ca810f7de5de637964b38f1eecae1a0b3208ef03ebbe17d34f06fa33e'}, 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInitializer.class': {'bytes': 8132, 'sha256': '2acbb21cea5e8b9564852817f958224671a0097a83b7579bb17aadeaddf02d43'}, 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class': {'bytes': 8509, 'sha256': 'c3d248e58dc54512434d706a2ddab2c83c67f742888ec4f51c811d40ee8fd47b'}, 'payload/business/run-template/classes/META-INF/spring.factories': {'bytes': 476, 'sha256': '720599a74bc620942f85a97343c1fe11720bfd7988bf2f042be7d84e38228918'}}



R31_NATIVE_FIELD = 'nativeSessionDefaultContext'

R31_NATIVE_CLASS = 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class'

R31_NATIVE_PIN = {'sha256': 'a1ba06d94e2a0c23e755e9975ae14fe55ceafb5d3b5c086c821a5fdf6887fa37', 'bytes': 8483}

R31_NATIVE_CONTRACT = {'revision': 'native-current-user-default-context-v1', 'endpoint': '/api/oauth/CurrentUser', 'explicitSystemCode': False, 'interceptor': {'path': 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class', 'sha256': 'a1ba06d94e2a0c23e755e9975ae14fe55ceafb5d3b5c086c821a5fdf6887fa37', 'bytes': 8483}, 'originalSDKAndPermissionsRetained': True, 'cacheValidatedSessions': False}



R23_ASYNC_FIELD = 'platformAsyncRequestMetadata'

R23_ASYNC_CONTRACT = {'revision': 'original-async-request-by-value-v1', 'files': {'payload/platform/run-template/own-platform-async-request.jar': {'bytes': 11183, 'sha256': '027f4c83709fe23116aa5add92a612e75f15f287a9d95fdca37fd45e5999348f'}, 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class': {'bytes': 6959, 'sha256': '5786e6b82ffd0faba74e53bfc62dcad3d41f13d83235b9f3ad404937741d659e'}}, 'originalAsyncConfigSHA256': 'b692d97a18bee115146d705e411610db8f1b1ea5bd4ee13184d4a53bdd8734d4'}

R23_ASYNC_ROWS = {'payload/platform/run-template/own-platform-async-request.jar': {'bytes': 11183, 'sha256': '027f4c83709fe23116aa5add92a612e75f15f287a9d95fdca37fd45e5999348f'}, 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class': {'bytes': 6959, 'sha256': '5786e6b82ffd0faba74e53bfc62dcad3d41f13d83235b9f3ad404937741d659e'}}

R23_CONTROLLER = 'tools/serve_original_server_release.py'

R23_ASYNC_HELPER = 'tools/original_platform_async_release_support.py'

R23_CONTROLLER_SHA = '8b6006fac79e096939bfb7b2cffc333c1bcd39dc01f9d43070c68dee4f402660'

R23_HELPER_SHA = '541699cbbb7792f6f1b71813eed32f7441c6bf696539aed6deaa20d963eeb078'

R23_OLD_CONTROLLER_SHA = '8e86438c8651f9f3a3064be24196d40d0ab3b50cd91c93bf085bc7758cd0cc02'

R23_AUTH_ADAPTER_SHA = 'eae7642792992da2ed4d2f6ff94f55001bda649888c754ffb0aeba4a39ae19d5'



R23_JOB = 'tools/original_server_windows_job.py'

R23_JOB_SHA = 'e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'

R23_OLD_JOB_SHA = '2434c23b8c8a28eb006eb0839e629a506d57c8fdda364ae17bc601f0faa06eb3'



R24_WORKFLOW_FIELD = 'nativeTaskGuardAndTemporaryLayout'

R24_TASK_CLASS = 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'

R24_PARAMETER = 'tools/original_server_release_parameters.py'

R24_OLD_PARAMETER_SHA = '8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9'

R24_TASK_PIN = {'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}

R24_PARAMETER_PIN = {'bytes': 11055, 'sha256': 'caf82f852f3ab80d66378869b09497f21f2965975364394579351a4bfda14bc9'}

R24_WORKFLOW_CONTRACT = {'revision': 'original-task-nonempty-flow-and-short-temporary-v1',

    'taskController': dict(path=R24_TASK_CLASS, **R24_TASK_PIN),

    'parameterAdapter': dict(path=R24_PARAMETER, **R24_PARAMETER_PIN)}





R25_MATERIAL_FIELD = "materialExcelFileTransaction"

R25_MATERIAL_ROWS = {'payload/business/run-template/classes/com/iemp/endanger/server/materials/controller/MaterialsController.class': {'bytes': 5164, 'sha256': '5a8d0b4103492819aa211c44aac854f47bcac439fbb8dcbda827926300affa4f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport$1.class': {'bytes': 5289, 'sha256': 'f405405dd5bb633da5c41f16398c4dc16be7fd2599ecb3644fed14a809768f7f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport.class': {'bytes': 5109, 'sha256': '1506e3cb8d4ebcadbba67f8565ea8125c440b772343e0ad62b36194673e7287a'}}

R25_MATERIAL_CONTRACT = {"revision": "original-whole-file-material-import-v1", "classes": R25_MATERIAL_ROWS}



R26_TEAM_FIELD = "nativeTeamMemberMapper"

R26_TEAM_ROWS = {'payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml': {'bytes': 2568, 'sha256': '2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'}}

R26_TEAM_SOURCE = {'payload/business/application.jar': {'bytes': 1371849, 'sha256': '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'}, 'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class': {'bytes': 7764, 'sha256': '69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4'}}

R26_TEAM_CONTRACT = {"revision": "original-members-default-scan-v1", "resources": R26_TEAM_ROWS, "retainedSources": R26_TEAM_SOURCE}



R27_POOL_FIELD='runtimeConnectionPoolPolicy'

R27_POOL_POLICY={'revision': 'pool-family-budget-v2', 'mysqlMinimum': 24, 'mysqlMaximum': 256, 'reservedConnections': 12, 'maximumSinglePool': 128}

R27_POOL_PINS={'tools/serve_original_server_release.py': {'bytes': 27013, 'sha256': '6c16afcf99aba74e74ce6d05c55e9255871134594f91c96318f901ede61f4374'}, 'tools/original_server_release_parameters.py': {'bytes': 17734, 'sha256': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'}}

R27_POOL_WORKFLOW_CONTRACT={'revision': 'original-task-short-temp-and-pool-budget-v1', 'taskController': {'path': 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class', 'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}, 'parameterAdapter': {'path': 'tools/original_server_release_parameters.py', 'bytes': 17734, 'sha256': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'}}



R32_AVATAR_FIELD = "nativePortalAvatarSource"
R32_AVATAR_CONTRACT = {'revision': 'two-native-portal-avatar-source-and-original-default-icon-v1', 'headerSourceSHA256': '5ec7dd353ecdd6e67880d8940e2c42f80dc12e7a851174b1390f9eb80a726bb3', 'normalizerSourceSHA256': '1ee6ad59c92aea246ffe339ebf63ee14ad522405a178f7996e840387a270193d', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 339, 'manifestSHA256': '69592cf5a8116a1b5f22a44580ccff923da2a9afb0c5d5b37e36020c6087ec86'}}, 'originalLoginSDKAndPermissionsRetained': True, 'originalMissingPhotoRestored': False}
R32_OLD_FRONTENDS = {'security_pc': {'files': 836, 'manifestSHA256': '5eb8b07cd2335ca8f71ce48c44bf39d93f14c0c0d7728d0cdfd0a9d60db3a079'}, 'emergency_pc': {'files': 339, 'manifestSHA256': '8f29a9c8d157fb46bafdf926df4a9ab863101a10834c2900a5a9bc3a48630c15'}}
R32_OLD_UPDATER_SHA = "477cd84dbce633623db7d31d6bf1504455cbcfa114f44c53f4c5d751a00d64ac"

def r32_frontend_manifest(rows, role):
    prefix = 'frontend/' + role + '/'
    selected = {n: p for n, p in rows.items() if n.startswith(prefix)}
    raw = json.dumps(selected, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'files': len(selected), 'manifestSHA256': hashlib.sha256(raw).hexdigest()}


def r32_avatar_declared(release, payload):
    if R32_AVATAR_FIELD not in release:
        return False
    require(release[R32_AVATAR_FIELD] == R32_AVATAR_CONTRACT,
            'EXACT_R32_AVATAR_DESCRIPTOR_REQUIRED')
    for role, expected in R32_AVATAR_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(payload['files'], role) == expected,
                'EXACT_R32_COMPILED_FRONTEND_REQUIRED:' + role)
    return True


def r32_frontend_scope(name, release, payload):
    # load_bundle validates the entire fixed avatar contract before these legacy guards.
    return name.startswith('frontend/emergency_pc/') or (
        release.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT
        and name.startswith('frontend/security_pc/'))


R33_HEADER_FIELD = "nativeEmergencyProjectHeaderHome"
R33_HEADER_CONTRACT = {'revision': 'emergency-project-mark-and-canonical-home-v1', 'projectMarkSHA256': '509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d', 'layoutAdapterSHA256': '0c5e94c17387c2e980798a96d0734d53acb10ab87ee44d16c245afdebe7e46a8', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': '40119e3ca86085aeedb03efecc546d0f8297915f11952db5e7f92c625ea75426'}}, 'canonicalHome': '/home/index', 'legacyHomeAlias': '/home', 'originalAvatarAndAuthRetained': True, 'originalUserMenuDataRetained': True}
R33_OLD_FRONTENDS = {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 339, 'manifestSHA256': '69592cf5a8116a1b5f22a44580ccff923da2a9afb0c5d5b37e36020c6087ec86'}}
R33_OLD_UPDATER_SHA = '97139494d048254cfa559d58eb5125a00ff370c3422acebe59a216e7a37fe6f3'

def r33_project_header_bundle_contract(app, bundle, plan, old, release, payload):
    require(R33_HEADER_FIELD in release and release[R33_HEADER_FIELD] == R33_HEADER_CONTRACT,
            'EXACT_R33_PROJECT_HEADER_DESCRIPTOR_REQUIRED')
    require(R33_HEADER_FIELD not in old, 'R33_REQUIRES_EXACT_PRE_HEADER_BASE')
    require(old.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT
            and release.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT,
            'R33_RETAINS_ORIGINAL_R32_AVATAR_DESCRIPTOR')
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    require(native_default_declared(old, previous), 'R33_REQUIRES_RETAINED_R31_NATIVE_DEFAULT')
    for role, expected in R33_OLD_FRONTENDS.items():
        require(r32_frontend_manifest(previous['files'], role) == expected, 'EXACT_R32_FRONTEND_BASE_REQUIRED:' + role)
    for role, expected in R33_HEADER_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(payload['files'], role) == expected, 'EXACT_R33_COMPILED_FRONTEND_REQUIRED:' + role)
    updater = 'tools/original_public_test_update.py'
    require(old['controllerFiles'].get(updater) == R33_OLD_UPDATER_SHA, 'EXACT_R32_UPDATER_BASE_REQUIRED')
    require(set(plan['acceptedOldReleases']) == {sha(regular(app, 'release-manifest.json'))}, 'R33_ONLY_ONE_EXACT_INSTALLED_RELEASE_REQUIRED')
    require(plan.get('legacyEntrySHA256') == {}, 'R33_NO_LEGACY_SCRIPT_ADAPTATION')
    retained = lambda rows: {n:p for n,p in rows.items() if not n.startswith('frontend/emergency_pc/')}
    require(retained(previous['files']) == retained(payload['files']), 'R33_ALL_NON_EMERGENCY_PAYLOAD_BYTES_RETAINED')
    require({n:p for n,p in old['controllerFiles'].items() if n != updater} == {n:p for n,p in release['controllerFiles'].items() if n != updater}, 'R33_OTHER_19_CONTROLLERS_RETAINED')
    require(set(old['controllerFiles']) == set(release['controllerFiles']) and release['controllerFiles'][updater] == sha(Path(__file__)), 'R33_EXACT_UPDATER_AND_CONTROL_SET_REQUIRED')
    mutable = {'payloadManifestSHA256','controllerFiles','publicTestRevision','publicAccepted',R33_HEADER_FIELD}
    require({n:p for n,p in old.items() if n not in mutable} == {n:p for n,p in release.items() if n not in mutable}, 'R33_OTHER_RELEASE_CONTRACTS_RETAINED')
    require(release.get('publicAccepted') is False, 'R33_NOT_FULL_PUBLIC_ACCEPTANCE')
    changed = {n:p for n,p in payload['files'].items() if n.startswith('frontend/emergency_pc/') and previous['files'].get(n) != p}
    require(set(plan['files']) == set(changed) | {updater,'payload-manifest.json','release-manifest.json'}, 'R33_EXACT_FRONTEND_DELTA_AND_UPDATER_TRANSPORT')
    require(plan['oldPayloadFiles'] == {n:previous['files'][n]for n in changed if n in previous['files']}, 'R33_EXACT_OLD_CHANGED_FRONTEND_PINS')
    obsolete = {n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in previous['files'].items() if n.startswith('frontend/emergency_pc/') and n not in payload['files']}
    require(plan.get('removedFrontendFiles') == obsolete, 'R33_EXACT_EMERGENCY_OBSOLETE_ASSETS')
    for name,pin in changed.items():
        require(plan['files'][name] == {'bytes':pin['bytes'],'SHA256':pin['sha256']}, 'R33_EXACT_FRONTEND_TRANSPORT_PIN:' + name)
        check_file(bundle / 'payload', name, pin['sha256'], pin['bytes'])
    return True


R34_PENDING_FIELD = "nativeWorkflowPendingOperatorVisibility"
R34_PENDING_CONTRACT = {'revision': 'exact-native-pending-operator-visibility-v1', 'component': 'src/components/workflow/info.vue', 'componentSHA256': '273cf0fb1f9e691cd2e3f585bd67a29d95b82f9dd1f95b3d1ef9a593f6a9c510', 'adapterSHA256': '5fc16002b17ffa48f086166e9db0df7e91d4f15704dbb397a06af5fe161c12ac', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': 'c4d09d02af5cfb462e45a9ed5a2c6f6feafc11c9a866f435b61ed8892164f81f'}}, 'exactCurrentUserProcessAndOperatorMembership': True, 'pendingLookupFailureDoesNotOfferApproval': True, 'originalAuthAuditAPIsAndInitiatorRulesRetained': True, 'independentBeforeAddsignOpinionFixed': False}
R34_OLD_UPDATER_SHA = 'a05348d866afef8e72a507c80679ba99228be779ca33fd2efc9f80a27361ef21'

def r34_pending_visibility_bundle_contract(app, bundle, plan, old, release, payload):
    require(R34_PENDING_FIELD in release and release[R34_PENDING_FIELD] == R34_PENDING_CONTRACT,
            'EXACT_R34_PENDING_VISIBILITY_DESCRIPTOR_REQUIRED')
    require(old.get(R33_HEADER_FIELD) == R33_HEADER_CONTRACT and R34_PENDING_FIELD not in old, 'R34_REQUIRES_EXACT_R33_HEADER_BASE')
    require(old.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT
            and release.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT,
            'R34_RETAINS_ORIGINAL_R32_AVATAR_DESCRIPTOR')
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    require(native_default_declared(old, previous), 'R34_REQUIRES_RETAINED_R31_NATIVE_DEFAULT')
    for role, expected in R33_HEADER_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(previous['files'], role) == expected, 'EXACT_R33_FRONTEND_BASE_REQUIRED:' + role)
    for role, expected in R34_PENDING_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(payload['files'], role) == expected, 'EXACT_R34_COMPILED_FRONTEND_REQUIRED:' + role)
    updater = 'tools/original_public_test_update.py'
    require(old['controllerFiles'].get(updater) == R34_OLD_UPDATER_SHA, 'EXACT_R33_UPDATER_BASE_REQUIRED')
    require(set(plan['acceptedOldReleases']) == {sha(regular(app, 'release-manifest.json'))}, 'R34_ONLY_ONE_EXACT_INSTALLED_RELEASE_REQUIRED')
    require(plan.get('legacyEntrySHA256') == {}, 'R34_NO_LEGACY_SCRIPT_ADAPTATION')
    retained = lambda rows: {n:p for n,p in rows.items() if not n.startswith('frontend/emergency_pc/')}
    require(retained(previous['files']) == retained(payload['files']), 'R34_ALL_NON_EMERGENCY_PAYLOAD_BYTES_RETAINED')
    require({n:p for n,p in old['controllerFiles'].items() if n != updater} == {n:p for n,p in release['controllerFiles'].items() if n != updater}, 'R34_OTHER_19_CONTROLLERS_RETAINED')
    require(set(old['controllerFiles']) == set(release['controllerFiles']) and release['controllerFiles'][updater] == sha(Path(__file__)), 'R34_EXACT_UPDATER_AND_CONTROL_SET_REQUIRED')
    mutable = {'payloadManifestSHA256','controllerFiles','publicTestRevision','publicAccepted',R34_PENDING_FIELD}
    require({n:p for n,p in old.items() if n not in mutable} == {n:p for n,p in release.items() if n not in mutable}, 'R34_OTHER_RELEASE_CONTRACTS_RETAINED')
    require(release.get('publicAccepted') is False, 'R34_NOT_FULL_PUBLIC_ACCEPTANCE')
    changed = {n:p for n,p in payload['files'].items() if n.startswith('frontend/emergency_pc/') and previous['files'].get(n) != p}
    require(set(plan['files']) == set(changed) | {updater,'payload-manifest.json','release-manifest.json'}, 'R34_EXACT_FRONTEND_DELTA_AND_UPDATER_TRANSPORT')
    require(plan['oldPayloadFiles'] == {n:previous['files'][n]for n in changed if n in previous['files']}, 'R34_EXACT_OLD_CHANGED_FRONTEND_PINS')
    obsolete = {n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in previous['files'].items() if n.startswith('frontend/emergency_pc/') and n not in payload['files']}
    require(plan.get('removedFrontendFiles') == obsolete, 'R34_EXACT_EMERGENCY_OBSOLETE_ASSETS')
    for name,pin in changed.items():
        require(plan['files'][name] == {'bytes':pin['bytes'],'SHA256':pin['sha256']}, 'R34_EXACT_FRONTEND_TRANSPORT_PIN:' + name)
        check_file(bundle / 'payload', name, pin['sha256'], pin['bytes'])
    return True


R35_PERSONAL_FIELD = "nativePersonalWorkflowRoutes"
R35_PERSONAL_CONTRACT = {'revision': 'authenticated-native-personal-workflow-pages-v1', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 340, 'manifestSHA256': '59bbadf5cec69e037c62f9851610c441435510484befb0e51a4847405d33ce9b'}}, 'adapterSHA256': 'cea0cd6abb28bb580db1a4776653cffa4c0fd42afc64dfcbd2ed71a9c21a5667', 'compiledSourceSHA256': {'src/router/routes.ts': '31b82a48157c1004048c0c4513dbbd56e9a9c8b424f3114e85e4f4651bd202bd', 'src/views/home/index.vue': 'ab6114919d10462c9db5a5b88764a96d2238fe3633121a2e7070ac9bb0294ef6', 'src/views/workflow/completedMatters/index.vue': '11ef812b739e50276e3070a68da47e1b63cf92c9baa2413d8534e967ad756087', 'src/views/workflow/completedMatters/info/index.vue': '79e62a84017568a4c529d7f49bd9d7f4015d62f2b7399fe8b95dfe4519e17e21'}, 'originalAuthenticatedMenuLoaderAndBackendAPIsRetained': True, 'configuredMenuRoutesNotReplaced': True, 'missingPersonalPagesRegisteredAfterAuthentication': True, 'handledDetailReadOnly': True, 'originalPendingOperatorVisibilityRetained': True, 'publicIndependentBeforeAddsignOpinionFixed': False}
R35_OLD_UPDATER_SHA = '2d18035b3df4c4489f3e221c168b789cf94d2f4ae93d08fa98a88d5a2e20ec71'

def r35_personal_workflow_bundle_contract(app, bundle, plan, old, release, payload):
    require(R35_PERSONAL_FIELD in release and release[R35_PERSONAL_FIELD] == R35_PERSONAL_CONTRACT,
            'EXACT_R35_PERSONAL_WORKFLOW_DESCRIPTOR_REQUIRED')
    require(old.get(R34_PENDING_FIELD) == R34_PENDING_CONTRACT and R35_PERSONAL_FIELD not in old, 'R35_REQUIRES_EXACT_R34_PENDING_BASE')
    require(old.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT
            and release.get(R32_AVATAR_FIELD) == R32_AVATAR_CONTRACT,
            'R35_RETAINS_ORIGINAL_R32_AVATAR_DESCRIPTOR')
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    require(native_default_declared(old, previous), 'R35_REQUIRES_RETAINED_R31_NATIVE_DEFAULT')
    for role, expected in R34_PENDING_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(previous['files'], role) == expected, 'EXACT_R34_FRONTEND_BASE_REQUIRED:' + role)
    for role, expected in R35_PERSONAL_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(payload['files'], role) == expected, 'EXACT_R35_COMPILED_FRONTEND_REQUIRED:' + role)
    updater = 'tools/original_public_test_update.py'
    require(old['controllerFiles'].get(updater) == R35_OLD_UPDATER_SHA, 'EXACT_R34_UPDATER_BASE_REQUIRED')
    require(set(plan['acceptedOldReleases']) == {sha(regular(app, 'release-manifest.json'))}, 'R35_ONLY_ONE_EXACT_INSTALLED_RELEASE_REQUIRED')
    require(plan.get('legacyEntrySHA256') == {}, 'R35_NO_LEGACY_SCRIPT_ADAPTATION')
    retained = lambda rows: {n:p for n,p in rows.items() if not n.startswith('frontend/emergency_pc/')}
    require(retained(previous['files']) == retained(payload['files']), 'R35_ALL_NON_EMERGENCY_PAYLOAD_BYTES_RETAINED')
    require({n:p for n,p in old['controllerFiles'].items() if n != updater} == {n:p for n,p in release['controllerFiles'].items() if n != updater}, 'R35_OTHER_19_CONTROLLERS_RETAINED')
    require(set(old['controllerFiles']) == set(release['controllerFiles']) and release['controllerFiles'][updater] == sha(Path(__file__)), 'R35_EXACT_UPDATER_AND_CONTROL_SET_REQUIRED')
    mutable = {'payloadManifestSHA256','controllerFiles','publicTestRevision','publicAccepted',R35_PERSONAL_FIELD}
    require({n:p for n,p in old.items() if n not in mutable} == {n:p for n,p in release.items() if n not in mutable}, 'R35_OTHER_RELEASE_CONTRACTS_RETAINED')
    require(release.get('publicAccepted') is False, 'R35_NOT_FULL_PUBLIC_ACCEPTANCE')
    changed = {n:p for n,p in payload['files'].items() if n.startswith('frontend/emergency_pc/') and previous['files'].get(n) != p}
    require(set(plan['files']) == set(changed) | {updater,'payload-manifest.json','release-manifest.json'}, 'R35_EXACT_FRONTEND_DELTA_AND_UPDATER_TRANSPORT')
    require(plan['oldPayloadFiles'] == {n:previous['files'][n]for n in changed if n in previous['files']}, 'R35_EXACT_OLD_CHANGED_FRONTEND_PINS')
    obsolete = {n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in previous['files'].items() if n.startswith('frontend/emergency_pc/') and n not in payload['files']}
    require(plan.get('removedFrontendFiles') == obsolete, 'R35_EXACT_EMERGENCY_OBSOLETE_ASSETS')
    for name,pin in changed.items():
        require(plan['files'][name] == {'bytes':pin['bytes'],'SHA256':pin['sha256']}, 'R35_EXACT_FRONTEND_TRANSPORT_PIN:' + name)
        check_file(bundle / 'payload', name, pin['sha256'], pin['bytes'])
    return True


def r32_avatar_bundle_contract(app, bundle, plan, old, release, payload):
    if R36_HISTORY_FIELD in release or R36_HISTORY_FIELD in old:
        return history_bundle_contract(app,bundle,plan,old,release,payload)
    if R35_PERSONAL_FIELD in release or R35_PERSONAL_FIELD in old:
        return r35_personal_workflow_bundle_contract(app, bundle, plan, old, release, payload)
    if R34_PENDING_FIELD in release or R34_PENDING_FIELD in old:
        return r34_pending_visibility_bundle_contract(app, bundle, plan, old, release, payload)
    if R33_HEADER_FIELD in release or R33_HEADER_FIELD in old:
        return r33_project_header_bundle_contract(app, bundle, plan, old, release, payload)
    if not r32_avatar_declared(release, payload):
        require(R32_AVATAR_FIELD not in old, 'RETAINED_R32_AVATAR_CANNOT_BE_DROPPED')
        return False
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    require(native_default_declared(old, previous), 'R32_REQUIRES_RETAINED_R31_NATIVE_DEFAULT')
    require(R32_AVATAR_FIELD not in old, 'R32_REQUIRES_FIXED_PRE_AVATAR_BASE')
    for role, expected in R32_OLD_FRONTENDS.items():
        require(r32_frontend_manifest(previous['files'], role) == expected,
                'EXACT_R31_FRONTEND_BASE_REQUIRED:' + role)
    updater = 'tools/original_public_test_update.py'
    require(old['controllerFiles'].get(updater) == R32_OLD_UPDATER_SHA,
            'EXACT_R31_UPDATER_BASE_REQUIRED')
    require(set(plan['acceptedOldReleases']) == {sha(regular(app, 'release-manifest.json'))},
            'R32_ONLY_ONE_EXACT_INSTALLED_RELEASE_REQUIRED')
    require(plan.get('legacyEntrySHA256') == {}, 'R32_NO_LEGACY_SCRIPT_ADAPTATION')
    retained = lambda rows: {n: p for n, p in rows.items()
        if not n.startswith(('frontend/security_pc/', 'frontend/emergency_pc/'))}
    require(retained(previous['files']) == retained(payload['files']),
            'R32_ALL_NON_AVATAR_PAYLOAD_BYTES_MUST_BE_RETAINED')
    require({n: p for n, p in old['controllerFiles'].items() if n != updater}
            == {n: p for n, p in release['controllerFiles'].items() if n != updater},
            'R32_OTHER_19_CONTROLLERS_MUST_BE_RETAINED')
    require(set(old['controllerFiles']) == set(release['controllerFiles'])
            and release['controllerFiles'][updater] == sha(Path(__file__)),
            'R32_EXACT_UPDATER_AND_CONTROL_SET_REQUIRED')
    mutable_metadata = {'payloadManifestSHA256', 'controllerFiles', 'publicTestRevision',
                        'publicAccepted', R32_AVATAR_FIELD}
    require({n: p for n, p in old.items() if n not in mutable_metadata}
            == {n: p for n, p in release.items() if n not in mutable_metadata},
            'R32_OTHER_RELEASE_CONTRACTS_MUST_BE_RETAINED')
    require(release.get('publicAccepted') is False, 'R32_NOT_FULL_PUBLIC_ACCEPTANCE')
    prefix = ('frontend/security_pc/', 'frontend/emergency_pc/')
    changed = {n: p for n, p in payload['files'].items()
               if n.startswith(prefix) and previous['files'].get(n) != p}
    require(set(plan['files']) == set(changed) | {
            updater, 'payload-manifest.json', 'release-manifest.json'},
            'R32_EXACT_FRONTEND_DELTA_AND_UPDATER_TRANSPORT_REQUIRED')
    require(plan['oldPayloadFiles'] == {n: previous['files'][n] for n in changed
                                      if n in previous['files']},
            'R32_EXACT_OLD_CHANGED_FRONTEND_PINS_REQUIRED')
    obsolete = {n: {'bytes': p['bytes'], 'SHA256': p['sha256']}
                for n, p in previous['files'].items()
                if n.startswith(prefix) and n not in payload['files']}
    require(plan.get('removedFrontendFiles') == obsolete,
            'R32_EXACT_TWO_PORTAL_OBSOLETE_ASSETS_REQUIRED')
    for name, pin in changed.items():
        require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},
                'R32_EXACT_FRONTEND_TRANSPORT_PIN_REQUIRED:' + name)
        check_file(bundle / 'payload', name, pin['sha256'], pin['bytes'])
    return True



R36_HISTORY_FIELD = "nativeBeforeAddsignOpinionHistory"
R36_HISTORY_CONTRACT = {'revision': 'native-before-addsign-original-date-history-v1', 'files': {'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class': {'bytes': 7462, 'sha256': 'cf8d31615a3dc0bf76a577151f3a1f90757f3840c9593775b2358c583ac869fa'}, 'payload/platform/run-template/own-before-addsign-history.jar': {'bytes': 11949, 'sha256': '4031f4e36efc985e079f53c684441e7093498b2536d5afcf4c9e5c36805bd017'}}, 'sameOriginalDynamicTransactionAndConnection': True, 'originalNativeServiceCallGate': True, 'originalJavaDateFieldsCopied': True, 'newDatasourceDDLOrStatusCode': False, 'originalAsyncAndAuthArchivesRetained': True}
R36_HISTORY_CONTROLLER_PIN = {'bytes': 27519, 'sha256': '0cefbf4ae43beb8cc22e61354ec824cfdd9d0de08c74c614faa1746c3d0341ab'}
R36_HISTORY_HELPER = "tools/original_native_history_release_support.py"
R36_HISTORY_HELPER_SHA = '5af0e91e9ec9da66e47978dbe279d4e8f03c8becd0b8130d1f65d1b1f17456ab'

R36_OLD_UPDATER_SHA = 'e8f0d69d4db3494139b293631ddf3c58ba07d98557772d0e6de17c35995c2d23'

def history_bundle_contract(app,bundle,plan,old,release,payload):
    require(history_declared(release),'EXACT_NATIVE_HISTORY_EXTENSION_REQUIRED')
    require(R36_HISTORY_FIELD not in old and old.get(R35_PERSONAL_FIELD)==R35_PERSONAL_CONTRACT,'HISTORY_REQUIRES_EXACT_R35_BASE')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    require(native_default_declared(old,previous) and old.get(R23_ASYNC_FIELD)==R23_ASYNC_CONTRACT,'HISTORY_RETAINS_ORIGINAL_NATIVE_AUTH_AND_ASYNC')
    for role,expected in R35_PERSONAL_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(previous['files'],role)==expected and r32_frontend_manifest(payload['files'],role)==expected,'HISTORY_KEEPS_BOTH_R35_FRONTENDS')
    control='tools/original_public_test_update.py';newrows=R36_HISTORY_CONTRACT['files']
    require(old['controllerFiles'].get(control)==R36_OLD_UPDATER_SHA and old['controllerFiles'].get(R23_CONTROLLER)==R27_POOL_PINS[R23_CONTROLLER]['sha256'] and R36_HISTORY_HELPER not in old['controllerFiles'],'HISTORY_EXACT_OLD_CONTROLLER_SOURCES_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))} and plan.get('legacyEntrySHA256')=={} and plan.get('removedFrontendFiles')=={},'HISTORY_ONE_INSTALLED_BASE_NO_LEGACY_OR_ASSET_REMOVALS')
    require(not set(newrows).intersection(previous['files']),'HISTORY_NEW_PATHS_MUST_BE_ABSENT')
    require({n:p for n,p in payload['files'].items()if n not in newrows}==previous['files'],'HISTORY_ALL_PRIOR_PAYLOAD_BYTES_KEPT')
    require(all(payload['files'].get(n)==p for n,p in newrows.items()),'EXACT_HISTORY_PAYLOAD_PINS_REQUIRED')
    changed_controls={R23_CONTROLLER,R36_HISTORY_HELPER,control}
    require(set(release['controllerFiles'])==set(old['controllerFiles'])|{R36_HISTORY_HELPER} and {n:p for n,p in old['controllerFiles'].items()if n not in changed_controls}=={n:p for n,p in release['controllerFiles'].items()if n not in changed_controls},'HISTORY_RETAINS_OTHER_18_CONTROLS')
    require(release['controllerFiles'][control]==sha(Path(__file__)),'EXACT_HISTORY_UPDATER_REQUIRED')
    mutable={'payloadManifestSHA256','controllerFiles','publicTestRevision','publicAccepted',R36_HISTORY_FIELD}
    require({n:p for n,p in old.items()if n not in mutable}=={n:p for n,p in release.items()if n not in mutable} and release.get('publicAccepted')is False,'HISTORY_ALL_PRIOR_RELEASE_CONTRACTS_KEPT')
    required={**newrows,R23_CONTROLLER:R36_HISTORY_CONTROLLER_PIN,R36_HISTORY_HELPER:{'sha256':R36_HISTORY_HELPER_SHA},control:{'sha256':sha(Path(__file__))}}
    require(set(plan['files'])==set(required)|{'payload-manifest.json','release-manifest.json'} and plan['oldPayloadFiles']=={},'EXACT_SEVEN_HISTORY_TRANSPORT_PATHS_REQUIRED')
    for name,pin in required.items():
        actual=plan['files'][name];require(actual['SHA256']==pin['sha256']and('bytes'not in pin or actual['bytes']==pin['bytes']),'EXACT_HISTORY_TRANSPORT_PIN:'+name)
        check_file(bundle/'payload',name,pin['sha256'],pin.get('bytes'))
    return True

def history_declared(release):
    if R36_HISTORY_FIELD not in release:return False
    require(release[R36_HISTORY_FIELD] == R36_HISTORY_CONTRACT, 'EXACT_NATIVE_HISTORY_DESCRIPTOR_REQUIRED')
    require(release['controllerFiles'].get(R23_CONTROLLER) == R36_HISTORY_CONTROLLER_PIN['sha256'] and release['controllerFiles'].get(R36_HISTORY_HELPER) == R36_HISTORY_HELPER_SHA, 'EXACT_HISTORY_CONTROLLER_AND_HELPER_REQUIRED')
    return True


R38_MAPPER_FIELD='nativeOriginalXmlMapperDefaults'
R38_PARAMETER_PIN={'bytes': 18172, 'sha256': 'b804d7e29921fd70bab4db2f711d01175a35bf11a1a77dcf99a8d147e9f41471'}
R38_MAPPER_CONTRACT={'revision': 'original-xml-mapper-default-v1', 'parameterAdapter': {'path': 'tools/original_server_release_parameters.py', 'bytes': 18172, 'sha256': 'b804d7e29921fd70bab4db2f711d01175a35bf11a1a77dcf99a8d147e9f41471'}, 'originalBusinessJar': {'path': 'payload/business/application.jar', 'bytes': 1371849, 'sha256': '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'}, 'defaultResourcePattern': 'classpath*:/xml/**/*.xml', 'expectedOriginalXMLResources': 96, 'expectedOriginalXMLStatements': 226, 'onlyWhenNoExplicitMapperLocations': True, 'originalSQLBytesUnchanged': True, 'newDatasourceOrDDL': False}

def original_mapper_defaults_declared(release):
    controls = release['controllerFiles']
    if R38_MAPPER_FIELD not in release:
        require(controls.get(R24_PARAMETER) != R38_PARAMETER_PIN['sha256'], 'EXPLICIT_ORIGINAL_MAPPER_DEFAULTS_REQUIRED')
        return False
    require(release[R38_MAPPER_FIELD] == R38_MAPPER_CONTRACT, 'EXACT_ORIGINAL_MAPPER_DEFAULT_CONTRACT_REQUIRED')
    require(controls.get(R24_PARAMETER) == R38_PARAMETER_PIN['sha256'], 'EXACT_ORIGINAL_MAPPER_PARAMETER_SOURCE_REQUIRED')
    require(release.get(R27_POOL_FIELD) == R27_POOL_POLICY and history_declared(release), 'ORIGINAL_MAPPER_REQUIRES_RETAINED_POOL_AND_HISTORY')
    return True

def pool_control_pins(release):
    pins=dict(R27_POOL_PINS)
    if history_declared(release):pins[R23_CONTROLLER]=R36_HISTORY_CONTROLLER_PIN
    if original_mapper_defaults_declared(release):pins[R24_PARAMETER]=R38_PARAMETER_PIN
    return pins

def history_ready(app,row):
    release=read(regular(app,'release-manifest.json'))
    if not history_declared(release):return None
    payload=read(check_file(app,'payload-manifest.json',release['payloadManifestSHA256']))
    for name,pin in R36_HISTORY_CONTRACT['files'].items():
        require(payload['files'].get(name)==pin,'HISTORY_PAYLOAD_DECLARATION_REQUIRED')
        check_file(app,name,pin['sha256'],pin['bytes'])
    check_file(app,R36_HISTORY_HELPER,R36_HISTORY_HELPER_SHA)
    platform=regular(app,Path(row['platformRun']).absolute().relative_to(app).as_posix())
    require(platform.parent==app/'UserData/TianjinOriginalPlatform/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}',platform.name),'OWN_HISTORY_PLATFORM_RUNTIME_REQUIRED')
    for name,pin in R36_HISTORY_CONTRACT['files'].items():check_file(platform,name.split('/run-template/',1)[1],pin['sha256'],pin['bytes'])
    report=regular(platform,'before-addsign-history-ready.properties')
    require(report.is_file() and report.stat().st_size<=4096,'BOUNDED_HISTORY_REPORT_REQUIRED')
    properties=dict(line.split('=',1)for line in report.read_text(encoding='ascii').splitlines()if '='in line)
    require(properties.get('installed')=='true' and properties.get('originalEntityMapperAndServicePinned')=='true' and properties.get('originalTransactionAndConnectionUsed')=='true' and properties.get('newDatasourceOrDDL')=='false' and properties.get('normalRoleUIAcceptanceProvenByStartup')=='false' and properties.get('factories','').isdigit() and 1<=int(properties['factories'])<=4,'EXACT_NATIVE_HISTORY_READY_REQUIRED')
    return {'exactNativeServiceGateAndSameTransactionHistoryModuleReady':True,'normalRoleAcceptanceClaimedByStartup':False,'newDatasourceOrDDL':False}

def runtime_pool_declared(release):
    original_mapper_defaults_declared(release)

    controls=release['controllerFiles']

    if R27_POOL_FIELD not in release:

        require(controls.get(R23_CONTROLLER)!=R27_POOL_PINS[R23_CONTROLLER]['sha256']

                and controls.get(R24_PARAMETER)!=R27_POOL_PINS[R24_PARAMETER]['sha256'], 'EXPLICIT_POOL_POLICY_REQUIRED')

        return False

    require(release[R27_POOL_FIELD]==R27_POOL_POLICY,'EXACT_POOL_POLICY_REQUIRED')

    require(all(controls.get(n)==p['sha256']for n,p in pool_control_pins(release).items()),'EXACT_POOL_CONTROL_DECLARATIONS_REQUIRED')

    return True



def workflow_contract_for(release):

    if runtime_pool_declared(release):
        value=dict(R27_POOL_WORKFLOW_CONTRACT)
        if original_mapper_defaults_declared(release):value['parameterAdapter']={'path':R24_PARAMETER,**R38_PARAMETER_PIN}
        return value
    return R24_WORKFLOW_CONTRACT



def parameter_pin_for(release):

    return pool_control_pins(release)[R24_PARAMETER]if runtime_pool_declared(release)else R24_PARAMETER_PIN



def controller_pin_for(release):

    if history_declared(release):return R36_HISTORY_CONTROLLER_PIN['sha256']
    return R27_POOL_PINS[R23_CONTROLLER]['sha256']if runtime_pool_declared(release)else R23_CONTROLLER_SHA



def runtime_pool_bundle_contract(app,bundle,plan,old,release,payload):

    if not runtime_pool_declared(release):

        require(R27_POOL_FIELD not in old,'RETAINED_POOL_POLICY_CANNOT_BE_DROPPED')

        return False

    fresh=R27_POOL_FIELD not in old

    prior={R23_CONTROLLER:R23_CONTROLLER_SHA,R24_PARAMETER:R24_PARAMETER_PIN['sha256']}if fresh else{n:p['sha256']for n,p in R27_POOL_PINS.items()}

    if not fresh:require(runtime_pool_declared(old),'EXACT_RETAINED_POOL_POLICY_REQUIRED')

    require(all(old['controllerFiles'].get(n)==p for n,p in prior.items()),'EXACT_PREVIOUS_POOL_CONTROL_SOURCES_REQUIRED')

    require(old.get(R24_WORKFLOW_FIELD)==workflow_contract_for(old),'POOL_REQUIRES_PREVIOUS_WORKFLOW_DESCRIPTOR')

    allowed=set(R27_POOL_PINS)|{'tools/original_public_test_update.py'}|({R36_HISTORY_HELPER}if history_declared(release)else set())

    require({n:p for n,p in release['controllerFiles'].items()if n not in allowed}=={n:p for n,p in old['controllerFiles'].items()if n not in allowed},'POOL_OTHER_CONTROLLERS_MUST_BE_RETAINED')

    if fresh:require(set(R27_POOL_PINS).issubset(plan['files']),'COMPLETE_POOL_CONTROL_TRANSPORT_REQUIRED')

    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))

    allowed_native = {R31_NATIVE_CLASS} if native_default_declared(release, payload) else set()

    retained=lambda rows:{n:p for n,p in rows.items()if not r32_frontend_scope(n, release, payload) and n not in allowed_native and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files'])}

    require(retained(previous['files'])==retained(payload['files']),'POOL_NON_EMERGENCY_PAYLOAD_MUST_BE_RETAINED')

    for n,pin in pool_control_pins(release).items():

        if n in plan['files']:require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'EXACT_POOL_TRANSPORT_PIN_REQUIRED')

        check_file(bundle/'payload'if n in plan['files']else app,n,pin['sha256'],pin['bytes'])

    return True



def runtime_pool_ready(app,row):

    release=read(regular(app,'release-manifest.json'))

    if not runtime_pool_declared(release):return None

    require(workflow_ready(app,row)is not None,'POOL_RETAINED_WORKFLOW_RUNTIME_REQUIRED')

    for n,pin in pool_control_pins(release).items():check_file(app,n,pin['sha256'],pin['bytes'])

    run=regular(app,Path(row['run']).absolute().relative_to(app).as_posix())

    require(run.parent==app/'UserData/OriginalServer/runs'and re.fullmatch(r'j[1-9][0-9]{0,3}',run.name),'OWNED_POOL_RUNTIME_REQUIRED')

    report=regular(run,'connection-budget.json');require(report.is_file()and report.stat().st_size<=16384,'BOUNDED_POOL_REPORT_REQUIRED');value=read(report)

    require(set(value)=={'policy','datasources','maximumPoolConnections','reservedConnections','mysqlMaxConnections'}and value['policy']==R27_POOL_POLICY,'EXACT_POOL_REPORT_FIELDS_REQUIRED')

    rows=value['datasources'];require(isinstance(rows,list)and 2<=len(rows)<=32,'BOUNDED_POOL_DATASOURCE_REPORT_REQUIRED');seen=set();total=0

    for item in rows:

        require(isinstance(item,dict)and set(item)=={'side','name','hikariMaximum','hikariMinimumIdle','hikariConnectionTimeoutMillis','druidMaximum','maximumBudget'},'EXACT_POOL_DATASOURCE_FIELDS_REQUIRED')

        require(item['side']in ['platform','business']and isinstance(item['name'],str)and re.fullmatch('[A-Za-z0-9_-]{1,40}',item['name']),'POOL_DATASOURCE_IDENTITY_REQUIRED')

        key=(item['side'],item['name']);require(key not in seen,'DUPLICATE_POOL_DATASOURCE_REFUSED');seen.add(key)

        require(all(type(item[k])is int for k in ['hikariMaximum','hikariMinimumIdle','hikariConnectionTimeoutMillis','druidMaximum','maximumBudget']),'POOL_REPORT_INTEGER_REQUIRED')

        require(1<=item['hikariMaximum']<=128 and 0<=item['hikariMinimumIdle']<=item['hikariMaximum']and 250<=item['hikariConnectionTimeoutMillis']<=300000 and 1<=item['druidMaximum']<=128,'POOL_REPORT_BOUNDS_REQUIRED')

        require(item['maximumBudget']==max(item['hikariMaximum'],item['druidMaximum']),'POOL_DATASOURCE_BUDGET_MISMATCH');total+=item['maximumBudget']

    require({x[0]for x in seen}=={'platform','business'},'BOTH_COMPONENT_POOL_REPORTS_REQUIRED')

    require(type(value['maximumPoolConnections'])is int and value['maximumPoolConnections']==total and type(value['reservedConnections'])is int and value['reservedConnections']==12 and type(value['mysqlMaxConnections'])is int and value['mysqlMaxConnections']==max(24,total+12)<=256,'POOL_TOTAL_BUDGET_MISMATCH')

    return {'poolPolicyAndExactRuntimeSourcesMatched':True,'datasources':len(rows),'mysqlMaxConnections':value['mysqlMaxConnections'],'accountsSessionsBusinessRowsOrCredentialsRead':False}





def team_declared(release, payload):

    present = set(R26_TEAM_ROWS).intersection(payload['files'])

    require({n for n in payload['files'] if n.startswith('payload/business/run-template/classes/mapper/')}

            <= set(R26_TEAM_ROWS), 'UNDECLARED_TEAM_MAPPER_RESOURCE_REFUSED')

    if R26_TEAM_FIELD not in release:

        require(not present, 'EXPLICIT_TEAM_MAPPER_DESCRIPTOR_REQUIRED')

        return False

    require(release[R26_TEAM_FIELD] == R26_TEAM_CONTRACT, 'EXACT_TEAM_MAPPER_DESCRIPTOR_REQUIRED')

    require(material_declared(release, payload), 'TEAM_MAPPER_REQUIRES_RETAINED_MATERIAL_CONTRACT')

    require(all(payload['files'].get(n) == pin for n, pin in {**R26_TEAM_ROWS, **R26_TEAM_SOURCE}.items()),

            'EXACT_TEAM_MAPPER_AND_RETAINED_SOURCE_PINS_REQUIRED')

    return True





def team_bundle_contract(app, bundle, plan, old, release, payload):

    declared = team_declared(release, payload)

    if not declared:

        require(R26_TEAM_FIELD not in old and not set(R26_TEAM_ROWS).intersection(plan['files']),

                'RETAINED_TEAM_MAPPER_CANNOT_BE_DROPPED')

        return False

    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))

    require(old.get(R25_MATERIAL_FIELD) == R25_MATERIAL_CONTRACT

            and all(previous['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),

            'TEAM_UPDATE_REQUIRES_EXACT_INSTALLED_MATERIAL_BASE')

    fresh = R26_TEAM_FIELD not in old

    if fresh:

        require(not set(R26_TEAM_ROWS).intersection(previous['files'])

                and set(R26_TEAM_ROWS).issubset(plan['files']), 'COMPLETE_FRESH_TEAM_MAPPER_TRANSPORT_REQUIRED')

    else:

        require(old[R26_TEAM_FIELD] == R26_TEAM_CONTRACT

                and all(previous['files'].get(n) == pin for n, pin in R26_TEAM_ROWS.items()),

                'EXACT_RETAINED_TEAM_MAPPER_REQUIRED')

    retained = lambda files: {n: pin for n, pin in files.items()

        if not r32_frontend_scope(n, release, payload) and n not in R26_TEAM_ROWS and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files']) and not (native_default_declared(release, payload) and n == R31_NATIVE_CLASS)}

    require(retained(previous['files']) == retained(payload['files']), 'TEAM_UPDATE_OTHER_PAYLOAD_MUST_BE_RETAINED')

    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R26_TEAM_ROWS)

    if runtime_pool_declared(release):legal.update(R27_POOL_PINS)
    if native_default_declared(release, payload):legal.add(R31_NATIVE_CLASS)

    legal.update(n for n in payload['files'] if r32_frontend_scope(n, release, payload))
    if history_declared(release):legal.update(R36_HISTORY_CONTRACT['files']);legal.add(R36_HISTORY_HELPER)

    require(set(plan['files']) <= legal, 'TEAM_UPDATE_EXACT_TRANSPORT_SCOPE_REQUIRED')

    for name, pin in R26_TEAM_SOURCE.items():

        check_file(app, name, pin['sha256'], pin['bytes'])

    import zipfile

    source = 'payload/business/application.jar'

    with zipfile.ZipFile(regular(app, source)) as archive:

        info = archive.getinfo('xml/FirstAidTeamMembersMapper.xml')

        require(info.file_size == 2568, 'ORIGINAL_MEMBER_XML_SIZE_REQUIRED')

        raw = archive.read(info)

    require(hashlib.sha256(raw).hexdigest() == next(iter(R26_TEAM_ROWS.values()))['sha256'],

            'ORIGINAL_MEMBER_XML_BYTES_REQUIRED')

    for name, pin in R26_TEAM_ROWS.items():

        if name in plan['files']:

            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},

                    'EXACT_TEAM_MAPPER_TRANSPORT_PIN_REQUIRED')

        check_file(bundle / 'payload' if name in plan['files'] else app, name, pin['sha256'], pin['bytes'])

    return True





def team_ready(app, row):

    release = read(regular(app, 'release-manifest.json'))

    payload = read(check_file(app, 'payload-manifest.json', release['payloadManifestSHA256']))

    if not team_declared(release, payload):

        return None

    require(material_ready(app, row) is not None, 'TEAM_MAPPER_RUNTIME_REQUIRES_RETAINED_MATERIAL')

    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())

    require(run.parent == app / 'UserData/OriginalServer/runs'

            and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None, 'OWNED_TEAM_MAPPER_RUN_REQUIRED')

    business = regular(run, 'b')

    owner = marker(regular(business, 'server-owner.properties'))

    require(owner.get('schema') == 'zhumadian.original.server.owner.v1'

            and owner.get('ownerId') == row['ownerId'], 'TEAM_MAPPER_RUNTIME_OWNER_MISMATCH')

    for name, pin in {**R26_TEAM_ROWS, **R26_TEAM_SOURCE}.items():

        check_file(app, name, pin['sha256'], pin['bytes'])

        if name.startswith('payload/business/run-template/'):

            check_file(business, name.removeprefix('payload/business/run-template/'), pin['sha256'], pin['bytes'])

    return {'originalTeamMemberXMLAndRetainedServiceRuntimeBytePinned': True,

            'actualMappedStatementOrAuthenticatedBusinessAcceptanceClaimed': False,

            'businessRecordsAccountsSessionsOrCredentialsRead': False}





def material_declared(release, payload):

    present = set(R25_MATERIAL_ROWS).intersection(payload['files'])

    require({n for n in payload['files'] if n.startswith('payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport')}

            <= set(R25_MATERIAL_ROWS), 'UNDECLARED_MATERIAL_HELPER_REFUSED')

    if R25_MATERIAL_FIELD not in release:

        require(not present, 'EXPLICIT_MATERIAL_TRANSACTION_DESCRIPTOR_REQUIRED')

        return False

    require(release[R25_MATERIAL_FIELD] == R25_MATERIAL_CONTRACT,

            'EXACT_MATERIAL_TRANSACTION_DESCRIPTOR_REQUIRED')

    require(all(payload['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),

            'EXACT_MATERIAL_TRANSACTION_CLASS_PINS_REQUIRED')

    require(release.get(R24_WORKFLOW_FIELD) == workflow_contract_for(release)

            and release.get(R23_ASYNC_FIELD) == R23_ASYNC_CONTRACT,

            'MATERIAL_TRANSACTION_REQUIRES_RETAINED_WORKFLOW_AND_ASYNC')

    return True





def material_bundle_contract(app, bundle, plan, old, release, payload):

    if not material_declared(release, payload):

        require(not set(R25_MATERIAL_ROWS).intersection(plan['files']),

                'MATERIAL_CODE_WITHOUT_DECLARATION_REFUSED')

        return False

    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))

    team = team_bundle_contract(app, bundle, plan, old, release, payload)

    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R25_MATERIAL_ROWS) | (set(R26_TEAM_ROWS) if team else set())

    if runtime_pool_declared(release):legal.update(R27_POOL_PINS)
    if native_default_declared(release, payload):legal.add(R31_NATIVE_CLASS)

    legal.update(n for n in payload['files'] if r32_frontend_scope(n, release, payload))
    if history_declared(release):legal.update(R36_HISTORY_CONTRACT['files']);legal.add(R36_HISTORY_HELPER)

    require(set(plan['files']) <= legal, 'MATERIAL_UPDATE_TRANSPORT_SCOPE_REFUSED')

    obsolete = {n for n in previous['files'] if r32_frontend_scope(n, release, payload) and n not in payload['files']}

    require(set(plan.get('removedFrontendFiles', {})) == obsolete,

            'EXACT_OBSOLETE_EMERGENCY_ASSET_REMOVALS_REQUIRED')

    fresh = R25_MATERIAL_FIELD not in old

    if fresh:

        require(not set(R25_MATERIAL_ROWS).intersection(previous['files'])

                and set(R25_MATERIAL_ROWS).issubset(plan['files']),

                'COMPLETE_FRESH_MATERIAL_TRANSACTION_TRANSPORT_REQUIRED')

    else:

        require(old[R25_MATERIAL_FIELD] == R25_MATERIAL_CONTRACT

                and all(previous['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),

                'EXACT_RETAINED_MATERIAL_TRANSACTION_REQUIRED')

    # This fixed extension changes only emergency assets and the three exact material classes.

    retained = lambda files: {n: p for n, p in files.items()

        if not r32_frontend_scope(n, release, payload) and n not in R25_MATERIAL_ROWS and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files']) and not (team and n in R26_TEAM_ROWS) and not (native_default_declared(release, payload) and n == R31_NATIVE_CLASS)}

    require(retained(previous['files']) == retained(payload['files']),

            'MATERIAL_UPDATE_OTHER_PAYLOAD_BYTES_MUST_BE_RETAINED')

    require(all(r32_frontend_scope(n, release, payload) for n in plan.get('removedFrontendFiles', {})),

            'MATERIAL_UPDATE_ONLY_OBSOLETE_EMERGENCY_ASSETS_REMOVED')

    for name, pin in R25_MATERIAL_ROWS.items():

        if name in plan['files']:

            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},

                    'EXACT_MATERIAL_TRANSACTION_TRANSPORT_PIN_REQUIRED:' + name)

        check_file(bundle / 'payload' if name in plan['files'] else app,

                   name, pin['sha256'], pin['bytes'])

    return True





def material_ready(app, row):

    release = read(regular(app, 'release-manifest.json'))

    payload = read(check_file(app, 'payload-manifest.json', release['payloadManifestSHA256']))

    if not material_declared(release, payload):

        return None

    require(workflow_ready(app, row) is not None, 'MATERIAL_RUNTIME_OWNED_WORKFLOW_REQUIRED')

    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())

    business = regular(run, 'b')

    for name, pin in R25_MATERIAL_ROWS.items():

        check_file(app, name, pin['sha256'], pin['bytes'])

        check_file(business, name.removeprefix('payload/business/run-template/'),

                   pin['sha256'], pin['bytes'])

    return {'threeMaterialRuntimeClassesBytePinned': True,

            'businessRecordsAccountsSessionsOrCredentialsRead': False}





def workflow_declared(release, payload):

    if R24_WORKFLOW_FIELD not in release:

        require(R24_TASK_CLASS not in payload['files']

                and release['controllerFiles'].get(R24_PARAMETER) != R24_PARAMETER_PIN['sha256'],

                'EXPLICIT_WORKFLOW_GUARD_EXTENSION_REQUIRED')

        return False

    require(release[R24_WORKFLOW_FIELD] == workflow_contract_for(release),

            'EXACT_WORKFLOW_GUARD_DESCRIPTOR_REQUIRED')

    require(release.get(R23_ASYNC_FIELD) == R23_ASYNC_CONTRACT,

            'WORKFLOW_GUARD_REQUIRES_COMPLETE_ASYNC_EXTENSION')

    require(payload['files'].get(R24_TASK_CLASS) == R24_TASK_PIN

            and release['controllerFiles'].get(R24_PARAMETER) == parameter_pin_for(release)['sha256'],

            'EXACT_WORKFLOW_GUARD_PAYLOAD_AND_PARAMETER_REQUIRED')

    return True





def workflow_bundle_contract(app, bundle, plan, old, release, payload):

    if not workflow_declared(release, payload):

        require(R24_TASK_CLASS not in plan['files'], 'WORKFLOW_CLASS_WITHOUT_DECLARATION_REFUSED')

        return False

    fresh = R24_WORKFLOW_FIELD not in old

    if fresh:

        require(old['controllerFiles'].get(R24_PARAMETER) == R24_OLD_PARAMETER_SHA,

                'EXACT_ORIGINAL_PARAMETER_ADAPTER_REQUIRED')

        require({R24_TASK_CLASS, R24_PARAMETER}.issubset(plan['files']),

                'COMPLETE_WORKFLOW_GUARD_TRANSPORT_REQUIRED')

    else:

        require(old[R24_WORKFLOW_FIELD] == workflow_contract_for(old)

                and old['controllerFiles'].get(R24_PARAMETER) == parameter_pin_for(old)['sha256'],

                'EXACT_RETAINED_WORKFLOW_GUARD_REQUIRED')

    for name, pin in ((R24_TASK_CLASS, R24_TASK_PIN), (R24_PARAMETER, parameter_pin_for(release))):

        if name in plan['files']:

            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},

                    'EXACT_WORKFLOW_GUARD_TRANSPORT_PIN_REQUIRED:' + name)

        check_file(bundle / 'payload' if name in plan['files'] else app,

                   name, pin['sha256'], pin['bytes'])

    return True





def workflow_ready(app, row):

    release = read(regular(app, 'release-manifest.json'))

    payload_path = check_file(app, 'payload-manifest.json', release['payloadManifestSHA256'])

    if not workflow_declared(release, read(payload_path)):

        return None

    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())

    require(run.parent == app / 'UserData/OriginalServer/runs'

            and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None,

            'OWNED_WORKFLOW_GUARD_RUN_REQUIRED')

    business = regular(run, 'b')

    owner = marker(regular(business, 'server-owner.properties'))

    require(owner == {'schema': 'zhumadian.original.server.owner.v1', 'ownerId': row['ownerId']},

            'EXACT_WORKFLOW_GUARD_RUNTIME_OWNER_REQUIRED')

    check_file(app, R24_TASK_CLASS, R24_TASK_PIN['sha256'], R24_TASK_PIN['bytes'])

    parameter_pin=parameter_pin_for(release)

    check_file(app, R24_PARAMETER, parameter_pin['sha256'], parameter_pin['bytes'])

    check_file(business, R24_TASK_CLASS.removeprefix('payload/business/run-template/'),

               R24_TASK_PIN['sha256'], R24_TASK_PIN['bytes'])

    return {'taskControllerPinned': True, 'parameterAdapterPinned': True}





def sha(path):

    with Path(path).open('rb') as stream:

        return hashlib.file_digest(stream, 'sha256').hexdigest()



def read(path):

    return json.loads(Path(path).read_text(encoding='utf-8-sig'))



def require(condition, message):

    if not condition:

        raise ValueError(message)



def regular(root, relative=''):

    root = Path(root).absolute()

    if relative:

        parts = PurePosixPath(relative)

        require(str(parts) == relative and not parts.is_absolute() and all(

            p not in ('.', '..') and not re.search(r'[\\:\x00-\x1f]', p)

            and not p.endswith((' ', '.')) for p in parts.parts), 'EXACT_RELATIVE_PATH_REQUIRED')

        result = root.joinpath(*parts.parts)

    else:

        result = root

    # Check every ancestor too: an apparently regular root can sit below a junction.

    for candidate in [*reversed(result.parents), result]:

        if candidate.exists() or candidate.is_symlink():

            attrs = getattr(candidate.lstat(), 'st_file_attributes', 0)

            require(not candidate.is_symlink() and not attrs & 0x400, 'REDIRECTED_PATH_REFUSED')

    require(result.is_relative_to(root), 'OWNED_PATH_REQUIRED')

    return result



def atomic(path, data):

    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    # Keep the sibling temporary name short even when the target basename is long.

    temp = path.with_name('.zmd-' + uuid.uuid4().hex + '.tmp')

    try:

        with temp.open('xb') as stream:

            stream.write(data)

            stream.flush()

            os.fsync(stream.fileno())

        os.replace(temp, path)

    finally:

        if temp.exists():

            temp.unlink()



def write_json(path, value):

    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))



@contextlib.contextmanager

def server_lock(app):

    import msvcrt

    with regular(app, 'UserData/OriginalServer/server-owner.lock').open('r+b') as lock:

        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)

        try:

            yield

        finally:

            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)



def check_file(root, name, pin, size=None):

    path = regular(root, name)

    require(path.is_file() and sha(path) == pin and

            (size is None or path.stat().st_size == size), 'FILE_PIN_MISMATCH:' + name)

    return path




R37_STATIC_FIELD = "staticInitialLoadPerformance"
R37_STATIC_CONTRACT = {'revision': 'gzip-hash-assets-no-store-html-api-v1', 'files': {'tools/original_project_branding.py': {'bytes': 6955, 'sha256': 'a8ba77817ab0fd3f1e45d06605204c27f2840f27aedb392f6590a91a9c3def4c'}, 'deploy/iis_original/App_Code/XnbyReferenceProxy.cs': {'bytes': 12869, 'sha256': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53'}, 'iis/App_Code/XnbyReferenceProxy.cs': {'bytes': 12869, 'sha256': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53'}}, 'onlyPublicStaticGETHEADNegotiatesGzip': True, 'encodedResponseBytesPreserved': True, 'contentEncodingAndVaryForwarded': True, 'successfulHashedAssetsImmutable': True, 'htmlBusinessErrorsAndNonHashedResourcesNotLongCached': True, 'businessPayloadAuthDatabaseAndPrivateConfigurationUnchanged': True}
R37_STATIC_BASE_METADATA = {'schema': 'zhumadian.original.server.release.v1', 'releaseId': 'e5385db1-3ca6-4399-9ae5-64dc3e442b27', 'controllerFiles': {'tools/serve_original_server_release.py': '0cefbf4ae43beb8cc22e61354ec824cfdd9d0de08c74c614faa1746c3d0341ab', 'tools/original_server_windows_job.py': 'e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22', 'tools/original_server_release_parameters.py': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106', 'tools/original_object_store_runtime.py': '7dedb5e278ada96ea1c64afa2e35bf4af03a9c645e1d27ab9570dc4a2ead77e1', 'tools/original_platform_files.py': '4c76b6349ace646857834f38861db0f796d57661fd2ec60cf0185289ee511d36', 'tools/portable_original_admin_frontend.py': '68f55f7a2e4ef7bebcec408dc2d7eb10f00ea7a4046e809d2139a07c7695b1c9', 'tools/readonly_original_static_archive.py': '5f89ccb0d17004f8d82b23ba3340902ffd6e830fe6e0278ba0618869ada3e6bc', 'tools/prepare_original_frontend_gateway.py': '006b17531f83d548d161b332531ff4c75e395816780744e033a52d56b5541cc8', 'tools/original_project_branding.py': 'e9e44d649dde71b89d1c2d5a9c93a11489d17811ecd46f83712f48be8b2f2af2', 'tools/reference_flat_runtime.py': '0b87b610cda9363db23ad8ab756aa1e44aa6b5be197ae6d74f96245b2e6d8ec6', 'deploy/iis_original/App_Code/XnbyReferenceProxy.cs': '1371eb2fcc04706a42463501a2e1b1bec14a83ca7fa6abd47177c71eed4da49a', 'deploy/iis_original/web.config.template': 'f6d4d4df1a859c203ac4a38973eb6d20b7b45b70b5cacfdf23e9c6d01996bc13', 'tools/original_callback_overlay.py': '85a1bd5238cc2b9423522683b00a3fb711aaa2982b5522f2d920a53c3f1bf151', 'tools/original_header_branding.py': '0e68e1ce9bfb20b2ef77cb3c6fcc4035593438fdbea027166748755ac066c2f2', 'tools/original_public_test_update.py': '67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca', 'tools/install_original_server_ingress.py': '6561368b6e88f7f08a377fd4399570cafc07d9bd1005b7d30ba8a8fd5a87768f', 'tools/original_iis_cutover.py': 'c6f55a4ab5a0d6445da87bf9722e29575e7a6430502992333680cea19e03bb4d', 'web.config': 'd3e3e7f58a5ba571d377c59a8f73a365730d8747b7e722226e540ff40ef0fed8', 'iis/Global.asax': '694ef766a4c998e750142d8687f36473fcb45557529d5865102de3d1dcac041b', 'tools/original_platform_async_release_support.py': '541699cbbb7792f6f1b71813eed32f7441c6bf696539aed6deaa20d963eeb078', 'tools/original_native_history_release_support.py': '5af0e91e9ec9da66e47978dbe279d4e8f03c8becd0b8130d1f65d1b1f17456ab'}, 'testRelease': True, 'originalBackendQAComplete': False, 'iisRuntimeVerified': False, 'publicAccepted': False, 'controllerRevision': '20261026-callback-r2', 'callbackProjectionExperimental': True, 'frontendRevision': 'original-event-operation-result-j58-20261029', 'workflowUserRequestCompatibilityExperimental': True, 'workflowRequestCompatibilityExperimental': True, 'requestErrorCompatibilityExperimental': True, 'approvalRetryCompatibilityExperimental': True, 'mobileApprovalCompatibilityExperimental': True, 'mobileRejectContractCompatibilityExperimental': True, 'mobilePaginationCompatibilityExperimental': True, 'businessResultCompatibilityExperimental': True, 'transactionObservationExperimental': True, 'transactionObservationRevision': 'existing-inventory-singleton-v2', 'passwordIdentityAliasExperimental': True, 'passwordIdentityAliasRevision': '20261026-user_id-to-userId', 'staticHeaderBrandingExperimental': True, 'staticHeaderBrandingRevision': '20261026-static-header-logo', 'missingAuthGuardExperimental': True, 'missingAuthGuardRevision': '20261026-web-context-and-preserved-lifecycle', 'missingAuthOverlayManifestSHA256': '91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb', 'excelJdkDesktopExperimental': True, 'excelJdkDesktopRevision': '20261026-fixed-font-boundary', 'inspectionPointEditCandidate': 'stable-child-ids-atomic-v1', 'inspectionPointNameCompatibilityExperimental': True, 'inspectionCombinedLocalRevision': '20261027-composed-tested-candidates', 'reservationEndTimeCandidate': 'original-end-time-atomic-v2', 'thirdPartyCredentialsCandidate': 'original-credentials-atomic-v2', 'workTransactionObservationCandidate': 'work-services-existing-singletons-v1', 'publicTestRevision': '20261103-R36-native-before-addsign-original-date-history', 'findingFailureObservationExperimental': True, 'findingFailureObservationRevision': '20261027-fixed-marker-metadata', 'trainingEmployeeEditCandidate': 'parent-first-atomic-v1', 'trainingTransactionObservationCandidate': 'parent-first-atomic-v1', 'workSafetyBatchEditCandidate': 'work-safety-batch-atomic-v1', 'workSafetyBatchObservationCandidate': 'work-safety-batch-atomic-v1', 'emergencyTeamAtomicCandidate': 'parent-first-save-edit-atomic-v1', 'emergencyTeamObservationCandidate': 'existing-singletons-manager-v1', 'eventDisposalAtomicCandidate': 'event-parent-record-atomic-v1', 'eventDisposalObservationCandidate': 'existing-singletons-manager-v1', 'emergencyExerciseAtomicCandidate': 'exercise-parent-files-atomic-v2', 'emergencyExerciseObservationCandidate': 'existing-singletons-manager-v1', 'applicationLayoutRevision': 'wwwroot-preserved-Application-v1', 'canonicalApplicationRoot': 'C:/inetpub/wwwroot/Zhumadian/Application', 'canonicalIISRoot': 'C:/inetpub/wwwroot/Zhumadian/Application/iis', 'platformTemporaryPathRevision': 'owned-platform-data-t-run-v1', 'objectStoreReadinessRevision': 'live-ready-verified-buckets-bounded-503-v1', 'homeViewportRevision': 'browser-viewport-flex-clamp-and-nonblocking-decoration-v1', 'workplaceViewportRevision': 'container-resize-statistics-grid-table-header-v1', 'canonicalHomeRootRevision': 'exact-https-project-root-301-v1', 'workplaceTaskHeadersRevision': 'native-font-14-15-16-sizes-small-default-large-v2', 'platformAsyncRequestMetadata': {'revision': 'original-async-request-by-value-v1', 'files': {'payload/platform/run-template/own-platform-async-request.jar': {'bytes': 11183, 'sha256': '027f4c83709fe23116aa5add92a612e75f15f287a9d95fdca37fd45e5999348f'}, 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class': {'bytes': 6959, 'sha256': '5786e6b82ffd0faba74e53bfc62dcad3d41f13d83235b9f3ad404937741d659e'}}, 'originalAsyncConfigSHA256': 'b692d97a18bee115146d705e411610db8f1b1ea5bd4ee13184d4a53bdd8734d4'}, 'nativeTaskGuardAndTemporaryLayout': {'revision': 'original-task-short-temp-and-pool-budget-v1', 'taskController': {'path': 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class', 'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}, 'parameterAdapter': {'path': 'tools/original_server_release_parameters.py', 'bytes': 17734, 'sha256': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'}}, 'riskUnitNativeSessionCandidate': 'original-risk-current-session-atomic-v1', 'materialExcelFileTransaction': {'revision': 'original-whole-file-material-import-v1', 'classes': {'payload/business/run-template/classes/com/iemp/endanger/server/materials/controller/MaterialsController.class': {'bytes': 5164, 'sha256': '5a8d0b4103492819aa211c44aac854f47bcac439fbb8dcbda827926300affa4f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport$1.class': {'bytes': 5289, 'sha256': 'f405405dd5bb633da5c41f16398c4dc16be7fd2599ecb3644fed14a809768f7f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport.class': {'bytes': 5109, 'sha256': '1506e3cb8d4ebcadbba67f8565ea8125c440b772343e0ad62b36194673e7287a'}}}, 'nativeTeamMemberMapper': {'revision': 'original-members-default-scan-v1', 'resources': {'payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml': {'bytes': 2568, 'sha256': '2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'}}, 'retainedSources': {'payload/business/application.jar': {'bytes': 1371849, 'sha256': '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'}, 'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class': {'bytes': 7764, 'sha256': '69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4'}}}, 'runtimeConnectionPoolPolicy': {'revision': 'pool-family-budget-v2', 'mysqlMinimum': 24, 'mysqlMaximum': 256, 'reservedConnections': 12, 'maximumSinglePool': 128}, 'nativeSessionDefaultContext': {'revision': 'native-current-user-default-context-v1', 'endpoint': '/api/oauth/CurrentUser', 'explicitSystemCode': False, 'interceptor': {'path': 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class', 'sha256': 'a1ba06d94e2a0c23e755e9975ae14fe55ceafb5d3b5c086c821a5fdf6887fa37', 'bytes': 8483}, 'originalSDKAndPermissionsRetained': True, 'cacheValidatedSessions': False}, 'nativePortalAvatarSource': {'revision': 'two-native-portal-avatar-source-and-original-default-icon-v1', 'headerSourceSHA256': '5ec7dd353ecdd6e67880d8940e2c42f80dc12e7a851174b1390f9eb80a726bb3', 'normalizerSourceSHA256': '1ee6ad59c92aea246ffe339ebf63ee14ad522405a178f7996e840387a270193d', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 339, 'manifestSHA256': '69592cf5a8116a1b5f22a44580ccff923da2a9afb0c5d5b37e36020c6087ec86'}}, 'originalLoginSDKAndPermissionsRetained': True, 'originalMissingPhotoRestored': False}, 'nativeEmergencyProjectHeaderHome': {'revision': 'emergency-project-mark-and-canonical-home-v1', 'projectMarkSHA256': '509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d', 'layoutAdapterSHA256': '0c5e94c17387c2e980798a96d0734d53acb10ab87ee44d16c245afdebe7e46a8', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': '40119e3ca86085aeedb03efecc546d0f8297915f11952db5e7f92c625ea75426'}}, 'canonicalHome': '/home/index', 'legacyHomeAlias': '/home', 'originalAvatarAndAuthRetained': True, 'originalUserMenuDataRetained': True}, 'nativeWorkflowPendingOperatorVisibility': {'revision': 'exact-native-pending-operator-visibility-v1', 'component': 'src/components/workflow/info.vue', 'componentSHA256': '273cf0fb1f9e691cd2e3f585bd67a29d95b82f9dd1f95b3d1ef9a593f6a9c510', 'adapterSHA256': '5fc16002b17ffa48f086166e9db0df7e91d4f15704dbb397a06af5fe161c12ac', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': 'c4d09d02af5cfb462e45a9ed5a2c6f6feafc11c9a866f435b61ed8892164f81f'}}, 'exactCurrentUserProcessAndOperatorMembership': True, 'pendingLookupFailureDoesNotOfferApproval': True, 'originalAuthAuditAPIsAndInitiatorRulesRetained': True, 'independentBeforeAddsignOpinionFixed': False}, 'nativePersonalWorkflowRoutes': {'revision': 'authenticated-native-personal-workflow-pages-v1', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 340, 'manifestSHA256': '59bbadf5cec69e037c62f9851610c441435510484befb0e51a4847405d33ce9b'}}, 'adapterSHA256': 'cea0cd6abb28bb580db1a4776653cffa4c0fd42afc64dfcbd2ed71a9c21a5667', 'compiledSourceSHA256': {'src/router/routes.ts': '31b82a48157c1004048c0c4513dbbd56e9a9c8b424f3114e85e4f4651bd202bd', 'src/views/home/index.vue': 'ab6114919d10462c9db5a5b88764a96d2238fe3633121a2e7070ac9bb0294ef6', 'src/views/workflow/completedMatters/index.vue': '11ef812b739e50276e3070a68da47e1b63cf92c9baa2413d8534e967ad756087', 'src/views/workflow/completedMatters/info/index.vue': '79e62a84017568a4c529d7f49bd9d7f4015d62f2b7399fe8b95dfe4519e17e21'}, 'originalAuthenticatedMenuLoaderAndBackendAPIsRetained': True, 'configuredMenuRoutesNotReplaced': True, 'missingPersonalPagesRegisteredAfterAuthentication': True, 'handledDetailReadOnly': True, 'originalPendingOperatorVisibilityRetained': True, 'publicIndependentBeforeAddsignOpinionFixed': False}, 'nativeBeforeAddsignOpinionHistory': {'revision': 'native-before-addsign-original-date-history-v1', 'files': {'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class': {'bytes': 7462, 'sha256': 'cf8d31615a3dc0bf76a577151f3a1f90757f3840c9593775b2358c583ac869fa'}, 'payload/platform/run-template/own-before-addsign-history.jar': {'bytes': 11949, 'sha256': '4031f4e36efc985e079f53c684441e7093498b2536d5afcf4c9e5c36805bd017'}}, 'sameOriginalDynamicTransactionAndConnection': True, 'originalNativeServiceCallGate': True, 'originalJavaDateFieldsCopied': True, 'newDatasourceDDLOrStatusCode': False, 'originalAsyncAndAuthArchivesRetained': True}}


R38_FRONTEND_FIELD="nativePlanExerciseRetainedFrontend"
R38_FRONTEND_CONTRACT = {'revision': 'retained-features-original-online-forms-and-authenticated-bootstrap-v4', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 344, 'manifestSHA256': '65a99ad7cbcfc8ed0937b91944443596245b6725102a377fbe6409e7ffcda557'}}, 'changedCompiledSourcePaths': 30, 'actualCompiledSourceInventorySHA256': '63b56adbbe7687a369c470feb65973b472e7c53b19e356ebb103e4014f915de8', 'originalLoginWorkflowAndPermissionsRetained': True, 'resourceDeleteCancellation': {'actions': ['cancel', 'close'], 'unknownRejectionsPropagated': True, 'relativeToR224OnlyThreeComponentsChanged': True, 'components': {'src/views/emergencyPlans/structured/components/expertsList.vue': '4a3f2979dc9dffafdd5582f528be602cf45e1b1b340aaf5927074a6be060366e', 'src/views/emergencyPlans/structured/components/goodsList.vue': '12ab095631066f1a7c8c64bcfe567888b8c5c48bff8524b17e7f54c862139456', 'src/views/emergencyPlans/structured/components/teamsList.vue': '867e696d9244c64da09bf906c03acf78eb13d1ead4282fe28d602f8d05f314b7'}}, 'researchRequiredLevelVisibility': {'component': 'src/views/emergencyResponse/response/info/detail.vue', 'beforeSHA256': '96f79d5373bdf2c7580abde20e95908d87f6e3c20c91f608b0ac2b055b2a36eb', 'afterSHA256': '639c4cb2daf37d6fa7c5a2f56102c2f26bcac0ea5a5632c2c0358fc8a01d5155', 'onlyResearchFormHiddenBindingChanged': True, 'baseReadonlyDetailVisibilityRetained': True, 'relativeToR40OnlyOneSourceChanged': True}, 'compiledSourceInventoryComparisonOrigin': 'retained-emergency-workflow-source-r17'}
R38_FRONTEND_ROWS = {'frontend/emergency_pc/favicon.ico': {'bytes': 54273, 'sha256': 'f22baa0ffd6a8db2fea9dfb4ae6285a8318194c0d6cff5d495a5c010ec7e8a2e'}, 'frontend/emergency_pc/index.html': {'bytes': 2426, 'sha256': '191a7e970e1964f4135d644e9eb45b3186cbd2f729a53413c72f42630ef9aaaf'}, 'frontend/emergency_pc/assets/css/activities-card-CZbuxhXw.css': {'bytes': 583, 'sha256': '15fd4adcb8ddee28d8d2ecfb33f3cdaa0b230109c75d5fc711e008e6dd540825'}, 'frontend/emergency_pc/assets/css/addOrEdit-BvKCNOiS.css': {'bytes': 13884, 'sha256': '11fba0c88944f24d6e7444d2400b123258f063e0991d03b9d28c4b15e64e4768'}, 'frontend/emergency_pc/assets/css/addOrEdit-SK9ao4fm.css': {'bytes': 104, 'sha256': '83bb539a99db128e2c21dac61c14c29329987f4efa57653ca9b0dc1571e858fc'}, 'frontend/emergency_pc/assets/css/alert-DHgn0A81.css': {'bytes': 3152, 'sha256': '0d65aa3f67f25f8ccd9a5ffdc98c264a3d92ad2f154442be1884c60e8b5e6031'}, 'frontend/emergency_pc/assets/css/authenticated-components-BCV6a_ls.css': {'bytes': 152351, 'sha256': '48e5e67acadd121c81593a9e6ceda731b2390519c011208eeea2eac8c9f37a46'}, 'frontend/emergency_pc/assets/css/card-CyGTQl3T.css': {'bytes': 931, 'sha256': 'c84ce1ef3fdd0229c199d1b261bf79331a909b973419e6d7200d8214d8407c3e'}, 'frontend/emergency_pc/assets/css/date-picker-NSevxL4s.css': {'bytes': 25877, 'sha256': '317655162a1f08b96b1f2f454c2bddd78fa6ccbb4dbe41a2a42f019af001f7b1'}, 'frontend/emergency_pc/assets/css/detail-C-9oMXeL.css': {'bytes': 197, 'sha256': 'f2177efb71b0d4c460f3637ced464144159f015e03339a61d4c290f3ced381bd'}, 'frontend/emergency_pc/assets/css/detail-CLryHg_2.css': {'bytes': 486, 'sha256': '07b26dc2ad0d690db1c0f1238efc2fc18f3c1677ed52e90545c0b2a4340d1f14'}, 'frontend/emergency_pc/assets/css/detail-CNKtIwKY.css': {'bytes': 97, 'sha256': 'cebda1f74e39cb47e0279937d75ec271b12fe2605ac4e5a4809e1b005394b216'}, 'frontend/emergency_pc/assets/css/eventList-NgkvF-8O.css': {'bytes': 142, 'sha256': 'e52ce5ae72344fd31be65cbdbbdbd0e779f44f8fc6772391514bfd4805110dc6'}, 'frontend/emergency_pc/assets/css/exerciseDetailDialog-DFC0HF7B.css': {'bytes': 348, 'sha256': 'f90d89caf5974a3df9ac30963a7bd2309f5a937e580da91c9d3272d32e3bdacc'}, 'frontend/emergency_pc/assets/css/exerciseDialog-BogGTbMN.css': {'bytes': 104, 'sha256': 'a6a1725edd1b2bb6e1db9e56559b5fbebc6a149a8a5e426aa23f7ec673e9fd16'}, 'frontend/emergency_pc/assets/css/exerciseList-Bvb0JIfw.css': {'bytes': 142, 'sha256': '1caf4d03dbc428d259cdf9251a7ddf66e083a885ad4c561ad08df7a6afa959c7'}, 'frontend/emergency_pc/assets/css/formList-mFdz4ucT.css': {'bytes': 565, 'sha256': '51d005eeeff63f0b43073f8c5e9cc280255c712d5de7577b152cb43e5a611283'}, 'frontend/emergency_pc/assets/css/goal-card-BkgNHKKo.css': {'bytes': 300, 'sha256': '6c1180e2f4ebc29931e6f92804eb267041dd57ce754d0689665be1a2cc5c9a8f'}, 'frontend/emergency_pc/assets/css/Imgs-BKOHgEFC.css': {'bytes': 2732, 'sha256': '2104d96eae0ff314a078171c6524b50dccc5f8f1a6a009a256a1c8bbe40f3a66'}, 'frontend/emergency_pc/assets/css/index-2mN1jRy8.css': {'bytes': 344, 'sha256': 'c5761fd696c2bf13fa63462d32d66df9df41c626bea51fca5df118251a1908b4'}, 'frontend/emergency_pc/assets/css/index-4EBdc1Mu.css': {'bytes': 441, 'sha256': '688cc600769146e49b73bc0475fea2665854ad40d2fa66bfe72ee89b5482e074'}, 'frontend/emergency_pc/assets/css/index-8Yxn9PaY.css': {'bytes': 58, 'sha256': '6cc68786414517163e2be9ca327092dba6a0692c892f6fb7a21690660185b906'}, 'frontend/emergency_pc/assets/css/index-BBoTrfAu.css': {'bytes': 58, 'sha256': '4123f94fe2d662cc89ee5a2fdf1fc5da1e049bdcc95d9533c6e1ce79075c8b01'}, 'frontend/emergency_pc/assets/css/index-BG31L1IX.css': {'bytes': 427, 'sha256': 'f05c4ef764b6718402e3c50d0156c8fb15aa5629d1c1b74d1a4d1b430851729a'}, 'frontend/emergency_pc/assets/css/index-BiyDmkFE.css': {'bytes': 770, 'sha256': '6a8f876c036bb4b8fb29f75cb76b4d05e5781995eafdd0f0a0e9fed1bb0a718c'}, 'frontend/emergency_pc/assets/css/index-BN3K_4b3.css': {'bytes': 58, 'sha256': '22985e4197dbaad60d01673991b7cb4b19a5fd57229e41a4d8328c9126b242ee'}, 'frontend/emergency_pc/assets/css/index-BVr5ZZGk.css': {'bytes': 671, 'sha256': 'ff9f5927f5a9f63d859ae0b6e4790445501981827ee6041c7b5ac626a9bf7895'}, 'frontend/emergency_pc/assets/css/index-C-S-m5i6.css': {'bytes': 60, 'sha256': '8298c75490534123cecb229062c27f0a7517187b8d9ae2b467bbf64c3a4ccfe5'}, 'frontend/emergency_pc/assets/css/index-C57pG7Yr.css': {'bytes': 93, 'sha256': '8574560b3fa4ccf8a5dd7ab48723686d38f3b01076adc5f14cbd387298c422ec'}, 'frontend/emergency_pc/assets/css/index-CaBBsn2b.css': {'bytes': 2053, 'sha256': '8977f69a8f8316febc426749d3a2161df7b5aa4e0624cc49544d4301b2ab7f1a'}, 'frontend/emergency_pc/assets/css/index-Cg9pbehc.css': {'bytes': 1001, 'sha256': '8bb1c7187463284797a7c832ffdf7b6cba6d430baabe9b3d58efbf90ce7d2ee0'}, 'frontend/emergency_pc/assets/css/index-CN-wOSGv.css': {'bytes': 426, 'sha256': '2920db8a2d170b8eb450f8aa78fc5ef0ed5e97866ac1d5b6c15aca8fed6590be'}, 'frontend/emergency_pc/assets/css/index-CnHGeBVz.css': {'bytes': 2638, 'sha256': '6483607656d8ced6e2757182be0275b297dd8d6714ea539dd8e64e9722ac80c5'}, 'frontend/emergency_pc/assets/css/index-CoSY25-e.css': {'bytes': 831, 'sha256': '76a2bc8d12caf93220bda6d8368111c91c010d3abf98e0b57f66a63f5957181f'}, 'frontend/emergency_pc/assets/css/index-CRXrVYsv.css': {'bytes': 867418, 'sha256': '4b34f117d0aaf505554964a852715bd15f8bcc2533abce3856ef8c1ae18380fb'}, 'frontend/emergency_pc/assets/css/index-CV6_It4b.css': {'bytes': 5464, 'sha256': 'a21f85633a6eff430953c1242299b450a10c95cf83b9f4eb407dcfc7846eb5f6'}, 'frontend/emergency_pc/assets/css/index-CyoSNaMF.css': {'bytes': 58, 'sha256': '674f053777354ea3809ee37e8b5b1f783d83a137c6e760e869e63a1a6abd8e87'}, 'frontend/emergency_pc/assets/css/index-D2C9J3FR.css': {'bytes': 58, 'sha256': '88157cac190723d7b4d7df203b7b87a3066d28902a8bb01ae34fbd1ea71459d7'}, 'frontend/emergency_pc/assets/css/index-D58Qj1xH.css': {'bytes': 178, 'sha256': '998ef62fa49e0ff61a65723cabe7647730e8f4a82cc5094b4df730b9a20d8819'}, 'frontend/emergency_pc/assets/css/index-DEF3qOjc.css': {'bytes': 58, 'sha256': 'e48ea4cfa556410f10c69dff007debd6ad72b374c835be6c30ef996476e03a93'}, 'frontend/emergency_pc/assets/css/index-DlYqIsOM.css': {'bytes': 1492, 'sha256': 'fb3fd583f999e1a418beeedae2cbeba781af68c90830ada7323604cf5cd41416'}, 'frontend/emergency_pc/assets/css/index-DoHeVWJz.css': {'bytes': 1527, 'sha256': '3daaae3155f3654601faec62daef4b2a2f1fb7bd39422c8658f3a1a61b7b9c5b'}, 'frontend/emergency_pc/assets/css/index-DTyfcoCY.css': {'bytes': 58, 'sha256': 'fe732f81cc3c93ca5f6bdfd26f97091ff80bbb78d0e62bc3248dbe13671f9749'}, 'frontend/emergency_pc/assets/css/index-DvgAUqqw.css': {'bytes': 58, 'sha256': 'c43a6b8432970f4d33dfe33428e9080d751fd5426ee67f16a8cbdaa75d4edcb3'}, 'frontend/emergency_pc/assets/css/index-DWXOVJQM.css': {'bytes': 2955, 'sha256': '7cfc017f3f486c771a739e6e5d0997a34b860df0b4a8ab1c8167856bbfc75159'}, 'frontend/emergency_pc/assets/css/index-NTk68GTK.css': {'bytes': 4156, 'sha256': '408ef059b48e225f7988175c1fce720bf6c432f57eacecd5d17ccfa73b44cc02'}, 'frontend/emergency_pc/assets/css/info-H5rVSFZy.css': {'bytes': 21557, 'sha256': '0daafbc8e767f5f85266d4a6720743040fd531d11d32ff08924eadbbc550c97e'}, 'frontend/emergency_pc/assets/css/link-card-BaI8iKIc.css': {'bytes': 325, 'sha256': 'ff5c28a28ae3934b0bf93a89e35782720440a69325beacf76f95d4176a539df1'}, 'frontend/emergency_pc/assets/css/link-COAyV-QT.css': {'bytes': 3177, 'sha256': 'caa2d35d4f62ba5d292da59eda74caf089814593b4f8ed8a96b8b6925fbc0cdc'}, 'frontend/emergency_pc/assets/css/list-BgePdby5.css': {'bytes': 142, 'sha256': '6c69450d0e3266f3271651c6a0af9abd424f2f6bfdfa3a477dfb98c11a580ecf'}, 'frontend/emergency_pc/assets/css/list-D_XDVIeP.css': {'bytes': 142, 'sha256': 'f7c913a348919d593c30fa8e75a6f7c3a5ffe915a25501502216dc412dca1fac'}, 'frontend/emergency_pc/assets/css/localData-BhhCYVWs.css': {'bytes': 3065, 'sha256': '3294a399b55b5db313c5ab02b70f242eb7c70537cadc7915b35148e4332eca1f'}, 'frontend/emergency_pc/assets/css/map-card-Db_rLdHj.css': {'bytes': 250, 'sha256': '990f004a58178a5f231f208bbc1dd9d6d4b9e0f4b37f87d0e4a131d02b6762ca'}, 'frontend/emergency_pc/assets/css/PersonDialog-Ra5K60Ff.css': {'bytes': 1174, 'sha256': '3f2cd96bfcf12271dd8aafea08b9c514faefa3c8e7d31184936a8860718d6841'}, 'frontend/emergency_pc/assets/css/personList-bVbmo1Ds.css': {'bytes': 142, 'sha256': '861abc19773be7824709cd6fef905d195478cebf9cae339667eab74c2625f531'}, 'frontend/emergency_pc/assets/css/profile-card-C1k6LaCU.css': {'bytes': 1216, 'sha256': '8bf6487ab16119981e4f933297433131d0b61910dfa58b543e0ef8c68cb6e6dc'}, 'frontend/emergency_pc/assets/css/project-card-CnpE5kYB.css': {'bytes': 94, 'sha256': 'dceacbfd9f96d613fd8d2f5f94e724d77a8637a1c90ebc0ee0d812420176f3ee'}, 'frontend/emergency_pc/assets/css/radio-DXoBifzg.css': {'bytes': 4363, 'sha256': 'a09f75b4488c7175a78864f5fbfc45546822d1f62376718f43da3561f8738bd7'}, 'frontend/emergency_pc/assets/css/radio-group-CVk8lhZF.css': {'bytes': 100, 'sha256': '515f435ac207a74981f3321f7726d7415c4de23abcf4c0e43e4afd6d72c94e7c'}, 'frontend/emergency_pc/assets/css/result-DFbetkHc.css': {'bytes': 1500, 'sha256': 'b7ba017dc6a9fa2abd2d332e177f7b6c6d85a192907cc9ebb5c497a77748c264'}, 'frontend/emergency_pc/assets/css/sale-card-C7VH_RZo.css': {'bytes': 3579, 'sha256': '70647ff0840853baaac4cd8b68de18c8b36c663df7574baa0dd103bd442ad7b7'}, 'frontend/emergency_pc/assets/css/statistics-card-C1Iq-Q-e.css': {'bytes': 1039, 'sha256': '8ca6b5b0383e40fdbe2e6d759d1d052bffdd1181e272ba313965840fef5b4467'}, 'frontend/emergency_pc/assets/css/statistics-card-C_Tmwukt.css': {'bytes': 1549, 'sha256': 'f6ed068de43924963286fecf5dcebe4e63abe916f14700a283b0d644d6999c33'}, 'frontend/emergency_pc/assets/css/task-card-Dln4nGYy.css': {'bytes': 576, 'sha256': '872d815d86a4e52988d9f9a7b30a75a486c81782575a762bdf9e738139f38481'}, 'frontend/emergency_pc/assets/css/timeline-item-DSj8Vu3_.css': {'bytes': 2631, 'sha256': '842560acb11bb0e5e108d90aa281b6eedc15e6cecc497604fb7738784ef0e709'}, 'frontend/emergency_pc/assets/css/tree-select-szutkSJz.css': {'bytes': 662, 'sha256': '75fcd25b9317f4aeaa2a98e49724c49df15e56d25c2cd0b23232f6db6c1ae3da'}, 'frontend/emergency_pc/assets/css/TreeFilter-IrcLqp-V.css': {'bytes': 278, 'sha256': '7060434dc8c3fed4e032b388d603b753878f7cf5d58fd42eda391ad73d71febf'}, 'frontend/emergency_pc/assets/css/user-account-IIHDLnd5.css': {'bytes': 512, 'sha256': '3a3dc543cb9bfbf16d041b63638ebd29a0a04b7e667942186098bf8da8bde71f'}, 'frontend/emergency_pc/assets/css/user-card-BHCttzZt.css': {'bytes': 1170, 'sha256': 'c04ebf0f7f8b5c3846899839d892acf1d3d7b05b95c123a5341c93ffe5f6f8d6'}, 'frontend/emergency_pc/assets/css/user-form-DaH1o311.css': {'bytes': 237, 'sha256': 'cb3b304cd21d4ad11093506383e05a878e5705317e30c0fe28b9c53c0a0f53be'}, 'frontend/emergency_pc/assets/css/user-list-BsgWbs9D.css': {'bytes': 413, 'sha256': '5520c85e4f24fe651f2a9987b4f0f684760843b181b72acf8a80fbadccc0af55'}, 'frontend/emergency_pc/assets/css/user-liveness-aAXqUv3k.css': {'bytes': 719, 'sha256': 'c8736c83f11ce80d6affa1a2f9ce45c882a46db99421a2c2c1cd11f1b25773e8'}, 'frontend/emergency_pc/assets/css/user-rate-BlmHAnZx.css': {'bytes': 2300, 'sha256': '79bb1431ecde99c2d2fb05f3c38633a5d3b6977817b56d82deb4cb3fa26e5474'}, 'frontend/emergency_pc/assets/css/user-satisfaction-x4qfb7T0.css': {'bytes': 1292, 'sha256': '1856f5e7c14fc9fa2ae9183a61c4e851c3560adaa279b84fea47859ad0b0afa6'}, 'frontend/emergency_pc/assets/js/wf-activities-card-DF728yfz.js': {'bytes': 2138, 'sha256': '47df9e7e71ab2d120b74ba8a502fb09408374c88edc492b3d2a204ffbda26863'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-2k5B55dr.js': {'bytes': 987, 'sha256': 'ba6a8b2b4fa3d18b15a41903b0b127ba97b6628b5a9602b8d28e57414e6abc95'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-BgdcX7zp.js': {'bytes': 525, 'sha256': '3ad59cff298c9fe220e1eab678c121b1b36b970380ed65c7328465f56434f117'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-BQWY46wb.js': {'bytes': 558, 'sha256': '9be4f562fce47a94e66d4421072f7b770f225cde918684dc35b9009a6d0d91be'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-Bv0s4Y0T.js': {'bytes': 876, 'sha256': '096612ddff1036cef82ae5030f32c1eab2e582f6d19d8bd19693dcbe42755c8e'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-BXIWabfV.js': {'bytes': 4481, 'sha256': '441a0abe8fb645ae1cd59a4bd3edc6addcf197fe42889e68d113db459c1ab95f'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-C8C5120T.js': {'bytes': 522, 'sha256': 'db0c1d1b6d18e4778e4383f1801fa4d039e8da1a861109d80c45a8c86572742e'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-DAnJgTre.js': {'bytes': 774, 'sha256': 'a2966929b7d3f0c3de0093ad717f2833bbfb8e810a8cfcbafa911b2a77aeb7f0'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-DbjFWV52.js': {'bytes': 546, 'sha256': 'f8345272eda0dc3033219a3d1a6e2c9c9b3e6d4b461e44ac972d50d6d80f9bf8'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit-ZGfeHB7s.js': {'bytes': 6376, 'sha256': '11ba0561a21aae3abd767a8188d60ffbee20c1bea73055bd2b9b342adb20e2b9'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-Be1tRO3k.js': {'bytes': 3038, 'sha256': 'f36c14010585387e8f2d9c20b5e6a86d1f36b092a99fbf9c9f6c8c7c8124bd8b'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-C7wR7tLi.js': {'bytes': 2737, 'sha256': '58f2c4a9b252d63eb8095a131920865c59f0a41c784692968bb4d7ec71f174c6'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-CMxMYSra.js': {'bytes': 3146, 'sha256': '907934801521d29cfe3b9fb24cad1a276aa239267735d4e56c70fde0a1c8daf5'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-Dgm-cHPC.js': {'bytes': 3480, 'sha256': 'f570d671e65791d1c74a2d2bcdbe7cc8793767734766941910183ba57a1d6329'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-DOrMVKuC.js': {'bytes': 5057, 'sha256': 'f8d0b0f0358a111661288d0bffcbdb55b5f1e115ce322801334933965d90a236'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-DVJNJ_M5.js': {'bytes': 2907, 'sha256': '3186295a94893d48a18702fc8043ce9d3978aeaf65a9e5c10c269393e2b99d6f'}, 'frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-DylYvT-1.js': {'bytes': 3147, 'sha256': 'cb33f6b5079ce07ace31e04cc53297d52919a87a269b8707d5b8eca202849727'}, 'frontend/emergency_pc/assets/js/wf-authenticated-components-DzopTDpF.js': {'bytes': 1254724, 'sha256': '0958fb92b4c570ae52a81d189b22d2da3fe2f4434866e311089675912abfc5fe'}, 'frontend/emergency_pc/assets/js/wf-browser-card-BK1bSiP2.js': {'bytes': 382, 'sha256': 'b45efb2d48536d67f29d3682204de9e17ce3a9ecc8d2e3d28e6d1a7958dbe98f'}, 'frontend/emergency_pc/assets/js/wf-browser-card.vue_vue_type_script_setup_true_lang-D6v5q8vK.js': {'bytes': 14492, 'sha256': 'd70a1f05f8e00d7093d550fae60bf89862c5b2a6d5b9a56a8095b362521c4b6a'}, 'frontend/emergency_pc/assets/js/wf-detail-5CgSAX33.js': {'bytes': 510, 'sha256': '64b9b4533058e6cf6a8507e5c01609883706b26bfe570f5fb49a6033cbfbb7c6'}, 'frontend/emergency_pc/assets/js/wf-detail-B5Ky210b.js': {'bytes': 1008, 'sha256': '95fc4ee43d9cef65342946111801c103fb1adb5c01f7dbdd24cb43e9fd3e265d'}, 'frontend/emergency_pc/assets/js/wf-detail-BGJDzEty.js': {'bytes': 443, 'sha256': 'e1aa6085038767de2bb3bb55221734ea202c6a10679e4e018d8dd11b8053b4fc'}, 'frontend/emergency_pc/assets/js/wf-detail-COX9QFkG.js': {'bytes': 543, 'sha256': '9b8e5f16978b05d6b155a1e7f1caf556b18b0129688f44dd60a351e227f82635'}, 'frontend/emergency_pc/assets/js/wf-detail-D36x9hgV.js': {'bytes': 510, 'sha256': '82d91d2ff0e07c6a876a1aaae6ef038bed26ae91d1165417a1478709e94ffff9'}, 'frontend/emergency_pc/assets/js/wf-detail-DF6qg1-z.js': {'bytes': 7627, 'sha256': '0c086c73e486f1c2035153edac1193d35812322f5536366f3ab00c8e08787b0a'}, 'frontend/emergency_pc/assets/js/wf-detail-Dso2T6TM.js': {'bytes': 1044, 'sha256': 'dc5cf764f13f00ac6e9dfa84e02dd0a2f2eae6a36911834a308070945365fb0d'}, 'frontend/emergency_pc/assets/js/wf-detail-DyAmBSAe.js': {'bytes': 1201, 'sha256': '53898f1e6e2cfc6b35a97f2270c3d0843f98b04a0719044e579163667c4e0806'}, 'frontend/emergency_pc/assets/js/wf-detail-geLJMjCw.js': {'bytes': 1961, 'sha256': 'b3ffabdeefa1bb35c1dfa844863bd6851868047ee052118e4662db17bb4819cf'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-CjVRUCvv.js': {'bytes': 1511, 'sha256': '7d0def1889b56e54c2a14f906749c8ac05b37bb3244d3162191180de38fcbfcf'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-CxNtgoet.js': {'bytes': 3010, 'sha256': '8ccbd7777855205de2cbf004da9b1ea182c75e60efd98a295d36e22645184356'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-D9-Vjw9h.js': {'bytes': 1741, 'sha256': '59263cd37bc4a8c756f19f868f22118f57a7b4f6a9d1bcc025c546033cadcfd1'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-DDzWx852.js': {'bytes': 4255, 'sha256': '4c105d6fda3c4c15cebc5ac947f10294d23cb5e0b4b1cc295e89d74bff13a85a'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-DOC3F9r7.js': {'bytes': 2651, 'sha256': 'e095f1a7edd5bbc9b00db89b97ab35c0be91e84ce2b02ec714519c86c9c710ae'}, 'frontend/emergency_pc/assets/js/wf-detail.vue_vue_type_script_setup_true_lang-v4LH8Sk9.js': {'bytes': 1497, 'sha256': 'dacdc038ad867f91a9442954503352acd0ed988e6e3e53a4e710c0384f0d43f8'}, 'frontend/emergency_pc/assets/js/wf-DisposalDialog-BmNJC4b3.js': {'bytes': 420, 'sha256': 'a15bcc3404b977e33a61d84a22a0c8123dd91a73382f6101475f87a340635412'}, 'frontend/emergency_pc/assets/js/wf-DisposalDialog.vue_vue_type_script_setup_true_lang-BGQ1X7EW.js': {'bytes': 1964, 'sha256': 'b55ddc64ad17ece0012cfe3edc4380f3a5473496fd5743b1088d35332a95746f'}, 'frontend/emergency_pc/assets/js/wf-eventList-BqHfHwz0.js': {'bytes': 2381, 'sha256': 'b3130d6573a882119ffe8bc46491b70d5505e070b43135d72d04195492b9f012'}, 'frontend/emergency_pc/assets/js/wf-EventReportDialog-BIaZIWxi.js': {'bytes': 281, 'sha256': 'fb7aedf9c78432f2743cf32559a97abefcc237c89892bc57b467da29ae3c9f8d'}, 'frontend/emergency_pc/assets/js/wf-EventReportDialog.vue_vue_type_script_setup_true_lang-B3XVC7Lo.js': {'bytes': 1077, 'sha256': '8cfab3c67689895f6690b9f31844ac917ddcc2b560e3fb5c81b198ee795b2d14'}, 'frontend/emergency_pc/assets/js/wf-exerciseDetailDialog-ZzK_6xo4.js': {'bytes': 4037, 'sha256': '80de6bf7ef076343869a4f5339b70d8f63f2bb6ccbb7adc8fc89b2cf86cdb756'}, 'frontend/emergency_pc/assets/js/wf-exerciseDialog-Bt2H5iX0.js': {'bytes': 4341, 'sha256': 'bcffc2a04cfe87d1e0fcd039eff9d14b5a53f5f26e6bfdb4c14e98f112334a71'}, 'frontend/emergency_pc/assets/js/wf-exerciseList-Cda41cst.js': {'bytes': 5228, 'sha256': '310f77a0b43eafd46c4fca1e72e541fd8880f4335c40e20413bb55387d4af5a0'}, 'frontend/emergency_pc/assets/js/wf-expertsList-C76HIZJH.js': {'bytes': 612, 'sha256': 'b9600affd6fc871b7e752b503a1c4f8d5168b0bfc5c00e1e7f4fed7068984d08'}, 'frontend/emergency_pc/assets/js/wf-expertsList.vue_vue_type_script_setup_true_lang-Cn70-Y-W.js': {'bytes': 2732, 'sha256': 'fd17907bf7e98bc2abbd8ec717cf46c36c938ff37ac111b5ca8dcdb0b5bd279a'}, 'frontend/emergency_pc/assets/js/wf-Files.vue_vue_type_script_setup_true_lang-ZVcrJoLE.js': {'bytes': 5626, 'sha256': '1072c51d2540a328d97eb6532c3edb063302cb686c44c45aa92c604b410c7ce4'}, 'frontend/emergency_pc/assets/js/wf-FormDialog-C7vuR967.js': {'bytes': 307, 'sha256': 'b0b1ef29f66f0005a6ff4400d269416345326498c546074af28293e8297283f1'}, 'frontend/emergency_pc/assets/js/wf-FormDialog.vue_vue_type_script_setup_true_lang-CMMhQniG.js': {'bytes': 1343, 'sha256': '4d0d7399bf29f7c9e11641c45c23d3d0eac0edd136388fadd1b9a40640b95e03'}, 'frontend/emergency_pc/assets/js/wf-formList-Dtrg0JjY.js': {'bytes': 3136, 'sha256': '2a55c1782bc96d939407900604b0edfce03b579c8413d5baf99aad844f65ff6f'}, 'frontend/emergency_pc/assets/js/wf-goal-card-D81d-plY.js': {'bytes': 1205, 'sha256': 'cac2526890076bdccec51b19865b79e4487ce1553340726a99053bfcac9eed81'}, 'frontend/emergency_pc/assets/js/wf-goodsList-B3oCwho_.js': {'bytes': 610, 'sha256': 'a5f11996b688d54663614e62d012633f8ee12be4774f14d0300dd0a0a453c320'}, 'frontend/emergency_pc/assets/js/wf-goodsList.vue_vue_type_script_setup_true_lang-DmXEaYGV.js': {'bytes': 2908, 'sha256': '79e56cf96e2fce90770ea0a3dd6fda9e32c66887bcc198cc5659066b4d64bf27'}, 'frontend/emergency_pc/assets/js/wf-GridItem.vue_vue_type_script_setup_true_lang-DAvkXE2m.js': {'bytes': 3256, 'sha256': 'e656362225c3ed9a7b2b18392fc2e2f06ea058c8f449a8fdeff348f53272a3a2'}, 'frontend/emergency_pc/assets/js/wf-hot-search-BEa2hT43.js': {'bytes': 413, 'sha256': 'df47f92324b8325c4a8806962ef447b273f42abe2afecc83eda483e964d662e5'}, 'frontend/emergency_pc/assets/js/wf-hot-search.vue_vue_type_script_setup_true_lang-F1JINHEi.js': {'bytes': 23898, 'sha256': 'fdc29617de8b2fa13eb4acc3e95f5ee762102af8afbf9d82ee823bee1249d5da'}, 'frontend/emergency_pc/assets/js/wf-icon-svg-BEBqrwNd.js': {'bytes': 15834, 'sha256': 'ae53836955378bb6f963aebc3cce742812aaa32a3bd939acbdc10eea4374d2d7'}, 'frontend/emergency_pc/assets/js/wf-icon-svg-C_74p_0x.js': {'bytes': 13688, 'sha256': '5a37dfd5aed2067d09226d13f0c212d191c206ada1dc0d41811f95dba4979ff5'}, 'frontend/emergency_pc/assets/js/wf-icon-svg-DsGjbCty.js': {'bytes': 12371, 'sha256': '4f1e35b5bde9938eaaedf91c0291ad990f3062a5b961460c472dfc739478818f'}, 'frontend/emergency_pc/assets/js/wf-Imgs-beWfVQvb.js': {'bytes': 64114, 'sha256': '88582997694863761a01f35fd4cb1b4bacd06140ae06cec9ad33b33d21c8c1a8'}, 'frontend/emergency_pc/assets/js/wf-index--4U-1-dv.js': {'bytes': 2898, 'sha256': '67998297b34b669f4058722a1f8f033f83a3ca0ef1f9ae273cd975c82c679325'}, 'frontend/emergency_pc/assets/js/wf-index--KEPg4XB.js': {'bytes': 527, 'sha256': 'ee79f4a9ac69b9e1539942cdd1b826b1c739a35028a429a38d718d638dff27f6'}, 'frontend/emergency_pc/assets/js/wf-index-19KcUtSI.js': {'bytes': 338, 'sha256': '4f6937b9c21376af7800b9dcf1779dc452a4ee2e8fdd757814562fa2e29d6d37'}, 'frontend/emergency_pc/assets/js/wf-index-5Yem_mOx.js': {'bytes': 480, 'sha256': '274ca25cb7928d8f5cf2410c8a82607e8e28ff5aa213b1962a47fbd6aff1b604'}, 'frontend/emergency_pc/assets/js/wf-index-6xKfiwvv.js': {'bytes': 2237, 'sha256': '3e36cf8e313422d85134e8c04bcd5340ea488428c8dca9ae4c0dce2495de3c6a'}, 'frontend/emergency_pc/assets/js/wf-index-B-cvx_WJ.js': {'bytes': 292, 'sha256': 'c48cd1261b2054fd118f91e5a084081a6de46a4fea50c48f8fff71fd3a965402'}, 'frontend/emergency_pc/assets/js/wf-index-B-FCQFXP.js': {'bytes': 449, 'sha256': '3192eb5cff0017134c3b42840ca236167ad822334e35a7b63432eb0432b87cc6'}, 'frontend/emergency_pc/assets/js/wf-index-B1GPD3uq.js': {'bytes': 415, 'sha256': '0192633c7ae6495d5491c50835fc2530f904e4987ba4a149b11400aba1169b4f'}, 'frontend/emergency_pc/assets/js/wf-index-B5MAdZaq.js': {'bytes': 877, 'sha256': '0cb6420db19b59d0a9151de2f49a148026d3813f055ce234d6c13f15cb37d67f'}, 'frontend/emergency_pc/assets/js/wf-index-BB5tOB97.js': {'bytes': 490, 'sha256': '5a0be674f7a7327b7908974c0d76ae099dbd08affb62fac120fe5f92f31f36b2'}, 'frontend/emergency_pc/assets/js/wf-index-BBGa15-U.js': {'bytes': 319, 'sha256': '2c06de423b11e964afd5ba08f256840be22d52f649dfe40a26bc919007c366b7'}, 'frontend/emergency_pc/assets/js/wf-index-Bj0CqaEF.js': {'bytes': 1326, 'sha256': '7f81f56493f5692cbf9168d15bdc55a1b53d0bfb2d05f5cea99455fa27a4db9b'}, 'frontend/emergency_pc/assets/js/wf-index-BjwC63VJ.js': {'bytes': 430, 'sha256': 'f8ed8ff51a8b4a7b29403758381f885dd9a40fc9871ae2706d140c39ab1c9a81'}, 'frontend/emergency_pc/assets/js/wf-index-Bl-Exa2w.js': {'bytes': 407, 'sha256': 'cee620be10505c016df659a8533bfc6764d83efde0f28814dc0e2578fdf15ab7'}, 'frontend/emergency_pc/assets/js/wf-index-Bs2rddSv.js': {'bytes': 410, 'sha256': 'c55633ff42123105aa2e882e5b526513088571df1d696df6d29b87178321a9be'}, 'frontend/emergency_pc/assets/js/wf-index-BX8R-aw1.js': {'bytes': 1526, 'sha256': '1cc04c6fdde73aea501fc3923a8848e59cfaaeee7c8c3594a1dc3a4dc9e11e31'}, 'frontend/emergency_pc/assets/js/wf-index-BYfeVy0U.js': {'bytes': 883, 'sha256': 'cc4a0e6bf945577d153058011350de539478211a6e5bb681a7fe367a2405914e'}, 'frontend/emergency_pc/assets/js/wf-index-BZwyxI0I.js': {'bytes': 2802, 'sha256': 'ba66c4e5b185a41cfb6683c2c8e2b1c704a1d07bf94701a69997fc6d72b209c3'}, 'frontend/emergency_pc/assets/js/wf-index-B_1mlaGE.js': {'bytes': 29376, 'sha256': 'd877b1383594f5849ffe9f8d0689d33a3f138eeed398559aa9f882fa7ba34541'}, 'frontend/emergency_pc/assets/js/wf-index-C15ot2Cq.js': {'bytes': 1384, 'sha256': '75fa27f4288e0e1bec63cc5e5e79b575cfa5c0093e33f9ea03a08a3f6ac64e76'}, 'frontend/emergency_pc/assets/js/wf-index-C9XAZYce.js': {'bytes': 120, 'sha256': '5842f11dd59a2b1eb7e1a82468347fc86ceb2692af17509566c0518c1f94ce39'}, 'frontend/emergency_pc/assets/js/wf-index-CdTFgD0u.js': {'bytes': 6154, 'sha256': '66d9e67a7c3217d47ac30923bd36c31b35ab28cf966bee5ac5ef839bcbbce0a4'}, 'frontend/emergency_pc/assets/js/wf-index-CeA4ua_p.js': {'bytes': 1620, 'sha256': '4d5ae7688eda2ec3518a63b1d8bcf4e84b850cf8b618e06281c72adc660d1e17'}, 'frontend/emergency_pc/assets/js/wf-index-CEPPMKpW.js': {'bytes': 1608, 'sha256': '16fe4edd7fee40069d53c1366da79392e4872cfc5353ea2d8d1d97ebc0503828'}, 'frontend/emergency_pc/assets/js/wf-index-CEXoh80J.js': {'bytes': 1111, 'sha256': '9a320fa65e12245eff17f638cd5ae550fdc85dbdeabdbeded97b49650981b0c1'}, 'frontend/emergency_pc/assets/js/wf-index-Ch8pwc6a.js': {'bytes': 2100, 'sha256': '4c4ffffc0630d5e88dcda651422c9273484d6357cc9cd9dddbe421075980f620'}, 'frontend/emergency_pc/assets/js/wf-index-ChT4T4x0.js': {'bytes': 374, 'sha256': '3332a2c27f0e45991ce33b18a80da4494a69e4568699e6fff7b43a8c6e5af097'}, 'frontend/emergency_pc/assets/js/wf-index-CjIx3gFB.js': {'bytes': 886, 'sha256': 'f32703121543cb52ddfc577bbb02164d9b1aba53bb58dadeb40c301bcc2409bb'}, 'frontend/emergency_pc/assets/js/wf-index-CL5zdpKn.js': {'bytes': 314, 'sha256': '02db86ba40f3640046ac3f14f44aa113b78b213acea498df05cba7a305dac617'}, 'frontend/emergency_pc/assets/js/wf-index-COO7GXeA.js': {'bytes': 1136, 'sha256': 'c1e57c29e50ad125445154d4306109afe2edd29ebb7bbd1a9b3d245eb2edebac'}, 'frontend/emergency_pc/assets/js/wf-index-CqkWxuMc.js': {'bytes': 678, 'sha256': '11a78ec91bb0a82895b169584e0396a2bab493eccba6a2934ed3d43315405808'}, 'frontend/emergency_pc/assets/js/wf-index-CR57kVZ8.js': {'bytes': 430, 'sha256': '3a125d539631942705a14d43383d07f15dd95ca2fb3007f2519edf2f5e9e0749'}, 'frontend/emergency_pc/assets/js/wf-index-CUKl4BlF.js': {'bytes': 3663, 'sha256': 'f92f3b605d69f88ffa965154408118458b72f27f968a90f509b982aeb355c6b2'}, 'frontend/emergency_pc/assets/js/wf-index-CWnXV01M.js': {'bytes': 714, 'sha256': '8245b4f29436a57e8c7dcb56010f15360e36d19c03cbb7513925304fe550b18b'}, 'frontend/emergency_pc/assets/js/wf-index-CwPMuPTR.js': {'bytes': 2264, 'sha256': 'a2fc0e64232cc4e28a6dad2e4eeca171120ec161f61a9cd828eddf2e4208714e'}, 'frontend/emergency_pc/assets/js/wf-index-C_ZP3Pto.js': {'bytes': 1320116, 'sha256': '8a7dc8a8e80dae2c8001d39676e33749c28bfa49b99f80379f2be94e9302a11f'}, 'frontend/emergency_pc/assets/js/wf-index-D5lSUZLH.js': {'bytes': 416, 'sha256': '483b5cdcad39631e05fea58018a934c6f0e11c330e7580346037dda84354e5ab'}, 'frontend/emergency_pc/assets/js/wf-index-D7S93r9C.js': {'bytes': 171, 'sha256': 'f6eae7fa4676b0a430c77c1c40788f69aaacf837091abe4b74ea50d8b97361e2'}, 'frontend/emergency_pc/assets/js/wf-index-DdWIz71s.js': {'bytes': 3276, 'sha256': '861ebef65fdab8c9bb44056aaa792c0da91f17dbd3e55215f2260433ba81313b'}, 'frontend/emergency_pc/assets/js/wf-index-De2oFNX8.js': {'bytes': 1349, 'sha256': '177d94a0b8ea7dbec1e62d85e782121bff2d136cfad32d41f13cb09338458bbf'}, 'frontend/emergency_pc/assets/js/wf-index-DghSpjgg.js': {'bytes': 1500, 'sha256': 'd5f30940c428f6c41eb25165e6feb6ca7d04380bf246b6fe75758d9c6ac46337'}, 'frontend/emergency_pc/assets/js/wf-index-Dj4iECvn.js': {'bytes': 299, 'sha256': '9e9a9879c529c78affce12b165ac2787b765809e0078932975c6a0ec8f317d77'}, 'frontend/emergency_pc/assets/js/wf-index-Dj6RXc16.js': {'bytes': 686, 'sha256': '25f77e1401bfdd237791e653b7d42dcee3c288be950e0d6e39695117bd3bd90e'}, 'frontend/emergency_pc/assets/js/wf-index-DjjDvBFz.js': {'bytes': 2549, 'sha256': '2ee34c557ea1bbb4d3c75bee2f60990f507513099938268ec86ad238852b18b6'}, 'frontend/emergency_pc/assets/js/wf-index-dKuF2e8y.js': {'bytes': 430, 'sha256': 'ae180f0835ef7e842149dbb47e445121ab99cf8cfccefef9c2fa2d8b29c0d810'}, 'frontend/emergency_pc/assets/js/wf-index-DlNWY3q_.js': {'bytes': 884, 'sha256': 'cec82636a82107d1c4e92fefcbd173bba7d839acc0d4c54e1504821dcd161170'}, 'frontend/emergency_pc/assets/js/wf-index-DN9bhOOd.js': {'bytes': 1193, 'sha256': '41bf6a0a9e4b4d498c5afb8737707e17acc927f09045e22747994ffada9427f2'}, 'frontend/emergency_pc/assets/js/wf-index-DOv73rGA.js': {'bytes': 971, 'sha256': 'b9cf7419d25b27979a4a78e31a580e8b76318b0df7af66f09f72a075bc1075de'}, 'frontend/emergency_pc/assets/js/wf-index-DTzcEtD6.js': {'bytes': 4027, 'sha256': 'f55c076a376ceff39cd5ed0ff0fe3b092d4c4c1620c7b2c8d899998fbe038ac8'}, 'frontend/emergency_pc/assets/js/wf-index-DY9NIszw.js': {'bytes': 2015, 'sha256': 'b268487cf1c7dc80064a38392d062eeb2e6eed6712296dee34793f5a35299128'}, 'frontend/emergency_pc/assets/js/wf-index-evPUjywm.js': {'bytes': 180, 'sha256': 'fd5a982862d09c3f3bc5b30619863a79bf52034c592211c645647d3c7c2f1069'}, 'frontend/emergency_pc/assets/js/wf-index-FUOdkblM.js': {'bytes': 2809, 'sha256': 'ab24269ece30090d1c9449453f7be0c43c26811c4347667b09c14e40b416cba5'}, 'frontend/emergency_pc/assets/js/wf-index-Fw2bqNQx.js': {'bytes': 392, 'sha256': 'cec92e167fbe1765dcd6f3d27d2265569f159abbe8bc232801cbe49898984f6b'}, 'frontend/emergency_pc/assets/js/wf-index-GqXYx3Ix.js': {'bytes': 271241, 'sha256': 'c7f516c668551ce2091493637e90234cad9c40e9a7c56c0f673502ea9143674f'}, 'frontend/emergency_pc/assets/js/wf-index-IHWfpqH-.js': {'bytes': 7116, 'sha256': '1ff7d033e879d536db0dcee1d8be36ec725b28822a32a92d677bacee567735da'}, 'frontend/emergency_pc/assets/js/wf-index-JNbl9Ed8.js': {'bytes': 682, 'sha256': '2b63f8898863a3c858e2d4ebfdf7972eeaefa3346292270ad7295ec5d3146a94'}, 'frontend/emergency_pc/assets/js/wf-index-JrtKei9Z.js': {'bytes': 1149, 'sha256': '1edd911e48f681abf60b22c2012aeb2a062751316e1eeac02987da690d6338d1'}, 'frontend/emergency_pc/assets/js/wf-index-ngBRgwnv.js': {'bytes': 2803, 'sha256': '471eb502d24730cad08d8cf082e8aca996d2d28a904685b807b7846cee21d39d'}, 'frontend/emergency_pc/assets/js/wf-index-Rn_O24ak.js': {'bytes': 2876, 'sha256': '7c9c03cf6660c670baebf5388f70eb9a5fc6c76adc22f953f53694f9e4cf4551'}, 'frontend/emergency_pc/assets/js/wf-index-tewM1POs.js': {'bytes': 1701, 'sha256': 'd804f01962b7e9ee16ad3afdd566280accfc5531fe8c0527af24d85bcf03da68'}, 'frontend/emergency_pc/assets/js/wf-index-VK7iRuk7.js': {'bytes': 1076, 'sha256': '54f8075bf7b6940f63cf0cab8aec62501df76048121d82c566820537c92b9dc6'}, 'frontend/emergency_pc/assets/js/wf-index-vsyy8aHR.js': {'bytes': 1144, 'sha256': 'd4366eb9fdc2dfa217fe96a8d5eb60c9983abf065912dfa16023597a1a615d10'}, 'frontend/emergency_pc/assets/js/wf-index-ySrTBVnI.js': {'bytes': 1313, 'sha256': 'faa31b48e5fdd76a2cb628057f3f268e4b80517c0637861c4417dfe60cb5ba59'}, 'frontend/emergency_pc/assets/js/wf-index-ztgfgj3B.js': {'bytes': 3043, 'sha256': '0de20223263f68848fc1a4816df0548e4c6b3942837dd3a1cee2cb78441e8c49'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_lang-Bs-L7UoX.js': {'bytes': 1402, 'sha256': '071f68f67f501a7789448ea1ee9da3af95189a4a893fcf096a6f2cbdc71246a6'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_lang-BtExM3D9.js': {'bytes': 1180, 'sha256': '24ca4378f4580fc9ffe7c882efc75b503b18a9fa404e72b9023a9ce0c033057e'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_lang-C0Z-bsUi.js': {'bytes': 1998, 'sha256': '2bf3ddc4566fb2357d273123dcdc7bec00c8af8d2f15e78c19f16fc653a9c13a'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_lang-D0WnTIyh.js': {'bytes': 5183, 'sha256': 'de8408a805e7fc640a43d99c287e375b055df7322a14f388c57c1735a3e88e36'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_lang-D4mBW8WT.js': {'bytes': 300653, 'sha256': 'c15d494006486a187f763443cd611004505fe62a29bdf28718cb4830a9670a96'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_name_ProTable_lang-BUdGHBZk.js': {'bytes': 9856, 'sha256': '5d6b9d940665168d287a15c145880d52c174e833bfb4be89f736f36b01103df1'}, 'frontend/emergency_pc/assets/js/wf-index.vue_vue_type_script_setup_true_name_SearchForm_lang-Dy0kvFwJ.js': {'bytes': 5575, 'sha256': 'cffb0a31de0d197cbf8d5dce424627bc8c73126db176e4bb61d99b170ee5b866'}, 'frontend/emergency_pc/assets/js/wf-info-BhxCSUhN.js': {'bytes': 63237, 'sha256': '4707a4908130674f2fb7fd57593361faa7a458cd0d7c6589129bdf49647a4e0d'}, 'frontend/emergency_pc/assets/js/wf-install-2U_fQz5q.js': {'bytes': 17032, 'sha256': '296625b57b3c4ff954d9cb2c2608d0fbca2005b9a1a065e5b2117fb144c7ca36'}, 'frontend/emergency_pc/assets/js/wf-install-BdLhFAQ-.js': {'bytes': 17982, 'sha256': 'e8a454c4746d2ce7fbb1d28c582d6f55a093538cfda19e0f488c0aa86af38514'}, 'frontend/emergency_pc/assets/js/wf-install-C_hCu7w8.js': {'bytes': 26748, 'sha256': '52e6ac857256eb3e8d108d79532ec8deb7e0f63bd754b87b5645934b3494e344'}, 'frontend/emergency_pc/assets/js/wf-labelGuideHelper-BYOPvJxM.js': {'bytes': 5443, 'sha256': 'b9d727c745b89bba678228686582f16748b4b10d97bb2582340d84b417f2d08b'}, 'frontend/emergency_pc/assets/js/wf-link-card-BwYBdMNW.js': {'bytes': 2451, 'sha256': '8947914e7466a3f1c1dd3d9a17d32d3a02abce759e1190facd1f9bf858559069'}, 'frontend/emergency_pc/assets/js/wf-list-BYvBLE73.js': {'bytes': 1843, 'sha256': 'ec9d03c54ccb66d27c98e40889ea77444a4ba74281d206c3d9306a6bebecb56f'}, 'frontend/emergency_pc/assets/js/wf-list-CNXuxZOY.js': {'bytes': 1777, 'sha256': '18246d2e27a46a45114ea70f2976c712a8a78cb7d496c826c0a88cc18301386c'}, 'frontend/emergency_pc/assets/js/wf-localData-COWRKD3f.js': {'bytes': 17927, 'sha256': '4d152169c1ff068f10a3c5820bf8ca36ac90a0b56ac268a3906aaf86a26fde5f'}, 'frontend/emergency_pc/assets/js/wf-map-card-LynnZMH8.js': {'bytes': 86352, 'sha256': 'e2e134220afe5409b2ca2d827aafbcdb64c728006f67e335b55242b049ed00d4'}, 'frontend/emergency_pc/assets/js/wf-message-letter-CGsRwtYB.js': {'bytes': 283, 'sha256': '6913ef4fb29ffeb3488c5a428a65fea3904d27820b8e9e3291ea578f078cc517'}, 'frontend/emergency_pc/assets/js/wf-message-letter.vue_vue_type_script_setup_true_lang-DKGz-Xx3.js': {'bytes': 2293, 'sha256': '831c3730ca8c8260f8ea8ebb84b434488ca40e516c8303d5f4c271188ece2405'}, 'frontend/emergency_pc/assets/js/wf-message-notice-w_aVJxa2.js': {'bytes': 283, 'sha256': 'c9e2e0164bcce208574f83f557963862ad3e9fa704ced2592457b685f82a2d7e'}, 'frontend/emergency_pc/assets/js/wf-message-notice.vue_vue_type_script_setup_true_lang-CC88dXCS.js': {'bytes': 2269, 'sha256': 'e93ad4904a631959416c94ab310af4fb1491b06dfab2f93c4b723b6bed009bbb'}, 'frontend/emergency_pc/assets/js/wf-message-todo-BNBXr5KC.js': {'bytes': 281, 'sha256': 'dfeceb9b0fad52ae58b701ba7a0fcb7f9829ef7dc88ae4eefaf8b7297c700b4c'}, 'frontend/emergency_pc/assets/js/wf-message-todo.vue_vue_type_script_setup_true_lang-DJth5Klp.js': {'bytes': 2267, 'sha256': 'e8c98a7c5f107a8db342696c5c19014dab334b9cb9102d617fd96dfe4acfc73f'}, 'frontend/emergency_pc/assets/js/wf-more-icon-Ldt4cz1L.js': {'bytes': 136, 'sha256': '73cc611d74b28f2f77cacf02daf1a3b5957161239c0b22cdd63baeda10fe8e31'}, 'frontend/emergency_pc/assets/js/wf-more-icon.vue_vue_type_script_setup_true_lang-B-2ohsuz.js': {'bytes': 679, 'sha256': 'a46411b7e9d15d898cf8a6c3a5e221b89904145f3b886c576e38f8fab68929fa'}, 'frontend/emergency_pc/assets/js/wf-notData-CvMaLoqa.js': {'bytes': 1609, 'sha256': '4d8956ab679a15d7fbbf07634a7d804ec183dc4520f866cecd0c054841fe2719'}, 'frontend/emergency_pc/assets/js/wf-online-num-BdlqBxF_.js': {'bytes': 280, 'sha256': '08d55ac8496bd8a9a0acee1d4c7caa728449473ea47f17e0f8a7bf1af6ab47e6'}, 'frontend/emergency_pc/assets/js/wf-online-num.vue_vue_type_script_setup_true_lang-B9OAKk4_.js': {'bytes': 1117, 'sha256': '1dc2ca26079331ec374dbafbfbeda83b94ef679dc2c2f222bc45851aafef837f'}, 'frontend/emergency_pc/assets/js/wf-OriginalEmergencyReadonlyDetail-rsQCUDem.js': {'bytes': 3488, 'sha256': '7b4d70525189345816096238361527e60806625feab2a4c0dfc61e6c09a643b9'}, 'frontend/emergency_pc/assets/js/wf-PersonDialog-D0sL4Hnc.js': {'bytes': 5342, 'sha256': '9925b0c47bcca62df65fad7f73a91b76486f85dc63fc31c8848a78591af8b2da'}, 'frontend/emergency_pc/assets/js/wf-personList-jjPNHOaz.js': {'bytes': 1861, 'sha256': 'ecf6139ffcf73b5b5f7e20d35f968c09df4a75f5be7a0f675b16faf67a8aa156'}, 'frontend/emergency_pc/assets/js/wf-profile-card-IizOloUT.js': {'bytes': 2214, 'sha256': '11faef9a4d1691ddab65e9189aebf8532f4b6dbd04dfd2844ede8a18102cd68f'}, 'frontend/emergency_pc/assets/js/wf-project-card-D5Mcy2SH.js': {'bytes': 2696, 'sha256': '24d04e6323eb653e5fdb4c4e80b5272a4c68fd3551163ba97fd0d8654b56511a'}, 'frontend/emergency_pc/assets/js/wf-sale-card-De6QLJT8.js': {'bytes': 4801, 'sha256': 'e01e6e2e4b9052f1d24e764f6973a78a0ea7247b85953f0b58dfcf9187ad265d'}, 'frontend/emergency_pc/assets/js/wf-sectorHelper--XXn88f7.js': {'bytes': 272, 'sha256': '6135a55c629f3609acf7978fc816b6fecd7148e6d48abf0b164ef3ecdfac82f4'}, 'frontend/emergency_pc/assets/js/wf-statistics-card-C6hPoiAS.js': {'bytes': 5137, 'sha256': '565e305464aa62c733adfacc14d27347856b37982ca37e17e72d919aacfef8ee'}, 'frontend/emergency_pc/assets/js/wf-statistics-card-DMFYDn6y.js': {'bytes': 3685, 'sha256': '33a9efae30baf5a678c7a82a52393d3bd578fe6afcfe2e5abcda70e2db719449'}, 'frontend/emergency_pc/assets/js/wf-task-card-XH3Pu-I6.js': {'bytes': 3100, 'sha256': '81d4d15f0d1e0594f3b29af1eede50948e5d2898a9e918d3420159abaa84ef96'}, 'frontend/emergency_pc/assets/js/wf-teamsList-CY--leKF.js': {'bytes': 577, 'sha256': 'e94407886e1475755bf6d3d1621f7ff474cd2a73f5f944d18caff20c2f8880c6'}, 'frontend/emergency_pc/assets/js/wf-teamsList.vue_vue_type_script_setup_true_lang-7myIb43Y.js': {'bytes': 2611, 'sha256': '9d15259a67fdf3adcc53dccfe8eab1d35ea7e8f6b4fa9cae63020dd08e972d98'}, 'frontend/emergency_pc/assets/js/wf-TreeFilter-CPKWKiFX.js': {'bytes': 1373, 'sha256': '5e71e327dd924c1c4e3267ab32a4c3ebdf3e863f1e65cca29dc2bb71e397e355'}, 'frontend/emergency_pc/assets/js/wf-use-echarts-D0P016X3.js': {'bytes': 437901, 'sha256': '993413722fac5b245b8d0ebe7a1a31b919fed9212ce18fb6d7b78e8c0c79efb1'}, 'frontend/emergency_pc/assets/js/wf-useDict-BhNbDTYC.js': {'bytes': 343, 'sha256': 'aef11855330a2244e5a5eaa36a9ef1040470748e63cff9bc2f487c5131af8fea'}, 'frontend/emergency_pc/assets/js/wf-useDownload-D_jY12Vz.js': {'bytes': 600, 'sha256': '0fe8b6ddf686e627cf39b620c3f36ffc52f425325c0690b2cf3f2e541eb1ac9a'}, 'frontend/emergency_pc/assets/js/wf-useHandleData-D8NRw-6V.js': {'bytes': 500, 'sha256': '85d2179e4f0a6803535cfe163bd994f37bf47f77595ac6f33121776e0fcec3ee'}, 'frontend/emergency_pc/assets/js/wf-useOrgTree-DidwNtgy.js': {'bytes': 392, 'sha256': '64527a4541f6ad3344ecba948025443e2c61509d02f74149a39442a51a445fe9'}, 'frontend/emergency_pc/assets/js/wf-user-account-PCt_UP_t.js': {'bytes': 2924, 'sha256': 'a90e1c26214c48a3c9442783f4f9c85dc1acef0fcf77716e5a6726b7999df07c'}, 'frontend/emergency_pc/assets/js/wf-user-card-to1ZivmB.js': {'bytes': 2935, 'sha256': '17d3eb65fc17e83042db85801765b84ed9baf5cafafb58bb0e007f115e69f985'}, 'frontend/emergency_pc/assets/js/wf-user-form-CpuqLRXQ.js': {'bytes': 3342, 'sha256': 'ecdeff5d185b8411a6883cb374a21597eb8c6d3234ffd41333b4f0458eca6621'}, 'frontend/emergency_pc/assets/js/wf-user-list-DkLoDoKs.js': {'bytes': 2193, 'sha256': '11a7e866a1aa79e8672d356490917c453295cade94bd8cdfc31ab0f0f4f852ef'}, 'frontend/emergency_pc/assets/js/wf-user-liveness-DpaWZCi4.js': {'bytes': 1161, 'sha256': '65717d75e727c3db451eda82c7b8e4e1f5b2b0c87142d2b4b52cabe909e00034'}, 'frontend/emergency_pc/assets/js/wf-user-rate-C-RorOR0.js': {'bytes': 2346, 'sha256': 'ada27aa75c0f9157d4895081b946837ba6b9d7c57ab74295658c42daa9bf9a58'}, 'frontend/emergency_pc/assets/js/wf-user-satisfaction-49In092t.js': {'bytes': 1252, 'sha256': 'd4cf5ef2993e4aa9a313372d06dd2ac868c90be54afe0ec3185d7f4320b9bafa'}, 'frontend/emergency_pc/assets/js/wf-visit-hour-Bco1XuGL.js': {'bytes': 333, 'sha256': '0ddcf8e35fd09a4f3a8467d7e2e86d39358d67185ad001150b0d85ed40938f4f'}, 'frontend/emergency_pc/assets/js/wf-visit-hour.vue_vue_type_script_setup_true_lang-DRlRCl-W.js': {'bytes': 1188, 'sha256': 'd71058fb3e17c09f24cadf2a8592d818a49b4ba94a828dc34fe5ad1b4b90ae1c'}, 'frontend/emergency_pc/assets/png/header-DioI81U5.png': {'bytes': 32447, 'sha256': '5ab97af1941ce93d3b50a9b1c7c5b59f1a4384da989b91fa77121599412365ea'}, 'frontend/emergency_pc/assets/png/login-bg-BkIjQ0FB.png': {'bytes': 59273, 'sha256': '2f630ceaaf60f080ceb4c6815dee3ed81bb96dd631f0bca87d2b5034b0fa3ab5'}, 'frontend/emergency_pc/assets/png/login-img-BQ7KMz7P.png': {'bytes': 122781, 'sha256': 'f0a89e6b7c3c579f4ba67e41583be89b99d532ee113ee51fa29134c283f682f3'}, 'frontend/emergency_pc/assets/png/welcome-VFYC1WKN.png': {'bytes': 75638, 'sha256': '65a50eaa2e71bfda14ce9b01147bdad8a852a91c9436ce90b2d51635d4c1518f'}, 'frontend/emergency_pc/assets/ttf/iconfont-DlTwZ9ZE.ttf': {'bytes': 311288, 'sha256': '17414732aa673a21d0273c977199d55392a68a35edc90db0d81f26b9fd2d03d2'}, 'frontend/emergency_pc/assets/ttf/iconfont-Doejzznz.ttf': {'bytes': 137200, 'sha256': 'b0e92bc39639552567bc6009e61542fbbad57f2ef7dad061490c630d8e0ca648'}, 'frontend/emergency_pc/assets/woff/iconfont-DlmQJsnZ.woff': {'bytes': 157768, 'sha256': 'd4aaab54abb4bcf9b79c369b7b71beea9645c0e4b0b3df6c778d3ea074174962'}, 'frontend/emergency_pc/assets/woff/iconfont-DXpWSwP3.woff': {'bytes': 83492, 'sha256': '9d6f1f613ca66b423355d7f37d8143aab87c92e6b1273304322f62fd8e2a903a'}, 'frontend/emergency_pc/assets/woff2/iconfont-BVocOvQs.woff2': {'bytes': 121936, 'sha256': 'a1e99fee3a02b7eb52916b0414e996fd1c9bb6ff0236b343d619ed78e1422fbf'}, 'frontend/emergency_pc/assets/woff2/iconfont-C3Y3s009.woff2': {'bytes': 68460, 'sha256': '6c3f5ed1cb99f4cc64f5bdaafd6181c8e310b2ff6761dd88309e00410cd6a916'}, 'frontend/emergency_pc/ele-file-list/ic_file_android.png': {'bytes': 503, 'sha256': 'fc005bf0faaf9b1c4870366b10141d12e09ef8fb7eef18ac4e8a219b7d0dde43'}, 'frontend/emergency_pc/ele-file-list/ic_file_android_sm.png': {'bytes': 345, 'sha256': '04bc8272dfb6fdd30b278b4a375296c523cde07d4f88e3cf66f8374975c82da5'}, 'frontend/emergency_pc/ele-file-list/ic_file_bt.png': {'bytes': 477, 'sha256': '7c0e79be7be4f9188480a08f8e56c9870e3bf286f1112ef8b731b47dfab8cb04'}, 'frontend/emergency_pc/ele-file-list/ic_file_bt_sm.png': {'bytes': 294, 'sha256': 'bcf6a4426dd9ff06576208d6027555209524fd78ccbd492cb80e7bd583da7395'}, 'frontend/emergency_pc/ele-file-list/ic_file_cad.png': {'bytes': 797, 'sha256': 'df047c9e6a4a1541c60b9f45701af176489c84a5d4c31012074cc4d47741904d'}, 'frontend/emergency_pc/ele-file-list/ic_file_cad_sm.png': {'bytes': 516, 'sha256': 'ceddd8879641d795fa1d89d421c2e894d94c9db35fbb3fa5236caf6a3b8a2053'}, 'frontend/emergency_pc/ele-file-list/ic_file_code.png': {'bytes': 550, 'sha256': '35721c5171ed7809b907b7719c78fafe84a7f00dc8edd5c6a2ab2ed6c7f39df7'}, 'frontend/emergency_pc/ele-file-list/ic_file_code_sm.png': {'bytes': 252, 'sha256': '1efa31df5c18579b735954570189ab070bb6805406c1728a4259dcf6e6a46544'}, 'frontend/emergency_pc/ele-file-list/ic_file_excel.png': {'bytes': 555, 'sha256': 'd786ce56a51b9b17463744f4e9f3110cedce3cd0690e5a95333edb605aac5154'}, 'frontend/emergency_pc/ele-file-list/ic_file_excel_sm.png': {'bytes': 314, 'sha256': '4a18f7d0a8abe4869707880dcc332ba51ddead5321aec99333057165d3fadc60'}, 'frontend/emergency_pc/ele-file-list/ic_file_exe.png': {'bytes': 423, 'sha256': 'a2d8b4ad8b6f423134ff1ac1a89ea1edaf2253b66fc4f94ffd2c28f2a8e00d1c'}, 'frontend/emergency_pc/ele-file-list/ic_file_exe_sm.png': {'bytes': 269, 'sha256': 'ee4b83e34eb339e25e458199ae060cdf08a7bd1e4e738eff8044abea933f7324'}, 'frontend/emergency_pc/ele-file-list/ic_file_flash.png': {'bytes': 434, 'sha256': 'b999c6b54c98608d1742774df3ea27cdf4cb0d466a734ea7ea37abffe248a9f4'}, 'frontend/emergency_pc/ele-file-list/ic_file_flash_sm.png': {'bytes': 297, 'sha256': 'a530858cbb633655e224b7fb9bf1b6efb5dd4d5a8e567e1d8af5152e430de74e'}, 'frontend/emergency_pc/ele-file-list/ic_file_folder.png': {'bytes': 265, 'sha256': 'e84ef319d4d0d42f8a1f912710b129a36181aaf2000ff3e52d2ca7c543bab46e'}, 'frontend/emergency_pc/ele-file-list/ic_file_folder_sm.png': {'bytes': 168, 'sha256': '54d1d885a283b4226915a58c6c67031f0dea15ef956b3e7d5ea44307fb4fbb56'}, 'frontend/emergency_pc/ele-file-list/ic_file_fonts.png': {'bytes': 533, 'sha256': 'de5449265e387d6491d01582d01ef0b782a11cecc216b745b2be94ede8cdf503'}, 'frontend/emergency_pc/ele-file-list/ic_file_fonts_sm.png': {'bytes': 360, 'sha256': '1f62992bd22a7602d9371ca62f6cfabaa5b5156277ce5595c3adfd5da0ed2f21'}, 'frontend/emergency_pc/ele-file-list/ic_file_htm.png': {'bytes': 524, 'sha256': 'ffb69ee5c49093a9c190c07cb0d02efb9b8c78ba3581f7c4fd6aca33ea9e4c1e'}, 'frontend/emergency_pc/ele-file-list/ic_file_htm_sm.png': {'bytes': 486, 'sha256': 'b39f2ae50c75bbc8f45725882c2b332954205ca675d8a6ed8c24c8e8fca0c36c'}, 'frontend/emergency_pc/ele-file-list/ic_file_ipa.png': {'bytes': 709, 'sha256': '4e267a16c6593ae6b372bf5100856466d9964d82de5925d7701c0f7afa3cf053'}, 'frontend/emergency_pc/ele-file-list/ic_file_ipa_sm.png': {'bytes': 414, 'sha256': '7cdfd66af6d75483a0a7920dedf7fc63dc01376e659ae5188b508267b9d018ca'}, 'frontend/emergency_pc/ele-file-list/ic_file_misc.png': {'bytes': 407, 'sha256': 'ad56813e1662ec3b8bb6465e58a3f3bedde608e1253514e6db67f53d10a540bb'}, 'frontend/emergency_pc/ele-file-list/ic_file_misc_sm.png': {'bytes': 234, 'sha256': 'c8261b266400e3c6d3f3ba2324e4ee7938c443ca5a13a3f4dd13a062bcb2f92f'}, 'frontend/emergency_pc/ele-file-list/ic_file_music.png': {'bytes': 390, 'sha256': '5a79d05b8122f2e8c68f2d973443751e9503d8150bc58bcfe606a718227eb65a'}, 'frontend/emergency_pc/ele-file-list/ic_file_music_sm.png': {'bytes': 240, 'sha256': '9452cca41ba357e2ec9694917b416af7005b59d89cca8bdd2b5687a5dbd872fc'}, 'frontend/emergency_pc/ele-file-list/ic_file_pdf.png': {'bytes': 701, 'sha256': 'dbaf29ac97089a7d3a58a0c0bd95477c5eec7f819972bde363cbe6bdb0580c69'}, 'frontend/emergency_pc/ele-file-list/ic_file_pdf_sm.png': {'bytes': 306, 'sha256': 'a733e587d550be9f96db3421405721e1c0f4b9ab83fe3e2970180f4848976e6b'}, 'frontend/emergency_pc/ele-file-list/ic_file_picture.png': {'bytes': 727, 'sha256': '749b3750e6abaa35c968a22346ee0f5a726129779da21d2ecf7d6100969d73c8'}, 'frontend/emergency_pc/ele-file-list/ic_file_picture_sm.png': {'bytes': 283, 'sha256': '6b12968d9589942b3697e7f9aafb26e1041b99bcd6b44ba57784358b5e8ea04d'}, 'frontend/emergency_pc/ele-file-list/ic_file_ppt.png': {'bytes': 406, 'sha256': '8be521c92fc9735879844fa3d0d0447b1c9bb2b6182dd7acb13b6d100d63d5ff'}, 'frontend/emergency_pc/ele-file-list/ic_file_ppt_sm.png': {'bytes': 263, 'sha256': 'ef23e51ee84afaa0f96bf01c8c41611866f18ca495b95faf9406eaea05f53751'}, 'frontend/emergency_pc/ele-file-list/ic_file_ps.png': {'bytes': 546, 'sha256': 'd48a768d165d3ffda207b53234625c6b3190d709f143a76415e876f7896f5494'}, 'frontend/emergency_pc/ele-file-list/ic_file_ps_sm.png': {'bytes': 360, 'sha256': 'e2e7a15387c94f02843274981d4154dafe676f1af680e1fa2be479ca962b51d2'}, 'frontend/emergency_pc/ele-file-list/ic_file_text.png': {'bytes': 281, 'sha256': '02a4dbe135c87f004015e85210c8f6782ffcd5f716cec3c8b3038ec1711f379d'}, 'frontend/emergency_pc/ele-file-list/ic_file_text_sm.png': {'bytes': 191, 'sha256': '7eb933b7e8b1c32daf6715b4dacecd0a5cc1fbdf1d1bccea181ede34fb186586'}, 'frontend/emergency_pc/ele-file-list/ic_file_video.png': {'bytes': 361, 'sha256': '3a1f58f0a41f1e304d7a07b241146f4e423ee12e362b020c1f35434a6dcc7290'}, 'frontend/emergency_pc/ele-file-list/ic_file_video_sm.png': {'bytes': 246, 'sha256': 'f619e4908f0fbe09c56fe9b3320856ec53fa1d80125c7dc69df3ea9d151edf2c'}, 'frontend/emergency_pc/ele-file-list/ic_file_visio.png': {'bytes': 495, 'sha256': '3d03fc33eafa4840ccc39aef910cb582238ee560493c9bfdb2bfa8485b868bd3'}, 'frontend/emergency_pc/ele-file-list/ic_file_visio_sm.png': {'bytes': 267, 'sha256': 'fc8de39ab948b5a3419ac6a9bb5aaf13492181508c7b967cf205a9fb86ee6946'}, 'frontend/emergency_pc/ele-file-list/ic_file_word.png': {'bytes': 588, 'sha256': '5c8073a05b54ee193571f3660e5381b2fbe9aac2f4c5bed454bc2627a18ebe0b'}, 'frontend/emergency_pc/ele-file-list/ic_file_word_sm.png': {'bytes': 326, 'sha256': '035433f2ed2fba2d14ac8ab2ac3f7f87c6140c4f9491153295ec899cf7b6e771'}, 'frontend/emergency_pc/ele-file-list/ic_file_zip.png': {'bytes': 334, 'sha256': 'e19ca058d18c64ffb13c88004e6ef3642fd8636d533f891395838154426d0a30'}, 'frontend/emergency_pc/ele-file-list/ic_file_zip_sm.png': {'bytes': 217, 'sha256': '7834d134cf86d7b67e4f0dd5e4619f1c7adee0bbdd64171b5dce72a8a2f115e1'}, 'frontend/emergency_pc/json/china-provinces.geo.json': {'bytes': 54239, 'sha256': 'f813274d1052ef6907b5a1f87add1c7d0d359ae01b9f044cd733edc79ff0492c'}, 'frontend/emergency_pc/json/regions-data.json': {'bytes': 140327, 'sha256': 'b168550280367c53cb1dcf159ce7ecd07469489efc1c83124278be0c60690afc'}, 'frontend/emergency_pc/tinymce/langs/zh_CN.js': {'bytes': 21254, 'sha256': 'bbf4bc7f799bd37f6a52eb032b1708583ca401e778a85c0e58cbeed4c71ef3c7'}, 'frontend/emergency_pc/tinymce/langs/zh_TW.js': {'bytes': 18814, 'sha256': '7868b9dbbae773b768f477746f7d72383603963069426a6281c4d24298160ef1'}, 'frontend/emergency_pc/tinymce/skins/content/dark/content.css': {'bytes': 2023, 'sha256': '9ee5239b3047d7886e77260cc103b5cd9fc833cdea24f7e5a10b4090be2f02fb'}, 'frontend/emergency_pc/tinymce/skins/content/dark/content.min.css': {'bytes': 1469, 'sha256': '6ae1ee9da9833e71b64005885f99373358d323bcb96207a4bae1a7ebc79a8226'}, 'frontend/emergency_pc/tinymce/skins/content/default/content.css': {'bytes': 1937, 'sha256': 'b63a09cc91f0bc25847015771d9ff5630bdcdd05d1eeae025dc34bb0fe0a0884'}, 'frontend/emergency_pc/tinymce/skins/content/default/content.min.css': {'bytes': 1399, 'sha256': '745fce7256a5c32c08164e452d9b5565dd4f732a789060cd29aeae2a0bb38997'}, 'frontend/emergency_pc/tinymce/skins/content/document/content.css': {'bytes': 2074, 'sha256': '92734fd0d145a6a356c935b86a53640718d3771a6060a2c6033667037528ef05'}, 'frontend/emergency_pc/tinymce/skins/content/document/content.min.css': {'bytes': 1498, 'sha256': '8341b9bbbe3b03ba4e46956729333f00b394b7dd400f47dea885a72819f99922'}, 'frontend/emergency_pc/tinymce/skins/content/writer/content.css': {'bytes': 1962, 'sha256': '89507bbe5886dea7490ca31565855a36dc9c7452177823546f6766b09da5809d'}, 'frontend/emergency_pc/tinymce/skins/content/writer/content.min.css': {'bytes': 1420, 'sha256': 'be20787478fa4ea2aabf7349341e51be90a5c050cf095377630cdded59a58c98'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.css': {'bytes': 24162, 'sha256': '8892d68c2d9ac91943b7ea5af17d35e1afea439dbddd988de7829fda81f0d715'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.inline.css': {'bytes': 24087, 'sha256': '50eb076eba4dcc50a9a13aeaa61cfa7520311b30155723b5d7e9ebb8b18fa061'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.inline.min.css': {'bytes': 21775, 'sha256': 'babcef077246d9dc5d6f7d5756c980dbac32aafd3992be021e11285ec0b76e16'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.min.css': {'bytes': 21834, 'sha256': '9298b5289424630e18080bcd98a8306a8d061a91cde503fb6ae091fb2c1beb51'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.mobile.css': {'bytes': 727, 'sha256': '2a89a7ddfe3a611cbffb65e8f2769220b03943468804c57d95bb938240b8177f'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/content.mobile.min.css': {'bytes': 544, 'sha256': '54cbb00de32f005fb21faf16ca7a973ee671b6e0a91e223bbafde43cb82591b4'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.css': {'bytes': 73017, 'sha256': 'd0b796cd5c9922a9af5e385df6792f3016a037b4d91daad876c7b73b1a364634'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.min.css': {'bytes': 61537, 'sha256': '005437a822f999bed1ac377a6148a80f352089f142fe944436282c36fe9ccda9'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.mobile.css': {'bytes': 24619, 'sha256': '43e0f869dbd11f0b80ab2c11d5fdf24f03e68f84625012ce262144473ceba974'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.mobile.min.css': {'bytes': 21004, 'sha256': 'f84b3a578836a33f81dbdf716a89e3329cd1d510a4432dce7592152356866690'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.shadowdom.css': {'bytes': 882, 'sha256': '758ac006278f144c2175b40f9664afb5d611d366c4a32d81e25de459e40aaa40'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/skin.shadowdom.min.css': {'bytes': 783, 'sha256': '2dc7245a107c73fdc7011abc3c3b923dd59c43c760ed73494f7ddf15b340d833'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide/fonts/tinymce-mobile.woff': {'bytes': 4624, 'sha256': 'e64bf156a432d63f5b34b4567b513dc0d351b49161c7f608fb82574bfdd9d213'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.css': {'bytes': 23728, 'sha256': '5ac385512c983e3a416d7e500d8813d926f3b6943712d046703013d9292edc18'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.inline.css': {'bytes': 24087, 'sha256': '50eb076eba4dcc50a9a13aeaa61cfa7520311b30155723b5d7e9ebb8b18fa061'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.inline.min.css': {'bytes': 21775, 'sha256': 'babcef077246d9dc5d6f7d5756c980dbac32aafd3992be021e11285ec0b76e16'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.min.css': {'bytes': 21451, 'sha256': 'a3be00e717763b9f43b8a9a2a9bb29cd7b89485d1cf4f89e55535906e3b45739'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.mobile.css': {'bytes': 727, 'sha256': '2a89a7ddfe3a611cbffb65e8f2769220b03943468804c57d95bb938240b8177f'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/content.mobile.min.css': {'bytes': 544, 'sha256': '54cbb00de32f005fb21faf16ca7a973ee671b6e0a91e223bbafde43cb82591b4'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.css': {'bytes': 72873, 'sha256': '884475e50c88bcc6fd5b7c49761622ab5209182a73a8edfc60f64582754c64d9'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.min.css': {'bytes': 61424, 'sha256': '7b0985dfe42e04babb7f9b4212412b9b3f1d9cd494678b0df555e1c5c2104954'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.mobile.css': {'bytes': 24619, 'sha256': '43e0f869dbd11f0b80ab2c11d5fdf24f03e68f84625012ce262144473ceba974'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.mobile.min.css': {'bytes': 21004, 'sha256': 'f84b3a578836a33f81dbdf716a89e3329cd1d510a4432dce7592152356866690'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.shadowdom.css': {'bytes': 882, 'sha256': '758ac006278f144c2175b40f9664afb5d611d366c4a32d81e25de459e40aaa40'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/skin.shadowdom.min.css': {'bytes': 783, 'sha256': '2dc7245a107c73fdc7011abc3c3b923dd59c43c760ed73494f7ddf15b340d833'}, 'frontend/emergency_pc/tinymce/skins/ui/oxide-dark/fonts/tinymce-mobile.woff': {'bytes': 4624, 'sha256': 'e64bf156a432d63f5b34b4567b513dc0d351b49161c7f608fb82574bfdd9d213'}}
R38_REVISION = '20261104-R45-original-online-forms-and-authenticated-bootstrap'


R39_R37_BASE_METADATA={'schema': 'zhumadian.original.server.release.v1', 'releaseId': 'e5385db1-3ca6-4399-9ae5-64dc3e442b27', 'controllerFiles': {'tools/serve_original_server_release.py': '0cefbf4ae43beb8cc22e61354ec824cfdd9d0de08c74c614faa1746c3d0341ab', 'tools/original_server_windows_job.py': 'e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22', 'tools/original_server_release_parameters.py': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106', 'tools/original_object_store_runtime.py': '7dedb5e278ada96ea1c64afa2e35bf4af03a9c645e1d27ab9570dc4a2ead77e1', 'tools/original_platform_files.py': '4c76b6349ace646857834f38861db0f796d57661fd2ec60cf0185289ee511d36', 'tools/portable_original_admin_frontend.py': '68f55f7a2e4ef7bebcec408dc2d7eb10f00ea7a4046e809d2139a07c7695b1c9', 'tools/readonly_original_static_archive.py': '5f89ccb0d17004f8d82b23ba3340902ffd6e830fe6e0278ba0618869ada3e6bc', 'tools/prepare_original_frontend_gateway.py': '006b17531f83d548d161b332531ff4c75e395816780744e033a52d56b5541cc8', 'tools/original_project_branding.py': 'a8ba77817ab0fd3f1e45d06605204c27f2840f27aedb392f6590a91a9c3def4c', 'tools/reference_flat_runtime.py': '0b87b610cda9363db23ad8ab756aa1e44aa6b5be197ae6d74f96245b2e6d8ec6', 'deploy/iis_original/App_Code/XnbyReferenceProxy.cs': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53', 'deploy/iis_original/web.config.template': 'f6d4d4df1a859c203ac4a38973eb6d20b7b45b70b5cacfdf23e9c6d01996bc13', 'tools/original_callback_overlay.py': '85a1bd5238cc2b9423522683b00a3fb711aaa2982b5522f2d920a53c3f1bf151', 'tools/original_header_branding.py': '0e68e1ce9bfb20b2ef77cb3c6fcc4035593438fdbea027166748755ac066c2f2', 'tools/original_public_test_update.py': '52daac9f348be6622592920240794a1ba701d46683fa6b7c3e0cb34da47fcf62', 'tools/install_original_server_ingress.py': '6561368b6e88f7f08a377fd4399570cafc07d9bd1005b7d30ba8a8fd5a87768f', 'tools/original_iis_cutover.py': 'c6f55a4ab5a0d6445da87bf9722e29575e7a6430502992333680cea19e03bb4d', 'web.config': 'd3e3e7f58a5ba571d377c59a8f73a365730d8747b7e722226e540ff40ef0fed8', 'iis/Global.asax': '694ef766a4c998e750142d8687f36473fcb45557529d5865102de3d1dcac041b', 'tools/original_platform_async_release_support.py': '541699cbbb7792f6f1b71813eed32f7441c6bf696539aed6deaa20d963eeb078', 'tools/original_native_history_release_support.py': '5af0e91e9ec9da66e47978dbe279d4e8f03c8becd0b8130d1f65d1b1f17456ab', 'iis/App_Code/XnbyReferenceProxy.cs': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53'}, 'testRelease': True, 'originalBackendQAComplete': False, 'iisRuntimeVerified': False, 'publicAccepted': False, 'controllerRevision': '20261026-callback-r2', 'callbackProjectionExperimental': True, 'frontendRevision': 'original-event-operation-result-j58-20261029', 'workflowUserRequestCompatibilityExperimental': True, 'workflowRequestCompatibilityExperimental': True, 'requestErrorCompatibilityExperimental': True, 'approvalRetryCompatibilityExperimental': True, 'mobileApprovalCompatibilityExperimental': True, 'mobileRejectContractCompatibilityExperimental': True, 'mobilePaginationCompatibilityExperimental': True, 'businessResultCompatibilityExperimental': True, 'transactionObservationExperimental': True, 'transactionObservationRevision': 'existing-inventory-singleton-v2', 'passwordIdentityAliasExperimental': True, 'passwordIdentityAliasRevision': '20261026-user_id-to-userId', 'staticHeaderBrandingExperimental': True, 'staticHeaderBrandingRevision': '20261026-static-header-logo', 'missingAuthGuardExperimental': True, 'missingAuthGuardRevision': '20261026-web-context-and-preserved-lifecycle', 'missingAuthOverlayManifestSHA256': '91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb', 'excelJdkDesktopExperimental': True, 'excelJdkDesktopRevision': '20261026-fixed-font-boundary', 'inspectionPointEditCandidate': 'stable-child-ids-atomic-v1', 'inspectionPointNameCompatibilityExperimental': True, 'inspectionCombinedLocalRevision': '20261027-composed-tested-candidates', 'reservationEndTimeCandidate': 'original-end-time-atomic-v2', 'thirdPartyCredentialsCandidate': 'original-credentials-atomic-v2', 'workTransactionObservationCandidate': 'work-services-existing-singletons-v1', 'publicTestRevision': '20261103-R37-static-initial-load-performance', 'findingFailureObservationExperimental': True, 'findingFailureObservationRevision': '20261027-fixed-marker-metadata', 'trainingEmployeeEditCandidate': 'parent-first-atomic-v1', 'trainingTransactionObservationCandidate': 'parent-first-atomic-v1', 'workSafetyBatchEditCandidate': 'work-safety-batch-atomic-v1', 'workSafetyBatchObservationCandidate': 'work-safety-batch-atomic-v1', 'emergencyTeamAtomicCandidate': 'parent-first-save-edit-atomic-v1', 'emergencyTeamObservationCandidate': 'existing-singletons-manager-v1', 'eventDisposalAtomicCandidate': 'event-parent-record-atomic-v1', 'eventDisposalObservationCandidate': 'existing-singletons-manager-v1', 'emergencyExerciseAtomicCandidate': 'exercise-parent-files-atomic-v2', 'emergencyExerciseObservationCandidate': 'existing-singletons-manager-v1', 'applicationLayoutRevision': 'wwwroot-preserved-Application-v1', 'canonicalApplicationRoot': 'C:/inetpub/wwwroot/Zhumadian/Application', 'canonicalIISRoot': 'C:/inetpub/wwwroot/Zhumadian/Application/iis', 'platformTemporaryPathRevision': 'owned-platform-data-t-run-v1', 'objectStoreReadinessRevision': 'live-ready-verified-buckets-bounded-503-v1', 'homeViewportRevision': 'browser-viewport-flex-clamp-and-nonblocking-decoration-v1', 'workplaceViewportRevision': 'container-resize-statistics-grid-table-header-v1', 'canonicalHomeRootRevision': 'exact-https-project-root-301-v1', 'workplaceTaskHeadersRevision': 'native-font-14-15-16-sizes-small-default-large-v2', 'platformAsyncRequestMetadata': {'revision': 'original-async-request-by-value-v1', 'files': {'payload/platform/run-template/own-platform-async-request.jar': {'bytes': 11183, 'sha256': '027f4c83709fe23116aa5add92a612e75f15f287a9d95fdca37fd45e5999348f'}, 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class': {'bytes': 6959, 'sha256': '5786e6b82ffd0faba74e53bfc62dcad3d41f13d83235b9f3ad404937741d659e'}}, 'originalAsyncConfigSHA256': 'b692d97a18bee115146d705e411610db8f1b1ea5bd4ee13184d4a53bdd8734d4'}, 'nativeTaskGuardAndTemporaryLayout': {'revision': 'original-task-short-temp-and-pool-budget-v1', 'taskController': {'path': 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class', 'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}, 'parameterAdapter': {'path': 'tools/original_server_release_parameters.py', 'bytes': 17734, 'sha256': '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'}}, 'riskUnitNativeSessionCandidate': 'original-risk-current-session-atomic-v1', 'materialExcelFileTransaction': {'revision': 'original-whole-file-material-import-v1', 'classes': {'payload/business/run-template/classes/com/iemp/endanger/server/materials/controller/MaterialsController.class': {'bytes': 5164, 'sha256': '5a8d0b4103492819aa211c44aac854f47bcac439fbb8dcbda827926300affa4f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport$1.class': {'bytes': 5289, 'sha256': 'f405405dd5bb633da5c41f16398c4dc16be7fd2599ecb3644fed14a809768f7f'}, 'payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport.class': {'bytes': 5109, 'sha256': '1506e3cb8d4ebcadbba67f8565ea8125c440b772343e0ad62b36194673e7287a'}}}, 'nativeTeamMemberMapper': {'revision': 'original-members-default-scan-v1', 'resources': {'payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml': {'bytes': 2568, 'sha256': '2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'}}, 'retainedSources': {'payload/business/application.jar': {'bytes': 1371849, 'sha256': '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'}, 'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class': {'bytes': 7764, 'sha256': '69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4'}}}, 'runtimeConnectionPoolPolicy': {'revision': 'pool-family-budget-v2', 'mysqlMinimum': 24, 'mysqlMaximum': 256, 'reservedConnections': 12, 'maximumSinglePool': 128}, 'nativeSessionDefaultContext': {'revision': 'native-current-user-default-context-v1', 'endpoint': '/api/oauth/CurrentUser', 'explicitSystemCode': False, 'interceptor': {'path': 'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class', 'sha256': 'a1ba06d94e2a0c23e755e9975ae14fe55ceafb5d3b5c086c821a5fdf6887fa37', 'bytes': 8483}, 'originalSDKAndPermissionsRetained': True, 'cacheValidatedSessions': False}, 'nativePortalAvatarSource': {'revision': 'two-native-portal-avatar-source-and-original-default-icon-v1', 'headerSourceSHA256': '5ec7dd353ecdd6e67880d8940e2c42f80dc12e7a851174b1390f9eb80a726bb3', 'normalizerSourceSHA256': '1ee6ad59c92aea246ffe339ebf63ee14ad522405a178f7996e840387a270193d', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 339, 'manifestSHA256': '69592cf5a8116a1b5f22a44580ccff923da2a9afb0c5d5b37e36020c6087ec86'}}, 'originalLoginSDKAndPermissionsRetained': True, 'originalMissingPhotoRestored': False}, 'nativeEmergencyProjectHeaderHome': {'revision': 'emergency-project-mark-and-canonical-home-v1', 'projectMarkSHA256': '509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d', 'layoutAdapterSHA256': '0c5e94c17387c2e980798a96d0734d53acb10ab87ee44d16c245afdebe7e46a8', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': '40119e3ca86085aeedb03efecc546d0f8297915f11952db5e7f92c625ea75426'}}, 'canonicalHome': '/home/index', 'legacyHomeAlias': '/home', 'originalAvatarAndAuthRetained': True, 'originalUserMenuDataRetained': True}, 'nativeWorkflowPendingOperatorVisibility': {'revision': 'exact-native-pending-operator-visibility-v1', 'component': 'src/components/workflow/info.vue', 'componentSHA256': '273cf0fb1f9e691cd2e3f585bd67a29d95b82f9dd1f95b3d1ef9a593f6a9c510', 'adapterSHA256': '5fc16002b17ffa48f086166e9db0df7e91d4f15704dbb397a06af5fe161c12ac', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 338, 'manifestSHA256': 'c4d09d02af5cfb462e45a9ed5a2c6f6feafc11c9a866f435b61ed8892164f81f'}}, 'exactCurrentUserProcessAndOperatorMembership': True, 'pendingLookupFailureDoesNotOfferApproval': True, 'originalAuthAuditAPIsAndInitiatorRulesRetained': True, 'independentBeforeAddsignOpinionFixed': False}, 'nativePersonalWorkflowRoutes': {'revision': 'authenticated-native-personal-workflow-pages-v1', 'frontends': {'security_pc': {'files': 836, 'manifestSHA256': '58311ebacbcfa8479218c15ad6f1ce8387b4d7dec2f714aa84b7cbb41206192b'}, 'emergency_pc': {'files': 340, 'manifestSHA256': '59bbadf5cec69e037c62f9851610c441435510484befb0e51a4847405d33ce9b'}}, 'adapterSHA256': 'cea0cd6abb28bb580db1a4776653cffa4c0fd42afc64dfcbd2ed71a9c21a5667', 'compiledSourceSHA256': {'src/router/routes.ts': '31b82a48157c1004048c0c4513dbbd56e9a9c8b424f3114e85e4f4651bd202bd', 'src/views/home/index.vue': 'ab6114919d10462c9db5a5b88764a96d2238fe3633121a2e7070ac9bb0294ef6', 'src/views/workflow/completedMatters/index.vue': '11ef812b739e50276e3070a68da47e1b63cf92c9baa2413d8534e967ad756087', 'src/views/workflow/completedMatters/info/index.vue': '79e62a84017568a4c529d7f49bd9d7f4015d62f2b7399fe8b95dfe4519e17e21'}, 'originalAuthenticatedMenuLoaderAndBackendAPIsRetained': True, 'configuredMenuRoutesNotReplaced': True, 'missingPersonalPagesRegisteredAfterAuthentication': True, 'handledDetailReadOnly': True, 'originalPendingOperatorVisibilityRetained': True, 'publicIndependentBeforeAddsignOpinionFixed': False}, 'nativeBeforeAddsignOpinionHistory': {'revision': 'native-before-addsign-original-date-history-v1', 'files': {'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class': {'bytes': 7462, 'sha256': 'cf8d31615a3dc0bf76a577151f3a1f90757f3840c9593775b2358c583ac869fa'}, 'payload/platform/run-template/own-before-addsign-history.jar': {'bytes': 11949, 'sha256': '4031f4e36efc985e079f53c684441e7093498b2536d5afcf4c9e5c36805bd017'}}, 'sameOriginalDynamicTransactionAndConnection': True, 'originalNativeServiceCallGate': True, 'originalJavaDateFieldsCopied': True, 'newDatasourceDDLOrStatusCode': False, 'originalAsyncAndAuthArchivesRetained': True}, 'staticInitialLoadPerformance': {'revision': 'gzip-hash-assets-no-store-html-api-v1', 'files': {'tools/original_project_branding.py': {'bytes': 6955, 'sha256': 'a8ba77817ab0fd3f1e45d06605204c27f2840f27aedb392f6590a91a9c3def4c'}, 'deploy/iis_original/App_Code/XnbyReferenceProxy.cs': {'bytes': 12869, 'sha256': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53'}, 'iis/App_Code/XnbyReferenceProxy.cs': {'bytes': 12869, 'sha256': '555c350a8ba9c15e118761f86de21e5e1373a26ee225a04d3f1602a21ab92e53'}}, 'onlyPublicStaticGETHEADNegotiatesGzip': True, 'encodedResponseBytesPreserved': True, 'contentEncodingAndVaryForwarded': True, 'successfulHashedAssetsImmutable': True, 'htmlBusinessErrorsAndNonHashedResourcesNotLongCached': True, 'businessPayloadAuthDatabaseAndPrivateConfigurationUnchanged': True}}
R39_PLAN_FIELD="nativePlanAtomicCompatibility"
R39_PLAN_CLASS='payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
R39_PLAN_ROW={'bytes': 21713, 'sha256': '384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'}
R39_PLAN_CONTRACT={'schema': 'xnby.native-plan-atomic.v1', 'javaMajor': 61, 'originalJarPlanClassSHA256': '3015417dfedfd3a2d0c139f79d7f1f4f5391f3919c9ce9b853a7aee8a8d744ce', 'candidateSourceSHA256': '5ad79c9bbbfcf2cce8488e28cad2fecf153b993e242c1e24a8c34a4b525d9fc6', 'files': {'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class': {'bytes': 21713, 'sha256': '384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'}}, 'schemaOrOriginalJarOrAuthenticationChanged': False}

def native_plan_runtime_declared(release, payload):
    rows=payload.get('files',{})
    if R39_PLAN_FIELD not in release:
        require(R39_PLAN_CLASS not in rows,'UNDECLARED_NATIVE_PLAN_RUNTIME_CLASS')
        return False
    require(release[R39_PLAN_FIELD]==R39_PLAN_CONTRACT,'EXACT_NATIVE_PLAN_RUNTIME_CONTRACT_REQUIRED')
    require(rows.get(R39_PLAN_CLASS)==R39_PLAN_ROW,'EXACT_NATIVE_PLAN_RUNTIME_CLASS_PIN_REQUIRED')
    jar=R38_MAPPER_CONTRACT['originalBusinessJar']
    require(rows.get(jar['path'])=={'bytes':jar['bytes'],'sha256':jar['sha256']},'NATIVE_PLAN_REQUIRES_ORIGINAL_BUSINESS_JAR')
    return True

def native_plan_runtime_ready(app,row):
    release=read(app/'release-manifest.json')
    payload=read(check_file(app,'payload-manifest.json',release['payloadManifestSHA256']))
    if not native_plan_runtime_declared(release,payload):return None
    pin=R39_PLAN_ROW
    check_file(app,R39_PLAN_CLASS,pin['sha256'],pin['bytes'])
    runtime=Path(row['run'])/'b'
    check_file(runtime,R39_PLAN_CLASS.split('/run-template/',1)[1],pin['sha256'],pin['bytes'])
    return {'candidatePlanClassSHA256':pin['sha256'],'installedAndRuntimeClassCopyMatched':True,
            'businessJDK':17,'actualBusinessFlowAcceptedByReadinessAlone':False}

R44_STYLE_ROWS = {'frontend/security_pc/index.html': {'bytes': 2591, 'sha256': '27b3a64cbac2189bc7ff39e7b797ce46b8afefc92e739ea6ba9b119c016bd296'}, 'frontend/security_pc/assets/css/xnby-workplace-period-736f7b07dd2c.css': {'bytes': 1915, 'sha256': '736f7b07dd2cebca59b613be97ac0288bde3ca01b54416d7a680f0ce97da68a3'}}
R44_STYLE_FIELD = "workplacePeriodHeaders"
R44_STYLE_CONTRACT = {'revision': 'scoped-chart-period-header-and-content-spacing-v1', 'files': {'frontend/security_pc/index.html': {'bytes': 2591, 'sha256': '27b3a64cbac2189bc7ff39e7b797ce46b8afefc92e739ea6ba9b119c016bd296'}, 'frontend/security_pc/assets/css/xnby-workplace-period-736f7b07dd2c.css': {'bytes': 1915, 'sha256': '736f7b07dd2cebca59b613be97ac0288bde3ca01b54416d7a680f0ce97da68a3'}}, 'scopeIds': ['data-v-0c8e02ef', 'data-v-7ffd414d'], 'onlyScopedLayoutAndOneHTMLLink': True, 'originalScriptsAPIsAndDateQueriesRetained': True, 'originalHashNamedAssetsNotOverwritten': True, 'publicLayoutAcceptedByStartup': False}

R45_BOOTSTRAP_FIELD = "emergencyOriginalFormBootstrap"
R45_BOOTSTRAP_CONTRACT = {'revision': 'original-sdk-online-forms-and-canonical-authenticated-bootstrap-v1', 'compiledSourceDeltaFromR44': {'src/components/workflow/components/OriginalWorkflowOnlineFormR470.vue': {'bytes': 2551, 'sha256': 'abbd35fc8dd149551acc4258706bd5746726ece6d1331a8abd16bab01d0cca00'}, 'src/router/index.ts': {'bytes': 1798, 'sha256': '6f643bf842c6c98ac007dfd2d2c2d4e5d2fb924f83bf192a312ccbd986d8809e'}, 'src/components/workflow/components/businessForm.vue': {'bytes': 3614, 'sha256': '4ca60991bfa6965e4b6c173a8b762d923ce4d2fdf8303f291e2048848f1eaef6'}, 'src/OriginalAuthenticatedInstallerR817.ts': {'bytes': 363, 'sha256': 'bdf96d80fdd267e0965175333f1d665e3657683f7d99bb579027f56ec5db6371'}, 'src/global-import.ts': {'bytes': 890, 'sha256': 'b491dcab7a8fd8538f43cab1713c6c126209cbeea86795d803cca789cb6a3e01'}, 'src/components/workflow/components/OriginalWorkflowOnlineFormModelR470.ts': {'bytes': 5575, 'sha256': 'c2d0a881c86cf94c27585cfa06e427bf6575ec2df26a37472f17f5ecc763010d'}, 'src/components/workflow/info.vue': {'bytes': 13790, 'sha256': '5d5a3e102a70413a8991fce712f41de720b85b10af4fe8900250bbc93cb9c17c'}}, 'staticBase': '/zhumadian/emergency/branding-20261025/', 'originalApplicationBase': '/zhumadian/emergency/', 'originalRouterBase': '/zhumadian/emergency', 'completeGlobalComponentsRetained': True, 'onlyCodeLoadPromiseShared': True, 'originalSDKAndBackendRetained': True, 'newSupervisionModuleRequired': False, 'onlySupportedOriginalSchemaFieldsRendered': True, 'allOriginalNangangSchemasAccepted': False, 'actualIISOrPublicAcceptance': False}

def r38_unified_bundle_contract(app,bundle,plan,old,release,payload):
    require(original_mapper_defaults_declared(release), 'R38_EXACT_MAPPER_DEFAULT_DESCRIPTOR_REQUIRED')
    require(release.get(R38_FRONTEND_FIELD)==R38_FRONTEND_CONTRACT, 'R38_EXACT_COMPILED_FRONTEND_DESCRIPTOR_REQUIRED')
    require(static_performance_declared(release), 'R38_RETAINED_STATIC_PERFORMANCE_REQUIRED')
    require({n:p for n,p in old.items()if n!='payloadManifestSHA256'}in (R37_STATIC_BASE_METADATA,R39_R37_BASE_METADATA), 'R39_EXACT_R36_OR_R37_BASE_METADATA_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    oldfront={n:p for n,p in previous['files'].items()if n.startswith('frontend/emergency_pc/')}
    require(R39_PLAN_CLASS not in previous['files'],'R39_REQUIRES_NO_PREEXISTING_PLAN_OVERRIDE')
    expected_files={n:p for n,p in previous['files'].items()if n not in oldfront};expected_files.update(R38_FRONTEND_ROWS);expected_files.update(R44_STYLE_ROWS);expected_files[R39_PLAN_CLASS]=R39_PLAN_ROW
    updater='tools/original_public_test_update.py';parameter=R24_PARAMETER
    source_pins={**R37_STATIC_CONTRACT['files'],parameter:R38_PARAMETER_PIN,updater:{'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__))}}
    for n,pin in source_pins.items():
        if n in previous['files']:expected_files[n]=pin
    expected_payload=dict(previous);expected_payload['files']=expected_files
    require(payload==expected_payload,'R38_ALL_OTHER_PAYLOAD_AND_PRIVATE_CONFIGURATION_RETAINED')
    expected=json.loads(json.dumps(old));expected['payloadManifestSHA256']=release['payloadManifestSHA256']
    expected['controllerFiles'].update({n:p['sha256']for n,p in source_pins.items()})
    expected[R24_WORKFLOW_FIELD]=workflow_contract_for(release);expected[R38_MAPPER_FIELD]=R38_MAPPER_CONTRACT
    expected[R38_FRONTEND_FIELD]=R38_FRONTEND_CONTRACT;expected[R37_STATIC_FIELD]=R37_STATIC_CONTRACT;expected[R39_PLAN_FIELD]=R39_PLAN_CONTRACT
    expected.update(publicAccepted=False,publicTestRevision=R38_REVISION);expected[R44_STYLE_FIELD]=R44_STYLE_CONTRACT;expected[R45_BOOTSTRAP_FIELD]=R45_BOOTSTRAP_CONTRACT
    require(release==expected,'R38_EXACT_COMPOSITION_AND_ALL_OTHER_RELEASE_FIELDS_RETAINED')
    require(workflow_declared(release,payload)and runtime_pool_declared(release),'R38_RETAINED_WORKFLOW_AND_POOL_REQUIRED')
    require(native_plan_runtime_declared(release,payload),'R39_EXPLICIT_NATIVE_PLAN_RUNTIME_REQUIRED')
    changed={n:p for n,p in R38_FRONTEND_ROWS.items()if oldfront.get(n)!=p};changed.update({n:p for n,p in R44_STYLE_ROWS.items()if previous['files'].get(n)!=p})
    removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldfront.items()if n not in R38_FRONTEND_ROWS}
    required=set(changed)|set(source_pins)|{'release-manifest.json','payload-manifest.json',R39_PLAN_CLASS}
    require(set(plan['files'])==required,'R38_ONLY_EXACT_COMPOSED_INSTALL_PATHS_REQUIRED')
    require(plan['removedFrontendFiles']==removed,'R38_ONLY_EXACT_OBSOLETE_EMERGENCY_FRONTEND_REMOVALS')
    require(plan['oldPayloadFiles']=={n:previous['files'][n]for n in required if n in previous['files']},'R38_EXACT_OLD_PAYLOAD_PINS_REQUIRED')
    for n,pin in {**changed,**source_pins,R39_PLAN_CLASS:R39_PLAN_ROW}.items():
        require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'R38_EXACT_COMPOSED_TRANSPORT_PIN_REQUIRED:'+n)
        check_file(bundle/'payload',n,pin['sha256'],pin['bytes'])
    proxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs';actual='iis/App_Code/XnbyReferenceProxy.cs'
    require(plan.get('iisProxySHA256')==old['controllerFiles'][proxy]and plan.get('legacyEntrySHA256')=={actual:[old['controllerFiles'][proxy]]},'R38_EXACT_OLD_IIS_PROXY_SOURCE_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))}and plan['acceptedOldReleases'][sha(app/'release-manifest.json')]=={'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']},'R38_ONE_EXACT_INSTALLED_BASE_REQUIRED')
    require(plan.get('callbackOverlay')=='payload/callback-overlay/20261026-password-identity/manifest.json'and plan.get('callbackOverlaySHA256')=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb','R38_ORIGINAL_CALLBACK_OVERLAY_RETAINED')
    return True

def static_performance_declared(release):
    if R37_STATIC_FIELD not in release:return False
    require(release[R37_STATIC_FIELD] == R37_STATIC_CONTRACT, 'R37_EXACT_STATIC_DESCRIPTOR_REQUIRED')
    controls=release['controllerFiles']; updater='tools/original_public_test_update.py'
    expected=dict(R37_STATIC_BASE_METADATA['controllerFiles'])
    expected.update({n:p['sha256'] for n,p in R37_STATIC_CONTRACT['files'].items()})
    expected[updater]=sha(Path(__file__))
    if original_mapper_defaults_declared(release):expected[R24_PARAMETER]=R38_PARAMETER_PIN['sha256']
    require(controls==expected,'R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED')
    return True

def static_performance_bundle_contract(app,bundle,plan,old,release,payload):
    require(static_performance_declared(release),'R37_EXPLICIT_STATIC_DESCRIPTOR_REQUIRED')
    # The fixed public wrapper additionally pins the exact deployed R36 release SHA.
    # Keeping only the payload manifest pointer variable permits the existing synthetic
    # private-configuration fixture without reading a real credential file.
    require({n:p for n,p in old.items() if n!='payloadManifestSHA256'}==R37_STATIC_BASE_METADATA,'R37_EXACT_R36_RELEASE_METADATA_AND_CONTROLS_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))},'R37_ONLY_ONE_INSTALLED_RELEASE_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    require(payload==previous and release['payloadManifestSHA256']==old['payloadManifestSHA256'],'R37_EVERY_PAYLOAD_ROW_AND_MANIFEST_BYTE_RETAINED')
    mutable={'controllerFiles','publicTestRevision','publicAccepted',R37_STATIC_FIELD}
    require({n:p for n,p in old.items()if n not in mutable}=={n:p for n,p in release.items()if n not in mutable},'R37_ALL_BUSINESS_FRONTEND_AUTH_AND_HISTORY_RELEASE_FIELDS_RETAINED')
    require(release.get('publicAccepted') is False and release.get('publicTestRevision')=='20261103-R37-static-initial-load-performance','R37_EXACT_STATIC_REVISION_REQUIRED')
    proxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs'; actual='iis/App_Code/XnbyReferenceProxy.cs'; updater='tools/original_public_test_update.py'
    require(plan.get('iisProxySHA256')==old['controllerFiles'][proxy],'R37_OLD_IIS_PROXY_PIN_REQUIRED_BEFORE_MUTATION')
    require(plan.get('legacyEntrySHA256')=={actual:[old['controllerFiles'][proxy]]},'R37_ONLY_EXACT_EXISTING_IIS_PROXY_LEGACY_PIN_REQUIRED')
    require(plan.get('oldPayloadFiles')=={} and plan.get('removedFrontendFiles')=={},'R37_NO_BUSINESS_OR_FRONTEND_CHANGE_OR_REMOVAL')
    required=set(R37_STATIC_CONTRACT['files'])|{updater,'release-manifest.json','payload-manifest.json'}
    require(set(plan['files'])==required,'R37_EXACT_SIX_STATIC_INSTALL_PATHS_REQUIRED')
    for n,pin in R37_STATIC_CONTRACT['files'].items():
        require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'R37_EXACT_STATIC_TRANSPORT_PIN_REQUIRED:'+n)
        check_file(bundle/'payload',n,pin['sha256'],pin['bytes'])
    require(plan['files'][updater]=={'bytes':Path(__file__).stat().st_size,'SHA256':sha(Path(__file__))},'R37_EXACT_SELF_UPDATER_REQUIRED')
    return True


R46_HOME_BASE_RELEASE_SHA = '3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
R46_HOME_BASE_PAYLOAD_SHA = '8df6a57a9dfec2c8c5ff65964db66b27b752a73cc026241576222bd4bcfc58bb'
R46_HOME_FIELD = 'homeTransferAssets'
R46_HOME_FEATURE = {'allOriginalGlyphsRetained': True, 'changedFiles': {'frontend/security_pc/assets/css/xnby-home-transfer-162b8ebe4004d78f.css': {'bytes': 381, 'sha256': '162b8ebe4004d78febc02d070c40734d9b1d0de66629d8aa6dfc83f63bd7797f'}, 'frontend/security_pc/assets/webp/home-background-415f7103fab4437c.webp': {'bytes': 2591292, 'sha256': '415f7103fab4437c13faeca1d33461c49cee62a3671e6ee290a3bb18e301fb97'}, 'frontend/security_pc/assets/woff2/YouSheBiaoTiHei-7af84bf1c97ae44e.woff2': {'bytes': 745328, 'sha256': '7af84bf1c97ae44e868e87303b6fcf485e7aa76cad58852ffaeb4c6c24e2d87b'}, 'frontend/security_pc/index.html': {'bytes': 2737, 'sha256': '730062a12cd7b52e4297302cbaaf3ed6756fa259e37297129ce8620a005aa562'}}, 'completeSecurityFrontendAfter': {'files': 840, 'manifestSHA256': 'bc5e0c96b588bb3155f63f90f661d5d29260e29b57bdc3436ae072b985207202'}, 'normalOriginalSDKAccepted': False, 'originalICCAndPixelsRetained': True, 'originalR45HTMLSHA256': '27b3a64cbac2189bc7ff39e7b797ce46b8afefc92e739ea6ba9b119c016bd296', 'publicAccepted': False, 'revision': 'lossless-navigation-assets-r900', 'staticFixturePixelChecksPassed': 3}
R46_HOME_FRONTEND = {'frontend/security_pc/assets/css/xnby-home-transfer-162b8ebe4004d78f.css': {'bytes': 381, 'sha256': '162b8ebe4004d78febc02d070c40734d9b1d0de66629d8aa6dfc83f63bd7797f'}, 'frontend/security_pc/assets/webp/home-background-415f7103fab4437c.webp': {'bytes': 2591292, 'sha256': '415f7103fab4437c13faeca1d33461c49cee62a3671e6ee290a3bb18e301fb97'}, 'frontend/security_pc/assets/woff2/YouSheBiaoTiHei-7af84bf1c97ae44e.woff2': {'bytes': 745328, 'sha256': '7af84bf1c97ae44e868e87303b6fcf485e7aa76cad58852ffaeb4c6c24e2d87b'}, 'frontend/security_pc/index.html': {'bytes': 2737, 'sha256': '730062a12cd7b52e4297302cbaaf3ed6756fa259e37297129ce8620a005aa562'}}
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


def load_bundle(app, bundle, pin, *, expected_target=TARGET, expected_port=18892):

    regular(app); regular(bundle)

    require(re.fullmatch('[0-9a-f]{64}', pin or '') is not None, 'MANIFEST_PIN_REQUIRED')

    check_file(bundle, 'update-manifest.json', pin)

    plan = read(bundle / 'update-manifest.json')

    require(plan['schema'] == 'zhumadian.public-test-update.v1'

            and plan['targetApplication'] == Path(expected_target).as_posix()

            and plan['gatewayPort'] == expected_port

            and plan['databaseUploadsCredentialsGISOrDependenciesIncluded'] is False,

            'EXACT_PUBLIC_TEST_UPDATE_REQUIRED')

    old_pin = sha(regular(app, 'release-manifest.json'))

    require(old_pin in plan['acceptedOldReleases'], 'UNKNOWN_INSTALLED_RELEASE_NO_FILES_CHANGED')

    old = read(app / 'release-manifest.json')

    accepted = plan['acceptedOldReleases'][old_pin]

    require(old['releaseId'] == plan['releaseId'] and

            old['payloadManifestSHA256'] == accepted['payloadManifestSHA256'] ==

            plan['basePayloadManifestSHA256'], 'ORIGINAL_PAYLOAD_BASE_REQUIRED')

    check_file(app, 'payload-manifest.json', old['payloadManifestSHA256'])

    for name, digest in accepted['controllerFiles'].items():

        check_file(app, name, digest)

    require(len(plan['files']) <= 1000 and

            sum(row['bytes'] for row in plan['files'].values()) <= 32 * 1024 ** 2,

            'SPARSE_UPDATE_LIMIT_EXCEEDED')

    require(not set(plan['files']).intersection(plan['removedFrontendFiles']), 'REPLACEMENT_REMOVAL_COLLISION')

    changes = {}

    for name, row in plan['files'].items():

        allowed = name.startswith(('frontend/security_pc/', 'frontend/emergency_pc/',

            'frontend/mobile/', 'payload/callback-overlay/20261026-password-identity/')) or name in (

            'release-manifest.json', 'payload-manifest.json', 'Start_Original_Server.cmd',

            'Deploy_Original_Server.cmd', 'Rollback_Original_Server.cmd', 'Start_Callback_Candidate.cmd',

            'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class',

            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class',

            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class',

            'payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeTrainServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeExamServiceImpl.class',

            'payload/business/run-template/classes/xnby/replica/OriginalTrainingTransactionObservation.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkSignServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkMeasuresRelevanceServiceImpl.class',

            'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class',

            'payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class',

            'payload/business/run-template/classes/xnby/replica/OriginalFindingFailureObservation.class',

            'payload/business/run-template/classes/xnby/replica/OriginalFindingFailureObservation$Resolver.class',

            'payload/business/run-template/own-finding-observation.enabled',

            'payload/business/run-template/classes/com/iemp/endanger/server/hidden/service/impl/RiskLevelServiceImpl.class',

            'payload/business/run-template/classes/com/iemp/endanger/server/hidden/controller/RiskLevelController.class',

            'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInitializer.class',

            'payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class',

            'payload/business/run-template/classes/META-INF/spring.factories') or name in R23_ASYNC_ROWS or name == R24_TASK_CLASS or name in R25_MATERIAL_ROWS or name in R26_TEAM_ROWS or name in (

                read(bundle / 'payload/release-manifest.json')['controllerFiles'])

        allowed = allowed or (history_declared(read(bundle / 'payload/release-manifest.json')) and name in R36_HISTORY_CONTRACT['files'])

        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),

                'UNEXPECTED_UPDATE_PATH:' + name)

        check_file(bundle / 'payload', name, row['SHA256'], row['bytes'])

        target = regular(app, name)

        before = None

        if name in accepted['controllerFiles']:

            before = accepted['controllerFiles'][name]

        elif name in plan['oldPayloadFiles']:

            before = plan['oldPayloadFiles'][name]['sha256']

        elif name == 'release-manifest.json':

            before = old_pin

        elif name == 'payload-manifest.json':

            before = old['payloadManifestSHA256']

        elif name in plan['legacyEntrySHA256']:

            require(target.is_file() and sha(target) in plan['legacyEntrySHA256'][name],

                    'UNKNOWN_OLD_ENTRY_SCRIPT')

            before = sha(target)

        if before is None:

            require(not target.exists(), 'NEW_PATH_ALREADY_EXISTS:' + name)

        else:

            check_file(app, name, before)

        changes[name] = {'before': before, 'after': row['SHA256']}

    check_file(bundle / 'payload', 'release-manifest.json', plan['newReleaseSHA256'])

    check_file(bundle / 'payload', 'payload-manifest.json', plan['newPayloadManifestSHA256'])

    release = read(bundle / 'payload/release-manifest.json')

    require(release['releaseId'] == old['releaseId'] and release['payloadManifestSHA256'] ==

            plan['newPayloadManifestSHA256'], 'NEW_RELEASE_IDENTITY_MISMATCH')

    payload = read(bundle / 'payload/payload-manifest.json')

    require(payload['releaseId'] == release['releaseId'], 'NEW_PAYLOAD_IDENTITY_MISMATCH')

    if R46_HOME_FIELD in release:
        r46_home_bundle_contract(app,bundle,plan,old,release,payload)
    elif R38_FRONTEND_FIELD in release or R38_MAPPER_FIELD in release:
        r38_unified_bundle_contract(app,bundle,plan,old,release,payload)
    elif R37_STATIC_FIELD in release:
        static_performance_bundle_contract(app,bundle,plan,old,release,payload)
    else:
        r32_avatar_bundle_contract(app, bundle, plan, old, release, payload)

        risk_bundle_contract(app, bundle, plan, old, release, payload)

        runtime_pool_bundle_contract(app, bundle, plan, old, release, payload)

        async_bundle_contract(app, bundle, plan, old, release, payload)

        material_bundle_contract(app, bundle, plan, old, release, payload)

    point_class = 'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class'

    if point_class in plan['files']:

        require(release.get('inspectionPointEditCandidate') == 'stable-child-ids-atomic-v1',

                'EXPLICIT_INSPECTION_POINT_CANDIDATE_REQUIRED')

        declared = payload['files'].get(point_class)

        actual = plan['files'][point_class]

        require(declared == {'bytes': actual['bytes'], 'sha256': actual['SHA256']},

                'INSPECTION_POINT_CLASS_PAYLOAD_PIN_REQUIRED')

    atomic_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'

    if atomic_class_0 in plan['files']:

        require(release.get('reservationEndTimeCandidate') == 'original-end-time-atomic-v2',

                'EXPLICIT_RESERVATION_END_TIME_CANDIDATE_REQUIRED')

        row = plan['files'][atomic_class_0]

        require(payload['files'].get(atomic_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'RESERVATION_END_TIME_CLASS_PAYLOAD_PIN_REQUIRED')

    atomic_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class'

    if atomic_class_1 in plan['files']:

        require(release.get('thirdPartyCredentialsCandidate') == 'original-credentials-atomic-v2',

                'EXPLICIT_THIRD_PARTY_CREDENTIALS_CANDIDATE_REQUIRED')

        row = plan['files'][atomic_class_1]

        require(payload['files'].get(atomic_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'THIRD_PARTY_CREDENTIALS_CLASS_PAYLOAD_PIN_REQUIRED')

    atomic_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class'

    if atomic_class_2 in plan['files']:

        require(release.get('workTransactionObservationCandidate') == 'work-services-existing-singletons-v1',

                'EXPLICIT_WORK_TRANSACTION_OBSERVER_CANDIDATE_REQUIRED')

        row = plan['files'][atomic_class_2]

        require(payload['files'].get(atomic_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'WORK_TRANSACTION_OBSERVER_CLASS_PAYLOAD_PIN_REQUIRED')

    training_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeTrainServiceImpl.class'

    if training_class_0 in plan['files']:

        require(release.get('trainingEmployeeEditCandidate') == 'parent-first-atomic-v1',

                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')

        row = plan['files'][training_class_0]

        require(payload['files'].get(training_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')

    training_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeExamServiceImpl.class'

    if training_class_1 in plan['files']:

        require(release.get('trainingEmployeeEditCandidate') == 'parent-first-atomic-v1',

                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')

        row = plan['files'][training_class_1]

        require(payload['files'].get(training_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')

    training_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalTrainingTransactionObservation.class'

    if training_class_2 in plan['files']:

        require(release.get('trainingTransactionObservationCandidate') == 'parent-first-atomic-v1',

                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')

        row = plan['files'][training_class_2]

        require(payload['files'].get(training_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']},

                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')

    safety_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkSignServiceImpl.class'

    if safety_class_0 in plan['files']:

        require(release.get('workSafetyBatchEditCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')

        row = plan['files'][safety_class_0]

        require(payload['files'].get(safety_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')

    safety_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkMeasuresRelevanceServiceImpl.class'

    if safety_class_1 in plan['files']:

        require(release.get('workSafetyBatchEditCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')

        row = plan['files'][safety_class_1]

        require(payload['files'].get(safety_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')

    safety_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class'

    if safety_class_2 in plan['files']:

        require(release.get('workSafetyBatchObservationCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')

        row = plan['files'][safety_class_2]

        require(payload['files'].get(safety_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')

    emergency_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class'

    if emergency_class_0 in plan['files']:

        require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXPLICIT_EMERGENCY_TEAM_CANDIDATE_REQUIRED')

        row = plan['files'][emergency_class_0]

        require(payload['files'].get(emergency_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'EMERGENCY_TEAM_CLASS_PAYLOAD_PIN_REQUIRED')

    emergency_class_1 = 'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class'

    if emergency_class_1 in plan['files']:

        require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXPLICIT_EMERGENCY_TEAM_CANDIDATE_REQUIRED')

        row = plan['files'][emergency_class_1]

        require(payload['files'].get(emergency_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'EMERGENCY_TEAM_CLASS_PAYLOAD_PIN_REQUIRED')

    if 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class' in plan['files']:

        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1', 'EXPLICIT_EVENT_DISPOSAL_CANDIDATE_REQUIRED')

        event_class_row = plan['files']['payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class']

        require(event_class_row['SHA256'] == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2' and payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')

    if 'payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class' in plan['files']:

        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1', 'EXPLICIT_EVENT_DISPOSAL_CANDIDATE_REQUIRED')

        event_class_row = plan['files']['payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class']

        require(event_class_row['SHA256'] == '53ad7c1a3996ee2c353938414fb7d0d806d78647bd3f5b93274056f1220e789a' and payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')

    if release.get('eventDisposalAtomicCandidate') is not None:

        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1' and release.get('eventDisposalObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EVENT_DISPOSAL_METADATA_REQUIRED')

        require(payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class', {}).get('sha256') == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')

        require(payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class', {}).get('sha256') == '53ad7c1a3996ee2c353938414fb7d0d806d78647bd3f5b93274056f1220e789a', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')

        event_factory_name = 'payload/business/run-template/classes/META-INF/spring.factories'

        event_prior_initializers = _event_initializers(regular(app, event_factory_name).read_bytes())

        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)

        event_next_initializers = _event_initializers(event_composed_factory.read_bytes())

        require('xnby.replica.OriginalEventDisposalTransactionObservation' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')

    if 'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class' in plan['files']:

        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2', 'EXPLICIT_EMERGENCY_EXERCISE_CANDIDATE_REQUIRED')

        event_class_row = plan['files']['payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class']

        require(event_class_row['SHA256'] == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece' and payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')

    if 'payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class' in plan['files']:

        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2', 'EXPLICIT_EMERGENCY_EXERCISE_CANDIDATE_REQUIRED')

        event_class_row = plan['files']['payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class']

        require(event_class_row['SHA256'] == 'c242fbfa1d552afc19aceeae46cdc6c6d2c7176d39f57bd1cf41bc530cf4f07e' and payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')

    if release.get('emergencyExerciseAtomicCandidate') is not None:

        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2' and release.get('emergencyExerciseObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EMERGENCY_EXERCISE_METADATA_REQUIRED')

        require(payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class', {}).get('sha256') == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')

        require(payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class', {}).get('sha256') == 'c242fbfa1d552afc19aceeae46cdc6c6d2c7176d39f57bd1cf41bc530cf4f07e', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')

        event_factory_name = 'payload/business/run-template/classes/META-INF/spring.factories'

        event_prior_initializers = _exercise_initializers(regular(app, event_factory_name).read_bytes())

        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)

        event_next_initializers = _exercise_initializers(event_composed_factory.read_bytes())

        require('xnby.replica.OriginalEmergencyExerciseTransactionObservation' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')

    # Verify the composed installation before downtime, including retained dependencies.

    # Seed data has already been moved into the installation's mutable database directory.

    for name, row in payload['files'].items():

        if name.startswith('seed/mysql/'):

            continue

        root = bundle / 'payload' if name in plan['files'] else app

        check_file(root, name, row['sha256'], row['bytes'])

    for name, value in release['controllerFiles'].items():

        root = bundle / 'payload' if name in plan['files'] else app

        check_file(root, name, value)

    for name, row in plan['removedFrontendFiles'].items():

        require(name.startswith(('frontend/security_pc/', 'frontend/emergency_pc/', 'frontend/mobile/')),

                'ONLY_OBSOLETE_FRONTEND_REMOVAL_ALLOWED')

        check_file(app, name, row['SHA256'], row['bytes'])

        changes[name] = {'before': row['SHA256'], 'after': None}

    return plan, old_pin, changes



def native_default_declared(release, payload):

    value = release.get(R31_NATIVE_FIELD)

    if value is None:

        require(R31_NATIVE_FIELD not in release, 'EXPLICIT_NATIVE_DEFAULT_DESCRIPTOR_REQUIRED')

        return False

    require(value == R31_NATIVE_CONTRACT

            and release.get('riskUnitNativeSessionCandidate') == R22_RISK_SESSION_REVISION,

            'EXACT_NATIVE_DEFAULT_CONTEXT_CONTRACT_REQUIRED')

    require(payload['files'].get(R31_NATIVE_CLASS) == R31_NATIVE_PIN,

            'EXACT_NATIVE_DEFAULT_CONTEXT_CLASS_REQUIRED')

    return True





def risk_backend_rows(release, payload):

    return {**R22_BACKEND_ROWS, R31_NATIVE_CLASS: R31_NATIVE_PIN} if native_default_declared(release, payload) else R22_BACKEND_ROWS





def native_default_bundle_contract(app, bundle, plan, old, release, payload):

    current = native_default_declared(release, payload)

    if not current:

        require(R31_NATIVE_FIELD not in old, 'NATIVE_DEFAULT_CONTEXT_CANNOT_BE_DROPPED')

        return False

    fresh = R31_NATIVE_FIELD not in old

    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))

    require(risk_declared(old, previous), 'EXACT_PREVIOUS_NATIVE_SESSION_GUARD_REQUIRED')

    if fresh:

        require(previous['files'].get(R31_NATIVE_CLASS) == R22_BACKEND_ROWS[R31_NATIVE_CLASS],

                'EXACT_PREVIOUS_NATIVE_CONTEXT_CLASS_REQUIRED')

        require({R31_NATIVE_CLASS, 'tools/original_public_test_update.py'}.issubset(plan['files']),

                'COMPLETE_NATIVE_CONTEXT_AND_UPDATER_TRANSPORT_REQUIRED')

    else:

        require(native_default_declared(old, previous), 'EXACT_RETAINED_NATIVE_DEFAULT_CONTEXT_REQUIRED')

    pin = plan['files'].get(R31_NATIVE_CLASS)

    if pin is not None:

        require(pin == {'bytes': R31_NATIVE_PIN['bytes'], 'SHA256': R31_NATIVE_PIN['sha256']},

                'EXACT_NATIVE_DEFAULT_TRANSPORT_PIN_REQUIRED')

    root = bundle / 'payload' if pin is not None else app

    check_file(root, R31_NATIVE_CLASS, R31_NATIVE_PIN['sha256'], R31_NATIVE_PIN['bytes'])

    return True





def risk_declared(release, payload):

    revision = release.get('riskUnitNativeSessionCandidate')

    classes = {n for n in R22_BACKEND_ROWS if n.endswith('.class')}

    if revision is None:

        require(R31_NATIVE_FIELD not in release, 'NATIVE_DEFAULT_REQUIRES_ORIGINAL_RISK_GUARD')

        require(not classes.intersection(payload['files']), 'EXPLICIT_RISK_NATIVE_SESSION_REVISION_REQUIRED')

        return False

    require(revision == R22_RISK_SESSION_REVISION, 'EXACT_RISK_NATIVE_SESSION_REVISION_REQUIRED')

    for name, pin in risk_backend_rows(release, payload).items():

        require(payload['files'].get(name) == pin, 'EXACT_RISK_NATIVE_SESSION_PAYLOAD_PIN_REQUIRED:' + name)

    return True





def risk_bundle_contract(app, bundle, plan, old, release, payload):

    """Validate the tested class set and preserve every existing initializer before downtime."""

    if not risk_declared(release, payload):

        require(not set(R22_BACKEND_ROWS).difference({n for n in R22_BACKEND_ROWS if n.endswith('spring.factories')}).intersection(plan['files']), 'RISK_CLASS_WITHOUT_DECLARATION_REFUSED')

        return None

    native_default_bundle_contract(app, bundle, plan, old, release, payload)

    factory = 'payload/business/run-template/classes/META-INF/spring.factories'

    previous = _event_initializers(regular(app, factory).read_bytes())

    root = bundle / 'payload' if factory in plan['files'] else app

    following = _event_initializers(check_file(root, factory, R22_BACKEND_ROWS[factory]['sha256'], R22_BACKEND_ROWS[factory]['bytes']).read_bytes())

    initializer = 'xnby.replica.OriginalNativeSessionInitializer'

    if old.get('riskUnitNativeSessionCandidate') is None:

        require(set(R22_BACKEND_ROWS).issubset(plan['files']), 'COMPLETE_RISK_SESSION_UPGRADE_REQUIRED')

        require(initializer not in previous and following == previous + [initializer], 'EXACT_EXISTING_INITIALIZER_ORDER_PLUS_NATIVE_SESSION_REQUIRED')

    else:

        require(old.get('riskUnitNativeSessionCandidate') == R22_RISK_SESSION_REVISION and following == previous and following.count(initializer) == 1, 'RETAINED_RISK_SESSION_FACTORY_REQUIRED')

    for name, pin in risk_backend_rows(release, payload).items():

        if name in plan['files']:

            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']}, 'RISK_SESSION_TRANSPORT_PIN_REQUIRED')

    return True





def native_session_ready(app, row):

    """Read only the current owned startup marker and the five exact runtime code files."""

    release = read(regular(app, 'release-manifest.json'))

    payload_path = regular(app, 'payload-manifest.json')

    require(sha(payload_path) == release['payloadManifestSHA256'], 'NATIVE_SESSION_PAYLOAD_MANIFEST_PIN_REQUIRED')

    payload = read(payload_path)

    if not risk_declared(release, payload):

        return None

    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())

    require(run.parent == app / 'UserData/OriginalServer/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None, 'OWNED_NATIVE_SESSION_RUN_REQUIRED')

    business = regular(run, 'b')

    owner = marker(regular(business, 'server-owner.properties'))

    require(owner.get('schema') == 'zhumadian.original.server.owner.v1' and owner.get('ownerId') == row['ownerId'], 'NATIVE_SESSION_RUNTIME_OWNER_MISMATCH')

    report = regular(business, 'native-session-guard-ready.properties')

    require(report.is_file() and report.stat().st_size <= 4096, 'BOUNDED_NATIVE_SESSION_READY_REPORT_REQUIRED')

    raw = report.read_bytes()

    require(raw.isascii(), 'ASCII_NATIVE_SESSION_REPORT_REQUIRED')

    lines = raw.decode('ascii').splitlines()

    require(len(lines) == 8 and all(line.count('=') == 1 for line in lines), 'EXACT_NATIVE_SESSION_REPORT_FIELDS_REQUIRED')

    value = dict(line.split('=', 1) for line in lines)

    require(len(value) == len(lines), 'UNIQUE_NATIVE_SESSION_REPORT_FIELDS_REQUIRED')

    expected = {'schema': 'xnby.original-native-session-guard.v1', 'guardCount': '1', 'originalSDKCount': '1', 'guardAfterOriginalSDK': 'true', 'originalSigningAndPermissionsRetained': 'true', 'nativeCurrentSessionChecked': 'true', 'localPositiveCache': 'false', 'unavailableFailsClosed': 'true'}

    require(value == expected, 'EXACT_NATIVE_SESSION_GUARD_READY_REQUIRED')

    prefix = 'payload/business/run-template/'

    for name, pin in risk_backend_rows(release, payload).items():

        check_file(business, name.removeprefix(prefix), pin['sha256'], pin['bytes'])

    return value





def async_declared(release, payload):

    value = release.get(R23_ASYNC_FIELD)

    if R23_ASYNC_FIELD not in release:

        require(not set(R23_ASYNC_ROWS).intersection(payload['files'])

                and R23_ASYNC_HELPER not in release['controllerFiles']

                and release['controllerFiles'].get(R23_CONTROLLER) != R23_CONTROLLER_SHA

                and release['controllerFiles'].get(R23_JOB) != R23_JOB_SHA,

                'EXPLICIT_ASYNC_EXTENSION_REQUIRED')

        return False

    require(isinstance(value, dict) and value == R23_ASYNC_CONTRACT,

            'EXACT_ASYNC_EXTENSION_DESCRIPTOR_REQUIRED')

    for name, pin in R23_ASYNC_ROWS.items():

        require(payload['files'].get(name) == pin, 'EXACT_ASYNC_PAYLOAD_PIN_REQUIRED:' + name)

    return True





def async_bundle_contract(app, bundle, plan, old, release, payload):

    """Check the complete tested extension and controller transition before downtime."""

    workflow = workflow_bundle_contract(app, bundle, plan, old, release, payload)

    if not async_declared(release, payload):

        require(not set(R23_ASYNC_ROWS).intersection(plan['files'])

                and R23_ASYNC_HELPER not in plan['files'], 'ASYNC_CODE_WITHOUT_DECLARATION_REFUSED')

        return None

    controls = release['controllerFiles']

    helper = R23_ASYNC_HELPER

    updater = 'tools/original_public_test_update.py'

    expected = {R23_CONTROLLER: controller_pin_for(release), helper: R23_HELPER_SHA, R23_JOB: R23_JOB_SHA,

                updater: sha(Path(__file__))}

    if history_declared(release):expected[R36_HISTORY_HELPER]=R36_HISTORY_HELPER_SHA

    if workflow:

        expected[R24_PARAMETER] = parameter_pin_for(release)['sha256']

    require(all(controls.get(n) == pin for n, pin in expected.items()),

            'EXACT_ASYNC_CONTROLLER_HELPER_UPDATER_REQUIRED')

    prior = old['controllerFiles']

    fresh = R23_ASYNC_FIELD not in old

    if fresh:

        require(prior.get(R23_CONTROLLER) == R23_OLD_CONTROLLER_SHA

                and prior.get(R23_JOB) == R23_OLD_JOB_SHA

                and helper not in prior and set(controls) == set(prior) | {helper},

                'EXACT_ORIGINAL_CONTROLLER_SET_PLUS_ASYNC_HELPER_REQUIRED')

        require(set(R23_ASYNC_ROWS).issubset(plan['files'])

                and set(expected).issubset(plan['files']), 'COMPLETE_ASYNC_EXTENSION_TRANSPORT_REQUIRED')

    else:

        require(old[R23_ASYNC_FIELD] == R23_ASYNC_CONTRACT and set(controls) == set(prior)|({R36_HISTORY_HELPER}if history_declared(release)else set()),

                'EXACT_RETAINED_ASYNC_CONTROLLER_SET_REQUIRED')

    require({n: p for n, p in controls.items() if n not in expected}

            == {n: p for n, p in prior.items() if n not in expected},

            'OTHER_ORIGINAL_CONTROLLERS_MUST_BE_RETAINED')

    for name, pin in {**R23_ASYNC_ROWS, **{n: {'sha256': p} for n, p in expected.items()}}.items():

        if name in plan['files']:

            actual = plan['files'][name]

            require(actual.get('SHA256') == pin['sha256']

                    and ('bytes' not in pin or actual.get('bytes') == pin['bytes']),

                    'EXACT_ASYNC_TRANSPORT_PIN_REQUIRED:' + name)

        root = bundle / 'payload' if name in plan['files'] else app

        check_file(root, name, pin['sha256'], pin.get('bytes'))

    return True





def async_state(raw):

    require(len(raw) <= 4096 and raw.isascii(), 'BOUNDED_ASCII_ASYNC_STATE_REQUIRED')

    lines = raw.decode('ascii').splitlines()

    require(len(lines) == 7 and all(line.count('=') == 1 for line in lines),

            'EXACT_ASYNC_STATE_FIELDS_REQUIRED')

    value = dict(line.split('=', 1) for line in lines)

    fixed = {'schema': 'xnby.original-async-request-metadata.v1',

             'originalDecoratorRetained': 'true', 'requestHeaderOrTokenValuesRecorded': 'false'}

    counters = {'capturedJobs', 'startedJobs', 'finishedJobs', 'activeJobs'}

    require(set(value) == set(fixed) | counters and all(value[k] == v for k, v in fixed.items()),

            'EXACT_ASYNC_STATE_IDENTITY_REQUIRED')

    for key in counters:

        text = value[key]

        require(re.fullmatch(r'0|[1-9][0-9]{0,18}', text) is not None

                and int(text) <= 9223372036854775807, 'BOUNDED_ASYNC_JOB_COUNT_REQUIRED')

    # The Java writer reads independent AtomicLong counters while jobs run.

    # Cross-counter equality is only valid after verified normal shutdown.

    return value





def async_ready(app, row):

    """Only read pinned code and owned bounded metadata; no account or business queries."""

    app = regular(app)

    release = read(regular(app, 'release-manifest.json'))

    payload_path = regular(app, 'payload-manifest.json')

    require(sha(payload_path) == release['payloadManifestSHA256'], 'ASYNC_PAYLOAD_MANIFEST_PIN_REQUIRED')

    if not async_declared(release, read(payload_path)):

        return None

    platform = regular(app, Path(row['platformRun']).absolute().relative_to(app).as_posix())

    require(platform.parent == app / 'UserData/TianjinOriginalPlatform/runs'

            and re.fullmatch(r'j[1-9][0-9]{0,3}', platform.name), 'OWNED_ASYNC_PLATFORM_RUN_REQUIRED')

    owner = row['ownerId']

    require(isinstance(owner, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', owner),

            'ASYNC_RUN_OWNER_REQUIRED')

    owner_path = regular(platform, 'server-owner.properties')

    expected_owner = ['schema=zhumadian.original.server.owner.v1', 'ownerId=' + owner]

    require(owner_path.is_file() and owner_path.stat().st_size <= 1024

            and owner_path.read_bytes().decode('ascii').splitlines() == expected_owner,

            'ASYNC_RUNTIME_OWNER_MISMATCH')

    for name, pin in R23_ASYNC_ROWS.items():

        check_file(app, name, pin['sha256'], pin['bytes'])

        check_file(platform, name.split('/run-template/', 1)[1], pin['sha256'], pin['bytes'])

    check_file(platform, 'own-platform-observation.jar', R23_AUTH_ADAPTER_SHA)

    for name, pin in ((R23_CONTROLLER, controller_pin_for(release)), (R23_ASYNC_HELPER, R23_HELPER_SHA), (R23_JOB, R23_JOB_SHA)):

        require(release['controllerFiles'].get(name) == pin, 'ASYNC_RUNTIME_CONTROL_DECLARATION_REQUIRED')

        check_file(app, name, pin)

    report = regular(platform, 'async-request-snapshot-state.properties')

    for attempt in range(10):

        try:

            require(report.is_file() and report.stat().st_size <= 4096, 'BOUNDED_ASYNC_READY_REPORT_REQUIRED')

            with report.open('rb') as stream:

                value = async_state(stream.read(4097))

            require(owner_path.read_bytes().decode('ascii').splitlines() == expected_owner,

                    'ASYNC_RUNTIME_OWNER_CHANGED')

            return value

        except (ValueError, FileNotFoundError):

            if attempt == 9:

                raise

            time.sleep(0.05)





def backup_code(app, attempt, changes):

    attempt = regular(attempt)

    require(not attempt.exists(), 'FRESH_BACKUP_REQUIRED')

    attempt.mkdir(parents=True)

    for name, row in changes.items():

        if row['before'] is not None:

            source = check_file(app, name, row['before'])

            dest = regular(attempt / 'before', name)

            dest.parent.mkdir(parents=True, exist_ok=True)

            shutil.copyfile(source, dest)

            check_file(attempt / 'before', name, row['before'])

    write_json(attempt / 'changes.json', changes)



def replace_code(app, bundle, changes, after_each=None):

    # The release pointer changes last, after its complete code and payload manifest.

    names = sorted(changes, key=lambda name: (name == 'release-manifest.json', name))

    for name in names:

        row = changes[name]; target = regular(app, name)

        if row['before'] is None:

            require(not target.exists(), 'CONCURRENT_NEW_PATH:' + name)

        else:

            check_file(app, name, row['before'])

        if row['after'] is None:

            target.unlink()

        else:

            source = check_file(bundle / 'payload', name, row['after'])

            atomic(target, source.read_bytes())

        if after_each:

            after_each(name)



def restore_code(app, attempt, changes):

    # Preflight all paths before restoring any: refuse an unrelated concurrent edit.

    for name, row in changes.items():

        target = regular(app, name)

        current = sha(target) if target.is_file() else None

        require(current in (row['before'], row['after']), 'ROLLBACK_FILE_DRIFT:' + name)

        if row['before'] is not None:

            check_file(attempt / 'before', name, row['before'])

    for name in sorted(changes, key=lambda name: (name == 'release-manifest.json', name)):

        row = changes[name]; target = regular(app, name)

        if row['before'] is None:

            if target.exists():

                target.unlink()

        else:

            atomic(target, (attempt / 'before' / name).read_bytes())



def process_owned(pid, app, pin):

    if type(pid) is not int or pid <= 0:

        return False

    command = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "

               "Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(pid) +

               "' | Select-Object ExecutablePath,CommandLine | ConvertTo-Json -Compress")

    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command],

        capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)

    if result.returncode or not result.stdout.strip():

        return False

    row = json.loads(result.stdout.decode('utf-8-sig'))

    text = row.get('CommandLine') or ''

    return (Path(row.get('ExecutablePath') or '').absolute() == app / 'runtime/python/python.exe'

            and str(app / 'tools/serve_original_server_release.py') in text and pin in text)



def owned_ready(app, pin, *, gateway_port=18892):

    row = read(regular(app, 'UserData/OriginalServer/current-run.json'))

    run = Path(row['run']).absolute()

    require(run.parent == app / 'UserData/OriginalServer/runs' and

            re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None, 'OWNED_RUN_REQUIRED')

    regular(run)

    require(row.get('ready') is True and row.get('gatewayPort') == gateway_port and

            row.get('releaseId') == read(app / 'release-manifest.json')['releaseId'] and

            process_owned(row.get('controllerPID'), app, pin), 'EXACT_READY_PUBLIC_CONTROLLER_REQUIRED')

    return row



def normal_stop(app, pin, row):

    require(process_owned(row['controllerPID'], app, pin), 'CONTROLLER_OWNERSHIP_CHANGED')

    run = regular(app, Path(row['run']).relative_to(app).as_posix())

    print('STOP: requesting normal shutdown of the owned public controller', flush=True)

    atomic(run / 'stop-requested.txt', b'stop\n')

    end = time.monotonic() + 180

    while time.monotonic() < end:

        receipt = run / 'receipt.json'

        if receipt.exists() and not process_owned(row['controllerPID'], app, pin):

            final = read(receipt)

            require(final.get('controllerPID') == row['controllerPID'] and

                    final.get('normalOwnedShutdown') is True and

                    final.get('allOwnedChildrenExited') is True and

                    set(final.get('exitCodesBeforeJobClose', {})) ==

                    {'store', 'mysql', 'redis', 'platform', 'business', 'gateway'} and

                    all(v == 0 for v in final['exitCodesBeforeJobClose'].values()),

                    'UNCLEAN_SHUTDOWN_NO_FILES_CHANGED')

            return final

        time.sleep(1)

    raise RuntimeError('NORMAL_SHUTDOWN_TIMEOUT_NO_FORCE_TERMINATION')



def http_check(port, path):

    client = http.client.HTTPConnection('127.0.0.1', port, timeout=12)

    try:

        client.request('GET', path, headers={'Connection': 'close'})

        response = client.getresponse(); body = response.read(4 * 1024 ** 2 + 1)

        require(len(body) <= 4 * 1024 ** 2, 'BOUNDED_HTTP_RESPONSE_REQUIRED')

        return response.status, body

    finally:

        client.close()



def marker(path):

    return dict(line.split('=', 1) for line in Path(path).read_text('ascii').splitlines()

                if '=' in line and not line.startswith(('#', '!')))



def finding_observer_ready(app, row):

    if read(app / 'release-manifest.json').get('findingFailureObservationExperimental') is not True:

        return None

    path = regular(app, Path(row['run']).relative_to(app).as_posix() + '/b/own-finding-observer-ready.json')

    require(path.is_file() and path.stat().st_size <= 1024, 'FINDING_OBSERVER_READY_REQUIRED')

    value = read(path)

    require(value.get('schema') == 'xnby.finding-observer-ready.v1'

            and value.get('PID') == row.get('children', {}).get('business')

            and type(value.get('PID')) is int

            and value.get('route') == '/checkPlan/saveCheckHiddenDanger'

            and value.get('maximumRecords') == 32

            and value.get('maximumRecordBytes') == 16384

            and value.get('originalResolversContinue') is True,

            'FINDING_OBSERVER_READY_IDENTITY_MISMATCH')

    return value





def training_observer_ready(app, row):

    """Validate startup-only existing singleton metadata; no business calls."""

    release = read(regular(app, 'release-manifest.json'))

    revision = release.get('trainingEmployeeEditCandidate')

    if revision is None:

        return None

    require(revision == release.get('trainingTransactionObservationCandidate') == 'parent-first-atomic-v1',

            'EXACT_TRAINING_RUNTIME_REVISION_REQUIRED')

    run = regular(Path(row['run']))

    path = regular(run / 'b', 'training-transaction-observation.json')

    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_TRAINING_OBSERVER_REPORT_REQUIRED')

    value = read(path)

    require(value.get('schema') == 'xnby.training-transaction-observation.v1'

            and type(value.get('PID')) is int and value['PID'] == row['children']['business']

            and value.get('run') == run.name

            and value.get('ownerIdSHA256') == hashlib.sha256(row['ownerId'].encode('ascii')).hexdigest()

            and value.get('existingSingletonMetadataOnly') is True

            and value.get('businessMethodsInvoked') is False

            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False

            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False,

            'TRAINING_OBSERVER_IDENTITY_OR_SCOPE_MISMATCH')

    pins = {

        'Train': '83d9f3c831073ac16c8b42cef8442a9649081b11aae0353a2ba8e351a0d89c3d',

        'Exam': 'ddf82926cedbb6419c771b384d7e1c63f3210a401f68d984dc28ff7e30cb34e3',

    }

    payload = read(regular(app, 'payload-manifest.json'))

    require(sha(app / 'payload-manifest.json') == release['payloadManifestSHA256'],

            'TRAINING_RUNTIME_PAYLOAD_MANIFEST_PIN_REQUIRED')

    for kind, pin in pins.items():

        name = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/Employee' + kind + 'ServiceImpl.class'

        declaration = payload['files'].get(name)

        require(isinstance(declaration, dict) and declaration.get('sha256') == pin,

                'TRAINING_RUNTIME_CLASS_DECLARATION_REQUIRED')

        check_file(app, name, pin, declaration['bytes'])

        group = value.get(kind)

        require(isinstance(group, dict) and group.get('existingSingletonMetadataOnly') is True

                and group.get('allMethodsHaveMatchingTransactionAdvisor') is True

                and len(group.get('services', [])) == 1,

                'ONE_MATCHING_TRAINING_SERVICE_REQUIRED')

        bean = group['services'][0]

        require(bean.get('existingSingleton') is True and bean.get('isAopProxy') is True

                and bean.get('targetClass') == 'com.iemp.endanger.server.safetyBasic.service.impl.Employee' + kind + 'ServiceImpl'

                and bean.get('targetClassSHA256') == pin

                and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True

                and bean.get('methods', {}).get('updateById', {}).get('matchingExceptionRollbackAdvisor') is True,

                'TRAINING_TARGET_CLASS_OR_TRANSACTION_ADVISOR_MISMATCH')

    return value







def safety_batch_observer_ready(app, row):

    """Require owned startup metadata and exact loaded classes, without business calls."""

    release = read(regular(app, 'release-manifest.json'))

    revision = release.get('workSafetyBatchEditCandidate')

    observation = release.get('workSafetyBatchObservationCandidate')

    if revision is None and observation is None:

        return None

    require(revision == observation == 'work-safety-batch-atomic-v1', 'EXACT_SAFETY_RUNTIME_REVISION_REQUIRED')

    run = regular(Path(row['run']))

    path = regular(run / 'b', 'work-safety-batch-observation.json')

    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_SAFETY_OBSERVER_REPORT_REQUIRED')

    value = read(path)

    require(value.get('schema') == 'xnby.work-safety-batch-observation.v1'

            and type(value.get('PID')) is int and value['PID'] == row['children']['business']

            and value.get('run') == run.name

            and value.get('ownerIdSHA256') == hashlib.sha256(row['ownerId'].encode('ascii')).hexdigest()

            and value.get('existingSingletonMetadataOnly') is True

            and value.get('businessMethodsInvoked') is False

            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False

            and value.get('actualRollbackHTTPOrPermitAcceptanceVerified') is False,

            'SAFETY_OBSERVER_IDENTITY_OR_SCOPE_MISMATCH')

    payload = read(regular(app, 'payload-manifest.json'))

    require(sha(app / 'payload-manifest.json') == release['payloadManifestSHA256'], 'SAFETY_RUNTIME_PAYLOAD_PIN_REQUIRED')

    pins = {

        'signBatch': ('WorkSign', 'e04f7605d831547e4ca4a548d07ea1a4df95cdfcbc9f4c14787581e52c0774e5'),

        'measureBatch': ('WorkMeasuresRelevance', '4d66b3232241e8f0d7e65e9d8fe11ab920c77d641a82021b18b5c2a62dcd6579'),

    }

    observer = 'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class'

    observer_pin = '9074d6476eab2a65af528f65c4553373126c8136916ecf703f08df3ebb05f238'

    declared = payload['files'].get(observer)

    require(isinstance(declared, dict) and declared.get('sha256') == observer_pin, 'SAFETY_OBSERVER_CLASS_DECLARATION_REQUIRED')

    check_file(app, observer, observer_pin, declared['bytes'])

    for key, (short, pin) in pins.items():

        name = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/' + short + 'ServiceImpl.class'

        declared = payload['files'].get(name)

        require(isinstance(declared, dict) and declared.get('sha256') == pin, 'SAFETY_RUNTIME_CLASS_DECLARATION_REQUIRED')

        check_file(app, name, pin, declared['bytes'])

        group = value.get(key)

        require(isinstance(group, dict) and group.get('existingSingletonMetadataOnly') is True

                and group.get('serviceType') == 'com.iemp.endanger.server.work.service.' + short + 'Service'

                and group.get('matchingSaveBatchExceptionRollbackAdvisor') is True

                and len(group.get('services', [])) == 1, 'ONE_MATCHING_SAFETY_SERVICE_REQUIRED')

        bean = group['services'][0]

        require(bean.get('existingSingleton') is True and bean.get('isAopProxy') is True

                and bean.get('targetClass') == 'com.iemp.endanger.server.work.service.impl.' + short + 'ServiceImpl'

                and bean.get('targetClassSHA256') == pin

                and bean.get('matchingSaveBatchExceptionRollbackAdvisor') is True,

                'SAFETY_TARGET_CLASS_OR_TRANSACTION_ADVISOR_MISMATCH')

        advisors = bean.get('advisors')

        require(isinstance(advisors, list) and 1 <= len(advisors) <= 32

                and any(isinstance(a, dict) and a.get('metadataMatched') is True

                        and a.get('staticPointcutMatches') is True and a.get('runtimePointcut') is False for a in advisors),

                'SAFETY_STATIC_EXCEPTION_ROLLBACK_ADVISOR_DETAILS_REQUIRED')

    return value





def emergency_team_observer_ready(app, row):

    release = read(app / 'release-manifest.json')

    if release.get('emergencyTeamAtomicCandidate') is None:

        return None

    require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXACT_TEAM_REVISION_REQUIRED')

    run = Path(row['run'])

    relative = run.relative_to(app).as_posix() + '/b/emergency-team-transaction-observation.json'

    path = regular(app, relative)

    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_TEAM_OBSERVER_REQUIRED')

    value = read(path)

    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))

    require(value.get('schema') == 'xnby.emergency-team-transaction-observation.v1'

            and value.get('PID') == row.get('children', {}).get('business')

            and type(value.get('PID')) is int and value.get('run') == run.name

            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()

            and value.get('existingSingletonMetadataOnly') is True

            and value.get('businessMethodsInvoked') is False

            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False

            and value.get('existingTransactionManagerCount') == 1

            and type(value.get('existingTransactionManagerCount')) is int

            and value.get('allEmergencyTeamMethodsAndManagerMatched') is True,

            'TEAM_OBSERVER_OWNER_OR_ADVISOR_MISMATCH')

    group = value.get('team')

    require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True,

            'TEAM_METHOD_ADVISORS_REQUIRED')

    services = group.get('services')

    require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_TEAM_SERVICE_REQUIRED')

    bean = services[0]

    payload = read(app / 'payload-manifest.json')

    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class', {}).get('sha256')

    require(isinstance(bean, dict) and bean.get('existingSingleton') is True

            and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True

            and expected == '69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4' and bean.get('targetClassSHA256') == expected,

            'EXACT_TESTED_TEAM_SINGLETON_CLASS_REQUIRED')

    checks = bean.get('methods')

    require(isinstance(checks, dict) and all(isinstance(checks.get(name), dict)

            and checks[name].get('matchingExceptionRollbackAdvisor') is True

            for name in ('save', 'updateById')), 'BOTH_TEAM_METHOD_DETAILS_REQUIRED')

    return value





def _event_initializers(raw):

    require(isinstance(raw, bytes) and len(raw) <= 4096, 'BOUNDED_INITIALIZER_REGISTRY_REQUIRED')

    key = b'org.springframework.context.ApplicationContextInitializer='

    lines = [line for line in raw.splitlines() if line.startswith(key)]

    require(len(lines) == 1 and b'\\' not in lines[0], 'EXACT_SINGLE_LINE_INITIALIZER_REGISTRY')

    names = lines[0][len(key):].decode('ascii').split(',')

    require(0 < len(names) <= 32 and len(names) == len(set(names))

            and all(name and name.strip() == name and all(c.isalnum() or c in '._$' for c in name) for name in names),

            'UNIQUE_CANONICAL_RETAINED_INITIALIZERS_REQUIRED')

    return names





def event_disposal_observer_ready(app, row):

    release = read(app / 'release-manifest.json')

    if release.get('eventDisposalAtomicCandidate') is None:

        return None

    require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1'

            and release.get('eventDisposalObservationCandidate') == 'existing-singletons-manager-v1',

            'EXACT_EVENT_DISPOSAL_REVISION_REQUIRED')

    run = Path(row['run'])

    relative = run.relative_to(app).as_posix() + '/b/event-disposal-transaction-observation.json'

    path = regular(app, relative)

    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_EVENT_DISPOSAL_OBSERVER_REQUIRED')

    value = read(path)

    require(isinstance(value, dict), 'EVENT_DISPOSAL_REPORT_OBJECT_REQUIRED')

    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))

    require(value.get('schema') == 'xnby.event-disposal-transaction-observation.v1'

            and value.get('PID') == row.get('children', {}).get('business')

            and type(value.get('PID')) is int and value.get('run') == run.name

            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()

            and value.get('existingSingletonMetadataOnly') is True

            and value.get('businessMethodsInvoked') is False

            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False

            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False

            and value.get('existingTransactionManagerCount') == 1

            and type(value.get('existingTransactionManagerCount')) is int

            and value.get('allEventDisposalMethodsAndManagerMatched') is True,

            'EVENT_DISPOSAL_OBSERVER_OWNER_OR_ADVISOR_MISMATCH')

    group = value.get('disposal')

    require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True

            and group.get('existingSingletonMetadataOnly') is True

            and group.get('serviceType') == 'com.iemp.endanger.server.emergencyResponse.service.EventDisposalRecordService',

            'EXACT_EVENT_DISPOSAL_SERVICE_GROUP_REQUIRED')

    services = group.get('services')

    require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_EVENT_DISPOSAL_SERVICE_REQUIRED')

    bean = services[0]

    payload = read(app / 'payload-manifest.json')

    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class', {}).get('sha256')

    require(isinstance(bean, dict) and bean.get('existingSingleton') is True

            and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True

            and expected == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2' and bean.get('targetClassSHA256') == expected,

            'EXACT_TESTED_EVENT_DISPOSAL_SINGLETON_CLASS_REQUIRED')

    checks = bean.get('methods')

    require(isinstance(checks, dict) and set(checks) == {'saveRecord'}

            and isinstance(checks['saveRecord'], dict)

            and checks['saveRecord'].get('matchingExceptionRollbackAdvisor') is True,

            'EVENT_DISPOSAL_SAVE_RECORD_ADVISOR_DETAIL_REQUIRED')

    return value





def _exercise_initializers(raw):

    require(isinstance(raw, bytes) and len(raw) <= 4096, 'BOUNDED_INITIALIZER_REGISTRY_REQUIRED')

    key = b'org.springframework.context.ApplicationContextInitializer='

    lines = [line for line in raw.splitlines() if line.startswith(key)]

    require(len(lines) == 1 and b'\\' not in lines[0], 'EXACT_SINGLE_LINE_INITIALIZER_REGISTRY')

    names = lines[0][len(key):].decode('ascii').split(',')

    require(0 < len(names) <= 32 and len(names) == len(set(names))

            and all(name and name.strip() == name and all(c.isalnum() or c in '._$' for c in name) for name in names),

            'UNIQUE_CANONICAL_RETAINED_INITIALIZERS_REQUIRED')

    return names





def emergency_exercise_observer_ready(app, row):

    release = read(app / 'release-manifest.json')

    if release.get('emergencyExerciseAtomicCandidate') is None:

        return None

    require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2'

            and release.get('emergencyExerciseObservationCandidate') == 'existing-singletons-manager-v1',

            'EXACT_EMERGENCY_EXERCISE_REVISION_REQUIRED')

    run = Path(row['run'])

    relative = run.relative_to(app).as_posix() + '/b/emergency-exercise-transaction-observation.json'

    path = regular(app, relative)

    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_EXERCISE_OBSERVER_REQUIRED')

    value = read(path)

    require(isinstance(value, dict), 'EXERCISE_REPORT_OBJECT_REQUIRED')

    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))

    require(value.get('schema') == 'xnby.emergency-exercise-transaction-observation.v1'

            and value.get('PID') == row.get('children', {}).get('business')

            and type(value.get('PID')) is int and value.get('run') == run.name

            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()

            and value.get('existingSingletonMetadataOnly') is True

            and value.get('businessMethodsInvoked') is False

            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False

            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False

            and value.get('existingTransactionManagerCount') == 1

            and type(value.get('existingTransactionManagerCount')) is int

            and value.get('allEmergencyExerciseMethodsAndManagerMatched') is True

            and value.get('nonNullUpdateStrategyMatched') is True,

            'EXERCISE_OBSERVER_OWNER_ADVISOR_OR_STRATEGY_MISMATCH')

    strategies = value.get('exerciseUpdateStrategies')

    expected_columns = {'emergency_plan_id', 'exercise_location', 'organize_department', 'commander_chief',

                        'exercise_time', 'participants', 'cooperating_unit', 'exercise_type', 'exercise_device',

                        'exercise_describe', 'exercise_special_situation', 'problems_andmeasures', 'created_at'}

    require(isinstance(strategies, dict) and set(strategies) == expected_columns

            and all(isinstance(item, dict) and item.get('updateStrategy') == 'NOT_NULL'

                    and item.get('withUpdateFill') is False for item in strategies.values()),

            'EXACT_EXERCISE_ACTUAL_FIELD_STRATEGIES_REQUIRED')

    groups = value.get('exercise')

    require(isinstance(groups, dict) and set(groups) == {'save', 'saveList', 'delete'}, 'THREE_EXERCISE_GROUPS_REQUIRED')

    payload = read(app / 'payload-manifest.json')

    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class', {}).get('sha256')

    require(expected == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece', 'EXACT_TESTED_EXERCISE_PAYLOAD_CLASS_REQUIRED')

    for key, method in [('save', 'save'), ('saveList', 'saveEmergencyExerciseList'), ('delete', 'delete')]:

        group = groups[key]

        require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True

                and group.get('existingSingletonMetadataOnly') is True

                and group.get('serviceType') == 'com.iemp.endanger.server.emergency.service.EmergencyExerciseService',

                'EXACT_EXERCISE_SERVICE_GROUP_REQUIRED')

        services = group.get('services')

        require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_EXERCISE_SERVICE_REQUIRED')

        bean = services[0]

        require(isinstance(bean, dict) and bean.get('existingSingleton') is True

                and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True

                and bean.get('targetClassSHA256') == expected,

                'EXACT_TESTED_EXERCISE_SINGLETON_CLASS_REQUIRED')

        checks = bean.get('methods')

        require(isinstance(checks, dict) and set(checks) == {method}

                and isinstance(checks[method], dict)

                and checks[method].get('matchingExceptionRollbackAdvisor') is True,

                'EXERCISE_METHOD_ADVISOR_DETAIL_REQUIRED')

    return value





def health(app, row, guarded=True, *, gateway_port=18892):

    for path in ['/zhumadian/home', '/zhumadian/h5/', '/zhumadian/project-icon-20261025.svg',

                 '/zhumadian/api/jnpf/oauth/getLoginConfig']:

        status, body = http_check(gateway_port, path)

        require(status == 200, 'OWN_GATEWAY_HTTP_FAILED:' + path)

        if path.endswith('getLoginConfig'):

            require(json.loads(body).get('code') == 200, 'LOGIN_CONFIG_FAILED')

    if guarded:

        status, body = http_check(gateway_port, '/zhumadian/api/serv/checkInventory/page?current=1&size=1')

        result = json.loads(body)

        require(status == 200 and result.get('code') == 600 and result.get('data') is None,

                'MISSING_AUTH_CONTRACT_FAILED')

        run = Path(row['run']); platform = Path(row['platformRun'])

        regular(run); regular(platform)

        guard = marker(run / 'b/missing-auth-guard-ready.properties')

        password = marker(platform / 'password-identity-claims-ready.properties')

        require(guard.get('guardCount') == guard.get('originalSecurityInterceptorCount') == '1'

                and guard.get('guardBeforeOriginal') == 'true' and

                guard.get('tokenValidationReplaced') == 'false', 'ORIGINAL_AUTH_CHAIN_REQUIRED')

        require(password.get('passwordBeanAdapted') ==

                password.get('originalPasswordAuthenticationInherited') ==

                password.get('originalSigningAndSessionsInherited') == 'true',

                'ORIGINAL_PASSWORD_AND_SESSION_CHAIN_REQUIRED')

    finding_observer_ready(app, row)

    emergency_team_observer_ready(app, row)

    emergency_exercise_observer_ready(app, row)

    event_disposal_observer_ready(app, row)

    training_observer_ready(app, row)

    safety_batch_observer_ready(app, row)

    native_session_ready(app, row)

    async_ready(app, row)
    history_ready(app, row)

    workflow_ready(app, row)

    material_ready(app, row)

    team_ready(app, row)

    runtime_pool_ready(app, row)

    native_plan_runtime_ready(app,row)



def installed_overlay(app, pin):

    """Preserve the installed callback/auth overlay when restarting or restoring code."""

    check_file(app, 'release-manifest.json', pin)

    release = read(app / 'release-manifest.json')

    digest = release.get('missingAuthOverlayManifestSHA256')

    if digest is None:

        return None

    require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) is not None,

            'INSTALLED_CALLBACK_OVERLAY_PIN_REQUIRED')

    relative = 'payload/callback-overlay/20261026-password-identity/manifest.json'

    check_file(app, relative, digest)

    return relative, digest



def launch(app, pin, folder, overlay=None, *, gateway_port=18892):

    selected = installed_overlay(app, pin)

    require(overlay is None or overlay == selected, 'CALLBACK_OVERLAY_RELEASE_MISMATCH')

    overlay = selected

    log_path = folder / ('controller-' + uuid.uuid4().hex + '.log')

    args = [str(app / 'runtime/python/python.exe'), '-I', '-B',

            str(app / 'tools/serve_original_server_release.py'), '--application', str(app),

            '--release-manifest-sha256', pin, '--gateway-port', str(gateway_port)]

    if overlay:

        args += ['--callback-overlay', str(app / overlay[0]), '--callback-overlay-sha256', overlay[1]]

    with log_path.open('xb') as output:

        process = subprocess.Popen(args, cwd=app, stdout=output, stderr=subprocess.STDOUT,

            close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)

    write_json(folder / 'launch-state.json', {'controllerPID': process.pid,

        'releaseSHA256': pin, 'log': str(log_path), 'ready': False})

    print('START: controller PID=' + str(process.pid) + '; waiting for real ready', flush=True)

    end = time.monotonic() + 600; next_progress = 0

    while time.monotonic() < end:

        if process.poll() is not None:

            raise RuntimeError('NEW_CONTROLLER_EXITED_INSPECT_LOG:' + str(log_path))

        current = app / 'UserData/OriginalServer/current-run.json'

        if current.exists():

            row = read(current)

            if row.get('controllerPID') == process.pid and row.get('ready'):

                write_json(folder / 'launch-state.json', dict(row, releaseSHA256=pin))

                return owned_ready(app, pin, gateway_port=gateway_port)

        if time.monotonic() >= next_progress:

            print('START: waiting; log=' + str(log_path), flush=True)

            next_progress = time.monotonic() + 10

        time.sleep(1)

    # Never kill a controller or restore code underneath running components.

    raise RuntimeError('START_TIMEOUT_CONTROLLER_RETAINED_INSPECT_LOG:' + str(log_path))



def ingress_preflight(app, plan, report):

    regular(IIS)

    check_file(IIS, 'App_Code/XnbyReferenceProxy.cs', plan['iisProxySHA256'])

    config = ET.fromstring((IIS / 'web.config').read_bytes())

    require(any(r.get('type') == 'XnbyReferenceProxy' for r in

                config.findall('./system.webServer/handlers/add')), 'EXISTING_ORIGINAL_IIS_HANDLER_REQUIRED')

    # The existing installer contains the verified certificate/SNI and site checks.

    ingress_relative = 'tools/install_original_server_ingress.py'

    ingress_pin = read(app / 'release-manifest.json')['controllerFiles'].get(ingress_relative)

    if ingress_pin is None:

        # R5 omitted this already-installed helper from its release manifest.

        # A SHA-pinned update plan may name the independently verified old file.

        ingress_pin = plan.get('existingIngressToolSHA256')

    require(isinstance(ingress_pin, str) and re.fullmatch('[0-9a-f]{64}', ingress_pin),

            'PINNED_EXISTING_INGRESS_TOOL_REQUIRED')

    check_file(app, ingress_relative, ingress_pin)

    sys.path.insert(0, str(app / 'tools'))

    import install_original_server_ingress as ingress

    address = ingress.preflight(app, IIS, report)

    require(ingress.tls_local(address, '/zhumadian/home')[0] == 200,

            'CURRENT_PUBLIC_HOME_REQUIRED')

    return ingress, address



def refresh_deployment_owner(app, row):

    path = regular(app, 'UserData/OriginalDeployment/active-deployment.private.json')

    require(path.is_file(), 'EXISTING_DEPLOYMENT_OWNER_REQUIRED')

    value = read(path)

    require(value.get('releaseId') == row['releaseId'], 'EXISTING_DEPLOYMENT_RELEASE_REQUIRED')

    value.update(controllerPID=row['controllerPID'], run=row['run'])

    write_json(path, value)



def preserve_previous_update(app, attempt, old_pin):

    path = regular(app, 'UserData/OriginalPublicUpdates/latest.json')

    if not path.exists():

        return False

    require(path.stat().st_size <= 64 * 1024, 'BOUNDED_PREVIOUS_UPDATE_RECEIPT_REQUIRED')

    previous = read(path)

    require(previous.get('newReleaseSHA256') == old_pin and previous.get('ready') is True

            and not previous.get('rolledBack'), 'EXACT_PREVIOUS_ACTIVE_UPDATE_REQUIRED')

    atomic(attempt / 'previous-latest.json', path.read_bytes())

    return True



def restore_previous_update(app, attempt, restored):

    path = regular(attempt, 'previous-latest.json')

    if not path.exists():

        return False

    require(path.stat().st_size <= 64 * 1024, 'BOUNDED_PREVIOUS_UPDATE_RECEIPT_REQUIRED')

    previous = read(path)

    require(previous.get('newReleaseSHA256') == sha(app / 'release-manifest.json')

            and previous.get('ready') is True and not previous.get('rolledBack'),

            'RESTORED_ACTIVE_RELEASE_RECEIPT_REQUIRED')

    previous.update(controllerPID=restored['controllerPID'], run=restored['run'],

                    publicAccepted=False, userNormalLoginPending=True)

    write_json(app / 'UserData/OriginalPublicUpdates/latest.json', previous)

    return True



def candidate_original_mapper_preflight(configuration):
    """Validate the same bounded config snapshot that is pinned before shutdown."""
    business = configuration['configuration']['business']
    require(isinstance(business, dict), 'MAPPER_CONFIGURATION_SHAPE_REQUIRED')
    def mapper_key(key):
        return isinstance(key, str) and re.fullmatch(
            r'mybatisplusmapperlocations(?:\[[0-9]+\])?',
            re.sub(r'[-_.]', '', key).lower()) is not None
    values = [value for key, value in business.items() if mapper_key(key)]
    values.extend(value for key, value in os.environ.items() if mapper_key(key))
    arguments = configuration.get('businessArguments', [])
    require(isinstance(arguments, list) and all(isinstance(a, str) for a in arguments),
            'MAPPER_BUSINESS_ARGUMENTS_SHAPE_REQUIRED')
    for argument in arguments:
        if argument.startswith(('-D', '--')):
            key, separator, value = argument[2:].partition('=')
            if mapper_key(key):
                require(separator == '=', 'EXPLICIT_MAPPER_ARGUMENT_VALUE_REQUIRED')
                values.append(value)
    require(not values or all(isinstance(v, str) and v in ('classpath*:/xml/**/*.xml', 'classpath*:xml/**/*Mapper.xml') for v in values),
            'EXPLICIT_MAPPER_LOCATIONS_REQUIRE_VALIDATION_BEFORE_SHUTDOWN')
    return {'passed': True, 'defaultWillApply': not values,
            'explicitOriginalPatternRetained': bool(values),
            'settingValuesOrCredentialsReturned': False}


def candidate_runtime_pool_preflight(app, bundle, plan):

    """Resolve the exact candidate's numeric policy before backup or shutdown."""

    import types

    release_path = regular(bundle, 'payload/release-manifest.json')

    release_raw = release_path.read_bytes()

    require(hashlib.sha256(release_raw).hexdigest() == plan['newReleaseSHA256'],

            'CANDIDATE_RELEASE_CHANGED_BEFORE_PREFLIGHT')

    candidate = json.loads(release_raw)

    descriptor = candidate.get(R27_POOL_FIELD)

    if descriptor is None:

        return None

    require(descriptor == R27_POOL_POLICY, 'EXACT_CANDIDATE_POOL_POLICY_REQUIRED')

    name = 'tools/original_server_release_parameters.py'

    source_root = bundle / 'payload' if name in plan['files'] else app

    source = check_file(source_root, name, candidate['controllerFiles'][name])

    source_raw = source.read_bytes()

    require(len(source_raw) <= 128 * 1024 and

            hashlib.sha256(source_raw).hexdigest() == candidate['controllerFiles'][name],

            'CANDIDATE_PARAMETERS_CHANGED_BEFORE_EXEC')

    private = regular(app, 'private/server-configuration.json')

    require(private.is_file() and private.stat().st_size <= 1024 * 1024,

            'BOUNDED_INSTALLED_CONFIGURATION_REQUIRED')

    raw = private.read_bytes()

    configuration = json.loads(raw)

    require(configuration.get('schema') == 'zhumadian.original.server.configuration.v1',

            'INSTALLED_CONFIGURATION_SCHEMA_REQUIRED')

    mapper_input = (candidate_original_mapper_preflight(configuration)
                    if original_mapper_defaults_declared(candidate) else None)

    module = types.ModuleType('owned_candidate_numeric_parameters')

    module.__file__ = str(source)

    exec(compile(source_raw, str(source), 'exec'), module.__dict__)

    budget = module.connection_pool_budget(configuration)

    require(budget['policy'] == descriptor, 'CANDIDATE_BUDGET_POLICY_MISMATCH')

    return {'budget': budget, 'configurationSHA256': hashlib.sha256(raw).hexdigest(),

            'candidateParametersSHA256': candidate['controllerFiles'][name],
            'originalMapperPreflight': mapper_input}





def apply_update(app, bundle, pin):

    print('CHECK: validating sparse files and installed release; public service remains running', flush=True)

    plan, old_pin, changes = load_bundle(app, bundle, pin)

    candidate_pool = candidate_runtime_pool_preflight(app, bundle, plan)

    require(shutil.disk_usage(app).free >= 12 * 1024 ** 3, 'TWELVE_GIB_SERVER_FREE_REQUIRED')

    row = owned_ready(app, old_pin)

    identity = read(regular(app, 'UserData/OriginalServer/installation.json'))

    require(identity['releaseId'] == plan['releaseId'] and identity['databaseUUID'] == row['databaseUUID'],

            'EXISTING_DATA_IDENTITY_REQUIRED')

    deployment = read(regular(app, 'UserData/OriginalDeployment/active-deployment.private.json'))

    require(deployment['releaseId'] == plan['releaseId'], 'EXISTING_DEPLOYMENT_RECORD_REQUIRED')

    ingress, address = ingress_preflight(app, plan, {})

    attempt = regular(app, 'UserData/OriginalPublicUpdates/' + uuid.uuid4().hex)

    backup_code(app, attempt, changes)

    preserve_previous_update(app, attempt, old_pin)

    report = {'schema': 'zhumadian.public-test-update.receipt.v1', 'updateId': plan['updateId'],

        'oldReleaseSHA256': old_pin, 'newReleaseSHA256': plan['newReleaseSHA256'],

        'callbackOverlay': plan['callbackOverlay'], 'callbackOverlaySHA256': plan['callbackOverlaySHA256'],

        'databaseUUID': identity['databaseUUID'], 'attempt': str(attempt), 'codeApplied': False,

        'iisChanged': False, 'databaseOrUploadsCopied': False, 'publicAccepted': False,

        'startedAt': datetime.datetime.now().astimezone().isoformat()}

    write_json(attempt / 'result.json', report)

    write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)

    try:

        if candidate_pool is not None:

            require(sha(regular(app, 'private/server-configuration.json')) == candidate_pool['configurationSHA256'],

                    'CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP')

        normal_stop(app, old_pin, row)

        report['oldNormalShutdownCompleted'] = True

        # Revalidate after shutdown to detect changes between preflight and mutation.

        with server_lock(app):

            load_bundle(app, bundle, pin)

            report['mutationStarted'] = True

            replace_code(app, bundle, changes)

        report['codeApplied'] = True

        report['iisChanged'] = static_performance_declared(read(app / 'release-manifest.json'))

        new = launch(app, plan['newReleaseSHA256'], attempt,

                     (plan['callbackOverlay'], plan['callbackOverlaySHA256']))

        health(app, new)

        for path in ['/zhumadian/home', '/zhumadian/h5/',

                     '/zhumadian/api/jnpf/oauth/getLoginConfig']:

            status, body = ingress.tls_local(address, path)

            require(status == 200, 'SERVER_TLS_GATEWAY_CHECK_FAILED')

            if path.endswith('getLoginConfig'):

                require(json.loads(body).get('code') == 200, 'SERVER_TLS_LOGIN_CONFIG_FAILED')

        status, body = ingress.tls_local(address,

            '/zhumadian/api/serv/checkInventory/page?current=1&size=1')

        require(status == 200 and json.loads(body).get('code') == 600,

                'SERVER_TLS_MISSING_AUTH_CHECK_FAILED')

        require(read(app / 'UserData/OriginalServer/installation.json') == identity,

                'INSTALLED_DATA_IDENTITY_CHANGED')

        refresh_deployment_owner(app, new)

        report.update(ready=True, controllerPID=new['controllerPID'], run=new['run'],

            serverLocalTLSVerified=True, externalPublicVerificationPending=True,

            userNormalLoginPending=True)

        write_json(app / 'UserData/OriginalPublicUpdates/latest.json', report)

        write_json(app / 'UserData/OriginalPublicUpdates/pending.json', dict(report, completed=True))

        print(plan['updateId'] + '_READY: server TLS passed; external verification and normal user login remain pending', flush=True)

    except BaseException as error:

        report.update(failureType=type(error).__name__, failure=str(error), ready=False)

        # Leave a running/unknown startup untouched. Rollback requires a proven normal stop.

        report['manualRecoveryRequired'] = bool(report.get('oldNormalShutdownCompleted') or

                                                report.get('mutationStarted'))

        print('UPDATE_STOPPED: inspect ' + str(attempt / 'result.json') + '; do not repeat the CMD', flush=True)

        raise

    finally:

        report['endedAt'] = datetime.datetime.now().astimezone().isoformat()

        write_json(attempt / 'result.json', report)

        write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)



def start_installed(app):

    latest = read(regular(app, 'UserData/OriginalPublicUpdates/latest.json'))

    require(sha(app / 'release-manifest.json') == latest['newReleaseSHA256'], 'LATEST_RELEASE_PIN_REQUIRED')

    current = read(app / 'UserData/OriginalServer/current-run.json')

    if process_owned(current.get('controllerPID'), app, latest['newReleaseSHA256']):

        health(app, owned_ready(app, latest['newReleaseSHA256']))

        print('R5_ALREADY_RUNNING: no duplicate controller started', flush=True)

        return

    require((Path(current['run']) / 'receipt.json').is_file(), 'PRIOR_RUN_RECEIPT_REQUIRED')

    previous = read(Path(current['run']) / 'receipt.json')

    require(previous.get('normalOwnedShutdown') and previous.get('allOwnedChildrenExited'),

            'PRIOR_NORMAL_SHUTDOWN_REQUIRED')

    row = launch(app, latest['newReleaseSHA256'], Path(latest['attempt']),

                 (latest['callbackOverlay'], latest['callbackOverlaySHA256']))

    health(app, row); refresh_deployment_owner(app, row)

    print('R5_RESTART_READY', flush=True)



def rollback_latest(app):

    latest = read(regular(app, 'UserData/OriginalPublicUpdates/latest.json'))

    require(not latest.get('directoryMigration'), 'USE_DIRECTORY_MIGRATION_COORDINATOR_FOR_LAYOUT_ROLLBACK')

    attempt = Path(latest['attempt']).absolute()

    require(attempt.parent == app / 'UserData/OriginalPublicUpdates', 'OWNED_UPDATE_BACKUP_REQUIRED')

    regular(attempt)

    require(not latest.get('rolledBack'), 'ROLLBACK_ALREADY_COMPLETED')

    row = owned_ready(app, latest['newReleaseSHA256'])

    changes = read(attempt / 'changes.json')

    # Check backup hashes and post-update file pins before requesting downtime.

    for name, change in changes.items():

        if change['after'] is not None:

            check_file(app, name, change['after'])

        else:

            require(not regular(app, name).exists(), 'REMOVED_PATH_RECREATED')

        if change['before'] is not None:

            check_file(attempt / 'before', name, change['before'])

    normal_stop(app, latest['newReleaseSHA256'], row)

    with server_lock(app):

        restore_code(app, attempt, changes)

    require(sha(app / 'release-manifest.json') == latest['oldReleaseSHA256'], 'RESTORED_RELEASE_PIN_REQUIRED')

    old = launch(app, latest['oldReleaseSHA256'], attempt)

    health(app, old, guarded=False); refresh_deployment_owner(app, old)

    latest.update(rolledBack=True, publicAccepted=False)

    write_json(attempt / 'rollback-result.json', latest)

    if not restore_previous_update(app, attempt, old):

        write_json(app / 'UserData/OriginalPublicUpdates/latest.json', latest)

    print('OLD_CODE_RESTORED: installed database and uploads retained', flush=True)



def recover_pending(app):

    """Recover a failed update only when its controller is ready or fully gone.



    An unknown or still-starting controller is deliberately left alone.

    """

    report = read(regular(app, 'UserData/OriginalPublicUpdates/pending.json'))

    require(report.get('failureType') and not report.get('ready') and

            not report.get('recovered'), 'FAILED_UPDATE_REQUIRED')

    attempt = Path(report['attempt']).absolute()

    require(attempt.parent == app / 'UserData/OriginalPublicUpdates', 'OWNED_UPDATE_BACKUP_REQUIRED')

    regular(attempt)

    old_pin = report['oldReleaseSHA256']; new_pin = report['newReleaseSHA256']

    current = read(app / 'UserData/OriginalServer/current-run.json')

    if process_owned(current.get('controllerPID'), app, new_pin):

        normal_stop(app, new_pin, owned_ready(app, new_pin))

    elif process_owned(current.get('controllerPID'), app, old_pin):

        require(not report.get('mutationStarted'), 'OLD_CONTROLLER_RUNNING_DURING_MUTATION')

        print('OLD_VERSION_STILL_RUNNING: no code recovery necessary', flush=True)

        return

    state_path = attempt / 'launch-state.json'

    if state_path.exists():

        launch_state = read(state_path)

        require(not process_owned(launch_state.get('controllerPID'), app,

                launch_state['releaseSHA256']), 'STARTING_CONTROLLER_RETAINED_NO_RECOVERY')

    # No database owner may remain, even after a controller-level startup failure.

    if report.get('mutationStarted') and state_path.exists():

        launch_state = read(state_path)

        receipts = []

        for receipt_path in (app / 'UserData/OriginalServer/runs').glob('j*/receipt.json'):

            regular(receipt_path)

            value = read(receipt_path)

            if value.get('controllerPID') == launch_state['controllerPID']:

                receipts.append(value)

        require(len(receipts) == 1 and receipts[0].get('allOwnedChildrenExited') is True

                and receipts[0].get('exitCodesBeforeJobClose', {}).get('mysql') == 0,

                'STARTUP_NORMAL_DATABASE_SHUTDOWN_RECEIPT_REQUIRED')

    with server_lock(app):

        require(sha(app / 'release-manifest.json') in (old_pin, new_pin), 'RECOVERY_RELEASE_DRIFT')

        if report.get('mutationStarted'):

            restore_code(app, attempt, read(attempt / 'changes.json'))

    row = launch(app, old_pin, attempt)

    health(app, row, guarded=False); refresh_deployment_owner(app, row)

    report.update(recovered=True, manualRecoveryRequired=False)

    restore_previous_update(app, attempt, row)

    write_json(attempt / 'recovery-result.json', report)

    write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)

    print('FAILED_UPDATE_RECOVERED_TO_OLD_CODE: database and uploads retained', flush=True)



def main():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--application', type=Path, required=True)

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument('--apply', type=Path); mode.add_argument('--start', action='store_true')

    mode.add_argument('--rollback-latest', action='store_true')

    mode.add_argument('--recover-pending', action='store_true')

    parser.add_argument('--manifest-sha256')

    args = parser.parse_args(); app = args.application.absolute()

    require(os.name == 'nt' and app == TARGET and app.resolve(strict=True) == app,

            'EXACT_EXISTING_SERVER_INSTALLATION_REQUIRED')

    import msvcrt

    lock_path = regular(app, 'UserData/OriginalPublicUpdates/update.lock')

    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open('a+b') as lock:

        lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)

        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)

        try:

            if args.apply:

                apply_update(app, args.apply.absolute(), args.manifest_sha256)

            elif args.start:

                start_installed(app)

            elif args.recover_pending:

                recover_pending(app)

            else:

                rollback_latest(app)

        finally:

            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)



if __name__ == '__main__':

    main()

