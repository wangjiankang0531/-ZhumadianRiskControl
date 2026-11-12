"""Read-only identity gate for the installed original project gateway.

There are no process signals, service changes, config writes or credential reads.
The returned observation is a planning input, not a durable authorization to reload.
"""
from contextlib import ExitStack
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('DUPLICATE_OWNER_INPUT_KEY')
        value[key] = item
    return value


def loads(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_OWNER_INPUT')))


def number(value):
    if type(value) is not int or not 0 < value < 2**32:
        raise ValueError('INVALID_PROCESS_IDENTITY')
    return value


def plain(path):
    path = Path(path).absolute()
    if '..' in path.parts or str(path).startswith('\\\\'):
        raise ValueError('LOCAL_EXACT_OWNER_PATH_REQUIRED')
    for part in (*reversed(path.parents), path):
        if part.exists() and (part.is_symlink() or getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('OWNER_PATH_REDIRECTION_REJECTED')
    return path


def read(path, limit=1048576):
    with plain(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('OWNER_INPUT_TOO_LARGE')
    return raw


class ProcessHandle:
    """Query-only handle retained until the entire observation has been checked."""
    def __init__(self, pid):
        if os.name != 'nt':
            raise ValueError('WINDOWS_IDENTITY_REQUIRED')
        self.pid = number(pid)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        k = self.kernel
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k.GetProcessTimes.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.handle = k.OpenProcess(0x1000 | 0x100000, False, pid)
        if not self.handle:
            raise ValueError('PROCESS_IDENTITY_UNAVAILABLE')
        try:
            self.creation = self.birth()
            size = wintypes.DWORD(32768)
            text = ctypes.create_unicode_buffer(size.value)
            if not k.QueryFullProcessImageNameW(self.handle, 0, text, ctypes.byref(size)):
                raise ValueError('PROCESS_IMAGE_UNAVAILABLE')
            self.image = str(plain(text.value))
        except BaseException:
            self.close()
            raise

    def birth(self):
        if self.kernel.WaitForSingleObject(self.handle, 0) != 258:
            raise ValueError('PROCESS_EXITED_DURING_OBSERVATION')
        values = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(self.handle, *[ctypes.byref(v) for v in values]):
            raise ValueError('PROCESS_CREATION_UNAVAILABLE')
        return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime

    def verify(self):
        if self.birth() != self.creation:
            raise ValueError('PROCESS_IDENTITY_CHANGED')

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def split_command_line(text):
    if not isinstance(text, str) or not text or len(text) > 32768 or '\0' in text:
        raise ValueError('PROCESS_ARGUMENTS_UNAVAILABLE')
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel.LocalFree.restype = wintypes.HLOCAL
    count = ctypes.c_int()
    argv = shell.CommandLineToArgvW(text, ctypes.byref(count))
    if not argv:
        raise ValueError('PROCESS_ARGUMENTS_UNAVAILABLE')
    try:
        if not 1 <= count.value <= 64:
            raise ValueError('PROCESS_ARGUMENTS_UNAVAILABLE')
        return [argv[i] for i in range(count.value)]
    finally:
        kernel.LocalFree(argv)


def cim_observation(pids, port=None):
    numbers = sorted({number(pid) for pid in pids})
    if not 1 <= len(numbers) <= 8:
        raise ValueError('BOUNDED_PROCESS_SELECTION_REQUIRED')
    if port is not None and (type(port) is not int or not 1024 <= port <= 65535):
        raise ValueError('INVALID_OWNER_PORT')
    # Only validated decimal IDs/port are inserted into a fixed read-only script.
    script = "$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
    script += '$numbers=@(' + ','.join(map(str, numbers)) + ');$listeners=@();'
    if port is not None:
        script += '$listeners=@(Get-NetTCPConnection -State Listen -LocalPort ' + str(port) + ' | ForEach-Object { @{address=$_.LocalAddress;port=[int]$_.LocalPort;pid=[int]$_.OwningProcess} });'
        script += "if($listeners.Count -eq 0 -or $listeners.Count -gt 8){throw 'Listener selection unavailable'};"
        script += '$numbers=@($numbers + @($listeners | ForEach-Object {$_.pid}) | Sort-Object -Unique);'
    script += "if($numbers.Count -gt 16){throw 'Process selection unavailable'};"
    script += '$rows=@(foreach($processNumber in $numbers){$row=Get-CimInstance Win32_Process -Filter (\'ProcessId=\'+$processNumber);'
    script += "if($null -eq $row -or $null -eq $row.CreationDate){throw 'Process unavailable'};"
    script += '@{pid=[int]$row.ProcessId;parent=[int]$row.ParentProcessId;image=$row.ExecutablePath;command=$row.CommandLine;creation=$row.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString([Globalization.CultureInfo]::InvariantCulture)}});'
    script += '@{processes=$rows;listeners=$listeners} | ConvertTo-Json -Compress -Depth 5;'
    exe = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run([str(exe), '-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand',
                             base64.b64encode(script.encode('utf-16-le')).decode('ascii')],
                            capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW,
                            close_fds=True)
    if result.returncode or len(result.stdout) > 1048576:
        raise ValueError('READ_ONLY_PROCESS_OBSERVATION_FAILED')
    try:
        value = loads(result.stdout.decode('utf-8-sig'))
        if not isinstance(value, dict) or set(value) != {'processes', 'listeners'}:
            raise ValueError('INVALID_PROCESS_OBSERVATION')
        if not isinstance(value['processes'], list) or not isinstance(value['listeners'], list):
            raise ValueError('INVALID_PROCESS_OBSERVATION')
        return value
    except (ValueError, TypeError, UnicodeError):
        raise ValueError('INVALID_PROCESS_OBSERVATION') from None


def sample_processes(pids, port=None):
    """Hold identities across CIM lookup; WMI timestamps have microsecond precision."""
    with ExitStack() as stack:
        handles = {pid: stack.enter_context(ProcessHandle(pid)) for pid in set(pids)}
        first = cim_observation(pids, port)
        result = []
        for row in first['processes']:
            pid = number(row.get('pid'))
            if pid not in handles:
                handles[pid] = stack.enter_context(ProcessHandle(pid))
            handle = handles[pid]
            if (not isinstance(row.get('creation'), str) or not re.fullmatch('[0-9]{1,20}', row['creation'])
                    or abs(int(row['creation']) - handle.creation) >= 10
                    or plain(row.get('image', '')) != plain(handle.image)):
                raise ValueError('PROCESS_CHANGED_DURING_OBSERVATION')
            result.append({'pid': pid, 'parent': number(row.get('parent')), 'image': handle.image,
                           'creation': str(handle.creation), 'argv': split_command_line(row.get('command'))})
        if {row['pid'] for row in result} != set(handles) or len(result) != len(handles):
            raise ValueError('INCOMPLETE_PROCESS_OBSERVATION')
        # Listener changes or PID reuse during the longer CIM query reject the sample.
        if port is not None:
            second = cim_observation(pids, port)
            canonical = lambda rows: sorted((r['address'], r['port'], r['pid']) for r in rows)
            if canonical(first['listeners']) != canonical(second['listeners']):
                raise ValueError('LISTENER_CHANGED_DURING_OBSERVATION')
        for handle in handles.values():
            handle.verify()
        return {'processes': result, 'listeners': first['listeners']}


def snapshot(application, preflight):
    app = plain(application)
    if (preflight.get('schema') != 'xnby.layer-sync.server-preflight.v1'
            or preflight.get('passed') is not True or plain(preflight['application']) != app):
        raise ValueError('MATCHING_PASSED_PREFLIGHT_REQUIRED')
    run = plain(preflight['run'])
    if run.parent != app / 'UserData/OriginalServer/runs' or not re.fullmatch('j[1-9][0-9]{0,3}', run.name):
        raise ValueError('EXACT_PROJECT_RUN_REQUIRED')
    paths = {'current': app / 'UserData/OriginalServer/current-run.json', 'ready': run / 'ready.json',
             'release': app / 'release-manifest.json', 'nginx': run / 'gateway/nginx.conf',
             'nginxPID': run / 'gateway/nginx.pid'}
    raw = {name: read(path, 4 * 1048576 if name == 'release' else 1048576) for name, path in paths.items()}
    for name, field in [('current', 'currentReadySHA256'), ('ready', 'currentReadySHA256'),
                        ('release', 'releaseManifestSHA256'), ('nginx', 'nginxConfigSHA256')]:
        if sha(raw[name]) != preflight[field]:
            raise ValueError('SERVER_CHANGED_SINCE_PREFLIGHT')
    ready = loads(raw['current'].decode('utf-8-sig'))
    release = loads(raw['release'].decode('utf-8-sig'))
    if (ready.get('ready') is not True or ready.get('releaseId') != preflight['releaseId']
            or release.get('releaseId') != preflight['releaseId'] or plain(ready['run']) != run):
        raise ValueError('SERVER_RUN_IDENTITY_MISMATCH')
    for field, port in preflight['ports'].items():
        if type(port) is not int or not 1024 <= port <= 65535 or ready.get(field) != port:
            raise ValueError('SERVER_PORT_CHANGED')
    controller = number(ready.get('controllerPID'))
    master = number(ready.get('children', {}).get('gateway'))
    if controller == master or raw['nginxPID'].strip() != str(master).encode('ascii'):
        raise ValueError('GATEWAY_MASTER_PID_MISMATCH')
    return {'app': app, 'run': run, 'paths': paths, 'raw': raw, 'ready': ready,
            'controller': controller, 'master': master}


def _options(argv, allowed):
    if len(argv) % 2 or any(argv[i] not in allowed for i in range(0, len(argv), 2)):
        raise ValueError('UNEXPECTED_OWNER_ARGUMENTS')
    result = {}
    for i in range(0, len(argv), 2):
        if argv[i] in result:
            raise ValueError('DUPLICATE_OWNER_ARGUMENT')
        result[argv[i]] = argv[i+1]
    return result


def verify_observation(state, observed, preflight):
    """Validate an observation, including listener worker lineage and exact flags."""
    app, run = state['app'], state['run']
    rows = observed.get('processes')
    listeners = observed.get('listeners')
    if not isinstance(rows, list) or not 2 <= len(rows) <= 10 or not isinstance(listeners, list) or not 1 <= len(listeners) <= 8:
        raise ValueError('BOUNDED_OWNER_OBSERVATION_REQUIRED')
    by_id = {}
    for row in rows:
        pid = number(row.get('pid'))
        if pid in by_id or not isinstance(row.get('creation'), str) or not re.fullmatch('[0-9]{1,20}', row['creation']):
            raise ValueError('INVALID_PROCESS_IDENTITY')
        if not isinstance(row.get('argv'), list) or not row['argv'] or not all(isinstance(a, str) for a in row['argv']):
            raise ValueError('INVALID_PROCESS_ARGUMENTS')
        by_id[pid] = row
    if state['controller'] not in by_id or state['master'] not in by_id:
        raise ValueError('SELECTED_OWNER_PROCESS_MISSING')
    controller = by_id[state['controller']]
    master = by_id[state['master']]
    python = app / 'runtime/python/python.exe'
    nginx = app / 'runtime/nginx/nginx.exe'
    if plain(controller['image']) != python or plain(controller['argv'][0]) != python:
        raise ValueError('CONTROLLER_IMAGE_MISMATCH')
    args = controller['argv'][1:]
    while args and args[0] in ('-I', '-B'):
        args = args[1:]
    if not args or plain(args[0]) != app / 'tools/serve_original_server_release.py':
        raise ValueError('CONTROLLER_SCRIPT_MISMATCH')
    options = _options(args[1:], {'--application', '--release-manifest-sha256', '--gateway-port',
                                  '--callback-overlay', '--callback-overlay-sha256'})
    if (plain(options.get('--application', '')) != app
            or options.get('--release-manifest-sha256') != preflight['releaseManifestSHA256']
            or options.get('--gateway-port', '18892') != str(preflight['ports']['gatewayPort'])):
        raise ValueError('CONTROLLER_ARGUMENTS_MISMATCH')
    if ('--callback-overlay' in options) != ('--callback-overlay-sha256' in options):
        raise ValueError('INCOMPLETE_CALLBACK_ARGUMENTS')
    if master.get('parent') != state['controller'] or int(master['creation']) < int(controller['creation']):
        raise ValueError('GATEWAY_CONTROLLER_LINEAGE_MISMATCH')
    selected = {state['controller'], state['master']}
    for listener in listeners:
        if (listener.get('address') != '127.0.0.1' or type(listener.get('port')) is not int
                or listener['port'] != preflight['ports']['gatewayPort']):
            raise ValueError('EXACT_LOOPBACK_LISTENER_REQUIRED')
        pid = number(listener.get('pid'))
        row = by_id.get(pid)
        if row is None:
            raise ValueError('LISTENER_PROCESS_MISSING')
        selected.add(pid)
        if pid != state['master'] and (row.get('parent') != state['master'] or int(row['creation']) < int(master['creation'])):
            raise ValueError('GATEWAY_WORKER_LINEAGE_MISMATCH')
    for pid in selected - {state['controller']}:
        row = by_id[pid]
        if plain(row['image']) != nginx or plain(row['argv'][0]) != nginx:
            raise ValueError('GATEWAY_IMAGE_MISMATCH')
        options = _options(row['argv'][1:], {'-p', '-c'})
        if set(options) != {'-p', '-c'} or plain(options['-p']) != run / 'gateway' or plain(options['-c']) != state['paths']['nginx']:
            raise ValueError('GATEWAY_ARGUMENTS_MISMATCH')
    if set(by_id) != selected:
        raise ValueError('UNEXPECTED_OBSERVED_PROCESS')
    return {'controller': {'pid': controller['pid'], 'creation': controller['creation']},
            'gatewayMaster': {'pid': master['pid'], 'creation': master['creation']},
            'listenerOwners': [{'pid': pid, 'creation': by_id[pid]['creation']} for pid in sorted(selected - {state['controller']})],
            'gatewayPort': preflight['ports']['gatewayPort']}


def inspect(application, preflight, sampler=sample_processes):
    state = snapshot(application, preflight)
    observed = sampler([state['controller'], state['master']], preflight['ports']['gatewayPort'])
    identity = verify_observation(state, observed, preflight)
    for name, path in state['paths'].items():
        if read(path, 4 * 1048576 if name == 'release' else 1048576) != state['raw'][name]:
            raise ValueError('SERVER_CHANGED_DURING_OWNER_CHECK')
    return {'schema': 'xnby.layer-sync.server-owner-observation.v1', 'passed': True,
            'identity': identity, 'snapshotSHA256': {name: sha(raw) for name, raw in state['raw'].items()},
            'configurationServiceDatabaseAndLayerWrites': 0, 'credentialsReadOrRecorded': False,
            'deploymentPerformed': False, 'reloadAuthorizedByObservation': False,
            'ownershipRevalidationRequiredBeforeMutation': True}
