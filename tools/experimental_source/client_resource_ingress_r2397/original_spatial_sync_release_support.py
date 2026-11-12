"""Optional pinned spatial service owned by the original application controller.

No import of the extension's tools namespace into the original controller. Its
interpreter and source are pinned; original account access remains in the worker.
"""
from pathlib import Path, PurePosixPath
import ctypes, hashlib, http.client, json, os, re, secrets, socket, subprocess, time
from ctypes import wintypes
from original_server_windows_job import OwnedWindowsJob
from original_scene_static_routes import preflight as scene_preflight, insert as insert_scene_routes
from original_scene_asset_policy import protect as protect_scene_assets, compose_model_authorization
PACKAGE_PIN = '6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3'

def need(value, code):
    if not value:
        raise ValueError(code)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def plain(path):
    path = Path(path).absolute()
    need('..' not in path.parts, 'SPATIAL_CANONICAL_PATH_REQUIRED')
    for q in [path, *path.parents]:
        if q.exists():
            need(not q.is_symlink() and (not q.is_junction()) and (not getattr(q.lstat(), 'st_file_attributes', 0) & 1024), 'SPATIAL_REPARSE_REFUSED')
    return path

def read(path, limit=131072):
    with plain(path).open('rb') as f:
        raw = f.read(limit + 1)
    need(len(raw) <= limit, 'SPATIAL_BOUNDED_INPUT_REQUIRED')
    return raw

def pairs(values):
    result = {}
    for k, v in values:
        need(k not in result, 'SPATIAL_DUPLICATE_JSON_FIELD')
        result[k] = v
    return result

def loads(raw):
    return json.loads(raw, object_pairs_hook=pairs)

def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf8')

def relative(value):
    need(isinstance(value, str) and re.fullmatch('[A-Za-z0-9_./-]+', value), 'SPATIAL_RELATIVE_PATH_REQUIRED')
    p = PurePosixPath(value)
    need(not p.is_absolute() and p.as_posix() == value and ('..' not in p.parts), 'SPATIAL_CANONICAL_RELATIVE_PATH_REQUIRED')
    return value

def write_new(path, raw):
    with plain(path).open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())

def process_birth(handle):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    times = [wintypes.FILETIME() for _ in range(4)]
    need(kernel.GetProcessTimes(wintypes.HANDLE(int(handle)), *[ctypes.byref(t) for t in times]), 'SPATIAL_PROCESS_BIRTH_UNVERIFIED')
    return str(times[0].dwHighDateTime << 32 | times[0].dwLowDateTime)

def parent_pid(pid):

    class Entry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD), ('pid', wintypes.DWORD), ('heap', ctypes.c_size_t), ('module', wintypes.DWORD), ('threads', wintypes.DWORD), ('parent', wintypes.DWORD), ('priority', wintypes.LONG), ('flags', wintypes.DWORD), ('exe', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ['Process32FirstW', 'Process32NextW']:
        getattr(kernel, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
        getattr(kernel, name).restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    need(handle not in (None, ctypes.c_void_p(-1).value), 'SPATIAL_PARENT_QUERY_FAILED')
    try:
        row = Entry()
        row.size = ctypes.sizeof(row)
        ok = kernel.Process32FirstW(handle, ctypes.byref(row))
        while ok:
            if row.pid == pid:
                return row.parent
            ok = kernel.Process32NextW(handle, ctypes.byref(row))
        raise ValueError('SPATIAL_WORKER_PARENT_NOT_FOUND')
    finally:
        kernel.CloseHandle(handle)

def checked_client_resources(value, local_sources):
    """Trusted project allowlist, optional and validated before any startup."""
    item = value.get('clientResources')
    if 'clientResources' not in value:
        return None
    need(isinstance(item, dict) and set(item) == {'schema', 'allowedInstallations'}
         and item['schema'] == 'xnby.client-resources.server-settings.v1', 'EXACT_CLIENT_RESOURCE_SETTINGS_REQUIRED')
    rows = item['allowedInstallations']
    need(isinstance(rows, list) and 1 <= len(rows) <= 16, 'BOUNDED_CLIENT_RESOURCE_INSTALLATIONS_REQUIRED')
    fields = ('installationIdentity', 'sourceRuntimeIdentity', 'sourceIndexIdentity')
    supported = {(r['sourceRuntimeIdentity'], r['sourceIndexIdentity']) for r in local_sources}
    seen = set()
    for row in rows:
        need(isinstance(row, dict) and set(row) == set(fields)
             and all(isinstance(row[k], str) and re.fullmatch('[a-f0-9]{64}', row[k]) for k in fields),
             'EXACT_CLIENT_RESOURCE_INSTALLATION_REQUIRED')
        key = tuple(row[k] for k in fields)
        need(key not in seen, 'DUPLICATE_CLIENT_RESOURCE_INSTALLATION_REFUSED')
        seen.add(key)
        need((row['sourceRuntimeIdentity'], row['sourceIndexIdentity']) in supported,
             'CLIENT_RESOURCE_SOURCE_NOT_DECLARED_FOR_PROJECT')
    return item


def preflight(application, release, *, gateway_port=None):
    need('fineSource' not in release, 'SERVER_ROLE_FORBIDS_GIS_PROCESS_DESCRIPTOR')
    descriptor = release.get('spatialSync')
    if descriptor is None:
        return None
    need(isinstance(descriptor, dict) and set(descriptor) == {'schema', 'codeRoot', 'packageManifestSHA256', 'settingsPath', 'settingsSHA256'} and (descriptor['schema'] == 'xnby.original.offline-gis-spatial-sync.v1'), 'EXACT_SPATIAL_DESCRIPTOR_REQUIRED')
    app = plain(application)
    code = plain(app / relative(descriptor['codeRoot']))
    settings = plain(app / relative(descriptor['settingsPath']))
    need(code.parent == app / 'extensions' and settings.parent == app / 'private', 'VERSION_PRIVATE_SPATIAL_CODE_AND_SETTINGS_REQUIRED')
    need(descriptor['packageManifestSHA256'] == PACKAGE_PIN, 'EXACT_QUALIFIED_SPATIAL_PACKAGE_REQUIRED')
    raw = read(code / 'package-manifest.json')
    need(digest(raw) == PACKAGE_PIN, 'SPATIAL_PACKAGE_MANIFEST_CHANGED')
    manifest = loads(raw)
    need(manifest.get('schema') == 'xnby.layer-sync.package.v1' and len(manifest.get('inputs', {})) == 44, 'SPATIAL_COMPLETE_PACKAGE_REQUIRED')
    for name, pin in manifest['inputs'].items():
        target = plain(code / relative(name))
        raw_source = read(target, 2 * 1048576)
        need(len(raw_source) == pin['bytes'] and digest(raw_source) == pin['sha256'], 'SPATIAL_SOURCE_CHANGED')
        need(release['controllerFiles'].get(target.relative_to(app).as_posix()) == pin['sha256'], 'SPATIAL_SOURCE_NOT_PINNED_TO_RELEASE')
    need(release['controllerFiles'].get((code / 'package-manifest.json').relative_to(app).as_posix()) == PACKAGE_PIN, 'SPATIAL_PACKAGE_NOT_PINNED_TO_RELEASE')
    settings_raw = read(settings, 32768)
    need(re.fullmatch('[0-9a-f]{64}', descriptor['settingsSHA256']) and digest(settings_raw) == descriptor['settingsSHA256'], 'SPATIAL_PRIVATE_SETTINGS_CHANGED')
    value = loads(settings_raw)
    need(isinstance(value, dict) and {'schema', 'dataRoot', 'projectFilesRoot', 'listenPort', 'access', 'localGIS'} <= set(value) and (set(value) <= {'schema', 'dataRoot', 'projectFilesRoot', 'listenPort', 'access', 'sceneReadOnlyAssets', 'developmentLoopbackOrigin', 'localGIS', 'sceneProjectsRoot', 'sceneModelCatalog', 'sceneModelCatalogSHA256', 'sceneModelsRoot', 'sceneModelsCatalog', 'sceneModelsCatalogSHA256', 'clientResources'}) and (value['schema'] == 'xnby.original.offline-gis-spatial-settings.v1'), 'EXACT_SPATIAL_PRIVATE_SETTINGS_REQUIRED')
    need(type(value['listenPort']) is int and (value['listenPort'] == 0 or 1024 <= value['listenPort'] <= 65535), 'SPATIAL_LOOPBACK_PORT_REQUIRED')
    need(all((isinstance(value[k], str) and Path(value[k]).is_absolute() for k in ['dataRoot', 'projectFilesRoot'])), 'ABSOLUTE_SPATIAL_DATA_ROOTS_REQUIRED')
    data = plain(value['dataRoot'])
    projects = plain(value['projectFilesRoot'])
    need(gateway_port is None or value['listenPort'] != gateway_port, 'SPATIAL_CANNOT_REUSE_GATEWAY_PORT')
    for data_path in [data, projects]:
        need(not data_path.is_relative_to(app) and (not app.is_relative_to(data_path)), 'PRIVATE_SPATIAL_DATA_OUTSIDE_APPLICATION_REQUIRED')
    need(not data.is_relative_to(projects) and (not projects.is_relative_to(data)), 'DISTINCT_SPATIAL_DATABASE_AND_PROJECTS_REQUIRED')
    acl = value['access']
    need(isinstance(acl, dict) and set(acl) == {'readers', 'writers', 'read_roles', 'write_roles', 'administrators'} and (type(acl['administrators']) is bool), 'EXACT_SPATIAL_PROJECT_ACL_REQUIRED')
    for key in ['readers', 'writers', 'read_roles', 'write_roles']:
        values = acl[key]
        need(isinstance(values, list) and len(values) <= 256 and all((isinstance(v, str) and 1 <= len(v) <= 256 and (v == v.strip()) and (not re.search('[\\x00-\\x1f\\x7f]', v)) for v in values)) and (len(set(values)) == len(values)), 'BOUNDED_EXPLICIT_SPATIAL_PROJECT_ACL_REQUIRED')
    need(type(value.get('developmentLoopbackOrigin', False)) is bool, 'EXPLICIT_DEVELOPMENT_ORIGIN_FLAG_REQUIRED')
    if value.get('developmentLoopbackOrigin', False):
        marker = app.parent / 'own-fixture.json'
        need(marker.is_file() and loads(read(marker, 16384)).get('ownedSyntheticFixtureOnly') is True and (type(gateway_port) is int) and (1024 <= gateway_port <= 65535), 'LOOPBACK_ORIGIN_ONLY_EXPLICIT_OWNED_FIXTURE_REQUIRED')
    scene_rows = scene_preflight(app, release.get('sceneStatic'), value.get('sceneReadOnlyAssets'))
    scene_library = None
    scene_keys = {'sceneProjectsRoot', 'sceneModelCatalog', 'sceneModelCatalogSHA256'}
    if scene_keys & set(value):
        need(scene_keys <= set(value), 'COMPLETE_SCENE_LIBRARY_SETTINGS_REQUIRED')
        need(all((isinstance(value[k], str) and Path(value[k]).is_absolute() for k in ['sceneProjectsRoot', 'sceneModelCatalog'])), 'ABSOLUTE_SCENE_LIBRARY_PATHS_REQUIRED')
        root = plain(value['sceneProjectsRoot'])
        catalog = plain(value['sceneModelCatalog'])
        need(not root.is_relative_to(app) and (not app.is_relative_to(root)), 'PRIVATE_SCENE_LIBRARY_OUTSIDE_APPLICATION_REQUIRED')
        for other in [data, projects, catalog]:
            need(not root.is_relative_to(other) and (not other.is_relative_to(root)), 'DISTINCT_SCENE_LIBRARY_ROOT_REQUIRED')
        need(isinstance(value['sceneModelCatalogSHA256'], str) and re.fullmatch('[0-9a-f]{64}', value['sceneModelCatalogSHA256']), 'PINNED_SCENE_LIBRARY_CATALOG_REQUIRED')
        catalog_raw = read(catalog, 262144)
        need(digest(catalog_raw) == value['sceneModelCatalogSHA256'], 'SCENE_LIBRARY_CATALOG_CHANGED')
        document = loads(catalog_raw)
        need(isinstance(document, dict) and document.get('schema') == 'xnby.scene-model-library.v1' and isinstance(document.get('models'), list) and (len(document['models']) <= 64), 'SCENE_LIBRARY_CATALOG_INVALID')
        ids = set()
        for row in document['models']:
            need(isinstance(row, dict) and isinstance(row.get('id'), str) and re.fullmatch('[-a-z0-9]{1,80}', row['id']) and (row['id'] not in ids) and isinstance(row.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'SCENE_LIBRARY_CATALOG_ROW_INVALID')
            ids.add(row['id'])
        need(scene_rows is not None and any((row['route'] == '/zhumadian/scene/model-library/catalog.json' and plain(row['file']) == catalog for row in scene_rows)), 'SCENE_LIBRARY_CATALOG_MUST_MATCH_DISPLAYED_PROJECT_MODELS')
        scene_library = {k: value[k] for k in scene_keys}
    model_library = None
    model_keys = {'sceneModelsRoot', 'sceneModelsCatalog', 'sceneModelsCatalogSHA256'}
    if model_keys & set(value):
        need(model_keys <= set(value), 'COMPLETE_MODEL_STORAGE_SETTINGS_REQUIRED')
        need(all((isinstance(value[k], str) and Path(value[k]).is_absolute() for k in ['sceneModelsRoot', 'sceneModelsCatalog'])), 'ABSOLUTE_MODEL_STORAGE_PATHS_REQUIRED')
        root = plain(value['sceneModelsRoot'])
        catalog = plain(value['sceneModelsCatalog'])
        need(not root.is_relative_to(app) and (not app.is_relative_to(root)), 'PRIVATE_MODEL_STORAGE_OUTSIDE_APPLICATION_REQUIRED')
        others = [data, projects, catalog]
        if scene_library is not None:
            others.append(plain(value['sceneProjectsRoot']))
        for other in others:
            need(not root.is_relative_to(other) and (not other.is_relative_to(root)), 'DISTINCT_MODEL_STORAGE_ROOT_REQUIRED')
        need(isinstance(value['sceneModelsCatalogSHA256'], str) and re.fullmatch('[0-9a-f]{64}', value['sceneModelsCatalogSHA256']), 'PINNED_MODEL_STORAGE_CATALOG_REQUIRED')
        catalog_raw = read(catalog, 262144)
        need(digest(catalog_raw) == value['sceneModelsCatalogSHA256'], 'MODEL_STORAGE_CATALOG_CHANGED')
        need(scene_rows is not None and any((row['route'] == '/zhumadian/scene/model-library/catalog.json' and plain(row['file']) == catalog for row in scene_rows)), 'MODEL_STORAGE_CATALOG_MUST_MATCH_DISPLAYED_PROJECT_MODELS')
        if scene_library is not None:
            need(catalog == plain(value['sceneModelCatalog']) and value['sceneModelsCatalogSHA256'] == value['sceneModelCatalogSHA256'], 'NAMED_SCENE_AND_LIVE_MODEL_CATALOG_MUST_MATCH')
        model_library = {k: value[k] for k in model_keys}
    local_gis = value['localGIS']
    need(isinstance(local_gis, dict) and set(local_gis) == {'schema', 'allowedSources'} and (local_gis['schema'] == 'xnby.local-gis.server-settings.v1'), 'EXACT_LOCAL_GIS_SETTINGS_REQUIRED')
    sources = local_gis['allowedSources']
    need(isinstance(sources, list) and 1 <= len(sources) <= 16, 'EXPLICIT_OFFLINE_SOURCES_REQUIRED')
    for source in sources:
        need(isinstance(source, dict) and set(source) == {'sourceRuntimeIdentity', 'sourceIndexIdentity', 'budgetMiB'} and all((isinstance(source[k], str) and re.fullmatch('[a-f0-9]{64}', source[k]) for k in ['sourceRuntimeIdentity', 'sourceIndexIdentity'])) and (type(source['budgetMiB']) is int) and (source['budgetMiB'] in (512, 1024, 2048)), 'OFFLINE_SOURCE_INVALID')
    resources = checked_client_resources(value, sources)
    need(scene_rows is not None and scene_library is not None and (model_library is not None), 'SERVER_MODELS_AND_SCENE_LIBRARIES_REQUIRED')
    return {'clientResources': resources, 'sceneModels': model_library, 'sceneLibrary': scene_library, 'localGIS': local_gis, 'sceneRows': scene_rows, 'application': app, 'code': code, 'settings': settings, 'settingsRaw': settings_raw, 'settingsSHA256': descriptor['settingsSHA256'], 'value': value}

class WorkerHandle:
    """Hold the real worker handle, validating birth and executable image."""

    def __init__(self, pid, birth, image):
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.k.OpenProcess.restype = wintypes.HANDLE
        self.k.CloseHandle.argtypes = [wintypes.HANDLE]
        self.k.CloseHandle.restype = wintypes.BOOL
        self.k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.k.WaitForSingleObject.restype = wintypes.DWORD
        self.k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.k.GetProcessTimes.restype = wintypes.BOOL
        self.k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.k.GetExitCodeProcess.restype = wintypes.BOOL
        need(type(pid) is int and pid > 0 and re.fullmatch('[0-9]{1,20}', birth), 'SPATIAL_NATIVE_IDENTITY_REQUIRED')
        self.handle = self.k.OpenProcess(4096 | 1048576, False, pid)
        need(self.handle, 'SPATIAL_WORKER_HANDLE_REQUIRED')
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            need(self.k.GetProcessTimes(self.handle, *[ctypes.byref(x) for x in times]), 'SPATIAL_BIRTH_QUERY_REQUIRED')
            actual = str(times[0].dwHighDateTime << 32 | times[0].dwLowDateTime)
            need(actual == birth, 'SPATIAL_WORKER_BIRTH_CHANGED')
            name = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(name))
            need(self.k.QueryFullProcessImageNameW(self.handle, 0, name, ctypes.byref(size)) and plain(name.value) == plain(image), 'SPATIAL_WORKER_IMAGE_CHANGED')
            need(self.alive(), 'SPATIAL_WORKER_ALREADY_EXITED')
        except BaseException:
            self.k.CloseHandle(self.handle)
            self.handle = None
            raise

    def alive(self):
        state = self.k.WaitForSingleObject(self.handle, 0)
        need(state in (0, 258), 'SPATIAL_WORKER_HANDLE_STATE_UNKNOWN')
        return state == 258

    def finish(self):
        need(not self.alive(), 'LIVE_SPATIAL_WORKER_HANDLE_RETAINED')
        code = wintypes.DWORD()
        need(self.k.GetExitCodeProcess(self.handle, ctypes.byref(code)), 'SPATIAL_EXIT_CODE_QUERY_REQUIRED')
        need(self.k.CloseHandle(self.handle), 'SPATIAL_HANDLE_CLOSE_FAILED')
        self.handle = None
        return code.value

class SpatialRuntime:

    def __init__(self, settings, run, platform_port, gateway_port, environment):
        self.settings = settings
        self.app = settings['application']
        self.code = settings['code']
        self.run = plain(run)
        self.env = environment
        need(self.run.parent == self.app / 'UserData/OriginalServer/runs' and re.fullmatch('j[1-9][0-9]{0,3}', self.run.name), 'EXACT_ORIGINAL_SPATIAL_RUN_REQUIRED')
        need(type(platform_port) is int and 1024 <= platform_port <= 65535, 'ACTUAL_ORIGINAL_PLATFORM_PORT_REQUIRED')
        need(type(gateway_port) is int and 1024 <= gateway_port <= 65535, 'ACTUAL_ORIGINAL_GATEWAY_PORT_REQUIRED')
        self.platform_port = platform_port
        self.gateway_port = gateway_port
        self.child = None
        self.record = None
        self.worker = None
        self.factory = None
        self.worker_handle = None
        self.tool_handles = []
        self.control = plain(self.app / 'UserData/LayerSyncControl')
        self.folder = self.run / 'spatial-sync'
        self.config_path = self.folder / 'server.private.json'
        self.config_raw = None
        self.config_sha = None

    def start(self, factory):
        self.factory = factory
        need(read(self.settings['settings'], 32768) == self.settings['settingsRaw'], 'SPATIAL_SETTINGS_CHANGED_BEFORE_START')
        value = self.settings['value']
        port = value['listenPort']
        while not port or port == self.gateway_port:
            with socket.socket() as reserved:
                reserved.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                reserved.bind(('127.0.0.1', 0))
                port = reserved.getsockname()[1]
        need(port != self.platform_port and port != self.gateway_port, 'SPATIAL_CANNOT_REUSE_ORIGINAL_PORT')
        self.folder.mkdir()
        worker_config = {'schema': 'xnby.layer-sync.server.v1', 'listenPort': port, 'platformPort': self.platform_port, 'access': value['access'], 'projectFilesRoot': value['projectFilesRoot']}
        if value.get('developmentLoopbackOrigin', False):
            worker_config['gatewayOrigin'] = 'http://127.0.0.1:' + str(self.gateway_port)
        if self.settings['sceneLibrary'] is not None:
            worker_config.update(self.settings['sceneLibrary'])
        if self.settings['sceneModels'] is not None:
            worker_config.update(self.settings['sceneModels'])
        worker_config['localGIS'] = self.settings['localGIS']
        if self.settings['clientResources'] is not None:
            worker_config['clientResources'] = self.settings['clientResources']
        self.config_raw = encode(worker_config)
        self.config_sha = digest(self.config_raw)
        write_new(self.config_path, self.config_raw)
        command = [str(self.app / 'runtime/python/python.exe'), '-I', '-B', str(self.code / 'tools/manage_layer_sync_server.py'), 'run', '--config', str(self.config_path), '--config-sha256', self.config_sha, '--manifest-sha256', PACKAGE_PIN, '--data-root', value['dataRoot'], '--control-root', str(self.control), '--max-restarts', '0']
        self.child = factory('spatial-sync', command, self.folder)
        self.child.require_job()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            need(self.child.process.poll() is None, 'SPATIAL_CONTROLLER_EXITED_BEFORE_READY')
            record = self._record()
            if record is not None:
                candidates = []
                for item in plain(record['run']).iterdir():
                    if item.is_dir() and re.fullmatch('[0-9a-f]{32}', item.name) and (item / 'ready.json').is_file():
                        worker = loads(read(item / 'ready.json', 16384))
                        need(worker.get('schema') == 'xnby.layer-sync.ready.v2' and worker.get('listen') == '127.0.0.1' and (worker.get('port') == port) and (worker.get('nativePlatformPort') == self.platform_port) and (worker.get('configSHA256') == self.config_sha) and (worker.get('manifestSHA256') == PACKAGE_PIN) and (worker.get('instanceId') == item.name), 'SPATIAL_READY_BINDING_CHANGED')
                        candidates.append(worker)
                need(len(candidates) <= 1, 'MULTIPLE_SPATIAL_READY_WORKERS_REFUSED')
                if candidates:
                    self.worker = candidates[0]
                    self.worker_handle = WorkerHandle(self.worker['pid'], self.worker['creation'], self.app / 'runtime/python/python.exe')
                    need(parent_pid(self.worker['pid']) == self.child.process.pid and self.worker_handle.alive(), 'SPATIAL_WORKER_PARENT_CHANGED')
                    self.record = record
                    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
                    try:
                        conn.request('GET', '/v2/project/layers')
                        response = conn.getresponse()
                        raw = response.read(4097)
                        need(response.status == 401 and len(raw) <= 4096 and (loads(raw) == {'error': 'LOGIN_REQUIRED'}), 'SPATIAL_ANONYMOUS_DENIAL_REQUIRED')
                    finally:
                        conn.close()
                    return self.state()
            time.sleep(0.05)
        raise TimeoutError('SPATIAL_READY_OBSERVATION_EXPIRED_NO_RESTART')

    def _record(self):
        pointer = self.control / 'current.private.json'
        if not pointer.exists():
            return None
        value = loads(read(pointer, 16384))
        need(value.get('schema') == 'xnby.layer-sync.controller.v1' and value.get('pid') == self.child.process.pid and (value.get('configSHA256') == self.config_sha) and (value.get('manifestSHA256') == PACKAGE_PIN), 'SPATIAL_CONTROLLER_POINTER_NOT_OWNED')
        need(self.child.process.poll() is None and value.get('creation') == process_birth(self.child.process._handle), 'SPATIAL_CONTROLLER_BIRTH_CHANGED')
        run = plain(value['run'])
        need(run.parent == self.control / 'runs' and re.fullmatch('[0-9a-f]{32}', run.name) and (run.name == value['instanceId']), 'SPATIAL_CONTROLLER_RUN_NOT_OWNED')
        return value

    def configure_gateway(self, config_path):
        path = plain(config_path)
        need(path == self.run / 'gateway/nginx.conf' and self.record is not None, 'OWN_NEW_GATEWAY_CONFIG_REQUIRED')
        before = read(path, 1048576)
        nonce = secrets.token_hex(16)
        script = "import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from tools.layer_sync_supervisor import verify_package;verify_package(Path(sys.argv[1]),sys.argv[2]);from tools.layer_sync_gateway_transaction import route_candidate;sys.stdout.buffer.write(route_candidate(sys.stdin.buffer.read(1048577),int(sys.argv[3]),sys.argv[4],project_files=True,project_scenes=sys.argv[5]=='1',project_models=sys.argv[6]=='1',local_gis=True,client_resources=sys.argv[7]=='1'))"
        with (self.folder / 'route-inspector.private.log').open('xb') as error:
            process = subprocess.Popen([str(self.app / 'runtime/python/python.exe'), '-I', '-B', '-c', script, str(self.code), PACKAGE_PIN, str(self.worker['port']), nonce, '1' if self.settings['sceneLibrary'] is not None else '0', '1' if self.settings['sceneModels'] is not None else '0', '1' if self.settings['clientResources'] is not None else '0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error, creationflags=subprocess.CREATE_NO_WINDOW, env=self.env, close_fds=True)
            record = {'process': process, 'job': None}
            self.tool_handles.append(record)
            try:
                job = OwnedWindowsJob(process)
                record['job'] = job
            except BaseException:
                process.communicate(input=b'')
                raise
            first = True
            while True:
                try:
                    after, _ = process.communicate(input=before if first else None, timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    first = False
            while job.active_processes():
                time.sleep(0.05)
            job.close()
            need(process.returncode == 0 and len(after) <= 1048576, 'SPATIAL_GATEWAY_GENERATOR_FAILED')
        after = insert_scene_routes(after, self.settings['sceneRows'])
        after = compose_model_authorization(after, self.worker['port'])
        after = protect_scene_assets(after, self.settings['sceneRows'], '/_xnby_original_scene_read_auth')
        need(read(path, 1048576) == before, 'OWN_GATEWAY_CHANGED_DURING_GENERATION')
        write_new(self.folder / 'gateway-before.conf', before)
        with path.open('wb') as f:
            f.write(after)
        self.route_nonce = nonce
        self.route_state = {'beforeSHA256': digest(before), 'afterSHA256': digest(after), 'accountBoundLayersAndProjectFiles': True}

    def verify_gateway(self):
        paths = ['/zhumadian/api/spatial-sync/v2/project/layers', '/zhumadian/api/spatial-sync/v2/project/files']
        if self.settings['sceneLibrary'] is not None:
            paths.append('/zhumadian/api/spatial-sync/v2/project/scenes')
        if self.settings['sceneModels'] is not None:
            paths.extend(['/zhumadian/api/spatial-sync/v2/project/scene-models', '/zhumadian/api/spatial-sync/v2/project/scene-models/operations/' + '0' * 32])
        for path in paths:
            conn = http.client.HTTPConnection('127.0.0.1', self.gateway_port, timeout=3)
            try:
                conn.request('GET', path)
                response = conn.getresponse()
                body = response.read(4097)
                need(response.status == 401 and response.getheader('X-XNBY-Layer-Sync-Deployment') == self.route_nonce and (len(body) <= 4096) and (loads(body) == {'error': 'LOGIN_REQUIRED'}), 'SPATIAL_ORIGINAL_GATEWAY_ROUTE_NOT_VERIFIED')
            finally:
                conn.close()
        if self.settings['sceneRows'] is not None:
            for route in ['/zhumadian/scene/', '/zhumadian/scene/viewer.js']:
                row = next((v for v in self.settings['sceneRows'] if v['route'] == route))
                expected = read(row['file'], 2 * 1048576)
                conn = http.client.HTTPConnection('127.0.0.1', self.gateway_port, timeout=5)
                try:
                    conn.request('GET', route)
                    response = conn.getresponse()
                    body = response.read(2 * 1048576 + 1)
                    need(response.status == 200 and body == expected, 'SCENE_ORIGINAL_GATEWAY_STATIC_CHANGED')
                finally:
                    conn.close()
        if self.settings['clientResources'] is not None:
            for suffix, expected_status in [('grants', 401), ('grants/consume', 403)]:
                conn = http.client.HTTPConnection('127.0.0.1', self.gateway_port, timeout=3)
                try:
                    conn.request('POST', '/zhumadian/api/spatial-sync/v2/client-resources/' + suffix,
                                 body=b'{}', headers={'Content-Type': 'application/json', 'Origin': 'https://www.joinlinksmart.com'})
                    response = conn.getresponse(); body = response.read(4097)
                    need(response.status == expected_status and len(body) <= 4096
                         and response.getheader('X-XNBY-Layer-Sync-Deployment') == self.route_nonce,
                         'CLIENT_RESOURCE_GATEWAY_ROUTE_NOT_VERIFIED')
                    code = loads(body).get('code')
                    need(code == ('RESOURCE_AUTHORIZATION_INVALID' if suffix == 'grants' else 'RESOURCE_GRANT_REJECTED'),
                         'CLIENT_RESOURCE_ANONYMOUS_GUARD_NOT_VERIFIED')
                finally:
                    conn.close()
        self.gateway_verified = True

    def require_alive(self):
        need(self.child is not None and self.child.process.poll() is None and (self.worker_handle is not None) and self.worker_handle.alive(), 'SPATIAL_OWNED_PROCESS_EXITED_AFTER_READY')

    def request_stop(self):
        if self.child is None or self.child.process.poll() is not None:
            return
        value = self._record()
        if value is None:
            return
        stop = plain(Path(value['run']) / 'stop.json')
        raw = encode({'schema': 'xnby.layer-sync.controller-stop.v1', 'instanceId': value['instanceId'], 'configSHA256': self.config_sha})
        if stop.exists():
            need(read(stop, 8192) == raw, 'UNKNOWN_SPATIAL_STOP_MARKER_RETAINED')
        else:
            write_new(stop, raw)

    def state(self):
        need(self.record is not None and self.worker is not None, 'SPATIAL_READY_NOT_OBSERVED')
        return {'schema': 'xnby.original.spatial-extension-ready.v1', 'controllerPID': self.child.process.pid, 'workerPID': self.worker['pid'], 'listenPort': self.worker['port'], 'platformPort': self.platform_port, 'configSHA256': self.config_sha, 'packageManifestSHA256': PACKAGE_PIN, 'originalGatewayRoutesVerified': getattr(self, 'gateway_verified', False), 'accountAccessThroughOriginalPlatform': True, 'actualOriginalAccountAccepted': False, 'sceneStaticConfigured': self.settings['sceneRows'] is not None, 'sceneModelsConfigured': self.settings['sceneModels'] is not None, 'modelCatalogSHA256': self.settings['sceneModels']['sceneModelsCatalogSHA256'] if self.settings['sceneModels'] is not None else None, 'clientOfflineGIS': True, 'localGISAuthorizationConfigured': True}

    def finish(self):
        result = {'clientOfflineGIS': True, 'controllerStarted': self.child is not None, 'workerReadyObserved': self.worker is not None, 'forceTerminationUsed': False}
        if self.child is not None:
            need(self.child.process.poll() is not None, 'LIVE_SPATIAL_CONTROLLER_MUST_BE_RETAINED')
            result['controllerExitCode'] = self.child.process.returncode
        if self.worker_handle is not None:
            result['workerExitCode'] = self.worker_handle.finish()
            result['actualWorkerHandleTerminal'] = True
        need(all((r['process'].poll() is not None and (r['job'] is None or r['job'].handle is None) for r in self.tool_handles)), 'LIVE_SPATIAL_GENERATOR_RETAINED')
        return result
