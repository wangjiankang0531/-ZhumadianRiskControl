"""Stage only previously verified components; do not fix a public apply scope yet."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile

R = Path('D:/Project/Zhumadian')
A, T, Q = R / 'Application', R / 'Application/tools', Path('D:/Zqa20261025/Application')
W = R / 'work/user_feedback_20261031'
C = R / 'work/event_delivery_consistency_20261030/full-business-main-r113'
S = W / 'r23-unified-candidate-r1'
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert not S.exists()
    assert shutil.disk_usage(W).free > 3 * 1024 ** 3
    proof = read(C / 'independent-disposal-observed.json')
    assert proof['browserChecks'] == 20 and proof['actualGatewayUpdateRequests'] == 1
    assert proof['nativeCallbacksHTTP200Code0'] == 2 and proof['original398DefinitionsUnchanged']
    old = W / 'r22-risk-candidate-r3'
    plan = read(old / 'candidate-stage.json')
    emergency = W / 'emergency-disposal-busy-r1'
    em = read(emergency / 'candidate-proof.json')
    assert len(plan['allMaterializedPayloadFiles']) == 841 and len(em['files']) == 204
    S.mkdir()
    sources = {}
    for name, pin in plan['allMaterializedPayloadFiles'].items():
        source = old / 'payload' / name
        assert sha(source) == pin['sha256'] and source.stat().st_size == pin['bytes']
        target = S / 'payload' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources[name] = str(source)
    for name, pin in em['files'].items():
        source = emergency / 'frontend' / name
        assert sha(source) == pin['sha256'] and source.stat().st_size == pin['bytes']
        rel = 'frontend/emergency_pc/' + name
        target = S / 'payload' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources[rel] = str(source)
    for name in ['r21-base-release-manifest.json', 'r21-base-payload-manifest.json']:
        shutil.copyfile(old / name, S / name)
    target = S / 'public-control/tools/original_server_release_parameters.py'
    target.parent.mkdir(parents=True)
    shutil.copyfile(old / 'public-control/tools/original_server_release_parameters.py', target)
    assert sha(target) == '8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9'
    pins = read(C / 'native-async-support-pins.json')
    support_rel = 'payload/platform/run-template/own-platform-async-request.jar'
    support = S / 'payload' / support_rel
    support.parent.mkdir(parents=True)
    with zipfile.ZipFile(support, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, expected in pins['addedClasses'].items():
            source = C / 'native-async-classes' / name
            assert sha(source) == expected
            archive.write(source, name)
    assert sha(support) == pins['separateSupportJarSHA256'], 'EXACT_R113_TESTED_JAR_REPRODUCTION_REQUIRED'
    launcher_rel = 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class'
    output = S / 'payload/payload/platform/run-template/persistent-launcher-classes'
    output.mkdir(parents=True)
    meta = read(R / 'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
    java = Path(meta['java'])
    assert sha(java) == meta['javaSHA256']
    cp = ';'.join(map(str, [Q / 'payload/platform/run-template/wrapper-classes',
                           Q / 'payload/platform/run-template/persistent-launcher-classes',
                           Q / 'payload/callback-overlay/20261026-password-identity/persistent-launcher-classes',
                           Q / 'payload/platform/boot-loader.jar', Q / 'payload/platform/process-boundary.jar']))
    run = subprocess.run([str(java.with_name('javac.exe')), '-J-Xmx128m', '-source', '8', '-target', '8',
                          '-encoding', 'UTF-8', '-proc:none', '-cp', cp, '-d', str(output),
                          str(T / 'java/public_emergency_workflow_async_r1/OriginalAsyncPersistentPlatformLaunch.java')],
                         capture_output=True, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
    (S / 'compile-launcher.stderr.log').write_bytes(run.stderr)
    assert run.returncode == 0
    prior = read(C / 'platform-production-input-pins.json')
    expected = next(v for k, v in prior.items() if k.endswith('OriginalAsyncPersistentPlatformLaunch.class'))
    assert sha(S / 'payload' / launcher_rel) == expected, 'EXACT_R113_TESTED_LAUNCHER_REQUIRED'
    platform = {rel: {'bytes': (S / 'payload' / rel).stat().st_size, 'sha256': sha(S / 'payload' / rel)}
                for rel in [support_rel, launcher_rel]}
    shipped = {p.relative_to(S / 'payload').as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
               for p in (S / 'payload').rglob('*') if p.is_file()}
    assert len(shipped) == 1047
    result = {'basePublicRevision': 'R21', 'securityFrontendFiles': 836, 'emergencyFrontendFiles': 204,
              'allMaterializedPayloadFiles': shipped, 'backendOperations': plan['backendOperations'],
              'platformOperations': platform, 'asyncOriginalConfigSHA256': pins['originalAsyncConfigSHA256'],
              'asyncSupportFiveClasses': pins['addedClasses'], 'exactR113SupportAndLauncherBytes': True,
              'sourceMap': sources, 'publicApplyScopeFixed': False, 'controllerAdapterPending': True,
              'updaterAndNormalRecoveryPending': True, 'publicInstalled': False, 'fullCloneReady': False}
    (S / 'candidate-stage.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'stagedFiles': len(shipped), 'totalBytes': sum(x['bytes'] for x in shipped.values()),
                      'runtimeArtifactsExactlyMatchR113': True, 'publicScopeFixed': False}))


if __name__ == '__main__':
    main()
