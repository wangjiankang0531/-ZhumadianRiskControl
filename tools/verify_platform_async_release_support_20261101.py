"""File/argument contract checks for the publication adapter; never starts a service."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil

R = Path('D:/Project/Zhumadian')
T = R / 'Application/tools'
S = R / 'work/user_feedback_20261031/r23-unified-candidate-r1'
O = R / 'work/user_feedback_20261031/r23-startup-contract-r1'
Q = Path('D:/Zqa20261025/Application')
spec = importlib.util.spec_from_file_location('declared_async', T / 'original_platform_async_release_support_20261101.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    assert not O.exists()
    O.mkdir()
    app = O / 'Application'
    root = app / 'UserData/TianjinOriginalPlatform/runs/j1'
    root.mkdir(parents=True)
    release = {m.FIELD: copy.deepcopy(m.CONTRACT)}
    for name in m.CONTRACT['files']:
        sub = name.split('/run-template/', 1)[1]
        dest = root / sub
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(S / 'payload' / name, dest)
    adapter = root / 'own-platform-observation.jar'
    shutil.copyfile(Q / 'payload/callback-overlay/20261026-password-identity/own-platform-observation.jar', adapter)
    native = Q / 'payload/platform/original-platform.jar'
    secret_marker = 'OWN_SYNTHETIC_PRIVATE_NOT_FOR_OUTPUT'
    original = {'configuration': {'platform': {'context.initializer.classes': 'own.first.Initializer,own.second.Initializer',
                                              'own.fake.private': secret_marker},
                                   'business': {'untouched': secret_marker}},
                'platformArguments': ['-Xmx768m', '-Down.platform.root=' + root.as_posix(),
                                      '-Down.platform.source.path=' + native.as_posix(), '-cp', 'OWN_CLASSPATH',
                                      m.OLD_MAIN, str(native), str(root)],
                'businessArguments': ['OWN_UNTOUCHED_BUSINESS_ARGUMENT']}
    expected_original = copy.deepcopy(original)
    cases = []

    def passed(name):
        cases.append({'case': name, 'passed': True})

    def reject(name, call):
        try:
            call()
        except (ValueError, FileNotFoundError) as error:
            assert secret_marker not in str(error)
            passed(name)
        else:
            raise AssertionError('GUARD_DID_NOT_REJECT:' + name)

    assert m.configure_platform({}, original, callback_enabled=False) is original
    assert m.adapt_platform_launch('NOT_A_PATH', {}, 'NOT_A_PATH', original) is original
    passed('old-release-exact-noop-with-no-code-or-path-read')
    configured = m.configure_platform(release, original, callback_enabled=True)
    assert original == expected_original
    expected = copy.deepcopy(original)
    expected['configuration']['platform']['context.initializer.classes'] += ',' + m.INITIALIZER
    assert configured == expected
    passed('only-one-initializer-added-all-original-config-and-business-arguments-preserved')
    prepared = {'side': 'platform', 'runtime': str(root), 'configuration': configured['configuration']['platform'],
                'properties': b'OWN_PREPARED_PROPERTIES_NOT_REWRITTEN', 'arguments': original['platformArguments']}
    ready = m.adapt_platform_launch(app, release, root, prepared)
    assert ready['configuration'] == prepared['configuration'] and ready['properties'] == prepared['properties']
    assert ready['arguments'][3:] == [m.NEW_MAIN if x == m.OLD_MAIN else x for x in prepared['arguments']]
    assert prepared['arguments'] == original['platformArguments']
    passed('only-three-declared-flags-and-one-main-class-change-no-input-mutation')
    empty = copy.deepcopy(original)
    empty['configuration']['platform'].pop('context.initializer.classes')
    assert m.configure_platform(release, empty, callback_enabled=True)['configuration']['platform']['context.initializer.classes'] == m.INITIALIZER
    passed('empty-explicit-initializers-supported-with-original-factories-retained')
    for name, value in [('null', None), ('wrong-type', []), ('wrong-revision', {**m.CONTRACT, 'revision': 'other'}),
                        ('extra-key', {**m.CONTRACT, 'extra': True}), ('wrong-original-config', {**m.CONTRACT, 'originalAsyncConfigSHA256': '0' * 64})]:
        reject('descriptor-' + name, lambda value=value: m.configure_platform({m.FIELD: value}, original, callback_enabled=True))
    wrong = copy.deepcopy(m.CONTRACT)
    next(iter(wrong['files'].values()))['sha256'] = '0' * 64
    reject('descriptor-code-pin-drift', lambda: m.configure_platform({m.FIELD: wrong}, original, callback_enabled=True))
    reject('callback-overlay-missing', lambda: m.configure_platform(release, original, callback_enabled=False))
    for name, init in [('existing-new-initializer', m.INITIALIZER), ('duplicate-old', 'own.first.Init,own.first.Init'),
                       ('empty-item', 'own.first.Init,'), ('malformed-class', 'own/first/Init'), ('control-character', 'own.first.Init\n')]:
        bad = copy.deepcopy(original)
        bad['configuration']['platform']['context.initializer.classes'] = init
        reject('initializer-' + name, lambda bad=bad: m.configure_platform(release, bad, callback_enabled=True))
    bad = copy.deepcopy(original)
    bad['platformArguments'].insert(0, '-Down.async.support.sha256=' + secret_marker)
    reject('existing-async-flags-and-private-marker-not-returned', lambda: m.configure_platform(release, bad, callback_enabled=True))
    bad = copy.deepcopy(original)
    bad['platformArguments'] = [x for x in bad['platformArguments'] if x != m.OLD_MAIN]
    reject('missing-main-rejected-before-components', lambda: m.configure_platform(release, bad, callback_enabled=True))
    for label in ['support', 'launcher', 'adapter']:
        path = adapter if label == 'adapter' else root / next(name.split('/run-template/', 1)[1] for name in m.CONTRACT['files']
                                                            if name.endswith('/own-platform-async-request.jar') == (label == 'support'))
        raw = path.read_bytes()
        path.write_bytes(raw + b'OWN_DRIFT')
        reject('runtime-' + label + '-drift', lambda: m.adapt_platform_launch(app, release, root, prepared))
        path.write_bytes(raw)
        path.unlink()
        reject('runtime-' + label + '-missing', lambda: m.adapt_platform_launch(app, release, root, prepared))
        path.write_bytes(raw)
    reject('foreign-runtime-layout', lambda: m.adapt_platform_launch(app, release, root.parent / 'not-owned', prepared))
    for label, change in [
        ('wrong-side', lambda p: p.update(side='business')),
        ('wrong-runtime', lambda p: p.update(runtime=str(root.parent / 'j2'))),
        ('missing-initializer', lambda p: p['configuration'].update({'context.initializer.classes': 'own.first.Initializer'})),
        ('missing-main', lambda p: p['arguments'].remove(m.OLD_MAIN)),
        ('duplicate-main', lambda p: p['arguments'].insert(0, m.OLD_MAIN)),
        ('already-new-main', lambda p: p['arguments'].insert(0, m.NEW_MAIN)),
        ('extra-main-argument', lambda p: p['arguments'].append('OWN_EXTRA')),
        ('wrong-root-argument', lambda p: p['arguments'].__setitem__(-1, str(root.parent / 'j2'))),
        ('async-override', lambda p: p['arguments'].insert(0, '-Down.async.request.snapshot.enabled=false')),
        ('duplicate-root-property', lambda p: p['arguments'].insert(0, '-Down.platform.root=' + str(root))),
        ('wrong-source-property', lambda p: p['arguments'].__setitem__(2, '-Down.platform.source.path=' + str(adapter))),
        ('wrong-native-jar', lambda p: p['arguments'].__setitem__(-2, str(adapter))),
    ]:
        bad = copy.deepcopy(prepared)
        change(bad)
        reject('arguments-' + label, lambda bad=bad: m.adapt_platform_launch(app, release, root, bad))
    assert original == expected_original
    result = {'cases': cases, 'allPassed': True, 'servicesStarted': False, 'databaseOrRealCredentialsRead': False,
              'originalInputObjectsUnchanged': True, 'sourceSHA256': hashlib.sha256((T / 'original_platform_async_release_support_20261101.py').read_bytes()).hexdigest(),
              'controllerAdapterStillNeedsRealRuntime': True, 'publicScopeFixed': False}
    (O / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'contractCases': len(cases), 'allPassed': True, 'noServicesStarted': True}))


if __name__ == '__main__':
    main()
