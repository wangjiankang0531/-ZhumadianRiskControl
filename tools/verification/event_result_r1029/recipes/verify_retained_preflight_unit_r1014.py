"""Focused AST unit regression only. File/helper/pool I/O is explicitly stubbed.

Does not execute the approval-blocked full physical-file verifier or lifecycle.
"""
from pathlib import Path
from types import SimpleNamespace
import ast, hashlib, json

V = Path(__file__).resolve().parent
R = Path('D:/Project/Zhumadian')
R1 = R/'Document/Deployment/event_result_runtime_r1000_20261105/source/original_public_test_update.py'
R2 = V/'r48-retained-preflight-r2-r1013/source/original_public_test_update.py'
OUT = V/'verified-retained-preflight-unit-r1014.json'
assert not OUT.exists(), 'DO_NOT_REPLAY_COMPLETED_UNIT'
APP, BUNDLE = Path('owned-unit-app'), Path('owned-unit-bundle')
JAR = 'payload/business/run-template/own-supervision-pdf.jar'
RAW = b'{"configuration":{"business":{}}}'
CONFIG_SHA = hashlib.sha256(RAW).hexdigest()
DESCRIPTOR = {'file': JAR, 'sha256': 'fixed-unit-module-pin', 'bytes': 42,
              'originalBusinessJarSHA256': 'fixed-unit-business-pin'}
cases = []

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def function_from_source(path):
    tree = ast.parse(path.read_text(encoding='utf8'))
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'preflight']
    assert len(nodes) == 1
    return nodes[0]

def run(path, transported, *, budget=True, drift=False, declared=True,
        helper_fail=False, module_fail=False, business_fail=False):
    calls, configured = [], []
    result = {'configurationSHA256': 'changed' if drift else CONFIG_SHA} if budget else None
    def check_file(root, rel, *pins):
        calls.append((str(root), rel, pins))
        if rel == JAR and module_fail:
            raise ValueError('MODULE_PIN_MISMATCH')
        if rel == 'payload/business/application.jar' and business_fail:
            raise ValueError('BUSINESS_PIN_MISMATCH')
    def configure(release, config):
        configured.append(config)
        if helper_fail:
            raise ValueError('INITIALIZER_REFUSED')
    env = {'original_preflight': lambda *args: result,
           'read': lambda *args: {'unit': True},
           'declared': lambda *args: declared, 'need': need,
           'm': SimpleNamespace(regular=lambda *args: SimpleNamespace(read_bytes=lambda: RAW),
                                check_file=check_file),
           'staged_helper': lambda *args: SimpleNamespace(configure_business=configure),
           'hashlib': hashlib, 'json': json, 'DESCRIPTOR': DESCRIPTOR}
    node = function_from_source(path)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), 'exec'), env)
    plan = {'files': {JAR: {}} if transported else {}}
    try:
        returned = env['preflight'](APP, BUNDLE, plan)
        error = None
    except ValueError as exc:
        returned, error = None, str(exc)
    return returned, error, calls, configured

# Reproduce first-draft defect using the actual extracted function.
_, err, calls, _ = run(R1, False)
assert err is None and calls[0][0] == str(BUNDLE/'payload')
cases.append('R1-retained-module-incorrectly-selected-stage-reproduced')

for transported in (False, True):
    returned, err, calls, configured = run(R2, transported)
    expected = BUNDLE/'payload' if transported else APP
    assert err is None and returned['supervisionModuleAndInitializerPreflightPassed'] is True
    assert calls == [(str(expected), JAR, (DESCRIPTOR['sha256'], DESCRIPTOR['bytes'])),
                     (str(APP), 'payload/business/application.jar', (DESCRIPTOR['originalBusinessJarSHA256'],))]
    assert configured == [json.loads(RAW)]
    cases.append('R2-' + ('transported-module-uses-stage' if transported else 'retained-module-uses-installed-app'))

for opts, reason, file_calls in [
    ({'budget': False}, 'RETAINED_BOUNDED_POOL_PREFLIGHT_REQUIRED', 0),
    ({'drift': True}, 'CONFIGURATION_CHANGED_DURING_SUPERVISION_PREFLIGHT', 0),
    ({'helper_fail': True}, 'INITIALIZER_REFUSED', 0),
    ({'module_fail': True}, 'MODULE_PIN_MISMATCH', 1),
    ({'business_fail': True}, 'BUSINESS_PIN_MISMATCH', 2),
]:
    _, err, calls, _ = run(R2, False, **opts)
    assert err == reason and len(calls) == file_calls
    cases.append('R2-refuses-' + reason)

returned, err, calls, configured = run(R2, False, budget=False, declared=False)
assert err is None and returned is None and not calls and not configured
cases.append('R2-undeclared-release-retains-original-preflight-result')

report = {'passed': True, 'checks': len(cases), 'cases': cases,
          'sourcePins': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (R1, R2)},
          'actualNestedFunctionExtractedFromEachSource': True,
          'poolFileHelperAndReleaseIOExplicitlyStubbed': True,
          'notPhysicalFileValidationOrSixComponentLifecycle': True,
          'blockedR1008NotExecutedOrRelocated': True,
          'projectGitPublicOrUserDataWritten': False}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'passed': True, 'checks': len(cases), 'report': str(OUT)}))
