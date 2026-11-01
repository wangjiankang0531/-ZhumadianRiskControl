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
R27_POOL_POLICY={'revision': 'pool-family-budget-v1', 'mysqlMinimum': 24, 'mysqlMaximum': 256, 'reservedConnections': 12, 'maximumSinglePool': 128}
R27_POOL_PINS={'tools/serve_original_server_release.py': {'bytes': 27013, 'sha256': '6c16afcf99aba74e74ce6d05c55e9255871134594f91c96318f901ede61f4374'}, 'tools/original_server_release_parameters.py': {'bytes': 15775, 'sha256': 'f849b0ed52e281d7568831ec8a2097b882a64887b8e6cf7da2ec46adfa196dc6'}}
R27_POOL_WORKFLOW_CONTRACT={'revision': 'original-task-short-temp-and-pool-budget-v1', 'taskController': {'path': 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class', 'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}, 'parameterAdapter': {'path': 'tools/original_server_release_parameters.py', 'bytes': 15775, 'sha256': 'f849b0ed52e281d7568831ec8a2097b882a64887b8e6cf7da2ec46adfa196dc6'}}

def runtime_pool_declared(release):
    controls=release['controllerFiles']
    if R27_POOL_FIELD not in release:
        require(controls.get(R23_CONTROLLER)!=R27_POOL_PINS[R23_CONTROLLER]['sha256']
                and controls.get(R24_PARAMETER)!=R27_POOL_PINS[R24_PARAMETER]['sha256'], 'EXPLICIT_POOL_POLICY_REQUIRED')
        return False
    require(release[R27_POOL_FIELD]==R27_POOL_POLICY,'EXACT_POOL_POLICY_REQUIRED')
    require(all(controls.get(n)==p['sha256']for n,p in R27_POOL_PINS.items()),'EXACT_POOL_CONTROL_DECLARATIONS_REQUIRED')
    return True

def workflow_contract_for(release):
    return R27_POOL_WORKFLOW_CONTRACT if runtime_pool_declared(release)else R24_WORKFLOW_CONTRACT

def parameter_pin_for(release):
    return R27_POOL_PINS[R24_PARAMETER]if runtime_pool_declared(release)else R24_PARAMETER_PIN

def controller_pin_for(release):
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
    allowed=set(R27_POOL_PINS)|{'tools/original_public_test_update.py'}
    require({n:p for n,p in release['controllerFiles'].items()if n not in allowed}=={n:p for n,p in old['controllerFiles'].items()if n not in allowed},'POOL_OTHER_CONTROLLERS_MUST_BE_RETAINED')
    if fresh:require(set(R27_POOL_PINS).issubset(plan['files']),'COMPLETE_POOL_CONTROL_TRANSPORT_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    retained=lambda rows:{n:p for n,p in rows.items()if not n.startswith('frontend/emergency_pc/')}
    require(retained(previous['files'])==retained(payload['files']),'POOL_NON_EMERGENCY_PAYLOAD_MUST_BE_RETAINED')
    for n,pin in R27_POOL_PINS.items():
        if n in plan['files']:require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'EXACT_POOL_TRANSPORT_PIN_REQUIRED')
        check_file(bundle/'payload'if n in plan['files']else app,n,pin['sha256'],pin['bytes'])
    return True

def runtime_pool_ready(app,row):
    release=read(regular(app,'release-manifest.json'))
    if not runtime_pool_declared(release):return None
    require(workflow_ready(app,row)is not None,'POOL_RETAINED_WORKFLOW_RUNTIME_REQUIRED')
    for n,pin in R27_POOL_PINS.items():check_file(app,n,pin['sha256'],pin['bytes'])
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
        if not n.startswith('frontend/emergency_pc/') and n not in R26_TEAM_ROWS}
    require(retained(previous['files']) == retained(payload['files']), 'TEAM_UPDATE_OTHER_PAYLOAD_MUST_BE_RETAINED')
    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R26_TEAM_ROWS)
    if runtime_pool_declared(release):legal.update(R27_POOL_PINS)
    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))
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
    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))
    require(set(plan['files']) <= legal, 'MATERIAL_UPDATE_TRANSPORT_SCOPE_REFUSED')
    obsolete = {n for n in previous['files'] if n.startswith('frontend/emergency_pc/') and n not in payload['files']}
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
        if not n.startswith('frontend/emergency_pc/') and n not in R25_MATERIAL_ROWS and not (team and n in R26_TEAM_ROWS)}
    require(retained(previous['files']) == retained(payload['files']),
            'MATERIAL_UPDATE_OTHER_PAYLOAD_BYTES_MUST_BE_RETAINED')
    require(all(n.startswith('frontend/emergency_pc/') for n in plan.get('removedFrontendFiles', {})),
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

def risk_declared(release, payload):
    revision = release.get('riskUnitNativeSessionCandidate')
    classes = {n for n in R22_BACKEND_ROWS if n.endswith('.class')}
    if revision is None:
        require(not classes.intersection(payload['files']), 'EXPLICIT_RISK_NATIVE_SESSION_REVISION_REQUIRED')
        return False
    require(revision == R22_RISK_SESSION_REVISION, 'EXACT_RISK_NATIVE_SESSION_REVISION_REQUIRED')
    for name, pin in R22_BACKEND_ROWS.items():
        require(payload['files'].get(name) == pin, 'EXACT_RISK_NATIVE_SESSION_PAYLOAD_PIN_REQUIRED:' + name)
    return True


def risk_bundle_contract(app, bundle, plan, old, release, payload):
    """Validate the tested class set and preserve every existing initializer before downtime."""
    if not risk_declared(release, payload):
        require(not set(R22_BACKEND_ROWS).difference({n for n in R22_BACKEND_ROWS if n.endswith('spring.factories')}).intersection(plan['files']), 'RISK_CLASS_WITHOUT_DECLARATION_REFUSED')
        return None
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
    for name, pin in R22_BACKEND_ROWS.items():
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
    for name, pin in R22_BACKEND_ROWS.items():
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
        require(old[R23_ASYNC_FIELD] == R23_ASYNC_CONTRACT and set(controls) == set(prior),
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
    workflow_ready(app, row)
    material_ready(app, row)
    team_ready(app, row)
    runtime_pool_ready(app, row)

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

def apply_update(app, bundle, pin):
    print('CHECK: validating sparse files and installed release; public service remains running', flush=True)
    plan, old_pin, changes = load_bundle(app, bundle, pin)
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
        normal_stop(app, old_pin, row)
        report['oldNormalShutdownCompleted'] = True
        # Revalidate after shutdown to detect changes between preflight and mutation.
        with server_lock(app):
            load_bundle(app, bundle, pin)
            report['mutationStarted'] = True
            replace_code(app, bundle, changes)
        report['codeApplied'] = True
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
