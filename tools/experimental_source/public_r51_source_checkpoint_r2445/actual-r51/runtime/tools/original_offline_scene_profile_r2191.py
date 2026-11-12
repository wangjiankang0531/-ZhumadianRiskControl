"""Exact complete scene successor graph over retained R49 lifecycle.

No service, private configuration, assets or business rows are changed here.
An externally pinned contract closes both complete graphs and every delta.
"""
from pathlib import Path, PurePosixPath
import copy, hashlib, json, re

FIELD = 'originalClientOfflineSceneIntegration'
PROFILE = 'tools/original_offline_scene_contract_r2193.json'
HELPER = 'tools/original_offline_scene_profile_r2191.py'
RESOURCE = 'tools/original_offline_scene_resource_preflight_r2192.py'
BASE = 'tools/original_public_test_base_r49.py'
UPDATER = 'tools/original_public_test_update.py'
IIS = ('iis/App_Code/XnbyReferenceProxy.cs', 'deploy/iis_original/App_Code/XnbyReferenceProxy.cs')
BASE_RELEASE_SHA = 'd2918cf14933b7a903368a0f88e6b2075116081cdbb847ca435b67bd01c8ea88'
REVISION = '20261112-public-scene-same-window-r51'
FORBIDDEN = ('private/', 'UserData/', 'seed/', 'Assets/', 'runtime/')


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf8')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    path = Path(path)
    need(path.is_file() and path.stat().st_size <= 8 * 1024**2, 'SCENE_FULL_BOUNDED_JSON_REQUIRED')
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'SCENE_FULL_DUPLICATE_JSON_KEY')
            result[k] = v
        return result
    def bad(_):
        raise ValueError('SCENE_FULL_NONFINITE_JSON')
    return json.loads(path.read_bytes(), object_pairs_hook=pairs, parse_constant=bad)


def path_name(name):
    need(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_./#$-]+', name), 'SCENE_FULL_RELATIVE_PATH_REQUIRED')
    p = PurePosixPath(name)
    need(not p.is_absolute() and p.as_posix() == name and '..' not in p.parts, 'SCENE_FULL_NORMAL_PATH_REQUIRED')
    return name


class Profile:
    def __init__(self, core, root, contract_sha):
        self.m = core
        self.root = core.regular(root)
        self.c = read(core.check_file(root, PROFILE, contract_sha))
        c = self.c
        need(set(c) == {'schema', 'baseReleaseSHA256', 'baseRelease', 'basePayload',
                        'candidateRelease', 'candidatePayload', 'descriptor', 'retainedUpdaterSHA256'},
             'SCENE_FULL_EXACT_CONTRACT_KEYS_REQUIRED')
        need(c['schema'] == 'xnby.client-offline-scene-profile.r2193.v1' and c['baseReleaseSHA256'] == BASE_RELEASE_SHA,
             'SCENE_FULL_EXACT_R49_BASE_REQUIRED')
        need(hashlib.sha256(encoded(c['baseRelease'])).hexdigest() == BASE_RELEASE_SHA,
             'SCENE_FULL_BASE_RELEASE_CONTENT_REQUIRED')
        need(hashlib.sha256(encoded(c['basePayload'])).hexdigest() == c['baseRelease']['payloadManifestSHA256'],
             'SCENE_FULL_BASE_PAYLOAD_CONTENT_REQUIRED')
        need(len(c['basePayload']['files']) == 16150, 'SCENE_FULL_COMPLETE_R49_PAYLOAD_REQUIRED')
        need(c['baseRelease']['releaseId'] == c['candidateRelease']['releaseId'] == c['candidatePayload']['releaseId'],
             'SCENE_FULL_SAME_INSTALLATION_ID_REQUIRED')
        need(c['retainedUpdaterSHA256'] == c['baseRelease']['controllerFiles'][UPDATER],
             'SCENE_FULL_RETAINED_R49_UPDATER_REQUIRED')
        core.check_file(root, BASE, c['retainedUpdaterSHA256'])
        need(FIELD not in c['baseRelease'] and FIELD not in c['candidateRelease'], 'SCENE_FULL_FRESH_PROFILE_REQUIRED')
        old = c['basePayload']['files']; new = c['candidatePayload']['files']
        for n, row in old.items():
            path_name(n)
            if n.startswith(FORBIDDEN):
                need(new.get(n) == row, 'SCENE_FULL_PRIVATE_DATA_AND_RUNTIME_RETAINED')
            elif n not in new:
                need(n.startswith(('frontend/security_pc/', 'frontend/emergency_pc/')), 'SCENE_FULL_ONLY_RETIRED_FRONTEND_REMOVALS')
        for n, row in new.items():
            path_name(n)
            need(set(row) == {'bytes', 'sha256'} and type(row['bytes']) is int and row['bytes'] >= 0
                 and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'SCENE_FULL_FILE_PIN_REQUIRED')
            if old.get(n) != row:
                need(not n.startswith(FORBIDDEN), 'SCENE_FULL_CODE_ONLY_DELTA_REQUIRED')
        for n, h in c['candidateRelease']['controllerFiles'].items():
            if n in new:
                need(new[n]['sha256'] == h, 'SCENE_FULL_CONTROLLER_PAYLOAD_PIN_MISMATCH')
            else:
                need(c['baseRelease']['controllerFiles'].get(n) == h and n not in old,
                     'SCENE_FULL_ONLY_EXACT_RETAINED_UNTRACKED_CONTROLLER_ALLOWED')
        static = c['candidateRelease']['staticInitialLoadPerformance']['files']
        for n in IIS:
            need(static.get(n) == new.get(n) and static[n]['sha256'] == c['candidateRelease']['controllerFiles'].get(n),
                 'SCENE_FULL_IIS_STATIC_METADATA_MUST_MATCH_ACTUAL_SOURCE')
        need(c['descriptor'] == {'revision': 'original-server-with-client-offline-gis-v1',
             'rangeBytes': 67108864, 'originalIISResponseLimitBytes': 134217728,
             'privateSpatialSettingsArePrerequisiteNotPayload': True,
             'resourcePreflightBeforeAnyShutdown': True,
             'clientGISExcludedFromServerLifecycle': True,
             'sourceAssetsAndOriginalBusinessRowsNotIncluded': True, 'callbackClosureBeforeAnyShutdown': True}, 'SCENE_FULL_EXACT_DESCRIPTOR_REQUIRED')
        need('fineSource'not in c['candidateRelease']and c['candidateRelease']['spatialSync']['schema']=='xnby.original.offline-gis-spatial-sync.v1','OFFLINE_SCENE_EXACT_SERVER_ROLE_REQUIRED')
        self.component = {}
        for n in (PROFILE, HELPER, RESOURCE, BASE, UPDATER):
            need(n == UPDATER or n not in new, 'SCENE_FULL_FRESH_COMPONENT_PATH_REQUIRED')
            f = core.regular(root, n)
            need(f.is_file(), 'SCENE_FULL_COMPONENT_REQUIRED')
            self.component[n] = {'bytes': f.stat().st_size, 'sha256': digest(f)}

    def payload(self):
        value = copy.deepcopy(self.c['candidatePayload'])
        value['files'].update(copy.deepcopy(self.component))
        return value

    def release(self, payload_sha):
        need(payload_sha == hashlib.sha256(encoded(self.payload())).hexdigest(), 'SCENE_FULL_COMPOSED_PAYLOAD_SHA_REQUIRED')
        value = copy.deepcopy(self.c['candidateRelease'])
        value['controllerFiles'].update({n: r['sha256'] for n, r in self.component.items()})
        value['payloadManifestSHA256'] = payload_sha
        value['publicTestRevision'] = REVISION
        value[FIELD] = copy.deepcopy(self.c['descriptor'])
        return value

    def declared(self, release):
        if FIELD not in release:
            return False
        need(encoded(release) == encoded(self.release(release.get('payloadManifestSHA256'))), 'SCENE_FULL_EXACT_RELEASE_REQUIRED')
        return True

    def expected_plan(self, target, port):
        payload = self.payload(); pr = encoded(payload)
        release = self.release(hashlib.sha256(pr).hexdigest())
        old = self.c['basePayload']['files']; new = payload['files']
        files = {n: {'bytes': r['bytes'], 'SHA256': r['sha256']} for n, r in new.items() if old.get(n) != r}
        for n, raw in [('payload-manifest.json', pr), ('release-manifest.json', encoded(release))]:
            files[n] = {'bytes': len(raw), 'SHA256': hashlib.sha256(raw).hexdigest()}
        need(len(files) <= 1000 and sum(r['bytes'] for r in files.values()) <= 64 * 1024**2, 'SCENE_FULL_BOUNDED_SPARSE_CODE_REQUIRED')
        return {'schema': 'zhumadian.public-test-update.v1', 'updateId': REVISION,
                'targetApplication': Path(target).absolute().as_posix(), 'gatewayPort': port,
                'databaseUploadsCredentialsGISOrDependenciesIncluded': False, 'releaseId': release['releaseId'],
                'baseReleaseSHA256': BASE_RELEASE_SHA, 'basePayloadManifestSHA256': self.c['baseRelease']['payloadManifestSHA256'],
                'newReleaseSHA256': hashlib.sha256(encoded(release)).hexdigest(),
                'newPayloadManifestSHA256': hashlib.sha256(pr).hexdigest(), 'files': files,
                'removedFrontendFiles': {n: {'bytes': r['bytes'], 'SHA256': r['sha256']} for n, r in old.items() if n not in new},
                'callbackOverlay': 'payload/callback-overlay/20261026-password-identity/manifest.json',
                'callbackOverlaySHA256': release['missingAuthOverlayManifestSHA256'],
                'iisProxySHA256': old[IIS[0]]['sha256']}

    def verify_callback_closure(self, app, release, candidate_payload):
        import importlib.util
        m = self.m
        name = 'tools/original_callback_overlay.py'
        expected = self.c['baseRelease']['controllerFiles'][name]
        need(release['controllerFiles'].get(name) == expected, 'OFFLINE_SCENE_ORIGINAL_CALLBACK_LOADER_RETAINED')
        source = m.check_file(app, name, expected)
        spec = importlib.util.spec_from_file_location('offline_original_callback_closure', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        relative = 'payload/callback-overlay/20261026-password-identity/manifest.json'
        pin = self.c['baseRelease']['missingAuthOverlayManifestSHA256']
        need(release.get('missingAuthOverlayManifestSHA256') == pin, 'OFFLINE_SCENE_ORIGINAL_AUTH_OVERLAY_RETAINED')
        result = module.load_callback_overlay(app, Path(app)/relative, pin)
        manifest = read(Path(app)/relative)
        for path, baseline_pin in manifest['baselines'].items():
            need(candidate_payload['files'].get(path, {}).get('sha256') == baseline_pin, 'OFFLINE_SCENE_CALLBACK_BASELINE_RETAINED')
        for path, row in result['filePins'].items():
            full = str(Path(relative).parent / path).replace(chr(92), '/')
            recorded = candidate_payload['files'].get(full)
            need(recorded is None or recorded == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'OFFLINE_SCENE_CALLBACK_MEMBER_PIN_CONSISTENT')
        return {'passed': True, 'membersVerified': len(result['filePins']), 'baselinesVerified': len(manifest['baselines']), 'originalLoaderExecuted': True}

    def verify_original_runtime_paths(self, app):
        import importlib.util
        name = 'tools/original_server_release_parameters.py'
        pin = self.c['baseRelease']['controllerFiles'][name]
        source = self.m.check_file(app, name, pin)
        spec = importlib.util.spec_from_file_location('offline_original_runtime_path_guard', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = Path(app)
        paths = [module.runtime_temporary_path(app, app/'UserData/TianjinOriginalPlatform/runs/j9999', 'platform'),
                 module.runtime_temporary_path(app, app/'UserData/OriginalServer/runs/j9999/b', 'business')]
        need(all(len(str(p)) <= 80 for p in paths), 'SHORT_WINDOWS_RUNTIME_PATH_REQUIRED_BEFORE_ANY_START')
        return {'passed': True, 'maximumTemporaryPathChars': max(map(lambda p: len(str(p)), paths)), 'originalParameterSourceExecuted': True}

    def load_bundle(self, app, bundle, manifest_sha, *, expected_target, expected_port):
        m = self.m; app = m.regular(app); bundle = m.regular(bundle)
        need(app == Path(expected_target).absolute(), 'SCENE_FULL_EXACT_APPLICATION_REQUIRED')
        need(type(expected_port) is int and 1 <= expected_port <= 65535, 'SCENE_FULL_EXACT_PORT_REQUIRED')
        plan = read(m.check_file(bundle, 'update-manifest.json', manifest_sha))
        need(encoded(plan) == encoded(self.expected_plan(expected_target, expected_port)), 'SCENE_FULL_EXACT_DELTA_REQUIRED')
        m.check_file(app, 'release-manifest.json', BASE_RELEASE_SHA)
        need(read(app/'release-manifest.json') == self.c['baseRelease'], 'SCENE_FULL_INSTALLED_BASE_RELEASE_REQUIRED')
        old = read(m.check_file(app, 'payload-manifest.json', plan['basePayloadManifestSHA256']))
        need(old == self.c['basePayload'], 'SCENE_FULL_INSTALLED_BASE_PAYLOAD_REQUIRED')
        release = read(m.check_file(bundle/'payload', 'release-manifest.json', plan['newReleaseSHA256']))
        payload = read(m.check_file(bundle/'payload', 'payload-manifest.json', plan['newPayloadManifestSHA256']))
        need(self.declared(release) and encoded(payload) == encoded(self.payload()), 'SCENE_FULL_EXACT_NEW_GRAPH_REQUIRED')
        changes = {}
        for n in {*plan['files'], *plan['removedFrontendFiles']}:
            before = old['files'].get(n, {}).get('sha256')
            if n == 'release-manifest.json':
                before = BASE_RELEASE_SHA
            elif n == 'payload-manifest.json':
                before = plan['basePayloadManifestSHA256']
            target = m.regular(app, n)
            if before is None:
                need(not target.exists(), 'SCENE_FULL_UNKNOWN_EXISTING_PATH:' + n)
            else:
                m.check_file(app, n, before)
            after = plan['files'].get(n)
            if after:
                m.check_file(bundle/'payload', n, after['SHA256'], after['bytes'])
            changes[n] = {'before': before, 'after': after['SHA256'] if after else None}
        for n, row in payload['files'].items():
            if n.startswith(('private/', 'UserData/', 'seed/', 'Assets/')):
                need(old['files'].get(n) == row, 'SCENE_FULL_PROTECTED_METADATA_RETAINED')
                continue
            m.check_file(bundle/'payload' if n in plan['files'] else app, n, row['sha256'], row['bytes'])
        for n, h in release['controllerFiles'].items():
            m.check_file(bundle/'payload' if n in plan['files'] else app, n, h)
        descriptor = release['spatialSync']
        need(descriptor['settingsPath'].startswith('private/'), 'SCENE_FULL_PRIVATE_PREREQUISITE_PATH_REQUIRED')
        m.check_file(app, descriptor['settingsPath'], descriptor['settingsSHA256'])
        self.verify_callback_closure(app, release, payload)
        self.verify_original_runtime_paths(app)
        return plan, BASE_RELEASE_SHA, changes


def install_selected_lifecycle(m, legacy, profile):
    """Keep six-component R49 separate; bind complete-profile runtime exactly."""
    import ctypes
    from ctypes import wintypes
    import time
    previous_pool = m.pool_control_pins
    previous_stop = m.normal_stop
    def selected(release):
        need(profile.declared(release), 'SCENE_FULL_EXACT_LIFECYCLE_RELEASE_REQUIRED')
    def controller_pin(release):
        if FIELD not in release:
            return legacy.controller_pin_for(release)
        selected(release)
        row = profile.c['candidatePayload']['files'][m.R23_CONTROLLER]
        need(release['controllerFiles'][m.R23_CONTROLLER] == row['sha256'],
             'SCENE_FULL_EXACT_CONTROLLER_PIN_REQUIRED')
        return row['sha256']
    def pool_pins(release):
        if FIELD not in release:
            return legacy.pool_control_pins(release)
        selected(release)
        pins = previous_pool(release)
        # Keep the existing pool family and its exact full-graph source rows.
        result = {}
        for name in pins:
            row = profile.c['candidatePayload']['files'][name]
            need(release['controllerFiles'][name] == row['sha256'],
                 'SCENE_FULL_EXACT_POOL_SOURCE_REQUIRED')
            result[name] = copy.deepcopy(row)
        return result
    def normal_stop(app, pin, row):
        release = read(m.regular(app, 'release-manifest.json'))
        if FIELD not in release:
            return previous_stop(app, pin, row)
        selected(release)
        m.check_file(app, 'release-manifest.json', pin)
        m.check_file(app, m.R23_CONTROLLER, controller_pin(release))
        need(row.get('ready') is True and row.get('releaseId') == release['releaseId'],
             'SCENE_FULL_READY_OWNER_REQUIRED')
        run = m.regular(app, Path(row['run']).relative_to(app).as_posix())
        need(run.parent == app/'UserData/OriginalServer/runs' and
             re.fullmatch(r'j[1-9][0-9]{0,3}', run.name), 'SCENE_FULL_EXACT_OWN_RUN_REQUIRED')
        pid = row.get('controllerPID')
        need(type(pid) is int and pid > 0 and m.process_owned(pid, app, pin),
             'SCENE_FULL_CONTROLLER_OWNERSHIP_REQUIRED')
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.CloseHandle.argtypes = [wintypes.HANDLE]; k.CloseHandle.restype = wintypes.BOOL
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetExitCodeProcess.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        handle = k.OpenProcess(0x1000 | 0x100000, False, pid)
        need(handle, 'SCENE_FULL_REAL_CONTROLLER_HANDLE_REQUIRED')
        try:
            image = ctypes.create_unicode_buffer(32768); length = wintypes.DWORD(len(image))
            need(k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length)) and
                 Path(image.value).absolute() == app/'runtime/python/python.exe',
                 'SCENE_FULL_HANDLE_IMAGE_REQUIRED')
            # Validate the live command after holding the handle and recheck that
            # this same kernel object has not exited before writing its stop file.
            need(m.process_owned(pid, app, pin) and k.WaitForSingleObject(handle, 0) == 258,
                 'SCENE_FULL_CONTROLLER_CHANGED_BEFORE_STOP')
            m.atomic(run/'stop-requested.txt', b'stop\n')
            while True:
                state = k.WaitForSingleObject(handle, 15000)
                need(state in (0, 258), 'SCENE_FULL_CONTROLLER_HANDLE_STATE_UNKNOWN')
                if state == 0:
                    break
                print('SAME_COMPLETE_CONTROLLER_HANDLE_LIVE_NORMAL_DRAIN_NO_FORCE', flush=True)
            exit_code = wintypes.DWORD()
            need(k.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value == 0,
                 'SCENE_FULL_CONTROLLER_NORMAL_EXIT_REQUIRED')
            final = read(m.regular(run, 'receipt.json'))
            for key in ['controllerPID', 'run', 'ownerId', 'releaseId', 'startedAt', 'children']:
                need(key in row and final.get(key) == row[key],
                     'SCENE_FULL_EXACT_READY_RECEIPT_BINDING_REQUIRED:'+key)
            codes = final.get('exitCodesBeforeJobClose', {})
            need(final.get('normalOwnedShutdown') is True and final.get('allOwnedChildrenExited') is True
                 and set(codes) == {'store','mysql','redis','platform','business','gateway','spatial-sync'}
                 and all(type(v) is int and v == 0 for v in codes.values())
                 and not final.get('forcedJobClosureComponents') and not final.get('jobAssignmentFailureComponents')
                 and not final.get('shutdownPendingComponents'), 'SCENE_FULL_SEVEN_NORMAL_EXITS_REQUIRED')
            spatial = final.get('spatialSyncShutdown', {})
            need(spatial.get('actualWorkerHandleTerminal') is True and spatial.get('workerExitCode') == 0
                 and spatial.get('controllerExitCode') == 0 and spatial.get('forceTerminationUsed') is False
                 and spatial.get('clientOfflineGIS') is True,
                 'SCENE_FULL_SPATIAL_HANDLES_AND_NO_SERVER_GIS_REQUIRED')
            return final
        finally:
            need(k.CloseHandle(handle), 'SCENE_FULL_CONTROLLER_HANDLE_CLOSE_FAILED')
    m.controller_pin_for = controller_pin
    m.pool_control_pins = pool_pins
    m.normal_stop = normal_stop
