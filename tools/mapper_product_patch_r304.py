from pathlib import Path
import argparse, hashlib, json, subprocess, os, importlib.util
R = Path('D:/Project/Zhumadian')
A = R / '_g/Application'
T = R / 'Application/tools'
C = R / 'work/event_delivery_consistency_20261030/full-controller-r163'
J = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
enc = lambda o: (json.dumps(o, ensure_ascii=False, indent=2) + '\n').encode()
p = argparse.ArgumentParser()
p.add_argument('action', choices=['prepare', 'restore'])
p.add_argument('--attempt', required=True, choices=['r135', 'r136'])
o = p.parse_args()
P = C / ('prepared-' + o.attempt)
assert J(A.parent / 'own-fixture.json')['ownedSyntheticFixtureOnly'] and (not (A.parent / 'user-manual-protected.json').exists())
query = '(Get-CimInstance Win32_Process -Filter "Name=\'python.exe\' OR Name=\'java.exe\' OR Name=\'mysqld.exe\' OR Name=\'minio.exe\' OR Name=\'chrome.exe\' OR Name=\'nginx.exe\' OR Name=\'redis-server.exe\'" | Where-Object {($_.CommandLine -replace \'\\\\\',\'/\').ToLowerInvariant().Contains(\'d:/project/zhumadian/_g/application\')} | Measure-Object).Count'
s = subprocess.run(['powershell.exe', '-NoProfile', '-Command', query], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
assert s.returncode == 0 and s.stdout.decode('utf-8-sig').strip() == '0'
if o.action == 'prepare':
    assert not (C / o.attempt).exists() and (not (P / 'mapper-product-scope.json').exists())
    before = {n: (A / n).read_bytes() for n in ['tools/original_server_release_parameters.py', 'tools/original_public_test_update.py', 'payload-manifest.json', 'release-manifest.json']}
    assert hashlib.sha256(before['tools/original_server_release_parameters.py']).hexdigest() == '8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'
    source = T / 'original_public_test_update_r38_mapper_preflight_r286.py'
    spec = importlib.util.spec_from_file_location('mapper_product', source)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    parameter = T / 'original_server_release_parameters_r263_mapper_default.py'
    assert sha(parameter) == m.R38_PARAMETER_PIN['sha256']
    after = {'tools/original_server_release_parameters.py': parameter.read_bytes(), 'tools/original_public_test_update.py': source.read_bytes()}
    q = J(A / 'payload-manifest.json')
    release = J(A / 'release-manifest.json')
    for n, b in after.items():
        release['controllerFiles'][n] = hashlib.sha256(b).hexdigest()
        if n in q['files']:
            q['files'][n] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
    release[m.R38_MAPPER_FIELD] = m.R38_MAPPER_CONTRACT
    release[m.R24_WORKFLOW_FIELD] = m.workflow_contract_for(release)
    assert m.workflow_declared(release, q) and m.runtime_pool_declared(release)
    after['payload-manifest.json'] = enc(q)
    release['payloadManifestSHA256'] = hashlib.sha256(after['payload-manifest.json']).hexdigest()
    after['release-manifest.json'] = enc(release)
    scope = {'onlyOwnedStoppedSyntheticFixture': True, 'exactProductParameterSourceExecuted': True, 'oldFiles': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in before.items()}, 'newFiles': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in after.items()}, 'fixedRuntimeSourceNotTransportAcceptance': True, 'publicTransportContractAvailable': False, 'privateConfigurationChangedByProductPatch': False}
    for n, b in before.items():
        p = P / 'mapper-product-before' / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    (P / 'mapper-product-scope.json').write_bytes(enc(scope))
    for n, b in after.items():
        p = A / n
        assert p.resolve() == p and (not p.lstat().st_file_attributes & 1024)
        p.unlink()
        p.write_bytes(b)
    ready = J(P / 'controller-fixture-ready.json')
    ready.update(releaseSHA256=sha(A / 'release-manifest.json'), updaterSHA256=sha(A / 'tools/original_public_test_update.py'))
    (P / 'controller-fixture-ready.json').write_bytes(enc(ready))
    print(json.dumps({'prepared': True, 'exactR263ParameterAndRuntimeDeclarationsInstalled': True, 'allOriginalSQLAndJarAndAuthKept': True}))
else:
    t = J(C / o.attempt / 'controller-terminal.json')
    outer = J(C / (o.attempt + '-outer-terminal.json'))
    receipt = J(C / o.attempt / 'scoped-controller-receipt.json')
    assert t['actualDescendantJobCountZeroBeforeClose'] and outer['actualDescendantsZeroBeforeClose'] and receipt['allOwnedChildrenExited'] and (not receipt['forcedJobClosureComponents']) and all((v == 0 for v in receipt['exitCodesBeforeJobClose'].values()))
    scope = J(P / 'mapper-product-scope.json')
    for n, pin in scope['newFiles'].items():
        assert sha(A / n) == pin['sha256'], 'FOREIGN_DRIFT_REFUSE_PRODUCT_RESTORE'
    for n, pin in scope['oldFiles'].items():
        assert sha(P / 'mapper-product-before' / n) == pin['sha256']
    for n in scope['oldFiles']:
        p = A / n
        tmp = p.with_name(p.name + '.own-r266-product-restore.tmp')
        assert not tmp.exists()
        tmp.write_bytes((P / 'mapper-product-before' / n).read_bytes())
        os.replace(tmp, p)
    assert all((sha(A / n) == pin['sha256'] for n, pin in scope['oldFiles'].items()))
    proof = {'passed': True, 'exactProductParameterUpdaterAndManifestBytesRestored': True, 'actualDescendantsZeroBeforeRestore': True, 'configurationDatabaseOrSQLRewritten': False}
    (P / 'mapper-product-restored.json').write_bytes(enc(proof))
    print(json.dumps(proof))
