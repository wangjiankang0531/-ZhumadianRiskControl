"""Install only the explicitly approved, absent HKCU scene logon value."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, subprocess, winreg

R = Path('D:/Project/Zhumadian')
A = R / 'Application'
D = R / 'Document/Deployment/local_scene_recovery_20261102'
NAME = 'XNBYZhumadianScene'
KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
PS = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
COMMAND = "& 'D:\\Project\\Zhumadian\\Application\\runtime\\python\\python.exe' -I -B 'D:\\Project\\Zhumadian\\Application\\tools\\scene_boot.py'"
VALUE = '"' + PS + '" -NoProfile -WindowStyle Hidden -Command "' + COMMAND + '"'
proposal = json.loads((D / 'startup-proposal.json').read_bytes())
assert proposal['registryKey'] == 'HKCU\\' + KEY
assert proposal['valueName'] == NAME and proposal['valueType'] == 'String'
assert proposal['valueData'] == VALUE and len(VALUE) == 225
for filename, pin in proposal['files'].items():
    raw = Path(filename).read_bytes()
    assert len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']
proof = json.loads((D / 'scene-boot-verification.json').read_bytes())
assert proof['passed'] and len(proof['cases']) == 6
assert proof['sourceSHA256'] == proposal['files'][str(A / 'tools/scene_boot.py').replace('/', '\\')]['sha256']
spec = importlib.util.spec_from_file_location('scene_boot', A / 'tools/scene_boot.py')
scene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scene)
pins = scene.pin_package(scene.PACKAGE)
before = scene.health(scene.PACKAGE, 8767, pins)
assert before is not None, 'CURRENT_SERVICE_NOT_READY_REFUSE_CONFIGURATION'
db = scene.PACKAGE / 'UserData/BusinessData/layers.sqlite'
db_sha = hashlib.sha256(db.read_bytes()).hexdigest()
result = {
    'schema': 'xnby.local-scene-logon-install.r170.v1',
    'at': datetime.datetime.now().astimezone().isoformat(),
    'approvalQuestionId': 'call_4ccaf7f8ffcb46f28ae6ffb646b200a8',
    'approvalAnswer': '启用登录后后台自启（推荐）',
    'registryKey': 'HKCU\\' + KEY, 'valueName': NAME,
    'valueType': 'REG_SZ', 'valueData': VALUE,
    'beforeValueAbsent': False, 'persistentStartupInstalled': False,
    'desktopInputSent': False, 'futureActualLogonTested': False,
    'serverAccountFirewallOrPublicPortChanged': False,
}
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
        try:
            winreg.QueryValueEx(key, NAME)
        except FileNotFoundError:
            result['beforeValueAbsent'] = True
        else:
            raise RuntimeError('EXISTING_VALUE_REFUSED_NO_OVERWRITE')
        winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, VALUE)
        actual, kind = winreg.QueryValueEx(key, NAME)
        assert actual == VALUE and kind == winreg.REG_SZ
        result.update(persistentStartupInstalled=True, exactRegistryReadback=True)
    # Invoke precisely the recorded Windows command line, hidden, without reboot.
    run = subprocess.run(VALUE, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=80)
    assert run.returncode == 0, 'STARTUP_COMMAND_CHECK_FAILED'
    state = json.loads(run.stdout.decode('utf-8'))
    assert state['ready'] and state['reusedExistingService'] and not state['newServiceStarted']
    after = scene.health(scene.PACKAGE, 8767, pins)
    assert after and after['servicePID'] == before['servicePID'] == state['servicePID']
    assert hashlib.sha256(db.read_bytes()).hexdigest() == db_sha
    result.update(passed=True, exactStartupCommandExecuted=True,
                  sameExistingServiceReused=True, servicePID=after['servicePID'],
                  serviceStoppedOrRestarted=False, layerDatabaseBytesUnchangedDuringInstall=True)
finally:
    (D / 'startup-install-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
